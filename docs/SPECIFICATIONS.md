# Voinux - Real-time Voice Transcription CLI Application

## Project Overview

**Voinux** is a command-line interface (CLI) application for real-time voice-to-text transcription on Linux systems. The application captures audio from the microphone, processes it using local GPU-accelerated Whisper models, and types the transcribed text directly into any active application using keyboard simulation.

**Primary Use Case**: Privacy-focused voice typing/dictation for any Linux application
**Target Platform**: Linux (with primary focus on modern distributions using PipeWire/PulseAudio)
**Backend**: faster-whisper (local GPU-accelerated OpenAI Whisper models)
**Key Benefits**: Free, offline-capable, private, unlimited usage

---

## Goals and Objectives

### Primary Goals
1. **Real-time transcription** with minimal latency (<2 seconds)
2. **System-wide voice typing** that works with any application
3. **High accuracy** transcription using Google's Chirp 3 model
4. **Simple CLI interface** for easy usage and integration
5. **Linux-first design** with proper audio stack integration

### Secondary Goals
1. Support for multiple languages (100+ via Google Cloud)
2. Configurable voice activation detection (VAD)
3. Keyboard shortcut activation
4. Low resource usage
5. Offline fallback option (future enhancement)

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Voinux CLI                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ Audio Capture│    │ Speech-to-Text   │    │   Keyboard   │
│   Module     │───▶│   Processing     │───▶│  Simulation  │
│              │    │                  │    │              │
│ PipeWire/    │    │ faster-whisper   │    │ ydotool/     │
│ PulseAudio   │    │ Local GPU/CUDA   │    │ xdotool      │
└──────────────┘    └──────────────────┘    └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ VAD Detection│    │ Text Processing  │    │ Active Window│
│ (optional)   │    │ & Formatting     │    │   Target     │
└──────────────┘    └──────────────────┘    └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Whisper Model  │
                    │  (Large-v3/Turbo)│
                    │   Cached Locally │
                    └──────────────────┘
```

### Audio Processing Pipeline

1. **Audio Capture** (16kHz, 16-bit, mono)
   - Capture from default microphone
   - Buffer audio in 100-200ms chunks
   - Optional: VAD to detect speech start/stop

2. **Local Inference**
   - Load Whisper model into GPU memory (one-time)
   - Process audio chunks through faster-whisper
   - GPU acceleration via CUDA (NVIDIA) or ROCm (AMD)
   - Generate transcription with <2s latency

3. **Text Processing**
   - Receive transcription results from local model
   - Built-in punctuation and capitalization
   - Apply text formatting and cleanup

4. **Keyboard Simulation**
   - Type final transcription into active window
   - Support for both X11 (xdotool) and Wayland (ydotool)

---

## Features and Requirements

### Core Features (v1.0)

#### 1. Real-time Audio Capture
- **Audio Source**: System microphone (default input device)
- **Format**: PCM 16-bit, 16kHz, mono
- **Compatibility**: PipeWire, PulseAudio, ALSA
- **Buffering**: Configurable chunk size (default 100ms)

#### 2. faster-whisper Integration (Local GPU)
- **Model**: Whisper Large-v3 or Large-v3-Turbo
- **Mode**: Local real-time inference with GPU acceleration
- **Language**: 100+ languages (auto-detect or specify)
- **Features**:
  - GPU acceleration via CUDA (NVIDIA) or ROCm (AMD)
  - Automatic punctuation and capitalization
  - Word-level timestamps
  - Model quantization (INT8) for reduced VRAM
  - CPU fallback if GPU unavailable
  - Offline operation (no internet required)

#### 3. Voice Activation Detection (VAD)
- **Purpose**: Detect speech start/stop to optimize processing
- **Implementation**: Local VAD before inference
- **Benefits**:
  - Reduces GPU usage during silence
  - Improves battery life
  - Better user experience (no silence processed)
  - Lower power consumption

#### 4. Keyboard Simulation
- **X11 Support**: xdotool for typing
- **Wayland Support**: ydotool for typing
- **Auto-detection**: Detect display server and use appropriate tool
- **Typing Speed**: Configurable (default: instant paste)

#### 5. CLI Interface
```bash
# Basic usage
voinux start                        # Start listening and typing
voinux start --lang es-ES           # Specify language
voinux start --continuous           # Continuous mode (always on)

