# Technical Design: Voinux Voice Transcription System

## Context

Voinux is a real-time voice-to-text transcription CLI application for Linux that processes audio locally using GPU-accelerated Whisper models. The system must:

- Capture audio from microphone in real-time (16kHz, mono, 16-bit PCM)
- Process audio through faster-whisper with <2s latency
- Type transcribed text into any active Linux application
- Support multiple audio backends (PipeWire, PulseAudio, ALSA)
- Support multiple display servers (X11, Wayland)
- Handle GPU acceleration (CUDA, ROCm) with CPU fallback
- Operate offline after initial model download

### Stakeholders
- **End Users**: Linux users needing privacy-focused voice typing
- **Developers**: Contributors extending functionality
- **Packagers**: Distribution maintainers (PyPI, AUR)

### Constraints
- Python ≥3.12 (modern async features, type hints)
- faster-whisper is synchronous (requires thread pool integration)
- ydotool requires uinput permissions on Wayland
- GPU memory limits (4-8GB VRAM for real-time models)
- Real-time performance requirement (<2s latency)

## Goals / Non-Goals

### Goals
- Clear separation of domain logic from infrastructure (hexagonal architecture)
- Easy to test (mock external dependencies)
- Easy to extend (new audio backends, STT providers, keyboard drivers)
- Type-safe with comprehensive type hints
- Async-first for I/O operations
- Graceful degradation (GPU → CPU, with VAD → without VAD)

### Non-Goals
- GUI application (CLI only for v1.0)
- Windows/macOS support (Linux-first)
- Cloud STT providers (local-only for v1.0, cloud optional in future)
- Real-time streaming (chunk-based processing is sufficient)
- Plugin system (hardcoded adapters for v1.0)

## Architecture Overview

### Hexagonal (Ports and Adapters) Pattern

```
┌──────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (click commands, argument parsing, user interaction)        │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Application Layer                          │
│  (Use Cases: StartTranscription, ConfigureSystem, etc.)      │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                      Domain Core                             │
│                                                               │
│  Entities:                                                    │
│  - TranscriptionSession                                       │
│  - AudioChunk                                                 │
│  - TranscriptionResult                                        │
│  - ModelConfig                                                │
│                                                               │
│  Ports (Interfaces):                                          │
│  - IAudioCapture                                              │
│  - ISpeechRecognizer                                          │
│  - IKeyboardSimulator                                         │
│  - IVoiceActivationDetector                                   │
│  - IModelManager                                              │
│  - IConfigRepository                                          │
│                                                               │
│  Services:                                                    │
│  - TranscriptionPipeline                                      │
│  - SessionManager                                             │
└───────────────────┬────────────────────────┬─────────────────┘
                    │                        │
       ┌────────────▼────────────┐  ┌────────▼───────────────┐
       │   Input Adapters        │  │   Output Adapters      │
       │                         │  │                        │
       │  - SoundCardAudioCapture│  │  - XDotoolKeyboard     │
       │  - PyAudioCapture       │  │  - YDotoolKeyboard     │
       │  - WebRTCVAD            │  │  - StdoutKeyboard      │
       │  - WhisperRecognizer    │  │  - YAMLConfigRepo      │
       │  - ModelCache           │  │                        │
       └─────────────────────────┘  └────────────────────────┘
```

### Directory Structure

