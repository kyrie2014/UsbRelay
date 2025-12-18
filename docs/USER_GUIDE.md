# User Guide

Comprehensive guide for using the USB Relay Controller.

## Table of Contents

- [Getting Started](#getting-started)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Tips and Tricks](#tips-and-tricks)

## Getting Started

### Prerequisites

Before using the USB Relay Controller, ensure you have:

1. **Hardware**:
   - USB Relay board (with serial communication support)
   - Type-B USB cable (PC to relay)
   - Micro-B USB cable (serial communication)
   - Device-specific USB cables

2. **Software**:
   - Windows OS (for USB DLL support)
   - Python 3.6+ or 2.7
   - MySQL Server (for logging)
   - ADB (Android Debug Bridge)
   - UsbDll.dll (place in project root)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/UsbRelay.git
   cd UsbRelay
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database**:
   ```bash
   cp config.example.py config/config_local.py
   ```
   
   Edit `config/config_local.py`:
   ```python
   DATABASE_CONFIG = {
       'host': 'localhost',
       'user': 'relay_user',
       'password': 'your_password',
       'database': 'relay_test',
       'port': 3306,
   }
   ```

4. **Place USB DLL**:
   - Copy `UsbDll.dll` to the project root directory
   - Ensure it's accessible from your Python path

### Hardware Setup

1. Connect USB relay to PC via Type-B USB cable
2. Connect relay's serial port to PC via Micro-B cable
3. Install relay drivers if prompted by Windows
4. Verify COM port in Device Manager (should show as "USB Serial Port")
5. Connect your test devices to the relay's USB ports

Physical setup:
```
┌──────────┐      Type-B USB       ┌─────────────┐
│    PC    │ ◄──────────────────► │             │      Device
│          │                       │  USB Relay  │ ◄───Cable──► DUT
│          │   Micro-B (Serial)   │   Board     │
│          │ ◄──────────────────► │             │
└──────────┘                       └─────────────┘
                                    Port 1  Port 2  ...
```

## Basic Usage

### Step 1: Start the Server

The server must be running to handle relay commands:

```bash
# Start with default settings (localhost:11222)
relay-server

# Or use Python directly
python -m relay.cli.server
```

Output:
```
2025-12-18 10:00:00 - relay.server - INFO - ======================...
2025-12-18 10:00:00 - relay.server - INFO - USB Relay Server Starting
2025-12-18 10:00:00 - relay.server - INFO - Server listening on localhost:11222
2025-12-18 10:00:00 - relay.server - INFO - Press Ctrl+C to stop server
```

**Keep this terminal open** - the server must be running for all other operations.

### Step 2: Bind Device to Relay Port

Before recovering devices, you need to bind them to relay ports:

```bash
# Bind device ABC123456 to an available relay port
relay-init bind ABC123456

# Or use Python directly
python -m relay.cli.initialize bind ABC123456
```

What happens:
1. System queries all relay port states
2. Finds device's USB hub ID
3. Searches for free relay port
4. Tests connection by toggling power
5. Binds device to port if ADB connects successfully
6. Saves binding to `JPORTS.PKL` file

Output:
```
2025-12-18 10:01:00 - InitCLI - INFO - Inquiry all free Relay Ports
2025-12-18 10:01:05 - InitCLI - INFO - Found adb enabled on Relay Port[1]
2025-12-18 10:01:05 - InitCLI - INFO - Bind port [1] to hub ID [0x05]
```

### Step 3: Recover Device (When ADB Lost)

When ADB connection is lost, trigger recovery:

```bash
# Recover device ABC123456
relay-recover --serial ABC123456

# Or use Python directly
python -m relay.cli.recover --serial ABC123456
```

What happens:
1. Checks if device is bound to a relay port
2. Detects USB hub ID
3. Disconnects USB power via relay
4. Waits 1 second
5. Reconnects USB power
6. Waits for ADB connection (up to 10 seconds)
7. Repeats if necessary (up to 3 attempts)
8. Logs results to database

Output:
```
2025-12-18 10:05:00 - RecoveryCLI - INFO - Device Recovery for ABC123456
2025-12-18 10:05:00 - Recovery - INFO - [ADB_STATE] - Not found DUT [ABC123456]
2025-12-18 10:05:01 - Recovery - INFO - [BOX_STAT] - Disconnect USB cable [0x05]
2025-12-18 10:05:02 - Recovery - INFO - [BOX_STAT] - Connect USB cable [0x05]
2025-12-18 10:05:03 - Recovery - INFO - [ADB_STATE] - Found DUT [ABC123456]
2025-12-18 10:05:03 - Recovery - INFO - Device recovered successfully
```

## Advanced Features

### Custom Server Configuration

#### Environment Variables

```bash
# Set environment variables
export RELAY_DB_HOST=192.168.1.100
export RELAY_DB_USER=custom_user
export RELAY_DB_PASSWORD=secure_pass
export RELAY_SERVER_PORT=12345

# Start server (will use env vars)
relay-server
```

#### Configuration File

Create `config/config_local.py`:

```python
# Database configuration
DATABASE_CONFIG = {
    'host': 'db.example.com',
    'user': 'relay_user',
    'password': 'secure_password',
    'database': 'relay_production',
    'port': 3306,
}

# Server configuration
SERVER_CONFIG = {
    'host': '0.0.0.0',  # Listen on all interfaces
    'port': 11222,
    'backlog': 10,
}

# Other settings
RELAY_CONFIG = {
    'log_dir': 'RelayLog',
    'adb_timeout': 15,
    'max_recovery_attempts': 5,
}
```

### Multiple Devices

Bind multiple devices to different ports:

```bash
# Bind device 1 to port 1
relay-init bind DEVICE001 --port 1

# Bind device 2 to port 2
relay-init bind DEVICE002 --port 2

# Bind device 3 to port 3
relay-init bind DEVICE003 --port 3

# View all bindings
relay-init list
```

### Programmatic Usage

Use the library in your own Python code:

```python
from relay.controllers.recovery import DeviceRecoveryController
from relay.core.config import ConfigManager

# Configure
config = ConfigManager()
config.update_config(adb_timeout=20, max_recovery_attempts=5)

# Recover device
with DeviceRecoveryController('ABC123456') as controller:
    if controller.execute():
        print('Recovery successful!')
    else:
        print('Recovery failed')
```

### Integration with Test Framework

Integrate with your test automation:

```python
import unittest
from relay.controllers.recovery import DeviceRecoveryController

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = 'ABC123456'
        self.controller = DeviceRecoveryController(self.serial)
        self.controller.initialize()
    
    def tearDown(self):
        self.controller.cleanup()
    
    def test_with_auto_recovery(self):
        # Run test
        try:
            result = self.run_adb_command('pm list packages')
            self.assertIsNotNone(result)
        except Exception:
            # ADB lost, try recovery
            self.controller.execute()
            # Retry test
            result = self.run_adb_command('pm list packages')
            self.assertIsNotNone(result)
```

## Troubleshooting

### Server Won't Start

**Problem**: `No serial ports found for relay communication`

**Solution**:
1. Check if relay is connected via USB
2. Verify drivers are installed (Device Manager → Ports)
3. Look for "USB Serial Port (COMx)"
4. If no COM port, reinstall drivers

**Problem**: `Address already in use`

**Solution**:
1. Check if server is already running: `tasklist | findstr python`
2. Kill existing process or use different port: `relay-server --port 12345`

### Device Binding Fails

**Problem**: `Device not found on any relay port`

**Solution**:
1. Ensure device is connected to one of the relay's USB ports
2. Check ADB connection manually: `adb devices`
3. Enable USB debugging on device
4. Try binding to specific port: `relay-init bind ABC123 --port 2`

**Problem**: `All ports are occupied`

**Solution**:
1. List current bindings: `relay-init list`
2. Release unused devices: `relay-init release OLD_DEVICE`
3. Force bind to specific port: `relay-init bind ABC123 --port 1 --force`

### Recovery Doesn't Work

**Problem**: `Device not recovered after 3 attempts`

**Solution**:
1. Check if device is properly bound: `relay-init status`
2. Verify USB cable is good
3. Try manual disconnect/reconnect
4. Increase attempts: `relay-recover -s ABC123 --attempts 10`
5. Check logs in `RelayLog/` directory

**Problem**: `Serial port timeout`

**Solution**:
1. Check relay's serial cable connection
2. Restart the server
3. Verify COM port in Device Manager
4. Try different USB port for serial connection

### Database Errors

**Problem**: `Can't connect to MySQL server`

**Solution**:
1. Verify MySQL is running: `net start MySQL` (Windows)
2. Check credentials in `config/config_local.py`
3. Test connection: `mysql -h localhost -u relay_user -p`
4. Ensure database exists: `CREATE DATABASE relay_test;`

**Problem**: `Table doesn't exist`

**Solution**:
- The table is created automatically on first use
- Or create manually:
  ```sql
  CREATE TABLE pm_recoveryadbdata (
      ID INTEGER PRIMARY KEY AUTO_INCREMENT,
      Date DATE,
      PC VARCHAR(256),
      Chipset VARCHAR(256),
      Serial VARCHAR(256),
      IMEI VARCHAR(256),
      AdbLost INTEGER,
      AdbRecovery INTEGER,
      Build TEXT,
      TotalRun INTEGER,
      TotalLost INTEGER,
      Comment TEXT,
      RebootTimes INTEGER
  );
  ```

## Tips and Tricks

### 1. View Real-time Logs

```bash
# Tail server log
tail -f RelayLog/relay_server_20251218.log

# Tail device log
tail -f RelayLog/relay_ABC123456_20251218.log

# On Windows PowerShell
Get-Content RelayLog\relay_server_20251218.log -Wait
```

### 2. Quick Device Check

```python
# Check if device is bound
python -c "import pickle; print(pickle.load(open('JPORTS.PKL', 'rb')))"

# Output: {'ABC123': (5, 1), 'DEF456': (6, 2)}
# Format: {serial: (hub_id, relay_port)}
```

### 3. Batch Recovery

Recover multiple devices:

```bash
# Create script: batch_recover.sh
for serial in ABC123 DEF456 GHI789; do
    echo "Recovering $serial..."
    relay-recover --serial $serial
done
```

### 4. Scheduled Recovery

Windows Task Scheduler:

```batch
REM create_task.bat
schtasks /create /tn "RelayRecovery" /tr "relay-recover -s ABC123" /sc hourly
```

### 5. Monitor with Dashboard

Create a simple monitoring script:

```python
from relay.utils import DatabaseManager
from relay.core.config import ConfigManager

config = ConfigManager().config
with DatabaseManager(**config.database.to_dict()) as db:
    results = db.query_table(
        'pm_recoveryadbdata',
        'Serial, AdbLost, AdbRecovery',
        order_by='AdbLost DESC'
    )
    
    print('Device Recovery Statistics')
    print('-' * 50)
    for serial, lost, recovered in results:
        rate = (recovered / lost * 100) if lost > 0 else 0
        print(f'{serial}: {recovered}/{lost} ({rate:.1f}%)')
```

### 6. Testing Relay Ports

Test individual ports:

```python
from relay.hardware.serial_comm import SerialCommunicator
import time

with SerialCommunicator('test') as serial:
    for port in range(1, 5):  # Test ports 1-4
        print(f'Testing port {port}...')
        serial.usb_off(port)
        time.sleep(1)
        serial.usb_on(port)
        time.sleep(2)
```

### 7. Export Statistics

```bash
# Export to CSV
mysql -h localhost -u relay_user -p relay_test \
    -e "SELECT * FROM pm_recoveryadbdata" \
    | sed 's/\t/,/g' > recovery_stats.csv
```

---

For more information:
- [API Documentation](API.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing](../CONTRIBUTING.md)

