# Lethe — Build Plan

**A Qwen-native memory engine for AI agents. Full lifecycle: remember, reinforce,
revise, decay, forget — every mutation audited, every recall inside a token budget.**

- **Hackathon:** Global AI Hackathon Series with Qwen Cloud (Devpost) — Track 1: MemoryAgent
- **License:** MIT (public repo, license visible — submission requirement)

---

## 1. Positioning

Existing memory layers (mem0, Zep, LangMem) optimize for accumulation — mem0's current
algorithm is ADD-only; nothing is revised or deleted. Lethe treats memory as a
lifecycle: facts carry confidence and provenance, are reconciled against what's already
known, decay on category half-lives, and retire with auditable reasons. Recall is
packed into a hard token budget.

One-liner: **"Lethe remembers like the best of them — and it's the only one that knows
how to forget."**

**Architecture stance:** Lethe follows the proven *shape* of mem0's developer
experience — SDK-first `Memory` class usable embedded or via a hosted REST server,
config-driven provider slots, docker-compose deployment, MCP server, dashboard — with
an original codebase and a different core algorithm (reconcile-and-decay vs add-only).
Zero code/prompt/API-copying from mem0, Zep, or LangMem. docs/PRIOR_ART.md states the
similarities (shape) and differences (algorithm, lifecycle, audit, budget) explicitly.

## 2. Hard submission requirements

- [ ] Public GitHub repo + MIT LICENSE visible in About
- [ ] Backend deployed on Alibaba Cloud ECS + separate proof recording
      (SSH in → `docker ps` → curl live URL → show ECS console)
- [ ] Judge-linkable Qwen API code file → `lethe/llms/qwen.py`
- [ ] Architecture diagram (README + docs/architecture.png)
- [ ] ~3 min public demo video (YouTube)
- [ ] Devpost description naming Track 1
- [ ] Optional blog post (extra $500) — source from docs/DECISIONS.md

## 3. Feature set (locked)

### Remembering — the engine
1. **add() pipeline:** messages/text in → qwen-turbo extracts candidate facts
   {statement, category: preference|state|identity|episodic|constraint, confidence,
   provenance span}.
2. **Reconciliation:** qwen-max compares candidates vs existing memories →
   ADD / REINFORCE (confidence up, decay clock reset) / REVISE / DEPRECATE, each with
   a human-readable reason. Contradictions never coexist as active.
3. **Scoping:** user_id (required) + optional agent_id, session_id. Multi-tenant.
4. **Hybrid retrieval:** pgvector cosine + Postgres full-text, fused; ranked by
   similarity × confidence × recency; optional gte-rerank.
5. **Budget-packed recall:** search(query, budget_tokens=1500) greedy-packs ranked
   memories; response reports included / cut / tokens_used. Hard invariant, tested.
6. **History API:** history(memory_id) → every mutation with reason + before/after.

### Forgetting — the differentiator
7. **Confidence decay:** per-category half-lives (state=7d, preference=90d,
   identity=∞ default; configurable); scheduler tick decays unless reinforced.
8. **Status lifecycle:** active → decaying (excluded from recall, inspectable) →
   deprecated (retired, reason kept).
9. **Contradiction-triggered revision:** old belief deprecated with cited reason —
   never silently overwritten.
10. **TTL + hard delete:** expiry-on-write; true deletion for privacy (audit records
    the deletion event without content).
11. **Time machine (playground-only):** fast-forward the decay clock to demo
    forgetting in seconds.

### Interfaces — the mem0-shaped part
12. **Python SDK:** `Memory.from_config({...})` embedded mode with provider slots
    (llm/embedder/vector_store/reranker; Qwen defaults) + `LetheClient` for hosted
    server. Methods: add, search, get, get_all, update, delete, history, reset.
13. **REST server:** FastAPI wrapping the SDK; polished OpenAPI docs; one-command
    compose.
