# Model Management Capability

## ADDED Requirements

### Requirement: Model Manager Port Interface
The system SHALL define an `IModelManager` port interface that abstracts Whisper model management operations, allowing different storage and download strategies.

#### Scenario: Adapter implements interface
- **GIVEN** a model manager adapter (e.g., ModelCache)
- **WHEN** the adapter implements IModelManager interface
- **THEN** it SHALL provide async download_model() method
- **AND** it SHALL provide get_model_path() method returning local path
- **AND** it SHALL provide list_models() method returning cached models
- **AND** it SHALL raise ModelError on failures

#### Scenario: Model metadata
- **GIVEN** any IModelManager implementation
- **WHEN** querying model information
- **THEN** it SHALL return model name
- **AND** it SHALL return model size in bytes
- **AND** it SHALL return model path
- **AND** it MAY return download timestamp and checksum

### Requirement: Model Cache Adapter
The system SHALL provide a ModelCache adapter for downloading, storing, and managing Whisper models locally.

#### Scenario: Model download
- **GIVEN** user requests model download via CLI or automatic trigger
- **WHEN** downloading model (e.g., "large-v3-turbo")
- **THEN** system SHALL use faster_whisper download utilities
- **AND** system SHALL save model to `~/.cache/voinux/models/`
- **AND** system SHALL display download progress (percentage, speed, ETA)
- **AND** system SHALL verify download integrity

#### Scenario: Model cache directory
- **GIVEN** system needs to store models
- **WHEN** initializing ModelCache
- **THEN** system SHALL use `~/.cache/voinux/models/` as default directory
- **AND** system SHALL create directory if it doesn't exist
- **AND** system SHALL respect XDG_CACHE_HOME environment variable
- **AND** user MAY override cache directory via configuration

#### Scenario: Model already cached
- **GIVEN** model exists in cache directory
- **WHEN** requesting model download or initialization
- **THEN** system SHALL detect existing model
- **AND** system SHALL skip download
- **AND** system SHALL log "Using cached model" message
- **AND** system SHALL validate model integrity

### Requirement: Supported Models
The system SHALL support all Whisper model sizes provided by faster-whisper.

#### Scenario: Model size options
- **GIVEN** user selects model for transcription
- **WHEN** validating model name
- **THEN** system SHALL support: tiny, base, small, medium, large-v2, large-v3, large-v3-turbo
- **AND** system SHALL reject invalid model names with suggestion list
- **AND** default model SHALL be "large-v3-turbo" (best balance)

#### Scenario: Model variant support
- **GIVEN** user specifies model variant
- **WHEN** downloading or loading
- **THEN** system SHALL support language-specific models (e.g., "small.en")
- **AND** system SHALL support quantized models
- **AND** system SHALL pass model identifier to faster_whisper

### Requirement: Automatic Model Download
The system SHALL automatically download required model on first run if not cached.

#### Scenario: First run without model
- **GIVEN** user runs `voinux start` for the first time
- **WHEN** initializing speech recognizer
- **THEN** system SHALL detect model is not cached
- **AND** system SHALL prompt user to download (or download automatically with confirmation)
- **AND** system SHALL download configured model
- **AND** system SHALL cache model for future use

#### Scenario: Download with progress
- **GIVEN** model download is in progress
- **WHEN** downloading large model (1-2GB)
- **THEN** system SHALL display progress bar with percentage
- **AND** system SHALL show download speed (MB/s)
- **AND** system SHALL show estimated time remaining
- **AND** system SHALL allow user to cancel (Ctrl+C)

#### Scenario: Download retry on failure
- **GIVEN** model download fails due to network error
- **WHEN** error occurs
- **THEN** system SHALL retry download up to 3 times
- **AND** system SHALL use exponential backoff (1s, 2s, 4s)
- **AND** system SHALL preserve partial download if possible (resume)
- **AND** system SHALL display clear error if all retries fail

### Requirement: Manual Model Management Commands
The system SHALL provide CLI commands for explicit model management.

#### Scenario: Download specific model
- **GIVEN** user runs `voinux model download <model>`
- **WHEN** command executes
- **THEN** system SHALL download specified model to cache
- **AND** system SHALL display progress
- **AND** system SHALL verify integrity after download
- **AND** system SHALL report success with model path

#### Scenario: List cached models
- **GIVEN** user runs `voinux model list`
- **WHEN** command executes
- **THEN** system SHALL scan cache directory
- **AND** system SHALL display table of cached models (name, size, path)
- **AND** system SHALL indicate which model is currently configured
- **AND** system SHALL show total cache size

#### Scenario: Show model information
- **GIVEN** user runs `voinux model info`
- **WHEN** command executes
- **THEN** system SHALL display currently configured model
- **AND** system SHALL show model size and VRAM requirements
- **AND** system SHALL show cache location
- **AND** system SHALL show model download status (cached/not cached)

#### Scenario: Remove model from cache
- **GIVEN** user runs `voinux model remove <model>` (future feature)
- **WHEN** command executes
- **THEN** system SHALL delete specified model from cache
- **AND** system SHALL free disk space
- **AND** system SHALL confirm deletion with user
- **AND** system SHALL prevent removal of currently active model

