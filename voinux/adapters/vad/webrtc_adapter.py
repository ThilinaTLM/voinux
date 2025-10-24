"""WebRTC VAD adapter for voice activation detection."""

import asyncio
from typing import Optional

import numpy as np
import webrtcvad

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import VADError
from voinux.domain.ports import IVoiceActivationDetector


class WebRTCVAD(IVoiceActivationDetector):
    """Adapter using WebRTC VAD for voice activation detection."""

    # WebRTC VAD only supports specific sample rates
    SUPPORTED_SAMPLE_RATES = [8000, 16000, 32000, 48000]

    # WebRTC VAD requires specific frame sizes (10, 20, or 30 ms)
    FRAME_DURATION_MS = 30

    def __init__(self) -> None:
        """Initialize the WebRTC VAD adapter."""
        self.vad: Optional[webrtcvad.Vad] = None
        self.sample_rate: int = 16000
        self.frame_size: int = 0
        self.aggressiveness: int = 2

    async def initialize(self, threshold: float, sample_rate: int) -> None:
        """Initialize the VAD with given parameters.

        Args:
            threshold: Detection threshold (0.0 to 1.0, mapped to aggressiveness)
            sample_rate: Audio sample rate in Hz

        Raises:
            VADError: If initialization fails
        """
        try:
            # Map threshold to WebRTC VAD aggressiveness (0-3)
            self.aggressiveness = self._threshold_to_aggressiveness(threshold)

            # Validate sample rate
            if sample_rate not in self.SUPPORTED_SAMPLE_RATES:
                # Find nearest supported sample rate
                sample_rate = min(self.SUPPORTED_SAMPLE_RATES, key=lambda x: abs(x - sample_rate))

            self.sample_rate = sample_rate

            # Calculate frame size in samples
            # Frame size = (sample_rate * frame_duration_ms) / 1000
            self.frame_size = (sample_rate * self.FRAME_DURATION_MS) // 1000

            # Create VAD instance
            self.vad = webrtcvad.Vad(mode=self.aggressiveness)

        except Exception as e:
            raise VADError(f"Failed to initialize WebRTC VAD: {e}") from e

    async def is_speech(self, audio_chunk: AudioChunk) -> bool:
        """Determine if an audio chunk contains speech.

        Args:
            audio_chunk: Audio data to analyze

        Returns:
            bool: True if speech is detected, False otherwise

        Raises:
            VADError: If detection fails
        """
        if self.vad is None:
            raise VADError("VAD not initialized. Call initialize() first.")

        try:
            # Convert float32 audio to int16 PCM
            audio_int16 = self._float32_to_int16(audio_chunk.data)

            # Process in frames
            num_samples = len(audio_int16)
            speech_frames = 0
            total_frames = 0

            for i in range(0, num_samples - self.frame_size + 1, self.frame_size):
                frame = audio_int16[i : i + self.frame_size]

                # VAD requires bytes
                frame_bytes = frame.tobytes()

                # Run VAD on frame
                # Run in thread pool since webrtcvad is synchronous
                loop = asyncio.get_event_loop()
                is_speech_frame = await loop.run_in_executor(
                    None,
                    self.vad.is_speech,
                    frame_bytes,
                    self.sample_rate,
                )

                if is_speech_frame:
                    speech_frames += 1
                total_frames += 1

            # Consider speech if majority of frames contain speech
            if total_frames == 0:
                return False

            speech_ratio = speech_frames / total_frames
            return speech_ratio > 0.5

        except Exception as e:
            raise VADError(f"Failed to detect speech: {e}") from e

    async def shutdown(self) -> None:
        """Shut down the VAD and release resources."""
        self.vad = None

    def _threshold_to_aggressiveness(self, threshold: float) -> int:
        """Map threshold (0.0-1.0) to WebRTC VAD aggressiveness (0-3).

        Args:
            threshold: Threshold value (0.0-1.0)

        Returns:
            int: Aggressiveness level (0-3)
        """
        if threshold <= 0.25:
            return 0
        elif threshold <= 0.5:
            return 1
        elif threshold <= 0.75:
            return 2
        else:
            return 3

    def _float32_to_int16(self, audio: np.ndarray) -> np.ndarray:
        """Convert float32 audio to int16 PCM.

        Args:
            audio: Audio samples as float32 (-1.0 to 1.0)

        Returns:
            np.ndarray: Audio samples as int16
        """
        # Clip to [-1.0, 1.0]
        audio = np.clip(audio, -1.0, 1.0)

        # Convert to int16 range
        audio_int16 = (audio * 32767).astype(np.int16)

        return audio_int16