14. **MCP server:** lethe-mcp (stdio + SSE): remember / recall / revise / forget.
    Any MCP agent (Claude Code, Qwen agents) mounts Lethe in one command.
15. **Playground:** split screen — Qwen chat assistant left; live memory dashboard
    right (confidence bars, status colors, streaming audit log, per-turn recall
    budget meter).

### Platform & proof
16. **Qwen-native orchestration:** MODEL_FAST=extraction, MODEL_REASONING=
    reconciliation+chat, MODEL_EMBED=embeddings, MODEL_RERANK=gte-rerank; all via
    DashScope OpenAI-compatible endpoint; IDs only in env.
17. **Alibaba Cloud deployment:** single ECS, docker compose, deployed in Phase 0.
18. **Benchmark:** 3 multi-session personas whose facts CHANGE mid-history; metrics:
    cross-session accuracy, tokens/query, **staleness errors** vs baselines
    (no-memory; naive RAG-append). Staleness chart = headline result.
19. **Production hygiene:** single Qwen choke point (retries/timeouts/token log),
    graceful degradation (Qwen down → vector-only recall flagged degraded; add
    queued), reconciler golden test set, tests on decay math + budget invariant.

**OUT (roadmap slide):** graph memory, entity linking, TS SDK, multiple vector-store
backends, managed platform, integrations catalog.

## 4. Repo layout (mem0-shaped, original code)

```
lethe/                  # pip-installable SDK-first package
  __init__.py           # exposes Memory, LetheClient
  memory/main.py        # Memory class — the public embedded API
  configs/              # Pydantic: LlmConfig, EmbedderConfig, VectorStoreConfig,
                        #   RerankerConfig, LifecycleConfig (half-lives, thresholds)
  llms/qwen.py          # THE judge-proof file: all chat-model calls, retries,
                        #   timeouts, token logging
  embeddings/qwen.py    # text-embedding-v3, content-hash cache
  vector_stores/pgvector.py
  rerankers/gte.py      # optional; degrade gracefully if unavailable
  extraction/           # prompt + Pydantic contract + tests
  reconcile/            # prompt + decision contract + golden test set
  recall/               # hybrid retrieve, ranking, budget packer (+ invariant test)
  lifecycle/            # decay curves, scheduler, status transitions
  audit/                # audit writer; every mutation passes through here
server/                 # FastAPI REST wrapping lethe/; SSE stream for audit events
mcp/                    # lethe-mcp server
playground/             # Next.js 14 + Tailwind demo app
bench/                  # personas, baselines, report generator
deploy/                 # compose, Dockerfile, Caddyfile, DEPLOY.md, .env.example
docs/                   # ARCHITECTURE, MEMORY_LIFECYCLE, PRIOR_ART, DECISIONS, PROGRESS
```

## 5. Data model

```sql
memories(
  id uuid pk, user_id text not null, agent_id text, session_id text,
  statement text, category text, confidence float,
  status text default 'active',        -- active|decaying|deprecated
  evidence jsonb,                      -- provenance spans / prior memory ids
  half_life_days int, ttl_at timestamptz null,
  last_reinforced_at timestamptz, created_at timestamptz,
  embedding vector(1024), tsv tsvector
)
memory_audit(
  id bigserial pk, memory_id uuid, op text,   -- add|reinforce|revise|deprecate|decay|delete
  reason text, before jsonb, after jsonb,
  actor text,                                  -- system|user|agent
  created_at timestamptz
)
```

## 6. Build phases — DEPLOY FIRST

**Phase 0 (h0–4): Alibaba Cloud validated before anything else.**
Use deploy-starter/ (provided): provision ECS, install Docker, bring up the walking
skeleton (FastAPI /health + /qwen-check + Postgres/pgvector + optional Caddy), confirm
a real Qwen completion returns from the ECS box, push repo public with MIT license.
Exit criteria: `curl http://<ecs-ip>/qwen-check` returns a Qwen-generated sentence.
Record 30s of raw footage now as backup proof material. If ANY blocker appears
(account verification, coupon, region, endpoint reachability) you find out at hour 2,
not hour 46. Full steps in deploy/DEPLOY.md.

