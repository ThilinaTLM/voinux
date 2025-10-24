"""Domain exceptions for the Voinux voice transcription system."""


class VoinuxError(Exception):
    """Base exception for all Voinux errors."""

    pass


class AudioCaptureError(VoinuxError):
    """Exception raised when audio capture fails."""

    pass


class TranscriptionError(VoinuxError):
    """Exception raised when speech transcription fails."""

    pass


class KeyboardSimulationError(VoinuxError):
    """Exception raised when keyboard simulation fails."""

    pass


class VADError(VoinuxError):
    """Exception raised when voice activation detection fails."""

    pass


class ModelDownloadError(VoinuxError):
    """Exception raised when model download fails."""

    pass


class ConfigError(VoinuxError):
    """Exception raised when configuration loading/saving fails."""

    pass


class InitializationError(VoinuxError):
    """Exception raised when system initialization fails."""

    pass


class SessionError(VoinuxError):
    """Exception raised when session management fails."""

    pass
