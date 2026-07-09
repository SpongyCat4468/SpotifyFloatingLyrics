"""System tray icon with a menu to show/hide, reposition, and quit the app.

The overlay itself is click-through, so it can't be interacted with
directly - all control (visibility, moving it, exiting) happens here.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from i18n import tr


class TrayIcon(QSystemTrayIcon):
    toggle_requested = Signal()
    movable_toggled = Signal(bool)
    copy_line_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        self._accent_color = QColor("#1DB954")
        super().__init__(self._make_icon(), parent)
        self.setToolTip(tr("Spotify Floating Lyrics"))

        menu = QMenu()
        self.toggle_action = menu.addAction(tr("Hide Lyrics"))
        self.toggle_action.triggered.connect(self.toggle_requested)

        menu.addSeparator()
        self.movable_action = menu.addAction(tr("Move Overlay"))
        self.movable_action.setCheckable(True)
        self.movable_action.toggled.connect(self.movable_toggled)

        menu.addSeparator()
        copy_line_action = menu.addAction(tr("Copy current line"))
        copy_line_action.triggered.connect(self.copy_line_requested)

        menu.addSeparator()
        settings_action = menu.addAction(tr("Settings..."))
        settings_action.triggered.connect(self.settings_requested)

        menu.addSeparator()
        exit_action = menu.addAction(tr("Exit"))
        exit_action.triggered.connect(self.quit_requested)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _make_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self._accent_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
        painter.end()
        return QIcon(pixmap)

    def set_accent_color(self, color: QColor):
        self._accent_color = color
        self.setIcon(self._make_icon())

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_requested.emit()

    def set_visible_state(self, visible: bool):
        self.toggle_action.setText(tr("Hide Lyrics") if visible else tr("Show Lyrics"))
