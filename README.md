# USB Relay Controller / USB继电器控制器

[![Python Version](https://img.shields.io/badge/python-2.7%20%7C%203.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern Python application for controlling USB relay boards to automate device testing and ADB connection recovery.

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## English

### ✨ Introduction

USB Relay Controller is a **production-ready, enterprise-grade** tool designed for automated testing environments. It automatically recovers lost ADB connections by controlling USB relay hardware, eliminating manual intervention and improving test reliability.

Built with **modern Python architecture** including type hints, dataclasses, abstract base classes, and comprehensive testing support.

### 🎯 Key Features

- 🔌 **Automatic Device Recovery**: Intelligent ADB connection recovery with configurable retry logic
- 🎛️ **Multi-Port Control**: Simultaneous management of multiple relay ports
- 📊 **Statistics Tracking**: MySQL database integration for recovery metrics and analytics
- 🖥️ **Modern Architecture**: Clean separation of concerns with dependency injection
- 🔧 **Extensible Design**: Abstract base classes and mixins for easy customization
- 📝 **Comprehensive Logging**: Colored console output with rotating log files
- 🐍 **Type Safety**: Full type hints for IDE support and static analysis
- 🔒 **Context Managers**: Automatic resource cleanup and error handling
- 📦 **Packaged CLI**: Professional command-line tools with argparse

### System Requirements

- **Operating System**: Windows (for USB DLL support)
- **Python**: 2.7 or 3.6+
- **Hardware**: USB Relay Board (with serial communication support)
- **Cables**: 
  - Type-B USB cable (for PC to relay communication)
  - Micro-B USB cable (for serial communication)
  - Device-specific USB cables

### Hardware Setup

1. Connect the USB relay to your PC using Type-B USB cable
2. Connect the relay's serial port to PC using Micro-B cable
3. Connect your test devices (DUTs) to the relay's controlled USB ports
4. Ensure all drivers are installed properly

```
┌──────────┐      Type-B      ┌─────────────┐      Device     ┌──────────┐
│    PC    │ ◄──────────────► │ USB  Relay  │ ◄────Cable────► │   DUT    │
└──────────┘   Micro-B (Serial)└─────────────┘                 └──────────┘
               ◄─────────────►
```

### 📥 Installation

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/UsbRelay.git
cd UsbRelay

# Install with pip (recommended)
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt
```

#### Configuration

1. **Copy example config**:
   ```bash
   cp config.example.py config/config_local.py
   ```

2. **Edit configuration**:
   ```python
   # config/config_local.py
   DATABASE_CONFIG = {
       'host': 'localhost',
       'user': 'relay_user',
       'password': 'your_password',
       'database': 'relay_test',
   }
   ```

3. **Set environment variables** (optional):
   ```bash
   export RELAY_DB_HOST=localhost
   export RELAY_DB_USER=relay_user
   export RELAY_DB_PASSWORD=your_password
   ```

4. **Place USB DLL**:
   - Ensure `UsbDll.dll` is in the project root
   - Required for Windows USB device detection

### 🚀 Quick Start

#### 1. Start the Server

```bash
# Using CLI command
relay-server

# Or with Python module
python -m relay.cli.server

# Custom configuration
relay-server --host 0.0.0.0 --port 11222 --log-level DEBUG
```

#### 2. Bind Device

```bash
# Auto-bind to available port
relay-init bind ABC123456

# Bind to specific port
relay-init bind ABC123456 --port 3

# Force binding
relay-init bind ABC123456 --port 3 --force
```

#### 3. Recover Device

```bash
# Recover lost ADB connection
relay-recover --serial ABC123456

# With custom settings
relay-recover -s ABC123456 --attempts 5 --timeout 15

# Force recovery
relay-recover -s ABC123456 --force
```

#### 4. Manage Devices

```bash
# List all bound devices
relay-init list

# Show relay port status
relay-init status

# Release device from port
relay-init release ABC123456
```

### 📁 Project Structure

```
relay/                      # Main package
├── __init__.py            # Package exports
├── constants.py           # Global constants with type safety
│
├── core/                  # Core infrastructure
│   ├── config.py          # Configuration management (dataclasses)
│   └── base.py            # Abstract base classes and mixins
│
├── hardware/              # Hardware communication
│   ├── protocol.py        # Protocol frame builder
│   └── serial_comm.py     # Serial interface (context manager)
│
├── utils/                 # Utilities
│   ├── relay_utils.py     # Device and Task classes
│   ├── database.py        # Database manager (context manager)
│   └── usb_info.py        # USB device info via DLL
│
├── server/                # Server implementation
│   └── task_manager.py    # Task queue and request handling
│
├── controllers/           # Business logic
│   ├── recovery.py        # Device recovery controller
│   └── initializer.py     # Device initialization controller
│
└── cli/                   # Command-line interfaces
    ├── server.py          # relay-server command
    ├── recover.py         # relay-recover command
    └── initialize.py      # relay-init command

docs/                      # Documentation
├── ARCHITECTURE.md        # Architecture overview
├── API.md                 # API reference
└── USER_GUIDE.md          # User guide

config/                    # Configuration files
└── config_local.py        # Local configuration (gitignored)

tests/                     # Test suite
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── e2e/                   # End-to-end tests
```

### Configuration

Edit `RelayConst.py` to configure database and relay settings:

```python
# Database Configuration
Const.HOST = 'your_database_host'
Const.USER = 'your_database_user'
Const.PASSWD = 'your_database_password'
Const.DB_NAME = 'your_database_name'
Const.PORT = 3306
```

### Protocol

The relay communicates using a custom protocol over serial:

- **Frame Structure**: `[HEAD][LEN][INDEX][MODE][STATE][XOR][END]`
- **Commands**: USB ON/OFF, Get States, Set State
- **Response**: ACK with status

### API Reference

#### Task Messages

```python
RELAY_DISCONNT_MSG = 0      # Disconnect USB by port index
RELAY_CONNECT_MSG = 1       # Connect USB by port index
RELAY_DISCONNT_MSG_SEC = 2  # Disconnect USB by hub value
RELAY_CONNECT_MSG_SEC = 3   # Connect USB by hub value
RELAY_GET_STATE_MSG = 4     # Get all port states
RELAY_SET_STATE_MSG = 5     # Set port state (bind device)
```

### Logging

Logs are stored in the `RelayLog/` directory:

- `relay_server_YYYYMMDD.log` - Server operations log
- `relay_<serial>_YYYYMMDD.log` - Device-specific logs

### Troubleshooting

**Serial port not found**
- Check if relay is connected and drivers installed
- Verify COM port in Device Manager

**ADB device not recognized**
- Ensure ADB is in system PATH
- Check USB cable connections
- Verify device is in debugging mode

**Database connection error**
- Verify database credentials in configuration
- Ensure MySQL server is running
- Check network connectivity

### 💻 Programmatic Usage

Use the library in your Python code:

```python
from relay.controllers.recovery import DeviceRecoveryController
from relay.core.config import ConfigManager

# Configure
config = ConfigManager()
config.update_config(adb_timeout=15, max_recovery_attempts=5)

# Recover device
with DeviceRecoveryController('ABC123456') as controller:
    if controller.execute():
        print('Recovery successful!')
```

See [API Documentation](docs/API.md) for complete API reference.

### 🏗️ Architecture Highlights

#### Modern Python Features

- **Type Hints**: Full type annotations for IDE support
  ```python
  def recover_device(serial: str, timeout: int = 10) -> bool:
      pass
  ```

- **Dataclasses**: Clean configuration management
  ```python
  @dataclass
  class DatabaseConfig:
      host: str = 'localhost'
      port: int = 3306
  ```

- **Context Managers**: Automatic resource cleanup
  ```python
  with SerialCommunicator('relay') as serial:
      serial.usb_on(1)
  # Automatically cleaned up
  ```

- **Abstract Base Classes**: Clear interfaces
  ```python
  class BaseRelayController(ABC):
      @abstractmethod
      def execute(self) -> bool:
          pass
  ```

- **Mixins**: Reusable functionality
  ```python
  class Controller(BaseRelayController, ADBCommandMixin):
      # Inherits ADB functionality
      pass
  ```

#### Design Patterns

- **Singleton**: Configuration management
- **Factory**: Logger creation
- **Strategy**: Protocol frame building
- **Observer**: Event-driven task processing

See [Architecture Documentation](docs/ARCHITECTURE.md) for details.

### 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Complete usage guide with examples
- **[API Reference](docs/API.md)**: Detailed API documentation
- **[Architecture](docs/ARCHITECTURE.md)**: System design and patterns
- **[Contributing](CONTRIBUTING.md)**: How to contribute

### 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Coding standards
- Pull request process

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Author

**Kyrie Liu**

### Acknowledgments

- Thanks to all contributors
- Inspired by automated testing requirements
- Built for the QA automation community

---

<a name="chinese"></a>
## 中文

### 简介

USB继电器控制器是一个专为自动化测试设计的工具，用于处理设备自动化测试中的ADB（Android Debug Bridge）异常。当测试框架检测到ADB连接失败时，该工具会自动控制USB继电器模拟人工插拔USB线或电池，帮助恢复设备连接。

### 特性

- 🔌 **自动设备恢复**：ADB连接丢失时自动重连设备
- 🎛️ **多端口支持**：同时控制多个USB继电器端口
- 📊 **数据库记录**：在MySQL数据库中跟踪和记录恢复统计信息
- 🖥️ **客户端-服务器架构**：服务器管理继电器硬件，客户端发送控制命令
- 🔧 **硬件抽象**：易于集成各种USB继电器型号
- 📝 **完整日志**：详细的调试和监控日志

### 系统要求

- **操作系统**：Windows（用于USB DLL支持）
- **Python**：2.7 或 3.6+
- **硬件**：USB继电器板（支持串口通信）
- **线缆**：
  - Type-B USB线（PC与继电器通信）
  - Micro-B USB线（串口通信）
  - 设备专用USB线

### 硬件配置

1. 使用Type-B USB线将USB继电器连接到PC
2. 使用Micro-B线将继电器的串口连接到PC
3. 将测试设备（DUT）连接到继电器的受控USB端口
4. 确保所有驱动程序正确安装

```
┌──────────┐      Type-B      ┌─────────────┐      设备线     ┌──────────┐
│   电脑   │ ◄──────────────► │  USB继电器  │ ◄────────────► │  测试设备│
└──────────┘  Micro-B (串口)  └─────────────┘                 └──────────┘
               ◄─────────────►
```

### 安装

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/UsbRelay.git
   cd UsbRelay
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置数据库设置**
   ```bash
   cp config.example.py config_local.py
   # 编辑config_local.py，填入你的数据库凭证
   ```

4. **放置USB DLL**
   - 确保`UsbDll.dll`在项目根目录或系统PATH中
   - Windows上USB设备检测需要此DLL

### 使用方法

#### 1. 启动继电器服务器

服务器管理物理继电器硬件：

```bash
python RelayServer.py
```

服务器在`localhost:11222`监听控制命令。

#### 2. 初始化设备绑定

将设备绑定到特定继电器端口：

```bash
python InitRelay.py -p bind <设备序列号>
```

示例：
```bash
python InitRelay.py -p bind SC98321E1007B081251
```

#### 3. 恢复丢失的ADB连接

当ADB连接丢失时，触发恢复：

```bash
python Relay.py -s <设备序列号>
```

示例：
```bash
python Relay.py -s SC98321E1007B081251
```

### 项目结构

```
UsbRelay/
├── Config.py              # 配置框架和日志
├── Const.py              # 全局常量定义
├── RelayConst.py         # 继电器特定常量
├── SerialComm.py         # 与继电器硬件的串口通信
├── RelayUtils.py         # 设备和任务包装类
├── RelayServer.py        # 继电器控制主服务器
├── Relay.py              # 设备恢复客户端
├── InitRelay.py          # 设备初始化和绑定
├── DatabaseUtils.py      # MySQL数据库操作
├── UsbInfo.py            # 通过Win32 DLL获取USB设备信息
├── UsbDll.dll           # Windows USB操作DLL（未包含）
├── requirements.txt      # Python依赖
├── config.example.py     # 示例配置文件
└── README.md            # 本文件
```

### 配置

编辑`RelayConst.py`配置数据库和继电器设置：

```python
# 数据库配置
Const.HOST = '你的数据库主机'
Const.USER = '你的数据库用户'
Const.PASSWD = '你的数据库密码'
Const.DB_NAME = '你的数据库名'
Const.PORT = 3306
```

### 通信协议

继电器通过串口使用自定义协议通信：

- **帧结构**：`[HEAD][LEN][INDEX][MODE][STATE][XOR][END]`
- **命令**：USB 开/关、获取状态、设置状态
- **响应**：带状态的ACK

### API参考

#### 任务消息

```python
RELAY_DISCONNT_MSG = 0      # 通过端口索引断开USB
RELAY_CONNECT_MSG = 1       # 通过端口索引连接USB
RELAY_DISCONNT_MSG_SEC = 2  # 通过hub值断开USB
RELAY_CONNECT_MSG_SEC = 3   # 通过hub值连接USB
RELAY_GET_STATE_MSG = 4     # 获取所有端口状态
RELAY_SET_STATE_MSG = 5     # 设置端口状态（绑定设备）
```

### 日志

日志存储在`RelayLog/`目录中：

- `relay_server_YYYYMMDD.log` - 服务器操作日志
- `relay_<序列号>_YYYYMMDD.log` - 设备特定日志

### 故障排除

**未找到串口**
- 检查继电器是否连接且驱动已安装
- 在设备管理器中验证COM端口

**ADB设备无法识别**
- 确保ADB在系统PATH中
- 检查USB线缆连接
- 验证设备处于调试模式

**数据库连接错误**
- 验证配置中的数据库凭证
- 确保MySQL服务器正在运行
- 检查网络连接

### 贡献

欢迎贡献！请阅读[CONTRIBUTING.md](CONTRIBUTING.md)了解我们的行为准则和提交拉取请求的流程。

### 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](LICENSE)文件。

### 作者

**Kyrie Liu**

### 致谢

- 感谢所有贡献者
- 受自动化测试需求启发
- 为QA自动化社区而构建
