"""Model commands for managing Whisper models."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voinux.application.factories import create_model_manager
from voinux.config.loader import ConfigLoader


@click.group(name="model")
def model_group() -> None:
    """Manage Whisper models."""
    pass


@model_group.command(name="list")
@click.pass_context
def model_list(ctx: click.Context) -> None:
    """List cached models."""
    console: Console = ctx.obj["console"]

    async def _list() -> None:
        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Get model manager
        model_manager = create_model_manager(config)
        models = await model_manager.list_cached_models()

        console.print(Panel("[bold cyan]Cached Whisper Models[/bold cyan]", expand=False))
        console.print()

        if not models:
            console.print("[yellow]No models cached yet.[/yellow]")
            console.print("Models will be downloaded automatically on first use.")
            console.print("Or run: voinux model download <model-name>")
        else:
            table = Table(show_header=True)
            table.add_column("Model", style="cyan")
            table.add_column("VRAM (INT8)", style="white")
            table.add_column("VRAM (FP16)", style="white")

            for model_name in models:
                vram_int8 = model_manager.get_vram_requirements(model_name, "int8")
                vram_fp16 = model_manager.get_vram_requirements(model_name, "float16")

                table.add_row(
                    model_name,
                    f"{vram_int8} MB" if vram_int8 > 0 else "N/A",
                    f"{vram_fp16} MB" if vram_fp16 > 0 else "N/A",
                )

            console.print(table)

    asyncio.run(_list())


@model_group.command(name="download")
@click.argument("model_name", type=str)
@click.option("--force", is_flag=True, help="Force re-download even if cached")
@click.pass_context
def model_download(ctx: click.Context, model_name: str, force: bool) -> None:
    """Download a Whisper model.

    MODEL_NAME: Name of the model (e.g., tiny, base, small, medium, large-v3, large-v3-turbo)
    """
    console: Console = ctx.obj["console"]

    async def _download() -> None:
        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Get model manager
        model_manager = create_model_manager(config)

        # Check if already cached
        if not force:
            model_path = await model_manager.get_model_path(model_name)
            if model_path:
                console.print(f"[green]✓ Model already cached: {model_path}[/green]")
                console.print("Use --force to re-download")
                return

        # Download model
        console.print(f"[yellow]Downloading model: {model_name}[/yellow]")
        console.print("This may take a while...")

        try:
            with console.status(f"[yellow]Downloading {model_name}...[/yellow]"):
                model_path = await model_manager.download_model(model_name, force=force)

            console.print(f"[green]✓ Model downloaded: {model_path}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Download failed: {e}[/red]")
            raise click.Abort() from e

    asyncio.run(_download())


@model_group.command(name="info")
@click.pass_context
def model_info(ctx: click.Context) -> None:
    """Show information about available models."""
    console: Console = ctx.obj["console"]

    console.print(Panel("[bold cyan]Whisper Model Information[/bold cyan]", expand=False))
    console.print()

    table = Table(show_header=True)
    table.add_column("Model", style="cyan")
    table.add_column("VRAM (INT8)", style="white")
    table.add_column("VRAM (FP16)", style="white")
    table.add_column("Speed", style="yellow")
    table.add_column("Accuracy", style="green")

    models_info = [
        ("tiny", 300, 500, "Fastest", "Lowest"),
        ("base", 500, 900, "Very Fast", "Low"),
        ("small", 1000, 1800, "Fast", "Medium"),
        ("medium", 2500, 4500, "Medium", "High"),
        ("large-v3", 5000, 8000, "Slow", "Highest"),
        ("large-v3-turbo", 4000, 6000, "Medium", "Very High"),
    ]

    for model_name, vram_int8, vram_fp16, speed, accuracy in models_info:
        table.add_row(
            model_name,
            f"{vram_int8} MB",
            f"{vram_fp16} MB",
            speed,
            accuracy,
        )

    console.print(table)
    console.print()
    console.print("[bold]Recommendations:[/bold]")
    console.print("• 4GB VRAM or less: Use [cyan]tiny[/cyan] or [cyan]base[/cyan] with INT8")
    console.print("• 6-8GB VRAM: Use [cyan]small[/cyan] or [cyan]medium[/cyan] with INT8")
    console.print("• 8GB+ VRAM: Use [cyan]large-v3-turbo[/cyan] with INT8 for best results")
