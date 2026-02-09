"""Faster Whisper backend (CTranslate2, ~4x faster CPU)."""

from __future__ import annotations

from notetaking.backends import Segment, TranscriptionResult


class Backend:
    def __init__(self) -> None:
        self._model = None

    def load_model(self, model_name: str, quiet: bool = False) -> None:
        from faster_whisper import WhisperModel

        if self._model is None:
            if not quiet:
                print(f"Loading faster-whisper model '{model_name}'...")
            self._model = WhisperModel(model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str, language: str = "en", model_name: str = "base.en", quiet: bool = False) -> TranscriptionResult:
        self.load_model(model_name, quiet=quiet)
        if not quiet:
            print(f"Transcribing {audio_path}...")
        segments_gen, _info = self._model.transcribe(str(audio_path), language=language)

        segments = []
        full_text_parts = []
        for seg in segments_gen:
            text = seg.text.strip()
            segments.append(Segment(start=seg.start, end=seg.end, text=text))
            full_text_parts.append(text)

        return TranscriptionResult(
            text=" ".join(full_text_parts),
            segments=segments,
        )
