"""Reads now-playing info from, and sends playback commands to, Spotify via
the Windows System Media Transport Controls (SMTC) session API - the same
API used by the volume flyout's media controls, so no Spotify login/API key
is needed either for reading state or for controlling playback.
"""

import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from PySide6.QtCore import QObject, Signal

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSession,
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)


@dataclass
class NowPlaying:
    title: str = ""
    artist: str = ""
    album: str = ""
    is_playing: bool = False
    position_ms: int = 0
    duration_ms: int = 0


class MediaSessionWatcher(QObject):
    track_changed = Signal(object)  # NowPlaying, emitted when title/artist changes
    state_updated = Signal(object)  # NowPlaying, emitted on every poll
    no_session = Signal()           # emitted when Spotify isn't playing anything

    def __init__(self, poll_interval: float = 0.5, parent=None):
        super().__init__(parent)
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_key = None  # (title, artist) used to detect track changes
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    # --- playback controls, safe to call from the GUI thread ---
    def toggle_play_pause(self):
        self._schedule(self._do_toggle_play_pause())

    def skip_next(self):
        self._schedule(self._do_skip_next())

    def skip_previous(self):
        self._schedule(self._do_skip_previous())

    def seek(self, position_ms: int):
        self._schedule(self._do_seek(position_ms))

    def _schedule(self, coro):
        # The watcher's asyncio loop lives on its own thread; button clicks
        # happen on the GUI thread, so hand the coroutine over thread-safely
        # instead of trying to run it directly.
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _do_toggle_play_pause(self):
        session = await self._find_spotify_session()
        if session is not None:
            try:
                await session.try_toggle_play_pause_async()
            except Exception:
                pass

    async def _do_skip_next(self):
        session = await self._find_spotify_session()
        if session is not None:
            try:
                await session.try_skip_next_async()
            except Exception:
                pass

    async def _do_skip_previous(self):
        session = await self._find_spotify_session()
        if session is not None:
            try:
                await session.try_skip_previous_async()
            except Exception:
                pass

    async def _do_seek(self, position_ms: int):
        session = await self._find_spotify_session()
        if session is not None:
            try:
                await session.try_change_playback_position_async(position_ms * 10_000)
            except Exception:
                pass

    def _run(self):
        asyncio.run(self._poll_loop())

    async def _poll_loop(self):
        self._loop = asyncio.get_running_loop()
        while not self._stop_event.is_set():
            try:
                now_playing = await self._read_spotify_session()
            except Exception:
                now_playing = None

            if now_playing is None:
                self._last_key = None
                self.no_session.emit()
            else:
                key = (now_playing.title, now_playing.artist)
                if key != self._last_key:
                    self._last_key = key
                    self.track_changed.emit(now_playing)
                self.state_updated.emit(now_playing)

            await asyncio.sleep(self._poll_interval)

    async def _find_spotify_session(self) -> Optional[GlobalSystemMediaTransportControlsSession]:
        manager = await MediaManager.request_async()
        for candidate in manager.get_sessions():
            if "spotify" in candidate.source_app_user_model_id.lower():
                return candidate
        return None

    async def _read_spotify_session(self) -> Optional[NowPlaying]:
        session = await self._find_spotify_session()
        if session is None:
            return None

        info = await session.try_get_media_properties_async()
        if not info or not info.title:
            return None

        timeline = session.get_timeline_properties()
        playback_info = session.get_playback_info()
        is_playing = (
            playback_info is not None
            and playback_info.playback_status == PlaybackStatus.PLAYING
        )

        # Spotify only pushes a new SMTC timeline update every few seconds,
        # not on every poll, so `timeline.position` is a snapshot as of
        # `last_updated_time`, not "right now". Extrapolate forward by
        # however long it's been since that snapshot, or the displayed
        # lyric line steadily lags behind and then jumps when a fresher
        # snapshot finally arrives.
        position_ms = timeline.position.total_seconds() * 1000
        if is_playing:
            staleness_ms = (datetime.now(timezone.utc) - timeline.last_updated_time).total_seconds() * 1000
            if staleness_ms > 0:
                position_ms += staleness_ms

        duration_ms = int(timeline.end_time.total_seconds() * 1000)
        if duration_ms > 0:
            position_ms = min(position_ms, duration_ms)

        return NowPlaying(
            title=info.title or "",
            artist=info.artist or "",
            album=info.album_title or "",
            is_playing=is_playing,
            position_ms=int(position_ms),
            duration_ms=duration_ms,
        )
