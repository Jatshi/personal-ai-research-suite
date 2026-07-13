# Attention Is All You Need

Source: https://arxiv.org/abs/1706.03762

The Transformer replaces recurrence and convolution with self-attention. The
paper evaluates machine translation on WMT 2014 English-to-German and
English-to-French. The base Transformer reports 27.3 BLEU on English-to-German;
the big model reports 28.4 BLEU on English-to-German and 41.8 BLEU on
English-to-French. Multi-head attention lets the model attend to information
from different representation subspaces. Positional encodings provide order
information because self-attention alone is permutation invariant.
