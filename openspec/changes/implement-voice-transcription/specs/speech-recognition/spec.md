# Speech Recognition Capability

## ADDED Requirements

### Requirement: Speech Recognizer Port Interface
The system SHALL define an `ISpeechRecognizer` port interface that abstracts speech-to-text operations, allowing different STT engine implementations to be used interchangeably.

#### Scenario: Adapter implements interface
- **GIVEN** a speech recognizer adapter (e.g., WhisperRecognizer)
- **WHEN** the adapter implements ISpeechRecognizer interface
- **THEN** it SHALL provide async transcribe() method accepting AudioChunk
- **AND** it SHALL return TranscriptionResult entity
- **AND** it SHALL support initialize() and shutdown() lifecycle methods
- **AND** it SHALL raise TranscriptionError on failures

#### Scenario: Transcription result format
- **GIVEN** any ISpeechRecognizer implementation
- **WHEN** transcription succeeds
- **THEN** result SHALL contain text string
- **AND** result SHALL contain confidence score (0.0-1.0)
- **AND** result SHALL contain language code (ISO 639-1)
- **AND** result MAY contain word-level timestamps

### Requirement: Whisper Recognizer Adapter
The system SHALL provide a WhisperRecognizer adapter using faster-whisper library for local GPU-accelerated transcription.

#### Scenario: Model initialization
- **GIVEN** configuration specifies Whisper model (e.g., "large-v3-turbo")
- **WHEN** initializing WhisperRecognizer
- **THEN** system SHALL load model into GPU memory
- **AND** initialization SHALL complete within 10 seconds
- **AND** system SHALL log model name, device (CUDA/ROCm/CPU), and compute type

#### Scenario: GPU transcription
- **GIVEN** WhisperRecognizer initialized with CUDA device
- **WHEN** transcribing audio chunk (500ms-2s)
- **THEN** transcription SHALL complete within 2 seconds
- **AND** system SHALL utilize GPU acceleration
- **AND** result SHALL include automatic punctuation and capitalization

#### Scenario: CPU fallback
- **GIVEN** CUDA is unavailable or initialization fails
- **WHEN** initializing WhisperRecognizer
- **THEN** system SHALL fall back to CPU device
- **AND** system SHALL log warning about degraded performance
- **AND** transcription SHALL still function (with higher latency 5-10s)

### Requirement: Model Configuration
The system SHALL support multiple Whisper model sizes with different accuracy/speed trade-offs.

#### Scenario: Model selection
- **GIVEN** user specifies model in configuration or CLI argument
- **WHEN** initializing WhisperRecognizer
- **THEN** system SHALL load specified model from cache
- **AND** system SHALL support models: tiny, base, small, medium, large-v2, large-v3, large-v3-turbo
- **AND** system SHALL validate model exists or trigger download

#### Scenario: Compute type selection
- **GIVEN** user specifies compute_type in configuration
- **WHEN** loading model
- **THEN** system SHALL use specified precision (float16, int8, float32)
- **AND** system SHALL default to int8 for VRAM efficiency
- **AND** system SHALL validate compute_type compatible with device

#### Scenario: Language configuration
- **GIVEN** user specifies language code in configuration
- **WHEN** transcribing audio
- **THEN** system SHALL use specified language for transcription
- **AND** system SHALL support 100+ languages via ISO 639-1 codes
- **AND** system SHALL auto-detect language if set to "auto"

### Requirement: Async Integration with Synchronous Library
The system SHALL integrate synchronous faster-whisper library with async architecture using thread pool execution.

#### Scenario: Non-blocking transcription
- **GIVEN** audio chunk ready for transcription
- **WHEN** calling async transcribe() method
- **THEN** system SHALL execute faster_whisper model.transcribe() in ThreadPoolExecutor
- **AND** await SHALL not block event loop
- **AND** other async operations SHALL continue during transcription

#### Scenario: Thread pool management
- **GIVEN** WhisperRecognizer is active
- **WHEN** processing multiple chunks
- **THEN** system SHALL use single thread in pool to avoid GPU context switching
- **AND** system SHALL queue transcription requests if pool is busy
- **AND** system SHALL limit queue size to prevent memory exhaustion

### Requirement: Transcription Result Entity
The system SHALL define a TranscriptionResult entity containing transcription output and metadata.

