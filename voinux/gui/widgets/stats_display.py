"""Statistics display widget."""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatsDisplayWidget(QWidget):
    """Widget that displays real-time transcription statistics."""

    def __init__(self, parent=None):
        """Initialize the statistics display widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Create labels
        self.duration_label = QLabel("Duration: 0:00")
        self.utterances_label = QLabel("Utterances: 0")
        self.characters_label = QLabel("Characters: 0")

        # Style labels
        font = QFont("monospace", 10)
        for label in [self.duration_label, self.utterances_label, self.characters_label]:
            label.setFont(font)
            label.setStyleSheet("color: #CCCCCC; background: transparent;")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        layout.addWidget(self.duration_label)
        layout.addWidget(self.utterances_label)
        layout.addWidget(self.characters_label)
        layout.addStretch()

        self.setLayout(layout)

        # Track session start time
        self.session_start: datetime | None = None

    def start_session(self) -> None:
        """Start tracking a new session."""
        self.session_start = datetime.now()
        self.update_duration()

    def update_duration(self) -> None:
        """Update the duration display."""
        if self.session_start is None:
            self.duration_label.setText("Duration: 0:00")
            return

        elapsed = datetime.now() - self.session_start
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        self.duration_label.setText(f"Duration: {minutes}:{seconds:02d}")

    def update_stats(self, utterances: int, characters: int) -> None:
        """Update the statistics display.

        Args:
            utterances: Total number of utterances transcribed
            characters: Total number of characters typed
        """
        self.utterances_label.setText(f"Utterances: {utterances}")
        self.characters_label.setText(f"Characters: {characters}")

    def reset(self) -> None:
        """Reset all statistics."""
        self.session_start = None
        self.duration_label.setText("Duration: 0:00")
        self.utterances_label.setText("Utterances: 0")
        self.characters_label.setText("Characters: 0")
