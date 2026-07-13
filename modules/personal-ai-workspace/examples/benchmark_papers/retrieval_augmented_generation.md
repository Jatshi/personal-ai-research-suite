# Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

Source: https://arxiv.org/abs/2005.11401

RAG combines a pretrained sequence-to-sequence generator with a dense Wikipedia
retriever. It introduces RAG-Sequence, which conditions a whole generated
sequence on the same retrieved passages, and RAG-Token, which can use different
passages for different generated tokens. The paper evaluates knowledge-intensive
generation and open-domain QA including Natural Questions, WebQuestions, and
TriviaQA. Retrieved documents make model knowledge updateable and provide an
evidence path, but retrieval errors can propagate to generation.
