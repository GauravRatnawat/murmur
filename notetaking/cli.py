from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from notetaking.config import NOTES_DIR, RECORDINGS_DIR, TRANSCRIPTS_DIR
from notetaking.llm import PROVIDERS

console = Console()

PROVIDER_NAMES = list(PROVIDERS.keys())


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
def transcribe(file):
    """Transcribe a recording. Defaults to the most recent."""
    from notetaking.transcriber import transcribe as do_transcribe

    if file is None:
        latest = _latest_file(RECORDINGS_DIR, ".wav")
        if latest is None:
            console.print("[red]No recordings found.[/red]")
            raise SystemExit(1)
        file = str(latest)
        console.print(f"Using latest recording: {latest.name}")

    path = do_transcribe(file)
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
def notes(device, duration, provider):
    """Full pipeline: record → transcribe → summarize."""
    from notetaking.recorder import record as do_record
    from notetaking.summarizer import summarize as do_summarize
    from notetaking.transcriber import transcribe as do_transcribe

    console.rule("[bold]Step 1: Record")
    wav_path = do_record(device_name=device, duration=duration)

    console.rule("[bold]Step 2: Transcribe")
    txt_path = do_transcribe(wav_path)

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
