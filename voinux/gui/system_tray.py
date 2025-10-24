"""System tray integration for Voinux GUI."""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTrayManager(QObject):
    """Manages the system tray icon and menu."""

    # Signals
    show_hide_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the system tray manager.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(parent)

        # Create icon (using a simple built-in icon for now)
        # TODO: Create a custom microphone icon
        icon = QIcon.fromTheme("audio-input-microphone")
        if icon.isNull():
            # Fallback to a generic icon
            icon = QIcon.fromTheme("media-record")
        self.tray_icon.setIcon(icon)

        # Create menu
        self.menu = QMenu()

        # Add actions
        self.show_hide_action = QAction("Show/Hide Panel", self.menu)
        self.show_hide_action.triggered.connect(self.show_hide_requested.emit)
        self.menu.addAction(self.show_hide_action)

        self.menu.addSeparator()

        self.stop_action = QAction("Stop Transcription", self.menu)
        self.stop_action.triggered.connect(self.stop_requested.emit)
        self.menu.addAction(self.stop_action)

        self.menu.addSeparator()

        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.quit_action)

        # Set menu
        self.tray_icon.setContextMenu(self.menu)

        # Connect click signal
        self.tray_icon.activated.connect(self._on_activated)

        # Set tooltip
        self.tray_icon.setToolTip("Voinux Voice Transcription")

    def show(self) -> None:
        """Show the system tray icon."""
        self.tray_icon.show()

    def hide(self) -> None:
        """Hide the system tray icon."""
        self.tray_icon.hide()

    def show_message(self, title: str, message: str, duration: int = 3000) -> None:
        """Show a notification message.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds
        """
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation.

        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - toggle window visibility
            self.show_hide_requested.emit()
