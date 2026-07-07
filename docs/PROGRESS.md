# Progress

Tracks BUILD_PLAN.md §6. Checked at each phase end.

## Phase 0 (h0-4): Alibaba Cloud validated before anything else

- [x] Repo scaffolding: SDK-first layout (`lethe/`, `server/`, `deploy/`, `docs/`, stubs for `mcp/`, `bench/`)
- [x] `lethe/llms/qwen.py` — the judge-proof Qwen choke point (retries, timeout, token logging)
- [x] FastAPI walking skeleton: `/health`, `/qwen-check` (graceful degradation, never 500s)
- [x] docker-compose: Postgres+pgvector, Redis, server; optional Caddy profile
- [x] `deploy/DEPLOY.md`, `.env.example`
- [x] MIT LICENSE
- [x] Tests: health, qwen-check degraded path, qwen.py retry/backoff/fail-fast
- [ ] **Exit criteria: `curl http://<ecs-ip>/qwen-check` returns a real Qwen sentence from an actual ECS instance.** Blocked in this session on missing `QWEN_API_KEY` and Alibaba Cloud ECS access — verified locally instead (degraded-path tests pass; docker-compose config validated). Needs a run with real credentials to close out.
- [ ] Public GitHub repo pushed with MIT license visible in About
- [ ] 30s raw footage of the ECS `/qwen-check` proof recorded as backup material

## Phase 1 (h4-16): the engine

- [ ] Schema + alembic migrations
- [ ] Extraction module + contract tests
- [ ] Reconciler + 15-case golden set (add/reinforce/revise/contradiction/ambiguous)
- [ ] Audit writer
- [ ] Decay scheduler + half-life math tests
- [ ] Recall: hybrid retrieve → rank → budget packer + invariant test
- [ ] TTL + hard delete

## Phase 2 (h16-22): interfaces

- [ ] `Memory` class + config system, `LetheClient`
- [ ] REST server wrapping SDK with polished OpenAPI
- [ ] MCP server (stdio + SSE)
- [ ] Redeploy to ECS

## Phase 3 (h22-34): playground + degradation

- [ ] Chat assistant using the SDK
- [ ] Dashboard: confidence bars, status colors, live audit stream, budget meter
- [ ] Time-machine control
- [ ] Degradation paths + tests
- [ ] Redeploy

## Phase 4 (h34-42): benchmark

- [ ] Personas with mid-history fact changes
- [ ] Run vs. no-memory and naive RAG-append baselines
- [ ] `bench/out/report.md` + `chart.png`
- [ ] Tune reconciler against golden set

## Phase 5 (h42-48): ship

- [ ] Final deploy
- [ ] Proof recording
- [ ] Architecture diagram (`docs/architecture.png`)
- [ ] README + docs complete
- [ ] 3-min demo video
- [ ] Devpost submission
- [ ] Optional blog post
