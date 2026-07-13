# REALM: Retrieval-Augmented Language Model Pre-Training

Source: https://arxiv.org/abs/2002.08909

REALM jointly learns a retriever and a language model with latent knowledge
retrieval during pretraining. It retrieves documents from a large corpus to
help predict masked spans. The paper evaluates open-domain question answering,
including Natural Questions. REALM differs from DPR because retrieval is part
of language-model pretraining rather than only a supervised QA retriever.
