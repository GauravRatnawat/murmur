"""Tests for notetaking.live_transcriber — live transcription from audio queue."""

import queue
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from notetaking.backends import TranscriptionResult


@pytest.fixture(autouse=True)
def mock_faster_whisper():
    """Mock faster_whisper so live_transcriber can import Backend."""
    mock_fw = MagicMock()
    with patch.dict(sys.modules, {"faster_whisper": mock_fw}):
        # Clear cached module so it reimports with the mock
        if "notetaking.backends._faster_whisper" in sys.modules:
            del sys.modules["notetaking.backends._faster_whisper"]
        if "notetaking.live_transcriber" in sys.modules:
            del sys.modules["notetaking.live_transcriber"]
        yield mock_fw


class TestLiveTranscribe:
    def test_processes_audio_chunks(self, mock_faster_whisper):
        from notetaking.live_transcriber import live_transcribe
        from notetaking.backends._faster_whisper import Backend

        # Mock the Backend's transcribe method
        with patch.object(Backend, "transcribe", return_value=TranscriptionResult(text="Hello world")):
            audio_q = queue.Queue()
            stop = threading.Event()
            transcripts = []

            # Put enough samples for one chunk (~5s at 48000Hz)
            chunk = np.zeros((48000 * 5, 2), dtype=np.float32)
            audio_q.put(chunk)

            def stop_soon():
                time.sleep(0.3)
                stop.set()

            t = threading.Thread(target=stop_soon)
            t.start()

            live_transcribe(audio_q, stop, lambda text: transcripts.append(text), chunk_duration=5.0)
            t.join()

            assert len(transcripts) >= 1
            assert "Hello world" in transcripts[0]

    def test_stop_event_stops_loop(self, mock_faster_whisper):
        from notetaking.live_transcriber import live_transcribe

        audio_q = queue.Queue()
        stop = threading.Event()
        stop.set()  # Immediately stop

        transcripts = []
        live_transcribe(audio_q, stop, lambda text: transcripts.append(text))

        # Should exit immediately without processing
        assert len(transcripts) == 0

    def test_error_resilience(self, mock_faster_whisper):
        from notetaking.live_transcriber import live_transcribe
        from notetaking.backends._faster_whisper import Backend

        with patch.object(Backend, "transcribe", side_effect=RuntimeError("model error")):
            audio_q = queue.Queue()
            stop = threading.Event()
            transcripts = []

            chunk = np.zeros((48000 * 5, 2), dtype=np.float32)
            audio_q.put(chunk)

            def stop_soon():
                time.sleep(0.3)
                stop.set()

            t = threading.Thread(target=stop_soon)
            t.start()

            # Should not raise despite backend error
            live_transcribe(audio_q, stop, lambda text: transcripts.append(text), chunk_duration=5.0)
            t.join()

            # No transcripts due to error, but no crash
            assert len(transcripts) == 0
