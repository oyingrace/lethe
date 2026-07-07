# Decisions

One line each, newest last. Source material for the optional blog post.

- Used the `openai` Python SDK against DashScope's OpenAI-compatible endpoint
  (`base_url` override) instead of Alibaba's native SDK, for portability and
  because every future dev already knows the `openai` client shape.
- `lethe/llms/qwen.py` fails fast (no retry) on configuration errors (missing
  `QWEN_API_KEY` or model env var) and only retries actual API-layer errors
  (`APIError`/`APITimeoutError`) — retrying a config error would just burn
  three timeouts for a problem that will never fix itself.
- `/qwen-check` returns `{"degraded": true, "error": ...}` with a 200 instead
  of a 5xx when Qwen is unreachable, establishing the graceful-degradation
  response shape `search()` will reuse in Phase 1 (invariant #4).
- Redis is provisioned in `docker-compose.yml` from Phase 0 even though
  nothing consumes it yet, so the lifecycle decay scheduler (Phase 1) has
  infra ready rather than retrofitted.
- Chose distribution name `lethe-memory` for `pyproject.toml` (PyPI name)
  while keeping the importable package name `lethe`, since the short name is
  the one users actually type (`import lethe`).
