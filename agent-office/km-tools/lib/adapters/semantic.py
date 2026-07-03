"""SemanticAdapter interface for the optional link-scoring similarity signal.

Design SoT: Knowledge-Manager 고도화 설계 v1 (2026-07-03) §4.

Contract (kept intentionally minimal so any backend can implement it):
    similarity(target, candidate) -> float | None   # 0..1 cosine-like, None = n/a
    is_available() -> bool                            # False => core heuristic only

The public repo provides only this Protocol + a disabled NullAdapter. A real
backend (e.g. a vault-search / embedding server) is configured via km-config.json
and lives outside this repo. If config is unset or the backend is unreachable,
`load_adapter` returns NullAdapter and link scoring falls back to the stdlib core.
"""
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class SemanticAdapter(Protocol):
    def similarity(self, target: dict, candidate: dict) -> Optional[float]:
        """Return a 0..1 similarity between two notes, or None if unavailable."""
        ...

    def is_available(self) -> bool:
        """True only when the backend is configured AND reachable."""
        ...


class NullAdapter:
    """Default adapter — always disabled. Core heuristic scoring only."""

    def similarity(self, target: dict, candidate: dict) -> Optional[float]:
        return None

    def is_available(self) -> bool:
        return False


def load_adapter(config: Optional[dict] = None) -> "SemanticAdapter":
    """Resolve an adapter from config, or NullAdapter when unset/unavailable.

    config = the `linking` block of km-config.json, e.g.
        {"semantic_adapter": {"type": "vault-search", "endpoint": "..."}}
    Unset / unknown type / import failure -> NullAdapter (core-only). This keeps
    the public repo self-contained: no adapter config == pure stdlib scoring.
    """
    if not config:
        return NullAdapter()
    spec = config.get("semantic_adapter")
    if not spec or not spec.get("type"):
        return NullAdapter()
    adapter_type = str(spec.get("type"))
    try:
        # Adapters are looked up by convention: lib/adapters/impl_<type>.py exposing
        # `build(spec) -> SemanticAdapter`. Reference impls are not shipped publicly.
        import importlib

        mod = importlib.import_module(
            f".impl_{adapter_type.replace('-', '_')}", package=__package__
        )
        adapter = mod.build(spec)
        return adapter if adapter and adapter.is_available() else NullAdapter()
    except Exception:
        # Any resolution failure => fall back to core-only (never break scoring).
        return NullAdapter()
