"""Composite audio processor for chaining multiple processors."""

import logging

from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError
from voinux.domain.ports import IAudioProcessor

logger = logging.getLogger(__name__)


class CompositeAudioProcessor(IAudioProcessor):
    """Composite audio processor that chains multiple processors in sequence.

    This allows combining multiple audio processing steps (e.g., noise suppression
    followed by silence trimming) into a single processor that can be used in the
    transcription pipeline.
    """

    def __init__(self, processors: list[IAudioProcessor]) -> None:
        """Initialize the composite processor.

        Args:
            processors: List of processors to chain (executed in order)
        """
        if not processors:
            raise ValueError("CompositeAudioProcessor requires at least one processor")

        self.processors = processors
        self._initialized = False

    async def initialize(self, sample_rate: int) -> None:
        """Initialize all processors in the chain.

        Args:
            sample_rate: Audio sample rate in Hz

        Raises:
            NoiseSuppressionError: If initialization fails
        """
        try:
            logger.info(
                "Initializing CompositeAudioProcessor with %d processors (sample_rate=%d)",
                len(self.processors),
                sample_rate,
            )

            for i, processor in enumerate(self.processors):
                processor_name = processor.__class__.__name__
                logger.debug(
                    "Initializing processor %d/%d: %s", i + 1, len(self.processors), processor_name
                )
                await processor.initialize(sample_rate)

            self._initialized = True
            logger.info("CompositeAudioProcessor initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize CompositeAudioProcessor: %s", e, exc_info=True)
            raise NoiseSuppressionError(f"Failed to initialize CompositeAudioProcessor: {e}") from e

    async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
        """Process audio through all processors in sequence.

        Args:
            audio_chunk: Audio chunk to process

        Returns:
            AudioChunk: Processed audio chunk

        Raises:
            NoiseSuppressionError: If processing fails
        """
        if not self._initialized:
            raise NoiseSuppressionError(
                "CompositeAudioProcessor not initialized. Call initialize() first."
            )

        try:
            processed_chunk = audio_chunk

            for processor in self.processors:
                processed_chunk = await processor.process(processed_chunk)

        except Exception as e:
            logger.error(
                "Failed to process audio through composite processor: %s", e, exc_info=True
            )
            raise NoiseSuppressionError(f"Failed to process audio: {e}") from e
        else:
            return processed_chunk

    async def shutdown(self) -> None:
        """Shut down all processors in the chain."""
        logger.info("Shutting down CompositeAudioProcessor")

        for i, processor in enumerate(self.processors):
            processor_name = processor.__class__.__name__
            logger.debug(
                "Shutting down processor %d/%d: %s", i + 1, len(self.processors), processor_name
            )
            await processor.shutdown()

        self._initialized = False
        logger.info("CompositeAudioProcessor shutdown complete")