```
voinux/
├── domain/                      # Core business logic (no external dependencies)
│   ├── __init__.py
│   ├── entities.py              # TranscriptionSession, AudioChunk, etc.
│   ├── ports.py                 # Interface definitions (IAudioCapture, etc.)
│   └── services.py              # TranscriptionPipeline, SessionManager
│
├── adapters/                    # Infrastructure implementations
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── soundcard_adapter.py # SoundCardAudioCapture
│   │   └── pyaudio_adapter.py   # PyAudioCapture (fallback)
│   ├── stt/
│   │   ├── __init__.py
│   │   └── whisper_adapter.py   # WhisperRecognizer
│   ├── keyboard/
│   │   ├── __init__.py
│   │   ├── xdotool_adapter.py   # XDotoolKeyboard
│   │   ├── ydotool_adapter.py   # YDotoolKeyboard
│   │   └── stdout_adapter.py    # StdoutKeyboard (testing)
│   ├── vad/
│   │   ├── __init__.py
│   │   └── webrtc_adapter.py    # WebRTCVAD
│   ├── models/
│   │   ├── __init__.py
│   │   └── model_cache.py       # ModelCache (download, storage)
│   └── config/
│       ├── __init__.py
│       └── yaml_adapter.py      # YAMLConfigRepository
│
├── application/                 # Use cases and orchestration
│   ├── __init__.py
│   ├── use_cases.py             # StartTranscription, RunSetup, etc.
│   └── factories.py             # DI container, adapter creation
│
├── cli/                         # User interface
│   ├── __init__.py
│   ├── main.py                  # Click app entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── start.py             # start command
│   │   ├── config.py            # config subcommands
│   │   ├── test.py              # test-* commands
│   │   ├── model.py             # model subcommands
│   │   └── setup.py             # setup wizard
│   └── utils.py                 # CLI helpers, formatting
│
└── __main__.py                  # Entry point for `python -m voinux`

tests/
├── unit/
│   ├── domain/                  # Test domain logic with mocks
│   ├── adapters/                # Test adapters with fixtures
│   └── application/             # Test use cases
├── integration/                 # Test adapter combinations
└── system/                      # End-to-end tests
```

## Key Decisions

### Decision 1: Hexagonal Architecture

**What**: Separate domain logic from infrastructure using ports (interfaces) and adapters (implementations).

**Why**:
- **Testability**: Mock external dependencies easily
- **Flexibility**: Swap audio/keyboard/STT implementations without changing core logic
- **Clarity**: Clear boundaries between business rules and technical details
- **Future-proof**: Easy to add new adapters (e.g., cloud STT, new audio backends)

**Alternatives Considered**:
- **Layered Architecture**: Simpler but tight coupling between layers
- **Simple Module Separation**: Easy to start but becomes tangled as complexity grows

**Trade-offs**:
- More upfront abstraction (interface definitions)
- More files and indirection
- Worth it for maintainability and testability

### Decision 2: asyncio Throughout

**What**: Use async/await for all I/O operations and coordination.

**Why**:
- Audio capture is naturally async (streaming)
- Keyboard simulation can be non-blocking
- Allows concurrent VAD processing and transcription
- Modern Python idiom

**Handling faster-whisper (sync)**:
```python
# Run blocking model inference in thread pool
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    thread_pool_executor,
    model.transcribe,
    audio_chunk
)
```

**Alternatives Considered**:
- **Threading**: Simpler for sync libraries but harder to coordinate
- **Queue-based**: Good for decoupling but more complexity

**Trade-offs**:
- Need to wrap sync faster-whisper calls
- Slightly more complex than pure sync
- Better scalability for future features (multiple streams, web UI)

### Decision 3: Pipeline Architecture

**What**: Process audio through a pipeline of stages:
1. Audio Capture → 2. VAD Filter → 3. Speech Recognition → 4. Keyboard Output

**Why**:
- Clear data flow
- Easy to test each stage independently
- VAD can filter out silence before expensive GPU inference
- Natural async boundaries

**Implementation**:
```python
class TranscriptionPipeline:
    def __init__(
        self,
        audio_capture: IAudioCapture,
        vad: IVoiceActivationDetector,
        recognizer: ISpeechRecognizer,
        keyboard: IKeyboardSimulator,
    ):
        self.audio_capture = audio_capture
        self.vad = vad
        self.recognizer = recognizer
        self.keyboard = keyboard

    async def run(self):
        async for chunk in self.audio_capture.stream():
            if await self.vad.is_speech(chunk):
                result = await self.recognizer.transcribe(chunk)
                if result.text:
                    await self.keyboard.type_text(result.text)
```

**Alternatives Considered**:
- **Event Bus**: More decoupled but harder to reason about flow
- **Reactive Streams**: Powerful but overkill for linear pipeline

