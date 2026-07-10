"""The floating, always-on-top, semi-transparent lyrics window.

Click-through by default (see set_movable) so it never blocks interaction
with whatever's underneath it.
"""

import ctypes
from typing import Optional

from win32_effect import color_gradient, remove_background_effect, set_acrylic_effect
from i18n import tr

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication, QFrame, QGraphicsObject, QGraphicsScene, QGraphicsView, QLabel, QVBoxLayout, QWidget

_SLIDE_MS = 320
_DIM_OPACITY = 0.45
_BRIGHT_OPACITY = 1.0
_DIM_SCALE = 0.85
_BRIGHT_SCALE = 1.0

# All sizes are derived from these at scale=100 (see set_scale), so the
# whole overlay grows/shrinks together as one consistent ratio. prev,
# current, and next all share the same font size and row height - only
# weight/opacity set the current line apart - so the transition reads as
# one continuous strip of text scrolling, not separately-sized labels
# swapping in and out.
_BASE_WIDTH = 620
_BASE_SIDE_MARGIN = 28
_BASE_V_MARGIN = 12
_BASE_SPACING = 4
_BASE_ROW_PADDING = 14
_BASE_TITLE_PT = 9
_BASE_LYRIC_PT = 15

DEFAULT_SCALE_PERCENT = 100
DEFAULT_OPACITY_PERCENT = 75
MIN_SCALE_PERCENT = 60
MAX_SCALE_PERCENT = 160
MIN_OPACITY_PERCENT = 1
MAX_OPACITY_PERCENT = 100

# Qt.WA_TransparentForMouseEvents alone doesn't reliably translate to the
# native click-through window style on Windows for this combination of
# frameless/translucent/tool/topmost flags, so the actual pass-through is
# done by setting WS_EX_TRANSPARENT on the native HWND directly.
_GWL_EXSTYLE = -20
_WS_EX_TRANSPARENT = 0x00000020
_user32 = ctypes.windll.user32
_user32.GetWindowLongPtrW.restype = ctypes.c_longlong
_user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
_user32.SetWindowLongPtrW.restype = ctypes.c_longlong
_user32.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_longlong]


def _set_native_click_through(hwnd: int, click_through: bool):
    style = _user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE)
    if click_through:
        style |= _WS_EX_TRANSPARENT
    else:
        style &= ~_WS_EX_TRANSPARENT
    _user32.SetWindowLongPtrW(hwnd, _GWL_EXSTYLE, style)


