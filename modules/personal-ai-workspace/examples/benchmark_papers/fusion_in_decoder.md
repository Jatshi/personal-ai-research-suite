# Leveraging Passage Retrieval with Generative Models for Open Domain QA

Source: https://arxiv.org/abs/2007.01282

Fusion-in-Decoder, commonly called FiD, encodes each retrieved passage together
with the question independently and fuses passage representations in the
decoder. It is a generative open-domain QA reader and can use many retrieved
passages. The paper evaluates Natural Questions and TriviaQA. FiD differs from
DPR: DPR focuses on retrieving passages, whereas FiD focuses on combining the
retrieved passages during generation.
