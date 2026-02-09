from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from notetaking.config import NOTES_DIR, RECORDINGS_DIR, TRANSCRIPTS_DIR
from notetaking.llm import PROVIDERS
from notetaking.backends import BACKENDS

console = Console()

PROVIDER_NAMES = list(PROVIDERS.keys())
BACKEND_NAMES = list(BACKENDS.keys())


def _latest_file(directory: Path, suffix: str) -> Path | None:
    """Return the most recently modified file with the given suffix."""
    files = sorted(directory.glob(f"*{suffix}"), key=lambda f: f.stat().st_mtime)
    return files[-1] if files else None


@click.group()
def cli():
    """Granola-like meeting notes CLI — record, transcribe, summarize."""
    pass


@cli.command()
def devices():
    """List available audio devices."""
    from notetaking.recorder import list_devices

    list_devices()


@cli.command()
@click.option("-d", "--device", default=None, help="Audio device name (substring match).")
@click.option("-t", "--duration", default=None, type=float, help="Recording duration in seconds. Omit to record until Ctrl+C.")
def record(device, duration):
    """Record meeting audio."""
    from notetaking.recorder import record as do_record

    path = do_record(device_name=device, duration=duration)
    console.print(f"[green]Recording saved:[/green] {path}")


@cli.command()
@click.argument("file", required=False)
@click.option("-b", "--backend", type=click.Choice(BACKEND_NAMES, case_sensitive=False), default=None, help="Transcription backend.")
@click.option("--diarize", is_flag=True, default=False, help="Enable speaker diarization (requires HF_TOKEN).")
def transcribe(file, backend, diarize):
    """Transcribe a recording. Defaults to the most recent."""
    from notetaking.transcriber import transcribe as do_transcribe

    if file is None:
        latest = _latest_file(RECORDINGS_DIR, ".wav")
        if latest is None:
            console.print("[red]No recordings found.[/red]")
            raise SystemExit(1)
        file = str(latest)
        console.print(f"Using latest recording: {latest.name}")

    path = do_transcribe(file, backend=backend, diarize=diarize)
    console.print(f"[green]Transcript saved:[/green] {path}")


@cli.command()
@click.argument("file", required=False)
@click.option("-p", "--provider", type=click.Choice(PROVIDER_NAMES, case_sensitive=False), default=None, help="LLM provider to use.")
def summarize(file, provider):
    """Summarize a transcript. Defaults to the most recent."""
    from notetaking.summarizer import summarize as do_summarize

    if file is None:
        latest = _latest_file(TRANSCRIPTS_DIR, ".txt")
        if latest is None:
            console.print("[red]No transcripts found.[/red]")
            raise SystemExit(1)
        file = str(latest)
        console.print(f"Using latest transcript: {latest.name}")

    path = do_summarize(file, provider=provider)
    console.print(f"[green]Notes saved:[/green] {path}")


@cli.command()
@click.option("-d", "--device", default=None, help="Audio device name (substring match).")
@click.option("-t", "--duration", default=None, type=float, help="Recording duration in seconds.")
@click.option("-p", "--provider", type=click.Choice(PROVIDER_NAMES, case_sensitive=False), default=None, help="LLM provider to use.")
@click.option("-b", "--backend", type=click.Choice(BACKEND_NAMES, case_sensitive=False), default=None, help="Transcription backend.")
@click.option("--diarize", is_flag=True, default=False, help="Enable speaker diarization.")
def notes(device, duration, provider, backend, diarize):
    """Full pipeline: record → transcribe → summarize."""
    from notetaking.recorder import record as do_record
    from notetaking.summarizer import summarize as do_summarize
    from notetaking.transcriber import transcribe as do_transcribe

    console.rule("[bold]Step 1: Record")
    wav_path = do_record(device_name=device, duration=duration)

    console.rule("[bold]Step 2: Transcribe")
    txt_path = do_transcribe(wav_path, backend=backend, diarize=diarize)

    console.rule("[bold]Step 3: Summarize")
    md_path = do_summarize(txt_path, provider=provider)

    console.print()
    console.print(f"[green bold]Done![/green bold] Notes at: {md_path}")


@cli.command(name="ls")
def list_files():
    """List all saved recordings, transcripts, and notes."""
    table = Table(title="Meeting Files")
    table.add_column("Recording", style="cyan")
    table.add_column("Transcript", style="yellow")
    table.add_column("Notes", style="green")

    recordings = {f.stem: f.name for f in sorted(RECORDINGS_DIR.glob("*.wav"))}
    transcripts = {f.stem: f.name for f in sorted(TRANSCRIPTS_DIR.glob("*.txt"))}
    notes_files = {f.stem: f.name for f in sorted(NOTES_DIR.glob("*.md"))}

    all_stems = sorted(set(recordings) | set(transcripts) | set(notes_files))

    if not all_stems:
        console.print("[dim]No files found.[/dim]")
        return

    for stem in all_stems:
        table.add_row(
            recordings.get(stem, "-"),
            transcripts.get(stem, "-"),
            notes_files.get(stem, "-"),
        )

    console.print(table)