class LyricItem(QGraphicsObject):
    """A single lyric line rendered in the QGraphicsScene.

    Position, opacity, and scale are all native QGraphicsItem properties
    exposed through QGraphicsObject, so they can be animated directly with
    QPropertyAnimation(b"pos"), (b"opacity"), (b"scale") — no per-property
    boilerplate needed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._font = QFont()
        self._bounding_rect = QRectF()
        self._color = QColor(Qt.white)

    def setColor(self, color: QColor):
        self._color = color
        self.update()

    def setText(self, text: str):
        self._text = text
        self.update()

    def setFont(self, font: QFont):
        self._font = font
        self.update()

    def setItemGeometry(self, w: float, h: float):
        self.prepareGeometryChange()
        self._bounding_rect = QRectF(-w / 2, -h / 2, w, h)

    def boundingRect(self):
        return self._bounding_rect

    def paint(self, painter, option, widget=None):
        if not self._text or self._bounding_rect.isEmpty():
            return
        painter.setFont(self._font)
        painter.setPen(self._color)
        painter.drawText(
            self._bounding_rect,
            Qt.AlignCenter | Qt.TextWordWrap,
            self._text,
        )


class OverlayWindow(QWidget):
    geometry_changed = Signal()
    drag_finished = Signal()  # emitted when the user finishes dragging the overlay

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._lines: list = []
        self._current_index = -1
        self._click_through = True
        self._drag_offset: Optional[QPoint] = None
        self._attached = False
        self._approximate = False
        self._dimmed = False
        self._lyrics_color = QColor(Qt.white)
        self._bg_color = QColor(18, 18, 18)
        self._acrylic_enabled = False
        self._pre_dim_opacity = DEFAULT_OPACITY_PERCENT
        self._lyrics_only = False  # transparent background, text only
        self._single_line = False  # show only the current lyric line
        self._build_ui()
        self.set_opacity(DEFAULT_OPACITY_PERCENT)
        self.set_scale(DEFAULT_SCALE_PERCENT)
        self._move_to_default_position()

    def set_attached(self, attached: bool):
        # When the control bar sits flush below, square off the bottom
        # corners so the two windows read as one continuous card.
        self._attached = attached
        self.set_opacity(self._opacity_percent)

    def showEvent(self, event):
        super().showEvent(event)
        # winId() forces native window creation, needed before the ctypes
        # call below can target a real HWND.
        hwnd = int(self.winId())
        _set_native_click_through(hwnd, self._click_through)
        if self._acrylic_enabled and not self._lyrics_only:
            set_acrylic_effect(hwnd, self._acrylic_gradient())

    def _acrylic_gradient(self) -> str:
        # Tint the acrylic with the current background colour so the frosted
        # look matches the theme; a fixed dark tint would leave light themes
        # looking muddy and under-drawn.
        c = self._bg_color
        return color_gradient(c.red(), c.green(), c.blue())

    def set_acrylic(self, enabled: bool):
        self._acrylic_enabled = enabled
        if not self.isVisible():
            return
        hwnd = int(self.winId())
        if enabled and not self._lyrics_only:
            set_acrylic_effect(hwnd, self._acrylic_gradient())
        else:
            remove_background_effect(hwnd)

    def set_lyrics_only(self, enabled: bool):
        # "Lyrics only": drop the card background to fully transparent so just
        # the text floats. Acrylic fills the whole window regardless of the
        # card alpha, so it must be suppressed here too, otherwise a frosted
        # rectangle would remain.
        self._lyrics_only = enabled
        self.set_opacity(self._opacity_percent)
        if not self.isVisible():
            return
        hwnd = int(self.winId())
        if enabled or not self._acrylic_enabled:
            remove_background_effect(hwnd)
        else:
            set_acrylic_effect(hwnd, self._acrylic_gradient())

    def set_single_line(self, enabled: bool):
        # Show only the current lyric line (no dimmed prev/next). Rebuilds the
        # geometry for the new row count and re-lays the current line; line
        # changes then swap in place instead of running the 3-row scroll.
        self._single_line = enabled
        self.set_scale(self._scale_percent)

    def set_movable(self, movable: bool):
        self._click_through = not movable
        self.setAttribute(Qt.WA_TransparentForMouseEvents, self._click_through)
        if self.isVisible():
            _set_native_click_through(int(self.winId()), self._click_through)

    # --- dragging, only active while set_movable(True) is in effect ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        was_dragging = self._drag_offset is not None
        self._drag_offset = None
        event.accept()
        if was_dragging:
            self.drag_finished.emit()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def _build_ui(self):
        self.card = QWidget(self)
        self.card.setObjectName("card")

        self._card_layout = QVBoxLayout(self.card)

        self.title_label = QLabel(tr("Waiting for Spotify..."))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: rgba(255,255,255,140);")
        self._card_layout.addWidget(self.title_label)

        # A yellow "unsynced" badge pinned to the top-right corner, shown only
        # when the lyrics are plain text spread evenly across the track (see
        # set_approximate) so the rough timing is clearly flagged.
        self.unsynced_label = QLabel(tr("unsynced"), self.card)
        self.unsynced_label.setObjectName("unsynced")
        self.unsynced_label.setAlignment(Qt.AlignCenter)
        self.unsynced_label.hide()

        # prev/current/next/incoming are rendered as QGraphicsItems inside a
        # QGraphicsScene/QGraphicsView.  Each item exposes pos / opacity /
        # scale as animatable Qt properties so scrolling can slide, fade,
        # and resize all four lines simultaneously.
        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene, self.card)
        self._view.setRenderHint(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setFrameShape(QFrame.NoFrame)
        self._view.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._view.setBackgroundBrush(QBrush(Qt.NoBrush))
        self._view.setStyleSheet("background: transparent; border: none;")
        self._view.setAutoFillBackground(False)
        self._view.viewport().setAutoFillBackground(False)
        self._card_layout.addWidget(self._view)

        # Four items: 0=prev, 1=current, 2=next, 3=incoming.
        self._items = [LyricItem() for _ in range(4)]
        for i, item in enumerate(self._items):
            self._scene.addItem(item)
            item.setZValue(i)

        self._rest_opacity = {
            0: _DIM_OPACITY,
            1: _BRIGHT_OPACITY,
            2: _DIM_OPACITY,
        }
        self._rest_scale = {
            0: _DIM_SCALE,
            1: _BRIGHT_SCALE,
            2: _DIM_SCALE,
        }

        self._slide_group: Optional[QParallelAnimationGroup] = None
        self._bold_timer: Optional[QTimer] = None
        self._normal_font = QFont()
        self._bold_font = QFont()

    def set_scale(self, scale_percent: int):
        self._scale_percent = scale_percent
        factor = scale_percent / 100

        side_margin = round(_BASE_SIDE_MARGIN * factor)
        v_margin = round(_BASE_V_MARGIN * factor)
        spacing = round(_BASE_SPACING * factor)
        self._card_layout.setContentsMargins(side_margin, v_margin, side_margin, v_margin)
        self._card_layout.setSpacing(spacing)

        title_font = QFont("Segoe UI", max(1, round(_BASE_TITLE_PT * factor)))
        self.title_label.setFont(title_font)

        lyric_pt = max(1, round(_BASE_LYRIC_PT * factor))
        self._normal_font = QFont("Segoe UI", lyric_pt)
        self._bold_font = QFont("Segoe UI", lyric_pt)
        self._bold_font.setBold(True)
        for item in self._items:
            item.setFont(self._normal_font)

        row_padding = round(_BASE_ROW_PADDING * factor)
        self._row_height = QFontMetrics(self._normal_font).height() * 2 + row_padding

        width = round(_BASE_WIDTH * factor)
        self._row_width = width - 2 * side_margin
        for item in self._items:
            item.setItemGeometry(self._row_width, self._row_height)

        # Single-line mode shows just the current row; the prev/next items stay
        # positioned in the 3-row scene but the view is cropped to the middle
        # band (where the current line sits) so they're clipped out of sight.
        visible_rows = 1 if self._single_line else 3
        self._view.setFixedHeight(self._row_height * visible_rows)
        if self._single_line:
            self._scene.setSceneRect(0, self._row_height, self._row_width, self._row_height)
        else:
            self._scene.setSceneRect(0, 0, self._row_width, self._row_height * 3)

        height = (
            v_margin * 2
            + QFontMetrics(title_font).height()
            + spacing
            + self._view.height()
        )
        old_center = self.geometry().center() if self.isVisible() else None
        self.resize(width, height)
        self.card.setGeometry(0, 0, width, height)
        if old_center is not None:
            self.move(old_center.x() - width // 2, old_center.y() - height // 2)
        self.geometry_changed.emit()

        badge_font = QFont("Segoe UI", max(6, round(_BASE_TITLE_PT * factor)), QFont.Bold)
        self.unsynced_label.setFont(badge_font)
        self.unsynced_label.adjustSize()
        self._badge_margin = round(10 * factor)
        self._position_unsynced_badge()

        # Re-render whatever's currently showing at the new sizes.
        if self._lines and 0 <= self._current_index < len(self._lines):
            idx = self._current_index
            prev_text = self._lines[idx - 1][1] if idx - 1 >= 0 else ""
            current_text = self._lines[idx][1]
            next_text = self._lines[idx + 1][1] if idx + 1 < len(self._lines) else ""
            self._reset_lyric_rows(prev_text, current_text, next_text)
        else:
            self._layout_lyrics_labels()

    def set_lyrics_color(self, color: QColor):
        self._lyrics_color = color
        for item in self._items:
            item.setColor(color)
        self._apply_title_color()
        # Re-emit the stylesheet so the general QLabel colour tracks the
        # lyrics colour too (matters for the light theme, where white text
        # would vanish on a light card).
        if hasattr(self, "_opacity_percent"):
            self.set_opacity(self._opacity_percent)

    def _apply_title_color(self):
        # The track title sits above the lyrics; keep it a dimmed tint of the
        # lyrics colour so it stays legible under both dark and light themes.
        c = self._lyrics_color
        self.title_label.setStyleSheet(
            f"color: rgba({c.red()}, {c.green()}, {c.blue()}, 140); background: transparent;"
        )

    def set_bg_color(self, color: QColor):
        self._bg_color = color
        self.set_opacity(self._opacity_percent)
        # Keep the acrylic tint in step with a theme/background change.
        if self._acrylic_enabled and not self._lyrics_only and self.isVisible():
            set_acrylic_effect(int(self.winId()), self._acrylic_gradient())

    def set_opacity(self, percent: int):
        self._opacity_percent = percent
        # Lyrics-only forces a fully transparent card so only the text shows.
        alpha = 0 if self._lyrics_only else round(255 * percent / 100)
        bottom_radius = 0 if self._attached else 16
        r, g, b = self._bg_color.red(), self._bg_color.green(), self._bg_color.blue()
        lr, lg, lb = self._lyrics_color.red(), self._lyrics_color.green(), self._lyrics_color.blue()
        self.setStyleSheet(
            f"""
            #card {{
                background-color: rgba({r}, {g}, {b}, {alpha});
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom-left-radius: {bottom_radius}px;
                border-bottom-right-radius: {bottom_radius}px;
            }}
            QLabel {{
                color: rgba({lr}, {lg}, {lb}, 255);
                background: transparent;
            }}
            #unsynced {{
                background-color: #F5C518;
                color: #101010;
                border-radius: 6px;
                padding: 1px 7px;
            }}
            """
        )

    def _position_unsynced_badge(self):
        margin = getattr(self, "_badge_margin", 10)
        self.unsynced_label.move(
            self.width() - self.unsynced_label.width() - margin, margin
        )

    def _layout_lyrics_labels(self):
        """Snap all items to their rest positions / opacity / scale."""
        cx = self._row_width / 2
        centers_y = [
            self._row_height / 2,
            self._row_height / 2 + self._row_height,
            self._row_height / 2 + 2 * self._row_height,
        ]
        for i, item in enumerate(self._items[:3]):
            item.setPos(QPointF(cx, centers_y[i]))
            item.setScale(self._rest_scale.get(i, _DIM_SCALE))
            opacity = self._rest_opacity.get(i, _DIM_OPACITY)
            if self._single_line and i != 1:
                opacity = 0.0  # hide prev/next, leaving only the current line
            item.setOpacity(opacity)
        # incoming sits just below the visible area, hidden.
        self._items[3].setPos(QPointF(cx, self._row_height / 2 + 3 * self._row_height))
        self._items[3].setScale(0.0)
        self._items[3].setOpacity(0.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.card.setGeometry(0, 0, self.width(), self.height())
        self._position_unsynced_badge()
        self.geometry_changed.emit()

    def _move_to_default_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.top() + 40
        self.move(x, y)

    # --- public API used by the controller ---
    def set_track_info(self, title: str, artist: str):
        self.title_label.setText(f"{title} — {artist}" if artist else title)

    def set_approximate(self, approximate: bool):
        # Plain lyrics carry no real timestamps; we spread them evenly across
        # the track, so the highlighted line is only a rough guess. Show the
        # yellow "unsynced" badge so the user knows the timing isn't exact.
        self._approximate = approximate
        self.unsynced_label.setVisible(approximate)
        if approximate:
            self.unsynced_label.adjustSize()
            self._position_unsynced_badge()

    def set_dimmed(self, dimmed: bool):
        if dimmed == self._dimmed:
            return
        self._dimmed = dimmed
        if self._acrylic_enabled:
            if dimmed:
                self._pre_dim_opacity = self._opacity_percent
                self.set_opacity(round(self._opacity_percent * 0.55))
            else:
                self.set_opacity(self._pre_dim_opacity)
            # set_opacity → setStyleSheet resets DWM composition;
            # re-apply the blur after every stylesheet change.
            if self.isVisible():
                hwnd = int(self.winId())
                set_acrylic_effect(hwnd, self._acrylic_gradient())
        else:
            self.setWindowOpacity(0.55 if dimmed else 1.0)

    def current_line_text(self) -> str:
        # The lyric line currently highlighted, or "" when there's nothing to
        # copy (idle, still loading, or no lyrics found).
        if self._lines and 0 <= self._current_index < len(self._lines):
            return self._lines[self._current_index][1]
        return ""

    def show_idle(self, message: str):
        self.set_approximate(False)
        self.title_label.setText(message)
        self._reset_lyric_rows("", "", "")
        self._lines = []
        self._current_index = -1

    def show_status(self, message: str):
        self._reset_lyric_rows("", message, "")
        self._lines = []
        self._current_index = -1

    def set_lyrics(self, result):
        self._lines = result.lines
        self._current_index = -1
        self._reset_lyric_rows("", "", "")

    def update_position(self, position_ms: int):
        if not self._lines:
            return
        index = self._current_index
        for i, (timestamp, _text) in enumerate(self._lines):
            if timestamp <= position_ms:
                index = i
            else:
                break
        if index == self._current_index:
            return
        advance = index - self._current_index
        prior_index = self._current_index
        self._current_index = index
        if advance == 1 and prior_index >= 0 and not self._single_line:
            self._scroll_to_next()
        else:
            prev_text = self._lines[index - 1][1] if index - 1 >= 0 else ""
            current_text = self._lines[index][1] if 0 <= index < len(self._lines) else ""
            next_text = self._lines[index + 1][1] if index + 1 < len(self._lines) else ""
            self._reset_lyric_rows(prev_text, current_text, next_text)

    def _stop_scroll_animation(self):
        if self._slide_group is not None:
            self._slide_group.stop()
            self._slide_group = None
        if self._bold_timer is not None:
            self._bold_timer.stop()
            self._bold_timer = None

    def _mid_scroll_bold_switch(self):
        self._bold_timer = None
        # item[1] is sliding away from current slot → lose bold
        self._items[1].setFont(self._normal_font)
        # item[2] is arriving at current slot → gain bold
        self._items[2].setFont(self._bold_font)

    def _scroll_to_next(self):
        idx = self._current_index
        new_prev_text = self._lines[idx - 1][1] if idx - 1 >= 0 else ""
        new_current_text = self._lines[idx][1]
        incoming_text = self._lines[idx + 1][1] if idx + 1 < len(self._lines) else ""

        self._stop_scroll_animation()
        # Any interrupted mid-flight animation leaves items off their rest
        # state; snap back to rest first so the new slide starts clean.
        self._layout_lyrics_labels()

        chain = [0, 1, 2, 3]
        cx = self._row_width / 2
        rest_centers_y = [
            self._row_height / 2,
            self._row_height / 2 + self._row_height,
            self._row_height / 2 + 2 * self._row_height,
            self._row_height / 2 + 3 * self._row_height,
        ]

        opacity_chain = [
            (_DIM_OPACITY, 0.0),
            (_BRIGHT_OPACITY, _DIM_OPACITY),
            (_DIM_OPACITY, _BRIGHT_OPACITY),
            (0.0, _DIM_OPACITY),
        ]
        scale_chain = [
            (_DIM_SCALE, 0.0),
            (_BRIGHT_SCALE, _DIM_SCALE),
            (_DIM_SCALE, _BRIGHT_SCALE),
            (0.0, _DIM_SCALE),
        ]

        # Place incoming just below the visible area.
        self._items[3].setText(incoming_text)
        self._items[3].setPos(QPointF(cx, rest_centers_y[3]))
        self._items[3].setScale(0.0)
        self._items[3].setOpacity(0.0)

        group = QParallelAnimationGroup(self)
        for i in chain:
            start_y = rest_centers_y[i]
            end_y = rest_centers_y[i - 1] if i > 0 else start_y - self._row_height
            start_opacity, end_opacity = opacity_chain[i]
            start_scale, end_scale = scale_chain[i]

            pos_anim = QPropertyAnimation(self._items[i], b"pos", group)
            pos_anim.setDuration(_SLIDE_MS)
            pos_anim.setStartValue(QPointF(cx, start_y))
            pos_anim.setEndValue(QPointF(cx, end_y))
            pos_anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(pos_anim)

            fade_anim = QPropertyAnimation(self._items[i], b"opacity", group)
            fade_anim.setDuration(_SLIDE_MS)
            fade_anim.setStartValue(start_opacity)
            fade_anim.setEndValue(end_opacity)
            fade_anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(fade_anim)

            scale_anim = QPropertyAnimation(self._items[i], b"scale", group)
            scale_anim.setDuration(_SLIDE_MS)
            scale_anim.setStartValue(start_scale)
            scale_anim.setEndValue(end_scale)
            scale_anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(scale_anim)

        group.finished.connect(lambda np=new_prev_text, nc=new_current_text, ni=incoming_text: self._finish_scroll(np, nc, ni))
        self._slide_group = group
        group.start()

        # Switch bold at the midpoint of the scroll so the arriving lyric
        # turns bold just as it settles into the current slot.
        self._bold_timer = QTimer(self)
        self._bold_timer.setSingleShot(True)
        self._bold_timer.timeout.connect(self._mid_scroll_bold_switch)
        self._bold_timer.start(_SLIDE_MS // 4)

    def _finish_scroll(self, prev_text: str, current_text: str, next_text: str):
        self._items[0].setText(prev_text)
        self._items[0].setFont(self._normal_font)
        self._items[1].setText(current_text)
        self._items[1].setFont(self._bold_font)
        self._items[2].setText(next_text)
        self._items[2].setFont(self._normal_font)
        self._items[3].setText("")
        self._items[3].setOpacity(0.0)

        self._layout_lyrics_labels()

    def _reset_lyric_rows(self, prev_text: str, current_text: str, next_text: str):
        self._stop_scroll_animation()
        self._items[0].setText(prev_text)
        self._items[0].setFont(self._normal_font)
        self._items[1].setText(current_text)
        self._items[1].setFont(self._bold_font)
        self._items[2].setText(next_text)
        self._items[2].setFont(self._normal_font)
        self._items[3].setText("")
        self._items[3].setOpacity(0.0)
        self._layout_lyrics_labels()
