"""A small settings panel, styled like the overlay, for tweaking its size
and background opacity live. Opened from the tray icon.
"""

import json
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QColorDialog
)
from overlay import (
    DEFAULT_OPACITY_PERCENT,
    DEFAULT_SCALE_PERCENT,
    MAX_OPACITY_PERCENT,
    MAX_SCALE_PERCENT,
    MIN_OPACITY_PERCENT,
    MIN_SCALE_PERCENT,
)

_CONFIG_PATH = (
    Path(os.getenv("LOCALAPPDATA", str(Path.home())))
    / "SpotifyFloatingLyrics"
    / "config.json"
)


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_config(data: dict):
    try:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass

_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        height: 4px;
        background: rgba(255,255,255,60);
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #1DB954;
        width: 14px;
        margin: -6px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #1DB954;
        border-radius: 2px;
    }
    QCheckBox {
        color: white;
        background: transparent;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,90);
        background: transparent;
    }
    QCheckBox::indicator:checked {
        background: #1DB954;
        border: 1px solid #1DB954;
    }
    QPushButton#clearcache, QPushButton#precache {
        background-color: rgba(255,255,255,18);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 7px;
    }
    QPushButton#clearcache:hover, QPushButton#precache:hover {
        background-color: rgba(255,255,255,32);
    }
    QPushButton#precache:disabled {
        color: rgba(255,255,255,90);
    }
    QLineEdit {
        background-color: rgba(255,255,255,15);
        color: white;
        border: 1px solid rgba(255,255,255,40);
        border-radius: 6px;
        padding: 5px 8px;
        selection-background-color: #1DB954;
    }
    QLineEdit:focus {
        border: 1px solid #1DB954;
    }
"""

_CONFIRM_STYLE = """
    QMessageBox {
        background-color: #1e1e1e;
    }
    QMessageBox QLabel {
        color: white;
    }
    QMessageBox QPushButton {
        background-color: #333333;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 18px;
        min-width: 64px;
    }
    QMessageBox QPushButton:hover {
        background-color: #444444;
    }
    QMessageBox QPushButton:default {
        background-color: #1DB954;
    }
    QMessageBox QPushButton:default:hover {
        background-color: #1ed760;
    }
    QPushButton#clearcache {
        background-color: rgba(255,255,255,18);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 7px;
    }
    QPushButton#clearcache:hover {
        background-color: rgba(255,255,255,32);
    }