#### Scenario: Result creation
- **GIVEN** successful transcription from Whisper model
- **WHEN** creating TranscriptionResult
- **THEN** result SHALL contain transcribed text string
- **AND** result SHALL contain language code
- **AND** result SHALL contain confidence score
- **AND** result SHALL contain processing duration in seconds
- **AND** result SHALL filter empty or whitespace-only text

#### Scenario: Result validation
- **GIVEN** TranscriptionResult entity
- **WHEN** validating result
- **THEN** text SHALL be non-null (empty string if no speech)
- **AND** confidence SHALL be between 0.0 and 1.0
- **AND** language SHALL be valid ISO 639-1 code

### Requirement: Transcription Options
The system SHALL support advanced transcription options for fine-tuning accuracy and performance.

#### Scenario: Beam search configuration
- **GIVEN** user specifies beam_size in configuration
- **WHEN** transcribing audio
- **THEN** system SHALL use specified beam size (1-10)
- **AND** higher beam size SHALL increase accuracy at cost of speed
- **AND** default SHALL be 5 (balanced)

#### Scenario: VAD filter integration
- **GIVEN** vad_filter is enabled in configuration
- **WHEN** transcribing audio
- **THEN** system SHALL use faster-whisper built-in VAD
- **AND** VAD SHALL filter silence within chunks
- **AND** VAD SHALL improve accuracy by removing non-speech frames

#### Scenario: Word timestamps
- **GIVEN** word_timestamps is enabled in configuration
- **WHEN** transcribing audio
- **THEN** system SHALL include word-level timing information in result
- **AND** timestamps SHALL be relative to chunk start
- **AND** timestamps MAY be used for future features (e.g., cursor positioning)

### Requirement: Error Handling and Recovery
The system SHALL handle transcription errors gracefully with clear messages and recovery strategies.

#### Scenario: Model loading failure
- **GIVEN** specified model cannot be loaded
- **WHEN** initializing WhisperRecognizer
- **THEN** system SHALL raise TranscriptionError with message "Failed to load model"
- **AND** error SHALL indicate missing model or corrupted files
- **AND** error SHALL suggest running `voinux model download <model>`

#### Scenario: CUDA out of memory
- **GIVEN** model is too large for available VRAM
- **WHEN** initializing or transcribing
- **THEN** system SHALL raise TranscriptionError with message "Out of VRAM"
- **AND** error SHALL suggest using smaller model or int8 compute type
- **AND** error SHALL suggest closing other GPU applications

#### Scenario: Transcription timeout
- **GIVEN** transcription takes longer than expected
- **WHEN** chunk processing exceeds 30 seconds
- **THEN** system SHALL raise TranscriptionError with message "Transcription timeout"
- **AND** system SHALL log chunk characteristics (duration, size)
- **AND** system SHALL continue with next chunk

### Requirement: GPU Testing
The system SHALL provide test commands to verify GPU availability and model performance.

#### Scenario: Test GPU availability
- **GIVEN** user runs `voinux test-gpu`
- **WHEN** command executes
- **THEN** system SHALL detect CUDA or ROCm availability
- **AND** system SHALL report GPU device name and VRAM
- **AND** system SHALL report PyTorch CUDA/ROCm version
- **AND** system SHALL recommend device setting (cuda/rocm/cpu)

#### Scenario: Test model inference
- **GIVEN** user runs `voinux test-model`
- **WHEN** command executes
- **THEN** system SHALL load configured model
- **AND** system SHALL transcribe 5-second test audio file
- **AND** system SHALL report inference time and latency
- **AND** system SHALL report VRAM usage during inference
- **AND** system SHALL verify transcription output is non-empty

### Requirement: Performance Monitoring
The system SHALL track and report transcription performance metrics for optimization.

#### Scenario: Latency tracking
- **GIVEN** transcription is active
- **WHEN** processing audio chunks
- **THEN** system SHALL measure transcription latency per chunk
- **AND** system SHALL log warning if latency exceeds 2 seconds
- **AND** system SHALL expose metrics for debugging (optional verbose mode)

#### Scenario: GPU utilization monitoring
- **GIVEN** GPU device is used
- **WHEN** transcription is active
- **THEN** system MAY log GPU utilization percentage
- **AND** system MAY log VRAM usage
- **AND** metrics SHALL be available in verbose/debug mode
