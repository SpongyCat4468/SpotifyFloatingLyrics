"""Spotify Web API access for pre-caching a playlist's lyrics.

Uses the Authorization Code + PKCE flow (spotipy), which needs only a Client
ID - no secret embedded in the exe. A one-time browser login covers any
public playlist plus the signed-in user's own private/collaborative ones.
(Spotify does not allow reading *other* users' private playlists via any
API, so those must be public to be pre-cached.)
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from spotipy import CacheFileHandler, Spotify
from spotipy.oauth2 import SpotifyPKCE

# Must exactly match a Redirect URI registered on the Spotify app.
REDIRECT_URI = "http://127.0.0.1:8888/callback"
_SCOPE = "playlist-read-private playlist-read-collaborative"
_TOKEN_CACHE = (
    Path(os.getenv("LOCALAPPDATA", str(Path.home())))
    / "SpotifyFloatingLyrics"
    / "spotify_token.json"
)

# Matches the id in an open.spotify.com URL, a spotify:playlist: URI, or a
# bare id.
_PLAYLIST_ID_RE = re.compile(r"playlist[/:]([A-Za-z0-9]+)")
_BARE_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")


@dataclass
class PlaylistTrack:
    title: str
    artist: str
    duration_ms: int


class SpotifyError(Exception):
    """Any user-facing failure talking to Spotify (bad id, auth, network)."""


def parse_playlist_id(url_or_id: str) -> Optional[str]:
    text = (url_or_id or "").strip()
    if not text:
        return None
    match = _PLAYLIST_ID_RE.search(text)
    if match:
        return match.group(1)
    if _BARE_ID_RE.match(text):
        return text
    return None


class SpotifyClient:
    def __init__(self, client_id: str):
        self._client_id = (client_id or "").strip()
        self._sp: Optional[Spotify] = None

    def _auth_manager(self) -> SpotifyPKCE:
        _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        return SpotifyPKCE(
            client_id=self._client_id,
            redirect_uri=REDIRECT_URI,
            scope=_SCOPE,
            open_browser=True,
            cache_handler=CacheFileHandler(cache_path=str(_TOKEN_CACHE)),
        )

    def has_cached_token(self) -> bool:
        """True if a previously-authorized token exists (even if expired - PKCE
        refreshes it silently), so we can skip the browser prompt."""
        if not self._client_id:
            return False
        try:
            token = self._auth_manager().cache_handler.get_cached_token()
            return bool(token)
        except Exception:
            return False

    def connect(self):
        """Authorize (opening the browser + a local 127.0.0.1:8888 listener on
        first run) and build the API client. Blocking - call off the GUI
        thread. Raises SpotifyError on failure."""
        if not self._client_id:
            raise SpotifyError("No Spotify Client ID set.")
        try:
            auth = self._auth_manager()
            # Triggers the interactive login only if there's no usable token.
            auth.get_access_token(check_cache=True)
            self._sp = Spotify(auth_manager=auth)
            self._sp.current_user()  # verify the token actually works
        except SpotifyError:
            raise
        except Exception as exc:
            raise SpotifyError(f"Spotify sign-in failed: {exc}") from exc

    def get_playlist_tracks(self, url_or_id: str) -> List[PlaylistTrack]:
        """Return every track's title/artist/duration, following pagination."""
        if self._sp is None:
            raise SpotifyError("Not connected to Spotify.")
        playlist_id = parse_playlist_id(url_or_id)
        if not playlist_id:
            raise SpotifyError("That doesn't look like a Spotify playlist link.")

        tracks: List[PlaylistTrack] = []
        offset = 0
        page_size = 100
        try:
            while True:
                page = self._sp.playlist_items(
                    playlist_id,
                    offset=offset,
                    limit=page_size,
                    additional_types=("track",),
                )
                items = page.get("items", [])
                for item in items:
                    # Spotify's playlist-item shape shifted: the track object
                    # now comes back under "item" rather than the historical
                    # "track", so accept whichever is present.
                    track = item.get("track") or item.get("item") or {}
                    name = track.get("name")
                    if not name:
                        continue  # local files / unavailable tracks
                    artists = track.get("artists") or []
                    artist = artists[0]["name"] if artists else ""
                    tracks.append(
                        PlaylistTrack(
                            title=name,
                            artist=artist,
                            duration_ms=int(track.get("duration_ms") or 0),
                        )
                    )
                if len(items) < page_size:
                    break
                offset += page_size
        except Exception as exc:
            raise SpotifyError(f"Couldn't read the playlist: {exc}") from exc
        return tracks
