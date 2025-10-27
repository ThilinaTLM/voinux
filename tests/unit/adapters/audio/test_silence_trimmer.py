"""Unit tests for SilenceTrimmer audio processor."""

from datetime import datetime

import numpy as np
import pytest

from voinux.adapters.audio.silence_trimmer import SilenceTrimmer
from voinux.domain.entities import AudioChunk
from voinux.domain.exceptions import NoiseSuppressionError


@pytest.fixture
def sample_rate() -> int:
    """Sample rate for tests."""
    return 16000


@pytest.fixture
def silence_trimmer(sample_rate: int) -> SilenceTrimmer:
    """Create a SilenceTrimmer instance for testing."""
    trimmer = SilenceTrimmer(threshold_db=-40.0, min_audio_duration_ms=100)
    return trimmer


class TestSilenceTrimmerInitialization:
    """Tests for SilenceTrimmer initialization."""

    async def test_initialization(self, silence_trimmer: SilenceTrimmer, sample_rate: int) -> None:
        """Test successful initialization."""
        await silence_trimmer.initialize(sample_rate=sample_rate)
        assert silence_trimmer._initialized is True
        assert silence_trimmer.sample_rate == sample_rate

    async def test_initialization_with_custom_params(self, sample_rate: int) -> None:
        """Test initialization with custom parameters."""
        trimmer = SilenceTrimmer(threshold_db=-50.0, min_audio_duration_ms=200)
        await trimmer.initialize(sample_rate=sample_rate)
        assert trimmer.threshold_db == -50.0
        assert trimmer.min_audio_duration_ms == 200

    async def test_shutdown(self, silence_trimmer: SilenceTrimmer, sample_rate: int) -> None:
        """Test shutdown."""
        await silence_trimmer.initialize(sample_rate=sample_rate)
        await silence_trimmer.shutdown()
        assert silence_trimmer._initialized is False


