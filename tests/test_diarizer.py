"""Tests for murmur.diarizer — speaker diarization and transcript merging."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from murmur.backends import Segment
from murmur.diarizer import DiarizedSegment, merge_transcript_with_speakers


class TestMergeTranscriptWithSpeakers:
    def test_basic_merge(self):
        segments = [
            Segment(start=0.0, end=5.0, text="Hello there"),
            Segment(start=5.0, end=10.0, text="How are you"),
        ]
        speaker_segments = [
            ("SPEAKER_00", 0.0, 6.0),
            ("SPEAKER_01", 6.0, 10.0),
        ]

        result = merge_transcript_with_speakers(segments, speaker_segments)

        assert len(result) == 2
        assert result[0].speaker == "SPEAKER_00"
        assert result[0].text == "Hello there"
        assert result[1].speaker == "SPEAKER_01"
        assert result[1].text == "How are you"

    def test_overlap_picks_max(self):
        """When a segment overlaps two speakers, pick the one with more overlap."""
        segments = [
            Segment(start=0.0, end=10.0, text="Long segment"),
        ]
        speaker_segments = [
            ("SPEAKER_00", 0.0, 3.0),  # 3s overlap
            ("SPEAKER_01", 3.0, 10.0),  # 7s overlap
        ]

        result = merge_transcript_with_speakers(segments, speaker_segments)
        assert result[0].speaker == "SPEAKER_01"

    def test_no_speaker_segments(self):
        segments = [
            Segment(start=0.0, end=5.0, text="Hello"),
        ]

        result = merge_transcript_with_speakers(segments, [])
        assert len(result) == 1
        assert result[0].speaker == "UNKNOWN"

    def test_empty_segments(self):
        result = merge_transcript_with_speakers([], [("SPEAKER_00", 0.0, 5.0)])
        assert result == []

    def test_diarized_segment_shape(self):
        seg = DiarizedSegment(speaker="SPEAKER_00", start=0.0, end=5.0, text="Hi")
        assert seg.speaker == "SPEAKER_00"
        assert seg.start == 0.0
        assert seg.end == 5.0
        assert seg.text == "Hi"


class TestDiarize:
    def test_missing_hf_token_raises(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        from murmur.diarizer import diarize
        with pytest.raises(RuntimeError, match="HF_TOKEN not set"):
            diarize("/fake/audio.wav")

    def test_diarize_calls_pipeline(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "fake-token")

        mock_turn1 = MagicMock()
        mock_turn1.start = 0.0
        mock_turn1.end = 5.0
        mock_turn2 = MagicMock()
        mock_turn2.start = 5.0
        mock_turn2.end = 10.0

        mock_pipeline_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.itertracks.return_value = [
            (mock_turn1, None, "SPEAKER_00"),
            (mock_turn2, None, "SPEAKER_01"),
        ]
        mock_pipeline_instance.return_value = mock_result

        mock_pyannote = MagicMock()
        mock_pyannote.Pipeline.from_pretrained.return_value = mock_pipeline_instance

        with patch.dict(sys.modules, {
            "pyannote": MagicMock(),
            "pyannote.audio": mock_pyannote,
        }):
            if "murmur.diarizer" in sys.modules:
                del sys.modules["murmur.diarizer"]
            from murmur.diarizer import diarize

            result = diarize("/fake/audio.wav", quiet=True)

            assert len(result) == 2
            assert result[0] == ("SPEAKER_00", 0.0, 5.0)
            assert result[1] == ("SPEAKER_01", 5.0, 10.0)
