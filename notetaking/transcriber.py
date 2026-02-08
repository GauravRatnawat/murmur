from pathlib import Path

import whisper

from notetaking.config import TRANSCRIPTS_DIR, WHISPER_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model


def transcribe(audio_path: str) -> str:
    """Transcribe an audio file using Whisper.

    Saves both full text and timestamped segments.
    Returns the path to the saved transcript.
    """
    audio_path = Path(audio_path)
    stem = audio_path.stem  # e.g. meeting_20250101_120000
    transcript_path = TRANSCRIPTS_DIR / f"{stem}.txt"

    model = _get_model()
    print(f"Transcribing {audio_path.name}...")
    result = model.transcribe(str(audio_path), language="en")

    lines = []

    # Full text header
    lines.append("=== TRANSCRIPT ===")
    lines.append("")
    lines.append(result["text"].strip())
    lines.append("")

    # Timestamped segments
    lines.append("=== TIMESTAMPED SEGMENTS ===")
    lines.append("")
    for seg in result["segments"]:
        start = _format_time(seg["start"])
        end = _format_time(seg["end"])
        text = seg["text"].strip()
        lines.append(f"[{start} -> {end}] {text}")

    transcript_path.write_text("\n".join(lines))
    print(f"Transcript saved to {transcript_path}")
    return str(transcript_path)


def _format_time(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"
