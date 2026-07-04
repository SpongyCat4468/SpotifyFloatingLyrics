"""The floating, always-on-top, semi-transparent lyrics window.

Click-through by default (see set_movable) so it never blocks interaction
with whatever's underneath it.
"""

import ctypes
from typing import Optional

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QParallelAnimationGroup, Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

_SLIDE_MS = 320
_DIM_OPACITY = 0.45
_BRIGHT_OPACITY = 1.0

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
MIN_OPACITY_PERCENT = 20
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


class OverlayWindow(QWidget):
    geometry_changed = Signal()

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
        _set_native_click_through(int(self.winId()), self._click_through)

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
        self._drag_offset = None
        event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def _build_ui(self):
        self.card = QWidget(self)
        self.card.setObjectName("card")

        self._card_layout = QVBoxLayout(self.card)

        self.title_label = QLabel("Waiting for Spotify...")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: rgba(255,255,255,140);")
        self._card_layout.addWidget(self.title_label)

        # prev/current/next/incoming are positioned manually (not via a
        # layout) inside this plain clipping container so they can be slid
        # vertically as one unit to scroll. incoming starts just below the
        # visible area and slides into "next" in lockstep with the others,
        # so the whole transition is a single continuous motion. All four
        # share the same row height/font size and wrap to a second line if
        # needed, instead of truncating with an ellipsis.
        self.lyrics_area = QWidget(self.card)
        self._card_layout.addWidget(self.lyrics_area)

        self.prev_label = self._make_row_label()
        self.current_label = self._make_row_label()
        self.next_label = self._make_row_label()
        self.incoming_label = self._make_row_label()

        self._rest_opacity = {
            self.prev_label: _DIM_OPACITY,
            self.current_label: _BRIGHT_OPACITY,
            self.next_label: _DIM_OPACITY,
        }
        self._effects = {
            label: QGraphicsOpacityEffect(label)
            for label in (self.prev_label, self.current_label, self.next_label, self.incoming_label)
        }
        for label, effect in self._effects.items():
            label.setGraphicsEffect(effect)
            effect.setOpacity(self._rest_opacity.get(label, 0.0))

        self.incoming_label.hide()
        self._slide_group: Optional[QParallelAnimationGroup] = None

        # Rows overlap slightly mid-slide (2-line-tall boxes moving through
        # each other's space); fixing the stacking order so each label
        # paints above the one before it in the prev->current->next->
        # incoming chain means the brightening label is always drawn on top
        # of the dimming one where they overlap.
        self.prev_label.raise_()
        self.current_label.raise_()
        self.next_label.raise_()
        self.incoming_label.raise_()

    def _make_row_label(self) -> QLabel:
        label = QLabel("", self.lyrics_area)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        return label

    def set_scale(self, scale_percent: int):
        self._scale_percent = scale_percent
        factor = scale_percent / 100

        side_margin = round(_BASE_SIDE_MARGIN * factor)
        v_margin = round(_BASE_V_MARGIN * factor)
        spacing = round(_BASE_SPACING * factor)
        self._card_layout.setContentsMargins(side_margin, v_margin, side_margin, v_margin)
        self._card_layout.setSpacing(spacing)

        title_font = QFont("Segoe UI", max(1, round(_BASE_TITLE_PT * factor)))
        lyric_pt = max(1, round(_BASE_LYRIC_PT * factor))
        self._dim_font = QFont("Segoe UI", lyric_pt)
        self._bright_font = QFont("Segoe UI", lyric_pt, QFont.Bold)
        self.title_label.setFont(title_font)
        self.prev_label.setFont(self._dim_font)
        self.next_label.setFont(self._dim_font)
        self.incoming_label.setFont(self._dim_font)
        self.current_label.setFont(self._bright_font)

        row_padding = round(_BASE_ROW_PADDING * factor)
        self._row_height = QFontMetrics(self._bright_font).height() * 2 + row_padding

        self._rest_y = {
            self.prev_label: 0,
            self.current_label: self._row_height,
            self.next_label: self._row_height * 2,
        }
        self.lyrics_area.setFixedHeight(self._row_height * 3)

        width = round(_BASE_WIDTH * factor)
        self._row_width = width - 2 * side_margin
        self._layout_lyrics_labels()

        height = (
            v_margin * 2
            + QFontMetrics(title_font).height()
            + spacing
            + self.lyrics_area.height()
        )
        old_center = self.geometry().center() if self.isVisible() else None
        self.resize(width, height)
        self.card.setGeometry(0, 0, width, height)
        if old_center is not None:
            self.move(old_center.x() - width // 2, old_center.y() - height // 2)
        self.geometry_changed.emit()

        # Re-render whatever's currently showing at the new sizes.
        if self._lines and 0 <= self._current_index < len(self._lines):
            idx = self._current_index
            prev_text = self._lines[idx - 1][1] if idx - 1 >= 0 else ""
            current_text = self._lines[idx][1]
            next_text = self._lines[idx + 1][1] if idx + 1 < len(self._lines) else ""
            self._reset_lyric_rows(prev_text, current_text, next_text)
        else:
            self._layout_lyrics_labels()

    def set_opacity(self, percent: int):
        self._opacity_percent = percent
        alpha = round(255 * percent / 100)
        bottom_radius = 0 if self._attached else 16
        self.setStyleSheet(
            f"""
            #card {{
                background-color: rgba(18, 18, 18, {alpha});
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom-left-radius: {bottom_radius}px;
                border-bottom-right-radius: {bottom_radius}px;
            }}
            QLabel {{
                color: white;
                background: transparent;
            }}
            """
        )

    def _layout_lyrics_labels(self):
        for label, rest_y in self._rest_y.items():
            label.setGeometry(0, rest_y, self._row_width, self._row_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.card.setGeometry(0, 0, self.width(), self.height())
        self.geometry_changed.emit()

    def _move_to_default_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.top() + 40
        self.move(x, y)

    # --- public API used by the controller ---
    def set_track_info(self, title: str, artist: str):
        self.title_label.setText(f"{title} — {artist}" if artist else title)

    def show_idle(self, message: str):
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
        if advance == 1 and prior_index >= 0:
            self._scroll_to_next()
        else:
            prev_text = self._lines[index - 1][1] if index - 1 >= 0 else ""
            current_text = self._lines[index][1] if 0 <= index < len(self._lines) else ""
            next_text = self._lines[index + 1][1] if index + 1 < len(self._lines) else ""
            self._reset_lyric_rows(prev_text, current_text, next_text)

    def _scroll_to_next(self):
        idx = self._current_index
        new_prev_text = self._lines[idx - 1][1] if idx - 1 >= 0 else ""
        new_current_text = self._lines[idx][1]
        incoming_text = self._lines[idx + 1][1] if idx + 1 < len(self._lines) else ""

        if self._slide_group is not None:
            self._slide_group.stop()
        # Any interrupted mid-flight animation leaves labels off their rest
        # position; snap back to rest first so the new slide starts clean
        # instead of jumping from wherever the old one was cut off.
        self._layout_lyrics_labels()
        for label, opacity in self._rest_opacity.items():
            self._effects[label].setOpacity(opacity)

        chain = [self.prev_label, self.current_label, self.next_label, self.incoming_label]
        incoming_row_y = self._row_height * 3

        self.incoming_label.setText(incoming_text)
        self.incoming_label.setGeometry(0, incoming_row_y, self._row_width, self._row_height)
        self._effects[self.incoming_label].setOpacity(0.0)
        self.incoming_label.show()

        rest_y_chain = [0, self._row_height, self._row_height * 2, incoming_row_y]
        opacity_chain = [
            (_DIM_OPACITY, 0.0),
            (_BRIGHT_OPACITY, _DIM_OPACITY),
            (_DIM_OPACITY, _BRIGHT_OPACITY),
            (0.0, _DIM_OPACITY),
        ]

        group = QParallelAnimationGroup(self)
        for i, label in enumerate(chain):
            start_y = rest_y_chain[i]
            end_y = rest_y_chain[i - 1] if i > 0 else start_y - self._row_height
            start_opacity, end_opacity = opacity_chain[i]

            pos_anim = QPropertyAnimation(label, b"pos", group)
            pos_anim.setDuration(_SLIDE_MS)
            pos_anim.setStartValue(QPoint(0, start_y))
            pos_anim.setEndValue(QPoint(0, end_y))
            pos_anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(pos_anim)

            fade_anim = QPropertyAnimation(self._effects[label], b"opacity", group)
            fade_anim.setDuration(_SLIDE_MS)
            fade_anim.setStartValue(start_opacity)
            fade_anim.setEndValue(end_opacity)
            fade_anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(fade_anim)

        group.finished.connect(lambda: self._finish_scroll(new_prev_text, new_current_text, incoming_text))
        self._slide_group = group
        group.start()

    def _finish_scroll(self, prev_text: str, current_text: str, next_text: str):
        self.prev_label.setText(prev_text)
        self.current_label.setText(current_text)
        self.next_label.setText(next_text)
        self.incoming_label.hide()

        self._layout_lyrics_labels()
        for label, opacity in self._rest_opacity.items():
            self._effects[label].setOpacity(opacity)

    def _reset_lyric_rows(self, prev_text: str, current_text: str, next_text: str):
        if self._slide_group is not None:
            self._slide_group.stop()
        self.incoming_label.hide()
        self.prev_label.setText(prev_text)
        self.current_label.setText(current_text)
        self.next_label.setText(next_text)
        self._layout_lyrics_labels()
        for label, opacity in self._rest_opacity.items():
            self._effects[label].setOpacity(opacity)
