"""Core domain entities for the Voinux voice transcription system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import numpy.typing as npt


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
