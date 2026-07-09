# Spotify Floating Lyrics

**English** | [繁體中文](#spotify-浮動歌詞)

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
- **Language** — switch the interface language (English, 繁體中文, 简体中文,
  日本語, 한국어, Español, Français, Deutsch, Português, Русский; restart the
  app to apply).
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

---

# Spotify 浮動歌詞

[English](#spotify-floating-lyrics) | **繁體中文**

一個小巧、永遠置頂的浮動視窗，顯示 Spotify 桌面版目前播放歌曲的同步歌詞。

- 直接透過 Windows 的系統媒體傳輸控制（System Media Transport Controls，與音量
  彈出視窗使用的相同 API）讀取正在播放的資訊，因此不需要 Spotify 登入或 API
  金鑰。需要 Spotify 桌面應用程式（不能只用瀏覽器分頁）。
- 透過 [syncedlyrics](https://github.com/moehmeni/syncedlyrics) 取得時間同步歌詞，
  並在歌曲播放時標示目前的歌詞行。

## 執行預先建置的 .exe（建議）

[`dist/SpotifyFloatingLyrics.exe`](dist/SpotifyFloatingLyrics.exe) 是獨立的建置版本 — 直接雙擊即可，
不需要安裝 Python。首次執行時，Windows 可能會對未簽署的 exe 顯示 SmartScreen
警告；點選「更多資訊」->「仍要執行」。

## 使用方式

啟動後會出現兩樣東西：

**歌詞浮動視窗**會顯示在螢幕上方附近。它預設為*點擊穿透*——滑鼠點擊會直接穿過它，
作用在底下的視窗（Spotify、遊戲、桌面等），因此絕不會擋路。

**系統匣圖示**——一個綠色的小 **「L」**。如果你不確定「系統匣」是什麼：它是 Windows
工作列最右端、時鐘旁邊那一小群圖示（微軟也稱之為*通知區域*）。Windows 常會把較少
使用的圖示收在那裡的向上箭頭（**^**）按鈕後面，所以如果沒有立刻看到綠色的「L」，
請點一下那個 **^** 箭頭把它展開。接著你可以把圖示拖曳到時鐘旁邊，讓它固定顯示。

由於浮動視窗本身是點擊穿透的，你無法直接點擊它——所有操作都改由這個系統匣圖示進行：

- **左鍵點擊**圖示可快速顯示或隱藏浮動視窗。
- **右鍵點擊**圖示開啟完整選單：
  - **顯示 / 隱藏歌詞**——開啟或關閉浮動視窗。
  - **移動視窗**——暫時讓浮動視窗可拖曳，方便你用滑鼠重新定位；再關閉它即可鎖回
    點擊穿透狀態。它的位置會在下次開啟應用程式時記住。
  - **複製目前歌詞**——將目前螢幕上的歌詞行複製到剪貼簿。
  - **設定...**——開啟設定面板（見下方）。
  - **結束**——完全退出應用程式（從系統匣隱藏浮動視窗只是把它藏起來；這才是完全
    停止程式的方式）。

### 設定

從系統匣選單選擇**設定...**，會開啟一個小面板，變更會即時套用：

- 浮動視窗的**大小**與**透明度**——兩者都會在每次啟動間記住。
- **主題**——一鍵切換**深色** / **淺色**預設，或自訂**歌詞**、**背景**與**強調色**。
- **壓克力效果 (Win10+)**——在浮動視窗後方選用的毛玻璃模糊效果。
- **僅顯示歌詞（無背景）**——隱藏面板，只讓文字浮動顯示。
- **只顯示一行歌詞**——只顯示目前的歌詞，而不顯示上下方較暗的前一行／下一行。
- **語言**——切換介面語言（English、繁體中文、简体中文、日本語、한국어、Español、
  Français、Deutsch、Português、Русский；需重新啟動應用程式才會套用）。
- **顯示播放控制列**——在浮動視窗底部加上 Spotify 風格的上一首／播放暫停／下一首
  控制列與可拖曳的進度條。即使歌詞維持點擊穿透，這個控制列仍可點擊。
- **開機時啟動**——登入時自動啟動應用程式（會安靜地在系統匣中啟動）。
- **清除歌詞快取**，以及**預先快取播放清單**（見下方）。

## 預先快取播放清單

一般情況下，歌詞會在每首歌第一次播放時才抓取。預先快取會提前下載 Spotify 播放
清單中每一首歌的歌詞，因此之後播放這些歌曲時歌詞會立即出現（且可離線使用）。

這是唯一需要（免費）Spotify Client ID 的功能——僅用於讀取播放清單的曲目列表。
應用程式不會儲存任何 client secret；它使用 Spotify 的 PKCE 登入流程，因此只需一次
瀏覽器登入即可。

### 1. 建立 Spotify 應用程式以取得 Client ID

前往 [Spotify 開發者主控台](https://developer.spotify.com/dashboard)，然後：
 - 點選 **Create app**（建立應用程式）。
 - 填入任意名稱與說明（內容不重要）。
 - 將 **Redirect URI** 設為完全相同的 `http://127.0.0.1:8888/callback`。
 - 在「Which API/SDKs are you planning to use?」下方勾選 **Web API**。
 - 儲存後，開啟該應用程式的 **Settings**，複製 **Client ID**。

### 2. 在應用程式中預先快取播放清單

 - 開啟系統匣選單（綠色「L」圖示），選擇**設定...**。
 - 捲動到**預先快取播放清單**區塊。
 - 將你的 **Client ID** 貼到「Spotify Client ID」欄位（會為下次記住）。
 - 將**播放清單連結**（例如 `https://open.spotify.com/playlist/...`）貼到「播放清單
   連結」欄位。
 - 點選**預先快取歌詞**。

第一次會開啟瀏覽器視窗要求你登入並授權應用程式——這是一次性的步驟，讓它能讀取你的
播放清單。進度會顯示在按鈕下方，完成後你會看到新增了多少歌詞、已快取多少、以及
找不到多少。

登入後，你可以預先快取任何公開播放清單，以及你自己的私人與協作播放清單。（Spotify
的 API 不允許讀取他人的私人播放清單，因此那些必須設為公開才能預先快取。）

## 設定（從原始碼執行）

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 從原始碼執行

```
.venv\Scripts\python main.py
```

這會啟動與預先建置 exe 相同的應用程式——浮動視窗與系統匣圖示的運作方式請見上方的
[使用方式](#使用方式)。

## 重新建置 .exe

```
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller --onefile --windowed --name SpotifyFloatingLyrics --collect-all winsdk main.py
```

輸出會產生在 `dist/SpotifyFloatingLyrics.exe`。必須加上 `--collect-all winsdk`——
否則 exe 會缺少存取 SMTC 所需的 WinRT 子模組。

## 附註

- 如果某首歌沒有可用的同步歌詞，純文字歌詞會依歌曲長度平均分配時間，讓它們仍以
  合理速度捲動，而不是一次全部顯示在螢幕上。如果完全找不到歌詞，浮動視窗會顯示提示。
- 目前的歌詞行若太長無法容納於一行，會換到第二行而不會被截斷；較暗的前一行／下一行
  則維持單行。
- 抓取到的歌詞會快取到 `%LOCALAPPDATA%\SpotifyFloatingLyrics\lyrics_cache`，因此重播
  歌曲（即使重新啟動應用程式後）也會略過網路抓取。
- 僅支援 Windows（使用 `winsdk` 套件存取 SMTC）。
