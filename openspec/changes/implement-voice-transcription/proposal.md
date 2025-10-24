# Implement Voice Transcription System

## Why

Linux users lack a privacy-focused, offline-capable voice typing solution that works system-wide. Commercial cloud-based solutions require constant internet connectivity, transmit sensitive audio data to third parties, and incur ongoing costs. Voinux addresses this by providing real-time voice-to-text transcription using local GPU-accelerated Whisper models, ensuring complete privacy, offline operation, and unlimited usage at zero recurring cost.

## What Changes

This proposal implements the complete Voinux v1.0 application from scratch with the following components:

- **Hexagonal Architecture**: Domain core with ports/interfaces and adapters for external dependencies, enabling clear separation of business logic from infrastructure
- **Audio Capture System**: Real-time microphone input with support for PipeWire, PulseAudio, and ALSA
- **Speech Recognition Engine**: Integration with faster-whisper for local GPU-accelerated transcription (CUDA/ROCm support)
- **Keyboard Simulation**: System-wide text typing via xdotool (X11) and ydotool (Wayland) with auto-detection
- **Voice Activation Detection**: VAD to detect speech start/stop, optimizing GPU usage and battery life
- **Model Management**: Automatic download, caching, and selection of Whisper models (tiny to large-v3-turbo)
- **CLI Interface**: Complete command-line interface with start, config, test, and model management commands
- **Configuration System**: YAML-based configuration with sensible defaults
- **Async Architecture**: asyncio-based pipeline for concurrent audio streaming and processing

### Key Features (v1.0)
- Real-time transcription with <2s latency
- GPU acceleration (NVIDIA CUDA, AMD ROCm) with CPU fallback
- 100+ language support with auto-detection
- System-wide voice typing (works in any application)
- Offline operation after initial model download
- VAD for power efficiency
- Configurable models (tiny/base/small/medium/large-v3/large-v3-turbo)
- INT8 quantization for reduced VRAM usage

## Impact

### Affected Specs
This change adds **7 new capabilities**:
- `audio-capture`: Audio input abstraction and implementations
- `speech-recognition`: Speech-to-text processing core
- `keyboard-simulation`: Keyboard output abstraction and implementations
- `voice-activation`: VAD integration for speech detection
- `model-management`: Whisper model download and caching
- `configuration`: YAML configuration management
- `cli-interface`: User-facing command-line interface

### Affected Code
This is a greenfield implementation creating:
- `voinux/domain/`: Core business logic (ports, entities, use cases)
- `voinux/adapters/`: Infrastructure implementations (audio, STT, keyboard)
- `voinux/application/`: Service layer orchestration
- `voinux/cli/`: Click-based CLI commands
- `voinux/config/`: Configuration management
- `tests/`: Comprehensive test suite

### Dependencies Added
- **Core**: Python ≥3.12, faster-whisper, torch (CUDA/ROCm), ctranslate2
- **Audio**: soundcard, pyaudio (fallback)
- **VAD**: webrtcvad
- **CLI**: click ≥8.0
- **Config**: pyyaml
- **Keyboard**: python-xdotool (subprocess calls to ydotool for Wayland)

### System Requirements
- Linux (Arch, Ubuntu, Fedora tested)
- PipeWire or PulseAudio
- X11 or Wayland
- NVIDIA GPU with 4-8GB VRAM (recommended) or AMD GPU with ROCm
- CUDA Toolkit 11.8+ (NVIDIA) or ROCm 5.0+ (AMD)
- External tools: xdotool (X11) or ydotool (Wayland)

## Breaking Changes
None - this is initial implementation.

## Migration Path
Not applicable - new application.

## Risks and Mitigations

### Risk: GPU/CUDA setup complexity
**Mitigation**:
- Provide clear setup instructions for CUDA/ROCm
- Auto-detect GPU and fall back to CPU gracefully
- Include `voinux test-gpu` command to verify setup

### Risk: faster-whisper is synchronous while we use asyncio
**Mitigation**:
- Run model inference in ThreadPoolExecutor with asyncio.run_in_executor()
- Maintain async architecture for audio I/O and coordination

### Risk: Wayland ydotool requires uinput permissions
**Mitigation**:
- Detect permissions during setup wizard
- Provide clear error messages with fix instructions
- Auto-detect X11/Wayland and use appropriate backend

### Risk: Model download size (1-2GB)
**Mitigation**:
- Download on first run with progress indicator
- Support manual download via `voinux model download`
- Cache models in `~/.cache/voinux/models`

### Risk: Real-time performance on CPU-only systems
**Mitigation**:
- Warn users that CPU mode has higher latency (>5s)
- Recommend GPU for real-time use
- Use smaller models (tiny/base) for CPU fallback

## Success Criteria

- [ ] User can install with `pip install voinux`
- [ ] Setup wizard (`voinux setup`) completes successfully on fresh system
- [ ] `voinux start` begins real-time transcription with <2s latency (GPU mode)
- [ ] Transcribed text types into active window (any application)
- [ ] Works on both X11 and Wayland display servers
- [ ] Supports Arch Linux, Ubuntu 22.04+, Fedora 38+
- [ ] GPU acceleration works with NVIDIA GPUs (8GB VRAM)
- [ ] CPU fallback mode available with degraded performance warning
- [ ] VAD reduces GPU usage by >50% during silence periods
- [ ] All CLI commands functional (start, config, test-*, model)
- [ ] Configuration persists in `~/.config/voinux/config.yaml`
- [ ] Comprehensive error messages with actionable solutions
- [ ] Documentation covers installation, usage, and troubleshooting
