"""Config commands for managing configuration."""

import asyncio

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from voinux.config.loader import ConfigLoader


@click.group(name="config")
def config_group() -> None:
    """Manage Voinux configuration."""
    pass


@config_group.command(name="show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration."""
    console: Console = ctx.obj["console"]

    async def _show() -> None:
        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Convert to dict for display
        from voinux.config.loader import ConfigLoader as CL
        config_dict = CL(config_file)._config_to_dict(config)

        # Display as YAML
        yaml_str = yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False)
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)

        console.print(Panel("[bold cyan]Current Configuration[/bold cyan]", expand=False))
        console.print()
        console.print(syntax)

    asyncio.run(_show())


@config_group.command(name="init")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.pass_context
def config_init(ctx: click.Context, force: bool) -> None:
    """Initialize configuration file with defaults."""
    console: Console = ctx.obj["console"]

    async def _init() -> None:
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        if await loader.exists() and not force:
            console.print("[yellow]Configuration file already exists. Use --force to overwrite.[/yellow]")
            return

        await loader.repo.create_default_config()
        console.print(f"[green]✓ Configuration file created: {loader.config_file}[/green]")

    asyncio.run(_init())


@config_group.command(name="path")
@click.pass_context
def config_path(ctx: click.Context) -> None:
    """Show path to configuration file."""
    console: Console = ctx.obj["console"]

    config_file = ctx.obj.get("config_file")
    loader = ConfigLoader(config_file=config_file)

    console.print(f"Configuration file: {loader.config_file}")

    async def _check() -> None:
        exists = await loader.exists()
        if exists:
            console.print("[green]✓ File exists[/green]")
        else:
            console.print("[yellow]⚠ File does not exist (using defaults)[/yellow]")
            console.print(f"Run 'voinux config init' to create it")

    asyncio.run(_check())
