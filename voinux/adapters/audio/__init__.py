"""Audio capture and processing adapters."""

from voinux.adapters.audio.composite_processor import CompositeAudioProcessor
from voinux.adapters.audio.silence_trimmer import SilenceTrimmer
from voinux.adapters.audio.soundcard_adapter import SoundCardAudioCapture

__all__ = [
    "CompositeAudioProcessor",
    "SilenceTrimmer",
    "SoundCardAudioCapture",
]
