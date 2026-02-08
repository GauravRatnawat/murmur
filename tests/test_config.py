"""Tests for notetaking.config — paths and settings."""

from pathlib import Path

from notetaking.config import (
    DATA_DIR,
    LLM_PROVIDER,
    NOTES_DIR,
    RECORDINGS_DIR,
    TRANSCRIPTS_DIR,
)


def test_data_dirs_exist():
    assert RECORDINGS_DIR.exists()
    assert TRANSCRIPTS_DIR.exists()
    assert NOTES_DIR.exists()


def test_data_dirs_are_under_data():
    assert RECORDINGS_DIR.parent == DATA_DIR
    assert TRANSCRIPTS_DIR.parent == DATA_DIR
    assert NOTES_DIR.parent == DATA_DIR


def test_llm_provider_is_string():
    assert isinstance(LLM_PROVIDER, str)
    assert len(LLM_PROVIDER) > 0
