"""Privacy notice and consent management for cloud providers."""

import click


def show_cloud_privacy_notice(provider: str) -> bool:
    """Show privacy notice for cloud providers and get user consent.

    Args:
        provider: Provider name (e.g., "gemini")

    Returns:
        bool: True if user accepts, False if declined
    """
    # Clear screen and show prominent warning
    click.clear()
    click.secho("=" * 80, fg="yellow", bold=True)
    click.secho("  PRIVACY NOTICE: CLOUD PROVIDER", fg="yellow", bold=True)
    click.secho("=" * 80, fg="yellow", bold=True)
    click.echo()

    # Provider-specific messaging
    if provider == "gemini":
        click.echo("You are about to use Google Gemini Flash 2.5 for speech recognition.")
        click.echo()
        click.secho(
            "IMPORTANT: This is NOT offline. Your audio data will be sent to Google.",
            fg="red",
            bold=True,
        )
        click.echo()

        click.echo("What this means:")
        click.echo("  • Your voice audio will be transmitted over the internet")
        click.echo("  • Audio is processed on Google's servers (not your device)")
        click.echo("  • Google may use data to improve their services (per their privacy policy)")
        click.echo("  • Network latency: 1-3 seconds (vs. <1s offline)")
        click.echo("  • Cost: ~$0.002/minute (~$10-15/month typical usage)")
        click.echo()

        click.echo("Why use cloud over offline Whisper?")
        click.echo("  ✓ AI-powered grammar correction")
        click.echo("  ✓ Better accuracy for accents and technical speech")
        click.echo("  ✓ Advanced natural language understanding")
        click.echo()

        click.echo("Privacy considerations:")
        click.echo("  • Google Privacy Policy: https://policies.google.com/privacy")
        click.echo("  • Gemini API Terms: https://ai.google.dev/gemini-api/terms")
        click.echo("  • You are responsible for API costs")
        click.echo()

    click.secho(
        "Voinux's default is 100% offline. Cloud providers require your explicit consent.",
        fg="cyan",
    )
    click.echo()
    click.secho("=" * 80, fg="yellow", bold=True)
    click.echo()

    # Get user consent (default: No)
    consent = click.confirm(
        "Do you understand and accept these privacy/cost trade-offs?",
        default=False,
    )

    if not consent:
        click.echo()
        click.secho("Cloud provider declined. Falling back to offline Whisper.", fg="green")
        return False

    # Remind user to persist the setting
    click.echo()
    click.secho("Cloud provider accepted for this session.", fg="green")
    click.echo()
    click.echo("To avoid this notice in future, set in config:")
    click.echo(f"  {provider}:")
    click.echo("    privacy_acknowledged: true")
    click.echo()

    return True


def get_provider_display_name(provider: str) -> str:
    """Get user-friendly display name for provider.

    Args:
        provider: Provider name (e.g., "gemini")

    Returns:
        str: Display name (e.g., "Google Gemini Flash 2.5")
    """
    display_names = {
        "gemini": "Google Gemini Flash 2.5",
        "whisper": "Whisper (Offline)",
    }
    return display_names.get(provider, provider.title())


def show_cost_warning(
    current_cost_usd: float,
    warn_threshold_usd: float,
    max_limit_usd: float,
) -> None:
    """Show cost warning when threshold is exceeded.

    Args:
        current_cost_usd: Current estimated cost in USD
        warn_threshold_usd: Warning threshold in USD
        max_limit_usd: Maximum cost limit in USD
    """
    click.echo()
    click.secho("⚠ COST WARNING", fg="yellow", bold=True)
    click.echo(f"Current estimated cost: ${current_cost_usd:.2f}")
    click.echo(f"Warning threshold: ${warn_threshold_usd:.2f}")
    click.echo(f"Maximum limit: ${max_limit_usd:.2f}")
    click.echo()

    if current_cost_usd >= max_limit_usd:
        click.secho("Maximum cost limit reached! Stopping transcription.", fg="red", bold=True)
        click.echo("Update config to increase limit if needed:")
        click.echo("  gemini:")
        click.echo(f"    max_monthly_cost_usd: {max_limit_usd + 10.0:.2f}")
    else:
        remaining_usd = max_limit_usd - current_cost_usd
        click.secho(
            f"Approaching cost limit. ${remaining_usd:.2f} remaining before shutdown.", fg="yellow"
        )
    click.echo()


def show_provider_indicator(provider: str, is_online: bool = True) -> None:
    """Show indicator for current provider in CLI output.

    Args:
        provider: Provider name (e.g., "gemini", "whisper")
        is_online: Whether provider is online (True) or offline (False)
    """
    status = "ONLINE" if is_online else "OFFLINE"
    display_name = get_provider_display_name(provider)

    if provider == "whisper":
        # Green for offline/privacy-friendly
        click.secho(f"[{status}] {display_name}", fg="green", bold=True)
    else:
        # Yellow for online/cloud
        click.secho(f"[{status}] {display_name}", fg="yellow", bold=True)
