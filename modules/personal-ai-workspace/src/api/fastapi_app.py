from __future__ import annotations

import os
import json
import asyncio
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.personal_assistant_agent import PersonalAssistantAgent
from src.cli import doctor_llm
from src.config.config_loader import load_config
from src.tools.default_registry import build_registry
from src.tools.kb_tools import ingest_tool, list_docs_tool

config = load_config()
registry = build_registry(config)
app = FastAPI(title="personal-ai-workspace")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("server", {}).get("cors_origins", ["http://localhost:3000", "http://127.0.0.1:3000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str | None = None
    mode: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    query_rewrite: str | None = None
    crag_enabled: bool | None = None
    multi_hop_enabled: bool | None = None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    query_rewrite: str | None = None
    crag_enabled: bool | None = None
    multi_hop_enabled: bool | None = None


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1)
    mode: str | None = Field(default=None, pattern="^(planner|react)$")
    session_id: str = Field(default="default", min_length=1, max_length=120)


class IngestRequest(BaseModel):
    path: str = Field(..., min_length=1)
    collection: str = "personal"
    tags: list[str] = []


class ReindexRequest(BaseModel):
    collection: str = "personal"


class DeleteDocRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    confirm: bool = False


class GraphBuildRequest(BaseModel):
    collection: str | None = None


class GraphAskRequest(BaseModel):
    query: str = Field(..., min_length=1)


class ResearchCrewRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    collection: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)


class EvaluationCompareRequest(BaseModel):
    dataset: str = Field(..., min_length=1)
    config_a: dict = Field(default_factory=dict)
    config_b: dict = Field(default_factory=dict)


class EvaluationRunRequest(BaseModel):
    dataset: str = Field(..., min_length=1)
    engine: str = Field(default="builtin", pattern="^(builtin|ragas)$")


class StreamChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    collection: str | None = None
    mode: str = Field(default="react", pattern="^(planner|react)$")
    session_id: str = Field(default="default", min_length=1, max_length=120)


class AgentWorkspacePathRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)


class SettingsUpdateRequest(BaseModel):
    changes: dict = Field(...)
    confirm: bool = False


UPLOAD_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt", ".html", ".htm"}


def require_api_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    server_cfg = config.get("server", {})
    if not bool(server_cfg.get("api_auth_enabled", False)):
        return
    token_env = server_cfg.get("api_token_env", "PERSONAL_AI_API_TOKEN")
    expected = os.getenv(token_env)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API auth is enabled but {token_env} is not set.",
        )
    provided = x_api_key or _bearer_token(authorization)
    if provided != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API token.")


def _bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    prefix = "Bearer "
    if value.startswith(prefix):
        return value[len(prefix) :]
    return None


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "app": config["app"]["name"],
        "llm_backend": config.get("llm", {}).get("backend"),
        "embedding_backend": config.get("embedding", {}).get("backend"),
    }


@app.post("/rag/search")
def rag_search(payload: SearchRequest, _: None = Depends(require_api_token)) -> dict:
    return registry.call("search_kb", _dump_model(payload))


@app.post("/rag/ask")
def rag_ask(payload: AskRequest, _: None = Depends(require_api_token)) -> dict:
    return registry.call("ask_kb", _dump_model(payload))


@app.post("/rag/ask/stream")
def rag_ask_stream(payload: AskRequest, _: None = Depends(require_api_token)) -> StreamingResponse:
    def events():
        yield _sse("status", {"stage": "retrieving"})
        result = registry.call("ask_kb", _dump_model(payload))
        yield _sse("result", result)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/agent/run")
def agent_run(payload: AgentRunRequest, _: None = Depends(require_api_token)) -> dict:
    request = _dump_model(payload)
    original = config["agent"].get("execution_mode", "planner")
    if request.get("mode"):
        config["agent"]["execution_mode"] = request["mode"]
    try:
        if config["agent"].get("execution_mode") == "react":
            from src.agents.react_agent import ReActAgent

            return ReActAgent(registry).run(payload.goal, payload.session_id)
        return PersonalAssistantAgent(registry).run(payload.goal)
    finally:
        config["agent"]["execution_mode"] = original


@app.post("/agent/chat/stream")
def agent_chat_stream(payload: StreamChatRequest, _: None = Depends(require_api_token)) -> StreamingResponse:
    def events():
        yield _sse("status", {"stage": "planning", "mode": payload.mode})
        if payload.mode == "react":
            from src.agents.react_agent import ReActAgent

            result = ReActAgent(registry).run(payload.message, payload.session_id)
        else:
            result = PersonalAssistantAgent(registry).run(payload.message)
        yield _sse("result", result)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/kb/ingest")
def kb_ingest(payload: IngestRequest, _: None = Depends(require_api_token)) -> dict:
    return ingest_tool(config, _dump_model(payload))


