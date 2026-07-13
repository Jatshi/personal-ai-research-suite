# Dense Passage Retrieval for Open-Domain Question Answering

Source: https://arxiv.org/abs/2004.04906

DPR uses two independently encoded dense vectors: one for a question and one
for a Wikipedia passage. Retrieval is maximum inner-product search over passage
embeddings. The paper evaluates open-domain QA on Natural Questions, TriviaQA,
WebQuestions, and CuratedTREC. DPR is trained with positive passages and hard
negative passages. Its central contribution is an effective dense retriever for
open-domain question answering rather than a generative reader.
