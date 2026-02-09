"""OpenAI Whisper backend (default)."""

from __future__ import annotations

from murmur.backends import Segment, TranscriptionResult


class Backend:
    def __init__(self) -> None:
        self._model = None

    def load_model(self, model_name: str, quiet: bool = False) -> None:
        import whisper

        if self._model is None:
            if not quiet:
                print(f"Loading Whisper model '{model_name}'...")
            self._model = whisper.load_model(model_name)

    def transcribe(self, audio_path: str, language: str = "en", model_name: str = "base.en", quiet: bool = False) -> TranscriptionResult:
        self.load_model(model_name, quiet=quiet)
        if not quiet:
            print(f"Transcribing {audio_path}...")
        result = self._model.transcribe(str(audio_path), language=language)

        segments = [
            Segment(start=seg["start"], end=seg["end"], text=seg["text"].strip())
            for seg in result["segments"]
        ]
        return TranscriptionResult(text=result["text"].strip(), segments=segments)
