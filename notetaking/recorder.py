import datetime
import threading

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from notetaking.config import CHANNELS, RECORDINGS_DIR, SAMPLE_RATE


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


def record(device_name: str | None = None, duration: float | None = None) -> str:
    """Record audio from the given device.

    If duration is None, records until Ctrl+C is pressed.
    Returns the path to the saved WAV file.
    """
    from notetaking.config import DEFAULT_DEVICE

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
    stop_event = threading.Event()

    def callback(indata, frames, time_info, status):
        if status:
            print(f"  ⚠ {status}")
        chunks.append(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=channels,
        device=device_id,
        dtype="float32",
        callback=callback,
    )

    print(f"Recording from: {dev_info['name']}")
    print(f"Sample rate: {SAMPLE_RATE} Hz, Channels: {channels}")
    if duration:
        print(f"Duration: {duration}s")
    else:
        print("Press Ctrl+C to stop recording...")

    try:
        stream.start()
        if duration:
            sd.sleep(int(duration * 1000))
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
    print(f"Saved {duration_actual:.1f}s of audio to {filepath}")
    return str(filepath)
