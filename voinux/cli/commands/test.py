"""Test commands for verifying system components."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voinux.application.use_cases import TestAudio, TestGPU
from voinux.config.loader import ConfigLoader


@click.command()
@click.option("--duration", "-d", type=int, default=5, help="Test duration in seconds")
@click.pass_context
def test_audio(ctx: click.Context, duration: int) -> None:
    """Test audio capture from microphone."""
    console: Console = ctx.obj["console"]

    async def _test() -> None:
        console.print(Panel(f"[bold cyan]Testing Audio Capture ({duration}s)[/bold cyan]", expand=False))
        console.print()

        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Run test
        use_case = TestAudio(config)

        with console.status("[yellow]Recording audio...[/yellow]"):
            results = await use_case.execute(duration_seconds=duration)

        # Display results
        if results["success"]:
            console.print("[green]✓ Audio capture successful![/green]")
            console.print()

            table = Table(show_header=False, box=None)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Chunks Received", str(results["chunks_received"]))
            table.add_row("Total Samples", str(results["total_samples"]))
            table.add_row("Sample Rate", f"{results['sample_rate']} Hz")
            table.add_row("Duration", f"{results['duration_seconds']}s")

            console.print(table)
        else:
            console.print("[red]✗ Audio capture failed[/red]")

    asyncio.run(_test())


@click.command()
@click.pass_context
def test_gpu(ctx: click.Context) -> None:
    """Test GPU availability and configuration."""
    console: Console = ctx.obj["console"]

    async def _test() -> None:
        console.print(Panel("[bold cyan]Testing GPU Configuration[/bold cyan]", expand=False))
        console.print()

        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Run test
        use_case = TestGPU(config)
        results = await use_case.execute()

        # Display results
        if results["cuda_available"]:
            console.print("[green]✓ CUDA is available![/green]")
            console.print()

            for device in results["devices"]:
                console.print(f"[bold]GPU {device['index']}:[/bold] {device['name']}")
                console.print(f"  Memory: {device['total_memory_gb']:.2f} GB")
                console.print()
        else:
            console.print("[yellow]✗ CUDA not available[/yellow]")
            console.print("Running in CPU mode (slower performance)")

    asyncio.run(_test())


@click.command()
@click.pass_context
def test_keyboard(ctx: click.Context) -> None:
    """Test keyboard simulation."""
    console: Console = ctx.obj["console"]

    async def _test() -> None:
        console.print(Panel("[bold cyan]Testing Keyboard Simulation[/bold cyan]", expand=False))
        console.print()

        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Create keyboard adapter
        from voinux.application.factories import create_keyboard_simulator

        try:
            keyboard = await create_keyboard_simulator(config)
            console.print(f"[green]✓ Keyboard backend initialized: {type(keyboard).__name__}[/green]")
            console.print()

            console.print("Testing keyboard output in 3 seconds...")
            await asyncio.sleep(3)

            console.print("Typing test message...")
            await keyboard.type_text("Hello from Voinux!")

            console.print()
            console.print("[green]✓ Keyboard test successful![/green]")

        except Exception as e:
            console.print(f"[red]✗ Keyboard test failed: {e}[/red]")

    asyncio.run(_test())
