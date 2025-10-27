"""Silence trimming audio processor adapter."""

import logging

import numpy as np

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError
from voinux.domain.ports import IAudioProcessor

logger = logging.getLogger(__name__)


class SilenceTrimmer(IAudioProcessor):
    """Audio processor that trims leading and trailing silence from audio chunks.

    This is particularly useful for cloud STT providers where audio duration
    directly affects API costs and data usage. Uses RMS energy-based detection
    to identify and remove silent regions at the start and end of audio.
    """

    # Frame size for energy calculation (in milliseconds)
    FRAME_SIZE_MS = 20

    def __init__(
        self,
        threshold_db: float = -40.0,
        min_audio_duration_ms: int = 100,
    ) -> None:
        """Initialize the silence trimmer.

        Args:
            threshold_db: Silence threshold in decibels (default: -40.0 dB)
            min_audio_duration_ms: Minimum audio duration to preserve (default: 100ms)
        """
        self.threshold_db = threshold_db
        self.min_audio_duration_ms = min_audio_duration_ms
        self.sample_rate: int = 16000
        self._initialized = False

    async def initialize(self, sample_rate: int) -> None:
        """Initialize the silence trimmer.

        Args:
            sample_rate: Audio sample rate in Hz

        Raises:
            NoiseSuppressionError: If initialization fails
        """
        try:
            self.sample_rate = sample_rate
            self._initialized = True

            logger.info(
                "Initialized SilenceTrimmer (threshold=%.1f dB, min_duration=%dms, sample_rate=%d)",
                self.threshold_db,
                self.min_audio_duration_ms,
                self.sample_rate,
            )

        except Exception as e:
            logger.error("Failed to initialize SilenceTrimmer: %s", e, exc_info=True)
            raise NoiseSuppressionError(f"Failed to initialize SilenceTrimmer: {e}") from e

    async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
        """Trim leading and trailing silence from an audio chunk.

        Args:
            audio_chunk: Audio chunk to process

        Returns:
            AudioChunk: Audio chunk with silence trimmed from start and end

        Raises:
            NoiseSuppressionError: If processing fails
        """
        if not self._initialized:
            raise NoiseSuppressionError("SilenceTrimmer not initialized. Call initialize() first.")

        try:
            audio_data = audio_chunk.data

            # If audio is too short, don't trim
            if len(audio_data) < (self.min_audio_duration_ms * self.sample_rate // 1000):
                logger.debug("Audio too short to trim, returning original")
                return audio_chunk

            # Calculate frame size in samples
            frame_size = (self.sample_rate * self.FRAME_SIZE_MS) // 1000

            if frame_size <= 0 or len(audio_data) < frame_size:
                logger.debug("Invalid frame size or audio too short, returning original")
                return audio_chunk

            # Calculate RMS energy for each frame
            num_frames = len(audio_data) // frame_size
            if num_frames == 0:
                return audio_chunk

            energy_db = np.zeros(num_frames)

            for i in range(num_frames):
                start_idx = i * frame_size
                end_idx = start_idx + frame_size
                frame = audio_data[start_idx:end_idx]

                # Calculate RMS (root mean square)
                rms = np.sqrt(np.mean(frame**2))

                # Convert to decibels (with floor to avoid log(0))
                if rms > 0:
                    energy_db[i] = 20 * np.log10(rms)
                else:
                    energy_db[i] = -100.0  # Very low energy

            # Find first and last frames above threshold
            above_threshold = energy_db > self.threshold_db

            if not np.any(above_threshold):
                # All frames are silent - return minimal audio
                logger.debug("All frames below threshold, returning minimal audio")
                min_samples = (self.min_audio_duration_ms * self.sample_rate) // 1000
                min_samples = min(min_samples, len(audio_data))
                trimmed_data = audio_data[:min_samples]
            else:
                # Find first and last non-silent frames
                first_frame = np.argmax(above_threshold)
                last_frame = len(above_threshold) - 1 - np.argmax(above_threshold[::-1])

                # Convert frame indices to sample indices
                start_sample = int(first_frame * frame_size)
                end_sample = int((last_frame + 1) * frame_size)

                # Ensure we don't go out of bounds
                end_sample = min(end_sample, len(audio_data))

                # Trim the audio
                trimmed_data = audio_data[start_sample:end_sample]

                # Log trimming statistics
                samples_removed = len(audio_data) - len(trimmed_data)
                ms_removed = (samples_removed * 1000) // self.sample_rate
                logger.debug(
                    "Trimmed %d samples (%.1fms) from audio (original: %dms, trimmed: %dms)",
                    samples_removed,
                    ms_removed,
                    audio_chunk.duration_ms,
                    (len(trimmed_data) * 1000) // self.sample_rate,
                )

            # Create new AudioChunk with trimmed data
            trimmed_duration_ms = (len(trimmed_data) * 1000) // self.sample_rate

            return AudioChunk(
                data=trimmed_data,
                sample_rate=audio_chunk.sample_rate,
                timestamp=audio_chunk.timestamp,
                duration_ms=trimmed_duration_ms,
            )

        except Exception as e:
            logger.error("Failed to trim silence: %s", e, exc_info=True)
            raise NoiseSuppressionError(f"Failed to trim silence: {e}") from e

    async def shutdown(self) -> None:
        """Shut down the silence trimmer and release resources."""
        logger.info("Shutting down SilenceTrimmer")
        self._initialized = False
        logger.debug("SilenceTrimmer shutdown complete")
