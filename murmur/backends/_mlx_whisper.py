"""MLX Whisper backend (Apple Silicon GPU)."""

from __future__ import annotations

from murmur.backends import Segment, TranscriptionResult

# Map short model names to HuggingFace repo IDs
_MODEL_MAP = {
    "tiny": "mlx-community/whisper-tiny",
    "tiny.en": "mlx-community/whisper-tiny.en",
    "base": "mlx-community/whisper-base",
    "base.en": "mlx-community/whisper-base.en",
    "small": "mlx-community/whisper-small",
    "small.en": "mlx-community/whisper-small.en",
    "medium": "mlx-community/whisper-medium",
    "medium.en": "mlx-community/whisper-medium.en",
    "large": "mlx-community/whisper-large-v3",
    "large-v3": "mlx-community/whisper-large-v3",
}


class Backend:
    def __init__(self) -> None:
        self._repo: str | None = None

    def load_model(self, model_name: str, quiet: bool = False) -> None:
        self._repo = _MODEL_MAP.get(model_name, model_name)
        if not quiet:
            print(f"Using mlx-whisper model '{self._repo}'...")

    def transcribe(self, audio_path: str, language: str = "en", model_name: str = "base.en", quiet: bool = False) -> TranscriptionResult:
        import mlx_whisper

        self.load_model(model_name, quiet=quiet)
        if not quiet:
            print(f"Transcribing {audio_path}...")

        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=self._repo,
            language=language,
        )

        segments = [
            Segment(start=seg["start"], end=seg["end"], text=seg["text"].strip())
            for seg in result["segments"]
        ]
        return TranscriptionResult(text=result["text"].strip(), segments=segments)
