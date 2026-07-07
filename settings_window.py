"""A small settings panel, styled like the overlay, for tweaking its size
and background opacity live. Opened from the tray icon.
"""

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent
from PySide6.QtWidgets import QApplication, QCheckBox, QColorDialog, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from overlay import (
    DEFAULT_OPACITY_PERCENT,
    DEFAULT_SCALE_PERCENT,
    MAX_OPACITY_PERCENT,
    MAX_SCALE_PERCENT,
    MIN_OPACITY_PERCENT,
    MIN_SCALE_PERCENT,
)


class SettingsWindow(QWidget):
    scale_changed = Signal(int)
    opacity_changed = Signal(int)
    controls_toggled = Signal(bool)
    lyrics_color_changed = Signal(QColor)
    bg_color_changed = Signal(QColor)
    accent_color_changed = Signal(QColor)

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
            )
        )

        self.controls_checkbox = QCheckBox("Show playback controls")
        self.controls_checkbox.toggled.connect(self.controls_toggled)
        layout.addWidget(self.controls_checkbox)

        # --- Color pickers ---
        layout.addLayout(self._make_color_row("Lyrics Color", self._lyrics_color, "lyrics"))
        layout.addLayout(self._make_color_row("Background", self._bg_color, "bg"))
        layout.addLayout(self._make_color_row("UI Theme", self._accent_color, "accent"))

        layout.addStretch()

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
        self._update_accent_style()

    def _make_slider_row(self, name, minimum, maximum, default, value_label, on_change):
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
        return row

    def _on_scale_changed(self, value: int):
        self.size_value_label.setText(f"{value}%")
        self.scale_changed.emit(value)

    def _on_opacity_changed(self, value: int):
        self.opacity_value_label.setText(f"{value}%")
        self.opacity_changed.emit(value)

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
