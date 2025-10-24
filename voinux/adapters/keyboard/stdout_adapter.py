"""Stdout keyboard adapter for testing (prints instead of typing)."""

import logging

from voinux.domain.exceptions import KeyboardSimulationError
from voinux.domain.ports import IKeyboardSimulator

logger = logging.getLogger(__name__)


class StdoutKeyboard(IKeyboardSimulator):
    """Adapter that prints text to stdout instead of typing (for testing)."""

    def __init__(self, add_space_after: bool = True) -> None:
        """Initialize the stdout keyboard adapter.

        Args:
            add_space_after: Add space after each transcription
        """
        self.add_space_after = add_space_after

    async def type_text(self, text: str) -> None:
        """Print the given text to stdout.

        Args:
            text: Text to print

        Raises:
            KeyboardSimulationError: If printing fails
        """
        if not text.strip():
            logger.debug("Stdout keyboard: Skipping empty text")
            return

        try:
            # Add space if configured
            if self.add_space_after and not text.endswith(" "):
                text = text + " "

            logger.debug("Stdout keyboard: Printing text (length=%d)", len(text))
            print(text, end="", flush=True)

        except Exception as e:
            logger.error("Failed to print text: %s", e, exc_info=True)
            raise KeyboardSimulationError(f"Failed to print text: {e}") from e

    async def is_available(self) -> bool:
        """Check if stdout is available (always true).

        Returns:
            bool: Always True
        """
        return True
