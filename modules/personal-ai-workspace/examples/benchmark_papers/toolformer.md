# Toolformer: Language Models Can Teach Themselves to Use Tools

Source: https://arxiv.org/abs/2302.04761

Toolformer teaches a language model when and how to call external APIs using
self-supervised examples. The paper studies calculator, question-answering,
search, translation, and calendar tools. Tool calls are inserted into text and
their outputs become context for subsequent prediction. In a production agent,
the model proposal must still be checked by a local tool schema and safety
policy before execution.
