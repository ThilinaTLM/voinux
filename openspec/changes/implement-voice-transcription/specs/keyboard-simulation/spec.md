# Keyboard Simulation Capability

## ADDED Requirements

### Requirement: Keyboard Simulator Port Interface
The system SHALL define an `IKeyboardSimulator` port interface that abstracts keyboard output operations, allowing different keyboard backend implementations to be used interchangeably.

#### Scenario: Adapter implements interface
- **GIVEN** a keyboard simulator adapter (e.g., XDotool, YDotool)
- **WHEN** the adapter implements IKeyboardSimulator interface
- **THEN** it SHALL provide async type_text() method accepting string
- **AND** it SHALL support initialize() and test_capability() methods
- **AND** it SHALL raise KeyboardSimulationError on failures

#### Scenario: Typing behavior
- **GIVEN** any IKeyboardSimulator implementation
- **WHEN** typing text into active window
- **THEN** typing SHALL occur in currently focused application
- **AND** typing SHALL not switch focus or activate other windows
- **AND** special characters SHALL be properly escaped/handled

### Requirement: XDotool Keyboard Adapter
The system SHALL provide an XDotoolKeyboard adapter for X11 display servers using the xdotool command-line tool.

#### Scenario: X11 typing
- **GIVEN** system is running X11 display server
- **WHEN** typing text with XDotoolKeyboard
- **THEN** system SHALL invoke `xdotool type --clearmodifiers --` command
- **AND** text SHALL appear in currently active X11 window
- **AND** typing SHALL complete within 100ms for typical sentences

#### Scenario: Handle special characters
- **GIVEN** transcription contains special characters (quotes, brackets, newlines)
- **WHEN** typing with xdotool
- **THEN** system SHALL properly escape shell special characters
- **AND** system SHALL use `--` to prevent argument interpretation
- **AND** characters SHALL appear correctly in target application

#### Scenario: xdotool availability check
- **GIVEN** XDotoolKeyboard adapter is selected
- **WHEN** initializing adapter
- **THEN** system SHALL verify xdotool binary exists in PATH
- **AND** system SHALL raise KeyboardSimulationError if not found
- **AND** error SHALL suggest installing xdotool package

### Requirement: YDotool Keyboard Adapter
The system SHALL provide a YDotoolKeyboard adapter for Wayland display servers using the ydotool command-line tool.

#### Scenario: Wayland typing
- **GIVEN** system is running Wayland display server
- **WHEN** typing text with YDotoolKeyboard
- **THEN** system SHALL invoke `ydotool type --` command
- **AND** text SHALL appear in currently active Wayland window
- **AND** typing SHALL respect Wayland security model

#### Scenario: uinput permissions check
- **GIVEN** YDotoolKeyboard adapter is selected
- **WHEN** initializing adapter
- **THEN** system SHALL verify user has uinput device access
- **AND** system SHALL check user is in 'input' group
- **AND** system SHALL raise KeyboardSimulationError if permissions insufficient
- **AND** error SHALL suggest running `sudo usermod -aG input $USER`

#### Scenario: ydotool daemon check
- **GIVEN** YDotoolKeyboard adapter is selected
- **WHEN** initializing adapter
- **THEN** system SHALL verify ydotool binary exists
- **AND** system MAY check if ydotoold daemon is running
- **AND** error SHALL provide troubleshooting steps if ydotool fails

### Requirement: Stdout Keyboard Adapter
The system SHALL provide a StdoutKeyboard adapter for testing and debugging that prints text to standard output instead of simulating keystrokes.

#### Scenario: Testing mode
- **GIVEN** StdoutKeyboard adapter is used
- **WHEN** typing text
- **THEN** system SHALL print text to stdout with prefix "TYPED: "
- **AND** system SHALL not invoke any keyboard simulation tools
- **AND** system SHALL always succeed (no external dependencies)

#### Scenario: Automatic fallback
- **GIVEN** neither xdotool nor ydotool are available
- **WHEN** system initializes keyboard adapter
- **THEN** system SHALL fall back to StdoutKeyboard
- **AND** system SHALL log warning about fallback mode

### Requirement: Display Server Auto-Detection
The system SHALL automatically detect the display server (X11 or Wayland) and select the appropriate keyboard backend.

#### Scenario: Wayland detection
- **GIVEN** XDG_SESSION_TYPE environment variable is "wayland"
- **WHEN** auto-detecting keyboard backend
- **THEN** system SHALL select YDotoolKeyboard
- **AND** system SHALL verify ydotool is available
- **AND** system SHALL fall back to XDotoolKeyboard if ydotool unavailable

