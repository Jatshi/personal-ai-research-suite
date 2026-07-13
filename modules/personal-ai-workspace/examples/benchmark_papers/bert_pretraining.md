# BERT: Pre-training of Deep Bidirectional Transformers

Source: https://arxiv.org/abs/1810.04805

BERT is a bidirectional Transformer encoder pretrained with masked language
modeling and next sentence prediction. It is fine-tuned with a small
task-specific output layer. The paper reports results on GLUE, SQuAD 1.1,
SQuAD 2.0, and SWAG. Masked language modeling predicts masked tokens from both
left and right context. The next sentence prediction objective models whether
two segments were adjacent in the original corpus.
