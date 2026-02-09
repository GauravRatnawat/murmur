import datetime
import queue
import threading
import time
from collections.abc import Callable

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from murmur.config import CHANNELS, RECORDINGS_DIR, SAMPLE_RATE


def list_devices():
    """Print all available audio devices."""
    print(sd.query_devices())


def find_device(name: str) -> int:
    """Find a device ID by substring match on its name."""
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if name.lower() in dev["name"].lower():
            return i
    raise ValueError(f"No device found matching '{name}'")


def record(
    device_name: str | None = None,
    duration: float | None = None,
    stop_event: threading.Event | None = None,
    on_chunk: Callable[[float], None] | None = None,
    quiet: bool = False,
    audio_queue: queue.Queue | None = None,
) -> str:
    """Record audio from the given device.

    If duration is None, records until Ctrl+C or stop_event is set.
    Returns the path to the saved WAV file.

    Args:
        device_name: Audio device name (substring match).
        duration: Recording duration in seconds. None for unlimited.
        stop_event: If provided, used to signal stop. Otherwise created internally.
        on_chunk: Called with elapsed seconds after each audio chunk.
        quiet: Suppress all print output.
        audio_queue: If provided, copies each audio chunk into this queue for live transcription.
    """
    from murmur.config import DEFAULT_DEVICE

    device_name = device_name or DEFAULT_DEVICE
    device_id = find_device(device_name)
    dev_info = sd.query_devices(device_id)

    channels = min(CHANNELS, dev_info["max_input_channels"])
    if channels == 0:
        raise ValueError(f"Device '{dev_info['name']}' has no input channels")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meeting_{timestamp}.wav"
    filepath = RECORDINGS_DIR / filename

    chunks: list[np.ndarray] = []
    if stop_event is None:
        stop_event = threading.Event()

    frame_count = 0

    def callback(indata, frames, time_info, status):
        nonlocal frame_count
        if status and not quiet:
            print(f"  ⚠ {status}")
        chunk_copy = indata.copy()
        chunks.append(chunk_copy)
        if audio_queue is not None:
            audio_queue.put(chunk_copy)
        frame_count += frames
        if on_chunk is not None:
            elapsed = frame_count / SAMPLE_RATE
            on_chunk(elapsed)

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=channels,
        device=device_id,
        dtype="float32",
        callback=callback,
    )

    if not quiet:
        print(f"Recording from: {dev_info['name']}")
        print(f"Sample rate: {SAMPLE_RATE} Hz, Channels: {channels}")
        if duration:
            print(f"Duration: {duration}s")
        else:
            print("Press Ctrl+C to stop recording...")

    try:
        stream.start()
        if duration:
            # Interruptible timed recording: check stop_event every 100ms
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline:
                if stop_event.wait(timeout=0.1):
                    break
        else:
            stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()

    if not chunks:
        raise RuntimeError("No audio was recorded")

    audio = np.concatenate(chunks, axis=0)

    # Convert float32 [-1, 1] to int16
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    wavfile.write(str(filepath), SAMPLE_RATE, audio_int16)

    duration_actual = len(audio) / SAMPLE_RATE
    if not quiet:
        print(f"Saved {duration_actual:.1f}s of audio to {filepath}")
    return str(filepath)
