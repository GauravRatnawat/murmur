"""Tests for notetaking.summarizer — transcript parsing and summarize flow."""

import os
from unittest.mock import call, patch

import pytest

from notetaking.summarizer import _sanitize_slug, summarize


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

    assert mock.call_args_list[0][0][0] == "gemini"


class TestSmartNaming:
    """Tests for smart file naming after summarization."""

    def _setup_meeting_files(self, tmp_path, stem="meeting_20260208_120000"):
        """Create fake recording, transcript, and set up dirs."""
        recordings = tmp_path / "recordings"
        transcripts = tmp_path / "transcripts"
        notes = tmp_path / "notes"
        recordings.mkdir()
        transcripts.mkdir()
        notes.mkdir()

        recording = recordings / f"{stem}.wav"
        recording.write_bytes(b"fake wav")

        transcript = transcripts / f"{stem}.txt"
        transcript.write_text(
            "=== TRANSCRIPT ===\n"
            "Alice: Let's review the Q1 product roadmap.\n"
            "Bob: Sounds good.\n"
        )

        return recordings, transcripts, notes, transcript

    def test_smart_naming_renames_all_files(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
        recordings, transcripts, notes, transcript = self._setup_meeting_files(tmp_path)

        monkeypatch.setattr("notetaking.summarizer.RECORDINGS_DIR", recordings)
        monkeypatch.setattr("notetaking.summarizer.TRANSCRIPTS_DIR", transcripts)
        monkeypatch.setattr("notetaking.summarizer.NOTES_DIR", notes)

        def fake_llm(provider, system, user):
            if "kebab-case" in system:
                return "q1-product-roadmap-review"
            return "## Summary\nReviewed Q1 roadmap."

        with patch("notetaking.summarizer.call_llm", side_effect=fake_llm):
            result = summarize(str(transcript), provider="anthropic")

        new_stem = "20260208_120000_q1-product-roadmap-review"
        assert result == str(notes / f"{new_stem}.md")
        assert (notes / f"{new_stem}.md").exists()
        assert (transcripts / f"{new_stem}.txt").exists()
        assert (recordings / f"{new_stem}.wav").exists()

        # Old files should be gone
        assert not (notes / "meeting_20260208_120000.md").exists()
        assert not (transcripts / "meeting_20260208_120000.txt").exists()
        assert not (recordings / "meeting_20260208_120000.wav").exists()

    def test_smart_naming_fallback_on_slug_failure(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
        recordings, transcripts, notes, transcript = self._setup_meeting_files(tmp_path)

        monkeypatch.setattr("notetaking.summarizer.RECORDINGS_DIR", recordings)
        monkeypatch.setattr("notetaking.summarizer.TRANSCRIPTS_DIR", transcripts)
        monkeypatch.setattr("notetaking.summarizer.NOTES_DIR", notes)

        call_count = 0

        def fake_llm(provider, system, user):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "## Summary\nSome notes."
            # Second call (slug generation) fails
            raise RuntimeError("API error")

        with patch("notetaking.summarizer.call_llm", side_effect=fake_llm):
            result = summarize(str(transcript), provider="anthropic")

        old_stem = "meeting_20260208_120000"
        assert result == str(notes / f"{old_stem}.md")
        assert (notes / f"{old_stem}.md").exists()
        assert (transcripts / f"{old_stem}.txt").exists()
        assert (recordings / f"{old_stem}.wav").exists()

    def test_smart_naming_skips_missing_files(self, tmp_path, monkeypatch):
        """Only renames files that exist (e.g., no recording)."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
        recordings, transcripts, notes, transcript = self._setup_meeting_files(tmp_path)

        # Remove the recording
        (recordings / "meeting_20260208_120000.wav").unlink()

        monkeypatch.setattr("notetaking.summarizer.RECORDINGS_DIR", recordings)
        monkeypatch.setattr("notetaking.summarizer.TRANSCRIPTS_DIR", transcripts)
        monkeypatch.setattr("notetaking.summarizer.NOTES_DIR", notes)

        def fake_llm(provider, system, user):
            if "kebab-case" in system:
                return "standup-sync"
            return "## Summary\nNotes."

        with patch("notetaking.summarizer.call_llm", side_effect=fake_llm):
            result = summarize(str(transcript), provider="anthropic")

        new_stem = "20260208_120000_standup-sync"
        assert (notes / f"{new_stem}.md").exists()
        assert (transcripts / f"{new_stem}.txt").exists()
        assert not (recordings / f"{new_stem}.wav").exists()  # was never there


class TestSanitizeSlug:
    def test_basic(self):
        assert _sanitize_slug("product-roadmap-review") == "product-roadmap-review"

    def test_strips_whitespace_and_lowercases(self):
        assert _sanitize_slug("  Product-Review  ") == "product-review"

    def test_removes_special_chars(self):
        assert _sanitize_slug("hello_world!@#") == "helloworld"

    def test_collapses_multiple_hyphens(self):
        assert _sanitize_slug("a---b--c") == "a-b-c"

    def test_truncates_to_50_chars(self):
        long = "a-" * 30
        result = _sanitize_slug(long)
        assert len(result) <= 50

    def test_returns_none_for_empty(self):
        assert _sanitize_slug("!!!") is None
        assert _sanitize_slug("") is None
