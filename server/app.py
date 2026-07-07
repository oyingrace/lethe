"""FastAPI server wrapping the Lethe SDK.

Phase 0 walking skeleton: /health proves the process is up, /qwen-check proves
a real Qwen completion round-trips through lethe.llms.qwen. If Qwen is
unreachable, /qwen-check reports degraded:true rather than raising — this is
the same graceful-degradation path search() will use once memory endpoints
land (BUILD_PLAN.md Phase 1-2).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from lethe.llms.qwen import QwenUnavailableError, complete

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Lethe", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/qwen-check")
def qwen_check() -> dict[str, object]:
    try:
        result = complete(
            "Reply with one short, cheerful sentence proving you're alive.",
            role="fast",
        )
    except QwenUnavailableError as exc:
        return {"degraded": True, "error": str(exc)}

    return {
        "degraded": False,
        "model": result.model,
        "text": result.text,
        "usage": {
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        },
    }
