"""Main CLI entry point for Voinux."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from voinux.config.loader import ConfigLoader

# Create console for rich output
console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="voinux")
@click.option(
    "--config-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.pass_context
def cli(ctx: click.Context, config_file: Optional[Path], verbose: bool, quiet: bool) -> None:
    """Voinux - Privacy-focused voice typing for Linux.

    Real-time voice-to-text transcription using local GPU-accelerated Whisper models.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["config_file"] = config_file
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["console"] = console


def run_async(coro):
    """Helper to run async functions in Click commands."""
    return asyncio.run(coro)


# Import and register commands
from voinux.cli.commands.config import config_group
from voinux.cli.commands.model import model_group
from voinux.cli.commands.start import start
from voinux.cli.commands.test import test_audio, test_gpu, test_keyboard

cli.add_command(start)
cli.add_command(config_group)
cli.add_command(model_group)
cli.add_command(test_audio)
cli.add_command(test_gpu)
cli.add_command(test_keyboard)


if __name__ == "__main__":
    cli()
