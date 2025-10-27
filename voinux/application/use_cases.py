"""Application use cases for Voinux."""

import asyncio
import logging
import signal
from collections.abc import Callable
from typing import Any

from voinux.application.factories import (
    create_audio_capture,
    create_audio_processor,
    create_keyboard_simulator,
    create_model_manager,
    create_speech_recognizer,
    create_vad,
)
from voinux.config.config import Config
from voinux.domain.entities import BufferConfig, ModelConfig, TranscriptionSession
from voinux.domain.exceptions import InitializationError
from voinux.domain.services import SessionManager, TranscriptionPipeline

logger = logging.getLogger(__name__)


class StartTranscription:
    """Use case for starting real-time transcription."""

    def __init__(
        self,
        config: Config,
        provider: str | None = None,
        api_key_override: str | None = None,
        enable_silence_trimming: bool | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            config: Application configuration
            provider: Provider override (None to use default "whisper")
            api_key_override: API key override from CLI
            enable_silence_trimming: Silence trimming override (None for auto based on provider)
        """
        self.config = config
        self.provider = provider
        self.api_key_override = api_key_override
        self.enable_silence_trimming = enable_silence_trimming
        self.pipeline: TranscriptionPipeline | None = None
        self.session_manager = SessionManager()

    async def execute(
        self,
        on_status_change: Callable[[str], None] | None = None,
        on_audio_chunk: Callable[[Any, bool], None] | None = None,
        install_signal_handlers: bool = True,
    ) -> TranscriptionSession:
        """Execute the transcription use case.

        Args:
            on_status_change: Callback for status updates
            on_audio_chunk: Optional callback for each audio chunk (chunk, is_speech)
            install_signal_handlers: Whether to install SIGINT/SIGTERM handlers (default: True)
                                    Set to False in GUI mode where Qt handles signals

        Returns:
            TranscriptionSession: The completed session

        Raises:
            InitializationError: If initialization fails
        """
        try:
            logger.info("Starting transcription use case")

            # Create session with provider info
            actual_provider = self.provider or "whisper"

            # Get API key for cloud providers (with precedence: CLI > Env > Config)
            api_key = None
            if actual_provider != "whisper":
                from voinux.application.api_key_manager import APIKeyManager

                api_key = APIKeyManager.get_api_key(
                    provider=actual_provider,
                    cli_api_key=self.api_key_override,
                    config_api_key=self.config.gemini.api_key,
                )

            model_config = ModelConfig(
                model_name=self.config.faster_whisper.model,
                device=self.config.faster_whisper.device,
                compute_type=self.config.faster_whisper.compute_type,
                beam_size=self.config.faster_whisper.beam_size,
                language=self.config.faster_whisper.language,
                vad_filter=False,
                model_path=self.config.faster_whisper.model_path,
                provider=actual_provider,
                api_key=api_key,
            )

            session = self.session_manager.create_session(model_config)

            # Download model if needed
            if on_status_change:
                on_status_change("Checking model...")

            logger.info("Checking for model: %s", self.config.faster_whisper.model)
            model_manager = create_model_manager(self.config)
            model_path = await model_manager.get_model_path(self.config.faster_whisper.model)

            if model_path is None:
                logger.info("Model not found, downloading: %s", self.config.faster_whisper.model)
                if on_status_change:
                    on_status_change(f"Downloading model: {self.config.faster_whisper.model}...")
                await model_manager.download_model(self.config.faster_whisper.model)
            else:
                logger.info("Model found at: %s", model_path)

            # Create adapters
            if on_status_change:
                on_status_change("Initializing components...")

            logger.info("Initializing components")
            audio_capture = await create_audio_capture(self.config)
            vad = await create_vad(self.config)
            # Create audio processor with silence trimming (auto-enabled for cloud providers)
            # If enable_silence_trimming is None, it defaults based on provider
            audio_processor = await create_audio_processor(
                self.config,
                enable_silence_trimming=self.enable_silence_trimming
                if self.enable_silence_trimming is not None
                else False,
                provider=actual_provider,
            )
            recognizer = await create_speech_recognizer(
                self.config, provider=self.provider, api_key_override=self.api_key_override
            )
            keyboard = await create_keyboard_simulator(self.config)
            logger.info("All components initialized successfully")

            # Create buffer config
            buffer_config = BufferConfig(
                silence_threshold_ms=self.config.buffering.silence_threshold_ms,
                max_buffer_duration_ms=self.config.buffering.max_buffer_duration_ms,
                min_utterance_duration_ms=self.config.buffering.min_utterance_duration_ms,
            )

            # Create pipeline
            self.pipeline = TranscriptionPipeline(
                audio_capture=audio_capture,
                vad=vad,
                recognizer=recognizer,
                keyboard=keyboard,
                session=session,
                buffer_config=buffer_config,
                vad_enabled=self.config.vad.enabled,
                noise_suppressor=audio_processor,
                on_audio_chunk=on_audio_chunk,
            )

            # Set up signal handlers for graceful shutdown (CLI mode only)
            if install_signal_handlers:
                loop = asyncio.get_event_loop()
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(
                        sig,
                        lambda: asyncio.create_task(self.stop()),
                    )
                logger.debug("Signal handlers installed for SIGINT and SIGTERM")

            # Start transcription
            if on_status_change:
                on_status_change("Listening...")

            logger.info("Starting transcription pipeline")
            await self.pipeline.start()

            # Get completed session
            completed_session = self.session_manager.end_current_session()
            logger.info("Transcription use case completed")
        except Exception as e:
            logger.error("Failed to start transcription: %s", e, exc_info=True)
            raise InitializationError(f"Failed to start transcription: {e}") from e
        else:
            return completed_session if completed_session else session

    async def stop(self) -> None:
        """Stop the transcription pipeline."""
        if self.pipeline:
            logger.info("Stopping transcription use case")
            await self.pipeline.stop()
            logger.info("Transcription use case stopped")


class TestAudio:
    """Use case for testing audio capture."""

    def __init__(self, config: Config) -> None:
        """Initialize the use case.

        Args:
            config: Application configuration
        """
        self.config = config

    async def execute(self, duration_seconds: int = 5) -> dict[str, Any]:
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

    async def execute(self) -> dict[str, Any]:
        """Test GPU availability.

        Returns:
            dict: GPU test results
        """
        import torch

        results: dict[str, Any] = {
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
