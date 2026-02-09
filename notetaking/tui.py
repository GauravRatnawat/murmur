"""Textual TUI dashboard for notetaking."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, ListItem, ListView, Markdown, Static

from notetaking.config import NOTES_DIR, RECORDINGS_DIR, TRANSCRIPTS_DIR


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Meeting:
    stem: str
    recording: Path | None = None
    transcript: Path | None = None
    notes: Path | None = None

    @property
    def status(self) -> str:
        """Return 'notes', 'transcript', or 'recording' based on what exists."""
        if self.notes:
            return "notes"
        if self.transcript:
            return "transcript"
        return "recording"

    @property
    def indicator(self) -> str:
        """Colored indicator character for display."""
        if self.notes:
            return "[green]●[/green]"
        if self.transcript:
            return "[yellow]○[/yellow]"
        return "[dim]◌[/dim]"


def scan_meetings() -> list[Meeting]:
    """Scan data dirs and merge into Meeting objects, sorted by stem."""
    recordings = {f.stem: f for f in RECORDINGS_DIR.glob("*.wav")}
    transcripts = {f.stem: f for f in TRANSCRIPTS_DIR.glob("*.txt")}
    notes = {f.stem: f for f in NOTES_DIR.glob("*.md")}

    all_stems = sorted(set(recordings) | set(transcripts) | set(notes), reverse=True)

    meetings = []
    for stem in all_stems:
        meetings.append(
            Meeting(
                stem=stem,
                recording=recordings.get(stem),
                transcript=transcripts.get(stem),
                notes=notes.get(stem),
            )
        )
    return meetings


# ---------------------------------------------------------------------------
# Custom messages
# ---------------------------------------------------------------------------

class RecordingComplete(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class TranscribeComplete(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class SummarizeComplete(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class ExportComplete(Message):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path


class LiveTranscriptUpdate(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class MeetingDetected(Message):
    def __init__(self, process_name: str) -> None:
        super().__init__()
        self.process_name = process_name


class MeetingEnded(Message):
    def __init__(self, process_name: str) -> None:
        super().__init__()
        self.process_name = process_name


class OperationError(Message):
    def __init__(self, operation: str, error: str) -> None:
        super().__init__()
        self.operation = operation
        self.error = error


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class MeetingItem(ListItem):
    """A single meeting entry in the list."""

    def __init__(self, meeting: Meeting) -> None:
        super().__init__()
        self.meeting = meeting

    def compose(self) -> ComposeResult:
        yield Label(f"{self.meeting.indicator}  {self.meeting.stem}")


class PreviewPane(Vertical):
    """Right panel — shows notes/transcript/placeholder for the selected meeting."""

    def compose(self) -> ComposeResult:
        yield Markdown("*Select a meeting to preview*", id="preview-md")

    def show_meeting(self, meeting: Meeting | None) -> None:
        md_widget = self.query_one("#preview-md", Markdown)
        if meeting is None:
            md_widget.update("*Select a meeting to preview*")
            return
        if meeting.notes:
            md_widget.update(meeting.notes.read_text())
        elif meeting.transcript:
            text = meeting.transcript.read_text()
            md_widget.update(f"```\n{text}\n```")
        elif meeting.recording:
            md_widget.update(f"*Recording only:* `{meeting.recording.name}`")
        else:
            md_widget.update("*No files found for this meeting.*")

    def show_live_transcript(self, text: str) -> None:
        md_widget = self.query_one("#preview-md", Markdown)
        md_widget.update(f"**Live Transcript:**\n\n{text}")


class RecordingBar(Static):
    """Bottom bar shown during recording with blinking indicator and timer."""

    elapsed = reactive(0.0)

    def render(self) -> str:
        mins, secs = divmod(int(self.elapsed), 60)
        hours, mins = divmod(mins, 60)
        return f"  ● REC  {hours:02d}:{mins:02d}:{secs:02d}   Press S to stop"

    DEFAULT_CSS = """
    RecordingBar {
        dock: bottom;
        height: 1;
        background: $error;
        color: $text;
        text-style: bold;
        display: none;
    }
    """


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class NotetakingApp(App):
    """Interactive TUI dashboard for notetaking."""

    TITLE = "Notetaking"

    CSS = """
    #main {
        height: 1fr;
    }
    #meeting-list {
        width: 1fr;
        min-width: 25;
        border-right: solid $primary;
    }
    #preview {
        width: 3fr;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("r", "record", "Record", show=True),
        Binding("s", "stop", "Stop", show=True),
        Binding("t", "transcribe", "Transcribe", show=True),
        Binding("n", "summarize", "Summarize", show=True),
        Binding("c", "copy", "Copy", show=True),
        Binding("e", "export", "Export", show=True),
        Binding("w", "watch", "Watch", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    meetings: reactive[list[Meeting]] = reactive(list, init=False)
    is_recording: reactive[bool] = reactive(False)
    is_watching: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self._stop_event: threading.Event | None = None
        self._selected_meeting: Meeting | None = None
        self._watch_stop: threading.Event | None = None
        self._live_stop: threading.Event | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield ListView(id="meeting-list")
            yield PreviewPane(id="preview")
        yield RecordingBar()
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_meetings()

    def _refresh_meetings(self) -> None:
        """Rescan dirs and repopulate the meeting list."""
        self.meetings = scan_meetings()
        list_view = self.query_one("#meeting-list", ListView)
        list_view.clear()
        for m in self.meetings:
            list_view.append(MeetingItem(m))
        self._update_status("")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle meeting selection."""
        if isinstance(event.item, MeetingItem):
            self._selected_meeting = event.item.meeting
            self.query_one(PreviewPane).show_meeting(self._selected_meeting)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update preview when highlight changes."""
        if event.item is not None and isinstance(event.item, MeetingItem):
            self._selected_meeting = event.item.meeting
            self.query_one(PreviewPane).show_meeting(self._selected_meeting)

    # -- Actions ---------------------------------------------------------------

    def action_record(self) -> None:
        if self.is_recording:
            self._update_status("Already recording...")
            return
        self.is_recording = True
        self._stop_event = threading.Event()
        self._live_stop = threading.Event()
        bar = self.query_one(RecordingBar)
        bar.elapsed = 0.0
        bar.styles.display = "block"
        self._update_status("Recording...")
        self._do_record()

    def action_stop(self) -> None:
        if not self.is_recording or self._stop_event is None:
            return
        self._stop_event.set()
        if self._live_stop:
            self._live_stop.set()

    def action_transcribe(self) -> None:
        if self.is_recording:
            self._update_status("Cannot transcribe while recording")
            return
        if self._selected_meeting is None:
            self._update_status("Select a meeting first")
            return
        if self._selected_meeting.recording is None:
            self._update_status("No recording for this meeting")
            return
        self._update_status(f"Transcribing {self._selected_meeting.stem}...")
        self._do_transcribe(str(self._selected_meeting.recording))

    def action_summarize(self) -> None:
        if self.is_recording:
            self._update_status("Cannot summarize while recording")
            return
        if self._selected_meeting is None:
            self._update_status("Select a meeting first")
            return
        if self._selected_meeting.transcript is None:
            self._update_status("No transcript for this meeting")
            return
        self._update_status(f"Summarizing {self._selected_meeting.stem}...")
        self._do_summarize(str(self._selected_meeting.transcript))

    def action_copy(self) -> None:
        """Copy selected meeting's notes or transcript to clipboard."""
        if self._selected_meeting is None:
            self._update_status("Select a meeting first")
            return

        try:
            import pyperclip
        except ImportError:
            self._update_status("pyperclip not installed (pip install notetaking[clipboard])")
            return

        if self._selected_meeting.notes:
            text = self._selected_meeting.notes.read_text()
        elif self._selected_meeting.transcript:
            text = self._selected_meeting.transcript.read_text()
        else:
            self._update_status("No notes or transcript to copy")
            return

        pyperclip.copy(text)
        self._update_status("Copied to clipboard")

    def action_export(self) -> None:
        """Export selected meeting's notes to PDF."""
        if self._selected_meeting is None:
            self._update_status("Select a meeting first")
            return
        if self._selected_meeting.notes is None:
            self._update_status("No notes to export")
            return
        self._update_status(f"Exporting {self._selected_meeting.stem}...")
        self._do_export(str(self._selected_meeting.notes))

    def action_watch(self) -> None:
        """Toggle meeting watch mode."""
        if self.is_watching:
            if self._watch_stop:
                self._watch_stop.set()
            self.is_watching = False
            self._update_status("Watch mode stopped")
            return

        self.is_watching = True
        self._watch_stop = threading.Event()
        self._update_status("Watch mode: monitoring for meetings...")
        self._do_watch()

    # -- Workers ---------------------------------------------------------------

    @work(thread=True)
    def _do_record(self) -> None:
        from notetaking.recorder import record

        audio_q: queue.Queue | None = None
        live_thread: threading.Thread | None = None

        # Try to start live transcription if faster-whisper is available
        try:
            from notetaking.live_transcriber import live_transcribe
            audio_q = queue.Queue()

            def on_live(text: str) -> None:
                self.post_message(LiveTranscriptUpdate(text))

            live_thread = threading.Thread(
                target=live_transcribe,
                args=(audio_q, self._live_stop, on_live),
                daemon=True,
            )
            live_thread.start()
        except ImportError:
            audio_q = None

        def on_chunk(elapsed: float) -> None:
            self.call_from_thread(self._update_elapsed, elapsed)

        try:
            path = record(
                stop_event=self._stop_event,
                on_chunk=on_chunk,
                quiet=True,
                audio_queue=audio_q,
            )
            self.post_message(RecordingComplete(path))
        except Exception as e:
            self.post_message(OperationError("record", str(e)))

        # Clean up live transcription
        if self._live_stop:
            self._live_stop.set()
        if live_thread:
            live_thread.join(timeout=5)

    @work(thread=True)
    def _do_transcribe(self, audio_path: str) -> None:
        from notetaking.transcriber import transcribe

        try:
            path = transcribe(audio_path, quiet=True)
            self.post_message(TranscribeComplete(path))
        except Exception as e:
            self.post_message(OperationError("transcribe", str(e)))

    @work(thread=True)
    def _do_summarize(self, transcript_path: str) -> None:
        from notetaking.summarizer import summarize

        try:
            path = summarize(transcript_path, quiet=True)
            self.post_message(SummarizeComplete(path))
        except Exception as e:
            self.post_message(OperationError("summarize", str(e)))

    @work(thread=True)
    def _do_export(self, notes_path: str) -> None:
        try:
            import pypandoc
        except ImportError:
            self.post_message(OperationError("export", "pypandoc not installed (pip install notetaking[export])"))
            return

        try:
            source = Path(notes_path)
            output_path = source.with_suffix(".pdf")
            pypandoc.convert_file(str(source), "pdf", outputfile=str(output_path))
            self.post_message(ExportComplete(str(output_path)))
        except Exception as e:
            self.post_message(OperationError("export", str(e)))

    @work(thread=True)
    def _do_watch(self) -> None:
        try:
            from notetaking.watcher import MeetingEvent, watch_meetings
        except ImportError:
            self.post_message(OperationError("watch", "psutil not installed (pip install notetaking[watch])"))
            return

        def on_event(event: MeetingEvent, process_name: str) -> None:
            if event == MeetingEvent.STARTED:
                self.post_message(MeetingDetected(process_name))
            elif event == MeetingEvent.ENDED:
                self.post_message(MeetingEnded(process_name))

        watch_meetings(on_event, self._watch_stop)

    # -- Message handlers ------------------------------------------------------

    def on_recording_complete(self, message: RecordingComplete) -> None:
        self.is_recording = False
        self.query_one(RecordingBar).styles.display = "none"
        self._refresh_meetings()
        self._update_status(f"Recording saved: {Path(message.path).name}")

    def on_transcribe_complete(self, message: TranscribeComplete) -> None:
        self._refresh_meetings()
        self._update_status(f"Transcript saved: {Path(message.path).name}")

    def on_summarize_complete(self, message: SummarizeComplete) -> None:
        self._refresh_meetings()
        self._update_status(f"Notes saved: {Path(message.path).name}")

    def on_export_complete(self, message: ExportComplete) -> None:
        self._update_status(f"Exported: {Path(message.path).name}")

    def on_live_transcript_update(self, message: LiveTranscriptUpdate) -> None:
        self.query_one(PreviewPane).show_live_transcript(message.text)

    def on_meeting_detected(self, message: MeetingDetected) -> None:
        self._update_status(f"Meeting detected: {message.process_name} — auto-recording...")
        self.action_record()

    def on_meeting_ended(self, message: MeetingEnded) -> None:
        self._update_status(f"Meeting ended: {message.process_name}")
        self.action_stop()

    def on_operation_error(self, message: OperationError) -> None:
        if message.operation == "record":
            self.is_recording = False
            self.query_one(RecordingBar).styles.display = "none"
        if message.operation == "watch":
            self.is_watching = False
        self._update_status(f"Error ({message.operation}): {message.error}")

    # -- Helpers ---------------------------------------------------------------

    def _update_elapsed(self, elapsed: float) -> None:
        self.query_one(RecordingBar).elapsed = elapsed

    def _update_status(self, text: str) -> None:
        self.query_one("#status-bar", Static).update(text)


def main() -> None:
    app = NotetakingApp()
    app.run()


if __name__ == "__main__":
    main()
