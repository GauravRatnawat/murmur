"""Tests for notetaking.cli — CLI commands and options."""

from click.testing import CliRunner

from notetaking.cli import cli


runner = CliRunner()


def test_cli_help():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "record" in result.output
    assert "transcribe" in result.output
    assert "summarize" in result.output
    assert "notes" in result.output


def test_summarize_help_shows_provider():
    result = runner.invoke(cli, ["summarize", "--help"])
    assert result.exit_code == 0
    assert "--provider" in result.output
    assert "anthropic" in result.output
    assert "gemini" in result.output
    assert "ollama" in result.output


def test_notes_help_shows_provider():
    result = runner.invoke(cli, ["notes", "--help"])
    assert result.exit_code == 0
    assert "--provider" in result.output


def test_ls_runs_without_error():
    result = runner.invoke(cli, ["ls"])
    assert result.exit_code == 0


def test_summarize_no_transcripts(tmp_path, monkeypatch):
    monkeypatch.setattr("notetaking.cli.TRANSCRIPTS_DIR", tmp_path)
    result = runner.invoke(cli, ["summarize"])
    assert result.exit_code == 1
    assert "No transcripts found" in result.output
