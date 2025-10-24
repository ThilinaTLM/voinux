# Voinux

**Privacy-focused, offline-capable voice typing solution for Linux**

Voinux provides real-time voice-to-text transcription using local GPU-accelerated Whisper models, ensuring complete privacy, offline operation, and unlimited usage at zero recurring cost.

## Features

- ⚡ **Real-time transcription** with <2s latency on GPU
- 🔒 **100% offline** - no cloud services, no data transmission
- 🚀 **GPU accelerated** (NVIDIA CUDA, AMD ROCm) with CPU fallback
- 🌍 **100+ languages** supported with auto-detection
- ⌨️ **System-wide typing** - works in any application
- 🎤 **VAD-powered** - voice activation detection for power efficiency
- ✨ **Easy setup** - automatic model download and configuration
- 🏗️ **Hexagonal architecture** - clean, testable, extensible

## Quick Start

### System Requirements

- **OS**: Linux (Arch, Ubuntu 22.04+, Fedora 38+)
- **Python**: ≥3.12
- **Audio**: PipeWire or PulseAudio
- **Display**: X11 or Wayland
- **GPU** (recommended): NVIDIA GPU with 4-8GB VRAM or AMD GPU with ROCm
- **CUDA** (optional): CUDA Toolkit 11.8+ for NVIDIA GPUs

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/voinux.git
cd voinux

# Install with uv (recommended)
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

### Quick Setup

```bash
# Initialize configuration
voinux config init

# Test your GPU (optional)
voinux test-gpu

# Test audio capture
voinux test-audio

# Start voice transcription
voinux start
```

## Usage

### Basic Commands

```bash
# Start transcription with default settings
voinux start

# Use a specific model
voinux start --model base

# Specify language
voinux start --language en

# Disable VAD
voinux start --no-vad

# Use CPU instead of GPU
voinux start --device cpu
```

### Configuration

Voinux uses a YAML configuration file located at `~/.config/voinux/config.yaml`.

See `voinux config init` to generate a default configuration file with all options documented.

### Model Management

```bash
# List available models
voinux model info

# List cached models
voinux model list

# Download a model manually
voinux model download large-v3-turbo
```

## Architecture

Voinux follows **hexagonal (ports and adapters) architecture** for clean separation of concerns.

For more details, see the technical design document in `openspec/changes/implement-voice-transcription/design.md`.

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/voinux.git
cd voinux

# Install with dev dependencies using uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy voinux

# Run linting
ruff check voinux
black voinux
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for efficient Whisper inference
- [OpenAI Whisper](https://github.com/openai/whisper) for the base models
- The Linux voice typing community