**Phase 1 (h4–16): the engine (features 1–11 core).**
Schema + alembic; extraction module + contract tests; reconciler + 15-case golden set
(add/reinforce/revise/contradiction/ambiguous); audit writer; decay scheduler +
half-life math tests; recall: hybrid retrieve → rank → packer + budget-invariant test;
TTL + hard delete.

**Phase 2 (h16–22): interfaces (12–14).**
Memory class + config system; LetheClient; REST server wrapping SDK with polished
OpenAPI; MCP server (stdio + SSE). Redeploy to ECS at end of phase (deploys are now
routine, not an event).

**Phase 3 (h22–34): playground (15) + degradation (19).**
Chat assistant using the SDK; dashboard with confidence bars, status colors, live
audit stream (SSE), per-turn recall panel with budget meter; time-machine control.
Degradation paths + tests. Redeploy.

**Phase 4 (h34–42): benchmark (18).**
Personas with mid-history fact changes; run vs both baselines; report.md + chart.png;
tune reconciler against golden set with findings.

**Phase 5 (h42–48): ship.**
Final deploy; proof recording; architecture diagram; README + docs complete; 3-min
video (script §8); Devpost submission; optional blog post.

## 7. Judging map

- **Technical depth 30%:** 4 Qwen models orchestrated by role; reconcile-and-decay
  algorithm (novel vs add-only SOTA); hard budget invariant; MCP server; hybrid
  retrieval + rerank; provider-slot config system.
- **Innovation & architecture 30%:** lifecycle + audit as first-class primitives;
  SDK-first layering (package/server/mcp/playground separable); golden-set-driven
  prompt engineering; degradation paths; tests on all novel logic.
- **Problem value 25%:** stale-memory bugs are universal in agent dev; pip-installable
  OSS infra with a clear adoption path; fills the Qwen ecosystem's missing native
  memory layer.
- **Presentation 15%:** dashboard visualizes the core logic by construction;
  staleness benchmark chart; strong API docs; architecture docs written per-phase.

## 8. Demo video script (3:00)

- 0:00–0:20 — "Agent memory today only grows. Stale facts pile up until your agent
  confidently describes a job you left last year. Lethe is memory with a lifecycle."
- 0:20–1:00 — Playground: share facts across two sessions; extraction and
  reconciliation decisions appear live with reasons.
- 1:00–1:40 — Contradict yourself ("actually, I moved to Abuja") → REVISE, old fact
  deprecated with reason. Time-machine +90 days → volatile facts decay, identity
  persists. Ask a question → recall panel shows budget packing (included vs cut).
- 1:40–2:10 — Mount Lethe into another agent live via MCP (one command). "Any agent,
  instant memory."
- 2:10–2:45 — Benchmark: staleness-error chart vs no-memory and RAG-append; tokens
  per query under a 1.5k budget.
- 2:45–3:00 — Architecture on Alibaba Cloud; roadmap (graph memory, TS SDK, managed
  platform); close on the one-liner.

## 9. Risks

- **"Isn't this mem0?"** Rehearsed answer: mem0-shaped DX by design, different
  algorithm class (reconcile-and-decay vs add-only), lifecycle/audit/budget as
  primitives, Qwen-native. PRIOR_ART.md documents it; zero code reuse.
- **$40 credits:** turbo for extraction, reasoning model only for reconcile + chat,
  embeddings cached, bench capped. Token log from hour 0 (it's in the skeleton).
- **Reconciler quality is make-or-break:** golden set exists from Phase 1; every bug
  becomes a new case.
- **ECS/account friction:** neutralized by Phase 0. If ECS is blocked outright,
  fallback: Alibaba Cloud SAE or a different region — decided at hour 2, not hour 46.
- **Infra demos flat:** playground + time machine are the answer; don't cut Phase 3
  polish.