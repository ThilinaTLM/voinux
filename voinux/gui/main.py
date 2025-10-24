"""Main GUI application entry point."""

import asyncio
import logging
import sys
from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from voinux.application.use_cases import StartTranscription
from voinux.config.config import Config
from voinux.domain.entities import TranscriptionSession
from voinux.gui.main_window import FloatingPanel
from voinux.gui.system_tray import SystemTrayManager

logger = logging.getLogger(__name__)


class VoinuxGUI:
    """Main GUI application controller."""

    def __init__(self, config: Config):
        """Initialize the GUI application.

        Args:
            config: Application configuration
        """
        self.config = config
        self.app: Optional[QApplication] = None
        self.loop: Optional[QEventLoop] = None
        self.window: Optional[FloatingPanel] = None
        self.tray: Optional[SystemTrayManager] = None
        self.use_case: Optional[StartTranscription] = None
        self.session: Optional[TranscriptionSession] = None

        # Stats update timer
        self.stats_timer: Optional[QTimer] = None

    def run(self) -> None:
        """Run the GUI application."""
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Voinux")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running with tray icon

        # Set up asyncio event loop with Qt integration
        self.loop = QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

        # Create GUI components
        self.window = FloatingPanel()
        self.tray = SystemTrayManager()

        # Connect signals
        self.window.stop_requested.connect(self._on_stop_requested)
        self.tray.show_hide_requested.connect(self._toggle_window)
        self.tray.stop_requested.connect(self._on_stop_requested)
        self.tray.quit_requested.connect(self._on_quit_requested)

        # Show window and tray
        self.window.show()
        self.tray.show()

        # Start transcription
        self.loop.create_task(self._start_transcription())

        # Set up stats update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(100)  # Update every 100ms

        # Run the event loop
        try:
            with self.loop:
                self.loop.run_forever()
        finally:
            # Cleanup
            if self.use_case:
                self.loop.run_until_complete(self.use_case.stop())

    async def _start_transcription(self) -> None:
        """Start the transcription pipeline."""
        try:
            logger.info("Starting transcription in GUI mode")

            # Create use case
            self.use_case = StartTranscription(self.config)

            # Status callback
            def on_status(status: str) -> None:
                logger.info("Status: %s", status)
                if self.window:
                    self.window.set_status(status)

            # Audio chunk callback for waveform
            def on_audio_chunk(chunk, is_speech: bool) -> None:
                if self.window:
                    self.window.add_audio_data(chunk.data, is_speech)

            # Start session tracking
            if self.window:
                self.window.start_session()

            # Execute transcription
            self.session = await self.use_case.execute(
                on_status_change=on_status, on_audio_chunk=on_audio_chunk
            )

            # Show completion notification
            if self.tray:
                self.tray.show_message(
                    "Transcription Complete",
                    f"Session ended. Typed {self.session.total_characters_typed} characters.",
                )

            # Update final status
            if self.window:
                self.window.set_status("✓ Session Complete")

        except Exception as e:
            logger.error("Transcription failed: %s", e, exc_info=True)
            if self.window:
                self.window.set_status(f"Error: {e}", is_error=True)
            if self.tray:
                self.tray.show_message("Error", f"Transcription failed: {e}")

    def _update_stats(self) -> None:
        """Update GUI statistics from the current session."""
        if not self.use_case or not self.use_case.pipeline or not self.window:
            return

        session = self.use_case.pipeline.session

        # Update statistics display
        self.window.update_stats(
            utterances=session.total_utterances_processed,
            characters=session.total_characters_typed,
        )

    def _on_stop_requested(self) -> None:
        """Handle stop request from GUI."""
        logger.info("Stop requested from GUI")
        if self.use_case:
            # Stop transcription asynchronously
            self.loop.create_task(self._stop_transcription())

    async def _stop_transcription(self) -> None:
        """Stop the transcription pipeline."""
        try:
            if self.use_case:
                await self.use_case.stop()
                logger.info("Transcription stopped")

                if self.window:
                    self.window.set_status("✓ Stopped")

                if self.tray:
                    self.tray.show_message("Stopped", "Transcription stopped.")

        except Exception as e:
            logger.error("Error stopping transcription: %s", e, exc_info=True)

    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.window:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.show()
                self.window.activateWindow()

    def _on_quit_requested(self) -> None:
        """Handle quit request."""
        logger.info("Quit requested from GUI")

        # Stop transcription first
        if self.use_case:
            self.loop.create_task(self._cleanup_and_quit())
        else:
            self.app.quit()

    async def _cleanup_and_quit(self) -> None:
        """Clean up and quit the application."""
        try:
            if self.use_case:
                await self.use_case.stop()
        except Exception as e:
            logger.error("Error during cleanup: %s", e, exc_info=True)
        finally:
            if self.app:
                self.app.quit()


def run_gui(config: Config) -> None:
    """Run the GUI application.

    Args:
        config: Application configuration
    """
    gui = VoinuxGUI(config)
    gui.run()