### Decision 4: Adapter Auto-Detection

**What**: Automatically detect and select best available adapter at runtime.

**Why**:
- Users shouldn't need to configure display server (X11/Wayland)
- Graceful fallback if preferred option unavailable
- Better user experience

**Implementation**:
```python
def create_keyboard_adapter(config: Config) -> IKeyboardSimulator:
    if config.keyboard.backend == "auto":
        display = os.environ.get("XDG_SESSION_TYPE", "")
        if display == "wayland" and ydotool_available():
            return YDotoolKeyboard()
        elif xdotool_available():
            return XDotoolKeyboard()
        else:
            return StdoutKeyboard()  # Fallback for testing
    # ... explicit backend selection
```

**Applies to**:
- Keyboard: xdotool → ydotool → stdout
- Audio: soundcard → pyaudio
- GPU: CUDA → ROCm → CPU

### Decision 5: Configuration Layers

**What**: Three-layer configuration system:
1. **Defaults** (hardcoded): Sensible defaults for most users
2. **Config File** (`~/.config/voinux/config.yaml`): User preferences
3. **CLI Arguments**: Runtime overrides

**Why**:
- Zero-config for common use cases
- Power users can customize
- CLI args for quick testing

**Precedence**: CLI args > Config file > Defaults

**Example**:
```yaml
# ~/.config/voinux/config.yaml
faster_whisper:
  model: "large-v3-turbo"
  device: "cuda"
  compute_type: "int8"

audio:
  sample_rate: 16000
  chunk_duration_ms: 100

vad:
  enabled: true
  threshold: 0.5
```

### Decision 6: Model Management

**What**: Automatic model download on first run with manual override.

**Why**:
- Better UX (no manual download steps)
- Cache models in standard location (`~/.cache/voinux/models`)
- Reuse models if already downloaded by other tools

**Implementation**:
- Use `faster_whisper.download_model()` utility
- Show progress bar for large downloads (1-2GB)
- Validate model integrity (hash check)
- Support offline mode (skip download if model exists)

**Commands**:
```bash
voinux model download large-v3-turbo  # Manual download
voinux model list                     # Show cached models
voinux model info                     # Current model stats
```

### Decision 7: Error Handling Strategy

**What**: Domain exceptions with adapter-specific wrapping.

**Why**:
- Domain code throws domain exceptions (`AudioCaptureError`, `TranscriptionError`)
- Adapters catch library-specific exceptions and wrap them
- CLI layer handles all exceptions and shows user-friendly messages

**Example**:
```python
# Domain
class AudioCaptureError(Exception):
    """Base exception for audio capture failures"""

# Adapter
class SoundCardAudioCapture(IAudioCapture):
    async def stream(self):
        try:
            # soundcard library code
        except soundcard.SoundcardException as e:
            raise AudioCaptureError(f"Failed to capture audio: {e}")

# CLI
try:
    await use_case.start_transcription()
except AudioCaptureError as e:
    click.echo(f"Error: {e}", err=True)
    click.echo("Try: arecord -l  # List audio devices")
    sys.exit(1)
```

### Decision 8: Testing Strategy

**What**: Three-tier testing:
1. **Unit Tests**: Test domain logic with mocked ports (fast, isolated)
2. **Integration Tests**: Test adapters with real dependencies (slower, environment-specific)
3. **System Tests**: End-to-end with all components (slowest, most realistic)

**Why**:
- Fast feedback loop with unit tests
- Confidence in adapter behavior with integration tests
- Realistic scenarios with system tests

**Mocking Strategy**:
- Use `unittest.mock` for unit tests
- Use `pytest-asyncio` for async tests
- Use fixtures for integration tests (real but controlled environment)

## Data Flow

### Startup Sequence
1. CLI parses arguments
2. Application layer loads configuration (file + CLI args)
3. Factory creates adapters based on config and auto-detection
4. Domain services initialized with adapters
5. Use case orchestrates the pipeline

