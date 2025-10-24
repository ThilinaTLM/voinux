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
        self.setFixedSize(320, 80)

        # Dragging state
        self.dragging = False
        self.drag_position = QPoint()

        # Session state
        self.is_recording = True  # Start in recording state
        self.session_start: datetime | None = None
        self.paused_duration: float = 0.0  # Track paused time when stopped
        self.pause_start: datetime | None = None  # When pause started
        self.utterances = 0
        self.characters = 0

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
        self.action_button.setFixedSize(45, 45)
        self.action_button.setIcon(load_svg_icon("stop", 24))
        self.action_button.setIconSize(self.action_button.size() * 0.5)
        self.action_button.setStyleSheet(
            """
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
        )
        self.action_button.clicked.connect(self._on_action_button_clicked)
        top_layout.addWidget(self.action_button)

        # Center section: timer and stats
        center_layout = QVBoxLayout()
        center_layout.setSpacing(2)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Timer label - compact font size
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.timer_label)

        # Compact stats label - smaller font
        self.stats_label = QLabel("0 utterances • 0 chars")
        self.stats_label.setFont(QFont("Sans", 7))
        self.stats_label.setStyleSheet("color: #888888; background: transparent;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.stats_label)

        top_layout.addLayout(center_layout, 1)

        # Right button (close) - compact size
        self.close_button = QPushButton()
        self.close_button.setFixedSize(45, 45)
        self.close_button.setIcon(load_svg_icon("close", 24))
        self.close_button.setIconSize(self.close_button.size() * 0.5)
        self.close_button.setStyleSheet(
            """
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
        )
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
        else:
            # Play/resume button clicked - start new session
            self.start_requested.emit()
            self.is_recording = True
            # Reset timing for new session
            self.paused_duration = 0.0
            self.pause_start = None
            self.action_button.setIcon(load_svg_icon("stop", 24))

    def _update_duration(self) -> None:
        """Update the duration display."""
        if self.session_start is None:
            self.timer_label.setText("00:00")
            return

        # Calculate elapsed time
        if self.is_recording:
            # Currently recording - show active elapsed time
            elapsed = (datetime.now() - self.session_start).total_seconds() - self.paused_duration
        else:
            # Paused - show frozen elapsed time
            if self.pause_start:
                elapsed = (self.pause_start - self.session_start).total_seconds() - self.paused_duration
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
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
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
        self.utterances = 0
        self.characters = 0
        self.is_recording = True
        self.action_button.setIcon(load_svg_icon("stop", 24))
        self._update_stats_display()

    def update_stats(self, utterances: int, characters: int) -> None:
        """Update statistics display.

        Args:
            utterances: Number of utterances
            characters: Number of characters typed
        """
        self.utterances = utterances
        self.characters = characters
        self._update_stats_display()

    def _update_stats_display(self) -> None:
        """Update the compact stats label."""
        self.stats_label.setText(f"{self.utterances} utterances • {self.characters} chars")

    def set_status(self, status: str, is_error: bool = False) -> None:
        """Set the status message.

        Args:
            status: Status message (currently unused in minimal UI)
            is_error: Whether this is an error status (currently unused)
        """
        # In the new minimal UI, we don't show status messages
        # This method is kept for backward compatibility
        pass

    def show_stopping(self) -> None:
        """Show UI feedback that stopping is in progress."""
        self.action_button.setEnabled(False)
        self.is_recording = False
        self.pause_start = datetime.now()

    def show_stopped(self) -> None:
        """Re-enable the button after stopping is complete."""
        self.action_button.setEnabled(True)
        self.is_recording = False
        self.action_button.setIcon(load_svg_icon("play", 24))
