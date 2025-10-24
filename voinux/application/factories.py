"""Factories for creating adapters with dependency injection."""

import os

from voinux.adapters.audio.soundcard_adapter import SoundCardAudioCapture
from voinux.adapters.keyboard.stdout_adapter import StdoutKeyboard
from voinux.adapters.keyboard.xdotool_adapter import XDotoolKeyboard
from voinux.adapters.keyboard.ydotool_adapter import YDotoolKeyboard
from voinux.adapters.models.model_cache import ModelCache
from voinux.adapters.stt.whisper_adapter import WhisperRecognizer
from voinux.adapters.vad.webrtc_adapter import WebRTCVAD
from voinux.config.config import Config
from voinux.domain.ports import (
    IAudioCapture,
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


async def create_speech_recognizer(config: Config) -> ISpeechRecognizer:
    """Create a speech recognizer adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        ISpeechRecognizer: Speech recognizer adapter
    """
    from voinux.domain.entities import ModelConfig

    recognizer = WhisperRecognizer()

    model_config = ModelConfig(
        model_name=config.faster_whisper.model,
        device=config.faster_whisper.device,
        compute_type=config.faster_whisper.compute_type,
        beam_size=config.faster_whisper.beam_size,
        language=config.faster_whisper.language,
        vad_filter=False,  # We handle VAD ourselves
        model_path=config.faster_whisper.model_path,
    )

    await recognizer.initialize(model_config)
    return recognizer


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
