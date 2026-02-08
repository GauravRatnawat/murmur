"""Tests for notetaking.llm — provider dispatch logic."""

import os
from unittest.mock import MagicMock, patch

import pytest

from notetaking.llm import PROVIDERS, call_llm


def test_providers_dict_has_all_expected():
    expected = {"anthropic", "openai", "gemini", "groq", "ollama"}
    assert set(PROVIDERS.keys()) == expected


def test_each_provider_has_correct_tuple_shape():
    for name, entry in PROVIDERS.items():
        assert len(entry) == 3, f"{name}: expected (func, env_var, pip_package)"
        func, env_var, pip_package = entry
        assert callable(func)
        assert isinstance(pip_package, str)
        assert env_var is None or isinstance(env_var, str)


def test_ollama_requires_no_api_key():
    _, env_var, _ = PROVIDERS["ollama"]
    assert env_var is None


def test_unknown_provider_raises():
    with pytest.raises(RuntimeError, match="Unknown provider 'bogus'"):
        call_llm("bogus", "sys", "msg")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY not set"):
        call_llm("openai", "sys", "msg")


def test_missing_sdk_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")

    with patch.dict("sys.modules", {"groq": None}):
        with pytest.raises(RuntimeError, match="pip install groq"):
            call_llm("groq", "sys", "msg")


def test_call_anthropic_dispatches(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="mocked response")]
    )

    with patch("anthropic.Anthropic", return_value=mock_client) as mock_cls:
        result = call_llm("anthropic", "system prompt", "user message")

    assert result == "mocked response"
    mock_cls.assert_called_once_with(api_key="fake-key")
    mock_client.messages.create.assert_called_once()


def test_provider_name_case_insensitive():
    """call_llm lowercases the provider name."""
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
        # Would fail on key check, not on "unknown provider"
        os.environ.pop("ANTHROPIC_API_KEY", None)
        call_llm("Anthropic", "sys", "msg")