# Configuration
voinux config set language en-US
voinux config set model large-v3-turbo
voinux config set device cuda       # or cpu, rocm
voinux config show

# Testing
voinux test-audio                   # Test microphone capture
voinux test-gpu                     # Test GPU/CUDA availability
voinux test-model                   # Test model inference
voinux test-keyboard                # Test keyboard simulation

# Model Management
voinux model download large-v3      # Download specific model
voinux model list                   # List available models
voinux model info                   # Show current model info

# Advanced
voinux start --hotkey "ctrl+alt+v"  # Activate with hotkey
voinux start --vad-threshold 0.5    # Set VAD sensitivity
voinux start --model medium         # Use different model
voinux start --device cpu           # Force CPU mode
```

### Configuration Options

```yaml
# ~/.config/voinux/config.yaml

# faster-whisper Settings
faster_whisper:
  model: "large-v3-turbo"  # tiny, base, small, medium, large-v2, large-v3, large-v3-turbo
  device: "cuda"           # cuda, cpu, rocm, auto
  compute_type: "int8"     # float16, int8 (int8 reduces VRAM usage)
  language: "en"           # ISO language code or "auto" for auto-detect
  model_cache_dir: "~/.cache/voinux/models"
  num_workers: 1           # Parallel transcription workers

  # Performance tuning
  beam_size: 5             # Higher = more accurate but slower (1-10)
  best_of: 5               # Number of candidates to consider
  vad_filter: true         # Use built-in VAD filter

# Audio Settings
audio:
  sample_rate: 16000
  channels: 1
  chunk_duration_ms: 100
  device: "default"  # or specific device name

# Voice Activation Detection (External, before model)
vad:
  enabled: true
  threshold: 0.5
  silence_duration_ms: 1000  # Stop after 1s of silence

# Keyboard Simulation
keyboard:
  backend: "auto"  # auto, xdotool, ydotool
  typing_delay_ms: 0

# Application Behavior
app:
  continuous_mode: false
  log_level: "info"
  hotkey: null  # e.g., "ctrl+alt+v"

# Cloud Providers (Optional fallback/alternative)
cloud_providers:
  enabled: false

  deepgram:
    api_key: null
    model: "nova-2"

  azure:
    api_key: null
    region: "eastus"
