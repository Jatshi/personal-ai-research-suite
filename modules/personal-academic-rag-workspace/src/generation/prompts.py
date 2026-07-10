ANSWER_PROMPT = """The application has already verified that the supplied evidence is sufficient.
Write a concise, factual answer using only those evidence chunks. Use the language of the question.
Include bracket citations such as [1] for every material claim. Do not say that evidence is insufficient.

Question: {query}
"""
