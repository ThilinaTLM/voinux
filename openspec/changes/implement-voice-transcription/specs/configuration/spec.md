# Configuration Capability

## ADDED Requirements

### Requirement: Config Repository Port Interface
The system SHALL define an `IConfigRepository` port interface that abstracts configuration storage and retrieval operations.

#### Scenario: Adapter implements interface
- **GIVEN** a config repository adapter (e.g., YAMLConfigRepository)
- **WHEN** the adapter implements IConfigRepository interface
- **THEN** it SHALL provide load() method returning Config entity
- **AND** it SHALL provide save() method accepting Config entity
- **AND** it SHALL provide get_config_path() method
- **AND** it SHALL raise ConfigError on failures

#### Scenario: Configuration entity
- **GIVEN** any IConfigRepository implementation
- **WHEN** loading configuration
- **THEN** it SHALL return Config entity with all settings
- **AND** entity SHALL use dataclasses for type safety
- **AND** entity SHALL include validation methods

### Requirement: YAML Configuration Repository
The system SHALL provide a YAMLConfigRepository adapter for storing configuration in YAML format.

#### Scenario: Configuration file location
- **GIVEN** system initializes configuration
- **WHEN** determining config file path
- **THEN** system SHALL use `~/.config/voinux/config.yaml`
- **AND** system SHALL respect XDG_CONFIG_HOME environment variable
- **AND** system SHALL create config directory if it doesn't exist

#### Scenario: Load existing configuration
- **GIVEN** config file exists at standard location
- **WHEN** loading configuration
- **THEN** system SHALL parse YAML file
- **AND** system SHALL validate all fields
- **AND** system SHALL merge with defaults for missing fields
- **AND** system SHALL raise ConfigError if YAML is invalid

#### Scenario: Create default configuration
- **GIVEN** config file does not exist
- **WHEN** loading configuration
- **THEN** system SHALL generate config with default values
- **AND** system SHALL create config file automatically
- **AND** system SHALL log "Created default configuration" message

#### Scenario: Save configuration
- **GIVEN** user modifies configuration via CLI
- **WHEN** saving configuration
- **THEN** system SHALL write YAML to config file
- **AND** system SHALL preserve file permissions (0600)
- **AND** system SHALL create backup of previous config
- **AND** system SHALL format YAML with comments for readability

### Requirement: Configuration Schema
The system SHALL define a comprehensive configuration schema with sensible defaults for all settings.

#### Scenario: faster-whisper settings
- **GIVEN** configuration is loaded
- **WHEN** accessing faster-whisper settings
- **THEN** config SHALL include model (default: "large-v3-turbo")
- **AND** config SHALL include device (default: "auto")
- **AND** config SHALL include compute_type (default: "int8")
- **AND** config SHALL include language (default: "en")
- **AND** config SHALL include beam_size (default: 5)
- **AND** config SHALL include vad_filter (default: true)

#### Scenario: Audio settings
- **GIVEN** configuration is loaded
- **WHEN** accessing audio settings
- **THEN** config SHALL include sample_rate (default: 16000)
- **AND** config SHALL include channels (default: 1)
- **AND** config SHALL include chunk_duration_ms (default: 100)
- **AND** config SHALL include device (default: "default")
- **AND** config SHALL include backend (default: "auto")

#### Scenario: VAD settings
- **GIVEN** configuration is loaded
- **WHEN** accessing VAD settings
- **THEN** config SHALL include enabled (default: true)
- **AND** config SHALL include threshold (default: 0.5)
- **AND** config SHALL include silence_duration_ms (default: 1000)

#### Scenario: Keyboard settings
- **GIVEN** configuration is loaded
- **WHEN** accessing keyboard settings
- **THEN** config SHALL include backend (default: "auto")
- **AND** config SHALL include typing_delay_ms (default: 0)

#### Scenario: Application settings
- **GIVEN** configuration is loaded
- **WHEN** accessing app settings
- **THEN** config SHALL include continuous_mode (default: false)
- **AND** config SHALL include log_level (default: "info")
- **AND** config SHALL include hotkey (default: null)

