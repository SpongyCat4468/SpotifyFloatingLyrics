"""Runs a playlist pre-cache on a background thread, reporting progress via
Qt signals so the settings UI can show it without freezing.
"""

import threading
import time

from PySide6.QtCore import QObject, Signal

from lyrics import precache_track
from spotify_playlist import (
    _QUEUE_SCOPE,
    SpotifyClient,
    SpotifyError,
)

# Small gap between actual network fetches so we don't hammer LRCLIB (a free
# community service). Cache hits don't sleep.
_THROTTLE_S = 0.35


class UpcomingPrecacher(QObject):
    """Best-effort: while a song plays, peek the Spotify queue and pre-cache
    the next track's lyrics so it's ready the instant the song changes - no
    loading screen. Silent by design: needs a connected Spotify account with
    the playback scope, and does nothing (never prompts) otherwise.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._busy = threading.Lock()

    def peek_and_cache(self, client_id: str):
        if not client_id:
            return
        if not self._busy.acquire(blocking=False):
            return  # a previous peek is still running
        threading.Thread(
            target=self._run, args=(client_id,), daemon=True
        ).start()

    def _run(self, client_id: str):
        try:
            client = SpotifyClient(client_id)
            # Only proceed with a cached token that already covers the queue
            # scope, so we never open a browser in the background.
            if not client.cached_token_has_scope(_QUEUE_SCOPE):
                return
            if not client.connect_silent():
                return
            upcoming = client.get_upcoming_tracks(limit=1)
            for track in upcoming:
                precache_track(track.title, track.artist, track.duration_ms)
        except Exception:
            pass  # best-effort; never disrupt playback
        finally:
            self._busy.release()


class PlaylistPrecacher(QObject):
    progress = Signal(int, int, str)   # done, total, current "title - artist"
    finished = Signal(int, int, int)   # saved, already_cached, failed
    failed = Signal(str)               # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._cancel = threading.Event()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, client_id: str, playlist_url: str):
        if self.is_running():
            return
        self._cancel.clear()
        self._thread = threading.Thread(
            target=self._run, args=(client_id, playlist_url), daemon=True
        )
        self._thread.start()

    def cancel(self):
        self._cancel.set()

    def _run(self, client_id: str, playlist_url: str):
        try:
            client = SpotifyClient(client_id)
            self.progress.emit(0, 0, "Connecting to Spotify…")
            client.connect()
            self.progress.emit(0, 0, "Reading playlist…")
            tracks = client.get_playlist_tracks(playlist_url)
        except SpotifyError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            self.failed.emit(f"Unexpected error: {exc}")
            return

        total = len(tracks)
        if total == 0:
            self.failed.emit("No playable tracks found in that playlist.")
            return

        saved = cached = failed = 0
        for index, track in enumerate(tracks, start=1):
            if self._cancel.is_set():
                break
            self.progress.emit(index, total, f"{track.title} — {track.artist}")
            try:
                status = precache_track(track.title, track.artist, track.duration_ms)
            except Exception:
                status = "failed"
            if status == "saved":
                saved += 1
                time.sleep(_THROTTLE_S)  # only pause after a real fetch
            elif status == "cached":
                cached += 1
            else:
                failed += 1

        self.finished.emit(saved, cached, failed)