```

---

## Technology Stack

### Core Dependencies

| Component | Library | Purpose | Version |
|-----------|---------|---------|---------|
| **Language** | Python | Core implementation | ≥3.12 |
| **STT Engine** | faster-whisper | GPU-accelerated Whisper inference | Latest |
| **GPU Runtime** | torch | PyTorch for CUDA support | ≥2.0 |
| **GPU Acceleration** | ctranslate2 | Optimized transformer inference | Latest |
| **Audio Capture** | soundcard | Cross-platform audio I/O | Latest |
| **Alternative Audio** | pyaudio | Audio I/O (fallback) | Latest |
| **VAD** | webrtcvad | Voice activity detection | Latest |
| **CLI Framework** | click | Command-line interface | ≥8.0 |
| **Keyboard (X11)** | python-xdotool | X11 keyboard simulation | Latest |
| **Keyboard (Wayland)** | subprocess | Call ydotool binary | N/A |
| **Config** | pyyaml | Configuration management | Latest |
| **Async** | asyncio | Async/await support | stdlib |

### System Requirements

- **OS**: Linux (tested on: Arch, Ubuntu, Fedora)
- **Audio Server**: PipeWire (recommended) or PulseAudio
- **Display Server**: X11 or Wayland
- **Python**: 3.12 or higher
- **GPU** (Recommended): NVIDIA GPU with 4-8GB VRAM
  - CUDA Toolkit 11.8+ (for NVIDIA GPUs)
  - ROCm 5.0+ (for AMD GPUs)
- **Internet**: Required only for initial model download (1-2GB one-time)
- **Disk Space**: 2-3GB for model storage
- **External Tools**:
  - `xdotool` (for X11 users)
  - `ydotool` (for Wayland users, requires uinput permissions)

### GPU Requirements by Model

| Model | VRAM (FP16) | VRAM (INT8) | Speed | Accuracy |
|-------|-------------|-------------|-------|----------|
| **tiny** | ~1GB | ~500MB | Very Fast | Good |
| **base** | ~1GB | ~500MB | Very Fast | Good |
| **small** | ~2GB | ~1GB | Fast | Better |
| **medium** | ~5GB | ~2.5GB | Medium | Great |
| **large-v3** | ~10GB | ~5GB | Slower | Excellent |
| **large-v3-turbo** | ~10GB | ~5GB | Fast | Excellent |

**Note**: CPU-only mode is available but slower (not recommended for real-time use)

### Initial Setup

1. Install CUDA Toolkit (NVIDIA) or ROCm (AMD)
2. Install PyTorch with GPU support:
   ```bash
   # NVIDIA
   pip install torch --index-url https://download.pytorch.org/whl/cu118

   # AMD (ROCm)
   pip install torch --index-url https://download.pytorch.org/whl/rocm5.6
   ```
3. Install Voinux:
   ```bash
   pip install voinux
   ```
4. Download model (automatic on first run, or manual):
   ```bash
   voinux model download large-v3-turbo
   ```

---

## Local Inference Integration

### faster-whisper Usage

#### Basic Setup
```python
from faster_whisper import WhisperModel

# Initialize model (one-time, loads to GPU)
model = WhisperModel(
    model_size_or_path="large-v3-turbo",
    device="cuda",              # or "cpu", "auto"
    compute_type="int8",        # or "float16", "float32"
    download_root="~/.cache/voinux/models",
)

# Transcribe audio
segments, info = model.transcribe(
    audio_data,
    language="en",              # or None for auto-detect
    beam_size=5,
    best_of=5,
    vad_filter=True,            # Built-in VAD
    word_timestamps=True,
)

# Process results
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

#### Real-time Streaming Setup
```python
import numpy as np
from faster_whisper import WhisperModel

# Initialize once
model = WhisperModel("large-v3-turbo", device="cuda", compute_type="int8")

# Process audio chunks in real-time
def process_audio_chunk(audio_chunk: np.ndarray):
    """
    Process a chunk of audio (16kHz, mono, float32)
    Returns transcription text
    """
    segments, _ = model.transcribe(
        audio_chunk,
        language="en",
        beam_size=5,
        vad_filter=True,
    )

    # Get first segment (real-time mode)
    for segment in segments:
        return segment.text
    return ""

# In your audio capture loop:
while capturing:
    chunk = capture_audio(duration_ms=500)  # 500ms chunks
    text = process_audio_chunk(chunk)
    if text:
        type_text_to_keyboard(text)
```

#### Performance Considerations
- **Model Loading**: 2-5 seconds one-time cost
- **Inference Latency**:
  - Medium model: 0.5-1s per chunk
  - Large-v3-turbo: 1-2s per chunk
- **VRAM Usage**:
  - INT8 quantization reduces VRAM by ~50%
  - Recommended for 8GB GPUs
- **Chunk Size**: 500ms-2s recommended for real-time

#### Cost Analysis
- **Hardware Cost**: One-time GPU purchase (or use existing)
- **Operating Cost**: ~50-80W power consumption during use
- **Monthly Cost**: $0 (after initial hardware)
- **Comparison**: vs $0.006/15s for Google Cloud = ~$17/hour of use

---

## Implementation Plan

