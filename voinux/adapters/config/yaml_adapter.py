"""YAML configuration repository adapter."""

from pathlib import Path
from typing import Any

import yaml

from voinux.domain.exceptions import ConfigError
from voinux.domain.ports import IConfigRepository


class YAMLConfigRepository(IConfigRepository):
    """Adapter for loading and saving configuration from/to YAML files."""

    def __init__(self, config_file: Path) -> None:
        """Initialize the YAML config repository.

        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file

    async def load(self) -> dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            dict: Configuration dictionary

        Raises:
            ConfigError: If loading fails
        """
        try:
            if not self.config_file.exists():
                return {}

            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
                return config if config is not None else {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML config: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_file}: {e}") from e

    async def save(self, config: dict[str, Any]) -> None:
        """Save configuration to YAML file.

        Args:
            config: Configuration dictionary to save

        Raises:
            ConfigError: If saving fails
        """
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w") as f:
                yaml.safe_dump(
                    config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                )

            # Set restrictive permissions (user read/write only)
            self.config_file.chmod(0o600)
        except Exception as e:
            raise ConfigError(f"Failed to save config to {self.config_file}: {e}") from e

    async def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            bool: True if configuration exists
        """
        return self.config_file.exists()

    async def create_default_config(self) -> None:
        """Create a default configuration file with comments.

        Raises:
            ConfigError: If creation fails
        """
        default_config = """# Voinux Configuration File
# This file controls the behavior of the Voinux voice transcription system.

# Faster-Whisper Model Configuration
faster_whisper:
  # Model size: tiny, base, small, medium, large-v3, large-v3-turbo
  # Smaller models are faster but less accurate
  model: base

  # Device: cuda (NVIDIA GPU), cpu, or auto (detect automatically)
  device: auto

  # Compute type: int8 (fastest, less VRAM), float16 (balanced), float32 (slowest, most accurate)
  compute_type: int8

  # Beam size for decoding (higher = more accurate but slower)
  beam_size: 5

  # Target language (e.g., "en", "es", "fr") or null for auto-detection
  language: null

  # Custom model path (null to use default cache)
  model_path: null

# Audio Capture Configuration
audio:
  # Sample rate in Hz (16000 is optimal for Whisper)
  sample_rate: 16000

  # Audio chunk duration in milliseconds
  chunk_duration_ms: 1000

  # Audio backend: auto, soundcard, pyaudio
  backend: auto

  # Specific audio device index (null for default device)
  device_index: null

# Voice Activation Detection (VAD) Configuration
vad:
  # Enable VAD to skip processing silence (saves GPU usage)
  enabled: true

  # VAD threshold (0.0-1.0, higher = more aggressive filtering)
  threshold: 0.5

  # WebRTC VAD aggressiveness (0-3, higher = more aggressive)
  aggressiveness: 2

# Keyboard Simulation Configuration
keyboard:
  # Keyboard backend: auto (detect), xdotool (X11), ydotool (Wayland), stdout (testing)
  backend: auto

  # Delay between keystrokes in milliseconds (0 for instant typing)
  typing_delay_ms: 0

  # Add space after each transcription
  add_space_after: true

# System Configuration
system:
  # Cache directory for models
  # cache_dir: ~/.cache/voinux

  # Configuration directory
  # config_dir: ~/.config/voinux

  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_level: INFO

  # Log file path (null for stdout only)
  log_file: null
"""

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                f.write(default_config)
            self.config_file.chmod(0o600)
        except Exception as e:
            raise ConfigError(f"Failed to create default config: {e}") from e
