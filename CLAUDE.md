# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Project Overview

Voinux is a privacy-focused, offline voice typing solution for Linux that uses GPU-accelerated Whisper models for real-time speech-to-text transcription. It's designed to work system-wide with any application.

**Key Features:**
- Real-time transcription with <2s latency on GPU
- 100% offline operation (no cloud services)
- GPU acceleration (NVIDIA CUDA, AMD ROCm) with CPU fallback
- 100+ languages supported
- System-wide keyboard typing (X11/Wayland)
- Hexagonal architecture for clean separation of concerns

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/domain/test_entities.py

# Run specific test
pytest tests/unit/domain/test_entities.py::TestAudioChunk::test_creation

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/

# Run unit tests only
pytest tests/unit/
```

### Code Quality
```bash
# Type checking
mypy voinux

# Linting
ruff check voinux

# Auto-fix linting issues
ruff check voinux --fix

# Formatting
black voinux

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Running the Application
```bash
# Initialize configuration
voinux config init

# Test GPU availability
voinux test-gpu

# Test audio capture
voinux test-audio

# Test keyboard simulation
voinux test-keyboard

# Start voice transcription
voinux start

# Start with specific options
voinux start --model base --language en --device cpu

# List cached models
voinux model list

# Download a specific model
voinux model download large-v3-turbo
```

## Architecture

Voinux follows **hexagonal (ports and adapters) architecture** to maintain clean separation between domain logic and infrastructure.

### Core Layers

1. **Domain Layer** (`voinux/domain/`)
   - Core business logic with no external dependencies
   - `entities.py`: Core domain entities (AudioChunk, TranscriptionResult, ModelConfig, TranscriptionSession)
   - `ports.py`: Port interfaces defining contracts (IAudioCapture, ISpeechRecognizer, IKeyboardSimulator, IVoiceActivationDetector, IModelManager, IConfigRepository)
   - `services.py`: Domain services (TranscriptionPipeline, SessionManager)
   - `exceptions.py`: Domain-specific exceptions

2. **Adapters Layer** (`voinux/adapters/`)
   - Infrastructure implementations of port interfaces
   - `audio/`: Audio capture adapters (SoundCard, PyAudio)
   - `stt/`: Speech-to-text adapters (Whisper via faster-whisper)
   - `keyboard/`: Keyboard simulation adapters (xdotool for X11, ydotool for Wayland, stdout for testing)
   - `vad/`: Voice activation detection (WebRTC VAD)
   - `models/`: Model management and caching
   - `config/`: Configuration persistence (YAML)

3. **Application Layer** (`voinux/application/`)
   - Use cases and orchestration
   - `use_cases.py`: Application use cases (StartTranscription, TestAudio, TestGPU)
   - `factories.py`: Dependency injection and adapter creation with auto-detection

4. **CLI Layer** (`voinux/cli/`)
   - User interface using Click framework
   - `main.py`: CLI entry point and command registration
   - `commands/`: Individual CLI commands (start, config, test, model)

### Data Flow

The transcription pipeline follows this flow:
```
AudioCapture (100ms chunks) → VAD (is_speech?) → Whisper Recognizer → Keyboard Simulator
```

### Configuration Layers

Configuration uses three-layer precedence:
1. **Defaults** (hardcoded in code)
2. **Config File** (`~/.config/voinux/config.yaml`)
3. **CLI Arguments** (runtime overrides)

CLI args > Config file > Defaults

### Adapter Auto-Detection

The system automatically detects and selects the best available adapter:
- **Keyboard**: ydotool (Wayland) → xdotool (X11) → stdout (testing)
- **Audio**: soundcard → pyaudio (future)
- **GPU**: CUDA → ROCm → CPU

## Key Design Decisions

1. **Hexagonal Architecture**: Enables easy testing with mocked ports and allows swapping implementations without changing domain logic

2. **Asyncio Throughout**: All I/O operations use async/await for non-blocking coordination. Note: faster-whisper is synchronous and runs in ThreadPoolExecutor

3. **Pipeline Architecture**: Clear data flow through stages (Capture → VAD → Recognition → Output) with independent testing for each stage

4. **Domain Entities are Frozen Dataclasses**: All domain entities (AudioChunk, TranscriptionResult, ModelConfig) are immutable with validation in `__post_init__`

5. **Error Handling**: Domain code throws domain-specific exceptions (AudioCaptureError, TranscriptionError), adapters wrap library-specific exceptions, CLI layer handles all exceptions with user-friendly messages

## Testing Strategy

Three-tier testing approach:
- **Unit Tests** (`tests/unit/`): Test domain logic with mocked ports (fast, isolated)
- **Integration Tests** (`tests/integration/`): Test adapters with real dependencies (slower, environment-specific)
- **System Tests** (`tests/system/`): End-to-end tests with all components (slowest, most realistic)

Use `pytest-asyncio` for async tests and `unittest.mock` for mocking.

## Important Implementation Notes

1. **Performance Budget**: Target <2s total latency (audio capture <100ms, VAD <50ms, model inference 500-1500ms, keyboard <50ms)

2. **VAD Optimization**: VAD filtering reduces GPU usage by 50%+ during silence periods

3. **Model Inference**: faster-whisper runs synchronously, so it's executed in ThreadPoolExecutor to avoid blocking the event loop

4. **Session Management**: SessionManager ensures only one transcription session is active at a time. Sessions track statistics (chunks processed, transcription times, characters typed, VAD efficiency)

5. **Model Caching**: Models are cached in `~/.cache/voinux/models` and downloaded automatically on first use

## Configuration File Location

User configuration: `~/.config/voinux/config.yaml`

## Technical Documentation

For detailed architecture and design decisions, see: `openspec/changes/implement-voice-transcription/design.md`
