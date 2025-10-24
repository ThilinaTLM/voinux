# Voice Activation Detection Capability

## ADDED Requirements

### Requirement: Voice Activation Detector Port Interface
The system SHALL define an `IVoiceActivationDetector` port interface that abstracts voice activity detection operations, allowing different VAD implementations to be used interchangeably.

#### Scenario: Adapter implements interface
- **GIVEN** a VAD adapter (e.g., WebRTCVAD)
- **WHEN** the adapter implements IVoiceActivationDetector interface
- **THEN** it SHALL provide async is_speech() method accepting AudioChunk
- **AND** it SHALL return boolean indicating speech presence
- **AND** it SHALL support configure() method for threshold adjustment
- **AND** it SHALL raise VADError on failures

#### Scenario: Speech detection result
- **GIVEN** any IVoiceActivationDetector implementation
- **WHEN** analyzing audio chunk
- **THEN** method SHALL return True if speech detected
- **AND** method SHALL return False if only silence/noise detected
- **AND** detection SHALL complete within 50ms

### Requirement: WebRTC VAD Adapter
The system SHALL provide a WebRTCVAD adapter using the webrtcvad library for speech detection.

#### Scenario: VAD initialization
- **GIVEN** configuration specifies VAD threshold (0-3)
- **WHEN** initializing WebRTCVAD adapter
- **THEN** system SHALL create webrtcvad.Vad instance
- **AND** system SHALL set aggressiveness level from configuration
- **AND** aggressiveness SHALL map: 0.0-0.3→0, 0.3-0.5→1, 0.5-0.7→2, 0.7-1.0→3

#### Scenario: Speech detection
- **GIVEN** audio chunk is 16kHz mono 16-bit PCM
- **WHEN** checking if speech is present
- **THEN** system SHALL call vad.is_speech() with audio frame
- **AND** system SHALL handle webrtcvad frame size requirements (10/20/30ms)
- **AND** system SHALL return boolean result immediately

#### Scenario: Frame size adaptation
- **GIVEN** audio chunk duration is not exact webrtcvad frame size
- **WHEN** detecting speech
- **THEN** system SHALL split chunk into valid frame sizes (10/20/30ms)
- **AND** system SHALL consider speech detected if ANY frame contains speech
- **AND** system SHALL pad last frame if necessary

### Requirement: VAD Configuration
The system SHALL support configurable VAD sensitivity to balance false positives and false negatives.

#### Scenario: Threshold configuration
- **GIVEN** user specifies vad.threshold in configuration (0.0-1.0)
- **WHEN** initializing VAD
- **THEN** system SHALL map threshold to webrtcvad aggressiveness (0-3)
- **AND** lower threshold (e.g., 0.3) SHALL be more sensitive (detect more speech)
- **AND** higher threshold (e.g., 0.8) SHALL be less sensitive (require clearer speech)

#### Scenario: Default threshold
- **GIVEN** user does not specify VAD threshold
- **WHEN** initializing VAD
- **THEN** system SHALL use default threshold of 0.5 (moderate sensitivity)
- **AND** default SHALL balance accuracy and responsiveness

#### Scenario: Runtime threshold adjustment
- **GIVEN** VAD is active
- **WHEN** user changes threshold via configuration or CLI
- **THEN** system SHALL apply new threshold without restart
- **AND** change SHALL take effect for next audio chunk

### Requirement: VAD Enable/Disable
The system SHALL support enabling or disabling VAD via configuration.

#### Scenario: VAD enabled
- **GIVEN** vad.enabled is true in configuration
- **WHEN** transcription pipeline processes audio
- **THEN** system SHALL filter chunks through VAD before STT
- **AND** system SHALL only send speech-containing chunks to recognizer
- **AND** system SHALL log VAD filter statistics (chunks filtered)

#### Scenario: VAD disabled
- **GIVEN** vad.enabled is false in configuration
- **WHEN** transcription pipeline processes audio
- **THEN** system SHALL send all chunks directly to STT recognizer
- **AND** system SHALL not perform VAD checks
- **AND** system SHALL not filter any chunks

#### Scenario: VAD bypass on error
- **GIVEN** VAD initialization or processing fails
- **WHEN** error occurs
- **THEN** system SHALL log warning about VAD failure
- **AND** system SHALL continue without VAD (send all chunks to STT)
- **AND** system SHALL not crash or stop transcription

### Requirement: Silence Detection and Handling
The system SHALL use VAD to detect silence periods and optimize GPU usage.

#### Scenario: Continuous silence detection
- **GIVEN** VAD is enabled
- **WHEN** audio contains only silence for configured duration
- **THEN** system SHALL not send chunks to STT recognizer
- **AND** system SHALL reduce GPU usage by 50%+ during silence
- **AND** system SHALL resume STT when speech detected

