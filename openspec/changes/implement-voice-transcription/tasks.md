# Implementation Tasks

## 1. Project Structure and Foundation
- [ ] 1.1 Initialize Python project with pyproject.toml
- [ ] 1.2 Configure Poetry or pip-tools for dependency management
- [ ] 1.3 Create directory structure (domain/, adapters/, application/, cli/)
- [ ] 1.4 Set up pytest and testing infrastructure
- [ ] 1.5 Configure pre-commit hooks (black, mypy, ruff)
- [ ] 1.6 Create __init__.py files for all packages

## 2. Domain Layer - Core Entities and Ports
- [ ] 2.1 Implement AudioChunk entity (voinux/domain/entities.py)
- [ ] 2.2 Implement TranscriptionResult entity
- [ ] 2.3 Implement ModelConfig entity
- [ ] 2.4 Implement TranscriptionSession entity
- [ ] 2.5 Define IAudioCapture port interface (voinux/domain/ports.py)
- [ ] 2.6 Define ISpeechRecognizer port interface
- [ ] 2.7 Define IKeyboardSimulator port interface
- [ ] 2.8 Define IVoiceActivationDetector port interface
- [ ] 2.9 Define IModelManager port interface
- [ ] 2.10 Define IConfigRepository port interface
- [ ] 2.11 Define custom exceptions (AudioCaptureError, TranscriptionError, etc.)

## 3. Domain Layer - Core Services
- [ ] 3.1 Implement TranscriptionPipeline service (voinux/domain/services.py)
- [ ] 3.2 Implement SessionManager service
- [ ] 3.3 Write unit tests for entities (tests/unit/domain/)
- [ ] 3.4 Write unit tests for services with mocked ports

## 4. Configuration System
- [ ] 4.1 Define Config dataclass with all settings (voinux/config/config.py)
- [ ] 4.2 Implement default configuration values
- [ ] 4.3 Implement configuration validation logic
- [ ] 4.4 Implement YAMLConfigRepository adapter (voinux/adapters/config/yaml_adapter.py)
- [ ] 4.5 Implement config file creation (with comments)
- [ ] 4.6 Implement configuration precedence (defaults → file → CLI → env)
- [ ] 4.7 Write tests for configuration loading and validation

## 5. Audio Capture Adapters
- [ ] 5.1 Implement SoundCardAudioCapture adapter (voinux/adapters/audio/soundcard_adapter.py)
- [ ] 5.2 Implement async audio streaming with asyncio queues
- [ ] 5.3 Implement audio format conversion (to 16kHz mono float32)
- [ ] 5.4 Implement PyAudioCapture fallback adapter (voinux/adapters/audio/pyaudio_adapter.py)
- [ ] 5.5 Implement audio backend auto-detection factory
- [ ] 5.6 Implement buffer management (bounded queue, drop oldest)
- [ ] 5.7 Write integration tests for audio capture (requires microphone)
- [ ] 5.8 Handle audio device disconnection gracefully

## 6. Voice Activation Detection Adapter
- [ ] 6.1 Implement WebRTCVAD adapter (voinux/adapters/vad/webrtc_adapter.py)
- [ ] 6.2 Implement frame size adaptation for webrtcvad
- [ ] 6.3 Implement threshold-to-aggressiveness mapping
- [ ] 6.4 Implement async wrapper for synchronous VAD
- [ ] 6.5 Implement VAD enable/disable logic
- [ ] 6.6 Implement VAD statistics tracking
- [ ] 6.7 Write unit tests for VAD adapter

## 7. Model Management Adapter
- [ ] 7.1 Implement ModelCache adapter (voinux/adapters/models/model_cache.py)
- [ ] 7.2 Implement model download with progress bar
- [ ] 7.3 Implement model path resolution (cache, absolute, HF)
- [ ] 7.4 Implement model integrity verification
- [ ] 7.5 Implement download retry logic with exponential backoff
- [ ] 7.6 Implement model listing (scan cache directory)
- [ ] 7.7 Implement VRAM requirements lookup table
- [ ] 7.8 Write tests for model management

## 8. Speech Recognition Adapter
- [ ] 8.1 Implement WhisperRecognizer adapter (voinux/adapters/stt/whisper_adapter.py)
- [ ] 8.2 Implement model initialization (GPU/CPU detection)
- [ ] 8.3 Implement async wrapper using ThreadPoolExecutor for faster-whisper
- [ ] 8.4 Implement transcription with all options (beam_size, language, etc.)
- [ ] 8.5 Implement CPU fallback with warning
- [ ] 8.6 Implement transcription timeout handling
- [ ] 8.7 Implement CUDA out-of-memory error handling
- [ ] 8.8 Implement performance monitoring (latency tracking)
- [ ] 8.9 Write integration tests with test audio files

