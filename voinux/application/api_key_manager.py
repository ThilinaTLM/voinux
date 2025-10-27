"""API key management with precedence: CLI > Env > Config."""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys with precedence logic and security best practices."""

    @staticmethod
    def get_api_key(
        provider: str,
        cli_api_key: str | None = None,
        config_api_key: str | None = None,
    ) -> str | None:
        """Get API key for a provider with precedence: CLI > Env > Config.

        Args:
            provider: Provider name (e.g., "gemini")
            cli_api_key: API key from CLI argument (highest priority)
            config_api_key: API key from config file (lowest priority)

        Returns:
            str | None: API key if found, None otherwise
        """
        # Priority 1: CLI argument (explicit override)
        if cli_api_key:
            logger.warning(
                "API key passed via CLI argument. This is visible in process list. "
                "Consider using environment variables instead."
            )
            return cli_api_key

        # Priority 2: Environment variable (recommended for security)
        env_var_name = f"{provider.upper()}_API_KEY"
        env_api_key = os.getenv(env_var_name)
        if env_api_key:
            logger.debug(f"Using API key from environment variable: {env_var_name}")
            return env_api_key

        # Priority 3: Config file (convenience for desktop users)
        if config_api_key:
            logger.debug(f"Using API key from config file for provider: {provider}")
            return config_api_key

        return None

    @staticmethod
    def redact_api_key(api_key: str) -> str:
        """Redact API key for logging (show first 8 and last 4 chars).

        Args:
            api_key: Full API key

        Returns:
            str: Redacted API key (e.g., "sk-abcd...xyz1")
        """
        if len(api_key) <= 12:
            # Too short to redact safely, show only first 4 chars
            return api_key[:4] + "..." if len(api_key) > 4 else "***"

        return f"{api_key[:8]}...{api_key[-4:]}"

    @staticmethod
    def validate_api_key(api_key: str | None, provider: str) -> str:
        """Validate that API key is present and not a placeholder.

        Args:
            api_key: API key to validate
            provider: Provider name (for error messages)

        Returns:
            str: Validated API key

        Raises:
            ValueError: If API key is missing or invalid
        """
        if not api_key:
            raise ValueError(
                f"API key required for {provider}. Set via:\n"
                f"  1. CLI: --api-key YOUR_KEY\n"
                f"  2. Env: export {provider.upper()}_API_KEY=YOUR_KEY\n"
                f"  3. Config: ~/.config/voinux/config.yaml ({provider}.api_key)"
            )

        # Check for common placeholder values
        placeholder_values = {
            "YOUR_API_KEY_HERE",
            "YOUR_API_KEY",
            "REPLACE_ME",
            "TODO",
            "XXX",
            "",
        }

        if api_key.upper() in placeholder_values:
            raise ValueError(
                f"Invalid API key for {provider}: appears to be a placeholder. "
                f"Please set a real API key."
            )

        if len(api_key) < 10:
            raise ValueError(f"Invalid API key for {provider}: too short (minimum 10 characters)")

        return api_key


def get_provider_config(
    provider: str, config: Any, cli_overrides: dict[str, Any]
) -> dict[str, Any]:
    """Extract provider-specific configuration with CLI overrides.

    Args:
        provider: Provider name (e.g., "gemini")
        config: Main configuration object
        cli_overrides: CLI argument overrides

    Returns:
        dict: Provider configuration with CLI overrides applied
    """
    # Get provider config from main config
    provider_config = {}

    if provider == "gemini":
        provider_config = {
            "api_key": config.gemini.api_key,
            "enable_grammar_correction": config.gemini.enable_grammar_correction,
            "privacy_acknowledged": config.gemini.privacy_acknowledged,
            "max_monthly_cost_usd": config.gemini.max_monthly_cost_usd,
            "warn_at_cost_usd": config.gemini.warn_at_cost_usd,
            "api_endpoint": config.gemini.api_endpoint,
        }

    # Apply CLI overrides
    for key, value in cli_overrides.items():
        if value is not None:
            provider_config[key] = value

    return provider_config