### Phase 1: Core Audio Capture (Week 1)
- [ ] Set up Python project structure
- [ ] Implement audio capture with soundcard/pyaudio
- [ ] Test microphone access on different Linux systems
- [ ] Implement basic audio buffering and chunking
- [ ] Add audio format validation (16kHz, mono, 16-bit)

### Phase 2: faster-whisper Integration (Week 2)
- [ ] Install and test CUDA/PyTorch setup
- [ ] Integrate faster-whisper library
- [ ] Implement model loading and GPU initialization
- [ ] Create real-time audio chunk processing pipeline
- [ ] Test with various audio inputs and GPU configurations
- [ ] Implement model auto-download on first run

### Phase 3: Keyboard Simulation (Week 3)
- [ ] Detect display server (X11/Wayland)
- [ ] Implement xdotool integration
- [ ] Implement ydotool integration
- [ ] Handle special characters and formatting
- [ ] Test typing in various applications

### Phase 4: VAD and Optimization (Week 4)
- [ ] Integrate webrtcvad
- [ ] Implement silence detection
- [ ] Optimize audio buffering and GPU memory usage
- [ ] Add performance metrics (latency, GPU usage, VRAM)
- [ ] Memory and GPU profiling
- [ ] Test CPU fallback mode

### Phase 5: CLI and Configuration (Week 5)
- [ ] Build CLI with click
- [ ] Implement configuration management
- [ ] Add testing commands (test-gpu, test-model, test-audio)
- [ ] Add model management commands (download, list, info)
- [ ] Create setup wizard for first-time users (GPU detection, model download)
- [ ] Add logging and debugging options

### Phase 6: Polish and Testing (Week 6)
- [ ] Comprehensive testing on multiple distros
- [ ] Performance optimization
- [ ] Documentation (README, usage examples)
- [ ] Error messages and user feedback
- [ ] Package for distribution (PyPI, AUR, etc.)

---

## Security and Privacy Considerations

