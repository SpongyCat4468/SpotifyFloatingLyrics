"""A Spotify-styled playback strip (prev/play-pause/next, seekable progress
bar) that sits flush against the bottom edge of the overlay window - same
width, no gap, squared top corners - so the two windows read as one card.

It has to be its own native window (not a child of the overlay) because
click-through is a per-window flag: the lyrics stay click-through while
these controls must accept clicks.
"""

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget
from win32_effect import color_gradient, remove_background_effect, set_acrylic_effect

_BASE_BUTTON_SIZE = 30
_BASE_ICON_SIZE = 12
_BASE_TIME_PT = 8

_WHITE = QColor(255, 255, 255, 230)


def _format_time(ms: int) -> str:
    total_seconds = max(0, ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


class IconButton(QPushButton):
    """Flat button that draws its own vector icon (play/pause/prev/next),
    white normally and Spotify-green on hover - no emoji glyphs."""

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind  # 'play_pause' | 'prev' | 'next'
        self._playing = False
        self._accent_color = QColor("#1DB954")
        self._base_color = _WHITE
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._icon_size = _BASE_ICON_SIZE

    def set_playing(self, playing: bool):
        if self.kind == "play_pause" and playing != self._playing:
            self._playing = playing
            self.update()

    def set_sizes(self, button_px: int, icon_px: int):
        self.setFixedSize(button_px, button_px)
        self._icon_size = icon_px
        self.update()

    def set_accent_color(self, color: QColor):
        self._accent_color = color
        self.update()

    def set_base_color(self, color: QColor):
        self._base_color = color
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self._accent_color if self.underMouse() else self._base_color
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)

        s = self._icon_size
        cx = self.width() / 2
        cy = self.height() / 2
        half = s / 2

        path = QPainterPath()
        if self.kind == "play_pause":
            if self._playing:
                bar_w = s * 0.3
                gap = s * 0.4
                path.addRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - half, bar_w, s), 1.5, 1.5)
                path.addRoundedRect(QRectF(cx + gap / 2, cy - half, bar_w, s), 1.5, 1.5)
            else:
                path.moveTo(QPointF(cx - half * 0.7, cy - half))
                path.lineTo(QPointF(cx + half, cy))
                path.lineTo(QPointF(cx - half * 0.7, cy + half))
                path.closeSubpath()
        elif self.kind == "next":
            path.moveTo(QPointF(cx - half, cy - half))
            path.lineTo(QPointF(cx + half * 0.5, cy))
            path.lineTo(QPointF(cx - half, cy + half))
            path.closeSubpath()
            path.addRoundedRect(QRectF(cx + half * 0.55, cy - half, s * 0.18, s), 1, 1)
        elif self.kind == "prev":
            path.moveTo(QPointF(cx + half, cy - half))
            path.lineTo(QPointF(cx - half * 0.5, cy))
            path.lineTo(QPointF(cx + half, cy + half))
            path.closeSubpath()
            path.addRoundedRect(QRectF(cx - half * 0.55 - s * 0.18, cy - half, s * 0.18, s), 1, 1)

        painter.drawPath(path)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()