#### Scenario: Silence duration threshold
- **GIVEN** vad.silence_duration_ms configured (e.g., 1000ms)
- **WHEN** silence persists for specified duration
- **THEN** system MAY signal end of utterance
- **AND** system MAY flush pending transcription
- **AND** behavior SHALL be documented for future features

#### Scenario: Mixed speech and silence
- **GIVEN** audio alternates between speech and short pauses
- **WHEN** processing chunks
- **THEN** system SHALL detect speech chunks correctly
- **AND** system SHALL not prematurely end utterance during natural pauses
- **AND** VAD SHALL handle normal speech rhythm

### Requirement: VAD Performance Optimization
The system SHALL ensure VAD processing does not add significant latency to the transcription pipeline.

#### Scenario: Low latency VAD
- **GIVEN** audio chunk ready for processing
- **WHEN** checking for speech
- **THEN** VAD SHALL complete within 50ms
- **AND** VAD SHALL not block audio capture
- **AND** VAD SHALL run concurrently with STT via async architecture

#### Scenario: Lightweight processing
- **GIVEN** VAD is active
- **WHEN** filtering audio chunks
- **THEN** VAD SHALL use <1% CPU on average
- **AND** VAD SHALL use <10MB RAM
- **AND** VAD SHALL not require GPU resources

### Requirement: VAD Async Integration
The system SHALL integrate synchronous webrtcvad library with async architecture.

#### Scenario: Non-blocking VAD check
- **GIVEN** audio chunk ready for VAD
- **WHEN** calling async is_speech() method
- **THEN** system SHALL execute webrtcvad.is_speech() in ThreadPoolExecutor if needed
- **AND** await SHALL not block event loop
- **AND** VAD SHALL complete quickly enough that thread pool MAY not be necessary

#### Scenario: VAD in pipeline
- **GIVEN** transcription pipeline is running
- **WHEN** audio chunk arrives
- **THEN** system SHALL check VAD before STT
- **AND** VAD SHALL filter in-line (no separate queue)
- **AND** filtered chunks SHALL not reach STT recognizer

### Requirement: VAD Error Handling
The system SHALL handle VAD errors gracefully without stopping transcription.

#### Scenario: VAD initialization failure
- **GIVEN** webrtcvad library is not available or fails to initialize
- **WHEN** starting transcription with VAD enabled
- **THEN** system SHALL log warning "VAD unavailable, continuing without VAD"
- **AND** system SHALL continue transcription without VAD filtering
- **AND** system SHALL not raise fatal error

#### Scenario: VAD processing failure
- **GIVEN** VAD is active
- **WHEN** is_speech() raises exception for specific chunk
- **THEN** system SHALL log warning with chunk details
- **AND** system SHALL assume chunk contains speech (pass to STT)
- **AND** system SHALL continue processing subsequent chunks

#### Scenario: Invalid audio format
- **GIVEN** audio chunk has incorrect format for webrtcvad
- **WHEN** VAD processes chunk
- **THEN** system SHALL raise VADError with format details
- **AND** error SHALL indicate expected format (16kHz, 16-bit, mono)
- **AND** system SHALL suggest checking audio capture configuration

### Requirement: VAD Statistics and Monitoring
The system SHALL track VAD performance metrics for debugging and optimization.

#### Scenario: Filter statistics
- **GIVEN** VAD is enabled and transcription is active
- **WHEN** processing multiple chunks
- **THEN** system SHALL count total chunks processed
- **AND** system SHALL count chunks with speech detected
- **AND** system SHALL count chunks filtered (silence)
- **AND** system SHALL log statistics periodically or on shutdown

#### Scenario: Verbose logging
- **GIVEN** user enables verbose or debug logging
- **WHEN** VAD processes chunks
- **THEN** system SHALL log each VAD decision (speech/silence)
- **AND** system SHALL log threshold and aggressiveness level
- **AND** system SHALL log timing information

### Requirement: VAD Testing
The system SHALL provide testing utilities to verify VAD configuration and performance.

#### Scenario: Test VAD sensitivity
- **GIVEN** user runs `voinux test-vad` (potential future command)
- **WHEN** command executes
- **THEN** system SHALL capture audio with VAD enabled
- **AND** system SHALL display real-time speech/silence detection
- **AND** system SHALL report detection accuracy
- **AND** system SHALL allow threshold adjustment during test

#### Scenario: VAD configuration in test-audio
- **GIVEN** user runs `voinux test-audio --vad`
- **WHEN** capturing audio
- **THEN** system SHALL overlay VAD speech detection on audio level meter
- **AND** system SHALL show periods detected as speech vs silence
- **AND** system SHALL display current VAD threshold
