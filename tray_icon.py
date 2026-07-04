"""System tray icon with a menu to show/hide, reposition, and quit the app.

The overlay itself is click-through, so it can't be interacted with
directly - all control (visibility, moving it, exiting) happens here.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#1DB954"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    toggle_requested = Signal()
    movable_toggled = Signal(bool)
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(_make_icon(), parent)
        self.setToolTip("Spotify Floating Lyrics")

        menu = QMenu()
        self.toggle_action = menu.addAction("Hide Lyrics")
        self.toggle_action.triggered.connect(self.toggle_requested)

        menu.addSeparator()
        self.movable_action = menu.addAction("Move Overlay")
        self.movable_action.setCheckable(True)
        self.movable_action.toggled.connect(self.movable_toggled)

        menu.addSeparator()
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.settings_requested)

        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.quit_requested)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_requested.emit()

    def set_visible_state(self, visible: bool):
        self.toggle_action.setText("Hide Lyrics" if visible else "Show Lyrics")
