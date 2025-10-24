# Voinux

**Privacy-focused, offline voice typing for Linux**

Voinux provides real-time voice-to-text transcription using local GPU-accelerated Whisper models, ensuring complete privacy, offline operation, and unlimited usage at zero recurring cost.

## ✨ Features

- ⚡ **Real-time transcription** - Sub-2 second latency on GPU
- 🔒 **100% offline** - No cloud services, no data transmission, no API costs
- 🚀 **GPU accelerated** - NVIDIA CUDA and AMD ROCm support with automatic CPU fallback
- 🌍 **100+ languages** - Multilingual support with auto-detection
- ⌨️ **System-wide typing** - Works in any application (browser, IDE, text editor, etc.)
- 🎤 **Smart VAD** - Voice activation detection reduces GPU usage by 50%+ during silence
- 🖥️ **CLI & GUI modes** - Floating panel with real-time stats or headless operation
- ✨ **Zero configuration** - Automatic model download and optimal settings detection
- 🏗️ **Clean architecture** - Hexagonal design for testability and extensibility

## 🎯 Why Voinux?

- **Privacy**: Your voice data never leaves your machine
- **Cost**: No subscription fees or API costs - unlimited usage
- **Speed**: Local GPU processing beats cloud latency every time
- **Reliability**: Works anywhere, anytime - no internet required
- **Control**: Full control over models, languages, and behavior

## 🚀 Quick Start

### System Requirements

- **OS**: Linux (Arch, Ubuntu 22.04+, Fedora 38+, or similar)
- **Python**: 3.12 or higher
- **Audio**: PipeWire or PulseAudio
- **Display**: X11 or Wayland
- **GPU** (recommended): NVIDIA GPU with 4-8GB VRAM or AMD GPU with ROCm support
- **CUDA** (optional): CUDA Toolkit 11.8+ for NVIDIA GPUs

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/voinux.git
cd voinux

# Install with uv (recommended - faster and more reliable)
uv sync

# For NVIDIA GPU support
uv sync --extra cuda

# For development
uv sync --extra dev

# Alternative: Install with pip
pip install -e .
pip install -e ".[cuda]"  # For NVIDIA GPU
pip install -e ".[dev]"   # For development
```

### First Run

```bash
# 1. Initialize configuration (creates ~/.config/voinux/config.yaml)
voinux config init

# 2. Test your setup
voinux test-gpu      # Verify GPU acceleration is working
voinux test-audio    # Verify microphone input is working
voinux test-keyboard # Verify keyboard simulation works

# 3. Start transcribing!
voinux start         # CLI mode with terminal output
voinux start --gui   # GUI mode with floating stats panel
```

On first run, Voinux will automatically download the default Whisper model (~140MB). This happens once and models are cached in `~/.cache/voinux/models`.

## 📖 Usage

### How It Works

1. Start Voinux with `voinux start` or `voinux start --gui`
2. Speak into your microphone
3. Text appears automatically in your focused application
4. Press `Ctrl+C` in the terminal to stop transcription

Voinux runs continuously in the background, listening to your microphone and typing transcribed text into any application you're focused on.

### Command Reference

```bash
# Start with default settings
voinux start

# Start with GUI (floating stats panel)
voinux start --gui

# Choose a specific Whisper model
voinux start --model base              # Faster, less accurate
voinux start --model large-v3-turbo    # Slower, more accurate

# Specify language (improves accuracy and speed)
voinux start --language en    # English
voinux start --language es    # Spanish
voinux start --language fr    # French
# ... supports 100+ languages

# Force CPU mode (no GPU)
voinux start --device cpu

# Disable voice activation detection (process all audio)
voinux start --no-vad

