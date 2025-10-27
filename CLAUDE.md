# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voinux is a privacy-focused, **offline-first** voice typing solution for Linux that uses GPU-accelerated Whisper models for real-time speech-to-text transcription. It's designed to work system-wide with any application.

**Key Features:**
- Real-time transcription with <2s latency on GPU
- **100% offline by default** (Whisper local models)
- **Optional cloud providers** (Gemini) with explicit opt-in for advanced features
- **Silence trimming** for cloud providers to reduce costs and data usage
- GPU acceleration (NVIDIA CUDA, AMD ROCm) with CPU fallback
- 100+ languages supported
- System-wide keyboard typing (X11/Wayland)
- Hexagonal architecture for clean separation of concerns

**IMPORTANT PHILOSOPHY:** Voinux is **offline-first** by design. Cloud providers are optional, require explicit user opt-in, and never change the default offline behavior. See ADR 003 for details.

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests with coverage (using uv script)
uv run test

# Or run pytest directly
uv run pytest

# Run specific test file
uv run pytest tests/unit/domain/test_entities.py

# Run specific test
uv run pytest tests/unit/domain/test_entities.py::TestAudioChunk::test_creation

# Run with verbose output
uv run pytest -v

# Run integration tests only
uv run pytest tests/integration/

# Run unit tests only
uv run pytest tests/unit/
```

### Code Quality

**IMPORTANT: All code changes MUST be formatted and pass linting before committing.**

The project uses **Ruff** for both linting and formatting (fast, modern, all-in-one tool) and **mypy** for strict type checking.

**Quick one-liner to run all checks:**
```bash
# Format, lint with auto-fix, and type check
uvx ruff format voinux && uvx ruff check --fix voinux && uv run mypy voinux
```

**Individual commands:**
```bash
# Format code (replaces Black, 10-100x faster)
uvx ruff format voinux

# Check formatting without making changes
uvx ruff format --check voinux

# Linting - check for issues
uvx ruff check voinux

# Linting - auto-fix issues where possible
uvx ruff check voinux --fix

# Type checking with mypy (strict mode) - runs in uv environment
uv run mypy voinux

# Run tests
uv run pytest
```

**Note:** `uv run mypy` ensures mypy has access to all project dependencies for accurate type checking.

**Linting Rules:**
The project uses comprehensive linting rules including:
- **E, F, W**: Pycodestyle errors, Pyflakes, warnings
- **I**: Import sorting (isort-compatible)
- **N**: PEP8 naming conventions
- **UP**: Python upgrade suggestions
- **B**: Bugbear (common bugs/design problems)
- **C4**: Comprehensions (list/dict/set comprehension improvements)
- **SIM**: Simplify (code simplification suggestions)
- **PL**: Pylint rules (code quality)
- **PERF**: Performance anti-patterns
- **RUF**: Ruff-specific rules
- **A**: Avoid shadowing Python builtins
- **PT**: Pytest style guidelines
- **ARG**: Unused arguments detection
- **PTH**: Prefer pathlib over os.path
- **TRY**: Exception handling best practices

**Workflow for AI Agents:**
1. Make code changes
2. Run `uvx ruff format voinux && uvx ruff check --fix voinux && uv run mypy voinux` to format, lint, and type-check
3. Fix any remaining issues manually
4. Run `uv run pytest` to ensure tests pass
5. Commit changes

**Quick check before committing:**
```bash
# One command to check everything (format + lint + type check)
uvx ruff format voinux && uvx ruff check --fix voinux && uv run mypy voinux
```

**Optional: Git pre-commit hook**
If you want automatic checks before commits, create `.git/hooks/pre-commit` manually:
```bash
#!/bin/sh
uvx ruff format voinux && uvx ruff check --fix voinux && uv run mypy voinux
```
Then make it executable: `chmod +x .git/hooks/pre-commit`

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

# Start voice transcription (default: offline Whisper)
voinux start

# Start with specific options
voinux start --model base --language en --device cpu

# Use cloud provider (requires explicit opt-in)
voinux start --provider gemini  # Shows privacy warning on first use

# Enable silence trimming to reduce cloud API costs (auto-enabled for cloud providers)
voinux start --provider gemini --enable-silence-trimming

# Disable silence trimming for cloud providers (if you need full audio context)
voinux start --provider gemini --no-silence-trimming

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
   - `audio/`: Audio capture (SoundCard, PyAudio) and processing (SilenceTrimmer, CompositeAudioProcessor)
   - `stt/`: Speech-to-text adapters (Whisper via faster-whisper, Gemini for cloud)
   - `keyboard/`: Keyboard simulation adapters (xdotool for X11, ydotool for Wayland, stdout for testing)
   - `vad/`: Voice activation detection (WebRTC VAD)
   - `noise/`: Noise reduction (noisereduce library)
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
AudioCapture (100ms chunks) → [Audio Processing*] → VAD (is_speech?) → Buffering → [Silence Trimming*] → Recognizer → Keyboard Simulator
```

*Audio Processing (optional): Noise reduction and/or silence trimming
- Noise reduction: Applied to each chunk (if enabled)
- Silence trimming: Applied to buffered utterances before transcription (auto-enabled for cloud providers)

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

6. **Composable Audio Processing**: Audio processors (noise reduction, silence trimming) implement `IAudioProcessor` interface and can be chained using `CompositeAudioProcessor` for flexible audio preprocessing pipelines

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

6. **Silence Trimming for Cloud Providers**: Automatically enabled for cloud STT providers (Gemini) to reduce API costs and data usage. Uses RMS energy-based detection to trim leading/trailing silence from buffered utterances before sending to API. Can be explicitly controlled via `--enable-silence-trimming` / `--no-silence-trimming` CLI flags. Default threshold: -40dB, minimum preserved audio: 100ms.

## Configuration File Location

User configuration: `~/.config/voinux/config.yaml`

## Technical Documentation & Architecture Decision Records

### Architecture Decision Records (ADRs)

Important architectural decisions are documented in `docs/adr/`:

- **ADR 001**: Add Cloud Provider Support - Decision to support optional cloud STT providers
- **ADR 002**: Choose Gemini as First Cloud Provider - Selection of Google Gemini Flash 2.5
- **ADR 003**: Maintain Offline-First Philosophy - **CRITICAL: Read this before any cloud-related work**
- **ADR 004**: API Key Management - Secure handling of cloud provider credentials

### Cloud Provider Guidelines

When working with cloud providers:

1. **Default is Always Offline**: Never auto-select cloud providers
2. **Explicit Opt-In Required**: Users must explicitly choose `--provider gemini`
3. **Privacy Warnings**: First-time cloud usage must show privacy notice
4. **No Feature Gating**: Core functionality must work offline
5. **Clear Documentation**: Cloud features marked as optional in all docs

See `docs/adr/003-maintain-offline-first.md` for complete requirements.

### Specifications

Detailed technical specs are in `docs/specs/`:
- Gemini integration specifications and implementation guides
- API integration references
- Testing strategies

### Documentation Structure

The `docs/` directory contains:
- `adr/` - Architecture Decision Records (see above)
- `specs/` - Technical specifications for major features
- `README.md` - Documentation index and contributor guide

Always check existing ADRs before proposing architectural changes.
