# Architecture

_A rendered diagram lands in `docs/architecture.png` once the Phase 1 engine
exists. This is the text version, kept current as phases land._

## Current state (Phase 0)

```
                        ┌──────────────────────┐
   curl /health ───────▶│                      │
   curl /qwen-check ───▶│   server/app.py      │
                        │   (FastAPI)          │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  lethe/llms/qwen.py  │──▶ DashScope (OpenAI-compatible)
                        │  (the only Qwen      │      MODEL_FAST / MODEL_REASONING
                        │   choke point)       │
                        └──────────────────────┘

   ┌─────────────┐   ┌─────────┐
   │  postgres   │   │  redis  │      (brought up via docker-compose;
   │  +pgvector  │   │         │       not yet wired into the app —
   └─────────────┘   └─────────┘       Phase 1 adds schema + scheduler)
```

## Target shape (post Phase 2)

```
                                    ┌────────────────────────────┐
                                    │        playground          │
                                    │  (Next.js: chat + dashboard│
                                    │   + time machine)          │
                                    └──────────────┬─────────────┘
                                                   │ REST / SSE
                                                   ▼
   MCP agents ──▶ mcp/ (lethe-mcp) ──▶ ┌────────────────────────────┐
                                       │      server/ (FastAPI)     │
                                       │  wraps lethe/ SDK, SSE     │
                                       │  audit stream              │
                                       └──────────────┬─────────────┘
                                                       ▼
                                       ┌────────────────────────────┐
                                       │        lethe/ SDK          │
                                       │  Memory.add/search/get/... │
                                       │                             │
                                       │  extraction → reconcile     │
                                       │  → audit → lifecycle/decay  │
                                       │  → recall (hybrid + budget) │
                                       └───────┬──────────┬──────────┘
                                               │          │
                                               ▼          ▼
                                    postgres+pgvector   lethe/llms/qwen.py
                                    (memories, audit,        │
                                     tsvector, embeddings)   ▼
                                                        DashScope (Qwen)
```

## Key design points

- **Single Qwen choke point.** `lethe/llms/qwen.py` is the only file that
  constructs an LLM client. Retries (3x expo backoff), timeouts, and per-call
  token logging live there once; every caller (extraction, reconciler,
  playground chat) gets them for free.
- **Reconcile-and-decay, not add-only.** New candidate facts are compared
  against existing memories and resolved to ADD / REINFORCE / REVISE /
  DEPRECATE with a human-readable reason — never silently appended.
- **Hard budget invariant.** `search(query, budget_tokens=N)` never returns
  more than N tokens of memory content; the response always reports
  included/cut/tokens_used.
- **Everything audited.** Every mutation (add/reinforce/revise/deprecate/
  decay/ttl/delete) writes a `memory_audit` row with a reason and
  before/after state.
- **Graceful degradation.** If Qwen is unreachable, `search()` falls back to
  vector-only recall flagged `degraded: true`; `add()` enqueues for later
  reconciliation. The server never 500s on a provider failure — see
  `/qwen-check` for the pattern this generalizes from.

See [MEMORY_LIFECYCLE.md](MEMORY_LIFECYCLE.md) for the state machine and
[PRIOR_ART.md](PRIOR_ART.md) for how this differs from mem0/Zep/LangMem.
