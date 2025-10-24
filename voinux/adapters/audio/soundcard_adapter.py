"""SoundCard audio capture adapter for real-time microphone input."""

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Optional

import numpy as np
import soundcard as sc

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import AudioCaptureError
from voinux.domain.ports import IAudioCapture


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
            else:
                self.microphone = sc.default_microphone()

            # Create queue for audio chunks
            self._queue = asyncio.Queue(maxsize=10)
            self._running = True

        except Exception as e:
            raise AudioCaptureError(f"Failed to start audio capture: {e}") from e

    async def stop(self) -> None:
        """Stop audio capture and release resources."""
        self._running = False
        self.microphone = None
        self._queue = None

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

                    yield chunk

        except Exception as e:
            self._running = False
            raise AudioCaptureError(f"Audio streaming failed: {e}") from e
