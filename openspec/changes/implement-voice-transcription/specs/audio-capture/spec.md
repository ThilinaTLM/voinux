# Audio Capture Capability

## ADDED Requirements

### Requirement: Audio Capture Port Interface
The system SHALL define an `IAudioCapture` port interface that abstracts audio input operations, allowing different audio backend implementations to be used interchangeably.

#### Scenario: Adapter implements interface
- **GIVEN** an audio capture adapter (e.g., SoundCard, PyAudio)
- **WHEN** the adapter implements IAudioCapture interface
- **THEN** it SHALL provide async stream() method returning AudioChunk objects
- **AND** it SHALL support start() and stop() lifecycle methods
- **AND** it SHALL raise AudioCaptureError on failures

#### Scenario: Audio format specification
- **GIVEN** any IAudioCapture implementation
- **WHEN** streaming audio chunks
- **THEN** chunks SHALL be 16kHz sample rate
- **AND** chunks SHALL be mono (single channel)
- **AND** chunks SHALL be 16-bit PCM format
- **AND** chunks SHALL be numpy float32 arrays normalized to [-1.0, 1.0]

### Requirement: SoundCard Audio Capture Adapter
The system SHALL provide a SoundCardAudioCapture adapter using the soundcard library as the primary audio input backend.

#### Scenario: Capture from default microphone
- **GIVEN** soundcard library is available
- **WHEN** user starts transcription without specifying audio device
- **THEN** system SHALL capture from default input device
- **AND** audio SHALL be captured in real-time with <100ms buffering latency

#### Scenario: Capture from specific device
- **GIVEN** user specifies audio device in configuration
- **WHEN** user starts transcription
- **THEN** system SHALL capture from specified device
- **AND** system SHALL validate device exists before starting

#### Scenario: Handle device disconnection
- **GIVEN** audio capture is active
- **WHEN** microphone is disconnected
- **THEN** system SHALL raise AudioCaptureError
- **AND** error message SHALL indicate device disconnection

### Requirement: PyAudio Fallback Adapter
The system SHALL provide a PyAudioCapture adapter as fallback when soundcard is unavailable or fails.

#### Scenario: Automatic fallback
- **GIVEN** soundcard library is not installed or fails
- **WHEN** system initializes audio capture
- **THEN** system SHALL attempt PyAudio adapter
- **AND** system SHALL log fallback reason

#### Scenario: PyAudio capture operation
- **GIVEN** PyAudio adapter is selected
- **WHEN** capturing audio
- **THEN** audio format SHALL match IAudioCapture specification (16kHz, mono, 16-bit)
- **AND** latency SHALL be comparable to soundcard (<150ms)

### Requirement: Audio Chunk Entity
The system SHALL define an AudioChunk entity representing a discrete segment of captured audio data.

#### Scenario: Chunk creation
- **GIVEN** audio data from capture adapter
- **WHEN** creating AudioChunk
- **THEN** chunk SHALL contain audio data as numpy array
- **AND** chunk SHALL contain timestamp
- **AND** chunk SHALL contain duration in seconds
- **AND** chunk SHALL validate format (shape, dtype, sample rate)

#### Scenario: Chunk duration configuration
- **GIVEN** configuration specifies chunk_duration_ms
- **WHEN** capturing audio
- **THEN** chunks SHALL have specified duration (default 100ms)
- **AND** chunks SHALL not exceed 2x configured duration (handle buffer variations)

### Requirement: Audio Buffer Management
The system SHALL manage audio buffering to prevent overruns and ensure continuous capture.

#### Scenario: Bounded buffer
- **GIVEN** audio capture is streaming
- **WHEN** processing cannot keep up with capture rate
- **THEN** system SHALL use bounded async queue (max 50 chunks)
- **AND** system SHALL drop oldest chunks when queue is full
- **AND** system SHALL log warning when dropping chunks

#### Scenario: Graceful shutdown
- **GIVEN** audio capture is active
- **WHEN** user stops transcription
- **THEN** system SHALL flush remaining chunks in buffer
- **AND** system SHALL close audio stream cleanly
- **AND** system SHALL release audio device resources

### Requirement: Audio Backend Auto-Detection
The system SHALL automatically detect and select the best available audio backend at runtime.

#### Scenario: Priority-based selection
- **GIVEN** no explicit backend specified in configuration
- **WHEN** initializing audio capture
- **THEN** system SHALL try soundcard first
- **AND** system SHALL try pyaudio if soundcard fails
- **AND** system SHALL raise AudioCaptureError if all backends fail

#### Scenario: User-specified backend
- **GIVEN** user specifies audio backend in configuration
- **WHEN** initializing audio capture
- **THEN** system SHALL use specified backend only
- **AND** system SHALL raise AudioCaptureError if specified backend unavailable

### Requirement: Audio Capture Error Handling
The system SHALL provide clear error messages and recovery guidance for audio capture failures.

#### Scenario: No microphone detected
- **GIVEN** no audio input devices are available
- **WHEN** attempting to start audio capture
- **THEN** system SHALL raise AudioCaptureError with message "No microphone detected"
- **AND** error message SHALL suggest running `arecord -l` to list devices

#### Scenario: Permission denied
- **GIVEN** user lacks permissions to access audio device
- **WHEN** attempting to start audio capture
- **THEN** system SHALL raise AudioCaptureError with message "Permission denied"
- **AND** error message SHALL suggest checking user group membership (audio/pulse)

#### Scenario: Device busy
- **GIVEN** audio device is in use by another application
- **WHEN** attempting to start audio capture
- **THEN** system SHALL raise AudioCaptureError with message "Device busy"
- **AND** error message SHALL suggest closing other audio applications

### Requirement: Audio Capture Testing
The system SHALL provide a test command to verify audio capture functionality.

#### Scenario: Test audio capture
- **GIVEN** user runs `voinux test-audio`
- **WHEN** command executes
- **THEN** system SHALL capture 3 seconds of audio
- **AND** system SHALL display audio level meters in real-time
- **AND** system SHALL report detected sample rate and channels
- **AND** system SHALL report backend used (soundcard or pyaudio)

#### Scenario: Test with specific device
- **GIVEN** user runs `voinux test-audio --device "USB Microphone"`
- **WHEN** command executes
- **THEN** system SHALL capture from specified device
- **AND** system SHALL validate device exists
- **AND** system SHALL display device information
