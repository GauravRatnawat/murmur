"""Tests for murmur.watcher — meeting detection via process monitoring."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from murmur.watcher import MEETING_PROCESSES, MeetingEvent, _is_meeting_active, watch_meetings


class TestIsMeetingActive:
    @patch("murmur.watcher.psutil")
    def test_no_meeting_processes(self, mock_psutil):
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "python"}),
            MagicMock(info={"name": "bash"}),
        ]
        mock_psutil.NoSuchProcess = type("NoSuchProcess", (Exception,), {})
        mock_psutil.AccessDenied = type("AccessDenied", (Exception,), {})
        assert _is_meeting_active() is None

    @patch("murmur.watcher.psutil")
    def test_zoom_detected(self, mock_psutil):
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "python"}),
            MagicMock(info={"name": "zoom.us"}),
        ]
        mock_psutil.NoSuchProcess = type("NoSuchProcess", (Exception,), {})
        mock_psutil.AccessDenied = type("AccessDenied", (Exception,), {})
        result = _is_meeting_active()
        assert result == "zoom.us"

    @patch("murmur.watcher.psutil")
    def test_teams_detected(self, mock_psutil):
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "Microsoft Teams"}),
        ]
        mock_psutil.NoSuchProcess = type("NoSuchProcess", (Exception,), {})
        mock_psutil.AccessDenied = type("AccessDenied", (Exception,), {})
        result = _is_meeting_active()
        assert result == "Microsoft Teams"

    @patch("murmur.watcher.psutil")
    def test_handles_access_denied(self, mock_psutil):
        AccessDen = type("AccessDenied", (Exception,), {})
        NoSuch = type("NoSuchProcess", (Exception,), {})
        mock_psutil.NoSuchProcess = NoSuch
        mock_psutil.AccessDenied = AccessDen

        bad_proc = MagicMock()
        bad_proc.info.__getitem__ = MagicMock(side_effect=AccessDen)
        mock_psutil.process_iter.return_value = [bad_proc]

        assert _is_meeting_active() is None

    def test_meeting_processes_list_not_empty(self):
        assert len(MEETING_PROCESSES) > 0
        assert "zoom" in MEETING_PROCESSES


class TestWatchMeetings:
    @patch("murmur.watcher._is_meeting_active")
    def test_watch_detects_start_and_end(self, mock_active):
        events = []
        call_count = [0]

        def side_effect():
            call_count[0] += 1
            if call_count[0] <= 2:
                return "zoom.us"
            return None

        mock_active.side_effect = side_effect
        stop = threading.Event()

        def on_event(event, name):
            events.append((event, name))
            if event == MeetingEvent.ENDED:
                stop.set()

        watch_meetings(on_event, stop, poll_interval=0.01)

        assert len(events) == 2
        assert events[0] == (MeetingEvent.STARTED, "zoom.us")
        assert events[1] == (MeetingEvent.ENDED, "zoom.us")

    @patch("murmur.watcher._is_meeting_active", return_value=None)
    def test_watch_stops_on_event(self, mock_active):
        stop = threading.Event()
        events = []

        def run():
            watch_meetings(lambda e, n: events.append(e), stop, poll_interval=0.01)

        t = threading.Thread(target=run)
        t.start()
        stop.set()
        t.join(timeout=2)
        assert not t.is_alive()