class TestSilenceTrimming:
    """Tests for silence trimming functionality."""

    async def test_trim_leading_silence(
        self, silence_trimmer: SilenceTrimmer, sample_rate: int
    ) -> None:
        """Test trimming leading silence from audio."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio with leading silence (0.5s) followed by speech (0.5s)
        silence_duration_ms = 500
        speech_duration_ms = 500
        silence_samples = (sample_rate * silence_duration_ms) // 1000
        speech_samples = (sample_rate * speech_duration_ms) // 1000

        # Silence: very low amplitude
        silence = np.zeros(silence_samples, dtype=np.float32) + 0.001
        # Speech: higher amplitude
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.5
        )

        audio_data = np.concatenate([silence, speech])
        duration_ms = (len(audio_data) * 1000) // sample_rate

        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should have trimmed leading silence
        assert len(processed_chunk.data) < len(chunk.data)
        assert processed_chunk.duration_ms < chunk.duration_ms

    async def test_trim_trailing_silence(
        self, silence_trimmer: SilenceTrimmer, sample_rate: int
    ) -> None:
        """Test trimming trailing silence from audio."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio with speech (0.5s) followed by trailing silence (0.5s)
        speech_duration_ms = 500
        silence_duration_ms = 500
        speech_samples = (sample_rate * speech_duration_ms) // 1000
        silence_samples = (sample_rate * silence_duration_ms) // 1000

        # Speech: higher amplitude
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.5
        )
        # Silence: very low amplitude
        silence = np.zeros(silence_samples, dtype=np.float32) + 0.001

        audio_data = np.concatenate([speech, silence])
        duration_ms = (len(audio_data) * 1000) // sample_rate

        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should have trimmed trailing silence
        assert len(processed_chunk.data) < len(chunk.data)
        assert processed_chunk.duration_ms < chunk.duration_ms

    async def test_trim_both_ends(self, silence_trimmer: SilenceTrimmer, sample_rate: int) -> None:
        """Test trimming silence from both ends."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio with leading silence (0.3s) + speech (0.4s) + trailing silence (0.3s)
        silence_duration_ms = 300
        speech_duration_ms = 400
        silence_samples = (sample_rate * silence_duration_ms) // 1000
        speech_samples = (sample_rate * speech_duration_ms) // 1000

        # Silence: very low amplitude
        silence = np.zeros(silence_samples, dtype=np.float32) + 0.001
        # Speech: higher amplitude
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.5
        )

        audio_data = np.concatenate([silence, speech, silence])
        duration_ms = (len(audio_data) * 1000) // sample_rate

        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should have trimmed both leading and trailing silence
        assert len(processed_chunk.data) < len(chunk.data)
        # Trimmed duration should be close to speech duration
        assert 300 <= processed_chunk.duration_ms <= 500  # Allow some tolerance

    async def test_no_trimming_needed(
        self, silence_trimmer: SilenceTrimmer, sample_rate: int
    ) -> None:
        """Test audio with no silence to trim."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio with only speech (no silence)
        speech_duration_ms = 500
        speech_samples = (sample_rate * speech_duration_ms) // 1000
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.5
        )

        chunk = AudioChunk(
            data=speech,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=speech_duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should have similar length (minimal trimming)
        assert abs(len(processed_chunk.data) - len(chunk.data)) < sample_rate * 0.1  # Within 100ms

    async def test_all_silence(self, silence_trimmer: SilenceTrimmer, sample_rate: int) -> None:
        """Test audio with only silence."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio with only silence
        silence_duration_ms = 500
        silence_samples = (sample_rate * silence_duration_ms) // 1000
        silence = np.zeros(silence_samples, dtype=np.float32) + 0.001

        chunk = AudioChunk(
            data=silence,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=silence_duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should return minimal audio (min_audio_duration_ms worth)
        expected_samples = (sample_rate * silence_trimmer.min_audio_duration_ms) // 1000
        assert len(processed_chunk.data) <= expected_samples + sample_rate * 0.02  # Small tolerance

    async def test_short_audio_not_trimmed(
        self, silence_trimmer: SilenceTrimmer, sample_rate: int
    ) -> None:
        """Test that very short audio is not trimmed."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        # Create audio shorter than min_audio_duration_ms
        short_duration_ms = 50  # Less than 100ms minimum
        short_samples = (sample_rate * short_duration_ms) // 1000
        audio_data = np.random.randn(short_samples).astype(np.float32) * 0.1

        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=short_duration_ms,
        )

        # Process the chunk
        processed_chunk = await silence_trimmer.process(chunk)

        # Should return original audio unchanged
        assert len(processed_chunk.data) == len(chunk.data)

    async def test_process_not_initialized(self, sample_rate: int) -> None:
        """Test that processing fails if not initialized."""
        trimmer = SilenceTrimmer()

        audio_data = np.random.randn(1000).astype(np.float32)
        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=62,
        )

        with pytest.raises(NoiseSuppressionError, match="not initialized"):
            await trimmer.process(chunk)


class TestSilenceTrimmerEdgeCases:
    """Tests for edge cases."""

    async def test_very_low_threshold(self, sample_rate: int) -> None:
        """Test with very low (aggressive) threshold."""
        trimmer = SilenceTrimmer(threshold_db=-60.0, min_audio_duration_ms=100)
        await trimmer.initialize(sample_rate=sample_rate)

        # Should trim more aggressively
        speech_samples = (sample_rate * 500) // 1000
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.1
        )

        chunk = AudioChunk(
            data=speech,
            sample_rate=sample_rate,
            timestamp=datetime.now(),
            duration_ms=500,
        )

        processed_chunk = await trimmer.process(chunk)
        assert len(processed_chunk.data) <= len(chunk.data)

    async def test_preserve_metadata(
        self, silence_trimmer: SilenceTrimmer, sample_rate: int
    ) -> None:
        """Test that metadata is preserved correctly."""
        await silence_trimmer.initialize(sample_rate=sample_rate)

        original_timestamp = datetime.now()
        speech_samples = (sample_rate * 500) // 1000
        speech = (
            np.sin(2 * np.pi * 440 * np.arange(speech_samples) / sample_rate).astype(np.float32)
            * 0.5
        )

        chunk = AudioChunk(
            data=speech,
            sample_rate=sample_rate,
            timestamp=original_timestamp,
            duration_ms=500,
        )

        processed_chunk = await silence_trimmer.process(chunk)

        # Metadata should be preserved
        assert processed_chunk.sample_rate == chunk.sample_rate
        assert processed_chunk.timestamp == original_timestamp
        # Duration should be updated to match trimmed audio
        expected_duration = (len(processed_chunk.data) * 1000) // sample_rate
        assert processed_chunk.duration_ms == expected_duration
