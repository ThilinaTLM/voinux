"""Google Gemini Live API adapter for speech recognition."""

import logging
from datetime import datetime
from typing import Any

import numpy as np

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionResult
from voinux.domain.exceptions import TranscriptionError
from voinux.domain.ports import ISpeechRecognizer

logger = logging.getLogger(__name__)


class GeminiRecognizer(ISpeechRecognizer):
    """Speech recognizer using Google Gemini Flash 2.5 Live API."""

    # Gemini token rate: 32 tokens per second of audio
    TOKENS_PER_SECOND = 32

    def __init__(self) -> None:
        """Initialize the Gemini recognizer."""
        self.client: Any = None
        self.session: Any = None
        self.model_config: ModelConfig | None = None
        self._initialized = False

    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize the Gemini API client and session.

        Args:
            model_config: Model configuration with API key and settings

        Raises:
            TranscriptionError: If initialization fails
        """
        try:
            logger.info("Initializing Gemini recognizer")

            if model_config.provider != "gemini":
                raise ValueError(f"Invalid provider: {model_config.provider}")

            if not model_config.api_key:
                raise ValueError("API key required for Gemini provider")

            self.model_config = model_config

            # Import google-genai SDK (optional dependency)
            try:
                from google import genai  # type: ignore[import-untyped]
            except ImportError as e:
                raise TranscriptionError(
                    "google-genai package not installed. "
                    "Install with: pip install voinux[cloud] or pip install google-genai"
                ) from e

            # Initialize client
            self.client = genai.Client(api_key=model_config.api_key)

            # Configure Live API session
            config_dict: dict[str, Any] = {
                "generation_config": {
                    "response_modalities": ["TEXT"],  # Only want transcription text
                }
            }

            # Add system instruction for grammar correction if enabled
            if model_config.enable_grammar_correction:
                config_dict["system_instruction"] = (
                    "You are a speech-to-text transcription assistant. "
                    "Transcribe the user's speech accurately with proper grammar, "
                    "punctuation, and capitalization. Fix minor grammar errors while "
                    "preserving the user's intent and voice."
                )

            # Create Live API session
            self.session = self.client.aio.live.connect(
                model="gemini-2.0-flash-exp",  # Gemini Flash 2.5 model
                config=config_dict,
            )

            # Start the session
            await self.session.__aenter__()

            self._initialized = True
            logger.info("Gemini recognizer initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize Gemini recognizer")
            raise TranscriptionError(f"Failed to initialize Gemini: {e}") from e

    async def transcribe(self, audio_chunk: AudioChunk) -> TranscriptionResult:
        """Transcribe an audio chunk using Gemini Live API.

        Args:
            audio_chunk: Audio chunk to transcribe

        Returns:
            TranscriptionResult: Transcription result with text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self._initialized or not self.session:
            raise TranscriptionError("Recognizer not initialized")

        start_time = datetime.now()

        try:
            # Convert float32 audio to int16 PCM bytes
            pcm_bytes = self._convert_to_pcm_bytes(audio_chunk.data)

            # Send audio to Gemini
            await self.session.send(
                {
                    "mime_type": "audio/pcm",
                    "data": pcm_bytes,
                },
                end_of_turn=True,  # Indicate end of utterance
            )

            # Receive and parse response
            transcribed_text = ""
            async for response in self.session.receive():
                if response.text:
                    transcribed_text += response.text

                # Break after receiving text response
                if transcribed_text:
                    break

            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Estimate tokens used (32 tokens/sec of audio)
            duration_sec = audio_chunk.duration_ms / 1000.0
            estimated_tokens = int(duration_sec * self.TOKENS_PER_SECOND)

            logger.debug(
                "Gemini transcription: %s (tokens: %d, time: %dms)",
                transcribed_text[:50],
                estimated_tokens,
                processing_time_ms,
            )

            return TranscriptionResult(
                text=transcribed_text.strip(),
                language=self.model_config.language if self.model_config else None,
                confidence=1.0,  # Gemini doesn't provide confidence scores
                processing_time_ms=processing_time_ms,
                timestamp=end_time,
            )

        except Exception as e:
            logger.exception("Gemini transcription failed")
            raise TranscriptionError(f"Gemini transcription failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the Gemini session and cleanup resources.

        Raises:
            TranscriptionError: If shutdown fails
        """
        try:
            logger.info("Shutting down Gemini recognizer")

            if self.session:
                try:
                    await self.session.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning("Error closing Gemini session: %s", e)

            self._initialized = False
            self.session = None
            self.client = None

            logger.info("Gemini recognizer shutdown complete")

        except Exception as e:
            logger.exception("Failed to shutdown Gemini recognizer")
            raise TranscriptionError(f"Failed to shutdown Gemini: {e}") from e

    def _convert_to_pcm_bytes(self, audio_data: np.ndarray) -> bytes:
        """Convert float32 audio to int16 PCM bytes for Gemini API.

        Args:
            audio_data: Audio data as float32 numpy array (range: -1.0 to 1.0)

        Returns:
            bytes: PCM audio data as int16 bytes
        """
        # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
        pcm_int16 = (audio_data * 32767).astype(np.int16)
        return pcm_int16.tobytes()
