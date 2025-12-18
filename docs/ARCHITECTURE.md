# USB Relay Controller - Architecture Documentation

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Design Patterns](#design-patterns)
- [Module Descriptions](#module-descriptions)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)

## Overview

The USB Relay Controller follows a modern Python application architecture with clear separation of concerns, dependency injection, and extensive use of Python's advanced features including type hints, dataclasses, abstract base classes, and context managers.

### Key Architectural Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Injection**: Configuration and dependencies are injected, not hardcoded
3. **Interface Segregation**: Abstract base classes define clear contracts
4. **DRY Principle**: Reusable components are extracted into mixins and utilities
5. **Type Safety**: Comprehensive type hints throughout the codebase

## Project Structure

```
relay/
├── __init__.py                 # Package initialization and exports
├── constants.py                # Global constants and enums
│
├── core/                       # Core infrastructure
│   ├── __init__.py
│   ├── config.py              # Configuration management (dataclasses)
│   └── base.py                # Abstract base classes and mixins
│
├── hardware/                   # Hardware communication layer
│   ├── __init__.py
│   ├── protocol.py            # Protocol frame builder
│   └── serial_comm.py         # Serial communication (context manager)
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── relay_utils.py         # Device and Task classes
│   ├── database.py            # Database operations (context manager)
│   └── usb_info.py            # USB device information via DLL
│
├── server/                     # Server implementation
│   ├── __init__.py
│   └── task_manager.py        # Task management and server logic
│
├── controllers/                # Business logic controllers
│   ├── __init__.py
│   ├── recovery.py            # Device recovery controller
│   └── initializer.py         # Device initialization controller
│
└── cli/                        # Command-line interfaces
    ├── __init__.py
    ├── server.py              # Server CLI
    ├── recover.py             # Recovery CLI
    └── initialize.py          # Initialization CLI
```

## Design Patterns

### 1. Singleton Pattern

**Used in**: `ConfigManager`

Ensures only one configuration instance exists throughout the application lifecycle.

```python
class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. Context Manager Pattern

**Used in**: `SerialCommunicator`, `DatabaseManager`, `BaseRelayController`

Provides automatic resource management using `__enter__` and `__exit__` methods.

```python
with SerialCommunicator('relay') as serial:
    serial.usb_on(1)
    # Automatically closes connection on exit
```

### 3. Mixin Pattern

**Used in**: `ADBCommandMixin`

Provides reusable functionality that can be added to multiple classes.

```python
class DeviceRecoveryController(BaseRelayController, ADBCommandMixin):
    # Inherits ADB functionality without tight coupling
    pass
```

### 4. Factory Pattern

**Used in**: `LoggerFactory`

Centralized creation of configured logger instances.

```python
logger = LoggerFactory.get_logger('MyModule', serial_number='ABC123')
```

### 5. Strategy Pattern

**Used in**: Protocol frame builders

Different strategies for building communication frames based on command type.

```python
protocol.build_usb_on_by_index(port)
protocol.build_usb_on_by_value(hub_value)
```

## Module Descriptions

### Core Modules

#### `core/config.py`

Manages application configuration using dataclasses:

- **`DatabaseConfig`**: Database connection parameters
- **`ServerConfig`**: Server network settings
- **`RelayConfig`**: Main configuration container
- **`ConfigManager`**: Singleton configuration loader
- **`LoggerFactory`**: Centralized logger creation

**Key Features**:
- Loads configuration from multiple sources (env vars, files, defaults)
- Immutable configuration using dataclasses
- Colored console output on Windows

#### `core/base.py`

Provides abstract base classes and mixins:

- **`BaseRelayController`**: Abstract base for all controllers
- **`ADBCommandMixin`**: Reusable ADB command execution

**Key Features**:
- Abstract methods enforce interface contracts
- Context manager support for resource management
- State management for controller lifecycle

### Hardware Layer

#### `hardware/protocol.py`

Implements relay communication protocol:

- **`ProtocolFrameBuilder`**: Frame construction for relay commands

**Protocol Format**:
```
[HEAD][LEN][INDEX][MODE][STATE][XOR][END]
```

**Key Features**:
- Stateless frame building
- XOR checksum calculation
- Hex string conversion utilities

#### `hardware/serial_comm.py`

High-level serial communication:

- **`SerialCommunicator`**: Serial port interface with context manager

**Key Features**:
- Automatic port detection
- Type-safe command methods
- Comprehensive logging
- Resource cleanup

### Utilities

#### `utils/relay_utils.py`

Data structures for relay operations:

- **`Device`**: Represents a device on a relay port
- **`Task`**: Represents a relay control task

**Key Features**:
- Property decorators for validation
- Rich comparison methods
- Clear `__repr__` for debugging

#### `utils/database.py`

Database operations with modern Python:

- **`DatabaseManager`**: MySQL operations with context manager

**Key Features**:
- Context manager for connection handling
- Type-safe method signatures
- Comprehensive error handling
- Alternative MySQL library support (PyMySQL/MySQLdb)

#### `utils/usb_info.py`

Windows USB device information:

- **`USBDeviceInfo`**: DLL interface for USB device queries

**Key Features**:
- Ctypes integration for Win32 DLL
- Multiple USB hub ID detection methods
- Comprehensive device information retrieval

### Controllers

Controllers implement business logic using the base class:

```python
class DeviceRecoveryController(BaseRelayController, ADBCommandMixin):
    def initialize(self) -> bool:
        # Setup logic
        pass
    
    def execute(self) -> bool:
        # Main recovery logic
        pass
    
    def cleanup(self) -> None:
        # Resource cleanup
        pass
```

### CLI Layer

Each CLI module provides:
- Argument parsing with argparse
- Help text and examples
- Proper exit codes
- Error handling

## Data Flow

### 1. Device Recovery Flow

```
User Command
    ↓
CLI (recover.py)
    ↓
DeviceRecoveryController
    ├→ ConfigManager (load settings)
    ├→ DatabaseManager (log attempts)
    ├→ USBDeviceInfo (get hub ID)
    ├→ RelayClient (send control commands)
    │      ↓
    │   RelayServer
    │      ├→ SerialCommunicator
    │      └→ ProtocolFrameBuilder
    └→ ADB Commands (verify recovery)
```

### 2. Server Request Flow

```
Client Request (pickle)
    ↓
TaskManager (socket server)
    ↓
Task Queue
    ↓
Task Handler
    ├→ Parse command
    ├→ SerialCommunicator
    │      ├→ ProtocolFrameBuilder
    │      └→ Serial Port
    └→ Response (pickle)
```

## Extension Points

### Adding New Commands

1. Add constant to `constants.py`:
```python
RELAY_NEW_COMMAND_MSG = 6
```

2. Add protocol method in `hardware/protocol.py`:
```python
def build_new_command(self, param: int) -> List[int]:
    # Build frame
    pass
```

3. Add handler in server task manager:
```python
elif event == Constants.RELAY_NEW_COMMAND_MSG:
    self.serial.execute_new_command(param)
```

### Adding New Controllers

1. Inherit from `BaseRelayController`:
```python
class MyController(BaseRelayController):
    def initialize(self) -> bool:
        # Setup
        return True
    
    def execute(self) -> bool:
        # Main logic
        return True
    
    def cleanup(self) -> None:
        # Cleanup
        pass
```

2. Add CLI interface in `cli/` directory

3. Register entry point in `setup.py`

### Adding Configuration Options

1. Add to appropriate dataclass in `core/config.py`:
```python
@dataclass
class RelayConfig:
    new_option: str = 'default_value'
```

2. Update configuration loading in `ConfigManager._load_config()`

3. Document in `config.example.py`

## Type Hints Strategy

The project uses comprehensive type hints:

```python
def process_device(
    serial_number: str,
    timeout: int = 10,
    force: bool = False
) -> Optional[Device]:
    """
    Process device with explicit types.
    
    Args:
        serial_number: Device SN
        timeout: Operation timeout
        force: Force operation
    
    Returns:
        Device instance or None if failed
    """
    pass
```

Benefits:
- IDE autocomplete
- Static type checking with mypy
- Self-documenting code
- Catch errors before runtime

## Best Practices

1. **Always use type hints** for function parameters and return values
2. **Use dataclasses** for data structures (config, DTOs)
3. **Implement context managers** for resources (connections, files)
4. **Use abstract base classes** to define interfaces
5. **Prefer composition over inheritance** (mixins)
6. **Log liberally** with appropriate levels
7. **Validate inputs** early and explicitly
8. **Handle errors gracefully** with specific exception types
9. **Write docstrings** for all public APIs
10. **Use enums** for constants that have fixed sets of values

## Testing Strategy

```python
# Unit tests
tests/
├── test_protocol.py      # Protocol frame building
├── test_database.py      # Database operations
├── test_usb_info.py      # USB device info

# Integration tests
tests/integration/
├── test_serial_comm.py   # Serial communication
├── test_server.py        # Server operations

# End-to-end tests
tests/e2e/
└── test_recovery_flow.py # Full recovery workflow
```

## Performance Considerations

1. **Connection Pooling**: Reuse serial and database connections
2. **Lazy Loading**: Load resources only when needed
3. **Caching**: Cache USB device info and relay states
4. **Async Operations**: Consider asyncio for concurrent device management
5. **Batch Operations**: Group database updates

## Security Considerations

1. **Configuration**: Store credentials in env vars or secure config files
2. **Input Validation**: Validate all user inputs and serial numbers
3. **SQL Injection**: Use parameterized queries
4. **Access Control**: Limit server binding to localhost by default
5. **Logging**: Don't log sensitive information (passwords, etc.)

---

For more information, see:
- [API Documentation](API.md)
- [User Guide](USER_GUIDE.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

