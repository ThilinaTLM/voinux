# CLI Interface Capability

## ADDED Requirements

### Requirement: Click Framework Integration
The system SHALL use Click framework for command-line interface implementation.

#### Scenario: CLI entry point
- **GIVEN** user invokes `voinux` command
- **WHEN** command is executed
- **THEN** system SHALL use Click as CLI framework
- **AND** system SHALL support subcommands and options
- **AND** system SHALL generate automatic help text

#### Scenario: Help text
- **GIVEN** user runs `voinux --help`
- **WHEN** displaying help
- **THEN** system SHALL show application description
- **AND** system SHALL list all available commands
- **AND** system SHALL show version with `--version` flag

### Requirement: Start Command
The system SHALL provide a `start` command to begin real-time voice transcription.

#### Scenario: Basic start
- **GIVEN** user runs `voinux start`
- **WHEN** command executes
- **THEN** system SHALL initialize all components (audio, STT, keyboard, VAD)
- **AND** system SHALL display "Listening..." message
- **AND** system SHALL begin real-time transcription
- **AND** system SHALL run until Ctrl+C pressed

#### Scenario: Start with language override
- **GIVEN** user runs `voinux start --lang es`
- **WHEN** command executes
- **THEN** system SHALL override configured language
- **AND** system SHALL transcribe in Spanish
- **AND** system SHALL not modify config file

#### Scenario: Start with model override
- **GIVEN** user runs `voinux start --model medium`
- **WHEN** command executes
- **THEN** system SHALL override configured model
- **AND** system SHALL use medium model for session
- **AND** system SHALL download model if not cached

#### Scenario: Continuous mode
- **GIVEN** user runs `voinux start --continuous`
- **WHEN** command executes
- **THEN** system SHALL run in continuous mode (always listening)
- **AND** system SHALL auto-restart on errors
- **AND** system SHALL run until explicitly stopped

#### Scenario: Device override
- **GIVEN** user runs `voinux start --device cuda` or `--device cpu`
- **WHEN** command executes
- **THEN** system SHALL override configured device
- **AND** system SHALL use specified device for transcription

#### Scenario: VAD threshold override
- **GIVEN** user runs `voinux start --vad-threshold 0.7`
- **WHEN** command executes
- **THEN** system SHALL override configured VAD threshold
- **AND** system SHALL use specified sensitivity

#### Scenario: Hotkey activation
- **GIVEN** user runs `voinux start --hotkey "ctrl+alt+v"`
- **WHEN** command executes
- **THEN** system SHALL register global hotkey
- **AND** system SHALL only transcribe when hotkey is pressed
- **AND** system SHALL release when hotkey is released

#### Scenario: Graceful shutdown
- **GIVEN** transcription is active
- **WHEN** user presses Ctrl+C
- **THEN** system SHALL stop audio capture
- **AND** system SHALL flush pending transcriptions
- **AND** system SHALL display session statistics
- **AND** system SHALL exit cleanly with code 0

### Requirement: Configuration Commands
The system SHALL provide `config` subcommands for managing configuration.

#### Scenario: Config show
- **GIVEN** user runs `voinux config show`
- **WHEN** command executes
- **THEN** system SHALL display full configuration as YAML
- **AND** system SHALL show config file path
- **AND** system SHALL indicate effective values (after precedence)

#### Scenario: Config get
- **GIVEN** user runs `voinux config get faster_whisper.model`
- **WHEN** command executes
- **THEN** system SHALL display value of specified key
- **AND** system SHALL exit with code 0 if key exists
- **AND** system SHALL exit with code 1 if key doesn't exist

#### Scenario: Config set
- **GIVEN** user runs `voinux config set faster_whisper.model large-v3`
- **WHEN** command executes
- **THEN** system SHALL update config file with new value
- **AND** system SHALL validate value before saving
- **AND** system SHALL display confirmation message

#### Scenario: Config reset
- **GIVEN** user runs `voinux config reset`
- **WHEN** command executes
- **THEN** system SHALL prompt for confirmation (y/n)
- **AND** system SHALL backup existing config
- **AND** system SHALL restore defaults
- **AND** system SHALL display "Configuration reset to defaults"

#### Scenario: Config edit
- **GIVEN** user runs `voinux config edit`
- **WHEN** command executes
- **THEN** system SHALL open config file in $EDITOR
- **AND** system SHALL validate config after editor closes
- **AND** system SHALL warn if invalid changes made

### Requirement: Test Commands
The system SHALL provide test commands to verify system components.

#### Scenario: Test audio
- **GIVEN** user runs `voinux test-audio`
- **WHEN** command executes
- **THEN** system SHALL capture 3 seconds of audio
- **AND** system SHALL display real-time audio level meter
- **AND** system SHALL report audio backend used
- **AND** system SHALL report sample rate and channels