### Requirement: Configuration Validation
The system SHALL validate configuration values to prevent invalid settings.

#### Scenario: Valid value ranges
- **GIVEN** user sets configuration values
- **WHEN** validating configuration
- **THEN** system SHALL enforce sample_rate in [8000, 16000, 48000]
- **AND** system SHALL enforce channels in [1, 2]
- **AND** system SHALL enforce chunk_duration_ms between 10 and 2000
- **AND** system SHALL enforce vad.threshold between 0.0 and 1.0
- **AND** system SHALL enforce beam_size between 1 and 10

#### Scenario: Valid enum values
- **GIVEN** user sets configuration enums
- **WHEN** validating configuration
- **THEN** system SHALL enforce device in ["auto", "cuda", "rocm", "cpu"]
- **AND** system SHALL enforce compute_type in ["float16", "int8", "float32"]
- **AND** system SHALL enforce log_level in ["debug", "info", "warning", "error"]
- **AND** system SHALL enforce keyboard.backend in ["auto", "xdotool", "ydotool", "stdout"]

#### Scenario: Invalid configuration
- **GIVEN** configuration contains invalid value
- **WHEN** loading configuration
- **THEN** system SHALL raise ConfigError with field name and valid options
- **AND** system SHALL not start with invalid configuration
- **AND** error SHALL suggest correcting config file

### Requirement: Configuration Precedence
The system SHALL apply configuration from multiple sources with clear precedence rules.

#### Scenario: Three-layer precedence
- **GIVEN** configuration from defaults, file, and CLI args
- **WHEN** resolving final configuration
- **THEN** system SHALL apply: CLI args > Config file > Defaults
- **AND** CLI args SHALL override config file values
- **AND** config file SHALL override default values
- **AND** unspecified values SHALL use defaults

#### Scenario: Partial configuration
- **GIVEN** config file specifies only some settings
- **WHEN** loading configuration
- **THEN** system SHALL use file values for specified settings
- **AND** system SHALL use defaults for unspecified settings
- **AND** system SHALL not require all fields in file

### Requirement: CLI Configuration Commands
The system SHALL provide CLI commands for viewing and modifying configuration.

#### Scenario: Show current configuration
- **GIVEN** user runs `voinux config show`
- **WHEN** command executes
- **THEN** system SHALL display all configuration values
- **AND** system SHALL indicate source (default/file/cli)
- **AND** system SHALL format as human-readable YAML
- **AND** system SHALL show config file path

#### Scenario: Set configuration value
- **GIVEN** user runs `voinux config set <key> <value>`
- **WHEN** command executes
- **THEN** system SHALL update specified key in config file
- **AND** system SHALL validate value before saving
- **AND** system SHALL confirm change with message
- **AND** system SHALL show updated value

#### Scenario: Get configuration value
- **GIVEN** user runs `voinux config get <key>`
- **WHEN** command executes
- **THEN** system SHALL display value of specified key
- **AND** system SHALL indicate if value is default or custom
- **AND** system SHALL return non-zero exit code if key doesn't exist

#### Scenario: Reset configuration
- **GIVEN** user runs `voinux config reset`
- **WHEN** command executes
- **THEN** system SHALL prompt user for confirmation
- **AND** system SHALL backup existing config
- **AND** system SHALL restore default configuration
- **AND** system SHALL confirm reset

#### Scenario: Edit configuration file
- **GIVEN** user runs `voinux config edit`
- **WHEN** command executes
- **THEN** system SHALL open config file in default editor ($EDITOR)
- **AND** system SHALL validate config after editor closes
- **AND** system SHALL warn if validation fails

### Requirement: Configuration File Format
The system SHALL use human-readable YAML with comments for documentation.

