"""Main CLI entry point for Voinux."""

# IMPORTANT: Set up CUDA library paths before any imports
# This must happen before any CUDA/CTranslate2 libraries are loaded
import os
import sys
import site
from pathlib import Path as _Path

def _setup_cuda_environment() -> None:
    """Set up CUDA library paths for CTranslate2.

    CTranslate2 may have difficulty finding NVIDIA libraries installed via pip.
    We set LD_LIBRARY_PATH and if already running, restart with updated env.
    """
    try:
        site_packages = site.getsitepackages()
        cuda_lib_paths = []

        for site_pkg in site_packages:
            site_path = _Path(site_pkg)

            # Add NVIDIA library directories
            nvidia_path = site_path / "nvidia"
            if nvidia_path.exists():
                for lib_dir in nvidia_path.iterdir():
                    if lib_dir.is_dir():
                        lib_path = lib_dir / "lib"
                        if lib_path.exists():
                            cuda_lib_paths.append(str(lib_path))

        if cuda_lib_paths:
            current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
            new_paths = [p for p in cuda_lib_paths if p not in current_ld_path]

            if new_paths:
                new_ld_path = ":".join(new_paths)
                if current_ld_path:
                    new_ld_path = new_ld_path + ":" + current_ld_path

                # Check if we need to restart with updated LD_LIBRARY_PATH
                if "LD_LIBRARY_PATH" not in os.environ or new_paths:
                    # Set the environment variable
                    os.environ["LD_LIBRARY_PATH"] = new_ld_path

                    # If this is not already a restarted process, restart with new env
                    if not os.environ.get("_VOINUX_LD_LIBRARY_PATH_SET"):
                        os.environ["_VOINUX_LD_LIBRARY_PATH_SET"] = "1"
                        # Restart the process with updated environment
                        os.execve(sys.executable, [sys.executable] + sys.argv, os.environ)
    except Exception:
        pass  # Fail silently, system CUDA libraries may still work

_setup_cuda_environment()

# Now import the rest
import asyncio
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
