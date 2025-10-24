"""Noise reduction adapter using the noisereduce library."""

import asyncio
import logging
from datetime import datetime

import noisereduce as nr
import numpy as np

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError
from voinux.domain.ports import IAudioProcessor

logger = logging.getLogger(__name__)


class NoiseReduceProcessor(IAudioProcessor):
    """Adapter using noisereduce library for noise suppression.

    Uses spectral gating to remove stationary and non-stationary noise from audio signals.
    Particularly effective for:
    - Keyboard clicks and typing sounds
    - Computer fan noise
    - HVAC/air conditioning hums
    - Background office noise
    - Constant environmental noise
    """

    def __init__(
        self,
        stationary: bool = True,
        prop_decrease: float = 1.0,
        freq_mask_smooth_hz: int = 500,
        time_mask_smooth_ms: int = 50,
    ) -> None:
        """Initialize the noise reduction processor.

        Args:
            stationary: Use stationary noise reduction (good for constant noise like fans)
            prop_decrease: Proportion to reduce noise (0.0-1.0, 1.0 = maximum reduction)
            freq_mask_smooth_hz: Frequency mask smoothing in Hz
            time_mask_smooth_ms: Time mask smoothing in milliseconds
        """
        self.stationary = stationary
        self.prop_decrease = prop_decrease
        self.freq_mask_smooth_hz = freq_mask_smooth_hz
        self.time_mask_smooth_ms = time_mask_smooth_ms
        self.sample_rate: int = 16000
        self._initialized = False

    async def initialize(self, sample_rate: int) -> None:
        """Initialize the noise suppressor with the given sample rate.

        Args:
            sample_rate: Audio sample rate in Hz

        Raises:
            NoiseSuppressionError: If initialization fails
        """
        try:
            self.sample_rate = sample_rate
            self._initialized = True

            logger.info(
                "Noise suppressor initialized (sample_rate=%d, stationary=%s, "
                "prop_decrease=%.2f, freq_smooth=%dHz, time_smooth=%dms)",
                sample_rate,
                self.stationary,
                self.prop_decrease,
                self.freq_mask_smooth_hz,
                self.time_mask_smooth_ms,
            )
        except Exception as e:
            logger.error("Failed to initialize noise suppressor: %s", e, exc_info=True)
            raise NoiseSuppressionError(f"Failed to initialize noise suppressor: {e}") from e

    async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
        """Process an audio chunk to remove noise.

        Args:
            audio_chunk: Audio data to process

        Returns:
            AudioChunk: Processed audio with noise reduced

        Raises:
            NoiseSuppressionError: If processing fails
        """
        if not self._initialized:
            raise NoiseSuppressionError("Processor not initialized. Call initialize() first.")

        try:
            # Run noise reduction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            reduced_audio = await loop.run_in_executor(
                None,
                self._reduce_noise,
                audio_chunk.data,
            )

            # Create new audio chunk with reduced noise
            return AudioChunk(
                data=reduced_audio,
                sample_rate=audio_chunk.sample_rate,
                timestamp=datetime.now(),
                duration_ms=audio_chunk.duration_ms,
            )

        except Exception as e:
            logger.error("Noise suppression failed: %s", e, exc_info=True)
            raise NoiseSuppressionError(f"Noise suppression failed: {e}") from e

    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Reduce noise in audio data (synchronous method for thread pool).

        Args:
            audio_data: Input audio samples as float32

        Returns:
            np.ndarray: Noise-reduced audio samples
        """
        # Apply noise reduction
        reduced: np.ndarray = nr.reduce_noise(
            y=audio_data,
            sr=self.sample_rate,
            stationary=self.stationary,
            prop_decrease=self.prop_decrease,
            freq_mask_smooth_hz=self.freq_mask_smooth_hz,
            time_mask_smooth_ms=self.time_mask_smooth_ms,
        )

        # Ensure output is float32
        return reduced.astype(np.float32)

    async def shutdown(self) -> None:
        """Shut down the processor and release resources."""
        logger.info("Shutting down noise suppressor")
        self._initialized = False
        logger.debug("Noise suppressor shutdown complete")
