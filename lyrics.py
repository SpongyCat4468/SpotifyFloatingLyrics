"""Fetches synced (LRC) lyrics for the current track.

Lookup order: LRCLIB's accurate /api/get (matches track + artist +
duration), then LRCLIB's fuzzy /api/search, then the syncedlyrics library.
Results are cached both in memory and on disk (keyed by title+artist), so
replaying a song - even after restarting the app - skips the network fetch.
"""

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import QObject, Signal
from rapidfuzz import fuzz

import requests
import syncedlyrics

LyricLine = Tuple[int, str]  # (timestamp_ms, text)

_LRC_LINE_RE = re.compile(r"\[(\d{1,2}):(\d{2}(?:\.\d+)?)\](.*)")

_CACHE_DIR = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "SpotifyFloatingLyrics" / "lyrics_cache"

_LRCLIB_GET_URL = "https://lrclib.net/api/get"
_LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
_USER_AGENT = "SpotifyFloatingLyrics (https://github.com/SpongyCat4468/SpotifyFloatingLyrics)"
_MIN_ARTIST_SIMILARITY = 85
_MIN_TITLE_SIMILARITY = 80


@dataclass
class LyricsResult:
    lines: List[LyricLine]
    synced: bool


def parse_lrc(lrc_text: str) -> List[LyricLine]:
    lines: List[LyricLine] = []
    for raw_line in lrc_text.splitlines():
        match = _LRC_LINE_RE.match(raw_line.strip())
        if not match:
            continue
        minutes, seconds, text = match.groups()
        timestamp_ms = int(float(minutes) * 60_000 + float(seconds) * 1000)
        text = text.strip()
        if text:
            lines.append((timestamp_ms, text))
    lines.sort(key=lambda pair: pair[0])
    return lines


def _result_from_lrclib_track(track: dict) -> Optional["LyricsResult"]:
    synced_text = track.get("syncedLyrics")
    if synced_text:
        lines = parse_lrc(synced_text)
        if lines:
            return LyricsResult(lines=lines, synced=True)

    plain_text = track.get("plainLyrics")
    if plain_text:
        plain_lines = [(0, line) for line in plain_text.splitlines() if line.strip()]
        if plain_lines:
            return LyricsResult(lines=plain_lines, synced=False)
    return None


def _lrclib_get(title: str, artist: str, duration_ms: int) -> Optional["LyricsResult"]:
    """Accurate signature lookup via LRCLIB's /api/get: it matches on track
    name, artist, AND duration, so it returns the one exact recording or a
    404 - never a fuzzy look-alike. Needs a real duration to disambiguate;
    without one we skip straight to the search fallback.
    """
    if not duration_ms:
        return None
    try:
        response = requests.get(
            _LRCLIB_GET_URL,
            params={
                "track_name": title,
                "artist_name": artist,
                "duration": round(duration_ms / 1000),
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
    except Exception:
        return None
    if response.status_code != 200:
        return None
    try:
        return _result_from_lrclib_track(response.json())
    except Exception:
        return None


def _lrclib_search(title: str, artist: str) -> Optional["LyricsResult"]:
    """Fuzzy fallback for when /api/get finds nothing (e.g. the track's
    duration doesn't match LRCLIB's copy). /api/search returns a ranked
    candidate list with no duration disambiguation, so we only accept a
    result whose artist and title both score above a similarity threshold -
    otherwise a title-only hit (e.g. "Lemonade" landing on a different
    artist's track) could slip through as a wrong-song match.
    """
    try:
        response = requests.get(
            _LRCLIB_SEARCH_URL,
            params={"track_name": title, "artist_name": artist},
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        candidates = response.json()
    except Exception:
        return None

    best_track = None
    best_score = -1
    for track in candidates:
        artist_score = fuzz.ratio(str(track.get("artistName", "")).lower(), artist.lower())
        title_score = fuzz.ratio(str(track.get("trackName", "")).lower(), title.lower())
        if artist_score < _MIN_ARTIST_SIMILARITY or title_score < _MIN_TITLE_SIMILARITY:
            continue
        score = artist_score + title_score
        if score > best_score:
            best_score = score
            best_track = track

    if best_track is None:
        return None
    return _result_from_lrclib_track(best_track)


def _cache_file_for(key: Tuple[str, str]) -> Path:
    digest = hashlib.sha1("|||".join(key).encode("utf-8")).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def _load_from_disk(key: Tuple[str, str]) -> Optional[LyricsResult]:
    path = _cache_file_for(key)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        lines = [(int(ms), text) for ms, text in data["lines"]]
        return LyricsResult(lines=lines, synced=data["synced"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _save_to_disk(key: Tuple[str, str], result: LyricsResult):
    path = _cache_file_for(key)
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"synced": result.synced, "lines": result.lines}),
            encoding="utf-8",
        )
    except OSError:
        pass


class LyricsFetcher(QObject):
    lyrics_loading = Signal(str, str)
    lyrics_ready = Signal(str, str, object)  # title, artist, LyricsResult
    lyrics_failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache = {}

    def request(self, title: str, artist: str, duration_ms: int = 0):
        key = (title.lower(), artist.lower())
        if key in self._cache:
            self.lyrics_ready.emit(title, artist, self._cache[key])
            return

        cached = _load_from_disk(key)
        if cached is not None:
            self._cache[key] = cached
            self.lyrics_ready.emit(title, artist, cached)
            return

        self.lyrics_loading.emit(title, artist)
        threading.Thread(
            target=self._fetch, args=(title, artist, duration_ms, key), daemon=True
        ).start()

    def _fetch(self, title: str, artist: str, duration_ms: int, key):
        # Accurate duration-signature lookup first; fall back to fuzzy search.
        result = _lrclib_get(title, artist, duration_ms) or _lrclib_search(title, artist)
        if result is not None:
            self._cache[key] = result
            _save_to_disk(key, result)
            self.lyrics_ready.emit(title, artist, result)
            return

        search_term = f"{title} {artist}".strip()
        result = None
        try:
            lrc = syncedlyrics.search(search_term, synced_only=True)
            if lrc:
                lrc_lines = parse_lrc(lrc)
                if lrc_lines:
                    result = LyricsResult(lines=lrc_lines, synced=True)
            if result is None:
                plain = syncedlyrics.search(search_term, plain_only=True)
                if plain:
                    plain_lines = [(0, line) for line in plain.splitlines() if line.strip()]
                    if plain_lines:
                        result = LyricsResult(lines=plain_lines, synced=False)
        except Exception:
            result = None

        if result is None:
            self.lyrics_failed.emit(title, artist)
            return

        self._cache[key] = result
        _save_to_disk(key, result)
        self.lyrics_ready.emit(title, artist, result)
