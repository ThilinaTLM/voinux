"""YDotool keyboard simulation adapter for Wayland."""

import asyncio
import logging

from voinux.domain.exceptions import KeyboardSimulationError
from voinux.domain.ports import IKeyboardSimulator

logger = logging.getLogger(__name__)


class YDotoolKeyboard(IKeyboardSimulator):
    """Adapter using ydotool for keyboard simulation on Wayland."""

    def __init__(self, typing_delay_ms: int = 0, add_space_after: bool = True) -> None:
        """Initialize the ydotool keyboard adapter.

        Args:
            typing_delay_ms: Delay between keystrokes in milliseconds
            add_space_after: Add space after each transcription
        """
        self.typing_delay_ms = typing_delay_ms
        self.add_space_after = add_space_after

    async def type_text(self, text: str) -> None:
        """Type the given text into the currently active window.

        Args:
            text: Text to type

        Raises:
            KeyboardSimulationError: If typing fails
        """
        if not text.strip():
            logger.debug("YDotool keyboard: Skipping empty text")
            return

        try:
            # Add space if configured
            if self.add_space_after and not text.endswith(" "):
                text = text + " "

            logger.debug(
                "YDotool keyboard: Typing text (length=%d, delay=%dms)",
                len(text),
                self.typing_delay_ms,
            )

            # Build ydotool command
            cmd = ["ydotool", "type"]

            if self.typing_delay_ms > 0:
                cmd.extend(["--key-delay", str(self.typing_delay_ms)])

            cmd.append(text)

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            _stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()

                # Check for permission errors
                if "permission denied" in error_msg.lower() or "uinput" in error_msg.lower():
                    logger.error("YDotool permission error: %s", error_msg)
                    raise KeyboardSimulationError(
                        "ydotool requires uinput permissions. "
                        "Run: sudo usermod -aG input $USER && "
                        'echo \'KERNEL=="uinput", GROUP="input", MODE="0660"\' | '
                        "sudo tee /etc/udev/rules.d/80-uinput.rules"
                    )

                logger.error("YDotool command failed: %s", error_msg)
                raise KeyboardSimulationError(f"ydotool command failed: {error_msg}")

            logger.debug("YDotool keyboard: Text typed successfully")

        except FileNotFoundError:
            logger.exception("ydotool not found on system")
            raise KeyboardSimulationError(
                "ydotool not found. Please install it: sudo apt install ydotool"
            ) from None
        except Exception as e:
            logger.error("Failed to type text: %s", e, exc_info=True)
            raise KeyboardSimulationError(f"Failed to type text: {e}") from e

    async def is_available(self) -> bool:
        """Check if ydotool is available on this system.

        Returns:
            bool: True if ydotool is available
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "which",
                "ydotool",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
