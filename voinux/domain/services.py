"""Core domain services for orchestrating voice transcription."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionSession
from voinux.domain.exceptions import SessionError, TranscriptionError
from voinux.domain.ports import (
    IAudioCapture,
    IKeyboardSimulator,
    ISpeechRecognizer,
    IVoiceActivationDetector,
)


class TranscriptionPipeline:
    """Core service that orchestrates the audio → VAD → STT → keyboard pipeline."""

    def __init__(
        self,
        audio_capture: IAudioCapture,
        vad: IVoiceActivationDetector,
        recognizer: ISpeechRecognizer,
        keyboard: IKeyboardSimulator,
        session: TranscriptionSession,
        vad_enabled: bool = True,
    ) -> None:
        """Initialize the transcription pipeline.

        Args:
            audio_capture: Audio capture adapter
            vad: Voice activation detection adapter
            recognizer: Speech recognition adapter
            keyboard: Keyboard simulation adapter
            session: Transcription session for tracking statistics
            vad_enabled: Whether to use VAD filtering
        """
        self.audio_capture = audio_capture
        self.vad = vad
        self.recognizer = recognizer
        self.keyboard = keyboard
        self.session = session
        self.vad_enabled = vad_enabled
        self._running = False
        self._stop_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Start the transcription pipeline.

        Raises:
            TranscriptionError: If pipeline fails to start
        """
        if self._running:
            raise TranscriptionError("Pipeline is already running")

        self._running = True
        self._stop_event = asyncio.Event()

        try:
            await self.audio_capture.start()
            await self._run_pipeline()
        except Exception as e:
            self._running = False
            self.session.end()
            raise TranscriptionError(f"Pipeline failed: {e}") from e

    async def stop(self) -> None:
        """Stop the transcription pipeline gracefully."""
        if not self._running:
            return

        self._running = False
        if self._stop_event:
            self._stop_event.set()

        await self.audio_capture.stop()
        await self.recognizer.shutdown()
        await self.vad.shutdown()
        self.session.end()

    async def _run_pipeline(self) -> None:
        """Main pipeline loop that processes audio chunks."""
        try:
            async for audio_chunk in self.audio_capture.stream():
                if not self._running:
                    break

                await self._process_chunk(audio_chunk)
        except Exception as e:
            raise TranscriptionError(f"Pipeline processing failed: {e}") from e

    async def _process_chunk(self, audio_chunk: AudioChunk) -> None:
        """Process a single audio chunk through the pipeline.

        Args:
            audio_chunk: Audio chunk to process
        """
        start_time = datetime.now()

        # Check for speech using VAD
        is_speech = True
        if self.vad_enabled:
            is_speech = await self.vad.is_speech(audio_chunk)

        if not is_speech:
            self.session.record_chunk(is_speech=False)
            return

        # Transcribe speech
        try:
            result = await self.recognizer.transcribe(audio_chunk)
            processing_time_ms = result.processing_time_ms
        except Exception as e:
            # Log error but continue processing
            self.session.record_chunk(is_speech=True, transcription_time_ms=0)
            raise TranscriptionError(f"Transcription failed: {e}") from e

        self.session.record_chunk(is_speech=True, transcription_time_ms=processing_time_ms)

        # Type the transcribed text
        if result.text.strip():
            try:
                await self.keyboard.type_text(result.text)
                self.session.record_typing(len(result.text))
            except Exception as e:
                raise TranscriptionError(f"Keyboard typing failed: {e}") from e

    @property
    def is_running(self) -> bool:
        """Check if the pipeline is currently running."""
        return self._running


class SessionManager:
    """Service for managing transcription sessions."""

    def __init__(self) -> None:
        """Initialize the session manager."""
        self._current_session: Optional[TranscriptionSession] = None

    def create_session(self, model_config: ModelConfig) -> TranscriptionSession:
        """Create a new transcription session.

        Args:
            model_config: Model configuration for the session

        Returns:
            TranscriptionSession: New session instance

        Raises:
            SessionError: If a session is already active
        """
        if self._current_session and self._current_session.is_active:
            raise SessionError("A session is already active. End it before creating a new one.")

        session_id = str(uuid.uuid4())
        session = TranscriptionSession(
            session_id=session_id,
            started_at=datetime.now(),
            model_config=model_config,
        )

        self._current_session = session
        return session

    def get_current_session(self) -> Optional[TranscriptionSession]:
        """Get the current active session.

        Returns:
            Optional[TranscriptionSession]: Current session or None
        """
        return self._current_session

    def end_current_session(self) -> Optional[TranscriptionSession]:
        """End the current session and return it for reporting.

        Returns:
            Optional[TranscriptionSession]: The ended session, or None if no active session
        """
        if self._current_session:
            self._current_session.end()

        ended_session = self._current_session
        self._current_session = None
        return ended_session
