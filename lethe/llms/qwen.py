"""The single choke point for every chat-model call in Lethe.

Extraction, reconciliation, and playground chat all call `complete()` here —
nothing else in the codebase is allowed to touch an LLM client directly. This
keeps retries, timeouts, and token logging in one judge-visible place, and
means graceful degradation (invariant #4: Qwen down -> vector-only recall,
never a 500) only has to be implemented once.

Model IDs are never hardcoded: MODEL_FAST and MODEL_REASONING come from the
environment so the same code runs against any DashScope-compatible model.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Literal

from openai import APIError, APITimeoutError, OpenAI

logger = logging.getLogger("lethe.llms.qwen")

DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

Role = Literal["fast", "reasoning"]

MAX_RETRIES = 3
TIMEOUT_SECONDS = 30.0
BACKOFF_BASE_SECONDS = 1.0

_ROLE_ENV_VAR: dict[Role, str] = {
    "fast": "MODEL_FAST",
    "reasoning": "MODEL_REASONING",
}


class QwenUnavailableError(RuntimeError):
    """Raised when Qwen is misconfigured or unreachable after all retries."""


@dataclass(frozen=True)
class QwenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class QwenCompletion:
    text: str
    model: str
    usage: QwenUsage


def _client() -> OpenAI:
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        raise QwenUnavailableError("QWEN_API_KEY is not set")
    return OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL, timeout=TIMEOUT_SECONDS)


def _model_for(role: Role) -> str:
    env_var = _ROLE_ENV_VAR[role]
    model = os.environ.get(env_var)
    if not model:
        raise QwenUnavailableError(f"{env_var} is not set")
    return model


def complete(
    prompt: str,
    *,
    role: Role = "fast",
    system: str | None = None,
    temperature: float = 0.0,
) -> QwenCompletion:
    """Call a Qwen chat model and return its text plus token usage.

    `role` picks the model tier per the budget in CLAUDE.md: "fast" (MODEL_FAST)
    for extraction/classification, "reasoning" (MODEL_REASONING) for the
    reconciler and playground chat. Missing configuration (no API key, no model
    env var) fails immediately; only actual API errors are retried, up to
    MAX_RETRIES with exponential backoff.
    """
    model = _model_for(role)
    client = _client()

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            usage = response.usage
            result = QwenCompletion(
                text=response.choices[0].message.content or "",
                model=model,
                usage=QwenUsage(
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                ),
            )
            logger.info(
                "qwen.complete role=%s model=%s attempt=%d prompt_tokens=%d "
                "completion_tokens=%d total_tokens=%d",
                role,
                model,
                attempt + 1,
                result.usage.prompt_tokens,
                result.usage.completion_tokens,
                result.usage.total_tokens,
            )
            return result
        except (APIError, APITimeoutError) as exc:
            last_error = exc
            logger.warning(
                "qwen.complete failed role=%s model=%s attempt=%d/%d error=%s",
                role,
                model,
                attempt + 1,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))

    raise QwenUnavailableError(f"Qwen API unreachable after {MAX_RETRIES} attempts") from last_error
