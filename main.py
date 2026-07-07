import ctypes
import os
import sys

# A --windowed/--noconsole build has no console, so sys.stdout/stderr are
# None. Any incidental print() (e.g. syncedlyrics logging a provider
# timeout) would then raise AttributeError writing to a None stream and can
# take the whole process down. Give them a real sink before anything else runs.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# A PyInstaller-built exe has no manifest declaring per-monitor DPI
# awareness, so Windows falls back to bitmap-stretching the whole window
# when it's moved to a monitor with a different scale factor - that's the
# "size goes enormous" bug. Declaring awareness explicitly, before
# QApplication exists, makes Windows hand the window native, correctly
# re-rendered content on every monitor instead of a stretched bitmap.
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
except (AttributeError, OSError):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

from PySide6.QtCore import QObject, QSettings, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from control_bar import ControlBar
from lyrics import LyricsFetcher, LyricsResult
from media_session import MediaSessionWatcher, NowPlaying
from overlay import DEFAULT_OPACITY_PERCENT, DEFAULT_SCALE_PERCENT, OverlayWindow
from position_tracker import PositionTracker
from precache_worker import PlaylistPrecacher, UpcomingPrecacher
from settings_window import SettingsWindow
from tray_icon import TrayIcon


def _spread_evenly(result: LyricsResult, duration_ms: int) -> LyricsResult:
    # Plain lyrics have no real timing, only line order. Assigning them
    # evenly-spaced timestamps across the track's duration lets the overlay
    # scroll through them like normal lyrics instead of showing every line
    # at once crammed into a single row.
    if not result.lines:
        return result
    count = len(result.lines)
    spaced_lines = [
        (int(i * duration_ms / count), text) for i, (_, text) in enumerate(result.lines)
    ]
    return LyricsResult(lines=spaced_lines, synced=result.synced)


