"""Tests for notetaking.tui — TUI data model and app integration."""

from pathlib import Path

import pytest

from notetaking.tui import (
    ExportComplete,
    LiveTranscriptUpdate,
    Meeting,
    MeetingDetected,
    MeetingEnded,
    NotetakingApp,
    scan_meetings,
)


# ---------------------------------------------------------------------------
# Meeting dataclass
# ---------------------------------------------------------------------------

class TestMeeting:
    def test_status_with_notes(self, tmp_path):
        m = Meeting(stem="test", notes=tmp_path / "test.md")
        assert m.status == "notes"

    def test_status_with_transcript_only(self, tmp_path):
        m = Meeting(stem="test", transcript=tmp_path / "test.txt")
        assert m.status == "transcript"

    def test_status_with_recording_only(self, tmp_path):
        m = Meeting(stem="test", recording=tmp_path / "test.wav")
        assert m.status == "recording"

    def test_status_precedence(self, tmp_path):
        """Notes take precedence over transcript."""
        m = Meeting(
            stem="test",
            recording=tmp_path / "test.wav",
            transcript=tmp_path / "test.txt",
            notes=tmp_path / "test.md",
        )
        assert m.status == "notes"

    def test_indicator_green_for_notes(self, tmp_path):
        m = Meeting(stem="test", notes=tmp_path / "test.md")
        assert "green" in m.indicator

    def test_indicator_yellow_for_transcript(self, tmp_path):
        m = Meeting(stem="test", transcript=tmp_path / "test.txt")
        assert "yellow" in m.indicator

    def test_indicator_dim_for_recording(self, tmp_path):
        m = Meeting(stem="test", recording=tmp_path / "test.wav")
        assert "dim" in m.indicator


# ---------------------------------------------------------------------------
# scan_meetings
# ---------------------------------------------------------------------------

class TestScanMeetings:
    def test_empty_dirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", tmp_path / "rec")
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", tmp_path / "txt")
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", tmp_path / "notes")
        (tmp_path / "rec").mkdir()
        (tmp_path / "txt").mkdir()
        (tmp_path / "notes").mkdir()

        result = scan_meetings()
        assert result == []

    def test_merged_stems(self, tmp_path, monkeypatch):
        rec_dir = tmp_path / "rec"
        txt_dir = tmp_path / "txt"
        notes_dir = tmp_path / "notes"
        rec_dir.mkdir()
        txt_dir.mkdir()
        notes_dir.mkdir()

        (rec_dir / "meeting_001.wav").write_bytes(b"fake")
        (txt_dir / "meeting_001.txt").write_text("transcript")
        (notes_dir / "meeting_001.md").write_text("# notes")

        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", rec_dir)
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", txt_dir)
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", notes_dir)

        result = scan_meetings()
        assert len(result) == 1
        m = result[0]
        assert m.stem == "meeting_001"
        assert m.recording is not None
        assert m.transcript is not None
        assert m.notes is not None

    def test_partial_meetings(self, tmp_path, monkeypatch):
        rec_dir = tmp_path / "rec"
        txt_dir = tmp_path / "txt"
        notes_dir = tmp_path / "notes"
        rec_dir.mkdir()
        txt_dir.mkdir()
        notes_dir.mkdir()

        (rec_dir / "meeting_a.wav").write_bytes(b"fake")
        (txt_dir / "meeting_b.txt").write_text("transcript")

        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", rec_dir)
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", txt_dir)
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", notes_dir)

        result = scan_meetings()
        assert len(result) == 2
        stems = {m.stem for m in result}
        assert stems == {"meeting_a", "meeting_b"}

    def test_sorted_reverse(self, tmp_path, monkeypatch):
        rec_dir = tmp_path / "rec"
        rec_dir.mkdir()
        (tmp_path / "txt").mkdir()
        (tmp_path / "notes").mkdir()

        (rec_dir / "meeting_20250101.wav").write_bytes(b"")
        (rec_dir / "meeting_20250201.wav").write_bytes(b"")
        (rec_dir / "meeting_20250301.wav").write_bytes(b"")

        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", rec_dir)
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", tmp_path / "txt")
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", tmp_path / "notes")

        result = scan_meetings()
        stems = [m.stem for m in result]
        assert stems == ["meeting_20250301", "meeting_20250201", "meeting_20250101"]