#### Scenario: Test audio with device
- **GIVEN** user runs `voinux test-audio --device "USB Mic"`
- **WHEN** command executes
- **THEN** system SHALL capture from specified device
- **AND** system SHALL validate device exists

#### Scenario: Test GPU
- **GIVEN** user runs `voinux test-gpu`
- **WHEN** command executes
- **THEN** system SHALL detect CUDA/ROCm availability
- **AND** system SHALL display GPU device name and VRAM
- **AND** system SHALL display PyTorch version and device support
- **AND** system SHALL recommend configuration

#### Scenario: Test model
- **GIVEN** user runs `voinux test-model`
- **WHEN** command executes
- **THEN** system SHALL load configured model
- **AND** system SHALL transcribe test audio (5 seconds)
- **AND** system SHALL report inference time and latency
- **AND** system SHALL display transcription result

#### Scenario: Test keyboard
- **GIVEN** user runs `voinux test-keyboard`
- **WHEN** command executes
- **THEN** system SHALL detect display server (X11/Wayland)
- **AND** system SHALL display selected keyboard backend
- **AND** system SHALL prompt user to focus text editor
- **AND** system SHALL type "Hello from Voinux!" after 3-second delay
- **AND** system SHALL report success or failure

### Requirement: Model Commands
The system SHALL provide `model` subcommands for managing Whisper models.

#### Scenario: Model download
- **GIVEN** user runs `voinux model download large-v3-turbo`
- **WHEN** command executes
- **THEN** system SHALL download specified model
- **AND** system SHALL display progress bar
- **AND** system SHALL save to cache directory
- **AND** system SHALL verify integrity

#### Scenario: Model download with force
- **GIVEN** user runs `voinux model download --force large-v3`
- **WHEN** command executes
- **THEN** system SHALL re-download model even if cached
- **AND** system SHALL overwrite existing cached model

#### Scenario: Model list
- **GIVEN** user runs `voinux model list`
- **WHEN** command executes
- **THEN** system SHALL scan cache directory
- **AND** system SHALL display table with columns: name, size, cached
- **AND** system SHALL indicate current model with asterisk (*)
- **AND** system SHALL show total cache size

#### Scenario: Model info
- **GIVEN** user runs `voinux model info`
- **WHEN** command executes
- **THEN** system SHALL display current model configuration
- **AND** system SHALL show VRAM requirements (FP16, INT8)
- **AND** system SHALL show cache status (cached/not cached)
- **AND** system SHALL show cache path

### Requirement: Setup Wizard
The system SHALL provide a `setup` command to guide first-time users through configuration.

#### Scenario: Setup wizard
- **GIVEN** user runs `voinux setup`
- **WHEN** command executes
- **THEN** system SHALL detect GPU and CUDA/ROCm availability
- **AND** system SHALL detect display server (X11/Wayland)
- **AND** system SHALL verify audio capture capability
- **AND** system SHALL verify keyboard simulation capability
- **AND** system SHALL recommend model based on VRAM
- **AND** system SHALL offer to download recommended model
- **AND** system SHALL create default configuration
- **AND** system SHALL run end-to-end test

#### Scenario: Setup with interactive prompts
- **GIVEN** setup wizard is running
- **WHEN** prompting user for choices
- **THEN** system SHALL ask which model to download (if multiple suitable)
- **AND** system SHALL ask which language to configure
- **AND** system SHALL ask whether to enable VAD
- **AND** system SHALL provide sensible defaults for each prompt

#### Scenario: Setup completion
- **GIVEN** setup wizard completes successfully
- **WHEN** wizard finishes
- **THEN** system SHALL display summary of configuration
- **AND** system SHALL show next steps (run `voinux start`)
- **AND** system SHALL create config file if doesn't exist

### Requirement: CLI Output Formatting
The system SHALL provide clear, user-friendly output with appropriate formatting.

#### Scenario: Status messages
- **GIVEN** commands are executing
- **WHEN** displaying status
- **THEN** system SHALL use consistent formatting
- **AND** system SHALL use colors (if terminal supports)
- **AND** system SHALL show progress indicators for long operations

#### Scenario: Error messages
- **GIVEN** errors occur
- **WHEN** displaying errors
- **THEN** system SHALL prefix with "Error: " in red
- **AND** system SHALL provide clear description
- **AND** system SHALL suggest remediation steps
- **AND** system SHALL exit with non-zero code

#### Scenario: Success messages
- **GIVEN** operations succeed
- **WHEN** displaying success
- **THEN** system SHALL use green color for success indicators
- **AND** system SHALL be concise but informative

