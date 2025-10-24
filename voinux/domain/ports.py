"""Port interfaces (contracts) for the Voinux voice transcription system.

These interfaces define the boundaries between the domain core and infrastructure adapters,
following the hexagonal architecture pattern.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path

from voinux.domain.entities import AudioChunk, ModelConfig, TranscriptionResult


class IAudioCapture(ABC):
    """Port for capturing audio from the microphone."""

    @abstractmethod
    async def start(self) -> None:
        """Start audio capture."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop audio capture and release resources."""
        ...

    @abstractmethod
    def stream(self) -> AsyncIterator[AudioChunk]:
        """Stream audio chunks as they are captured.

        Yields:
            AudioChunk: Audio data chunks ready for processing

        Raises:
            AudioCaptureError: If audio capture fails
        """
        ...


class ISpeechRecognizer(ABC):
    """Port for speech-to-text recognition."""

    @abstractmethod
    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize the speech recognizer with given model configuration.

        Args:
            model_config: Configuration for the model

        Raises:
            TranscriptionError: If initialization fails
        """
        ...

    @abstractmethod
    async def transcribe(self, audio_chunk: AudioChunk) -> TranscriptionResult:
        """Transcribe an audio chunk to text.

        Args:
            audio_chunk: Audio data to transcribe

        Returns:
            TranscriptionResult: Transcription result with text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the recognizer and release resources."""
        ...


class IKeyboardSimulator(ABC):
    """Port for simulating keyboard input to type text system-wide."""

    @abstractmethod
    async def type_text(self, text: str) -> None:
        """Type the given text into the currently active window.

        Args:
            text: Text to type

        Raises:
            KeyboardSimulationError: If typing fails
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if keyboard simulation is available on this system.

        Returns:
            bool: True if keyboard simulation is available
        """
        ...


class IVoiceActivationDetector(ABC):
    """Port for voice activation detection (VAD) to detect speech vs silence."""

    @abstractmethod
    async def initialize(self, threshold: float, sample_rate: int) -> None:
        """Initialize the VAD with given parameters.

        Args:
            threshold: Detection threshold (0.0 to 1.0, higher = more aggressive)
            sample_rate: Audio sample rate in Hz

        Raises:
            VADError: If initialization fails
        """
        ...

    @abstractmethod
    async def is_speech(self, audio_chunk: AudioChunk) -> bool:
        """Determine if an audio chunk contains speech.

        Args:
            audio_chunk: Audio data to analyze

        Returns:
            bool: True if speech is detected, False otherwise

        Raises:
            VADError: If detection fails
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the VAD and release resources."""
        ...


class IModelManager(ABC):
    """Port for managing Whisper models (download, cache, etc.)."""

    @abstractmethod
    async def download_model(self, model_name: str, force: bool = False) -> Path:
        """Download a Whisper model to local cache.

        Args:
            model_name: Name of the model (e.g., "large-v3-turbo")
            force: Force re-download even if cached

        Returns:
            Path: Path to the downloaded model directory

        Raises:
            ModelDownloadError: If download fails
        """
        ...

    @abstractmethod
    async def get_model_path(self, model_name: str) -> Path | None:
        """Get the local path to a cached model.

        Args:
            model_name: Name of the model

        Returns:
            Optional[Path]: Path to the model, or None if not cached
        """
        ...

    @abstractmethod
    async def list_cached_models(self) -> list[str]:
        """List all models currently in the cache.

        Returns:
            list[str]: List of cached model names
        """
        ...

    @abstractmethod
    def get_vram_requirements(self, model_name: str, compute_type: str) -> int:
        """Get estimated VRAM requirements for a model in MB.

        Args:
            model_name: Name of the model
            compute_type: Computation type (int8, float16, float32)

        Returns:
            int: Estimated VRAM in MB
        """
        ...


class IConfigRepository(ABC):
    """Port for loading and persisting configuration."""

    @abstractmethod
    async def load(self) -> dict[str, any]:  # type: ignore[valid-type]
        """Load configuration from storage.

        Returns:
            dict: Configuration dictionary

        Raises:
            ConfigError: If loading fails
        """
        ...

    @abstractmethod
    async def save(self, config: dict[str, any]) -> None:  # type: ignore[valid-type]
        """Save configuration to storage.

        Args:
            config: Configuration dictionary to save

        Raises:
            ConfigError: If saving fails
        """
        ...

    @abstractmethod
    async def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            bool: True if configuration exists
        """
        ...