# ---------------------------------------------------------------------------
# App integration tests (Textual Pilot)
# ---------------------------------------------------------------------------

class TestNotetakingApp:
    @pytest.fixture
    def app_with_data(self, tmp_path, monkeypatch):
        rec_dir = tmp_path / "rec"
        txt_dir = tmp_path / "txt"
        notes_dir = tmp_path / "notes"
        rec_dir.mkdir()
        txt_dir.mkdir()
        notes_dir.mkdir()

        (rec_dir / "meeting_001.wav").write_bytes(b"fake")
        (txt_dir / "meeting_001.txt").write_text("=== TRANSCRIPT ===\nHello world")
        (notes_dir / "meeting_001.md").write_text("# Meeting Notes\n\n## Summary\nTest")

        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", rec_dir)
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", txt_dir)
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", notes_dir)

        return NotetakingApp()

    @pytest.fixture
    def empty_app(self, tmp_path, monkeypatch):
        for d in ("rec", "txt", "notes"):
            (tmp_path / d).mkdir()
        monkeypatch.setattr("notetaking.tui.RECORDINGS_DIR", tmp_path / "rec")
        monkeypatch.setattr("notetaking.tui.TRANSCRIPTS_DIR", tmp_path / "txt")
        monkeypatch.setattr("notetaking.tui.NOTES_DIR", tmp_path / "notes")
        return NotetakingApp()

    @pytest.mark.asyncio
    async def test_app_starts(self, empty_app):
        async with empty_app.run_test() as pilot:
            assert empty_app.title == "Notetaking"

    @pytest.mark.asyncio
    async def test_app_shows_meetings(self, app_with_data):
        async with app_with_data.run_test() as pilot:
            from textual.widgets import ListView
            list_view = app_with_data.query_one("#meeting-list", ListView)
            assert len(list_view) == 1

    @pytest.mark.asyncio
    async def test_quit_binding(self, empty_app):
        async with empty_app.run_test() as pilot:
            await pilot.press("q")
            # App should be exiting after q press

    @pytest.mark.asyncio
    async def test_tui_cli_help(self):
        from click.testing import CliRunner
        from notetaking.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["tui", "--help"])
        assert result.exit_code == 0
        assert "TUI" in result.output or "tui" in result.output.lower()

    # -- New keybinding tests --------------------------------------------------

    @pytest.mark.asyncio
    async def test_app_has_copy_binding(self, empty_app):
        async with empty_app.run_test() as pilot:
            bindings = [b.key for b in empty_app.BINDINGS]
            assert "c" in bindings

    @pytest.mark.asyncio
    async def test_app_has_export_binding(self, empty_app):
        async with empty_app.run_test() as pilot:
            bindings = [b.key for b in empty_app.BINDINGS]
            assert "e" in bindings

    @pytest.mark.asyncio
    async def test_app_has_watch_binding(self, empty_app):
        async with empty_app.run_test() as pilot:
            bindings = [b.key for b in empty_app.BINDINGS]
            assert "w" in bindings

    # -- New message classes exist ------------------------------------------

    def test_export_complete_message(self):
        msg = ExportComplete("/path/to/file.pdf")
        assert msg.path == "/path/to/file.pdf"

    def test_live_transcript_update_message(self):
        msg = LiveTranscriptUpdate("Hello world")
        assert msg.text == "Hello world"

    def test_meeting_detected_message(self):
        msg = MeetingDetected("zoom.us")
        assert msg.process_name == "zoom.us"

    def test_meeting_ended_message(self):
        msg = MeetingEnded("zoom.us")
        assert msg.process_name == "zoom.us"