@app.post("/kb/upload")
async def kb_upload(
    files: list[UploadFile] = File(...),
    collection: str = Form("personal", min_length=1, max_length=80),
    tags: str = Form("[]"),
    _: None = Depends(require_api_token),
) -> dict:
    """Persist browser uploads under data/raw before using the normal ingestion path."""
    from src.config.config_loader import resolve_project_path

    try:
        parsed_tags = json.loads(tags)
        if not isinstance(parsed_tags, list) or not all(isinstance(tag, str) for tag in parsed_tags):
            raise ValueError
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="tags must be a JSON array of strings.") from exc
    safe_collection = "".join(char for char in collection if char.isalnum() or char in {"-", "_"})
    if not safe_collection:
        raise HTTPException(status_code=422, detail="collection must include letters, numbers, '-' or '_'.")
    upload_root = resolve_project_path(config, config["app"]["data_dir"]) / "raw" / "uploads" / safe_collection
    upload_root.mkdir(parents=True, exist_ok=True)
    max_bytes = int(config.get("server", {}).get("upload_max_bytes", 100 * 1024 * 1024))
    saved: list[str] = []
    for uploaded in files:
        filename = Path(uploaded.filename or "").name
        suffix = Path(filename).suffix.lower()
        if not filename or suffix not in UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=415, detail=f"Unsupported upload type: {filename or 'unnamed'}")
        target = upload_root / f"{uuid.uuid4().hex[:8]}_{filename}"
        total = 0
        try:
            with target.open("wb") as output:
                while chunk := await uploaded.read(1024 * 1024):
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(status_code=413, detail=f"Upload exceeds {max_bytes} byte limit: {filename}")
                    output.write(chunk)
            saved.append(str(target))
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            await uploaded.close()
    documents: list[dict] = []
    for path in saved:
        documents.extend(ingest_tool(config, {"path": path, "collection": safe_collection, "tags": parsed_tags})["documents"])
    return {"success": True, "collection": safe_collection, "uploaded_files": len(saved), "documents": documents}


@app.get("/kb/docs")
def kb_docs(collection: str | None = None, _: None = Depends(require_api_token)) -> dict:
    return list_docs_tool(config, {"collection": collection})


@app.get("/kb/docs/{doc_id}")
def kb_document_detail(doc_id: str, chunk_limit: int = 20, _: None = Depends(require_api_token)) -> dict:
    from src.api.workbench_service import document_detail

    detail = document_detail(config, doc_id, max(1, min(chunk_limit, 100)))
    if detail is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return detail


@app.post("/kb/reindex")
def kb_reindex(payload: ReindexRequest, _: None = Depends(require_api_token)) -> dict:
    from pathlib import Path

    from src.indexing.chroma_store import delete_chroma_collection
    from src.indexing.index_manager import ingest_path
    from src.storage.sqlite_store import SQLiteStore

    store = SQLiteStore(config)
    docs = store.list_documents(payload.collection)
    paths = sorted({d["file_path"] for d in docs if d.get("file_path")})
    store.delete_collection(payload.collection)
    delete_chroma_collection(config, payload.collection)
    reindexed = []
    for path in paths:
        if Path(path).exists():
            reindexed.extend(ingest_path(config, path, payload.collection))
    return {"success": True, "collection": payload.collection, "source_documents": len(paths), "reindexed_documents": len(reindexed)}


@app.post("/kb/delete")
def kb_delete(payload: DeleteDocRequest, _: None = Depends(require_api_token)) -> dict:
    from src.indexing.chroma_store import delete_chroma_ids
    from src.storage.sqlite_store import SQLiteStore

    store = SQLiteStore(config)
    chunks = [c for c in store.get_chunks() if c.get("doc_id") == payload.doc_id]
    collection = chunks[0].get("collection") if chunks else None
    plan = {"operation": "delete_doc", "doc_id": payload.doc_id, "chunk_count": len(chunks), "collection": collection, "confirm": payload.confirm}
    if not payload.confirm:
        return {"success": True, "executed": False, "requires_confirmation": True, "plan": plan}
    delete_chroma_ids(config, collection, [c["chunk_id"] for c in chunks])
    store.delete_document(payload.doc_id)
    return {"success": True, "executed": True, "deleted": payload.doc_id, "plan": plan}


@app.post("/graph/build")
def graph_build(payload: GraphBuildRequest, _: None = Depends(require_api_token)) -> dict:
    from src.generation.factory import build_embedding_client, build_llm_client
    from src.graphrag.graph_index import NetworkXGraphIndex
    from src.storage.sqlite_store import SQLiteStore

    store = SQLiteStore(config)
    chunks = store.get_chunks(payload.collection)
    graph_cfg = config.get("graphrag", {})
    backend = str(graph_cfg.get("backend", "networkx")).lower()
    if backend == "lightrag":
        from src.graphrag.lightrag_adapter import LightRAGAdapter

        working_dir = Path(graph_cfg.get("working_dir", "./data/lightrag")).resolve()
        adapter = LightRAGAdapter(
            str(working_dir),
            build_llm_client(config),
            build_embedding_client(config),
            int(config.get("embedding", {}).get("dimension", 384)),
            str(config.get("embedding", {}).get("model_name", "mock-embedding")),
        )
        asyncio.run(adapter.index([str(chunk.get("text", "")) for chunk in chunks]))
        return {"success": True, "collection": payload.collection, "backend": "lightrag", "indexed_chunks": len(chunks)}
    return {"success": True, "collection": payload.collection, "backend": "networkx", **NetworkXGraphIndex(store).build(chunks, payload.collection)}