# Combine options
voinux start --gui --model base --language en
```

### Available Models

| Model | Size | VRAM | Speed | Accuracy | Best For |
|-------|------|------|-------|----------|----------|
| `tiny` | 75 MB | ~1 GB | Fastest | Lowest | Testing, low-end hardware |
| `base` | 145 MB | ~1 GB | Fast | Good | Balanced performance |
| `small` | 488 MB | ~2 GB | Medium | Better | General use |
| `medium` | 1.5 GB | ~5 GB | Slow | Great | High accuracy needs |
| `large-v3-turbo` | 1.6 GB | ~6 GB | Slower | Best | Maximum accuracy |

Models are automatically downloaded on first use and cached in `~/.cache/voinux/models`.

### Configuration

Voinux uses a three-layer configuration system (CLI args override config file, config file overrides defaults):

1. **Defaults** - Built-in sensible defaults
2. **Config file** - `~/.config/voinux/config.yaml`
3. **CLI arguments** - Runtime overrides

```bash
# Generate default config file with documentation
voinux config init

# View current configuration
voinux config show

# Edit configuration
$EDITOR ~/.config/voinux/config.yaml
```

Example configuration:
```yaml
model:
  name: "base"
  device: "cuda"  # or "cpu"
  language: "en"

audio:
  sample_rate: 16000
  chunk_duration_ms: 100

vad:
  enabled: true
  aggressiveness: 3  # 0-3, higher = more aggressive silence filtering

keyboard:
  adapter: "auto"  # auto-detects xdotool (X11) or ydotool (Wayland)
```

### Model Management

```bash
# List all available Whisper models
voinux model info

# List models cached locally
voinux model list

# Download a model manually (optional - happens automatically on use)
voinux model download large-v3-turbo

# Clear model cache to free disk space
rm -rf ~/.cache/voinux/models
```

## 🏗️ Architecture

Voinux follows **hexagonal (ports and adapters) architecture** for clean separation of concerns and testability.

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Application                          │
│                   (CLI, GUI, Use Cases)                     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────┐
│              Domain Layer (Pure Business Logic)            │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Entities │  │  Ports   │  │ Services  │  │Exceptions│ │
│  └──────────┘  └──────────┘  └───────────┘  └──────────┘ │
└─────────────────────────────┬─────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────┐
│               Adapters (Infrastructure)                    │
│  ┌──────┐  ┌──────┐  ┌──────────┐  ┌─────┐  ┌──────────┐ │
│  │Audio │  │ STT  │  │Keyboard  │  │ VAD │  │  Models  │ │
│  └──────┘  └──────┘  └──────────┘  └─────┘  └──────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Transcription Pipeline:**
```
Audio Capture → VAD → Whisper Recognition → Keyboard Simulation
  (100ms)      (50ms)     (500-1500ms)          (<50ms)
```

### Project Structure

```
voinux/
├── domain/          # Pure business logic (no dependencies)
│   ├── entities.py  # Core domain objects (AudioChunk, TranscriptionResult)
│   ├── ports.py     # Interface contracts
│   └── services.py  # Domain services (TranscriptionPipeline)
├── adapters/        # Infrastructure implementations
│   ├── audio/       # Audio capture (soundcard, pyaudio)
│   ├── stt/         # Speech-to-text (faster-whisper)
│   ├── keyboard/    # Keyboard simulation (xdotool, ydotool)
│   ├── vad/         # Voice activation (WebRTC VAD)
│   └── models/      # Model management and caching
├── application/     # Use cases and orchestration
│   ├── use_cases.py # Application logic
│   └── factories.py # Dependency injection
├── cli/             # Click-based CLI interface
└── gui/             # PyQt6-based GUI (optional)
```

For detailed architecture documentation, see `openspec/changes/implement-voice-transcription/design.md`.

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/voinux.git
cd voinux

# Install with dev dependencies using uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks (auto-format and lint on commit)
pre-commit install
```

### Code Quality

The project enforces high code quality standards with **Ruff** (linting + formatting) and **mypy** (type checking):

```bash
# Format code (auto-fix style issues)
ruff format voinux

# Lint code (check for issues)
ruff check voinux

# Lint + auto-fix where possible
ruff check voinux --fix

# Type checking (strict mode)
mypy voinux

# Run all checks at once (same as pre-commit hooks)
pre-commit run --all-files
```

Pre-commit hooks automatically run on every commit to ensure code quality. If hooks make changes, review and commit again.

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

# Run only unit tests (fast)
pytest tests/unit/

