# Prior Art

Lethe intentionally follows the *shape* of mem0's developer experience —
SDK-first `Memory` class usable embedded or via a hosted REST server,
config-driven provider slots, docker-compose deployment, an MCP server, a
dashboard. That shape is a reasonable, by-now-conventional answer to "how
should a memory SDK feel to use." The algorithm, lifecycle model, audit
trail, and budget enforcement underneath it are original and are where Lethe
differs.

Zero code, prompts, or verbatim API signatures are copied from mem0, Zep, or
LangMem. This document is kept current as design changes — if a difference
below goes stale, that's a bug in this doc, not in the code.

## vs. mem0

| | mem0 | Lethe |
|---|---|---|
| Core algorithm | ADD-only; facts accumulate, nothing is revised or deleted | Reconcile-and-decay: every candidate fact resolves to ADD / REINFORCE / REVISE / DEPRECATE |
| Forgetting | Not a first-class concept | Confidence decay on category half-lives, status lifecycle (active → decaying → deprecated), TTL + hard delete |
| Audit | Not a first-class primitive | Every mutation writes a `memory_audit` row with a human-readable reason + before/after |
| Recall budget | Not enforced as a hard invariant | `search(budget_tokens=N)` never exceeds N tokens; reports included/cut/tokens_used |
| Model provider | Multi-provider | Qwen-native by design (DashScope OpenAI-compatible endpoint); 4 models orchestrated by role |

## vs. Zep

Zep leans on a temporal knowledge graph (entities/relations over time) for
recall. Lethe's Phase 1-5 scope is deliberately narrower and flatter — no
graph memory, no entity linking (see BUILD_PLAN.md §3 "OUT" list) — trading
that richness for a hard token budget, an explicit reconcile-and-decay
lifecycle, and a from-scratch audit trail as the primary differentiators
within hackathon scope.

## vs. LangMem

LangMem exposes memory as tools/hooks integrated into LangGraph agents rather
than as a standalone SDK-first product with its own REST/MCP/playground
surface. Lethe is provider-and-framework agnostic: any agent (Claude Code,
Qwen-based agents, custom loops) mounts it via the Python SDK, REST API, or
MCP server without adopting a specific agent framework.

## Why this matters for judging

The "isn't this just mem0?" question is expected. The rehearsed answer: same
DX shape by design (so it's immediately familiar to anyone who's used mem0),
different algorithm class (reconcile-and-decay vs add-only), with
lifecycle/audit/budget as first-class primitives rather than afterthoughts,
built Qwen-native from the ground up.
