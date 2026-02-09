"""Tests for murmur.backends — factory, registry, backend behavior."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from murmur.backends import BACKENDS, Segment, TranscriptionResult, get_backend, _cached_backend


@pytest.fixture(autouse=True)
def clear_backend_cache():
    """Clear the backend cache before each test."""
    _cached_backend.clear()
    yield
    _cached_backend.clear()


class TestRegistry:
    def test_backends_dict_has_all_expected(self):
        assert "whisper" in BACKENDS
        assert "faster" in BACKENDS
        assert "mlx" in BACKENDS

    def test_each_backend_has_correct_tuple_shape(self):
        for name, entry in BACKENDS.items():
            assert len(entry) == 2, f"Backend '{name}' should have (module_path, pip_package)"
            module_path, pip_package = entry
            assert isinstance(module_path, str)
            assert isinstance(pip_package, str)

    def test_unknown_backend_raises(self):
        with pytest.raises(RuntimeError, match="Unknown backend"):
            get_backend("nonexistent")


class TestTranscriptionResult:
    def test_result_with_text_only(self):
        result = TranscriptionResult(text="Hello world")
        assert result.text == "Hello world"
        assert result.segments == []

    def test_result_with_segments(self):
        segs = [Segment(start=0.0, end=1.0, text="Hello")]
        result = TranscriptionResult(text="Hello", segments=segs)
        assert len(result.segments) == 1
        assert result.segments[0].text == "Hello"
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 1.0

    def test_segment_speaker_default_none(self):
        seg = Segment(start=0.0, end=1.0, text="test")
        assert seg.speaker is None

    def test_segment_with_speaker(self):
        seg = Segment(start=0.0, end=1.0, text="test", speaker="SPEAKER_00")
        assert seg.speaker == "SPEAKER_00"


class TestFactory:
    def test_get_backend_imports_module(self):
        with patch("murmur.backends.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.Backend.return_value = MagicMock()
            mock_import.return_value = mock_module

            backend = get_backend("whisper")
            mock_import.assert_called_once_with("murmur.backends._whisper")
            assert backend is not None

    def test_get_backend_caches(self):
        with patch("murmur.backends.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_backend = MagicMock()
            mock_module.Backend.return_value = mock_backend
            mock_import.return_value = mock_module

            b1 = get_backend("whisper")
            b2 = get_backend("whisper")
            assert b1 is b2
            mock_import.assert_called_once()

    def test_get_backend_missing_package_raises(self):
        with patch("murmur.backends.importlib.import_module", side_effect=ImportError):
            with pytest.raises(RuntimeError, match="not installed"):
                get_backend("faster")

    def test_get_backend_default_from_config(self, monkeypatch):
        monkeypatch.setattr("murmur.config.TRANSCRIPTION_BACKEND", "whisper")
        with patch("murmur.backends.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.Backend.return_value = MagicMock()
            mock_import.return_value = mock_module

            get_backend(None)
            mock_import.assert_called_once_with("murmur.backends._whisper")


class TestWhisperBackend:
    @patch("whisper.load_model")
    def test_whisper_backend_transcribe(self, mock_load):
        from murmur.backends._whisper import Backend

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": " Hello world ",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello world "},
            ],
        }
        mock_load.return_value = mock_model

        backend = Backend()
        result = backend.transcribe("/fake/audio.wav", quiet=True)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello world"
        assert len(result.segments) == 1
        assert result.segments[0].text == "Hello world"


class TestFasterWhisperBackend:
    def test_faster_backend_transcribe(self):
        # Create a mock faster_whisper module
        mock_fw = MagicMock()
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 1.5
        mock_seg.text = " Hello world "

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_seg], MagicMock())
        mock_fw.WhisperModel.return_value = mock_model

        with patch.dict(sys.modules, {"faster_whisper": mock_fw}):
            # Force reimport
            if "murmur.backends._faster_whisper" in sys.modules:
                del sys.modules["murmur.backends._faster_whisper"]
            from murmur.backends._faster_whisper import Backend

            backend = Backend()
            result = backend.transcribe("/fake/audio.wav", quiet=True)

            assert isinstance(result, TranscriptionResult)
            assert result.text == "Hello world"
            assert len(result.segments) == 1


class TestMlxWhisperBackend:
    def test_mlx_backend_transcribe(self):
        # Create a mock mlx_whisper module
        mock_mlx = MagicMock()
        mock_mlx.transcribe.return_value = {
            "text": " Hello world ",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello world "},
            ],
        }

        with patch.dict(sys.modules, {"mlx_whisper": mock_mlx}):
            if "murmur.backends._mlx_whisper" in sys.modules:
                del sys.modules["murmur.backends._mlx_whisper"]
            from murmur.backends._mlx_whisper import Backend

            backend = Backend()
            result = backend.transcribe("/fake/audio.wav", quiet=True)

            assert isinstance(result, TranscriptionResult)
            assert result.text == "Hello world"
            assert len(result.segments) == 1
            mock_mlx.transcribe.assert_called_once()
