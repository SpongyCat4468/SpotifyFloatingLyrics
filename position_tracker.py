"""Interpolates playback position between polls.

media_session.py already extrapolates each sample to "right now" using
SMTC's own last-updated timestamp, so samples are trustworthy on arrival.
This just fills the gap between polls (every ~0.5s) and UI ticks (every
~0.2s) by projecting forward from the most recent sample using a
monotonic clock.
"""

import time


class PositionTracker:
    def __init__(self):
        self._anchor_ms = 0
        self._anchor_time = time.monotonic()
        self._is_playing = False
        self._duration_ms = 0

    def update(self, position_ms: int, is_playing: bool, duration_ms: int):
        self._anchor_ms = position_ms
        self._anchor_time = time.monotonic()
        self._is_playing = is_playing
        self._duration_ms = duration_ms

    def estimated_position_ms(self) -> int:
        if self._is_playing:
            elapsed_ms = (time.monotonic() - self._anchor_time) * 1000
            position_ms = self._anchor_ms + elapsed_ms
        else:
            position_ms = self._anchor_ms
        upper_bound = self._duration_ms or (1 << 30)
        return max(0, min(int(position_ms), upper_bound))
