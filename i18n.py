"""Tiny UI localisation helper.

Strings are keyed by their English text, so `tr("Settings")` returns the
translation for the active language or falls back to the English key itself.
The active language is chosen once at startup from the saved setting; the
menus and settings panel are built with `tr(...)` at that point, so changing
language takes effect on the next launch (runtime status strings that are
re-set each poll pick it up immediately).
"""

# Language code -> human-readable name shown in the picker (in its own script).
LANGUAGES = {
    "en": "English",
    "zh_TW": "繁體中文",
}

_TRANSLATIONS = {
    "en": {},  # English keys map to themselves.
    "zh_TW": {
        # Tray menu
        "Hide Lyrics": "隱藏歌詞",
        "Show Lyrics": "顯示歌詞",
        "Move Overlay": "移動視窗",
        "Copy current line": "複製目前歌詞",
        "Settings...": "設定...",
        "Exit": "結束",
        "Spotify Floating Lyrics": "Spotify 浮動歌詞",
        # Overlay
        "Waiting for Spotify...": "等待 Spotify...",
        "Loading lyrics...": "載入歌詞中...",
        "No lyrics found": "找不到歌詞",
        "unsynced": "非同步",
        # Settings panel
        "Settings": "設定",
        "Size": "大小",
        "Opacity": "透明度",
        "Acrylic effect (Win10+)": "壓克力效果 (Win10+)",
        "Lyrics only (no background)": "僅顯示歌詞（無背景）",
        "Single line (one lyric at a time)": "只顯示一行歌詞",
        "Show playback controls": "顯示播放控制列",
        "Start with Windows": "開機時啟動",
        "Language": "語言",
        "Restart the app to apply the language change.": "重新啟動應用程式以套用語言變更。",
        "Theme": "主題",
        "Dark": "深色",
        "Light": "淺色",
        "Lyrics Color": "歌詞顏色",
        "Background": "背景",
        "UI Accent": "介面強調色",
        "Clear lyrics cache": "清除歌詞快取",
        "Cache cleared ✓": "已清除快取 ✓",
        # Pre-cache section
        "Pre-cache a playlist": "預先快取播放清單",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "提前下載 Spotify 播放清單中每首歌的歌詞。需要一組免費的 Spotify "
            "Client ID（開發者主控台），重新導向 URI 為 "
            "http://127.0.0.1:8888/callback。",
        "Playlist link": "播放清單連結",
        "Pre-cache lyrics": "預先快取歌詞",
        "Enter your Spotify Client ID first.": "請先輸入 Spotify Client ID。",
        "Paste a playlist link first.": "請先貼上播放清單連結。",
        "Starting…": "開始中…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "完成 — 新增 {saved}，已有 {cached}，找不到 {failed}",
        # Clear-cache confirmation dialog
        "Delete all cached lyrics?": "刪除所有已快取的歌詞？",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.": "已儲存的歌詞將被移除，並在下次播放時重新下載。",
        "Delete": "刪除",
        "Cancel": "取消",
        # Colour picker dialog
        "Choose {name} Color": "選擇{name}顏色",
    },
}

_current = "en"


def set_language(code: str) -> None:
    global _current
    _current = code if code in _TRANSLATIONS else "en"


def language() -> str:
    return _current


def tr(key: str) -> str:
    return _TRANSLATIONS.get(_current, {}).get(key, key)
