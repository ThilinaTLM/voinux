"""Factories for creating adapters with dependency injection."""

import os

from voinux.adapters.audio.composite_processor import CompositeAudioProcessor
from voinux.adapters.audio.silence_trimmer import SilenceTrimmer
from voinux.adapters.audio.soundcard_adapter import SoundCardAudioCapture
from voinux.adapters.keyboard.stdout_adapter import StdoutKeyboard
from voinux.adapters.keyboard.xdotool_adapter import XDotoolKeyboard
from voinux.adapters.keyboard.ydotool_adapter import YDotoolKeyboard
from voinux.adapters.models.model_cache import ModelCache
from voinux.adapters.noise.noisereduce_adapter import NoiseReduceProcessor
from voinux.adapters.stt.whisper_adapter import WhisperRecognizer
from voinux.adapters.vad.webrtc_adapter import WebRTCVAD
from voinux.config.config import Config
from voinux.domain.ports import (
    IAudioCapture,
    IAudioProcessor,
    IKeyboardSimulator,
    IModelManager,
    ISpeechRecognizer,
    IVoiceActivationDetector,
)


async def create_audio_capture(config: Config) -> IAudioCapture:
    """Create an audio capture adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        IAudioCapture: Audio capture adapter
    """
    # For now, only soundcard is implemented
    # Future: Add PyAudio fallback
    return SoundCardAudioCapture(
        sample_rate=config.audio.sample_rate,
        chunk_duration_ms=config.audio.chunk_duration_ms,
        device_index=config.audio.device_index,
    )


async def create_vad(config: Config) -> IVoiceActivationDetector:
    """Create a VAD adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        IVoiceActivationDetector: VAD adapter
    """
    vad = WebRTCVAD()
    await vad.initialize(
        threshold=config.vad.threshold,
        sample_rate=config.audio.sample_rate,
    )
    return vad


async def create_audio_processor(
    config: Config, enable_silence_trimming: bool = False, provider: str = "whisper"
) -> IAudioProcessor | None:
    """Create an audio processor (noise suppressor and/or silence trimmer).

    Args:
        config: Application configuration
        enable_silence_trimming: Whether to enable silence trimming
        provider: Provider name (for determining default silence trimming behavior)

    Returns:
        IAudioProcessor | None: Audio processor adapter, or None if all disabled
    """
    processors: list[IAudioProcessor] = []

    # Add noise suppressor if enabled
    if config.noise_suppression.enabled:
        noise_processor = NoiseReduceProcessor(
            stationary=config.noise_suppression.stationary,
            prop_decrease=config.noise_suppression.prop_decrease,
            freq_mask_smooth_hz=config.noise_suppression.freq_mask_smooth_hz,
            time_mask_smooth_ms=config.noise_suppression.time_mask_smooth_ms,
        )
        await noise_processor.initialize(sample_rate=config.audio.sample_rate)
        processors.append(noise_processor)

    # Add silence trimmer if enabled (default: True for cloud providers, False for Whisper)
    should_trim = enable_silence_trimming or (provider != "whisper")
    if should_trim:
        silence_trimmer = SilenceTrimmer(
            threshold_db=-40.0,  # Default threshold
            min_audio_duration_ms=100,  # Minimum 100ms preserved
        )
        await silence_trimmer.initialize(sample_rate=config.audio.sample_rate)
        processors.append(silence_trimmer)

    # Return None if no processors
    if not processors:
        return None

    # Return single processor directly, or wrap multiple in composite
    if len(processors) == 1:
        return processors[0]

    return CompositeAudioProcessor(processors)


async def create_noise_suppressor(config: Config) -> IAudioProcessor | None:
    """Create a noise suppression adapter based on configuration.

    DEPRECATED: Use create_audio_processor instead. Kept for backward compatibility.

    Args:
        config: Application configuration

    Returns:
        IAudioProcessor | None: Noise suppressor adapter, or None if disabled
    """
    return await create_audio_processor(config, enable_silence_trimming=False, provider="whisper")


