"""Lethe: a Qwen-native memory engine for AI agents.

Public API: `lethe.Memory` (embedded SDK) and `lethe.LetheClient` (hosted REST
client). Both are stubs in the Phase 0 walking skeleton — see BUILD_PLAN.md
Phase 1-2 for the engine and interfaces that back them.
"""

from __future__ import annotations

__all__ = ["Memory", "LetheClient"]


class Memory:
    """Embedded SDK entrypoint. Lands in BUILD_PLAN.md Phase 1-2."""

    @classmethod
    def from_config(cls, config: dict) -> Memory:
        raise NotImplementedError("Memory.from_config lands in BUILD_PLAN.md Phase 1-2")


class LetheClient:
    """Hosted REST client. Lands in BUILD_PLAN.md Phase 2."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        raise NotImplementedError("LetheClient lands in BUILD_PLAN.md Phase 2")
