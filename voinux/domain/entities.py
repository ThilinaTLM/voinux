"""Core domain entities for the Voinux voice transcription system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np
import numpy.typing as npt


class SpeechState(Enum):
    """States for the speech buffer state machine."""

    IDLE = "idle"  # No speech detected, buffer is empty
    BUFFERING = "buffering"  # Currently buffering speech chunks
    PROCESSING = "processing"  # Processing buffered audio


@dataclass(frozen=True)
class AudioChunk:
    """Represents a chunk of audio data captured from the microphone."""

    data: npt.NDArray[np.float32]  # Audio samples (mono, 16kHz, float32)
    sample_rate: int  # Sample rate in Hz (typically 16000)
    timestamp: datetime  # When the chunk was captured
    duration_ms: int  # Duration of the chunk in milliseconds

    def __post_init__(self) -> None:
        """Validate audio chunk data."""
        if self.sample_rate <= 0:
            raise ValueError(f"Invalid sample_rate: {self.sample_rate}")
        if self.duration_ms <= 0:
            raise ValueError(f"Invalid duration_ms: {self.duration_ms}")
        if len(self.data) == 0:
            raise ValueError("Audio data cannot be empty")


@dataclass(frozen=True)
class TranscriptionResult:
    """Represents the result of transcribing an audio chunk."""

    text: str  # Transcribed text
    language: Optional[str]  # Detected or specified language code (e.g., "en", "es")
    confidence: float  # Confidence score (0.0 to 1.0)
    processing_time_ms: int  # Time taken for transcription in milliseconds
    timestamp: datetime  # When the transcription completed

    def __post_init__(self) -> None:
        """Validate transcription result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.processing_time_ms < 0:
            raise ValueError(f"Invalid processing_time_ms: {self.processing_time_ms}")


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for the Whisper model."""

    model_name: str  # Model size (tiny, base, small, medium, large-v3, large-v3-turbo)
    device: str  # Device to run on ("cuda", "cpu", "auto")
    compute_type: str  # Computation precision ("int8", "float16", "float32")
    beam_size: int  # Beam size for beam search decoding
    language: Optional[str]  # Target language (None for auto-detection)
    vad_filter: bool  # Whether to use VAD filtering
    model_path: Optional[str]  # Custom model path (None for default cache)

    def __post_init__(self) -> None:
        """Validate model configuration."""
        valid_models = {"tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"}
        if self.model_name not in valid_models:
            raise ValueError(
                f"Invalid model_name: {self.model_name}. Must be one of {valid_models}"
            )

        valid_devices = {"cuda", "cpu", "auto"}
        if self.device not in valid_devices:
            raise ValueError(
                f"Invalid device: {self.device}. Must be one of {valid_devices}"
            )

        valid_compute_types = {"int8", "float16", "float32"}
        if self.compute_type not in valid_compute_types:
            raise ValueError(
                f"Invalid compute_type: {self.compute_type}. "
                f"Must be one of {valid_compute_types}"
            )

        if self.beam_size < 1:
            raise ValueError(f"beam_size must be >= 1, got {self.beam_size}")


@dataclass(frozen=True)
class BufferConfig:
    """Configuration for speech buffering behavior."""

    silence_threshold_ms: int = 1200  # Wait time after speech before processing
    max_buffer_duration_ms: int = 30000  # Maximum buffer size (30 seconds)
    min_utterance_duration_ms: int = 300  # Minimum utterance to process

    def __post_init__(self) -> None:
        """Validate buffer configuration."""
        if self.silence_threshold_ms < 0:
            raise ValueError(f"silence_threshold_ms must be >= 0, got {self.silence_threshold_ms}")
        if self.max_buffer_duration_ms < 1000:
            raise ValueError(f"max_buffer_duration_ms must be >= 1000ms, got {self.max_buffer_duration_ms}")
        if self.min_utterance_duration_ms < 0:
            raise ValueError(f"min_utterance_duration_ms must be >= 0, got {self.min_utterance_duration_ms}")


@dataclass
class SpeechBuffer:
    """Manages buffering of audio chunks until utterance is complete."""

    buffer_config: BufferConfig
    sample_rate: int
    state: SpeechState = SpeechState.IDLE
    buffered_chunks: list[AudioChunk] = field(default_factory=list)
    silence_duration_ms: int = 0
    total_buffered_duration_ms: int = 0
    utterance_start_time: Optional[datetime] = None

    def add_chunk(self, chunk: AudioChunk, is_speech: bool) -> None:
        """Add a chunk to the buffer and update state.

        Args:
            chunk: Audio chunk to add
            is_speech: Whether the chunk contains speech
        """
        if is_speech:
            # Reset silence counter when speech is detected
            self.silence_duration_ms = 0

            # Start buffering if idle
            if self.state == SpeechState.IDLE:
                self.state = SpeechState.BUFFERING
                self.utterance_start_time = chunk.timestamp

            # Add chunk to buffer
            if self.state == SpeechState.BUFFERING:
                self.buffered_chunks.append(chunk)
                self.total_buffered_duration_ms += chunk.duration_ms
        else:
            # Increment silence counter if we were buffering
            if self.state == SpeechState.BUFFERING:
                self.silence_duration_ms += chunk.duration_ms

    def should_process(self) -> bool:
        """Check if the buffer should be processed.

        Returns:
            bool: True if buffer should be processed
        """
        # Don't process if idle or empty
        if self.state != SpeechState.BUFFERING or not self.buffered_chunks:
            return False

        # Process if silence threshold reached
        if self.silence_duration_ms >= self.buffer_config.silence_threshold_ms:
            return True

        # Process if max buffer duration reached (safety limit)
        if self.total_buffered_duration_ms >= self.buffer_config.max_buffer_duration_ms:
            return True

        return False

    def should_ignore(self) -> bool:
        """Check if the buffered utterance should be ignored (too short).

        Returns:
            bool: True if utterance is too short to process
        """
        return self.total_buffered_duration_ms < self.buffer_config.min_utterance_duration_ms

    def get_concatenated_audio(self) -> AudioChunk:
        """Concatenate all buffered chunks into a single AudioChunk.

        Returns:
            AudioChunk: Single chunk containing all buffered audio

        Raises:
            ValueError: If buffer is empty
        """
        if not self.buffered_chunks:
            raise ValueError("Cannot concatenate empty buffer")

        # Concatenate all audio data
        concatenated_data = np.concatenate([chunk.data for chunk in self.buffered_chunks])

        # Use the timestamp of the first chunk
        first_chunk = self.buffered_chunks[0]

        return AudioChunk(
            data=concatenated_data,
            sample_rate=self.sample_rate,
            timestamp=first_chunk.timestamp,
            duration_ms=self.total_buffered_duration_ms,
        )

    def reset(self) -> None:
        """Reset the buffer to idle state."""
        self.state = SpeechState.IDLE
        self.buffered_chunks.clear()
        self.silence_duration_ms = 0
        self.total_buffered_duration_ms = 0
        self.utterance_start_time = None


@dataclass
class TranscriptionSession:
    """Represents an active transcription session with statistics."""

    session_id: str
    started_at: datetime
    model_config: ModelConfig
    total_chunks_processed: int = 0
    total_speech_chunks: int = 0
    total_silence_chunks: int = 0
    total_transcription_time_ms: int = 0
    total_characters_typed: int = 0
    # Utterance-based statistics
    total_utterances_processed: int = 0
    total_utterance_duration_ms: int = 0
    total_buffer_overflows: int = 0  # Times max buffer was hit
    is_active: bool = True
    ended_at: Optional[datetime] = None

    def record_chunk(self, is_speech: bool, transcription_time_ms: int = 0) -> None:
        """Record processing of an audio chunk."""
        self.total_chunks_processed += 1
        if is_speech:
            self.total_speech_chunks += 1
            self.total_transcription_time_ms += transcription_time_ms
        else:
            self.total_silence_chunks += 1

    def record_utterance(self, utterance_duration_ms: int, transcription_time_ms: int, was_overflow: bool = False) -> None:
        """Record processing of a complete utterance.

        Args:
            utterance_duration_ms: Duration of the utterance in milliseconds
            transcription_time_ms: Time taken to transcribe
            was_overflow: Whether this was triggered by buffer overflow
        """
        self.total_utterances_processed += 1
        self.total_utterance_duration_ms += utterance_duration_ms
        self.total_transcription_time_ms += transcription_time_ms
        if was_overflow:
            self.total_buffer_overflows += 1

    def record_typing(self, character_count: int) -> None:
        """Record characters typed to output."""
        self.total_characters_typed += character_count

    def end(self) -> None:
        """Mark the session as ended."""
        self.is_active = False
        self.ended_at = datetime.now()

    @property
    def duration_seconds(self) -> float:
        """Calculate session duration in seconds."""
        end_time = self.ended_at if self.ended_at else datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def average_transcription_time_ms(self) -> float:
        """Calculate average transcription time per speech chunk."""
        if self.total_speech_chunks == 0:
            return 0.0
        return self.total_transcription_time_ms / self.total_speech_chunks

    @property
    def vad_efficiency_percent(self) -> float:
        """Calculate percentage of chunks filtered by VAD (silence)."""
        if self.total_chunks_processed == 0:
            return 0.0
        return (self.total_silence_chunks / self.total_chunks_processed) * 100

    @property
    def average_utterance_duration_ms(self) -> float:
        """Calculate average duration of processed utterances."""
        if self.total_utterances_processed == 0:
            return 0.0
        return self.total_utterance_duration_ms / self.total_utterances_processed
