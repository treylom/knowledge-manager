"""Optional link-scoring adapters.

The public Knowledge Manager repo ships ONLY the interface + a disabled
NullAdapter. A semantic adapter adds a similarity signal to link scoring, but
the core (lib/link_scorer.py) works fully without any adapter — the public repo
has zero dependency on external search/embedding infrastructure.

To enable a semantic signal, set `linking.semantic_adapter` in km-config.json and
provide an implementation of `SemanticAdapter`. Reference (vault-search / graphrag)
implementations live outside this public repo by design.
"""
from .semantic import NullAdapter, SemanticAdapter, load_adapter

__all__ = ["SemanticAdapter", "NullAdapter", "load_adapter"]
