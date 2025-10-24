"""Application use cases for Voinux."""

import asyncio
import signal
from typing import Callable, Optional

from voinux.application.factories import (
    create_audio_capture,
    create_keyboard_simulator,
    create_model_manager,
    create_speech_recognizer,
    create_vad,
)
from voinux.config.config import Config
from voinux.domain.entities import ModelConfig, TranscriptionSession
from voinux.domain.exceptions import InitializationError
from voinux.domain.services import SessionManager, TranscriptionPipeline


class StartTranscription:
    """Use case for starting real-time transcription."""

    def __init__(self, config: Config) -> None:
        """Initialize the use case.

        Args:
            config: Application configuration
        """
        self.config = config
        self.pipeline: Optional[TranscriptionPipeline] = None
        self.session_manager = SessionManager()

    async def execute(
        self,
        on_status_change: Optional[Callable[[str], None]] = None,
    ) -> TranscriptionSession:
        """Execute the transcription use case.

        Args:
            on_status_change: Callback for status updates

        Returns:
            TranscriptionSession: The completed session

        Raises:
            InitializationError: If initialization fails
        """
        try:
            # Create session
            model_config = ModelConfig(
                model_name=self.config.faster_whisper.model,
                device=self.config.faster_whisper.device,
                compute_type=self.config.faster_whisper.compute_type,
                beam_size=self.config.faster_whisper.beam_size,
                language=self.config.faster_whisper.language,
                vad_filter=False,
                model_path=self.config.faster_whisper.model_path,
            )

            session = self.session_manager.create_session(model_config)

            # Download model if needed
            if on_status_change:
                on_status_change("Checking model...")

            model_manager = create_model_manager(self.config)
            model_path = await model_manager.get_model_path(self.config.faster_whisper.model)

            if model_path is None:
                if on_status_change:
                    on_status_change(f"Downloading model: {self.config.faster_whisper.model}...")
                await model_manager.download_model(self.config.faster_whisper.model)

            # Create adapters
            if on_status_change:
                on_status_change("Initializing components...")

            audio_capture = await create_audio_capture(self.config)
            vad = await create_vad(self.config)
            recognizer = await create_speech_recognizer(self.config)
            keyboard = await create_keyboard_simulator(self.config)

            # Create pipeline
            self.pipeline = TranscriptionPipeline(
                audio_capture=audio_capture,
                vad=vad,
                recognizer=recognizer,
                keyboard=keyboard,
                session=session,
                vad_enabled=self.config.vad.enabled,
            )

            # Set up signal handlers for graceful shutdown
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.stop()),
                )

            # Start transcription
            if on_status_change:
                on_status_change("Listening...")

            await self.pipeline.start()

            # Get completed session
            completed_session = self.session_manager.end_current_session()
            return completed_session if completed_session else session

        except Exception as e:
            raise InitializationError(f"Failed to start transcription: {e}") from e

    async def stop(self) -> None:
        """Stop the transcription pipeline."""
        if self.pipeline:
            await self.pipeline.stop()


class TestAudio:
    """Use case for testing audio capture."""

    def __init__(self, config: Config) -> None:
        """Initialize the use case.

        Args:
            config: Application configuration
        """
        self.config = config

    async def execute(self, duration_seconds: int = 5) -> dict[str, any]:  # type: ignore[valid-type]
        """Test audio capture for a specified duration.

        Args:
            duration_seconds: How long to test audio capture

        Returns:
            dict: Test results with audio statistics
        """
        audio_capture = await create_audio_capture(self.config)
        await audio_capture.start()

        chunks_received = 0
        total_samples = 0

        try:
            async for chunk in audio_capture.stream():
                chunks_received += 1
                total_samples += len(chunk.data)

                # Calculate elapsed time
                elapsed = (chunks_received * self.config.audio.chunk_duration_ms) / 1000

                if elapsed >= duration_seconds:
                    break

        finally:
            await audio_capture.stop()

        return {
            "success": True,
            "chunks_received": chunks_received,
            "total_samples": total_samples,
            "duration_seconds": duration_seconds,
            "sample_rate": self.config.audio.sample_rate,
        }


class TestGPU:
    """Use case for testing GPU availability and configuration."""

    def __init__(self, config: Config) -> None:
        """Initialize the use case.

        Args:
            config: Application configuration
        """
        self.config = config

    async def execute(self) -> dict[str, any]:  # type: ignore[valid-type]
        """Test GPU availability.

        Returns:
            dict: GPU test results
        """
        import torch

        results = {
            "cuda_available": torch.cuda.is_available(),
            "device_count": 0,
            "devices": [],
        }

        if torch.cuda.is_available():
            results["device_count"] = torch.cuda.device_count()

            for i in range(torch.cuda.device_count()):
                device_info = {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "total_memory_gb": torch.cuda.get_device_properties(i).total_memory / (1024**3),
                }
                results["devices"].append(device_info)

        return results