## 9. Keyboard Simulation Adapters
- [ ] 9.1 Implement XDotoolKeyboard adapter (voinux/adapters/keyboard/xdotool_adapter.py)
- [ ] 9.2 Implement YDotoolKeyboard adapter (voinux/adapters/keyboard/ydotool_adapter.py)
- [ ] 9.3 Implement StdoutKeyboard adapter for testing (voinux/adapters/keyboard/stdout_adapter.py)
- [ ] 9.4 Implement text sanitization and shell escaping
- [ ] 9.5 Implement display server detection (X11/Wayland)
- [ ] 9.6 Implement keyboard backend auto-detection factory
- [ ] 9.7 Implement uinput permissions check (Wayland)
- [ ] 9.8 Implement typing modes (instant vs delayed)
- [ ] 9.9 Write integration tests for keyboard simulation

## 10. Application Layer - Use Cases
- [ ] 10.1 Implement StartTranscription use case (voinux/application/use_cases.py)
- [ ] 10.2 Implement RunSetup use case
- [ ] 10.3 Implement TestAudio use case
- [ ] 10.4 Implement TestGPU use case
- [ ] 10.5 Implement TestModel use case
- [ ] 10.6 Implement TestKeyboard use case
- [ ] 10.7 Implement ManageModels use case
- [ ] 10.8 Implement ManageConfig use case

## 11. Application Layer - Dependency Injection
- [ ] 11.1 Implement adapter factory functions (voinux/application/factories.py)
- [ ] 11.2 Implement DI container for creating configured adapters
- [ ] 11.3 Implement auto-detection logic (audio backend, keyboard backend, GPU device)
- [ ] 11.4 Implement graceful fallback chain for each adapter type

## 12. CLI Layer - Command Infrastructure
- [ ] 12.1 Set up Click application (voinux/cli/main.py)
- [ ] 12.2 Implement main CLI group with --version, --help
- [ ] 12.3 Implement common options (--verbose, --quiet, --config-file)
- [ ] 12.4 Implement signal handlers (SIGINT, SIGTERM)
- [ ] 12.5 Implement colored output with terminal detection
- [ ] 12.6 Implement progress bars for long operations
- [ ] 12.7 Implement error formatting and exit codes

## 13. CLI Layer - Start Command
- [ ] 13.1 Implement start command (voinux/cli/commands/start.py)
- [ ] 13.2 Add start command options (--lang, --model, --device, --continuous, --vad-threshold)
- [ ] 13.3 Implement real-time status display (listening, transcribing indicators)
- [ ] 13.4 Implement audio level meter (optional)
- [ ] 13.5 Implement session statistics on shutdown
- [ ] 13.6 Implement hotkey activation (if time permits)

## 14. CLI Layer - Config Commands
- [ ] 14.1 Implement config command group (voinux/cli/commands/config.py)
- [ ] 14.2 Implement config show subcommand
- [ ] 14.3 Implement config get subcommand
- [ ] 14.4 Implement config set subcommand with validation
- [ ] 14.5 Implement config reset subcommand with confirmation
- [ ] 14.6 Implement config edit subcommand (open in $EDITOR)

## 15. CLI Layer - Test Commands
- [ ] 15.1 Implement test-audio command (voinux/cli/commands/test.py)
- [ ] 15.2 Implement test-gpu command
- [ ] 15.3 Implement test-model command
- [ ] 15.4 Implement test-keyboard command
- [ ] 15.5 Add real-time feedback for all test commands

## 16. CLI Layer - Model Commands
- [ ] 16.1 Implement model command group (voinux/cli/commands/model.py)
- [ ] 16.2 Implement model download subcommand with progress
- [ ] 16.3 Implement model list subcommand with table formatting
- [ ] 16.4 Implement model info subcommand
- [ ] 16.5 Add --force flag for re-downloading models

## 17. CLI Layer - Setup Wizard
- [ ] 17.1 Implement setup command (voinux/cli/commands/setup.py)
- [ ] 17.2 Implement GPU/CUDA detection
- [ ] 17.3 Implement display server detection
- [ ] 17.4 Implement audio/keyboard capability checks
- [ ] 17.5 Implement model recommendation based on VRAM
- [ ] 17.6 Implement interactive prompts for configuration
- [ ] 17.7 Implement end-to-end test after setup
- [ ] 17.8 Implement setup summary display

## 18. Entry Points and Packaging
- [ ] 18.1 Create __main__.py for `python -m voinux` support
- [ ] 18.2 Configure entry_points in pyproject.toml for `voinux` command
- [ ] 18.3 Add package metadata (version, author, description, license)
- [ ] 18.4 List all dependencies with version constraints
- [ ] 18.5 Create extras for optional dependencies (cuda, rocm)

