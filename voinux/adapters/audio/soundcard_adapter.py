"""SoundCard audio capture adapter for real-time microphone input."""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Optional

import numpy as np
import soundcard as sc

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import AudioCaptureError
from voinux.domain.ports import IAudioCapture

logger = logging.getLogger(__name__)


class SoundCardAudioCapture(IAudioCapture):
    """Adapter using soundcard library for audio capture."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 1000,
        device_index: Optional[int] = None,
    ) -> None:
        """Initialize the sound card audio capture.

        Args:
            sample_rate: Sample rate in Hz
            chunk_duration_ms: Duration of each audio chunk in milliseconds
            device_index: Specific device index (None for default)
        """
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.device_index = device_index
        self.chunk_size = (sample_rate * chunk_duration_ms) // 1000
        self.microphone: Optional[sc.Microphone] = None
        self._running = False
        self._queue: Optional[asyncio.Queue[AudioChunk]] = None

    async def start(self) -> None:
        """Start audio capture.

        Raises:
            AudioCaptureError: If audio capture fails to start
        """
        try:
            # Get microphone
            if self.device_index is not None:
                mics = sc.all_microphones()
                if self.device_index >= len(mics):
                    raise AudioCaptureError(
                        f"Invalid device index: {self.device_index}. "
                        f"Available devices: {len(mics)}"
                    )
                self.microphone = mics[self.device_index]
                logger.info(
                    "Starting audio capture (device_index=%d, device=%s, sample_rate=%d, chunk_size=%d)",
                    self.device_index,
                    self.microphone.name,
                    self.sample_rate,
                    self.chunk_size,
                )
            else:
                self.microphone = sc.default_microphone()
                logger.info(
                    "Starting audio capture (default_device=%s, sample_rate=%d, chunk_size=%d)",
                    self.microphone.name,
                    self.sample_rate,
                    self.chunk_size,
                )

            # Create queue for audio chunks
            self._queue = asyncio.Queue(maxsize=10)
            self._running = True

        except Exception as e:
            logger.error("Failed to start audio capture: %s", e, exc_info=True)
            raise AudioCaptureError(f"Failed to start audio capture: {e}") from e

    async def stop(self) -> None:
        """Stop audio capture and release resources."""
        logger.info("Stopping audio capture")
        self._running = False

        # Give time for the recording loop to exit cleanly
        # This prevents PulseAudio mutex lock errors
        if self.microphone is not None:
            await asyncio.sleep(0.1)

        self.microphone = None
        self._queue = None
        logger.debug("Audio capture stopped")

    async def stream(self) -> AsyncIterator[AudioChunk]:
        """Stream audio chunks as they are captured.

        Yields:
            AudioChunk: Audio data chunks ready for processing

        Raises:
            AudioCaptureError: If audio capture fails
        """
        if not self._running or self.microphone is None:
            raise AudioCaptureError("Audio capture not started. Call start() first.")

        try:
            # Start recording in background thread
            loop = asyncio.get_event_loop()

            logger.debug("Starting audio stream recording loop")
            chunk_count = 0

            with self.microphone.recorder(
                samplerate=self.sample_rate,
                channels=1,  # Mono
                blocksize=self.chunk_size,
            ) as recorder:
                while self._running:
                    # Record chunk in thread pool
                    data = await loop.run_in_executor(
                        None,
                        recorder.record,
                        self.chunk_size,
                    )

                    # Convert to float32 mono
                    if data.ndim > 1:
                        data = data.mean(axis=1)

                    data = data.astype(np.float32)

                    # Create audio chunk
                    chunk = AudioChunk(
                        data=data,
                        sample_rate=self.sample_rate,
                        timestamp=datetime.now(),
                        duration_ms=self.chunk_duration_ms,
                    )

                    chunk_count += 1
                    logger.debug(
                        "Audio chunk captured (chunk_count=%d, samples=%d, duration=%dms)",
                        chunk_count,
                        len(data),
                        self.chunk_duration_ms,
                    )

                    yield chunk

            logger.debug("Audio stream recording loop ended (total_chunks=%d)", chunk_count)

        except Exception as e:
            self._running = False
            logger.error("Audio streaming failed: %s", e, exc_info=True)
            raise AudioCaptureError(f"Audio streaming failed: {e}") from e