#### Scenario: X11 detection
- **GIVEN** XDG_SESSION_TYPE environment variable is "x11" or unset
- **WHEN** auto-detecting keyboard backend
- **THEN** system SHALL select XDotoolKeyboard
- **AND** system SHALL verify xdotool is available
- **AND** system SHALL fall back to StdoutKeyboard if xdotool unavailable

#### Scenario: Explicit backend override
- **GIVEN** user specifies keyboard backend in configuration
- **WHEN** initializing keyboard adapter
- **THEN** system SHALL use specified backend (xdotool/ydotool/stdout)
- **AND** system SHALL not perform auto-detection
- **AND** system SHALL raise error if specified backend unavailable

### Requirement: Typing Mode Configuration
The system SHALL support different typing modes for different use cases and performance characteristics.

#### Scenario: Instant mode (default)
- **GIVEN** typing_delay_ms is 0 in configuration
- **WHEN** typing text
- **THEN** system SHALL send entire text as single command (paste-like behavior)
- **AND** typing SHALL complete in single operation
- **AND** typing SHALL be fastest mode

#### Scenario: Delayed mode
- **GIVEN** typing_delay_ms is >0 in configuration
- **WHEN** typing text
- **THEN** system SHALL type character-by-character with specified delay
- **AND** delay SHALL apply between each character
- **AND** mode SHALL simulate more natural typing (if needed for compatibility)

### Requirement: Text Sanitization
The system SHALL sanitize transcription text before keyboard simulation to prevent command injection and handle special cases.

#### Scenario: Command injection prevention
- **GIVEN** transcription text contains shell metacharacters
- **WHEN** preparing text for keyboard simulation
- **THEN** system SHALL properly escape characters for subprocess calls
- **AND** system SHALL use parameterized commands when possible
- **AND** system SHALL prevent unintended command execution

#### Scenario: Empty text handling
- **GIVEN** transcription result has empty or whitespace-only text
- **WHEN** attempting to type
- **THEN** system SHALL skip keyboard simulation
- **AND** system SHALL not invoke keyboard tool
- **AND** system SHALL log debug message about empty text

#### Scenario: Text length limits
- **GIVEN** transcription exceeds reasonable length (e.g., >10000 characters)
- **WHEN** attempting to type
- **THEN** system SHALL log warning about unusually long text
- **AND** system MAY chunk text into smaller segments
- **AND** system SHALL handle entire text without truncation

### Requirement: Error Handling
The system SHALL handle keyboard simulation errors with clear messages and recovery guidance.

#### Scenario: Tool execution failure
- **GIVEN** xdotool or ydotool command fails
- **WHEN** attempting to type text
- **THEN** system SHALL raise KeyboardSimulationError with exit code and stderr
- **AND** system SHALL log the command that failed
- **AND** system SHALL continue processing next transcription (non-fatal)

#### Scenario: Permission denied
- **GIVEN** user lacks permissions for keyboard simulation
- **WHEN** initializing keyboard adapter
- **THEN** system SHALL raise KeyboardSimulationError with clear message
- **AND** error SHALL indicate permission issue (uinput on Wayland)
- **AND** error SHALL provide fix instructions

#### Scenario: No active window
- **GIVEN** no window has keyboard focus
- **WHEN** attempting to type text
- **THEN** xdotool/ydotool SHALL handle as per tool behavior (may fail or type nowhere)
- **AND** system SHALL log warning if typing fails
- **AND** system SHALL continue processing next transcription

### Requirement: Keyboard Testing
The system SHALL provide a test command to verify keyboard simulation functionality.

#### Scenario: Test keyboard typing
- **GIVEN** user runs `voinux test-keyboard`
- **WHEN** command executes
- **THEN** system SHALL display detected display server (X11/Wayland)
- **AND** system SHALL display selected keyboard backend
- **AND** system SHALL wait for user confirmation to proceed
- **AND** system SHALL type test message "Hello from Voinux!"
- **AND** system SHALL report success or failure

#### Scenario: Test with focus check
- **GIVEN** user runs `voinux test-keyboard`
- **WHEN** test begins
- **THEN** system SHALL prompt user to focus a text editor
- **AND** system SHALL wait 3 seconds before typing
- **AND** system SHALL verify text appeared (via user confirmation)

### Requirement: Typing Performance
The system SHALL ensure keyboard simulation does not introduce significant latency to the transcription pipeline.

#### Scenario: Low latency typing
- **GIVEN** transcription result is ready
- **WHEN** typing text (instant mode)
- **THEN** keyboard simulation SHALL complete within 100ms
- **AND** typing SHALL not block audio capture or STT processing
- **AND** typing SHALL occur asynchronously

#### Scenario: Concurrent typing
- **GIVEN** multiple transcription results arrive rapidly
- **WHEN** typing multiple texts
- **THEN** system SHALL queue typing operations
- **AND** system SHALL maintain text order
- **AND** system SHALL not interleave characters from different texts
