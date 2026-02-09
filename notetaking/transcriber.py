from pathlib import Path

from notetaking.config import TRANSCRIPTS_DIR, WHISPER_MODEL


def transcribe(
    audio_path: str,
    quiet: bool = False,
    backend: str | None = None,
    diarize: bool = False,
) -> str:
    """Transcribe an audio file using the selected backend.

    Saves both full text and timestamped segments.
    Returns the path to the saved transcript.
    """
    from notetaking.backends import get_backend

    audio_path = Path(audio_path)
    stem = audio_path.stem
    transcript_path = TRANSCRIPTS_DIR / f"{stem}.txt"

    b = get_backend(backend)
    result = b.transcribe(
        str(audio_path), language="en", model_name=WHISPER_MODEL, quiet=quiet,
    )

    # Optionally merge speaker diarization
    if diarize:
        from notetaking.diarizer import diarize as run_diarize, merge_transcript_with_speakers
        speaker_segments = run_diarize(str(audio_path), quiet=quiet)
        diarized = merge_transcript_with_speakers(result.segments, speaker_segments)
        # Update segments with speaker info
        for seg, dseg in zip(result.segments, diarized):
            seg.speaker = dseg.speaker

    lines = []

    # Full text header
    lines.append("=== TRANSCRIPT ===")
    lines.append("")
    lines.append(result.text)
    lines.append("")

    # Timestamped segments
    lines.append("=== TIMESTAMPED SEGMENTS ===")
    lines.append("")
    for seg in result.segments:
        start = _format_time(seg.start)
        end = _format_time(seg.end)
        if seg.speaker:
            lines.append(f"[{seg.speaker}] [{start} -> {end}] {seg.text}")
        else:
            lines.append(f"[{start} -> {end}] {seg.text}")

    transcript_path.write_text("\n".join(lines))
    if not quiet:
        print(f"Transcript saved to {transcript_path}")
    return str(transcript_path)


def _format_time(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"
