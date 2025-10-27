"""Google Gemini API adapter for speech recognition."""

import json
import logging
from datetime import datetime
from typing import Any

import numpy as np

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionResult
from voinux.domain.exceptions import TranscriptionError
from voinux.domain.ports import ISpeechRecognizer

logger = logging.getLogger(__name__)


class GeminiRecognizer(ISpeechRecognizer):
    """Speech recognizer using Google Gemini Flash API."""

    # Gemini token rate: 32 tokens per second of audio
    TOKENS_PER_SECOND = 32
    # Model to use for transcription
    MODEL_NAME = "gemini-flash-lite-latest"

    def __init__(self) -> None:
        """Initialize the Gemini recognizer."""
        self.client: Any = None
        self._genai_types: Any = None
        self.model_config: ModelConfig | None = None
        self._initialized = False

    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize the Gemini API client.

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
                from google import genai
                from google.genai import types
            except ImportError as e:
                raise TranscriptionError(
                    "google-genai package not installed. "
                    "Install with: pip install voinux[cloud] or pip install google-genai"
                ) from e

            # Store types module for use in transcribe()
            self._genai_types = types

            # Initialize client
            self.client = genai.Client(api_key=model_config.api_key)

            self._initialized = True
            logger.info(f"Gemini recognizer initialized successfully (model: {self.MODEL_NAME})")

        except Exception as e:
            logger.exception("Failed to initialize Gemini recognizer")
            raise TranscriptionError(f"Failed to initialize Gemini: {e}") from e

    async def transcribe(self, audio_chunk: AudioChunk) -> TranscriptionResult:
        """Transcribe an audio chunk using Gemini API.

        Args:
            audio_chunk: Audio chunk to transcribe

        Returns:
            TranscriptionResult: Transcription result with text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self._initialized or not self.client:
            raise TranscriptionError("Recognizer not initialized")

        start_time = datetime.now()

        try:
            # Convert float32 audio to WAV format bytes
            wav_bytes = self._convert_to_wav_bytes(audio_chunk.data, audio_chunk.sample_rate)

            # Create audio Part with inline data (WAV format required by Gemini)
            audio_part = self._genai_types.Part(
                inline_data=self._genai_types.Blob(data=wav_bytes, mime_type="audio/wav")
            )

            # Build system instruction based on grammar correction setting
            if self.model_config and self.model_config.enable_grammar_correction:
                system_instruction = (
                    "You are a transcription AI. Convert the audio to text with proper "
                    "grammar, punctuation, and capitalization. Fix grammar errors while "
                    "preserving the speaker's intent. Output only the corrected transcription "
                    "with no additional commentary."
                )
            else:
                system_instruction = (
                    "You are a transcription AI. Convert the audio to text exactly as spoken. "
                    "Output only the transcription with no additional commentary, explanations, "
                    "or metadata."
                )

            # Create content with audio
            contents = [
                self._genai_types.Content(
                    role="user",
                    parts=[audio_part],
                )
            ]

            # Configure generation with JSON schema for structured output
            generate_config = self._genai_types.GenerateContentConfig(
                thinking_config=self._genai_types.ThinkingConfig(thinking_budget=0),
                response_mime_type="application/json",
                response_schema=self._genai_types.Schema(
                    type=self._genai_types.Type.OBJECT,
                    required=["transcription"],
                    properties={
                        "transcription": self._genai_types.Schema(
                            type=self._genai_types.Type.STRING,
                        ),
                    },
                ),
                system_instruction=[self._genai_types.Part.from_text(text=system_instruction)],
            )

            # Generate content with streaming
            transcribed_text = ""
            stream = await self.client.aio.models.generate_content_stream(
                model=self.MODEL_NAME,
                contents=contents,
                config=generate_config,
            )
            async for chunk in stream:
                if chunk.text:
                    transcribed_text += chunk.text

            # Parse JSON response
            try:
                response_json = json.loads(transcribed_text)
                final_text = response_json.get("transcription", "").strip()
            except json.JSONDecodeError:
                # Fallback: use raw text if JSON parsing fails
                logger.warning("Failed to parse JSON response, using raw text")
                final_text = transcribed_text.strip()

            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Estimate tokens used (32 tokens/sec of audio)
            duration_sec = audio_chunk.duration_ms / 1000.0
            estimated_tokens = int(duration_sec * self.TOKENS_PER_SECOND)

            logger.debug(
                "Gemini transcription: %s (tokens: %d, time: %dms)",
                final_text[:50],
                estimated_tokens,
                processing_time_ms,
            )

            return TranscriptionResult(
                text=final_text,
                language=self.model_config.language if self.model_config else None,
                confidence=1.0,  # Gemini doesn't provide confidence scores
                processing_time_ms=processing_time_ms,
                timestamp=end_time,
            )

        except Exception as e:
            logger.exception("Gemini transcription failed")
            raise TranscriptionError(f"Gemini transcription failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the Gemini recognizer and cleanup resources.

        Raises:
            TranscriptionError: If shutdown fails
        """
        try:
            logger.info("Shutting down Gemini recognizer")

            self._initialized = False
            self.client = None
            self._genai_types = None
            self.model_config = None

            logger.info("Gemini recognizer shutdown complete")

        except Exception as e:
            logger.exception("Failed to shutdown Gemini recognizer")
            raise TranscriptionError(f"Failed to shutdown Gemini: {e}") from e

    def _convert_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """Convert float32 audio to WAV format bytes for Gemini API.

        Gemini requires WAV format, not raw PCM. This adds a proper WAV header
        to the PCM data.

        Args:
            audio_data: Audio data as float32 numpy array (range: -1.0 to 1.0)
            sample_rate: Sample rate in Hz (e.g., 16000)

        Returns:
            bytes: Complete WAV file data (header + PCM data)
        """
        # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
        pcm_int16 = (audio_data * 32767).astype(np.int16)
        pcm_bytes = pcm_int16.tobytes()

        # WAV file parameters
        num_channels = 1  # Mono
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        file_size = 36 + data_size  # 44 bytes header - 8 bytes + data

        # Build WAV header (44 bytes total)
        wav_header = bytearray()

        # RIFF header (12 bytes)
        wav_header.extend(b"RIFF")  # ChunkID
        wav_header.extend(file_size.to_bytes(4, "little"))  # ChunkSize
        wav_header.extend(b"WAVE")  # Format

        # fmt subchunk (24 bytes)
        wav_header.extend(b"fmt ")  # Subchunk1ID
        wav_header.extend((16).to_bytes(4, "little"))  # Subchunk1Size (16 for PCM)
        wav_header.extend((1).to_bytes(2, "little"))  # AudioFormat (1 = PCM)
        wav_header.extend(num_channels.to_bytes(2, "little"))  # NumChannels
        wav_header.extend(sample_rate.to_bytes(4, "little"))  # SampleRate
        wav_header.extend(byte_rate.to_bytes(4, "little"))  # ByteRate
        wav_header.extend(block_align.to_bytes(2, "little"))  # BlockAlign
        wav_header.extend(bits_per_sample.to_bytes(2, "little"))  # BitsPerSample

        # data subchunk (8 bytes header)
        wav_header.extend(b"data")  # Subchunk2ID
        wav_header.extend(data_size.to_bytes(4, "little"))  # Subchunk2Size

        # Combine header and PCM data
        return bytes(wav_header) + pcm_bytes
