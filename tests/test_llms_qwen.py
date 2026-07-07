from unittest.mock import MagicMock

import pytest

from lethe.llms import qwen


def test_model_for_missing_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_FAST", raising=False)

    with pytest.raises(qwen.QwenUnavailableError):
        qwen._model_for("fast")


def test_complete_missing_api_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.setenv("MODEL_FAST", "qwen-turbo")

    sleep_calls = []
    monkeypatch.setattr(qwen.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    with pytest.raises(qwen.QwenUnavailableError):
        qwen.complete("hello", role="fast")

    assert sleep_calls == []


def test_complete_retries_transient_error_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_FAST", "qwen-turbo")
    monkeypatch.setattr(qwen.time, "sleep", lambda seconds: None)

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "hi there"
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 3
    mock_response.usage.total_tokens = 8

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        qwen.APITimeoutError(request=MagicMock()),
        mock_response,
    ]
    monkeypatch.setattr(qwen, "_client", lambda: mock_client)

    result = qwen.complete("hello", role="fast")

    assert result.text == "hi there"
    assert result.model == "qwen-turbo"
    assert result.usage.total_tokens == 8
    assert mock_client.chat.completions.create.call_count == 2


def test_complete_raises_after_exhausting_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_FAST", "qwen-turbo")
    monkeypatch.setattr(qwen.time, "sleep", lambda seconds: None)

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = qwen.APITimeoutError(request=MagicMock())
    monkeypatch.setattr(qwen, "_client", lambda: mock_client)

    with pytest.raises(qwen.QwenUnavailableError):
        qwen.complete("hello", role="fast")

    assert mock_client.chat.completions.create.call_count == qwen.MAX_RETRIES
