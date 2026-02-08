"""Tests for notetaking.summarizer — transcript parsing and summarize flow."""

import os
from unittest.mock import patch

import pytest

from notetaking.summarizer import summarize


@pytest.fixture
def transcript_file(tmp_path):
    """Create a temporary transcript file."""
    txt = tmp_path / "meeting_2025-01-01.txt"
    txt.write_text(
        "=== TRANSCRIPT ===\n"
        "Alice: Let's ship the feature by Friday.\n"
        "Bob: Sounds good, I'll update the tests.\n"
        "=== TIMESTAMPED SEGMENTS ===\n"
        "[00:00] Alice: Let's ship the feature by Friday.\n"
    )
    return txt


@pytest.fixture
def empty_transcript(tmp_path):
    txt = tmp_path / "empty.txt"
    txt.write_text("=== TRANSCRIPT ===\n\n=== TIMESTAMPED SEGMENTS ===\n")
    return txt


def test_empty_transcript_raises(empty_transcript):
    with pytest.raises(RuntimeError, match="Transcript is empty"):
        summarize(str(empty_transcript))


def test_summarize_calls_llm_and_writes_notes(transcript_file, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")

    with patch("notetaking.summarizer.call_llm", return_value="## Summary\nTest notes") as mock:
        path = summarize(str(transcript_file), provider="anthropic")

    mock.assert_called_once()
    args = mock.call_args
    assert args[0][0] == "anthropic"
    assert "meeting transcript" in args[0][2].lower()

    from pathlib import Path
    notes = Path(path)
    assert notes.exists()
    content = notes.read_text()
    assert "Meeting Notes" in content
    assert "Test notes" in content


def test_summarize_respects_provider_arg(transcript_file, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")

    with patch("notetaking.summarizer.call_llm", return_value="notes") as mock:
        summarize(str(transcript_file), provider="gemini")

    assert mock.call_args[0][0] == "gemini"