"""


class SettingsWindow(QWidget):
    scale_changed = Signal(int)
    opacity_changed = Signal(int)
    controls_toggled = Signal(bool)
    lyrics_color_changed = Signal(QColor)
    bg_color_changed = Signal(QColor)
    accent_color_changed = Signal(QColor)
    clear_cache_requested = Signal()
    precache_requested = Signal(str, str)  # client_id, playlist_url

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(320, 380)

        self._drag_offset: Optional[QPoint] = None
        self._lyrics_color = QColor(Qt.white)
        self._bg_color = QColor(18, 18, 18)
        self._accent_color = QColor("#1DB954")
        self._build_ui()
        # Size to exactly fit the content so there's no dead space below the
        # last control, rather than the fixed height above.
        self.resize(320, self.card.sizeHint().height())
        self._move_to_default_position()

    def _build_ui(self):
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setGeometry(0, 0, self.width(), self.height())

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        self.size_value_label = QLabel()
        layout.addLayout(
            self._make_slider_row(
                "Size",
                MIN_SCALE_PERCENT,
                MAX_SCALE_PERCENT,
                DEFAULT_SCALE_PERCENT,
                self.size_value_label,
                self._on_scale_changed,
                slider_attr="_size_slider",
            )
        )

        self.opacity_value_label = QLabel()
        layout.addLayout(
            self._make_slider_row(
                "Opacity",
                MIN_OPACITY_PERCENT,
                MAX_OPACITY_PERCENT,
                DEFAULT_OPACITY_PERCENT,
                self.opacity_value_label,
                self._on_opacity_changed,
                slider_attr="_opacity_slider",
            )
        )

        self.controls_checkbox = QCheckBox("Show playback controls")
        self.controls_checkbox.toggled.connect(self.controls_toggled)
        layout.addWidget(self.controls_checkbox)

        # --- Color pickers ---
        layout.addLayout(self._make_color_row("Lyrics Color", self._lyrics_color, "lyrics"))
        layout.addLayout(self._make_color_row("Background", self._bg_color, "bg"))
        layout.addLayout(self._make_color_row("UI Accent", self._accent_color, "accent"))
        self.clear_cache_button = QPushButton("Clear lyrics cache")
        self.clear_cache_button.setObjectName("clearcache")
        self.clear_cache_button.setCursor(Qt.PointingHandCursor)
        self.clear_cache_button.clicked.connect(self._confirm_clear_cache)
        layout.addWidget(self.clear_cache_button)

        self._build_precache_section(layout)

        self.close_button = QLabel("✕", self)
        self.close_button.setStyleSheet("color: rgba(255,255,255,140);")
        self.close_button.setFont(QFont("Segoe UI", 10))
        self.close_button.move(self.width() - 26, 8)
        self.close_button.mousePressEvent = lambda _event: self.hide()

        self._update_accent_style()

    def _make_color_row(self, name: str, color: QColor, target: str):
        row = QHBoxLayout()
        row.setSpacing(10)

        label = QLabel(name)
        label.setFixedWidth(70)

        preview = QLabel()
        preview.setFixedSize(20, 20)
        preview.setStyleSheet(
            f"background-color: {color.name()}; border-radius: 3px; border: 1px solid rgba(255,255,255,60);"
        )
        preview.mousePressEvent = lambda _e, t=target: self._pick_color(t)

        hex_label = QLabel(color.name().upper())
        hex_label.setFixedWidth(60)

        row.addWidget(label)
        row.addWidget(preview)
        row.addWidget(hex_label)
        row.addStretch()

        setattr(self, f"_{target}_preview", preview)
        setattr(self, f"_{target}_hex", hex_label)
        return row

    def _pick_color(self, target: str):
        current = getattr(self, f"_{target}_color")
        color = QColorDialog.getColor(current, self, f"Choose {target.title()} Color")
        if not color.isValid():
            return
        setattr(self, f"_{target}_color", color)
        preview: QLabel = getattr(self, f"_{target}_preview")
        hex_label: QLabel = getattr(self, f"_{target}_hex")
        preview.setStyleSheet(
            f"background-color: {color.name()}; border-radius: 3px; border: 1px solid rgba(255,255,255,60);"
        )
        hex_label.setText(color.name().upper())

        signal_map = {
            "lyrics": self.lyrics_color_changed,
            "bg": self.bg_color_changed,
            "accent": self.accent_color_changed,
        }
        signal_map[target].emit(color)
        if target == "accent":
            self._update_accent_style()

    def _update_accent_style(self):
        accent = self._accent_color.name()
        self.setStyleSheet(
            f"""
            #card {{
                background-color: rgba(18, 18, 18, 235);
                border-radius: 16px;
            }}
            QLabel {{
                color: white;
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: rgba(255,255,255,60);
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                width: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 2px;
            }}
            QCheckBox {{
                color: white;
                background: transparent;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(255,255,255,90);
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border: 1px solid {accent};
            }}
            QPushButton#clearcache {{
                background-color: rgba(255,255,255,18);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 7px;
            }}
            QPushButton#clearcache:hover {{
                background-color: rgba(255,255,255,32);
            }}
            """
        )

    def set_colors(self, lyrics_color: QColor, bg_color: QColor, accent_color: QColor):
        for target, color in [("lyrics", lyrics_color), ("bg", bg_color), ("accent", accent_color)]:
            setattr(self, f"_{target}_color", color)
            preview: QLabel = getattr(self, f"_{target}_preview")
            hex_label: QLabel = getattr(self, f"_{target}_hex")
            preview.setStyleSheet(
                f"background-color: {color.name()}; border-radius: 3px; border: 1px solid rgba(255,255,255,60);"
            )
            hex_label.setText(color.name().upper())
        self.accent_color_changed.emit(accent_color)
        self._update_accent_style()
        self.style().unpolish(self)
        self.style().polish(self)

    def _make_slider_row(self, name, minimum, maximum, default, value_label, on_change, slider_attr=None):
        row = QHBoxLayout()
        row.setSpacing(10)
        name_label = QLabel(name)
        name_label.setFixedWidth(56)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(default)
        slider.valueChanged.connect(on_change)
        value_label.setFixedWidth(42)
        value_label.setText(f"{default}%")
        row.addWidget(name_label)
        row.addWidget(slider)
        row.addWidget(value_label)
        if slider_attr:
            setattr(self, slider_attr, slider)
        return row

    def set_scale_value(self, percent: int):
        """Set the Size slider (used to restore the saved size on launch)."""
        self._size_slider.setValue(percent)

    def set_opacity_value(self, percent: int):
        """Set the Opacity slider (used to restore the saved opacity)."""
        self._opacity_slider.setValue(percent)

    def _build_precache_section(self, layout):
        heading = QLabel("Pre-cache a playlist")
        heading.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(heading)

        hint = QLabel(
            "Downloads lyrics for every song in a Spotify playlist ahead of "
            "time. Needs a free Spotify Client ID (Developer Dashboard) with "
            "redirect URI http://127.0.0.1:8888/callback."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgba(255,255,255,120);")
        hint.setFont(QFont("Segoe UI", 8))
        layout.addWidget(hint)

        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("Spotify Client ID")
        self.client_id_edit.setText(_load_config().get("client_id", ""))
        layout.addWidget(self.client_id_edit)

        self.playlist_edit = QLineEdit()
        self.playlist_edit.setPlaceholderText("Playlist link")
        layout.addWidget(self.playlist_edit)

        self.precache_button = QPushButton("Pre-cache lyrics")
        self.precache_button.setObjectName("precache")
        self.precache_button.setCursor(Qt.PointingHandCursor)
        self.precache_button.clicked.connect(self._on_precache_clicked)
        layout.addWidget(self.precache_button)

        self.precache_status = QLabel("")
        self.precache_status.setWordWrap(True)
        self.precache_status.setStyleSheet("color: rgba(255,255,255,150);")
        self.precache_status.setFont(QFont("Segoe UI", 8))
        layout.addWidget(self.precache_status)

    def _on_precache_clicked(self):
        client_id = self.client_id_edit.text().strip()
        playlist = self.playlist_edit.text().strip()
        if not client_id:
            self.precache_status.setText("Enter your Spotify Client ID first.")
            return
        if not playlist:
            self.precache_status.setText("Paste a playlist link first.")
            return
        _save_config({"client_id": client_id})
        self.precache_button.setEnabled(False)
        self.precache_status.setText("Starting…")
        self.precache_requested.emit(client_id, playlist)

    # --- called by the controller as the background pre-cache progresses ---
    def set_precache_progress(self, done: int, total: int, label: str):
        if total > 0:
            self.precache_status.setText(f"{done} / {total}   {label}")
        else:
            self.precache_status.setText(label)

    def set_precache_finished(self, saved: int, cached: int, failed: int):
        self.precache_button.setEnabled(True)
        self.precache_status.setText(
            f"Done — {saved} added, {cached} already cached, {failed} not found"
        )

    def set_precache_error(self, message: str):
        self.precache_button.setEnabled(True)
        self.precache_status.setText(message)

    def _on_scale_changed(self, value: int):
        self.size_value_label.setText(f"{value}%")
        self.scale_changed.emit(value)

    def _on_opacity_changed(self, value: int):
        self.opacity_value_label.setText(f"{value}%")
        self.opacity_changed.emit(value)

    def _confirm_clear_cache(self):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Clear lyrics cache")
        box.setText("Delete all cached lyrics?")
        box.setInformativeText(
            "Saved lyrics will be removed and re-downloaded the next time "
            "each song plays."
        )
        box.setStyleSheet(_CONFIRM_STYLE)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        box.button(QMessageBox.Yes).setText("Delete")
        box.button(QMessageBox.No).setText("Cancel")
        if box.exec() == QMessageBox.Yes:
            self.clear_cache_requested.emit()
            self.clear_cache_button.setText("Cache cleared ✓")
            QTimer.singleShot(
                2000, lambda: self.clear_cache_button.setText("Clear lyrics cache")
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.card.setGeometry(0, 0, self.width(), self.height())
        self.close_button.move(self.width() - 26, 8)

    def _move_to_default_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.center().y() - self.height() // 2
        self.move(x, y)

    def open(self):
        self.show()
        self.raise_()
        self.activateWindow()

    # --- dragging: unlike the overlay, this is a normal interactive window ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_offset = None
        event.accept()
