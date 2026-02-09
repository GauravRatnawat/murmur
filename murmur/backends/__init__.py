"""Pluggable transcription backend system.

Selection via TRANSCRIPTION_BACKEND env var or --backend CLI flag.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass
class TranscriptionResult:
    text: str
    segments: list[Segment] = field(default_factory=list)


# Maps backend name -> (module_path, pip_package)
BACKENDS: dict[str, tuple[str, str]] = {
    "whisper": ("murmur.backends._whisper", "openai-whisper"),
    "faster": ("murmur.backends._faster_whisper", "faster-whisper"),
    "mlx": ("murmur.backends._mlx_whisper", "mlx-whisper"),
}

_cached_backend: dict[str, object] = {}


def get_backend(name: str | None = None):
    """Return a backend instance by name. Caches per name."""
    from murmur.config import TRANSCRIPTION_BACKEND

    name = (name or TRANSCRIPTION_BACKEND).lower()

    if name in _cached_backend:
        return _cached_backend[name]

    if name not in BACKENDS:
        names = ", ".join(BACKENDS)
        raise RuntimeError(f"Unknown backend '{name}'. Choose from: {names}")

    module_path, pip_package = BACKENDS[name]

    try:
        mod = importlib.import_module(module_path)
    except ImportError:
        raise RuntimeError(
            f"Backend '{name}' not installed. Run: pip install {pip_package}"
        )

    backend = mod.Backend()
    _cached_backend[name] = backend
    return backend
