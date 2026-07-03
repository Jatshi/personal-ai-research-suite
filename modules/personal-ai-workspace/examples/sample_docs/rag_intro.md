# RAG Introduction

Retrieval Augmented Generation, or RAG, combines search over a local knowledge base with answer generation. A reliable RAG system retrieves evidence chunks, builds citations, checks confidence, and refuses to answer when evidence is insufficient.

Hybrid retrieval combines BM25 keyword search and vector semantic search. BM25 is strong for exact terms such as dataset names, method names, and project identifiers. Vector search is useful when the query is semantically related but does not share the same words.

