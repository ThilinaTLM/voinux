"""Main floating panel window for Voinux GUI."""

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from voinux.gui.widgets.stats_display import StatsDisplayWidget
from voinux.gui.widgets.waveform import WaveformWidget


class FloatingPanel(QWidget):
    """Floating panel window for voice transcription control."""

    # Signals
    stop_requested = pyqtSignal()

    def __init__(self):
        """Initialize the floating panel."""
        super().__init__()

        # Window setup - frameless, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # Don't show in taskbar
        )

        # Set window properties
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        # Dragging state
        self.dragging = False
        self.drag_position = QPoint()

        # Build UI
        self._build_ui()

        # Update timer for duration
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_duration)
        self.update_timer.start(1000)  # Update every second

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title bar (for dragging)
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)

        # Status label
        self.status_label = QLabel("🎤 Listening...")
        self.status_label.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #76AF50; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Waveform widget
        self.waveform = WaveformWidget(self)
        main_layout.addWidget(self.waveform)

        # Statistics display
        self.stats_display = StatsDisplayWidget(self)
        main_layout.addWidget(self.stats_display)

        # Stop button
        self.stop_button = QPushButton("Stop Transcription")
        self.stop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
            QPushButton:pressed {
                background-color: #F44336;
            }
        """
        )
        self.stop_button.clicked.connect(self.stop_requested.emit)
        main_layout.addWidget(self.stop_button)

        # Set main layout
        self.setLayout(main_layout)

        # Set overall styling
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                border-radius: 10px;
            }
        """
        )

    def _create_title_bar(self) -> QWidget:
        """Create a custom title bar for dragging.

        Returns:
            QWidget: Title bar widget
        """
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #2D2D2D; border-radius: 5px;")

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("Voinux")
        title_label.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #CCCCCC; background: transparent;")
        layout.addWidget(title_label)

        layout.addStretch()

        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #CCCCCC;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
                border-radius: 3px;
            }
        """
        )
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button)

        title_bar.setLayout(layout)
        return title_bar

    def _update_duration(self) -> None:
        """Update the duration display."""
        self.stats_display.update_duration()

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
        self.stats_display.start_session()
        self.waveform.reset()
        self.status_label.setText("🎤 Listening...")
        self.status_label.setStyleSheet("color: #76AF50; background: transparent;")

    def update_stats(self, utterances: int, characters: int) -> None:
        """Update statistics display.

        Args:
            utterances: Number of utterances
            characters: Number of characters typed
        """
        self.stats_display.update_stats(utterances, characters)

    def add_audio_data(self, audio_data, is_speech: bool = False) -> None:
        """Add audio data to waveform.

        Args:
            audio_data: Audio data (numpy array)
            is_speech: Whether this is speech
        """
        self.waveform.add_audio_data(audio_data, is_speech)

    def set_status(self, status: str, is_error: bool = False) -> None:
        """Set the status message.

        Args:
            status: Status message
            is_error: Whether this is an error status
        """
        color = "#D32F2F" if is_error else "#76AF50"
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color}; background: transparent;")

    def show_stopping(self) -> None:
        """Show UI feedback that stopping is in progress."""
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stopping...")
        self.set_status("⏹ Stopping transcription...")
