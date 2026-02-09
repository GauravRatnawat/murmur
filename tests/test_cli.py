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
    assert "copy" in result.output
    assert "export" in result.output
    assert "watch" in result.output


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


# -- New command help tests ------------------------------------------------


def test_copy_help():
    result = runner.invoke(cli, ["copy", "--help"])
    assert result.exit_code == 0
    assert "clipboard" in result.output.lower() or "Copy" in result.output


def test_export_help():
    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.output
    assert "pdf" in result.output
    assert "docx" in result.output


def test_watch_help():
    result = runner.invoke(cli, ["watch", "--help"])
    assert result.exit_code == 0
    assert "Watch" in result.output or "watch" in result.output.lower()


def test_transcribe_help_shows_backend():
    result = runner.invoke(cli, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "--backend" in result.output
    assert "whisper" in result.output
    assert "faster" in result.output
    assert "mlx" in result.output


def test_transcribe_help_shows_diarize():
    result = runner.invoke(cli, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "--diarize" in result.output


def test_notes_help_shows_backend_and_diarize():
    result = runner.invoke(cli, ["notes", "--help"])
    assert result.exit_code == 0
    assert "--backend" in result.output
    assert "--diarize" in result.output
