# CLAUDE.md — Lethe

Qwen-native memory engine for AI agents. Full lifecycle: extract → reconcile →
reinforce/revise → decay → forget, all audited; recall always inside a hard token
budget. Hackathon sprint (Qwen Cloud Global AI Hackathon, Track 1). Read BUILD_PLAN.md
before any large task. Deadline is real: simple and working beats clever.

## Repo layout (SDK-first, mem0-shaped, original code)

```
lethe/                 pip package — public API is lethe.Memory / lethe.LetheClient
  memory/main.py       Memory class (add/search/get/get_all/update/delete/history/reset)
  configs/             Pydantic provider + lifecycle configs
  llms/qwen.py         ONLY place chat models are called (judge-visible proof file)
  embeddings/qwen.py   text-embedding-v3 + content-hash cache
  vector_stores/pgvector.py
  rerankers/gte.py     optional; feature-flagged
  extraction/  reconcile/  recall/  lifecycle/  audit/
server/                FastAPI REST wrapping the SDK; SSE audit stream
mcp/                   lethe-mcp (stdio + SSE)
playground/            Next.js demo: chat + live memory dashboard + time machine
bench/                 personas, baselines, report generator
deploy/                compose, Dockerfile, Caddyfile, DEPLOY.md, .env.example
docs/                  ARCHITECTURE, MEMORY_LIFECYCLE, PRIOR_ART, DECISIONS, PROGRESS
```

## Commands

- `make dev` — postgres+redis up, server --reload, playground dev
- `make test` — pytest; must stay green: reconciler golden set, decay math,
  budget-packer invariant, audit completeness
- `make bench` — writes bench/out/report.md + chart.png
- `make deploy` — sync + `docker compose up -d --build` on ECS (see deploy/DEPLOY.md)

## Deploy-first workflow

Phase 0 deploys the walking skeleton to Alibaba Cloud ECS BEFORE feature work; every
phase ends with a redeploy. If a change would break `docker compose up`, fix that
before continuing. The live URL must work at all times after hour 4.

## Qwen Cloud rules (hackathon requirement)

- openai SDK, base_url `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`,
  key `QWEN_API_KEY`. Model IDs ONLY via env: MODEL_REASONING, MODEL_FAST,
  MODEL_EMBED, MODEL_RERANK. Never hardcode model names.
- All chat-model calls go through `lethe/llms/qwen.py`: 3 retries expo backoff,
  timeouts, per-call token logging. Judges are pointed at this file — keep it clean.
- Budget $40 total: MODEL_FAST for extraction/classification; MODEL_REASONING only in
  reconciler + playground chat; embeddings cached by content hash; bench runs capped.

## Non-negotiable invariants

1. **No silent mutations.** Every change (add/reinforce/revise/deprecate/decay/ttl/
   delete) writes memory_audit with human-readable reason + before/after.
2. **Budget is hard.** search(budget_tokens=N) NEVER returns more than N tokens of
   memory content; response always reports included/cut/tokens_used. Invariant test
   exists — never weaken it.
3. **Contradictions never coexist as active.** Reconciler resolves or flags for
   clarification. Every reconciler bug becomes a new golden-set case.
4. **Graceful degradation.** Qwen unreachable → search serves vector-only with
   degraded:true; add enqueues for later reconciliation. Never 500 on provider
   failure.
5. **Originality.** mem0-shaped developer experience is intentional; copying code,
   prompts, or verbatim API signatures from mem0/Zep/LangMem is forbidden. Keep
   docs/PRIOR_ART.md current when design changes.

## Style

- Python: ruff, full type hints, routes thin / services own logic; every LLM
  structured output validated by a Pydantic model with one repair-retry then graceful
  skip (log, never crash).
- Playground: TS strict; React state only, no state libraries.
- Conventional commits, PR-sized (judges read history).
- Notable design decisions → one line each in docs/DECISIONS.md (blog-prize fuel).

## Current phase

Track BUILD_PLAN.md §6; update docs/PROGRESS.md checkboxes at each phase end.