# Lethe

**A Qwen-native memory engine for AI agents. Full lifecycle: remember,
reinforce, revise, decay, forget — every mutation audited, every recall
inside a hard token budget.**

> Lethe remembers like the best of them — and it's the only one that knows
> how to forget.

Built for the Qwen Cloud Global AI Hackathon (Track 1: MemoryAgent). Existing
memory layers (mem0, Zep, LangMem) optimize for accumulation — facts only get
added, never revised or retired. Lethe treats memory as a lifecycle: facts
carry confidence and provenance, get reconciled against what's already known,
decay on category half-lives, and retire with an auditable reason. See
[docs/PRIOR_ART.md](docs/PRIOR_ART.md) for the detailed comparison.

## Status

This is a hackathon sprint in progress — see [BUILD_PLAN.md](BUILD_PLAN.md)
for the full plan and [docs/PROGRESS.md](docs/PROGRESS.md) for what's done.
Right now only the **Phase 0 walking skeleton** exists: a FastAPI server with
health/Qwen-connectivity checks, Postgres+pgvector and Redis wired up via
docker-compose, and the single choke point (`lethe/llms/qwen.py`) all chat
model calls will go through. The actual memory engine (extraction,
reconciliation, decay, recall) lands in Phase 1.

## Architecture

```
lethe/      pip-installable SDK — public API is lethe.Memory / lethe.LetheClient
server/     FastAPI REST wrapping the SDK; SSE audit stream (Phase 2+)
mcp/        lethe-mcp: stdio + SSE MCP server (Phase 2)
playground/ Next.js chat + live memory dashboard + time machine (Phase 3)
bench/      personas, baselines, staleness report (Phase 4)
deploy/     docker-compose, Dockerfile, Caddyfile, DEPLOY.md
docs/       architecture, memory lifecycle, prior art, decisions, progress
```

A full diagram lands in `docs/architecture.png` once the engine exists; see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current text version.

## Quickstart (local dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[server,dev]"

cp deploy/.env.example deploy/.env
# fill in QWEN_API_KEY (get one from the Alibaba Cloud Model Studio console)

make dev     # postgres + redis up, FastAPI with --reload on :8000
```

Then:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/qwen-check
```

`/qwen-check` returns `{"degraded": false, ...}` with a real Qwen completion
once `QWEN_API_KEY` is set, or `{"degraded": true, "error": "..."}` if Qwen is
unreachable — the server never 500s on a provider failure (see invariant #4
in [CLAUDE.md](CLAUDE.md)).

## Testing

```bash
make test    # pytest
make lint    # ruff check
```

## Deploying

See [deploy/DEPLOY.md](deploy/DEPLOY.md) for provisioning an Alibaba Cloud
ECS instance and bringing the stack up with `docker compose`.

## Qwen models

All chat-model calls go through `lethe/llms/qwen.py` against DashScope's
OpenAI-compatible endpoint. Model IDs are only ever read from the
environment — `MODEL_FAST`, `MODEL_REASONING`, `MODEL_EMBED`, `MODEL_RERANK`
— never hardcoded.

## License

MIT — see [LICENSE](LICENSE).
