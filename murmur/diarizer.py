"""Speaker diarization using pyannote.audio."""

from __future__ import annotations

import os
from dataclasses import dataclass

from murmur.backends import Segment


@dataclass
class DiarizedSegment:
    speaker: str
    start: float
    end: float
    text: str


def diarize(audio_path: str, quiet: bool = False) -> list[tuple[str, float, float]]:
    """Run speaker diarization on an audio file.

    Returns list of (speaker, start, end) tuples.
    Requires HF_TOKEN env var for pyannote.audio model access.
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError(
            "HF_TOKEN not set. Speaker diarization requires a Hugging Face token. "
            "Get one at https://huggingface.co/settings/tokens and add it to .env"
        )

    from pyannote.audio import Pipeline

    if not quiet:
        print("Running speaker diarization...")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    result = pipeline(audio_path)

    speaker_segments = []
    for turn, _, speaker in result.itertracks(yield_label=True):
        speaker_segments.append((speaker, turn.start, turn.end))

    if not quiet:
        print(f"Identified {len(set(s for s, _, _ in speaker_segments))} speakers")
    return speaker_segments


def merge_transcript_with_speakers(
    segments: list[Segment],
    speaker_segments: list[tuple[str, float, float]],
) -> list[DiarizedSegment]:
    """Assign a speaker to each transcript segment by max overlap.

    For each transcript segment, finds the speaker segment with the
    greatest temporal overlap and assigns that speaker.
    """
    diarized = []
    for seg in segments:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0

        for speaker, sp_start, sp_end in speaker_segments:
            overlap_start = max(seg.start, sp_start)
            overlap_end = min(seg.end, sp_end)
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker

        diarized.append(DiarizedSegment(
            speaker=best_speaker,
            start=seg.start,
            end=seg.end,
            text=seg.text,
        ))

    return diarized
