# Corrective Retrieval Augmented Generation

Source: https://arxiv.org/abs/2401.15884

CRAG evaluates the quality of retrieved documents before generation. It can use
a lightweight retrieval evaluator to label evidence as correct, ambiguous, or
incorrect. For ambiguous or incorrect retrieval, CRAG can expand the query with
web search and decompose documents into smaller knowledge strips. Corrective
retrieval is a routing strategy: low-quality evidence should trigger correction
or refusal rather than unsupported generation.
