"""Live transcription from audio queue using faster-whisper."""

from __future__ import annotations

import queue
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from murmur.config import SAMPLE_RATE


def live_transcribe(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    on_transcript: Callable[[str], None],
    chunk_duration: float = 5.0,
) -> None:
    """Read chunks from audio_queue, accumulate ~chunk_duration seconds,
    transcribe with faster-whisper, and call on_transcript with the full text.

    Args:
        audio_queue: Queue receiving numpy audio chunks from recorder.
        stop_event: Set to stop live transcription.
        on_transcript: Called with accumulated transcript text after each chunk.
        chunk_duration: Seconds of audio to accumulate before transcribing.
    """
    from murmur.backends._faster_whisper import Backend

    backend = Backend()
    accumulated: list[np.ndarray] = []
    accumulated_samples = 0
    target_samples = int(chunk_duration * SAMPLE_RATE)
    full_text_parts: list[str] = []

    while not stop_event.is_set():
        try:
            chunk = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        accumulated.append(chunk)
        accumulated_samples += len(chunk)

        if accumulated_samples >= target_samples:
            audio_data = np.concatenate(accumulated, axis=0)
            accumulated = []
            accumulated_samples = 0

            try:
                # Write temp WAV
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    tmp_path = f.name
                    audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
                    wavfile.write(tmp_path, SAMPLE_RATE, audio_int16)

                result = backend.transcribe(tmp_path, quiet=True)
                if result.text.strip():
                    full_text_parts.append(result.text.strip())
                    on_transcript("\n".join(full_text_parts))
            except Exception:
                pass  # Graceful degradation
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    # Process remaining audio
    if accumulated:
        try:
            audio_data = np.concatenate(accumulated, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
                audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
                wavfile.write(tmp_path, SAMPLE_RATE, audio_int16)

            result = backend.transcribe(tmp_path, quiet=True)
            if result.text.strip():
                full_text_parts.append(result.text.strip())
                on_transcript("\n".join(full_text_parts))
        except Exception:
            pass
        finally:
            Path(tmp_path).unlink(missing_ok=True)