class ControlBar(QWidget):
    play_pause_clicked = Signal()
    next_clicked = Signal()
    previous_clicked = Signal()
    seek_requested = Signal(int)  # position_ms

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._duration_ms = 0
        self._user_seeking = False
        self._opacity_percent = 75
        self._accent_color = QColor("#1DB954")
        self._bg_color = QColor(18, 18, 18)
        self._fg_color = QColor(255, 255, 255)
        self._acrylic_enabled = False

        self._build_ui()
        self.set_opacity(self._opacity_percent)
        self.set_scale(100)

    def _build_ui(self):
        self.card = QWidget(self)
        self.card.setObjectName("card")

        outer = QVBoxLayout(self.card)
        outer.setContentsMargins(20, 4, 20, 10)
        outer.setSpacing(2)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(26)
        buttons_row.addStretch()

        self.prev_button = IconButton("prev")
        self.play_pause_button = IconButton("play_pause")
        self.next_button = IconButton("next")
        for button in (self.prev_button, self.play_pause_button, self.next_button):
            buttons_row.addWidget(button)
        buttons_row.addStretch()
        outer.addLayout(buttons_row)

        self.prev_button.clicked.connect(self.previous_clicked)
        self.play_pause_button.clicked.connect(self.play_pause_clicked)
        self.next_button.clicked.connect(self.next_clicked)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)

        self.elapsed_label = QLabel("0:00")
        self.total_label = QLabel("0:00")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)

        progress_row.addWidget(self.elapsed_label)
        progress_row.addWidget(self.progress_slider)
        progress_row.addWidget(self.total_label)
        outer.addLayout(progress_row)

    def set_scale(self, scale_percent: int):
        factor = scale_percent / 100

        button_px = max(16, round(_BASE_BUTTON_SIZE * factor))
        icon_px = max(8, round(_BASE_ICON_SIZE * factor))
        for button in (self.prev_button, self.play_pause_button, self.next_button):
            button.set_sizes(button_px, icon_px)

        time_font = QFont("Segoe UI", max(6, round(_BASE_TIME_PT * factor)))
        self.elapsed_label.setFont(time_font)
        self.total_label.setFont(time_font)

        self.card.adjustSize()
        self.resize(self.width() or 620, self.card.sizeHint().height())
        self.card.setGeometry(0, 0, self.width(), self.height())

    def set_accent_color(self, color: QColor):
        self._accent_color = color
        for button in (self.prev_button, self.play_pause_button, self.next_button):
            button.set_accent_color(color)
        self.set_opacity(self._opacity_percent)

    def set_bg_color(self, color: QColor):
        self._bg_color = color
        self.set_opacity(self._opacity_percent)
        # Keep the acrylic tint in step with a theme/background change.
        if self._acrylic_enabled and self.isVisible():
            set_acrylic_effect(int(self.winId()), self._acrylic_gradient())

    def set_fg_color(self, color: QColor):
        # The overlay's lyrics colour doubles as this strip's foreground so
        # the two windows stay a matched pair under both themes.
        self._fg_color = color
        base = QColor(color.red(), color.green(), color.blue(), 230)
        for button in (self.prev_button, self.play_pause_button, self.next_button):
            button.set_base_color(base)
        self.set_opacity(self._opacity_percent)

    def set_opacity(self, percent: int):
        self._opacity_percent = percent
        alpha = round(255 * percent / 100)
        accent = self._accent_color.name()
        br, bg, bb = self._bg_color.red(), self._bg_color.green(), self._bg_color.blue()
        fr, fg, fb = self._fg_color.red(), self._fg_color.green(), self._fg_color.blue()
        # Square top corners: this strip joins flush to the overlay's bottom
        # edge, so only the bottom corners are rounded.
        self.setStyleSheet(
            f"""
            #card {{
                background-color: rgba({br}, {bg}, {bb}, {alpha});
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
            QLabel {{
                color: rgba({fr}, {fg}, {fb}, 160);
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: rgba({fr}, {fg}, {fb}, 60);
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: rgba({fr}, {fg}, {fb}, 255);
                width: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 2px;
            }}
            """
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.card.setGeometry(0, 0, self.width(), self.height())

    def _on_slider_pressed(self):
        self._user_seeking = True

    def _on_slider_released(self):
        self._user_seeking = False
        self.seek_requested.emit(self.progress_slider.value())

    def set_playing(self, is_playing: bool):
        self.play_pause_button.set_playing(is_playing)

    def set_progress(self, position_ms: int, duration_ms: int):
        if duration_ms != self._duration_ms:
            self._duration_ms = duration_ms
            self.progress_slider.setRange(0, max(0, duration_ms))
            self.total_label.setText(_format_time(duration_ms))
        if not self._user_seeking:
            self.progress_slider.setValue(max(0, min(position_ms, duration_ms)))
            self.elapsed_label.setText(_format_time(position_ms))

    def follow(self, overlay_geometry: QRect):
        # Same width, zero gap: visually one continuous card with the overlay.
        if self.width() != overlay_geometry.width():
            self.resize(overlay_geometry.width(), self.card.sizeHint().height())
        self.move(overlay_geometry.x(), overlay_geometry.y() + overlay_geometry.height())

    def showEvent(self, event):
        super().showEvent(event)
        if self._acrylic_enabled:
            set_acrylic_effect(int(self.winId()), self._acrylic_gradient())

    def _acrylic_gradient(self) -> str:
        # Match the acrylic tint to the current background colour so the strip
        # frosts to the same theme as the overlay above it.
        c = self._bg_color
        return color_gradient(c.red(), c.green(), c.blue())

    def set_acrylic(self, enabled: bool):
        self._acrylic_enabled = enabled
        if not self.isVisible():
            return
        hwnd = int(self.winId())
        if enabled:
            set_acrylic_effect(hwnd, self._acrylic_gradient())
        else:
            remove_background_effect(hwnd)