### Data Handling (Privacy-First Design)
1. **Audio data**: Processed entirely on local machine, **never transmitted to cloud**
2. **Transcripts**: Not logged by default (configurable for user's own records)
3. **Model files**: Stored locally in user's cache directory
4. **Configuration**: Stored in user config directory (0600 permissions)
5. **No telemetry**: No usage data, analytics, or tracking

### Permissions Required
- **Microphone access**: Required for audio capture
- **uinput device**: Required for ydotool on Wayland (needs user in `input` group)
- **GPU access**: Required for CUDA acceleration (optional, CPU fallback available)
- **Network access**: Only for initial model download (can be done offline with manual download)

### Security Best Practices
1. Validate all configuration inputs
2. Sanitize text before keyboard simulation (prevent injection attacks)
3. Use secure file permissions (0600) for configuration files
4. Regular model updates for security patches
5. Optional: Run in sandboxed environment (containers, firejail)

### Privacy Advantages vs Cloud Solutions
| Aspect | Local (Voinux) | Cloud APIs |
|--------|----------------|------------|
| **Data Transmission** | None | All audio sent to cloud |
| **Data Storage** | Local only | May be stored/logged |
| **Third-party Access** | None | Service provider has access |
| **Compliance** | Inherent (GDPR, HIPAA) | Depends on provider |
| **Internet Required** | No (after setup) | Yes, always |
| **Offline Use** | ✅ Full functionality | ❌ Not possible |

---

## User Experience Flow

### First-time Setup
```bash
# 1. Install system dependencies (CUDA for NVIDIA)
# See GPU setup instructions above

# 2. Install voinux
pip install voinux  # or from AUR

# 3. Run setup wizard
voinux setup
# - Detect GPU and CUDA availability
# - Download Whisper model (large-v3-turbo recommended)
# - Test microphone access
# - Detect display server (X11/Wayland)
# - Configure keyboard backend
# - Run end-to-end transcription test

# 4. Start using
voinux start
```

### Typical Usage Session
```bash
# Start voinux
voinux start

# [Speaking] User says: "Hello world, this is a test."
# [Interim] "hello world"
# [Interim] "hello world this is a"
# [Final]   "Hello world, this is a test."
# [Typing]  Text appears in active window

# Press Ctrl+C to stop
```

### Continuous Mode
```bash
# Always-on voice typing
voinux start --continuous

# Automatically restarts on errors
# Pauses during silence (VAD)
# Runs in background
```

---

## Error Handling

### Common Issues and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| **No microphone detected** | Audio device not found | Check `arecord -l`, set device in config |
| **Permission denied (uinput)** | User not in input group | `sudo usermod -aG input $USER` |
| **CUDA not available** | GPU drivers not installed | Install NVIDIA CUDA Toolkit, check `nvidia-smi` |
| **Out of VRAM** | Model too large for GPU | Use smaller model or INT8 quantization |
| **Model download failed** | Network issues | Check internet, use `voinux model download` |
| **High latency** | GPU overloaded / wrong model | Use turbo model, close other GPU apps |
| **Slow performance** | Running on CPU | Enable GPU, check CUDA installation |

### Graceful Degradation
- If GPU unavailable: Automatically fall back to CPU (with warning about slower performance)
- If VAD fails: Continue without VAD (always-on mode)
- If keyboard simulation fails: Output to stdout
- If model not found: Auto-download on first run
- If VRAM exceeded: Suggest smaller model or INT8 mode

---

## Future Enhancements (Post v1.0)

### Short-term (v1.1 - v1.5)
- [ ] Hotkey activation (global keyboard shortcut)
- [ ] Multiple language support with auto-detection (already supported, needs UI polish)
- [ ] Custom word/phrase replacements (e.g., "newline" → "\n")
- [ ] Punctuation commands ("period", "question mark")
- [ ] Voice commands ("delete that", "undo", "select all")
- [ ] Model switching on-the-fly (without restart)

### Medium-term (v2.0)
- [ ] GUI application for easier configuration
- [ ] System tray integration with status indicator
- [ ] Per-application settings/profiles
- [ ] Macro support (voice-triggered automation)
- [ ] Support for AMD ROCm GPUs (in addition to NVIDIA CUDA)
- [ ] Fine-tuned models for specific domains (medical, legal, etc.)

### Long-term (v3.0+)
- [ ] Plugin system for extensibility
- [ ] Cloud providers as optional alternatives (Deepgram, Azure, AWS)
- [ ] Multi-user support with profiles
- [ ] Distributed inference (use multiple GPUs or machines)
- [ ] Custom model training/fine-tuning interface
- [ ] Mobile companion app (remote dictation using home server)

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Latency** | <2 seconds | Time from speech end to text typed |
| **CPU Usage** | <5% | Average during GPU mode (idle except audio) |
| **GPU Usage** | 50-80% | During active transcription |
| **VRAM Usage** | <6 GB | With large-v3-turbo + INT8 |
| **RAM Usage** | <500 MB | System memory (excluding model) |
| **Accuracy** | >95% | WER (Word Error Rate) for clear speech |
| **Power Usage** | 50-80W | GPU power during transcription |
| **Startup Time** | <5 seconds | From command to ready (including model load) |

---

## Testing Strategy

### Unit Tests
- Audio capture and formatting
- Configuration loading and validation
- Text processing and formatting
- Keyboard backend detection
- Model loading and initialization
- GPU/CPU device selection

### Integration Tests
- End-to-end transcription flow
- Error handling and recovery
- Multi-language support
- Long-duration sessions
- GPU memory management
- Model switching

### System Tests
- Test on various Linux distributions
- Test with different audio backends
- Test on X11 and Wayland
- Test with NVIDIA and AMD GPUs
- Test CPU fallback mode
- Performance profiling and optimization
- VRAM usage monitoring

### Manual Tests
- Real-world usage scenarios
- Different accents and speaking styles
- Background noise handling
- Various applications (browsers, editors, terminals)

---

## Success Criteria

Version 1.0 will be considered complete when:

1. ✅ User can install with single command
2. ✅ Setup wizard configures system correctly (GPU detection, model download)
3. ✅ Real-time transcription works with <2s latency
4. ✅ Transcribed text types into any Linux application
5. ✅ Works on both X11 and Wayland
6. ✅ Supports common Linux distributions (Arch, Ubuntu, Fedora)
7. ✅ GPU acceleration works on NVIDIA GPUs (8GB+ VRAM)
8. ✅ CPU fallback mode available for systems without GPU
9. ✅ Handles errors gracefully with clear messages
10. ✅ Documentation covers all features and troubleshooting
11. ✅ Performance meets targets (see above)
12. ✅ VAD reduces unnecessary GPU processing by >50%

---

## License and Distribution

- **License**: MIT (permissive open source)
- **Repository**: GitHub
- **Distribution**:
  - PyPI (pip install voinux)
  - AUR (Arch User Repository)
  - Snap/Flatpak (future)
- **Documentation**: GitHub Pages or ReadTheDocs

---

## Contributing Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use conventional commits
- Submit PRs with clear descriptions

---

## Appendix

### A. STT Provider Comparison

**Primary Solution (Voinux Default)**

| Provider | Implementation | Pros | Cons |
|----------|----------------|------|------|
| **faster-whisper** | Local GPU | Free, offline, private, high accuracy (95%+), 100+ languages, unlimited usage | Requires GPU (4-8GB VRAM), one-time hardware cost |

**Alternative/Optional Providers**

| Provider | Type | Pros | Cons | When to Use |
|----------|------|------|------|-------------|
| **Deepgram** | Cloud | Ultra-low latency (<300ms), $200 free credits | Requires internet, costs after credits | Need lowest latency possible |
| **Azure Speech** | Cloud | 5 hrs/month free (ongoing), enterprise features | Requires internet, 5hr monthly limit | No GPU, light usage |
| **Google Cloud** | Cloud | High accuracy, 125+ languages, Chirp 3 | Requires internet, only 60min/month free | Legacy compatibility |
| **Vosk** | Local CPU | Fully offline, very lightweight, runs on CPU | Lower accuracy (~80%), fewer languages | No GPU, CPU-only systems |
| **whisper.cpp** | Local (C++) | Faster than Python, lower memory | More complex integration | Advanced optimization |

**Voinux Primary Choice Rationale:**
- **faster-whisper** provides the best balance of cost ($0 ongoing), privacy (local), performance (<2s latency), and accuracy (95%+)
- Most Linux desktop users have or can access an 8GB GPU (~$200 one-time vs ongoing API costs)
- One month of heavy Deepgram usage ($200 credits ≈ 33 hours) costs more than a used 8GB GPU
- Local processing means unlimited usage, no data transmission, and offline capability

### B. Similar Projects

- **voice_typing** (themanyone) - Bash script with Whisper.cpp
- **voice-typing-linux** (GitJuhb) - Go-based with Whisper
- **waystt** - Signal-driven for Wayland
- **Nerd Dictation** - Python-based with Vosk

### C. Useful Resources

**Primary Technologies:**
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI Whisper Repository](https://github.com/openai/whisper)
- [CTranslate2 Documentation](https://github.com/OpenNMT/CTranslate2)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)

**Linux Audio & Input:**
- [PipeWire Documentation](https://pipewire.org/)
- [ydotool GitHub](https://github.com/ReimuNotMoe/ydotool)
- [xdotool Documentation](https://www.semicomplete.com/projects/xdotool/)
- [webrtcvad Documentation](https://github.com/wiseman/py-webrtcvad)

**Alternative Providers:**
- [Deepgram API Documentation](https://developers.deepgram.com/)
- [Azure Speech API Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [Google Cloud Speech-to-Text Documentation](https://cloud.google.com/speech-to-text/docs)

---

**Document Version**: 2.0
**Last Updated**: 2025-10-24
**Major Changes**: Migrated from Google Cloud Speech-to-Text to faster-whisper (local GPU-accelerated inference)
**Author**: Voinux Development Team
