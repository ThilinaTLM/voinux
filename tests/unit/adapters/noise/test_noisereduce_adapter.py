"""Unit tests for NoiseReduceProcessor adapter."""

from datetime import datetime

import numpy as np
import pytest

from voinux.adapters.noise.noisereduce_adapter import NoiseReduceProcessor
from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError


class TestNoiseReduceProcessor:
    """Test suite for NoiseReduceProcessor."""

    @pytest.fixture
    def processor(self) -> NoiseReduceProcessor:
        """Create a processor instance for testing."""
        return NoiseReduceProcessor(
            stationary=True,
            prop_decrease=1.0,
            freq_mask_smooth_hz=500,
            time_mask_smooth_ms=50,
        )

    @pytest.fixture
    def sample_audio_chunk(self) -> AudioChunk:
        """Create a sample audio chunk for testing."""
        # Generate 1 second of random audio at 16kHz
        sample_rate = 16000
        duration_ms = 1000
        num_samples = (sample_rate * duration_ms) // 1000

        # Create random noise
        audio_data = np.random.randn(num_samples).astype(np.float32) * 0.1

        return AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )

    async def test_initialize(self, processor: NoiseReduceProcessor) -> None:
        """Test processor initialization."""
        await processor.initialize(sample_rate=16000)
        assert processor._initialized is True
        assert processor.sample_rate == 16000

    async def test_process_without_initialize_raises_error(
        self, processor: NoiseReduceProcessor, sample_audio_chunk: AudioChunk
    ) -> None:
        """Test that processing without initialization raises an error."""
        with pytest.raises(NoiseSuppressionError, match="not initialized"):
            await processor.process(sample_audio_chunk)

    async def test_process_audio_chunk(
        self, processor: NoiseReduceProcessor, sample_audio_chunk: AudioChunk
    ) -> None:
        """Test processing an audio chunk."""
        await processor.initialize(sample_rate=16000)

        processed_chunk = await processor.process(sample_audio_chunk)

        # Verify output is an AudioChunk
        assert isinstance(processed_chunk, AudioChunk)

        # Verify output has same shape as input
        assert processed_chunk.data.shape == sample_audio_chunk.data.shape

        # Verify output is float32
        assert processed_chunk.data.dtype == np.float32

        # Verify sample rate and duration are preserved
        assert processed_chunk.sample_rate == sample_audio_chunk.sample_rate
        assert processed_chunk.duration_ms == sample_audio_chunk.duration_ms

    async def test_shutdown(self, processor: NoiseReduceProcessor) -> None:
        """Test processor shutdown."""
        await processor.initialize(sample_rate=16000)
        await processor.shutdown()
        assert processor._initialized is False
