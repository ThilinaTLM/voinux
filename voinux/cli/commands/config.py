"""Config commands for managing configuration."""

import asyncio
from typing import Any

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
@click.option(
    "--skip-interactive", is_flag=True, help="Skip interactive prompts, create empty config"
)
@click.pass_context
def config_init(ctx: click.Context, force: bool, skip_interactive: bool) -> None:
    """Initialize configuration file interactively.

    This will guide you through setting up common configuration options.
    Only your custom settings will be saved to the config file.
    """
    console: Console = ctx.obj["console"]

    async def _init() -> None:
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        if await loader.exists() and not force:
            console.print(
                "[yellow]Configuration file already exists. Use --force to overwrite.[/yellow]"
            )
            return

        # Create minimal config file first
        await loader.repo.create_default_config()
        console.print(f"[green]✓ Configuration file created: {loader.config_file}[/green]")

        if skip_interactive:
            console.print(
                "[cyan]Empty configuration created. Use 'voinux config set' to add settings.[/cyan]"
            )
            return

        # Interactive configuration
        console.print()
        console.print("[bold cyan]Interactive Configuration Setup[/bold cyan]")
        console.print("Press Enter to accept defaults (shown in brackets)\n")

        config_updates: dict[str, dict[str, Any]] = {}

        # Model selection
        console.print("[bold]Whisper Model Size[/bold]")
        console.print("  tiny      - Fastest, least accurate (~1GB VRAM)")
        console.print("  base      - Fast, good accuracy (~1GB VRAM) [default]")
        console.print("  small     - Balanced (~2GB VRAM)")
        console.print("  medium    - High accuracy (~5GB VRAM)")
        console.print("  large-v3  - Best accuracy (~10GB VRAM)")
        model = click.prompt(
            "Select model",
            type=click.Choice(["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"]),
            default="base",
            show_default=True,
        )
        if model != "base":
            config_updates.setdefault("faster_whisper", {})["model"] = model

        # Device selection
        console.print()
        console.print("[bold]Device Selection[/bold]")
        device = click.prompt(
            "Select device",
            type=click.Choice(["auto", "cuda", "cpu"]),
            default="auto",
            show_default=True,
        )
        if device != "auto":
            config_updates.setdefault("faster_whisper", {})["device"] = device

        # Language
        console.print()
        console.print("[bold]Language[/bold]")
        console.print("  auto - Detect language automatically [default]")
        console.print("  en   - English")
        console.print("  es   - Spanish")
        console.print("  fr   - French")
        console.print("  de   - German")
        console.print("  ... and many more")
        language = click.prompt(
            "Language code (or 'auto')",
            type=str,
            default="auto",
            show_default=True,
        )
        if language != "auto":
            config_updates.setdefault("faster_whisper", {})["language"] = language

        # VAD
        console.print()
        console.print("[bold]Voice Activation Detection (VAD)[/bold]")
        console.print("VAD filters out silence to save GPU processing")
        vad_enabled = click.confirm("Enable VAD?", default=True)
        if not vad_enabled:
            config_updates.setdefault("vad", {})["enabled"] = False

        # Save configuration
        if config_updates:
            console.print()
            console.print("[yellow]Saving your custom configuration...[/yellow]")
            await loader.repo.save(config_updates)
            console.print("[green]✓ Configuration saved![/green]")
        else:
            console.print()
            console.print("[cyan]No custom settings (all defaults selected)[/cyan]")

        # Show summary
        console.print()
        console.print("[bold]Configuration Summary:[/bold]")
        console.print(f"  Model: {model}")
        console.print(f"  Device: {device}")
        console.print(f"  Language: {language}")
        console.print(f"  VAD: {'enabled' if vad_enabled else 'disabled'}")
        console.print()
        console.print("You can change these settings anytime with:")
        console.print("  voinux config set <key> <value>")
        console.print("  voinux config list")

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