#### Scenario: Progress bars
- **GIVEN** long-running operations (downloads, processing)
- **WHEN** operation is in progress
- **THEN** system SHALL display progress bar with percentage
- **AND** system SHALL show operation description
- **AND** system SHALL update progress in real-time

### Requirement: Real-time Status Display
The system SHALL display real-time transcription status during active session.

#### Scenario: Listening indicator
- **GIVEN** transcription is active
- **WHEN** waiting for speech
- **THEN** system SHALL display "Listening..." message
- **AND** system SHALL show audio level meter (optional)
- **AND** system SHALL indicate VAD status (speech/silence)

#### Scenario: Transcription feedback
- **GIVEN** audio is being transcribed
- **WHEN** processing chunk
- **THEN** system SHALL display "Transcribing..." indicator
- **AND** system SHALL show interim results if available
- **AND** system SHALL show latency for each transcription

#### Scenario: Session statistics
- **GIVEN** user stops transcription (Ctrl+C)
- **WHEN** session ends
- **THEN** system SHALL display total session duration
- **AND** system SHALL show total chunks processed
- **AND** system SHALL show average latency
- **AND** system SHALL show VAD filter rate (% chunks filtered)

### Requirement: Logging Configuration
The system SHALL support configurable logging levels via CLI and configuration.

#### Scenario: Verbose mode
- **GIVEN** user runs `voinux start --verbose` or `-v`
- **WHEN** command executes
- **THEN** system SHALL set log level to DEBUG
- **AND** system SHALL display detailed operational logs
- **AND** system SHALL show component initialization details

#### Scenario: Quiet mode
- **GIVEN** user runs `voinux start --quiet` or `-q`
- **WHEN** command executes
- **THEN** system SHALL set log level to ERROR
- **AND** system SHALL suppress info and warning messages
- **AND** system SHALL only show errors

#### Scenario: Log level via config
- **GIVEN** user sets app.log_level in config
- **WHEN** running any command
- **THEN** system SHALL use configured log level
- **AND** CLI flags SHALL override config log level

### Requirement: Error Handling and Exit Codes
The system SHALL use appropriate exit codes and error handling for scripting integration.

#### Scenario: Success exit code
- **GIVEN** command completes successfully
- **WHEN** exiting
- **THEN** system SHALL exit with code 0

#### Scenario: Error exit codes
- **GIVEN** command fails
- **WHEN** exiting
- **THEN** system SHALL exit with non-zero code
- **AND** code 1 SHALL indicate general errors
- **AND** code 2 SHALL indicate configuration errors
- **AND** code 130 SHALL indicate user interrupt (Ctrl+C)

#### Scenario: Error message format
- **GIVEN** error occurs
- **WHEN** displaying error
- **THEN** system SHALL write to stderr (not stdout)
- **AND** system SHALL include error type and description
- **AND** system SHALL suggest remediation when possible

### Requirement: Package Entry Point
The system SHALL provide multiple invocation methods for user convenience.

#### Scenario: Command invocation
- **GIVEN** voinux is installed
- **WHEN** user invokes application
- **THEN** system SHALL support `voinux` command
- **AND** system SHALL support `python -m voinux` invocation

#### Scenario: Version display
- **GIVEN** user runs `voinux --version`
- **WHEN** command executes
- **THEN** system SHALL display version number
- **AND** system SHALL display Python version
- **AND** system SHALL display platform information

### Requirement: Signal Handling
The system SHALL handle Unix signals gracefully for clean shutdown.

#### Scenario: SIGINT handling (Ctrl+C)
- **GIVEN** transcription is active
- **WHEN** user presses Ctrl+C
- **THEN** system SHALL catch SIGINT signal
- **AND** system SHALL stop transcription gracefully
- **AND** system SHALL clean up resources
- **AND** system SHALL exit with code 130

#### Scenario: SIGTERM handling
- **GIVEN** transcription is active
- **WHEN** system receives SIGTERM
- **THEN** system SHALL stop transcription
- **AND** system SHALL flush pending work
- **AND** system SHALL exit cleanly

### Requirement: CLI Accessibility
The system SHALL provide accessible CLI interface following Linux conventions.

#### Scenario: Standard streams
- **GIVEN** any command execution
- **WHEN** producing output
- **THEN** system SHALL write normal output to stdout
- **AND** system SHALL write errors to stderr
- **AND** system SHALL support piping and redirection

#### Scenario: Non-interactive mode
- **GIVEN** stdin is not a TTY
- **WHEN** commands require user input
- **THEN** system SHALL use default values or fail gracefully
- **AND** system SHALL not hang waiting for input

#### Scenario: Color detection
- **GIVEN** terminal capabilities vary
- **WHEN** using colored output
- **THEN** system SHALL detect color support
- **AND** system SHALL disable colors if not supported
- **AND** system SHALL respect NO_COLOR environment variable
