"""Configuration loader with precedence support."""

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from voinux.adapters.config.yaml_adapter import YAMLConfigRepository
from voinux.config.config import Config
from voinux.domain.exceptions import ConfigError


class ConfigLoader:
    """Loads configuration with precedence: defaults → file → CLI → env."""

    def __init__(self, config_file: Optional[Path] = None) -> None:
        """Initialize the config loader.

        Args:
            config_file: Path to configuration file (None for default location)
        """
        if config_file is None:
            config_file = Path.home() / ".config" / "voinux" / "config.yaml"

        self.config_file = config_file
        self.repo = YAMLConfigRepository(config_file)

    async def load(
        self,
        cli_overrides: Optional[dict[str, Any]] = None,
        env_overrides: Optional[dict[str, Any]] = None,
    ) -> Config:
        """Load configuration with all precedence layers.

        Args:
            cli_overrides: Overrides from CLI arguments
            env_overrides: Overrides from environment variables

        Returns:
            Config: Loaded and validated configuration

        Raises:
            ConfigError: If configuration is invalid
        """
        # Start with defaults
        config = Config.default()

        # Load from file
        if await self.repo.exists():
            try:
                file_config = await self.repo.load()
                config = self._merge_config(config, file_config)
            except Exception as e:
                raise ConfigError(f"Failed to load config from file: {e}") from e

        # Apply CLI overrides
        if cli_overrides:
            config = self._merge_config(config, cli_overrides)

        # Apply environment variable overrides
        if env_overrides:
            config = self._merge_config(config, env_overrides)

        # Apply env vars with VOINUX_ prefix
        env_config = self._load_from_env()
        if env_config:
            config = self._merge_config(config, env_config)

        # Validate final configuration
        try:
            config.validate()
        except ValueError as e:
            raise ConfigError(f"Invalid configuration: {e}") from e

        return config

    async def save(self, config: Config) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save

        Raises:
            ConfigError: If save fails
        """
        config_dict = self._config_to_dict(config)
        await self.repo.save(config_dict)

    async def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            bool: True if configuration exists
        """
        return await self.repo.exists()

    async def create_default(self) -> None:
        """Create a default configuration file.

        Raises:
            ConfigError: If creation fails
        """
        await self.repo.create_default_config()

    def _merge_config(self, base: Config, overrides: dict[str, Any]) -> Config:
        """Recursively merge overrides into base configuration.

        Args:
            base: Base configuration
            overrides: Override values

        Returns:
            Config: Merged configuration
        """
        base_dict = self._config_to_dict(base)
        merged_dict = self._deep_merge(base_dict, overrides)
        return self._dict_to_config(merged_dict)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            dict: Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _config_to_dict(self, config: Config) -> dict[str, Any]:
        """Convert Config object to dictionary.

        Args:
            config: Configuration object

        Returns:
            dict: Configuration dictionary
        """
        return {
            "faster_whisper": asdict(config.faster_whisper),
            "audio": asdict(config.audio),
            "vad": asdict(config.vad),
            "keyboard": asdict(config.keyboard),
            "system": {
                **asdict(config.system),
                "cache_dir": str(config.system.cache_dir),
                "config_dir": str(config.system.config_dir),
                "log_file": str(config.system.log_file) if config.system.log_file else None,
            },
        }

    def _dict_to_config(self, config_dict: dict[str, Any]) -> Config:
        """Convert dictionary to Config object.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Config: Configuration object
        """
        # Convert string paths back to Path objects
        if "system" in config_dict:
            system = config_dict["system"]
            if "cache_dir" in system and isinstance(system["cache_dir"], str):
                system["cache_dir"] = Path(system["cache_dir"])
            if "config_dir" in system and isinstance(system["config_dir"], str):
                system["config_dir"] = Path(system["config_dir"])
            if "log_file" in system and system["log_file"] is not None:
                system["log_file"] = Path(system["log_file"])

        from voinux.config.config import (
            AudioConfig,
            FasterWhisperConfig,
            KeyboardConfig,
            SystemConfig,
            VADConfig,
        )

        return Config(
            faster_whisper=FasterWhisperConfig(**config_dict.get("faster_whisper", {})),
            audio=AudioConfig(**config_dict.get("audio", {})),
            vad=VADConfig(**config_dict.get("vad", {})),
            keyboard=KeyboardConfig(**config_dict.get("keyboard", {})),
            system=SystemConfig(**config_dict.get("system", {})),
        )

    def _load_from_env(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables.

        Environment variables should be prefixed with VOINUX_ and use double underscores
        for nested values. For example:
        - VOINUX_FASTER_WHISPER__MODEL=base
        - VOINUX_AUDIO__SAMPLE_RATE=16000

        Returns:
            dict: Configuration overrides from environment
        """
        config_dict: dict[str, Any] = {}

        for key, value in os.environ.items():
            if not key.startswith("VOINUX_"):
                continue

            # Remove prefix and split by double underscore
            key_parts = key[7:].lower().split("__")

            if len(key_parts) == 2:
                section, option = key_parts
                if section not in config_dict:
                    config_dict[section] = {}
                config_dict[section][option] = self._parse_env_value(value)
            elif len(key_parts) == 1:
                # Top-level config (unlikely but supported)
                config_dict[key_parts[0]] = self._parse_env_value(value)

        return config_dict

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Any: Parsed value (str, int, float, bool, or None)
        """
        # Handle boolean values
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Handle None/null
        if value.lower() in ("none", "null", ""):
            return None

        # Try to parse as number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Return as string
        return value
