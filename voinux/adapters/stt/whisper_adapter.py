"""Faster-Whisper speech recognition adapter."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

import torch
from faster_whisper import WhisperModel

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionResult
from voinux.domain.exceptions import TranscriptionError
from voinux.domain.ports import ISpeechRecognizer


class WhisperRecognizer(ISpeechRecognizer):
    """Adapter using faster-whisper for speech recognition."""

    def __init__(self) -> None:
        """Initialize the Whisper recognizer."""
        self.model: Optional[WhisperModel] = None
        self.model_config: Optional[ModelConfig] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.device: str = "cpu"

    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize the speech recognizer with given model configuration.

        Args:
            model_config: Configuration for the model

        Raises:
            TranscriptionError: If initialization fails
        """
        try:
            self.model_config = model_config

            # Detect device if set to auto
            device = model_config.device
            if device == "auto":
                device = self._detect_device()

            self.device = device

            # Determine model path
            model_path = model_config.model_path or model_config.model_name

            # Create thread pool executor (single thread to avoid memory duplication)
            self.executor = ThreadPoolExecutor(max_workers=1)

            # Initialize model in thread pool
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                lambda: WhisperModel(
                    model_path,
                    device=device,
                    compute_type=model_config.compute_type,
                ),
            )

        except Exception as e:
            raise TranscriptionError(f"Failed to initialize Whisper model: {e}") from e

    async def transcribe(self, audio_chunk: AudioChunk) -> TranscriptionResult:
        """Transcribe an audio chunk to text.

        Args:
            audio_chunk: Audio data to transcribe

        Returns:
            TranscriptionResult: Transcription result with text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if self.model is None or self.model_config is None:
            raise TranscriptionError("Model not initialized. Call initialize() first.")

        try:
            start_time = time.time()

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                self.executor,
                lambda: self.model.transcribe(  # type: ignore[union-attr]
                    audio_chunk.data,
                    beam_size=self.model_config.beam_size,  # type: ignore[union-attr]
                    language=self.model_config.language,  # type: ignore[union-attr]
                    vad_filter=self.model_config.vad_filter,  # type: ignore[union-attr]
                ),
            )

            # Collect all segments into text
            text = " ".join(segment.text for segment in segments)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create result
            return TranscriptionResult(
                text=text.strip(),
                language=info.language if hasattr(info, "language") else None,
                confidence=info.language_probability if hasattr(info, "language_probability") else 0.0,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now(),
            )

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e

    async def shutdown(self) -> None:
        """Shut down the recognizer and release resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None

        self.model = None
        self.model_config = None

    def _detect_device(self) -> str:
        """Detect the best available device (CUDA, ROCm, or CPU).

        Returns:
            str: Device string ("cuda", "cpu")
        """
        # Check for CUDA
        if torch.cuda.is_available():
            return "cuda"

        # Check for ROCm (AMD GPU)
        try:
            if hasattr(torch.version, "hip") and torch.version.hip is not None:
                return "cuda"  # ROCm uses "cuda" device string in PyTorch
        except Exception:
            pass

        # Fall back to CPU
        return "cpu"

    def get_device_info(self) -> dict[str, any]:  # type: ignore[valid-type]
        """Get information about the current device.

        Returns:
            dict: Device information
        """
        info = {
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available():
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            info["cuda_memory_allocated"] = torch.cuda.memory_allocated(0)
            info["cuda_memory_reserved"] = torch.cuda.memory_reserved(0)

        return info
