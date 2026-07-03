# Neuro-Symbolic RAG for Complex Acoustic Scene Understanding

Authors: Jian Example, Mei Researcher

Abstract: This paper studies retrieval augmented generation for complex acoustic scene understanding. The research question is how to combine semantic evidence, keyword evidence, and grounded citations for reliable academic question answering.

Keywords: retrieval augmented generation, acoustic scene, hybrid search, citation grounding

2026 Workshop on Local Academic AI

## Introduction

Complex acoustic scenes contain overlapping targets, environmental noise, and time-varying events. A personal academic assistant should retrieve evidence from papers, notes, and thesis materials.

## Related Work

Prior work studies vector search, BM25 keyword retrieval, and reranking. Many systems lack citation-level grounding.

## Method

The method builds document chunks with page or paragraph metadata, computes mock embeddings, indexes chunks in a local vector store, and fuses semantic scores with BM25 scores. A rule reranker combines keyword coverage, vector similarity, and filename matches.

## Experiments

The demonstration dataset contains Markdown notes, text notes, and simulated academic papers. Evaluation uses retrieval relevance, citation traceability, and evidence sufficiency.

## Discussion

The limitation is that the mock model cannot perform deep reasoning. Future work can replace mock embeddings with OpenAI, SentenceTransformers, or local embedding models.

## Conclusion

Hybrid retrieval and explicit evidence checking improve reliability for local academic RAG systems.

## References

[1] Example reference about RAG.