# Run only integration tests (slower, requires audio/GPU)
pytest tests/integration/
```

**Test Structure:**
- `tests/unit/` - Fast, isolated tests with mocked dependencies
- `tests/integration/` - Tests with real adapters (audio, GPU, etc.)
- `tests/system/` - End-to-end tests of complete workflows

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting: `pre-commit run --all-files && pytest`
5. Commit your changes (pre-commit hooks will run automatically)
6. Push to your fork and submit a pull request

Please ensure:
- All tests pass
- Code is formatted with Ruff
- Type checking passes with mypy
- New features include tests
- Public APIs have docstrings

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Check GPU availability
voinux test-gpu

# If CUDA/ROCm is not detected, try:
# 1. Verify CUDA/ROCm installation
nvidia-smi  # For NVIDIA
rocm-smi    # For AMD

# 2. Install CUDA extras
uv sync --extra cuda

# 3. Fall back to CPU mode
voinux start --device cpu
```

### No Audio Input

```bash
# Test audio capture
voinux test-audio

# If no audio is captured:
# 1. Check microphone selection in system settings
# 2. Verify PipeWire/PulseAudio is running
pactl list sources  # List audio sources

# 3. Check permissions (may need to add user to audio group)
sudo usermod -a -G audio $USER
```

### Keyboard Typing Not Working

```bash
# Test keyboard simulation
voinux test-keyboard

# Wayland users: ydotool requires daemon
sudo systemctl enable --now ydotool.service

# X11 users: install xdotool
sudo pacman -S xdotool  # Arch
sudo apt install xdotool  # Ubuntu/Debian
```

### Poor Transcription Quality

- **Use a better model**: Try `--model small` or `--model large-v3-turbo`
- **Specify language**: Use `--language en` instead of auto-detection
- **Check audio quality**: Use `voinux test-audio` to verify clear input
- **Reduce background noise**: Use a better microphone or quieter environment
- **Adjust VAD settings**: Try `--no-vad` or adjust VAD aggressiveness in config

### High Latency

- **Use GPU**: Ensure `voinux test-gpu` shows GPU acceleration is working
- **Use smaller model**: Try `--model tiny` or `--model base`
- **Reduce VAD aggressiveness**: Lower values process more audio
- **Check system resources**: Close other GPU-intensive applications

### Model Download Issues

```bash
# Manually download a model
voinux model download base

# If download fails, check:
# 1. Internet connection
# 2. Disk space in ~/.cache/voinux/
# 3. Try again (downloads are resumable)
```

## 📊 Performance

### Latency Benchmarks (NVIDIA RTX 3060, 12GB VRAM)

| Model | Inference Time | Total Latency | VRAM Usage |
|-------|---------------|---------------|------------|
| `tiny` | 50-100ms | ~400ms | ~1 GB |
| `base` | 150-300ms | ~600ms | ~1 GB |
| `small` | 300-500ms | ~800ms | ~2 GB |
| `medium` | 800-1200ms | ~1.5s | ~5 GB |
| `large-v3-turbo` | 1000-1500ms | ~1.8s | ~6 GB |

**Total Latency Breakdown:**
- Audio capture: ~100ms (configurable chunk size)
- VAD processing: ~50ms
- Model inference: varies by model (see table)
- Keyboard simulation: <50ms

### VAD Impact

Voice Activation Detection (VAD) reduces unnecessary GPU processing:
- **Silence periods**: Near-zero GPU usage
- **Speech periods**: Full model inference
- **Average GPU reduction**: 50-70% in typical use

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Efficient CTranslate2-based Whisper implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Original speech recognition models
- [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) - Voice activity detection
- [soundcard](https://github.com/bastibe/SoundCard) - Clean audio I/O for Python
- The Linux voice typing community

## 🔗 Related Projects

- [Nerd Dictation](https://github.com/ideasman42/nerd-dictation) - Another offline voice typing solution for Linux
- [Whisper](https://github.com/openai/whisper) - OpenAI's speech recognition model
- [Talon](https://talonvoice.com/) - Voice control and dictation (proprietary, cross-platform)

---

**Made with ❤️ for the Linux community**
