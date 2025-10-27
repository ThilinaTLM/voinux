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

            with self.config_file.open() as f:
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

            with self.config_file.open("w") as f:
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
        """Create a minimal default configuration file.

        Creates an empty config file with a helpful header comment.
        Users can add settings using 'voinux config set' or by editing the file.

        Raises:
            ConfigError: If creation fails
        """
        minimal_config = """# Voinux Configuration File
#
# This file contains your custom configuration overrides.
# Only settings that differ from defaults are stored here.
#
# To see all available settings and their current values:
#   voinux config list
#
# To change a setting:
#   voinux config set <key> <value>
#   Example: voinux config set faster_whisper.model large-v3
#
# To view current configuration:
#   voinux config show
#
# For full configuration reference, see:
#   https://docs.voinux.dev/configuration
#   Or: voinux config example
#
# All default settings are used unless overridden below.

"""

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w") as f:
                f.write(minimal_config)
            self.config_file.chmod(0o600)
        except Exception as e:
            raise ConfigError(f"Failed to create default config: {e}") from e
