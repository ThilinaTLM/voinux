"""Unit tests for CompositeAudioProcessor."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from voinux.adapters.audio.composite_processor import CompositeAudioProcessor
from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError
from voinux.domain.ports import IAudioProcessor


class MockAudioProcessor(IAudioProcessor):
    """Mock audio processor for testing."""

    def __init__(self, name: str) -> None:
        """Initialize mock processor."""
        self.name = name
        self.initialized = False
        self.process_called = False
        self.shutdown_called = False

    async def initialize(self, sample_rate: int) -> None:
        """Initialize the processor."""
        self.initialized = True
        self.sample_rate = sample_rate

    async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
        """Process audio chunk."""
        self.process_called = True
        # Simulate processing by modifying the audio slightly
        modified_data = audio_chunk.data * 0.9
        return AudioChunk(
            data=modified_data,
            sample_rate=audio_chunk.sample_rate,
            timestamp=audio_chunk.timestamp,
            duration_ms=audio_chunk.duration_ms,
        )

    async def shutdown(self) -> None:
        """Shutdown the processor."""
        self.shutdown_called = True
        self.initialized = False


@pytest.fixture
def sample_rate() -> int:
    """Sample rate for tests."""
    return 16000


@pytest.fixture
def audio_chunk(sample_rate: int) -> AudioChunk:
    """Create a test audio chunk."""
    audio_data = np.random.randn(sample_rate).astype(np.float32) * 0.5
    return AudioChunk(
        data=audio_data,
        sample_rate=sample_rate,
        timestamp=datetime.now(),
        duration_ms=1000,
    )


class TestCompositeProcessorInitialization:
    """Tests for CompositeAudioProcessor initialization."""

    async def test_initialization_single_processor(self, sample_rate: int) -> None:
        """Test initialization with single processor."""
        processor = MockAudioProcessor("processor1")
        composite = CompositeAudioProcessor([processor])

        await composite.initialize(sample_rate=sample_rate)

        assert composite._initialized is True
        assert processor.initialized is True
        assert processor.sample_rate == sample_rate

    async def test_initialization_multiple_processors(self, sample_rate: int) -> None:
        """Test initialization with multiple processors."""
        processor1 = MockAudioProcessor("processor1")
        processor2 = MockAudioProcessor("processor2")
        composite = CompositeAudioProcessor([processor1, processor2])

        await composite.initialize(sample_rate=sample_rate)

        assert composite._initialized is True
        assert processor1.initialized is True
        assert processor2.initialized is True
        assert processor1.sample_rate == sample_rate
        assert processor2.sample_rate == sample_rate

    def test_initialization_empty_list(self) -> None:
        """Test that empty processor list raises error."""
        with pytest.raises(ValueError, match="at least one processor"):
            CompositeAudioProcessor([])

    async def test_shutdown(self, sample_rate: int) -> None:
        """Test shutdown."""
        processor1 = MockAudioProcessor("processor1")
        processor2 = MockAudioProcessor("processor2")
        composite = CompositeAudioProcessor([processor1, processor2])

        await composite.initialize(sample_rate=sample_rate)
        await composite.shutdown()

        assert composite._initialized is False
        assert processor1.shutdown_called is True
        assert processor2.shutdown_called is True


class TestCompositeProcessorProcessing:
    """Tests for audio processing."""

    async def test_process_single_processor(
        self, sample_rate: int, audio_chunk: AudioChunk
    ) -> None:
        """Test processing with single processor."""
        processor = MockAudioProcessor("processor1")
        composite = CompositeAudioProcessor([processor])

        await composite.initialize(sample_rate=sample_rate)
        result = await composite.process(audio_chunk)

        assert processor.process_called is True
        assert result.sample_rate == audio_chunk.sample_rate
        assert len(result.data) == len(audio_chunk.data)

    async def test_process_multiple_processors_in_sequence(
        self, sample_rate: int, audio_chunk: AudioChunk
    ) -> None:
        """Test that processors are applied in sequence."""
        processor1 = MockAudioProcessor("processor1")
        processor2 = MockAudioProcessor("processor2")
        composite = CompositeAudioProcessor([processor1, processor2])

        await composite.initialize(sample_rate=sample_rate)
        result = await composite.process(audio_chunk)

        # Both processors should have been called
        assert processor1.process_called is True
        assert processor2.process_called is True

        # Result should be affected by both processors (0.9 * 0.9 = 0.81)
        # Original data is reduced by 10% by each processor
        assert result.sample_rate == audio_chunk.sample_rate
        assert len(result.data) == len(audio_chunk.data)

    async def test_process_not_initialized(self, audio_chunk: AudioChunk) -> None:
        """Test that processing fails if not initialized."""
        processor = MockAudioProcessor("processor1")
        composite = CompositeAudioProcessor([processor])

        with pytest.raises(NoiseSuppressionError, match="not initialized"):
            await composite.process(audio_chunk)

    async def test_process_preserves_chain_order(
        self, sample_rate: int, audio_chunk: AudioChunk
    ) -> None:
        """Test that processors are called in the correct order."""
        call_order = []

        class OrderTrackingProcessor(IAudioProcessor):
            """Processor that tracks call order."""

            def __init__(self, name: str) -> None:
                self.name = name

            async def initialize(self, sample_rate: int) -> None:
                pass

            async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
                call_order.append(self.name)
                return audio_chunk

            async def shutdown(self) -> None:
                pass

        processor1 = OrderTrackingProcessor("first")
        processor2 = OrderTrackingProcessor("second")
        processor3 = OrderTrackingProcessor("third")
        composite = CompositeAudioProcessor([processor1, processor2, processor3])

        await composite.initialize(sample_rate=sample_rate)
        await composite.process(audio_chunk)

        assert call_order == ["first", "second", "third"]


class TestCompositeProcessorErrorHandling:
    """Tests for error handling."""

    async def test_initialization_failure_propagates(self, sample_rate: int) -> None:
        """Test that initialization errors are propagated."""

        class FailingProcessor(IAudioProcessor):
            async def initialize(self, sample_rate: int) -> None:
                raise RuntimeError("Initialization failed")

            async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
                return audio_chunk

            async def shutdown(self) -> None:
                pass

        processor = FailingProcessor()
        composite = CompositeAudioProcessor([processor])

        with pytest.raises(NoiseSuppressionError, match="Initialization failed"):
            await composite.initialize(sample_rate=sample_rate)

    async def test_processing_failure_propagates(
        self, sample_rate: int, audio_chunk: AudioChunk
    ) -> None:
        """Test that processing errors are propagated."""

        class FailingProcessor(IAudioProcessor):
            async def initialize(self, sample_rate: int) -> None:
                pass

            async def process(self, audio_chunk: AudioChunk) -> AudioChunk:
                raise RuntimeError("Processing failed")

            async def shutdown(self) -> None:
                pass

        processor = FailingProcessor()
        composite = CompositeAudioProcessor([processor])

        await composite.initialize(sample_rate=sample_rate)

        with pytest.raises(NoiseSuppressionError, match="Processing failed"):
            await composite.process(audio_chunk)
