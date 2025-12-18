# API Documentation

Complete API reference for USB Relay Controller.

## Table of Contents

- [Core Classes](#core-classes)
- [Hardware Layer](#hardware-layer)
- [Utilities](#utilities)
- [Controllers](#controllers)
- [Constants](#constants)

## Core Classes

### ConfigManager

Singleton configuration manager.

```python
from relay.core.config import ConfigManager

# Get configuration instance
config_manager = ConfigManager()
config = config_manager.config

# Access configuration
print(config.database.host)
print(config.server.port)

# Update configuration
config_manager.update_config(adb_timeout=15)
```

### LoggerFactory

Factory for creating configured loggers.

```python
from relay.core.config import LoggerFactory

# Get logger for specific device
logger = LoggerFactory.get_logger('MyModule', serial_number='ABC123')

# Get server logger
server_logger = LoggerFactory.get_server_logger()

# Use logger
logger.info('Operation started')
logger.error('Operation failed', exc_info=True)
```

### BaseRelayController

Abstract base class for controllers.

```python
from relay.core.base import BaseRelayController

class MyController(BaseRelayController):
    def initialize(self) -> bool:
        """Initialize controller."""
        self.log_section('Initializing')
        return True
    
    def execute(self) -> bool:
        """Execute main logic."""
        self.logger.info('Executing...')
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.logger.info('Cleaning up')

# Use as context manager
with MyController('ABC123') as controller:
    success = controller.execute()
```

### ADBCommandMixin

Mixin providing ADB operations.

```python
from relay.core.base import BaseRelayController, ADBCommandMixin

class MyController(BaseRelayController, ADBCommandMixin):
    def execute(self) -> bool:
        # Check ADB connection
        if not self.is_adb_connected():
            self.logger.error('ADB not connected')
            return False
        
        # Execute shell command
        result = self.execute_shell_command('getprop ro.build.version.release')
        self.logger.info(f'Android version: {result}')
        
        # Wait for ADB
        if self.wait_for_adb(timeout=10):
            self.logger.info('ADB connected')
        
        return True
```

## Hardware Layer

### ProtocolFrameBuilder

Builds communication frames for relay hardware.

```python
from relay.hardware.protocol import ProtocolFrameBuilder

protocol = ProtocolFrameBuilder()

# Build frames for different commands
frame_on = protocol.build_usb_on_by_index(port_index=1)
frame_off = protocol.build_usb_off_by_index(port_index=1)
frame_states = protocol.build_get_port_states()

# Calculate checksum
checksum = protocol.calculate_xor([126, 7, 1, 64, 255])

# Convert to hex string
hex_str = protocol.bytes_to_hex_string([126, 7, 1, 64, 255, 185, 85])
# Output: '7e 07 01 40 ff b9 55'
```

### SerialCommunicator

High-level serial communication interface.

```python
from relay.hardware.serial_comm import SerialCommunicator

# Initialize (auto-connects to first available port)
with SerialCommunicator('relay') as serial:
    # Check if open
    if serial.is_open:
        # Control operations
        serial.usb_on(port_index=1)           # Turn on port 1
        serial.usb_off(port_index=1)          # Turn off port 1
        
        # By hub value
        serial.usb_on_by_value(hub_value=0x05)
        serial.usb_off_by_value(hub_value=0x05)
        
        # Query states
        states = serial.get_all_port_states()
        print(f'Port states: {states}')
        
        # Set port state (bind device)
        serial.set_port_state(port_index=1, hub_value=0x05)

# Find available ports
ports = SerialCommunicator.find_serial_ports('Serial')
print(f'Available ports: {ports}')
```

## Utilities

### Device

Represents a device on a relay port.

```python
from relay.utils import Device

# Create device
device = Device(serial_no='ABC123456', index=1, value=0x05)

# Access properties
print(device.serial_no)  # 'ABC123456'
print(device.index)      # 1
print(device.value)      # 5

# Modify
device.set_index(2)
device.set_value(0x06)

# String representation
print(device)            # [Port-2, SN:"ABC123456"]
print(repr(device))      # Device(index=2, serial_no="ABC123456", value=6)

# Comparison
device1 = Device('ABC123')
device2 = Device('ABC123')
print(device1 == device2)  # True
```

### Task

Represents a relay control task.

```python
from relay.utils import Device, Task
from relay.constants import RELAY_CONNECT_MSG

device = Device('ABC123', index=1, value=0x05)
task = Task(device, RELAY_CONNECT_MSG, priority=0)

# Access task properties
print(task.device)       # Device instance
print(task.message)      # 1 (RELAY_CONNECT_MSG)
print(task.priority)     # 0
print(task.index)        # 1 (from device)
print(task.value)        # 5 (from device)

# String representation
print(task)              # [P0, [Port-1, SN:"ABC123"], MSG=1]

# Tasks can be compared by priority (for priority queues)
task1 = Task(device, RELAY_CONNECT_MSG, priority=1)
task2 = Task(device, RELAY_CONNECT_MSG, priority=2)
print(task1 < task2)     # True (lower priority value = higher priority)
```

### DatabaseManager

MySQL database operations with context manager.

```python
from relay.utils import DatabaseManager

# Use as context manager (auto-closes connection)
with DatabaseManager(
    host='localhost',
    user='relay_user',
    password='password',
    database='relay_test'
) as db:
    # Check if table exists
    if not db.table_exists('devices'):
        # Create table
        db.create_table('devices', [
            'id INTEGER PRIMARY KEY AUTO_INCREMENT',
            'serial VARCHAR(256)',
            'status VARCHAR(50)'
        ])
    
    # Insert data
    db.insert_row('devices', [0, 'ABC123', 'active'])
    
    # Check if row exists
    if db.has_row('devices', 'serial="ABC123"'):
        # Update
        db.update_row('devices', 'status="inactive"', 'serial="ABC123"')
    
    # Query
    results = db.query_table(
        table_name='devices',
        columns='serial, status',
        condition='status="active"',
        order_by='serial'
    )
    
    for serial, status in results:
        print(f'{serial}: {status}')
    
    # Delete
    db.delete_rows('devices', 'status="inactive"')
    
    # Get row count
    count = db.get_row_count('devices', '1=1')
    print(f'Total rows: {count}')
```

### USBDeviceInfo

Windows USB device information via DLL.

```python
from relay.utils import USBDeviceInfo

# Initialize (loads UsbDll.dll)
usb_info = USBDeviceInfo()

serial_number = 'ABC123456'

# Check if device is valid
if usb_info.is_valid_device(serial_number):
    # Get USB hub ID (method 1)
    hub_id = usb_info.get_usb_hub_id(serial_number)
    print(f'Hub ID: {hub_id}')
    
    # Get USB hub ID (method 2 - alternative)
    hub_id_alt = usb_info.get_usb_hub_id_method2(serial_number)
    print(f'Hub ID (alt): {hub_id_alt}')
    
    # Get comprehensive info
    info = usb_info.get_device_info(serial_number)
    print(info)
    # {
    #     'serial_number': 'ABC123456',
    #     'is_valid': True,
    #     'hub_id': 5,
    #     'hub_id_alt': 5
    # }

# Custom DLL path
usb_info = USBDeviceInfo(dll_path='path/to/UsbDll.dll')
```

## Controllers

### DeviceRecoveryController

Recovers lost ADB connections.

```python
from relay.controllers.recovery import DeviceRecoveryController

# Use as context manager
with DeviceRecoveryController('ABC123456') as controller:
    # Configure
    controller.config.adb_timeout = 15
    controller.config.max_recovery_attempts = 5
    
    # Execute recovery
    success = controller.execute()
    
    if success:
        print('Device recovered successfully')
    else:
        print('Recovery failed')
```

### DeviceInitializer

Initializes and binds devices to relay ports.

```python
from relay.controllers.initializer import DeviceInitializer

# Bind device to relay port
with DeviceInitializer('ABC123456') as initializer:
    # Auto-bind to available port
    success = initializer.bind_device()
    
    # Bind to specific port
    success = initializer.bind_device(port=3)
    
    # Force binding (even if port occupied)
    success = initializer.bind_device(port=3, force=True)

# Release device from relay port
with DeviceInitializer('ABC123456') as initializer:
    success = initializer.release_device()
```

## Constants

### Message Types

```python
from relay.constants import (
    RELAY_DISCONNECT_MSG,      # 0 - Disconnect USB by port index
    RELAY_CONNECT_MSG,         # 1 - Connect USB by port index
    RELAY_DISCONNECT_MSG_SEC,  # 2 - Disconnect USB by hub value
    RELAY_CONNECT_MSG_SEC,     # 3 - Connect USB by hub value
    RELAY_GET_STATE_MSG,       # 4 - Get all port states
    RELAY_SET_STATE_MSG,       # 5 - Set port state (bind device)
)

# Use in tasks
from relay.utils import Task, Device

device = Device('ABC123')
task = Task(device, RELAY_CONNECT_MSG)
```

### Configuration Access

```python
from relay import constants

# Database settings
print(constants.HOST)
print(constants.USER)
print(constants.DB_NAME)

# Server settings
print(constants.SERVER_HOST)
print(constants.SERVER_PORT)

# Protocol constants
print(constants.FRAME_HEAD)      # 126
print(constants.FRAME_END)       # 85
print(constants.CMD_ON)          # 255
print(constants.CMD_OFF)         # 0
```

## CLI Usage

### Server

```bash
# Start server with defaults
relay-server

# Custom host and port
relay-server --host 0.0.0.0 --port 12345

# Debug logging
relay-server --log-level DEBUG
```

### Recovery

```bash
# Recover device
relay-recover --serial ABC123456

# Custom attempts and timeout
relay-recover -s ABC123456 --attempts 5 --timeout 15

# Force recovery
relay-recover -s ABC123456 --force
```

### Initialization

```bash
# Bind device to available port
relay-init bind ABC123456

# Bind to specific port
relay-init bind ABC123456 --port 3

# Release device
relay-init release ABC123456

# List bound devices
relay-init list

# Show relay status
relay-init status
```

## Error Handling

### Exceptions

```python
from relay.hardware.serial_comm import SerialCommunicator
from relay.utils import DatabaseManager

# Serial communication errors
try:
    serial = SerialCommunicator('relay')
except ValueError as e:
    print(f'No serial ports found: {e}')

try:
    serial.send_data([126, 7, 1])
except RuntimeError as e:
    print(f'Port not open: {e}')

# Database errors
try:
    with DatabaseManager('invalid_host', 'user', 'pass', 'db') as db:
        pass
except Exception as e:
    print(f'Database connection failed: {e}')

# USB DLL errors
from relay.utils import USBDeviceInfo

try:
    usb_info = USBDeviceInfo('missing.dll')
except OSError as e:
    print(f'DLL not found: {e}')
```

## Best Practices

1. **Always use context managers** for resources:
   ```python
   with SerialCommunicator('relay') as serial:
       serial.usb_on(1)
   # Automatically closed
   ```

2. **Check return values**:
   ```python
   if serial.is_open:
       serial.usb_on(1)
   ```

3. **Use logging instead of print**:
   ```python
   logger = LoggerFactory.get_logger('MyModule')
   logger.info('Operation started')
   ```

4. **Handle exceptions gracefully**:
   ```python
   try:
       controller.execute()
   except Exception as e:
       logger.error(f'Failed: {e}', exc_info=True)
   ```

5. **Type hints for clarity**:
   ```python
   def my_function(serial: str, timeout: int) -> bool:
       pass
   ```

---

For more examples, see the [examples/](../examples/) directory.

