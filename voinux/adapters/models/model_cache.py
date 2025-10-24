"""Model management adapter for downloading and caching Whisper models."""

import asyncio
from pathlib import Path
from typing import Optional

from faster_whisper.utils import download_model

from voinux.domain.exceptions import ModelDownloadError
from voinux.domain.ports import IModelManager


class ModelCache(IModelManager):
    """Adapter for managing Whisper model downloads and caching."""

    # VRAM requirements in MB for different model/compute_type combinations
    VRAM_REQUIREMENTS = {
        ("tiny", "int8"): 300,
        ("tiny", "float16"): 500,
        ("tiny", "float32"): 1000,
        ("base", "int8"): 500,
        ("base", "float16"): 900,
        ("base", "float32"): 1500,
        ("small", "int8"): 1000,
        ("small", "float16"): 1800,
        ("small", "float32"): 3000,
        ("medium", "int8"): 2500,
        ("medium", "float16"): 4500,
        ("medium", "float32"): 7000,
        ("large-v3", "int8"): 5000,
        ("large-v3", "float16"): 8000,
        ("large-v3", "float32"): 12000,
        ("large-v3-turbo", "int8"): 4000,
        ("large-v3-turbo", "float16"): 6000,
        ("large-v3-turbo", "float32"): 10000,
    }

    def __init__(self, cache_dir: Path) -> None:
        """Initialize the model cache.

        Args:
            cache_dir: Directory for caching models
        """
        self.cache_dir = cache_dir
        self.models_dir = cache_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    async def download_model(self, model_name: str, force: bool = False) -> Path:
        """Download a Whisper model to local cache.

        Args:
            model_name: Name of the model (e.g., "large-v3-turbo")
            force: Force re-download even if cached

        Returns:
            Path: Path to the downloaded model directory

        Raises:
            ModelDownloadError: If download fails
        """
        try:
            # Check if model already exists
            model_path = await self.get_model_path(model_name)
            if model_path and not force:
                return model_path

            # Download model using faster-whisper utility
            # Run in thread pool since download_model is synchronous
            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(
                None,
                lambda: download_model(
                    model_name,
                    output_dir=str(self.models_dir),
                    local_files_only=False,
                ),
            )

            return Path(downloaded_path)

        except Exception as e:
            raise ModelDownloadError(f"Failed to download model '{model_name}': {e}") from e

    async def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get the local path to a cached model.

        Args:
            model_name: Name of the model

        Returns:
            Optional[Path]: Path to the model, or None if not cached
        """
        # Check standard cache location
        model_path = self.models_dir / model_name
        if model_path.exists() and model_path.is_dir():
            return model_path

        # Also check if the model_name is an absolute path
        if Path(model_name).exists():
            return Path(model_name)

        return None

    async def list_cached_models(self) -> list[str]:
        """List all models currently in the cache.

        Returns:
            list[str]: List of cached model names
        """
        if not self.models_dir.exists():
            return []

        models = []
        for item in self.models_dir.iterdir():
            if item.is_dir():
                models.append(item.name)

        return sorted(models)

    def get_vram_requirements(self, model_name: str, compute_type: str) -> int:
        """Get estimated VRAM requirements for a model in MB.

        Args:
            model_name: Name of the model
            compute_type: Computation type (int8, float16, float32)

        Returns:
            int: Estimated VRAM in MB
        """
        key = (model_name, compute_type)
        return self.VRAM_REQUIREMENTS.get(key, 0)

    async def verify_model_integrity(self, model_name: str) -> bool:
        """Verify that a cached model is complete and valid.

        Args:
            model_name: Name of the model to verify

        Returns:
            bool: True if model is valid
        """
        model_path = await self.get_model_path(model_name)
        if not model_path:
            return False

        # Check for required files (model.bin, config.json, vocabulary, etc.)
        required_files = ["model.bin", "config.json"]
        for filename in required_files:
            if not (model_path / filename).exists():
                return False

        return True