### Transcription Loop
```
┌──────────────┐
│ AudioCapture │
│ (100ms chunks)│
└───────┬──────┘
        │ AudioChunk
        ▼
┌──────────────┐
│     VAD      │◀── threshold
│ (is_speech?) │
└───────┬──────┘
        │ (if speech detected)
        ▼
┌──────────────┐
│   Whisper    │◀── model, device, compute_type
│  Recognizer  │
└───────┬──────┘
        │ TranscriptionResult
        ▼
┌──────────────┐
│   Keyboard   │
│  Simulator   │
└──────────────┘
```

### Configuration Flow
```
Defaults (code) → Config File (~/.config) → CLI Args
                      ↓
                Final Config
                      ↓
            Adapter Factories
                      ↓
                Domain Services
```

## Performance Considerations

### Latency Budget (<2s total)
- Audio capture: <100ms (buffering)
- VAD processing: <50ms (lightweight)
- Model inference: 500-1500ms (GPU, depends on chunk size and model)
- Keyboard typing: <50ms (instant paste mode)
- **Total**: ~700-1700ms (within budget)

### Memory Usage
- Audio buffer: ~200KB (100ms chunks × ringbuffer)
- VAD state: ~1MB
- Whisper model (GPU VRAM):
  - tiny/base: 500MB-1GB
  - small: 1-2GB
  - medium: 2.5-5GB
  - large-v3-turbo (INT8): 5-6GB
- Python overhead: 50-100MB
- **Total RAM**: ~200MB (excluding model in VRAM)

### CPU/GPU Usage
- Audio capture: <1% CPU
- VAD: 1-2% CPU
- Whisper (GPU): 50-80% GPU utilization during speech
- Whisper (CPU fallback): 100% CPU, 5-10s latency (not real-time)

### Optimization Strategies
1. **VAD reduces GPU usage by 50%+** during silence
2. **INT8 quantization** reduces VRAM by ~50% with minimal accuracy loss
3. **Chunk size tuning**: 500ms-1s chunks balance latency and accuracy
4. **Model caching**: Load model once at startup (2-5s cost)
5. **Thread pool size**: 1 thread for model inference (avoid memory duplication)

## Risks / Trade-offs

### Risk: faster-whisper blocking GPU
**Mitigation**: Run in ThreadPoolExecutor with single thread to avoid context switching overhead. Monitor GPU utilization.

### Risk: Audio buffer overrun
**Mitigation**: Use asyncio queues with bounded size. Drop oldest chunks if queue full (with warning log).

### Risk: Wayland permission issues
**Mitigation**: Detect missing uinput permissions during setup. Provide clear instructions. Fall back to stdout if can't type.

### Risk: Model download failure
**Mitigation**: Retry with exponential backoff. Support manual download and sideload. Cache partial downloads.

### Risk: Inconsistent audio backends across distros
**Mitigation**: Auto-detect and try soundcard → pyaudio → ALSA in order. Provide `test-audio` command to diagnose issues.

## Migration Plan

Not applicable - initial implementation.

## Rollout Plan

1. **Phase 1**: Core implementation (audio, STT, keyboard)
2. **Phase 2**: VAD and model management
3. **Phase 3**: CLI polish and setup wizard
4. **Phase 4**: Testing across distros (Arch, Ubuntu, Fedora)
5. **Phase 5**: Package and publish (PyPI, AUR)

## Open Questions

1. **Should we support multiple concurrent transcription sessions?**
   - **Leaning**: No for v1.0 (single session only). Add in v2.0 if requested.

2. **Should we log audio data for debugging?**
   - **Leaning**: No (privacy-first). Only log text transcriptions if user opts in via config.

3. **Should we support custom model paths (fine-tuned models)?**
   - **Leaning**: Yes, via config `faster_whisper.model_path`. Document in advanced usage.

4. **Should we implement rate limiting for keyboard typing?**
   - **Leaning**: No for v1.0. Type as fast as possible (instant mode). Add configurable delay if users report issues.

5. **Should we support streaming transcription (partial results)?**
   - **Leaning**: Not in v1.0 (faster-whisper doesn't support it well). Consider in v2.0 with different backend.
