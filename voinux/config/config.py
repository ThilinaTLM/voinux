"""Configuration management for Voinux."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FasterWhisperConfig:
    """Configuration for the faster-whisper model."""

    model: str = "base"  # Model size: tiny, base, small, medium, large-v3, large-v3-turbo
    device: str = "auto"  # Device: cuda, cpu, auto
    compute_type: str = "int8"  # Compute type: int8, float16, float32
    beam_size: int = 5  # Beam size for decoding
    language: str | None = None  # Target language (None for auto-detection)
    model_path: str | None = None  # Custom model path (None for default cache)


@dataclass
class AudioConfig:
    """Configuration for audio capture."""

    sample_rate: int = 16000  # Sample rate in Hz
    chunk_duration_ms: int = 1000  # Chunk duration in milliseconds
    backend: str = "auto"  # Audio backend: auto, soundcard, pyaudio
    device_index: int | None = None  # Specific device index (None for default)


@dataclass
class VADConfig:
    """Configuration for voice activation detection."""

    enabled: bool = True  # Whether VAD is enabled
    threshold: float = 0.5  # VAD threshold (0.0-1.0, higher = more aggressive)
    aggressiveness: int = 2  # WebRTC VAD aggressiveness (0-3)


@dataclass
class KeyboardConfig:
    """Configuration for keyboard simulation."""

    backend: str = "auto"  # Keyboard backend: auto, xdotool, ydotool, stdout
    typing_delay_ms: int = 0  # Delay between keystrokes in ms (0 for instant)
    add_space_after: bool = True  # Add space after each transcription


@dataclass
class BufferingConfig:
    """Configuration for speech buffering."""

    silence_threshold_ms: int = 1200  # Wait time after speech before processing
    max_buffer_duration_ms: int = 30000  # Maximum buffer size (30 seconds)
    min_utterance_duration_ms: int = 300  # Minimum utterance duration to process


@dataclass
class SystemConfig:
    """System-level configuration."""

    cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "voinux")
    config_dir: Path = field(default_factory=lambda: Path.home() / ".config" / "voinux")
    log_level: str = "INFO"  # Log level: DEBUG, INFO, WARNING, ERROR
    log_file: Path | None = None  # Log file path (None for stdout only)


@dataclass
class Config:
    """Main configuration container."""

    faster_whisper: FasterWhisperConfig = field(default_factory=FasterWhisperConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    buffering: BufferingConfig = field(default_factory=BufferingConfig)
    system: SystemConfig = field(default_factory=SystemConfig)

    @classmethod
    def default(cls) -> "Config":
        """Create a configuration with all default values."""
        return cls()

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Validate model name
        valid_models = {"tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"}
        if self.faster_whisper.model not in valid_models:
            raise ValueError(
                f"Invalid model: {self.faster_whisper.model}. Must be one of {valid_models}"
            )

        # Validate device
        valid_devices = {"cuda", "cpu", "auto"}
        if self.faster_whisper.device not in valid_devices:
            raise ValueError(
                f"Invalid device: {self.faster_whisper.device}. Must be one of {valid_devices}"
            )

        # Validate compute type
        valid_compute_types = {"int8", "float16", "float32"}
        if self.faster_whisper.compute_type not in valid_compute_types:
            raise ValueError(
                f"Invalid compute_type: {self.faster_whisper.compute_type}. "
                f"Must be one of {valid_compute_types}"
            )

        # Validate beam size
        if self.faster_whisper.beam_size < 1:
            raise ValueError(f"beam_size must be >= 1, got {self.faster_whisper.beam_size}")

        # Validate audio config
        if self.audio.sample_rate <= 0:
            raise ValueError(f"sample_rate must be > 0, got {self.audio.sample_rate}")

        if self.audio.chunk_duration_ms <= 0:
            raise ValueError(f"chunk_duration_ms must be > 0, got {self.audio.chunk_duration_ms}")

        # Validate VAD threshold
        if not 0.0 <= self.vad.threshold <= 1.0:
            raise ValueError(f"VAD threshold must be between 0.0 and 1.0, got {self.vad.threshold}")

        if not 0 <= self.vad.aggressiveness <= 3:
            raise ValueError(
                f"VAD aggressiveness must be between 0 and 3, got {self.vad.aggressiveness}"
            )

        # Validate keyboard config
        if self.keyboard.typing_delay_ms < 0:
            raise ValueError(f"typing_delay_ms must be >= 0, got {self.keyboard.typing_delay_ms}")

        # Validate buffering config
        if self.buffering.silence_threshold_ms < 0:
            raise ValueError(
                f"silence_threshold_ms must be >= 0, got {self.buffering.silence_threshold_ms}"
            )
        if self.buffering.max_buffer_duration_ms < 1000:
            raise ValueError(
                f"max_buffer_duration_ms must be >= 1000ms, got {self.buffering.max_buffer_duration_ms}"
            )
        if self.buffering.min_utterance_duration_ms < 0:
            raise ValueError(
                f"min_utterance_duration_ms must be >= 0, got {self.buffering.min_utterance_duration_ms}"
            )

        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.system.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.system.log_level}. Must be one of {valid_log_levels}"
            )

    def merge_with_overrides(self, overrides: dict[str, any]) -> "Config":  # type: ignore[valid-type]
        """Create a new config with overrides applied.

        Args:
            overrides: Dictionary of override values

        Returns:
            Config: New config with overrides applied
        """
        # This is a simplified implementation - a real one would recursively merge
        # For now, we'll just apply direct overrides
        new_config = Config(
            faster_whisper=FasterWhisperConfig(
                **{**vars(self.faster_whisper), **overrides.get("faster_whisper", {})}
            ),
            audio=AudioConfig(**{**vars(self.audio), **overrides.get("audio", {})}),
            vad=VADConfig(**{**vars(self.vad), **overrides.get("vad", {})}),
            keyboard=KeyboardConfig(**{**vars(self.keyboard), **overrides.get("keyboard", {})}),
            buffering=BufferingConfig(**{**vars(self.buffering), **overrides.get("buffering", {})}),
            system=SystemConfig(**{**vars(self.system), **overrides.get("system", {})}),
        )
        new_config.validate()
        return new_config
