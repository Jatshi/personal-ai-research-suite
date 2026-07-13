# Precise Zero-Shot Dense Retrieval without Relevance Labels

Source: https://arxiv.org/abs/2212.10496

HyDE stands for Hypothetical Document Embeddings. For a query, an instruction
following language model generates a hypothetical relevant document; a dense
encoder embeds that document and retrieves real corpus documents near it. HyDE
is a zero-shot dense retrieval method and is evaluated on the BEIR benchmark.
It does not treat the generated hypothetical document as evidence: it is only a
search representation used to improve recall without relevance labels.
