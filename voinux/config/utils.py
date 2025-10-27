"""Utilities for configuration management."""

from dataclasses import fields
from typing import Any

from voinux.config.config import (
    AudioConfig,
    BufferingConfig,
    Config,
    FasterWhisperConfig,
    GeminiConfig,
    KeyboardConfig,
    NoiseSuppressionConfig,
    SystemConfig,
    VADConfig,
)

# Mapping of section names to their config classes
CONFIG_SECTIONS = {
    "faster_whisper": FasterWhisperConfig,
    "audio": AudioConfig,
    "vad": VADConfig,
    "keyboard": KeyboardConfig,
    "buffering": BufferingConfig,
    "noise_suppression": NoiseSuppressionConfig,
    "gemini": GeminiConfig,
    "system": SystemConfig,
}


def parse_config_key(key: str) -> tuple[str, str]:
    """Parse a dot-notation config key into section and field.

    Args:
        key: Config key in dot notation (e.g., "faster_whisper.model")

    Returns:
        tuple[str, str]: (section, field) tuple

    Raises:
        ValueError: If key format is invalid

    Examples:
        >>> parse_config_key("faster_whisper.model")
        ("faster_whisper", "model")
        >>> parse_config_key("vad.enabled")
        ("vad", "enabled")
    """
    parts = key.split(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid config key: '{key}'. Must be in format 'section.field' (e.g., 'faster_whisper.model')"
        )

    section, field = parts

    if section not in CONFIG_SECTIONS:
        valid_sections = ", ".join(CONFIG_SECTIONS.keys())
        raise ValueError(f"Invalid config section: '{section}'. Valid sections: {valid_sections}")

    return section, field


def validate_config_key(key: str) -> bool:
    """Check if a config key is valid.

    Args:
        key: Config key in dot notation (e.g., "faster_whisper.model")

    Returns:
        bool: True if key exists in config schema

    Examples:
        >>> validate_config_key("faster_whisper.model")
        True
        >>> validate_config_key("invalid.key")
        False
    """
    try:
        section, field = parse_config_key(key)
        config_class = CONFIG_SECTIONS[section]
        field_names = {f.name for f in fields(config_class)}
    except (ValueError, KeyError):
        return False
    else:
        return field in field_names


def get_all_config_keys() -> list[str]:
    """Get a list of all valid config keys in dot notation.

    Returns:
        list[str]: List of all config keys (e.g., ["faster_whisper.model", ...])

    Examples:
        >>> keys = get_all_config_keys()
        >>> "faster_whisper.model" in keys
        True
    """
    all_keys: list[str] = []
    for section, config_class in CONFIG_SECTIONS.items():
        all_keys.extend(f"{section}.{field.name}" for field in fields(config_class))
    return sorted(all_keys)


def get_config_value(config: Config, key: str) -> Any:
    """Get a config value using dot notation.

    Args:
        config: Config object
        key: Config key in dot notation (e.g., "faster_whisper.model")

    Returns:
        Any: The config value

    Raises:
        ValueError: If key is invalid

    Examples:
        >>> config = Config.default()
        >>> get_config_value(config, "faster_whisper.model")
        "base"
    """
    section, field = parse_config_key(key)

    # Get the section object
    section_obj = getattr(config, section)

    # Get the field value
    if not hasattr(section_obj, field):
        raise ValueError(f"Field '{field}' not found in section '{section}'")

    return getattr(section_obj, field)


def set_config_value(config_dict: dict[str, Any], key: str, value: str) -> None:
    """Set a config value in a config dictionary with type coercion.

    Args:
        config_dict: Configuration dictionary (mutable)
        key: Config key in dot notation (e.g., "faster_whisper.model")
        value: String value to set (will be coerced to appropriate type)

    Raises:
        ValueError: If key is invalid

    Examples:
        >>> config_dict = {}
        >>> set_config_value(config_dict, "faster_whisper.model", "base")
        >>> config_dict
        {"faster_whisper": {"model": "base"}}
    """
    section, field = parse_config_key(key)

    # Get the config class to determine field type
    config_class = CONFIG_SECTIONS[section]
    field_type = None
    for f in fields(config_class):
        if f.name == field:
            field_type = f.type
            break

    if field_type is None:
        raise ValueError(f"Field '{field}' not found in section '{section}'")

    # Coerce value to the appropriate type
    coerced_value = coerce_value(value, field_type)

    # Set the value in the nested dictionary
    if section not in config_dict:
        config_dict[section] = {}

    config_dict[section][field] = coerced_value


def coerce_value(value: str, target_type: Any) -> Any:  # noqa: PLR0911
    """Coerce a string value to the target type.

    Args:
        value: String value to coerce
        target_type: Target type (from field annotation)

    Returns:
        Any: Coerced value

    Raises:
        ValueError: If coercion fails

    Note:
        Multiple return statements are necessary for different type coercions.
    """
    # Handle None/null
    if value.lower() in ("none", "null", ""):
        return None

    # Get the origin type for generic types (e.g., str | None -> str)
    import typing

    # Handle Union types (e.g., str | None, int | None)
    if hasattr(typing, "get_origin") and typing.get_origin(target_type) is typing.Union:
        # Get the non-None type from the Union
        args = typing.get_args(target_type)
        non_none_types = [t for t in args if t is not type(None)]
        if non_none_types:
            target_type = non_none_types[0]

    # Handle bool (must come before int since bool is subclass of int)
    if target_type is bool:
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False
        raise ValueError(
            f"Invalid boolean value: '{value}'. Use true/false, yes/no, 1/0, or on/off"
        )

    # Handle int
    if target_type is int:
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"Invalid integer value: '{value}'") from e

    # Handle float
    if target_type is float:
        try:
            return float(value)
        except ValueError as e:
            raise ValueError(f"Invalid float value: '{value}'") from e

    # Handle Path (for system.cache_dir, etc.)
    from pathlib import Path

    if target_type is Path:
        return Path(value)

    # Default to string
    return value


def get_config_diff(config: Config, defaults: Config) -> dict[str, Any]:
    """Compute the difference between a config and defaults.

    Only returns values that differ from defaults, enabling minimal config files.

    Args:
        config: Current configuration
        defaults: Default configuration

    Returns:
        dict: Dictionary containing only non-default values

    Examples:
        >>> config = Config.default()
        >>> config.faster_whisper.model = "large-v3"
        >>> diff = get_config_diff(config, Config.default())
        >>> diff
        {"faster_whisper": {"model": "large-v3"}}
    """
    diff: dict[str, Any] = {}

    for section in CONFIG_SECTIONS:
        section_obj = getattr(config, section)
        default_section_obj = getattr(defaults, section)

        section_diff = {}
        for field in fields(section_obj):
            value = getattr(section_obj, field.name)
            default_value = getattr(default_section_obj, field.name)

            # Compare values (handling Path objects specially)
            from pathlib import Path

            if isinstance(value, Path) and isinstance(default_value, Path):
                if value != default_value:
                    section_diff[field.name] = str(value)
            elif value != default_value:
                # Convert Path to string for storage
                if isinstance(value, Path):
                    section_diff[field.name] = str(value)
                else:
                    section_diff[field.name] = value

        if section_diff:
            diff[section] = section_diff

    return diff