async def create_speech_recognizer(
    config: Config, provider: str | None = None, api_key_override: str | None = None
) -> ISpeechRecognizer:
    """Create a speech recognizer adapter based on configuration.

    Args:
        config: Application configuration
        provider: Provider override (None to use config default, always defaults to "whisper")
        api_key_override: API key override from CLI

    Returns:
        ISpeechRecognizer: Speech recognizer adapter
    """
    import logging

    from voinux.application.api_key_manager import APIKeyManager
    from voinux.domain.entities import ModelConfig

    logger = logging.getLogger(__name__)

    # Determine provider (default to whisper for offline-first)
    provider_name = provider or "whisper"

    # Offline provider (Whisper)
    if provider_name == "whisper":
        logger.info("Using Whisper (offline) speech recognizer")
        recognizer = WhisperRecognizer()

        model_config = ModelConfig(
            model_name=config.faster_whisper.model,
            device=config.faster_whisper.device,
            compute_type=config.faster_whisper.compute_type,
            beam_size=config.faster_whisper.beam_size,
            language=config.faster_whisper.language,
            vad_filter=False,  # We handle VAD ourselves
            model_path=config.faster_whisper.model_path,
            provider="whisper",
        )

        await recognizer.initialize(model_config)
        return recognizer

    # Cloud provider (Gemini)
    if provider_name == "gemini":
        logger.info("Using Gemini (cloud) speech recognizer")

        from voinux.adapters.stt.gemini_adapter import GeminiRecognizer

        # Get API key with precedence: CLI > Env > Config
        api_key = APIKeyManager.get_api_key(
            provider="gemini",
            cli_api_key=api_key_override,
            config_api_key=config.gemini.api_key,
        )

        # Validate API key
        api_key = APIKeyManager.validate_api_key(api_key, "gemini")

        recognizer_gemini = GeminiRecognizer()

        model_config_gemini = ModelConfig(
            model_name=config.faster_whisper.model,  # Not used for Gemini but required
            device="auto",  # Not applicable for cloud
            compute_type="float32",  # Not applicable for cloud
            beam_size=1,  # Not applicable for cloud
            language=config.faster_whisper.language,
            vad_filter=False,
            model_path=None,
            provider="gemini",
            api_key=api_key,
            api_endpoint=config.gemini.api_endpoint,
            enable_grammar_correction=config.gemini.enable_grammar_correction,
        )

        await recognizer_gemini.initialize(model_config_gemini)
        return recognizer_gemini

    # Unknown provider - fallback to Whisper with warning
    logger.warning(f"Unknown provider: {provider_name}, falling back to Whisper (offline)")
    return await create_speech_recognizer(config, provider="whisper")


async def create_keyboard_simulator(config: Config) -> IKeyboardSimulator:
    """Create a keyboard simulator adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        IKeyboardSimulator: Keyboard simulator adapter
    """
    backend = config.keyboard.backend

    if backend == "auto":
        # Auto-detect based on display server
        return await _auto_detect_keyboard(config)
    if backend == "xdotool":
        keyboard: IKeyboardSimulator = XDotoolKeyboard(
            typing_delay_ms=config.keyboard.typing_delay_ms,
            add_space_after=config.keyboard.add_space_after,
        )
        if not await keyboard.is_available():
            raise RuntimeError("xdotool not available")
        return keyboard
    if backend == "ydotool":
        keyboard_ydotool: IKeyboardSimulator = YDotoolKeyboard(
            typing_delay_ms=config.keyboard.typing_delay_ms,
            add_space_after=config.keyboard.add_space_after,
        )
        if not await keyboard_ydotool.is_available():
            raise RuntimeError("ydotool not available")
        return keyboard_ydotool
    if backend == "stdout":
        return StdoutKeyboard(add_space_after=config.keyboard.add_space_after)
    raise ValueError(f"Unknown keyboard backend: {backend}")


async def _auto_detect_keyboard(config: Config) -> IKeyboardSimulator:
    """Auto-detect the best keyboard backend.

    Args:
        config: Application configuration

    Returns:
        IKeyboardSimulator: Best available keyboard adapter
    """
    # Detect display server
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")

    # Try Wayland first if detected
    if session_type == "wayland" or wayland_display:
        ydotool = YDotoolKeyboard(
            typing_delay_ms=config.keyboard.typing_delay_ms,
            add_space_after=config.keyboard.add_space_after,
        )
        if await ydotool.is_available():
            return ydotool

    # Try X11
    xdotool = XDotoolKeyboard(
        typing_delay_ms=config.keyboard.typing_delay_ms,
        add_space_after=config.keyboard.add_space_after,
    )
    if await xdotool.is_available():
        return xdotool

    # Fallback to stdout for testing
    return StdoutKeyboard(add_space_after=config.keyboard.add_space_after)


def create_model_manager(config: Config) -> IModelManager:
    """Create a model manager adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        IModelManager: Model manager adapter
    """
    return ModelCache(cache_dir=config.system.cache_dir)
