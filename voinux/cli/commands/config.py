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
        config_dict = ConfigLoader(config_file)._config_to_dict(config)

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
            console.print(
                "[yellow]Configuration file already exists. Use --force to overwrite.[/yellow]"
            )
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
            console.print("Run 'voinux config init' to create it")

    asyncio.run(_check())


@config_group.command(name="set-api-key")
@click.argument("provider", type=click.Choice(["gemini"]))
@click.argument("api_key", type=str)
@click.pass_context
def config_set_api_key(ctx: click.Context, provider: str, api_key: str) -> None:
    """Set API key for a cloud provider.

    PROVIDER: Cloud provider name (gemini)

    API_KEY: Your API key for the provider
    """
    console: Console = ctx.obj["console"]

    async def _set_key() -> None:
        # Load existing config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        # Check if config exists, if not create it
        if not await loader.exists():
            console.print("[yellow]Config file doesn't exist, creating...[/yellow]")
            await loader.create_default()

        config = await loader.load()

        # Update provider config
        if provider == "gemini":
            from voinux.config.config import GeminiConfig

            config.gemini = GeminiConfig(
                api_key=api_key,
                enable_grammar_correction=config.gemini.enable_grammar_correction,
                privacy_acknowledged=config.gemini.privacy_acknowledged,
                max_monthly_cost_usd=config.gemini.max_monthly_cost_usd,
                warn_at_cost_usd=config.gemini.warn_at_cost_usd,
                api_endpoint=config.gemini.api_endpoint,
            )

        # Save updated config
        await loader.save(config)

        # Redact API key for display
        from voinux.application.api_key_manager import APIKeyManager

        redacted_key = APIKeyManager.redact_api_key(api_key)
        console.print(f"[green]✓ API key set for {provider}: {redacted_key}[/green]")
        console.print()
        console.print(
            f"[yellow]Note: Set '{provider}.privacy_acknowledged: true' in config "
            "to skip privacy notice[/yellow]"
        )

    asyncio.run(_set_key())