class AppController(QObject):
    # Must be a QObject (not a plain class) so Qt knows its thread affinity
    # is the GUI thread: watcher/lyrics_fetcher emit from worker threads, and
    # without that affinity Qt calls these slots directly on those threads
    # instead of queuing them, which would touch widgets off the GUI thread.
    def __init__(self):
        super().__init__()
        self.watcher = MediaSessionWatcher()
        self.lyrics_fetcher = LyricsFetcher()
        self.overlay = OverlayWindow()
        self.position_tracker = PositionTracker()
        self.settings_window = SettingsWindow()
        self.control_bar = ControlBar()
        self.tray_icon = TrayIcon()
        self.precacher = PlaylistPrecacher()
        self.upcoming_precacher = UpcomingPrecacher()

        self.current_now_playing: NowPlaying | None = None
        self.current_lyrics: LyricsResult | None = None

        self.watcher.track_changed.connect(self._on_track_changed)
        self.watcher.state_updated.connect(self._on_state_updated)
        self.watcher.no_session.connect(self._on_no_session)

        self.lyrics_fetcher.lyrics_loading.connect(self._on_lyrics_loading)
        self.lyrics_fetcher.lyrics_ready.connect(self._on_lyrics_ready)
        self.lyrics_fetcher.lyrics_failed.connect(self._on_lyrics_failed)

        self.tray_icon.toggle_requested.connect(self._toggle_overlay_visibility)
        self.tray_icon.movable_toggled.connect(self.overlay.set_movable)
        self.tray_icon.settings_requested.connect(self.settings_window.open)
        self.tray_icon.quit_requested.connect(QApplication.instance().quit)

        self.settings_window.scale_changed.connect(self.overlay.set_scale)
        self.settings_window.scale_changed.connect(self.control_bar.set_scale)
        self.settings_window.opacity_changed.connect(self.overlay.set_opacity)
        self.settings_window.opacity_changed.connect(self.control_bar.set_opacity)
        self.settings_window.controls_toggled.connect(self._toggle_control_bar)
        self.settings_window.clear_cache_requested.connect(self.lyrics_fetcher.clear_cache)
        self.settings_window.precache_requested.connect(self.precacher.start)

        self.precacher.progress.connect(self.settings_window.set_precache_progress)
        self.precacher.finished.connect(self.settings_window.set_precache_finished)
        self.precacher.failed.connect(self.settings_window.set_precache_error)

        self.settings_window.lyrics_color_changed.connect(self._on_lyrics_color_changed)
        self.settings_window.bg_color_changed.connect(self._on_bg_color_changed)
        self.settings_window.accent_color_changed.connect(self._on_accent_color_changed)

        settings = QSettings("SpotifyFloatingLyrics", "SpotifyFloatingLyrics")
        lyrics_color = settings.value("lyrics/color", QColor(Qt.white))
        bg_color = settings.value("background/color", QColor(18, 18, 18))
        accent_color = settings.value("accent/color", QColor("#1DB954"))
        if isinstance(lyrics_color, str):
            lyrics_color = QColor(lyrics_color)
        if isinstance(bg_color, str):
            bg_color = QColor(bg_color)
        if isinstance(accent_color, str):
            accent_color = QColor(accent_color)
        self.overlay.set_lyrics_color(lyrics_color)
        self.overlay.set_bg_color(bg_color)
        self.control_bar.set_accent_color(accent_color)
        self.tray_icon.set_accent_color(accent_color)
        self.settings_window.set_colors(lyrics_color, bg_color, accent_color)

        # Restore the overlay's saved size, opacity, and on-screen position so
        # it reopens exactly where (and how big) the user last left it. Size is
        # applied before position: it's set while the overlay is still hidden
        # (so it resizes without re-centering), then moved to the saved spot.
        self._settings = settings
        saved_scale = int(settings.value("overlay/scale", DEFAULT_SCALE_PERCENT))
        saved_opacity = int(settings.value("overlay/opacity", DEFAULT_OPACITY_PERCENT))
        self.settings_window.set_scale_value(saved_scale)
        self.settings_window.set_opacity_value(saved_opacity)
        saved_x = settings.value("overlay/pos_x")
        saved_y = settings.value("overlay/pos_y")
        if saved_x is not None and saved_y is not None:
            self.overlay.move(int(saved_x), int(saved_y))

        self.settings_window.scale_changed.connect(self._save_scale)
        self.settings_window.opacity_changed.connect(self._save_opacity)
        self.overlay.drag_finished.connect(self._save_position)

        self.overlay.geometry_changed.connect(self._sync_control_bar_position)

        self.control_bar.play_pause_clicked.connect(self.watcher.toggle_play_pause)
        self.control_bar.next_clicked.connect(self.watcher.skip_next)
        self.control_bar.previous_clicked.connect(self.watcher.skip_previous)
        self.control_bar.seek_requested.connect(self.watcher.seek)

        self.tick_timer = QTimer()
        self.tick_timer.setInterval(200)
        self.tick_timer.timeout.connect(self._tick)
        self.tick_timer.start()

    def start(self):
        self.overlay.show()
        self.tray_icon.show()
        self.watcher.start()

    def _toggle_overlay_visibility(self):
        visible = not self.overlay.isVisible()
        self.overlay.setVisible(visible)
        self.tray_icon.set_visible_state(visible)
        # The attached control bar shares the overlay's fate; it comes back
        # only if its settings checkbox is still on.
        self.control_bar.setVisible(visible and self.settings_window.controls_checkbox.isChecked())
        if self.control_bar.isVisible():
            self.control_bar.follow(self.overlay.geometry())

    def _toggle_control_bar(self, enabled: bool):
        self.control_bar.setVisible(enabled)
        self.overlay.set_attached(enabled)
        if enabled:
            self.control_bar.follow(self.overlay.geometry())

    def _on_lyrics_color_changed(self, color: QColor):
        self.overlay.set_lyrics_color(color)
        QSettings("SpotifyFloatingLyrics", "SpotifyFloatingLyrics").setValue("lyrics/color", color)

    def _on_bg_color_changed(self, color: QColor):
        self.overlay.set_bg_color(color)
        QSettings("SpotifyFloatingLyrics", "SpotifyFloatingLyrics").setValue("background/color", color)

    def _on_accent_color_changed(self, color: QColor):
        self.control_bar.set_accent_color(color)
        self.tray_icon.set_accent_color(color)
        QSettings("SpotifyFloatingLyrics", "SpotifyFloatingLyrics").setValue("accent/color", color)

    def _save_scale(self, percent: int):
        self._settings.setValue("overlay/scale", int(percent))
        self._settings.sync()  # flush now, not just on (possibly abrupt) exit

    def _save_opacity(self, percent: int):
        self._settings.setValue("overlay/opacity", int(percent))
        self._settings.sync()

    def _save_position(self):
        pos = self.overlay.pos()
        self._settings.setValue("overlay/pos_x", pos.x())
        self._settings.setValue("overlay/pos_y", pos.y())
        self._settings.sync()

    def _sync_control_bar_position(self):
        if self.control_bar.isVisible():
            self.control_bar.follow(self.overlay.geometry())

    def _on_track_changed(self, now_playing: NowPlaying):
        self.current_now_playing = now_playing
        self.current_lyrics = None
        self.position_tracker.update(now_playing.position_ms, now_playing.is_playing, now_playing.duration_ms)
        self.overlay.set_track_info(now_playing.title, now_playing.artist)
        self.overlay.set_approximate(False)  # reset until lyrics arrive
        self.control_bar.set_playing(now_playing.is_playing)
        self.lyrics_fetcher.request(
            now_playing.title, now_playing.artist, now_playing.duration_ms
        )
        # Best-effort: pre-cache the next queued song's lyrics so it's ready
        # instantly when this one ends (needs Spotify connected with the
        # playback scope; silently does nothing otherwise).
        self.upcoming_precacher.peek_and_cache(
            self.settings_window.client_id_edit.text().strip()
        )

    def _on_state_updated(self, now_playing: NowPlaying):
        self.current_now_playing = now_playing
        self.position_tracker.update(now_playing.position_ms, now_playing.is_playing, now_playing.duration_ms)
        self.control_bar.set_playing(now_playing.is_playing)

    def _on_no_session(self):
        self.current_now_playing = None
        self.current_lyrics = None
        self.overlay.show_idle("Waiting for Spotify...")

    def _on_lyrics_loading(self, _title, _artist):
        self.overlay.show_status("Loading lyrics...")

    def _on_lyrics_ready(self, title, _artist, result: LyricsResult):
        if self.current_now_playing and self.current_now_playing.title == title:
            if not result.synced and self.current_now_playing.duration_ms:
                result = _spread_evenly(result, self.current_now_playing.duration_ms)
            self.current_lyrics = result
            self.overlay.set_approximate(not result.synced)
            self.overlay.set_lyrics(result)

    def _on_lyrics_failed(self, title, _artist):
        if self.current_now_playing and self.current_now_playing.title == title:
            self.overlay.show_status("No lyrics found")

    def _tick(self):
        if self.current_now_playing is None:
            return
        position_ms = self.position_tracker.estimated_position_ms()
        self.control_bar.set_progress(position_ms, self.current_now_playing.duration_ms)
        if self.current_lyrics is not None:
            self.overlay.update_position(position_ms)


def main():
    app = QApplication(sys.argv)
    # Hiding the overlay via the tray toggle must not quit the app - only
    # the tray menu's Exit action should.
    app.setQuitOnLastWindowClosed(False)

    controller = AppController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
