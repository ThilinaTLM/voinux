"""Core domain services for orchestrating voice transcription."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from voinux.domain.entities import (
    AudioChunk,
    BufferConfig,
    ModelConfig,
    SpeechBuffer,
    TranscriptionSession,
)
from voinux.domain.exceptions import SessionError, TranscriptionError
from voinux.domain.ports import (
    IAudioCapture,
    IKeyboardSimulator,
    ISpeechRecognizer,
    IVoiceActivationDetector,
)

logger = logging.getLogger(__name__)


class TranscriptionPipeline:
    """Core service that orchestrates the audio → VAD → STT → keyboard pipeline.

    Uses utterance-based buffering: buffers audio chunks while speaking,
    waits for silence, then transcribes complete utterances.
    """

    def __init__(
        self,
        audio_capture: IAudioCapture,
        vad: IVoiceActivationDetector,
        recognizer: ISpeechRecognizer,
        keyboard: IKeyboardSimulator,
        session: TranscriptionSession,
        buffer_config: Optional[BufferConfig] = None,
        vad_enabled: bool = True,
    ) -> None:
        """Initialize the transcription pipeline.

        Args:
            audio_capture: Audio capture adapter
            vad: Voice activation detection adapter
            recognizer: Speech recognition adapter
            keyboard: Keyboard simulation adapter
            session: Transcription session for tracking statistics
            buffer_config: Buffer configuration (uses defaults if None)
            vad_enabled: Whether to use VAD filtering
        """
        self.audio_capture = audio_capture
        self.vad = vad
        self.recognizer = recognizer
        self.keyboard = keyboard
        self.session = session
        self.buffer_config = buffer_config or BufferConfig()
        self.vad_enabled = vad_enabled
        self._running = False
        self._stop_event: Optional[asyncio.Event] = None
        self._speech_buffer: Optional[SpeechBuffer] = None

    async def start(self) -> None:
        """Start the transcription pipeline.

        Raises:
            TranscriptionError: If pipeline fails to start
        """
        if self._running:
            raise TranscriptionError("Pipeline is already running")

        self._running = True
        self._stop_event = asyncio.Event()

        # Initialize speech buffer (we'll get sample rate from first chunk)
        self._speech_buffer = None

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
        """Process a single audio chunk through the buffering pipeline.

        Args:
            audio_chunk: Audio chunk to process
        """
        # Initialize speech buffer on first chunk
        if self._speech_buffer is None:
            self._speech_buffer = SpeechBuffer(
                buffer_config=self.buffer_config,
                sample_rate=audio_chunk.sample_rate,
            )

        # Check for speech using VAD
        is_speech = True
        if self.vad_enabled:
            is_speech = await self.vad.is_speech(audio_chunk)

        # Record chunk in session statistics
        self.session.record_chunk(is_speech=is_speech)

        # Add chunk to buffer
        self._speech_buffer.add_chunk(audio_chunk, is_speech)

        # Check if we should process the buffered utterance
        if self._speech_buffer.should_process():
            await self._process_buffered_utterance()

    async def _process_buffered_utterance(self) -> None:
        """Process the complete buffered utterance."""
        if self._speech_buffer is None:
            return

        # Check if utterance is too short to process
        if self._speech_buffer.should_ignore():
            self._speech_buffer.reset()
            return

        try:
            # Get concatenated audio
            utterance_audio = self._speech_buffer.get_concatenated_audio()
            utterance_duration_ms = self._speech_buffer.total_buffered_duration_ms

            # Check if this was a buffer overflow
            was_overflow = (
                self._speech_buffer.total_buffered_duration_ms
                >= self._speech_buffer.buffer_config.max_buffer_duration_ms
            )

            # Reset buffer before transcription (so we can start buffering next utterance)
            self._speech_buffer.reset()

            # Transcribe the complete utterance
            result = await self.recognizer.transcribe(utterance_audio)

            # Record utterance statistics
            self.session.record_utterance(
                utterance_duration_ms=utterance_duration_ms,
                transcription_time_ms=result.processing_time_ms,
                was_overflow=was_overflow,
            )

            # Type the transcribed text
            if result.text.strip():
                await self.keyboard.type_text(result.text)
                self.session.record_typing(len(result.text))

        except Exception as e:
            # Reset buffer on error to avoid stuck state
            if self._speech_buffer:
                self._speech_buffer.reset()
            raise TranscriptionError(f"Failed to process utterance: {e}") from e

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