#### Scenario: YAML structure
- **GIVEN** configuration file is generated
- **WHEN** user opens config file
- **THEN** file SHALL be valid YAML
- **AND** file SHALL group related settings
- **AND** file SHALL include comments explaining each section
- **AND** file SHALL include comments with example values

#### Scenario: Default config template
- **GIVEN** system creates default config file
- **WHEN** writing file
- **THEN** system SHALL include all sections even if using defaults
- **AND** system SHALL comment out optional/advanced settings
- **AND** system SHALL include inline documentation for each field

### Requirement: Configuration Security
The system SHALL protect configuration files from unauthorized access.

#### Scenario: File permissions
- **GIVEN** system creates or updates config file
- **WHEN** writing to disk
- **THEN** system SHALL set permissions to 0600 (owner read/write only)
- **AND** system SHALL warn if permissions are too permissive
- **AND** system SHALL protect against world-readable config

#### Scenario: Sensitive data handling
- **GIVEN** configuration may contain sensitive data (future: API keys)
- **WHEN** storing configuration
- **THEN** system SHALL not log sensitive values
- **AND** system SHALL mask sensitive values in `config show` output
- **AND** system SHALL warn users about security when storing secrets

### Requirement: Configuration Migration
The system SHALL support configuration format changes across versions.

#### Scenario: Version field
- **GIVEN** configuration schema
- **WHEN** creating config file
- **THEN** system SHALL include version field (e.g., "1.0")
- **AND** system SHALL check version when loading
- **AND** system SHALL migrate old configs to new format if needed

#### Scenario: Backward compatibility
- **GIVEN** older config file without new fields
- **WHEN** loading configuration
- **THEN** system SHALL add missing fields with defaults
- **AND** system SHALL not break existing configs
- **AND** system SHALL log migration actions

### Requirement: Configuration Error Handling
The system SHALL handle configuration errors with clear messages and recovery guidance.

#### Scenario: Malformed YAML
- **GIVEN** config file contains syntax errors
- **WHEN** loading configuration
- **THEN** system SHALL raise ConfigError with YAML line number
- **AND** error SHALL show syntax error details
- **AND** error SHALL suggest fixing or resetting config

#### Scenario: Permission denied
- **GIVEN** config directory is not writable
- **WHEN** attempting to save configuration
- **THEN** system SHALL raise ConfigError "Permission denied"
- **AND** error SHALL show config directory path
- **AND** error SHALL suggest checking directory permissions

#### Scenario: Config file corruption
- **GIVEN** config file is corrupted or unreadable
- **WHEN** loading configuration
- **THEN** system SHALL attempt to load backup config
- **AND** system SHALL fall back to defaults if backup unavailable
- **AND** system SHALL log recovery action

### Requirement: Environment Variable Overrides
The system SHALL support environment variables for containerized and CI/CD deployments.

#### Scenario: Override via environment
- **GIVEN** environment variable VOINUX_MODEL is set
- **WHEN** loading configuration
- **THEN** system SHALL use environment value for model setting
- **AND** environment SHALL override config file (but not CLI args)
- **AND** system SHALL support VOINUX_* prefix for all config keys

#### Scenario: Environment variable mapping
- **GIVEN** hierarchical config keys (e.g., faster_whisper.model)
- **WHEN** mapping to environment variables
- **THEN** system SHALL use format VOINUX_FASTER_WHISPER_MODEL
- **AND** system SHALL use underscores for nesting
- **AND** system SHALL be case-insensitive

### Requirement: Configuration Documentation
The system SHALL provide comprehensive documentation for all configuration options.

#### Scenario: In-file documentation
- **GIVEN** default config file
- **WHEN** user opens config file
- **THEN** file SHALL include comment for each setting
- **AND** comments SHALL explain purpose and valid values
- **AND** comments SHALL include examples

#### Scenario: CLI help for config commands
- **GIVEN** user runs `voinux config --help`
- **WHEN** displaying help
- **THEN** system SHALL list all config subcommands
- **AND** system SHALL explain config precedence
- **AND** system SHALL show example usage