## 19. Testing - Unit Tests
- [ ] 19.1 Write tests for all domain entities (AudioChunk, TranscriptionResult, etc.)
- [ ] 19.2 Write tests for domain services with mocked ports
- [ ] 19.3 Write tests for configuration loading and validation
- [ ] 19.4 Write tests for adapter factories
- [ ] 19.5 Achieve >80% code coverage for domain and application layers

## 20. Testing - Integration Tests
- [ ] 20.1 Write integration tests for audio capture with mock hardware
- [ ] 20.2 Write integration tests for STT with test audio files
- [ ] 20.3 Write integration tests for keyboard simulation (stdout adapter)
- [ ] 20.4 Write integration tests for VAD with known speech/silence samples
- [ ] 20.5 Write integration tests for model download (mock HTTP)

## 21. Testing - System Tests
- [ ] 21.1 Write end-to-end test (audio → STT → keyboard) with mocks
- [ ] 21.2 Write CLI command tests using Click testing utilities
- [ ] 21.3 Test error handling for all major failure modes
- [ ] 21.4 Test configuration precedence (defaults → file → CLI → env)
- [ ] 21.5 Test graceful shutdown and resource cleanup

## 22. Documentation
- [ ] 22.1 Write README.md with installation instructions
- [ ] 22.2 Document system requirements and dependencies
- [ ] 22.3 Document GPU setup (CUDA/ROCm installation)
- [ ] 22.4 Document usage examples for all CLI commands
- [ ] 22.5 Write troubleshooting guide (common errors and fixes)
- [ ] 22.6 Document configuration options with examples
- [ ] 22.7 Create architecture diagram
- [ ] 22.8 Add docstrings to all public APIs

## 23. Performance Optimization
- [ ] 23.1 Profile audio capture latency
- [ ] 23.2 Profile STT inference latency
- [ ] 23.3 Optimize VAD to ensure <50ms processing time
- [ ] 23.4 Optimize keyboard typing latency
- [ ] 23.5 Tune audio chunk size for best latency/accuracy trade-off
- [ ] 23.6 Measure and optimize memory usage
- [ ] 23.7 Verify GPU utilization during transcription

## 24. Error Handling and Robustness
- [ ] 24.1 Add comprehensive error messages for all failure modes
- [ ] 24.2 Implement recovery strategies for transient failures
- [ ] 24.3 Add logging throughout the application
- [ ] 24.4 Ensure no crashes, only graceful errors
- [ ] 24.5 Test on different Linux distributions (Arch, Ubuntu, Fedora)

## 25. Continuous Mode Features
- [ ] 25.1 Implement continuous mode flag handling
- [ ] 25.2 Implement auto-restart on recoverable errors
- [ ] 25.3 Implement long-running session stability
- [ ] 25.4 Add signal handling for graceful shutdown in continuous mode

## 26. Polish and UX Improvements
- [ ] 26.1 Add color and formatting to all CLI output
- [ ] 26.2 Implement spinner/progress indicators for long operations
- [ ] 26.3 Add confirmation prompts for destructive operations
- [ ] 26.4 Implement helpful error messages with suggested fixes
- [ ] 26.5 Add ASCII banner on first run or help
- [ ] 26.6 Ensure all commands have comprehensive help text

## 27. Distribution and Packaging
- [ ] 27.1 Configure build system for PyPI distribution
- [ ] 27.2 Test installation via pip in clean environment
- [ ] 27.3 Create release script (version bump, tag, build, publish)
- [ ] 27.4 Write CHANGELOG.md for v1.0 release
- [ ] 27.5 Create GitHub releases with release notes
- [ ] 27.6 Consider AUR package for Arch Linux (future)

## 28. Final Validation
- [ ] 28.1 Run all tests and ensure they pass
- [ ] 28.2 Run type checker (mypy) with strict mode
- [ ] 28.3 Run linters (ruff, black) and fix issues
- [ ] 28.4 Verify all success criteria from proposal.md
- [ ] 28.5 Manual testing on fresh Ubuntu 22.04 VM
- [ ] 28.6 Manual testing on fresh Arch Linux VM
- [ ] 28.7 Manual testing on fresh Fedora 38 VM
- [ ] 28.8 Verify GPU acceleration works on NVIDIA GPU
- [ ] 28.9 Verify CPU fallback works
- [ ] 28.10 Verify both X11 and Wayland support
- [ ] 28.11 Performance verification: <2s latency, VAD reduces GPU usage by >50%
- [ ] 28.12 Security verification: config file permissions, no secrets logged

## Notes
- Tasks should be completed sequentially within each section
- Some tasks in different sections can be parallelized (e.g., adapters can be built concurrently)
- Mark each task as [x] when completed
- Add sub-tasks if a task becomes too large during implementation
- Continuously run tests as you implement to catch regressions early