@cli.command()
@click.argument("file", required=False)
def copy(file):
    """Copy notes (or transcript) to clipboard. Defaults to latest notes."""
    try:
        import pyperclip
    except ImportError:
        console.print(
            "[red]pyperclip is not installed.[/red] "
            "Install it with: [bold]pip install notetaking\\[clipboard][/bold]"
        )
        raise SystemExit(1)

    if file is None:
        latest = _latest_file(NOTES_DIR, ".md")
        if latest is None:
            latest = _latest_file(TRANSCRIPTS_DIR, ".txt")
        if latest is None:
            console.print("[red]No notes or transcripts found.[/red]")
            raise SystemExit(1)
        file = str(latest)
        console.print(f"Using: {latest.name}")

    text = Path(file).read_text()
    pyperclip.copy(text)
    console.print("[green]Copied to clipboard.[/green]")


@cli.command()
@click.argument("file", required=False)
@click.option("-f", "--format", "fmt", type=click.Choice(["pdf", "docx"], case_sensitive=False), default="pdf", help="Export format (pdf or docx).")
def export(file, fmt):
    """Export notes to PDF or DOCX. Defaults to latest notes as PDF."""
    try:
        import pypandoc
    except ImportError:
        console.print(
            "[red]pypandoc is not installed.[/red] "
            "Install it with: [bold]pip install notetaking\\[export][/bold]"
        )
        raise SystemExit(1)

    if file is None:
        latest = _latest_file(NOTES_DIR, ".md")
        if latest is None:
            console.print("[red]No notes found.[/red]")
            raise SystemExit(1)
        file = str(latest)
        console.print(f"Using latest notes: {latest.name}")

    source = Path(file)
    output_path = source.with_suffix(f".{fmt}")
    pypandoc.convert_file(str(source), fmt, outputfile=str(output_path))
    console.print(f"[green]Exported:[/green] {output_path}")


@cli.command()
@click.option("-d", "--device", default=None, help="Audio device name (substring match).")
@click.option("-b", "--backend", type=click.Choice(BACKEND_NAMES, case_sensitive=False), default=None, help="Transcription backend.")
@click.option("-p", "--provider", type=click.Choice(PROVIDER_NAMES, case_sensitive=False), default=None, help="LLM provider to use.")
def watch(device, backend, provider):
    """Watch for meeting apps and auto-record when detected."""
    import threading

    try:
        from notetaking.watcher import MeetingEvent, watch_meetings
    except ImportError:
        console.print(
            "[red]psutil is not installed.[/red] "
            "Install it with: [bold]pip install notetaking\\[watch][/bold]"
        )
        raise SystemExit(1)

    from notetaking.recorder import record as do_record
    from notetaking.summarizer import summarize as do_summarize
    from notetaking.transcriber import transcribe as do_transcribe

    stop_recording = threading.Event()
    recording_thread: threading.Thread | None = None
    recorded_path: str | None = None

    def on_meeting_event(event: MeetingEvent, process_name: str) -> None:
        nonlocal recording_thread, recorded_path, stop_recording

        if event == MeetingEvent.STARTED:
            console.print(f"[green]Meeting detected:[/green] {process_name}")
            console.print("Auto-recording started...")
            stop_recording = threading.Event()

            def do():
                nonlocal recorded_path
                recorded_path = do_record(
                    device_name=device, stop_event=stop_recording, quiet=True,
                )

            recording_thread = threading.Thread(target=do, daemon=True)
            recording_thread.start()

        elif event == MeetingEvent.ENDED:
            console.print(f"[yellow]Meeting ended:[/yellow] {process_name}")
            stop_recording.set()
            if recording_thread:
                recording_thread.join(timeout=5)
            if recorded_path:
                console.print(f"Recording saved: {recorded_path}")
                console.print("Transcribing...")
                txt = do_transcribe(recorded_path, backend=backend, quiet=True)
                console.print(f"Transcript saved: {txt}")
                console.print("Summarizing...")
                md = do_summarize(txt, provider=provider, quiet=True)
                console.print(f"[green bold]Notes saved:[/green bold] {md}")
                recorded_path = None

    stop_watch = threading.Event()
    console.print("[bold]Watching for meeting apps...[/bold] Press Ctrl+C to stop.")
    console.print("[dim]Monitors: Zoom, Teams, WebEx, Slack, FaceTime[/dim]")
    console.print("[dim]Note: Google Meet runs in browser and may not be detected.[/dim]")

    try:
        watch_meetings(on_meeting_event, stop_watch)
    except KeyboardInterrupt:
        stop_watch.set()
        stop_recording.set()
        console.print("\n[dim]Stopped watching.[/dim]")


@cli.command()
def tui():
    """Launch interactive TUI dashboard."""
    try:
        from notetaking.tui import main
    except ImportError:
        console.print(
            "[red]Textual is not installed.[/red] "
            "Install it with: [bold]pip install notetaking\\[tui][/bold]"
        )
        raise SystemExit(1)
    main()