@app.post("/graph/ask")
def graph_ask(payload: GraphAskRequest, _: None = Depends(require_api_token)) -> dict:
    """Query the optional official LightRAG integration after a LightRAG graph build."""
    from src.generation.factory import build_embedding_client, build_llm_client
    from src.graphrag.lightrag_adapter import LightRAGAdapter

    graph_cfg = config.get("graphrag", {})
    if str(graph_cfg.get("backend", "networkx")).lower() != "lightrag":
        raise HTTPException(status_code=409, detail="Set graphrag.backend=lightrag before using /graph/ask.")
    adapter = LightRAGAdapter(
        str(Path(graph_cfg.get("working_dir", "./data/lightrag")).resolve()),
        build_llm_client(config),
        build_embedding_client(config),
        int(config.get("embedding", {}).get("dimension", 384)),
        str(config.get("embedding", {}).get("model_name", "mock-embedding")),
    )
    return {"success": True, "backend": "lightrag", "answer": asyncio.run(adapter.query(payload.query))}


@app.post("/agents/crew/run")
def research_crew_run(payload: ResearchCrewRequest, _: None = Depends(require_api_token)) -> dict:
    from src.multi_agent.research_crew import run_research_crew

    return run_research_crew(config, payload.topic, payload.collection, payload.top_k)


@app.post("/integrations/agent-workspace/organize")
def agent_workspace_organize(payload: AgentWorkspacePathRequest, _: None = Depends(require_api_token)) -> dict:
    from src.integrations.agent_workspace_bridge import run_file_organizer

    try:
        return run_file_organizer(config, payload.path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/integrations/agent-workspace/thesis-check")
def agent_workspace_thesis_check(payload: AgentWorkspacePathRequest, _: None = Depends(require_api_token)) -> dict:
    from src.integrations.agent_workspace_bridge import run_thesis_check

    try:
        return run_thesis_check(config, payload.path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/integrations/agent-workspace/read-papers")
def agent_workspace_read_papers(payload: AgentWorkspacePathRequest, _: None = Depends(require_api_token)) -> dict:
    from src.integrations.agent_workspace_bridge import run_paper_reading

    try:
        return run_paper_reading(config, payload.path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/integrations/mcp/doctor")
def mcp_doctor(_: None = Depends(require_api_token)) -> dict:
    from src.integrations.agent_workspace_bridge import run_mcp_doctor

    try:
        return run_mcp_doctor(config)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/evaluation/compare")
def evaluation_compare(payload: EvaluationCompareRequest, _: None = Depends(require_api_token)) -> dict:
    from src.evaluation.ab_testing import compare_configs

    return compare_configs(config, payload.dataset, payload.config_a, payload.config_b)


@app.post("/evaluation/run")
def evaluation_run(payload: EvaluationRunRequest, _: None = Depends(require_api_token)) -> dict:
    from src.evaluation.rag_evaluator import eval_rag
    from src.observability.trace_logger import log_event

    try:
        if payload.engine == "ragas":
            from src.evaluation.ragas_evaluator import eval_ragas

            report = eval_ragas(config, payload.dataset)
        else:
            report = eval_rag(config, payload.dataset)
        response = {"success": True, "engine": payload.engine, "dataset": payload.dataset, **report}
        log_event(config, "evaluation.jsonl", response)
        return response
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/llm/doctor")
def llm_doctor(_: None = Depends(require_api_token)) -> dict:
    return doctor_llm(config, call_api=False)


@app.get("/observability/logs")
def logs(category: str | None = None, limit: int = 50, _: None = Depends(require_api_token)) -> dict:
    from src.api.workbench_service import observability_events

    try:
        return observability_events(config, category, max(1, min(limit, 200)))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/dashboard/summary")
def dashboard(_: None = Depends(require_api_token)) -> dict:
    from src.api.workbench_service import dashboard_summary

    return dashboard_summary(config)


@app.get("/settings/public")
def settings_public(_: None = Depends(require_api_token)) -> dict:
    from src.api.workbench_service import public_settings

    return public_settings(config)


@app.post("/settings/update")
def settings_update(payload: SettingsUpdateRequest, _: None = Depends(require_api_token)) -> dict:
    from src.api.workbench_service import update_settings

    try:
        return update_settings(config, payload.changes, payload.confirm)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/agent/sessions/{session_id}/memory")
def agent_memory(session_id: str, _: None = Depends(require_api_token)) -> dict:
    from src.memory.memory_store import MemoryStore

    return {"success": True, "session_id": session_id, "memories": MemoryStore(config).list(session_id, limit=50)}


def _dump_model(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
