# Spotify Floating Lyrics

A small always-on-top overlay that shows synced lyrics for whatever is
currently playing in the Spotify desktop app.

- Reads now-playing info straight from Windows' System Media Transport
  Controls (the same API the volume flyout uses), so no Spotify login or API
  key is needed. Requires the Spotify desktop app (not just a browser tab).
- Fetches time-synced lyrics via [syncedlyrics](https://github.com/moehmeni/syncedlyrics)
  and highlights the current line as the song plays.

## Run the prebuilt .exe (Recommended)

[`dist/SpotifyFloatingLyrics.exe`](dist/SpotifyFloatingLyrics.exe) is a standalone build — just double-click it,
no Python install needed. Windows may show a SmartScreen warning for an
unsigned exe the first time; click "More info" -> "Run anyway".

## Pre-caching playlists
Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), then follow the instructions below:
 - Click on create app
 - App name and description does not matter, just make sure you fill in `http://127.0.0.1:8888/callback` in Redirect URLs
 - After filling in the URL, copy the CLIENT ID on top and fill it into 

## Setup (running from source)

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Run from source

```
.venv\Scripts\python main.py
```

The overlay appears near the top of your screen and is click-through by
default - mouse clicks pass straight to whatever's underneath it (Spotify, a
game, your desktop, etc.), so it never gets in the way.

A system tray icon (the green "L") appears in the notification area -
Windows may tuck it into the hidden icons ("^" chevron) by default; drag it
out to pin it visible. Left-click it, or use its right-click menu, to
show/hide the overlay. Check "Move Overlay" in the tray menu to temporarily
make it draggable so you can reposition it, then uncheck it to lock it back
to click-through. Use "Settings..." in the tray menu to adjust its size and
background opacity live, and to enable the playback control strip - a
Spotify-styled prev/play-pause/next + seekable progress bar that attaches
flush to the bottom of the overlay (the strip itself is clickable even
while the lyrics stay click-through). Use "Exit" in the tray menu to quit.

## Rebuilding the .exe

```
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller --onefile --windowed --name SpotifyFloatingLyrics --collect-all winsdk main.py
```

The output lands in `dist/SpotifyFloatingLyrics.exe`. `--collect-all winsdk`
is required — without it the exe is missing WinRT submodules needed for SMTC
access.

## Notes

- If a track has no synced lyrics available, plain lyrics are spread evenly
  across the track's duration so they still scroll at a reasonable pace
  instead of being dumped on screen all at once. If nothing is found at all,
  the overlay says so.
- The current line wraps to a second line instead of being cut off if it's
  too long to fit on one; the dimmed prev/next lines stay single-line.
- Fetched lyrics are cached to `%LOCALAPPDATA%\SpotifyFloatingLyrics\lyrics_cache`,
  so replaying a song (even after restarting the app) skips the network fetch.
- Windows only (uses the `winsdk` package for SMTC access).
