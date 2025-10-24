"""Main floating panel window for Voinux GUI."""

from datetime import datetime

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from voinux.gui.assets import load_svg_icon


class FloatingPanel(QWidget):
    """Floating panel window for voice transcription control."""

    # Signals
    stop_requested = pyqtSignal()
    start_requested = pyqtSignal()
    close_requested = pyqtSignal()

    # Button stylesheets
    STOP_BUTTON_STYLE = """
        QPushButton {
            background-color: #B85555;
            border: none;
            border-radius: 12px;
        }
        QPushButton:hover {
            background-color: #C86565;
        }
        QPushButton:pressed {
            background-color: #A84545;
        }
    """

    PLAY_BUTTON_STYLE = """
        QPushButton {
            background-color: #55B855;
            border: none;
            border-radius: 12px;
        }
        QPushButton:hover {
            background-color: #65C865;
        }
        QPushButton:pressed {
            background-color: #45A845;
        }
    """

    CLOSE_BUTTON_STYLE = """
        QPushButton {
            background-color: #666666;
            border: none;
            border-radius: 12px;
        }
        QPushButton:hover {
            background-color: #777777;
        }
        QPushButton:pressed {
            background-color: #555555;
        }
    """

    def __init__(self):
        """Initialize the floating panel."""
        super().__init__()

        # Window setup - frameless, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # Don't show in taskbar
        )

        # Set fixed window size - compact layout
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(280, 70)

        # Dragging state
        self.dragging = False
        self.drag_position = QPoint()

        # Session state
        self.is_recording = True  # Start in recording state
        self.session_start: datetime | None = None
        self.paused_duration: float = 0.0  # Track paused time when stopped
        self.pause_start: datetime | None = None  # When pause started
        self.status_message = "Starting"  # Current status message
        self.last_activity_time = datetime.now()  # Track last transcription activity

        # Build UI
        self._build_ui()

        # Update timer for duration
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_duration)
        self.update_timer.start(1000)  # Update every second

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main layout - compact margins and spacing
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # Top section: buttons + timer + stats
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # Left button (stop/play toggle) - compact size
        self.action_button = QPushButton()
        self.action_button.setFixedSize(40, 40)
        self.action_button.setIcon(load_svg_icon("stop", 24))
        self.action_button.setIconSize(self.action_button.size() * 0.5)
        self.action_button.setStyleSheet(self.STOP_BUTTON_STYLE)
        self.action_button.clicked.connect(self._on_action_button_clicked)
        top_layout.addWidget(self.action_button)

        # Center section: timer and status
        center_layout = QVBoxLayout()
        center_layout.setSpacing(2)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Timer label - compact font size
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.timer_label)

        # Status label - shows current state
        self.status_label = QLabel("Starting")
        self.status_label.setFont(QFont("Sans", 8))
        self.status_label.setStyleSheet("color: #888888; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.status_label)

        top_layout.addLayout(center_layout, 1)

        # Right button (close) - compact size
        self.close_button = QPushButton()
        self.close_button.setFixedSize(40, 40)
        self.close_button.setIcon(load_svg_icon("close", 24))
        self.close_button.setIconSize(self.close_button.size() * 0.5)
        self.close_button.setStyleSheet(self.CLOSE_BUTTON_STYLE)
        self.close_button.clicked.connect(self.close_requested.emit)
        top_layout.addWidget(self.close_button)

        main_layout.addLayout(top_layout)

        # Set main layout
        self.setLayout(main_layout)

        # Set overall styling
        self.setStyleSheet(
            """
            FloatingPanel {
                background-color: #0A0A0A;
                border-radius: 15px;
            }
        """
        )

    def _on_action_button_clicked(self) -> None:
        """Handle action button click (stop/play toggle)."""
        if self.is_recording:
            # Stop button clicked - pause the timer
            self.stop_requested.emit()
            self.is_recording = False
            self.pause_start = datetime.now()
            self.action_button.setIcon(load_svg_icon("play", 24))
            self.action_button.setStyleSheet(self.PLAY_BUTTON_STYLE)
        else:
            # Play/resume button clicked - start new session
            self.start_requested.emit()
            self.is_recording = True
            # Reset timing for new session
            self.paused_duration = 0.0
            self.pause_start = None
            self.action_button.setIcon(load_svg_icon("stop", 24))
            self.action_button.setStyleSheet(self.STOP_BUTTON_STYLE)

    def _update_duration(self) -> None:
        """Update the duration display."""
        if self.session_start is None:
            self.timer_label.setText("00:00")
            return

        # Calculate elapsed time
        if self.is_recording:
            # Currently recording - show active elapsed time
            elapsed = (datetime.now() - self.session_start).total_seconds() - self.paused_duration
        # Paused - show frozen elapsed time
        elif self.pause_start:
            elapsed = (
                self.pause_start - self.session_start
            ).total_seconds() - self.paused_duration
        else:
            elapsed = 0

        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Don't start dragging if clicking on a button
            widget_under_mouse = self.childAt(event.pos())
            if widget_under_mouse not in [self.action_button, self.close_button]:
                self.dragging = True
                self.drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging.

        Args:
            event: Mouse event
        """
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release for dragging.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def start_session(self) -> None:
        """Start a new transcription session."""
        self.session_start = datetime.now()
        self.paused_duration = 0.0
        self.pause_start = None
        self.last_activity_time = datetime.now()
        self.is_recording = True
        self.action_button.setIcon(load_svg_icon("stop", 24))
        self.action_button.setStyleSheet(self.STOP_BUTTON_STYLE)
        self.set_status("Starting")

    def update_stats(self, utterances: int, characters: int) -> None:
        """Update statistics display.

        Args:
            utterances: Number of utterances
            characters: Number of characters typed
        """
        # Track if there's new activity (new transcription)
        current_time = datetime.now()

        # If we're recording and there's new activity, show "Transcribing"
        if self.is_recording and (utterances > 0 or characters > 0):
            # Check if there's been recent activity (within last 2 seconds)
            time_since_activity = (current_time - self.last_activity_time).total_seconds()
            if time_since_activity < 2:
                self.set_status("Transcribing")
            else:
                self.set_status("Listening")
            self.last_activity_time = current_time

    def set_status(self, status: str, is_error: bool = False) -> None:
        """Set the status message.

        Args:
            status: Status message to display (e.g., "Listening", "Transcribing", "Stopped")
            is_error: Whether this is an error status
        """
        self.status_message = status
        self.status_label.setText(status)

        # Change color for errors
        if is_error:
            self.status_label.setStyleSheet("color: #B85555; background: transparent;")
        else:
            self.status_label.setStyleSheet("color: #888888; background: transparent;")

    def show_stopping(self) -> None:
        """Show UI feedback that stopping is in progress."""
        self.action_button.setEnabled(False)
        self.is_recording = False
        self.pause_start = datetime.now()
        self.set_status("Stopping")

    def show_stopped(self) -> None:
        """Re-enable the button after stopping is complete."""
        self.action_button.setEnabled(True)
        self.is_recording = False
        self.action_button.setIcon(load_svg_icon("play", 24))
        self.action_button.setStyleSheet(self.PLAY_BUTTON_STYLE)
        self.set_status("Stopped")
