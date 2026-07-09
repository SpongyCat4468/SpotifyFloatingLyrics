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

## Using the app

Once it's running, two things appear:

**The lyrics overlay** shows near the top of your screen. It's *click-through*
by default — mouse clicks pass straight through it to whatever's underneath
(Spotify, a game, your desktop, etc.), so it never gets in the way.

**A system tray icon** — a small green **"L"**. If you're not sure what the
"system tray" is: it's the little cluster of icons at the far-right end of the
Windows taskbar, right next to the clock (Microsoft also calls it the
*notification area*). Windows often hides icons it thinks you use less behind a
small upward-arrow (**^**) button there, so if you don't immediately see the
green "L", click that **^** arrow to reveal it. You can then drag the icon out
next to the clock to keep it permanently visible.

Because the overlay itself is click-through, you can't click it directly — you
control everything from this tray icon instead:

- **Left-click** the icon to quickly show or hide the overlay.
- **Right-click** the icon for the full menu:
  - **Show / Hide Lyrics** — toggle the overlay on or off.
  - **Move Overlay** — temporarily makes the overlay draggable so you can
    reposition it with the mouse; turn it off again to lock it back to
    click-through. Its position is remembered the next time you open the app.
  - **Copy current line** — copies the lyric line currently on screen to your
    clipboard.
  - **Settings...** — opens the settings panel (below).
  - **Exit** — fully quits the app (closing the overlay from the tray only
    hides it; this is how you stop it completely).

### Settings

Choosing **Settings...** from the tray menu opens a small panel where changes
apply live:

- **Size** and **Opacity** of the overlay — both remembered between launches.
- **Theme** — one-click **Dark** / **Light** presets, or pick your own
  **Lyrics**, **Background**, and **Accent** colours.
- **Acrylic effect (Win10+)** — an optional frosted-glass blur behind the
  overlay.
- **Lyrics only (no background)** — hides the panel so only the text floats.
- **Single line (one lyric at a time)** — shows just the current lyric instead
  of the dimmed previous/next lines above and below it.
- **Language** — switch the interface between **English** and **繁體中文**
  (restart the app to apply).
- **Show playback controls** — adds a Spotify-styled prev / play-pause / next
  strip with a seekable progress bar, attached to the bottom of the overlay.
  The strip stays clickable even though the lyrics remain click-through.
- **Start with Windows** — launch the app automatically when you sign in
  (it starts quietly in the tray).
- **Clear lyrics cache**, and **Pre-cache a playlist** (see below).

## Pre-caching playlists

Normally lyrics are fetched the first time each song plays. Pre-caching
downloads the lyrics for every track in a Spotify playlist ahead of time, so
they appear instantly (and work offline) when you later play those songs.

This is the only feature that needs a (free) Spotify Client ID — used purely
to read a playlist's track list. No client secret is stored in the app; it
uses Spotify's PKCE login flow, so a one-time browser sign-in is all that's
required.

### 1. Create a Spotify app to get a Client ID

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and:
 - Click **Create app**.
 - Give it any name and description (these don't matter).
 - Set the **Redirect URI** to exactly `http://127.0.0.1:8888/callback`.
 - Under "Which API/SDKs are you planning to use?", tick **Web API**.
 - Save, then open the app's **Settings** and copy the **Client ID**.

### 2. Pre-cache a playlist in the app

 - Open the tray menu (the green "L" icon) and choose **Settings...**.
 - Scroll to the **Pre-cache a playlist** section.
 - Paste your **Client ID** into the "Spotify Client ID" box (it's remembered
   for next time).
 - Paste a **playlist link** (e.g. `https://open.spotify.com/playlist/...`)
   into the "Playlist link" box.
 - Click **Pre-cache lyrics**.

The first time, a browser window opens asking you to log in and authorize the
app — a one-time step so it can read your playlists. Progress is shown under
the button, and when it finishes you'll see how many lyrics were added, were
already cached, or couldn't be found.

You can pre-cache any public playlist, plus your own private and collaborative
playlists once you're signed in. (Spotify's API doesn't allow reading other
people's private playlists, so those must be public to be pre-cached.)

## Setup (running from source)

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Run from source

```
.venv\Scripts\python main.py
```

This launches the same app as the prebuilt exe — see [Using the app](#using-the-app)
above for how the overlay and the system tray icon work.

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
