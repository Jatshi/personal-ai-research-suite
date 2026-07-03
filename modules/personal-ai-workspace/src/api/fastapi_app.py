from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from src.agents.personal_assistant_agent import PersonalAssistantAgent
from src.cli import doctor_llm
from src.config.config_loader import load_config
from src.tools.default_registry import build_registry
from src.tools.kb_tools import ingest_tool, list_docs_tool

config = load_config()
registry = build_registry(config)
app = FastAPI(title="personal-ai-workspace")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str | None = None
    mode: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1)


class IngestRequest(BaseModel):
    path: str = Field(..., min_length=1)
    collection: str = "personal"
    tags: list[str] = []


class ReindexRequest(BaseModel):
    collection: str = "personal"


class DeleteDocRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    confirm: bool = False


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


@app.post("/agent/run")
def agent_run(payload: AgentRunRequest, _: None = Depends(require_api_token)) -> dict:
    return PersonalAssistantAgent(registry).run(payload.goal)


@app.post("/kb/ingest")
def kb_ingest(payload: IngestRequest, _: None = Depends(require_api_token)) -> dict:
    return ingest_tool(config, _dump_model(payload))


@app.get("/kb/docs")
def kb_docs(collection: str | None = None, _: None = Depends(require_api_token)) -> dict:
    return list_docs_tool(config, {"collection": collection})


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


@app.get("/llm/doctor")
def llm_doctor(_: None = Depends(require_api_token)) -> dict:
    return doctor_llm(config, call_api=False)


@app.get("/observability/logs")
def logs(_: None = Depends(require_api_token)) -> dict:
    from src.observability.trace_logger import JsonlLogger

    return {"tool_calls": JsonlLogger(config, "tool_calls.jsonl").tail(50)}


def _dump_model(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)
