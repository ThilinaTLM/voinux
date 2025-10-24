"""Faster-Whisper speech recognition adapter."""

import asyncio
import logging
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from faster_whisper import WhisperModel

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionResult
from voinux.domain.exceptions import TranscriptionError
from voinux.domain.ports import ISpeechRecognizer

# Suppress deprecation warnings from dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", category=UserWarning, module="webrtcvad")

logger = logging.getLogger(__name__)


class WhisperRecognizer(ISpeechRecognizer):
    """Adapter using faster-whisper for speech recognition."""

    def __init__(self) -> None:
        """Initialize the Whisper recognizer."""
        self.model: Optional[WhisperModel] = None
        self.model_config: Optional[ModelConfig] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.device: str = "cpu"
        self._setup_cuda_libraries()

    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize the speech recognizer with given model configuration.

        Args:
            model_config: Configuration for the model

        Raises:
            TranscriptionError: If initialization fails
        """
        try:
            logger.info(
                "Initializing Whisper recognizer (model=%s, device=%s, compute_type=%s, beam_size=%d)",
                model_config.model_name,
                model_config.device,
                model_config.compute_type,
                model_config.beam_size,
            )

            self.model_config = model_config

            # Detect device if set to auto
            device = model_config.device
            if device == "auto":
                device = self._detect_device()
                logger.info("Auto-detected device: %s", device)

            self.device = device

            # Determine model path
            model_path = model_config.model_path or model_config.model_name
            logger.debug("Model path: %s", model_path)

            # Create thread pool executor (single thread to avoid memory duplication)
            self.executor = ThreadPoolExecutor(max_workers=1)

            # Initialize model in thread pool
            logger.info("Loading Whisper model (this may take a moment)...")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                lambda: WhisperModel(
                    model_path,
                    device=device,
                    compute_type=model_config.compute_type,
                ),
            )

            logger.info(
                "Whisper model loaded successfully (device=%s, compute_type=%s)",
                device,
                model_config.compute_type,
            )

        except Exception as e:
            logger.error("Failed to initialize Whisper model: %s", e, exc_info=True)
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
            logger.debug(
                "Starting Whisper transcription (audio_samples=%d, duration=%dms)",
                len(audio_chunk.data),
                audio_chunk.duration_ms,
            )

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

            # Get language and confidence
            language = info.language if hasattr(info, "language") else None
            confidence = info.language_probability if hasattr(info, "language_probability") else 0.0

            logger.debug(
                "Whisper transcription completed (text_length=%d, language=%s, "
                "confidence=%.2f, processing_time=%dms)",
                len(text.strip()),
                language or "unknown",
                confidence,
                processing_time_ms,
            )

            # Create result
            return TranscriptionResult(
                text=text.strip(),
                language=language,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error("Whisper transcription failed: %s", e, exc_info=True)
            raise TranscriptionError(f"Transcription failed: {e}") from e

    async def shutdown(self) -> None:
        """Shut down the recognizer and release resources."""
        logger.info("Shutting down Whisper recognizer")

        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None

        self.model = None
        self.model_config = None

        logger.debug("Whisper recognizer shutdown complete")

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

    def _setup_cuda_libraries(self) -> None:
        """Set up CUDA library paths for CTranslate2 to find cuDNN and cuBLAS.

        CTranslate2 may have trouble finding NVIDIA libraries installed via pip.
        This method adds the necessary paths to LD_LIBRARY_PATH and creates
        symlinks if needed to ensure proper library loading.
        """
        try:
            # Find the nvidia package directories in site-packages
            import site
            site_packages = site.getsitepackages()

            cuda_lib_paths = []
            for site_pkg in site_packages:
                site_path = Path(site_pkg)

                # Add NVIDIA cuDNN library path
                cudnn_path = site_path / "nvidia" / "cudnn" / "lib"
                if cudnn_path.exists():
                    cuda_lib_paths.append(str(cudnn_path))

                # Add NVIDIA cuBLAS library path
                cublas_path = site_path / "nvidia" / "cublas" / "lib"
                if cublas_path.exists():
                    cuda_lib_paths.append(str(cublas_path))

                # Add other NVIDIA library paths
                nvidia_path = site_path / "nvidia"
                if nvidia_path.exists():
                    for lib_dir in nvidia_path.iterdir():
                        if lib_dir.is_dir():
                            lib_path = lib_dir / "lib"
                            if lib_path.exists() and str(lib_path) not in cuda_lib_paths:
                                cuda_lib_paths.append(str(lib_path))

            if cuda_lib_paths:
                # Update LD_LIBRARY_PATH environment variable
                current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
                new_paths = [p for p in cuda_lib_paths if p not in current_ld_path]

                if new_paths:
                    if current_ld_path:
                        os.environ["LD_LIBRARY_PATH"] = ":".join(new_paths) + ":" + current_ld_path
                    else:
                        os.environ["LD_LIBRARY_PATH"] = ":".join(new_paths)

        except Exception:
            # Silently fail - this is a best-effort optimization
            # If it fails, the system may still work with system CUDA libraries
            pass

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