@config_group.command(name="set")
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.

    KEY: Configuration key in dot notation (e.g., faster_whisper.model)

    VALUE: Value to set (will be coerced to appropriate type)

    Examples:
      voinux config set faster_whisper.model large-v3
      voinux config set vad.enabled false
      voinux config set audio.sample_rate 16000
    """
    console: Console = ctx.obj["console"]

    async def _set() -> None:
        from voinux.config.utils import set_config_value, validate_config_key

        # Validate key
        if not validate_config_key(key):
            console.print(f"[red]Error: Invalid config key: '{key}'[/red]")
            console.print()
            console.print("Run 'voinux config list' to see all available keys")
            raise click.Abort()

        # Load existing config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        # Check if config exists, if not create it
        if not await loader.exists():
            console.print("[yellow]Config file doesn't exist, creating...[/yellow]")
            await loader.create_default()

        # Load current config
        config = await loader.load()

        # Create a dict for the update
        update_dict: dict[str, Any] = {}
        try:
            set_config_value(update_dict, key, value)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort() from e

        # Merge with existing config and save
        merged = loader._merge_config(config, update_dict)
        merged.validate()  # Ensure the new config is valid
        await loader.save(merged, minimal=True)

        console.print(f"[green]✓ Configuration updated: {key} = {value}[/green]")

    asyncio.run(_set())


@config_group.command(name="get")
@click.argument("key", type=str)
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """Get a configuration value.

    KEY: Configuration key in dot notation (e.g., faster_whisper.model)

    Examples:
      voinux config get faster_whisper.model
      voinux config get vad.enabled
    """
    console: Console = ctx.obj["console"]

    async def _get() -> None:
        from voinux.config.utils import get_config_value, validate_config_key

        # Validate key
        if not validate_config_key(key):
            console.print(f"[red]Error: Invalid config key: '{key}'[/red]")
            console.print()
            console.print("Run 'voinux config list' to see all available keys")
            raise click.Abort()

        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()

        # Get value
        try:
            value = get_config_value(config, key)
            console.print(f"{key}: [cyan]{value}[/cyan]")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort() from e

    asyncio.run(_get())


@config_group.command(name="unset")
@click.argument("key", type=str)
@click.pass_context
def config_unset(ctx: click.Context, key: str) -> None:
    """Remove a configuration value (revert to default).

    KEY: Configuration key in dot notation (e.g., faster_whisper.model)

    Examples:
      voinux config unset faster_whisper.model
      voinux config unset vad.enabled
    """
    console: Console = ctx.obj["console"]

    async def _unset() -> None:
        from voinux.config.utils import parse_config_key, validate_config_key

        # Validate key
        if not validate_config_key(key):
            console.print(f"[red]Error: Invalid config key: '{key}'[/red]")
            console.print()
            console.print("Run 'voinux config list' to see all available keys")
            raise click.Abort()

        # Load config file (raw dict)
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        if not await loader.exists():
            console.print("[yellow]Config file doesn't exist, nothing to unset[/yellow]")
            return

        # Load raw config dict from file
        config_dict = await loader.repo.load()

        # Parse key
        section, field = parse_config_key(key)

        # Remove the key
        if section in config_dict and field in config_dict[section]:
            del config_dict[section][field]
            # Remove empty sections
            if not config_dict[section]:
                del config_dict[section]

            # Save updated config
            await loader.repo.save(config_dict)
            console.print(f"[green]✓ Removed config key: {key} (reverted to default)[/green]")
        else:
            console.print(
                f"[yellow]Key '{key}' not found in config file (already using default)[/yellow]"
            )

    asyncio.run(_unset())


@config_group.command(name="list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all keys including defaults")
@click.pass_context
def config_list(ctx: click.Context, show_all: bool) -> None:
    """List configuration keys and their values.

    By default, shows only non-default values from the config file.
    Use --all to show all available configuration keys.
    """
    console: Console = ctx.obj["console"]

    async def _list() -> None:
        from voinux.config.utils import get_all_config_keys, get_config_value

        # Load config
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)
        config = await loader.load()
        defaults = loader._dict_to_config({})  # Config with all defaults

        # Get all keys
        all_keys = get_all_config_keys()

        # Group by section
        from collections import defaultdict

        sections: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

        for key in all_keys:
            section = key.split(".")[0]
            value = get_config_value(config, key)
            default_value = get_config_value(defaults, key)

            # Determine source
            if value != default_value:
                source = "[file]" if show_all else ""
            else:
                if not show_all:
                    continue  # Skip default values unless --all
                source = "[default]"

            # Format value
            if value is None:
                value_str = "null"
            elif isinstance(value, bool):
                value_str = str(value).lower()
            else:
                value_str = str(value)

            sections[section].append((key, value_str, source))

        # Display
        if not sections:
            console.print("[yellow]No custom configuration set (all defaults)[/yellow]")
            console.print("Use 'voinux config list --all' to see all available keys")
            return

        for section in sorted(sections.keys()):
            console.print(f"\n[bold]{section}:[/bold]")
            for key, value, source in sections[section]:
                field = key.split(".", 1)[1]
                if source:
                    console.print(f"  {field}: [cyan]{value}[/cyan] [dim]{source}[/dim]")
                else:
                    console.print(f"  {field}: [cyan]{value}[/cyan]")

    asyncio.run(_list())


@config_group.command(name="reset")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def config_reset(ctx: click.Context, force: bool) -> None:
    """Reset configuration to defaults.

    This will delete the configuration file, reverting all settings to defaults.
    """
    console: Console = ctx.obj["console"]

    async def _reset() -> None:
        config_file = ctx.obj.get("config_file")
        loader = ConfigLoader(config_file=config_file)

        if not await loader.exists():
            console.print("[yellow]Config file doesn't exist, nothing to reset[/yellow]")
            return

        # Confirmation
        if not force:
            console.print(
                "[yellow]This will delete your configuration file and reset all settings to defaults.[/yellow]"
            )
            if not click.confirm("Are you sure you want to continue?"):
                console.print("[yellow]Reset cancelled[/yellow]")
                return

        # Delete config file
        loader.config_file.unlink()
        console.print("[green]✓ Configuration reset to defaults[/green]")
        console.print(f"Config file removed: {loader.config_file}")

    asyncio.run(_reset())


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
