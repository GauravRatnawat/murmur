"""Auto-meeting detection via process monitoring."""

from __future__ import annotations

import enum
import threading
from collections.abc import Callable

import psutil

MEETING_PROCESSES = [
    "zoom",
    "zoom.us",
    "teams",
    "microsoft teams",
    "webex",
    "ciscospark",
    "slack",
    "facetime",
]


class MeetingEvent(enum.Enum):
    STARTED = "started"
    ENDED = "ended"


def _is_meeting_active() -> str | None:
    """Check if a known meeting process is running. Returns process name or None."""
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"].lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        for meeting in MEETING_PROCESSES:
            if meeting in name:
                return proc.info["name"]
    return None


def watch_meetings(
    on_event: Callable[[MeetingEvent, str], None],
    stop_event: threading.Event,
    poll_interval: float = 5.0,
) -> None:
    """Poll for meeting processes, firing callbacks on start/end.

    Args:
        on_event: Called with (MeetingEvent.STARTED, process_name) or
                  (MeetingEvent.ENDED, process_name).
        stop_event: Set to stop watching.
        poll_interval: Seconds between polls.
    """
    active_process: str | None = None

    while not stop_event.is_set():
        current = _is_meeting_active()

        if current and not active_process:
            active_process = current
            on_event(MeetingEvent.STARTED, current)
        elif not current and active_process:
            ended = active_process
            active_process = None
            on_event(MeetingEvent.ENDED, ended)

        stop_event.wait(timeout=poll_interval)
