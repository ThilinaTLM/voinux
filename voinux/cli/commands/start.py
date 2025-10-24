"""Start command for beginning voice transcription."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from voinux.application.use_cases import StartTranscription
from voinux.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


@click.command()
@click.option("--model", type=str, help="Whisper model to use (tiny, base, small, medium, large-v3, large-v3-turbo)")
@click.option("--device", type=click.Choice(["cuda", "cpu", "auto"]), help="Device to use")
@click.option("--language", "-l", type=str, help="Target language code (e.g., 'en', 'es')")
@click.option("--no-vad", is_flag=True, help="Disable voice activation detection")
@click.option("--continuous", "-c", is_flag=True, help="Continuous mode (restart on errors)")
@click.option("--gui", is_flag=True, help="Launch GUI instead of CLI interface")
@click.pass_context
def start(
    ctx: click.Context,
    model: Optional[str],
    device: Optional[str],
    language: Optional[str],
    no_vad: bool,
    continuous: bool,
    gui: bool,
) -> None:
    """Start real-time voice transcription.

    Press Ctrl+C to stop transcription (CLI mode).
    Use the Stop button or system tray to stop (GUI mode).
    """
    console: Console = ctx.obj["console"]

    # If GUI mode, launch GUI and return early
    if gui:
        logger.info("Launching GUI mode")

        async def _start_gui() -> None:
            # Load configuration
            config_file = ctx.obj.get("config_file")
            loader = ConfigLoader(config_file=config_file)

            # Build CLI overrides
            cli_overrides = {}
            if model:
                cli_overrides.setdefault("faster_whisper", {})["model"] = model
            if device:
                cli_overrides.setdefault("faster_whisper", {})["device"] = device
            if language:
                cli_overrides.setdefault("faster_whisper", {})["language"] = language
            if no_vad:
                cli_overrides.setdefault("vad", {})["enabled"] = False

            config = await loader.load(cli_overrides=cli_overrides)
            return config

        # Get config
        config = asyncio.run(_start_gui())

        # Import and run GUI
        from voinux.gui.main import run_gui
        run_gui(config)
        return

    async def _start() -> None:
        logger.info("Start command invoked")

        # Load configuration
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        # Build CLI overrides
        cli_overrides = {}
        if model:
            cli_overrides.setdefault("faster_whisper", {})["model"] = model
        if device:
            cli_overrides.setdefault("faster_whisper", {})["device"] = device
        if language:
            cli_overrides.setdefault("faster_whisper", {})["language"] = language
        if no_vad:
            cli_overrides.setdefault("vad", {})["enabled"] = False

        logger.debug("Loading configuration with CLI overrides: %s", cli_overrides)
        config = await loader.load(cli_overrides=cli_overrides)

        # Display configuration
        console.print(Panel("[bold cyan]Voinux Voice Transcription[/bold cyan]", expand=False))
        console.print()

        config_table = Table(show_header=False, box=None)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        config_table.add_row("Model", config.faster_whisper.model)
        config_table.add_row("Device", config.faster_whisper.device)
        config_table.add_row("Compute Type", config.faster_whisper.compute_type)
        config_table.add_row("VAD Enabled", "Yes" if config.vad.enabled else "No")
        if config.faster_whisper.language:
            config_table.add_row("Language", config.faster_whisper.language)

        console.print(config_table)
        console.print()

        logger.info(
            "Configuration loaded (model=%s, device=%s, vad=%s, language=%s)",
            config.faster_whisper.model,
            config.faster_whisper.device,
            config.vad.enabled,
            config.faster_whisper.language or "auto",
        )

        # Create use case
        use_case = StartTranscription(config)

        # Status callback
        def on_status(status: str) -> None:
            console.print(f"[yellow]{status}[/yellow]")

        try:
            # Start transcription
            logger.info("Executing transcription use case")
            session = await use_case.execute(on_status_change=on_status)

            # Display session statistics
            console.print()
            console.print(Panel("[bold green]Session Complete[/bold green]", expand=False))

            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Statistic", style="cyan")
            stats_table.add_column("Value", style="white")
            stats_table.add_row("Duration", f"{session.duration_seconds:.1f}s")
            stats_table.add_row("Chunks Processed", str(session.total_chunks_processed))
            stats_table.add_row("Speech Chunks", str(session.total_speech_chunks))
            stats_table.add_row("Silence Chunks", str(session.total_silence_chunks))
            if session.total_speech_chunks > 0:
                stats_table.add_row(
                    "Avg Transcription Time",
                    f"{session.average_transcription_time_ms:.0f}ms"
                )
            stats_table.add_row("Characters Typed", str(session.total_characters_typed))
            if config.vad.enabled:
                stats_table.add_row(
                    "VAD Efficiency",
                    f"{session.vad_efficiency_percent:.1f}%"
                )

            console.print(stats_table)

            logger.info(
                "Session completed (duration=%.1fs, chunks=%d, utterances=%d, characters=%d)",
                session.duration_seconds,
                session.total_chunks_processed,
                session.total_utterances_processed,
                session.total_characters_typed,
            )

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            console.print("\n[yellow]Stopping transcription...[/yellow]")
            await use_case.stop()
        except Exception as e:
            logger.error("Error during transcription: %s", e, exc_info=True)
            console.print(f"\n[red]Error: {e}[/red]")
            raise click.Abort()

    asyncio.run(_start())
