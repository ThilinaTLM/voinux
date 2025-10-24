"""Audio waveform visualization widget."""

import numpy as np
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Widget that displays a live audio waveform visualization."""

    def __init__(self, parent=None, buffer_size: int = 100):
        """Initialize the waveform widget.

        Args:
            parent: Parent widget
            buffer_size: Number of audio level samples to display
        """
        super().__init__(parent)
        self.buffer_size = buffer_size
        self.audio_levels = [0.0] * buffer_size
        self.is_speech_buffer = [False] * buffer_size
        self.current_index = 0

        # Colors - updated for new minimal design
        self.bg_color = QColor(10, 10, 10)  # Match window background
        self.silence_color = QColor(60, 60, 60)  # Darker gray
        self.speech_color = QColor(229, 165, 165)  # Pink to match buttons
        self.grid_color = QColor(30, 30, 30)  # Subtle grid

        # Set minimum size (height will be flexible)
        self.setMinimumSize(300, 60)

        # Update timer for smooth animation
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)  # 20 FPS

    def add_audio_data(self, audio_chunk: np.ndarray, is_speech: bool = False) -> None:
        """Add new audio data to the waveform.

        Args:
            audio_chunk: Audio data as numpy array
            is_speech: Whether this chunk contains speech
        """
        # Calculate RMS (root mean square) for audio level
        if len(audio_chunk) > 0:
            rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
            # Normalize to 0-1 range (assuming 16-bit audio)
            level = min(1.0, rms / 5000.0)
        else:
            level = 0.0

        # Add to circular buffer
        self.audio_levels[self.current_index] = level
        self.is_speech_buffer[self.current_index] = is_speech
        self.current_index = (self.current_index + 1) % self.buffer_size

    def paintEvent(self, event):
        """Paint the waveform visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw grid lines
        painter.setPen(QPen(self.grid_color, 1))
        height = self.height()
        painter.drawLine(0, height // 2, self.width(), height // 2)
        painter.drawLine(0, height // 4, self.width(), height // 4)
        painter.drawLine(0, 3 * height // 4, self.width(), 3 * height // 4)

        # Draw waveform
        if self.width() <= 0:
            return

        bar_width = max(1, self.width() / self.buffer_size)
        center_y = height / 2

        for i in range(self.buffer_size):
            # Calculate position in circular buffer
            buffer_index = (self.current_index + i) % self.buffer_size
            level = self.audio_levels[buffer_index]
            is_speech = self.is_speech_buffer[buffer_index]

            # Choose color based on speech detection
            color = self.speech_color if is_speech else self.silence_color
            painter.setPen(QPen(color, bar_width))

            # Draw bar from center
            bar_height = level * (height / 2) * 0.9  # 90% of half height
            x = i * bar_width

            # Draw top and bottom bars
            painter.drawLine(
                int(x), int(center_y - bar_height), int(x), int(center_y + bar_height)
            )

    def reset(self) -> None:
        """Reset the waveform display."""
        self.audio_levels = [0.0] * self.buffer_size
        self.is_speech_buffer = [False] * self.buffer_size
        self.current_index = 0
