"""XDotool keyboard simulation adapter for X11."""

import asyncio
import shlex
import subprocess
from typing import Optional

from voinux.domain.exceptions import KeyboardSimulationError
from voinux.domain.ports import IKeyboardSimulator


class XDotoolKeyboard(IKeyboardSimulator):
    """Adapter using xdotool for keyboard simulation on X11."""

    def __init__(self, typing_delay_ms: int = 0, add_space_after: bool = True) -> None:
        """Initialize the xdotool keyboard adapter.

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
            return

        try:
            # Add space if configured
            if self.add_space_after and not text.endswith(" "):
                text = text + " "

            # Build xdotool command
            # Use type command with delay option
            cmd = ["xdotool", "type"]

            if self.typing_delay_ms > 0:
                cmd.extend(["--delay", str(self.typing_delay_ms)])

            cmd.append(text)

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise KeyboardSimulationError(
                    f"xdotool command failed: {error_msg}"
                )

        except FileNotFoundError:
            raise KeyboardSimulationError(
                "xdotool not found. Please install it: sudo apt install xdotool"
            )
        except Exception as e:
            raise KeyboardSimulationError(f"Failed to type text: {e}") from e

    async def is_available(self) -> bool:
        """Check if xdotool is available on this system.

        Returns:
            bool: True if xdotool is available
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "which",
                "xdotool",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