### Requirement: Model Integrity Verification
The system SHALL verify model integrity to prevent corrupted or incomplete downloads.

#### Scenario: Checksum validation
- **GIVEN** model is downloaded
- **WHEN** download completes
- **THEN** system SHALL compute file checksum
- **AND** system SHALL compare against known good checksum (if available)
- **AND** system SHALL mark model as valid or corrupted

#### Scenario: Load-time validation
- **GIVEN** model exists in cache
- **WHEN** loading model for transcription
- **THEN** system SHALL attempt to load with faster_whisper
- **AND** system SHALL catch initialization errors
- **AND** system SHALL suggest re-downloading if model corrupted

### Requirement: Model Path Resolution
The system SHALL resolve model paths flexibly supporting cache, absolute paths, and Hugging Face identifiers.

#### Scenario: Resolve from cache
- **GIVEN** configuration specifies model name (e.g., "large-v3-turbo")
- **WHEN** resolving model path
- **THEN** system SHALL check cache directory first
- **AND** system SHALL return cached path if found
- **AND** system SHALL trigger download if not found

#### Scenario: Custom model path
- **GIVEN** configuration specifies absolute path to model
- **WHEN** resolving model path
- **THEN** system SHALL use specified path directly
- **AND** system SHALL validate path exists
- **AND** system SHALL raise ModelError if path invalid

#### Scenario: Hugging Face model identifier
- **GIVEN** configuration specifies HF model ID (e.g., "Systran/faster-whisper-large-v3")
- **WHEN** loading model
- **THEN** system SHALL pass identifier to faster_whisper
- **AND** faster_whisper SHALL handle download from HF Hub
- **AND** system SHALL respect HF_HOME environment variable for cache

### Requirement: Model Switching
The system SHALL support changing models without reinstallation.

#### Scenario: Change model via config
- **GIVEN** user edits config file to change model
- **WHEN** restarting transcription
- **THEN** system SHALL load new model
- **AND** system SHALL download if not cached
- **AND** system SHALL release previous model from memory

#### Scenario: Change model via CLI argument
- **GIVEN** user runs `voinux start --model medium`
- **WHEN** starting transcription
- **THEN** system SHALL override config model with CLI argument
- **AND** system SHALL load specified model
- **AND** system SHALL not modify config file

### Requirement: Model Size and VRAM Requirements
The system SHALL provide information about model resource requirements to help users choose appropriate models.

#### Scenario: Display VRAM requirements
- **GIVEN** user views model information
- **WHEN** system displays model details
- **THEN** system SHALL show estimated VRAM usage for float16 and int8
- **AND** system SHALL warn if model likely exceeds available VRAM
- **AND** system SHALL suggest alternative models if needed

#### Scenario: Model size reference
- **GIVEN** user runs `voinux model info` or `voinux model list`
- **WHEN** displaying model information
- **THEN** system SHALL show disk size for each model
- **AND** system SHALL show VRAM requirements (FP16 and INT8)
- **AND** system SHALL show expected latency tier (fast/medium/slow)

### Requirement: Offline Operation
The system SHALL support fully offline operation after initial model download.

#### Scenario: Offline transcription
- **GIVEN** model is cached locally
- **WHEN** user starts transcription without internet
- **THEN** system SHALL load model from cache
- **AND** system SHALL not attempt network requests
- **AND** system SHALL function normally

#### Scenario: Offline model verification
- **GIVEN** system is offline and model is not cached
- **WHEN** user attempts transcription
- **THEN** system SHALL raise ModelError "Model not cached and offline"
- **AND** error SHALL suggest downloading model when online
- **AND** error SHALL show command: `voinux model download <model>`

### Requirement: Model Error Handling
The system SHALL handle model-related errors with clear messages and recovery guidance.

#### Scenario: Model not found
- **GIVEN** specified model does not exist
- **WHEN** attempting to download or load
- **THEN** system SHALL raise ModelError "Model '<name>' not found"
- **AND** error SHALL list available models
- **AND** error SHALL suggest checking model name spelling

#### Scenario: Download network error
- **GIVEN** network is unavailable during download
- **WHEN** download fails after retries
- **THEN** system SHALL raise ModelError with network details
- **AND** error SHALL suggest checking internet connection
- **AND** error SHALL preserve partial download for resume

#### Scenario: Insufficient disk space
- **GIVEN** insufficient space for model download
- **WHEN** attempting to download large model
- **THEN** system SHALL detect low disk space before download
- **AND** system SHALL raise ModelError "Insufficient disk space"
- **AND** error SHALL show required space and available space
- **AND** error SHALL suggest removing old models or freeing space

#### Scenario: Corrupted model file
- **GIVEN** model file is corrupted or incomplete
- **WHEN** attempting to load model
- **THEN** system SHALL detect corruption during load
- **AND** system SHALL raise ModelError "Model corrupted"
- **AND** error SHALL suggest re-downloading: `voinux model download --force <model>`
