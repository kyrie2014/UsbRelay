# -*- coding: utf-8 -*-
"""
Configuration Management Module

Provides centralized configuration management and logging setup.
"""

import os
import time
import logging
import ctypes
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


# Windows Console Colors
FOREGROUND_WHITE = 0x0007
FOREGROUND_BLUE = 0x01
FOREGROUND_GREEN = 0x02
FOREGROUND_RED = 0x04
FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN

STD_OUTPUT_HANDLE = -11


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = 'localhost'
    user: str = 'relay_user'
    password: str = 'password'
    database: str = 'relay_test'
    port: int = 3306
    table_name: str = 'pm_recoveryadbdata'


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = 'localhost'
    port: int = 11222
    backlog: int = 5


@dataclass
class RelayConfig:
    """Main relay configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    log_dir: str = 'RelayLog'
    adb_timeout: int = 10
    max_recovery_attempts: int = 3
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RelayConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            RelayConfig instance
        """
        db_config = DatabaseConfig(**config_dict.get('database', {}))
        srv_config = ServerConfig(**config_dict.get('server', {}))
        
        return cls(
            database=db_config,
            server=srv_config,
            log_dir=config_dict.get('log_dir', 'RelayLog'),
            adb_timeout=config_dict.get('adb_timeout', 10),
            max_recovery_attempts=config_dict.get('max_recovery_attempts', 3)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database': {
                'host': self.database.host,
                'user': self.database.user,
                'password': self.database.password,
                'database': self.database.database,
                'port': self.database.port,
                'table_name': self.database.table_name,
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'backlog': self.server.backlog,
            },
            'log_dir': self.log_dir,
            'adb_timeout': self.adb_timeout,
            'max_recovery_attempts': self.max_recovery_attempts,
        }


class ConfigManager:
    """
    Centralized configuration manager.
    
    Loads configuration from multiple sources with priority:
    1. Environment variables
    2. config_local.py (if exists)
    3. RelayConst.py (legacy)
    4. Default values
    """
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[RelayConfig] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager."""
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> RelayConfig:
        """Load configuration from all sources."""
        config = RelayConfig()
        
        # Try loading from config_local.py
        try:
            from config import config_local
            if hasattr(config_local, 'DATABASE_CONFIG'):
                config.database = DatabaseConfig(**config_local.DATABASE_CONFIG)
            if hasattr(config_local, 'SERVER_CONFIG'):
                config.server = ServerConfig(**config_local.SERVER_CONFIG)
        except ImportError:
            pass
        
        # Try loading from RelayConst.py (legacy)
        try:
            from relay import constants as const
            config.database.host = getattr(const, 'HOST', config.database.host)
            config.database.user = getattr(const, 'USER', config.database.user)
            config.database.password = getattr(const, 'PASSWD', config.database.password)
            config.database.database = getattr(const, 'DB_NAME', config.database.database)
            config.database.port = getattr(const, 'PORT', config.database.port)
            config.database.table_name = getattr(const, 'DB_TABLE_NAME', config.database.table_name)
        except ImportError:
            pass
        
        # Override with environment variables
        config.database.host = os.getenv('RELAY_DB_HOST', config.database.host)
        config.database.user = os.getenv('RELAY_DB_USER', config.database.user)
        config.database.password = os.getenv('RELAY_DB_PASSWORD', config.database.password)
        config.database.database = os.getenv('RELAY_DB_NAME', config.database.database)
        
        if os.getenv('RELAY_DB_PORT'):
            config.database.port = int(os.getenv('RELAY_DB_PORT'))
        
        if os.getenv('RELAY_SERVER_PORT'):
            config.server.port = int(os.getenv('RELAY_SERVER_PORT'))
        
        return config
    
    @property
    def config(self) -> RelayConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)


class ColoredConsoleHandler(logging.StreamHandler):
    """
    Colored console handler for Windows.
    
    Applies colors to console output based on log level.
    """
    
    COLORS = {
        logging.DEBUG: FOREGROUND_WHITE,
        logging.INFO: FOREGROUND_GREEN,
        logging.WARNING: FOREGROUND_YELLOW,
        logging.ERROR: FOREGROUND_RED,
        logging.CRITICAL: FOREGROUND_RED,
    }
    
    def __init__(self):
        """Initialize colored console handler."""
        super().__init__()
        try:
            self.std_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        except (AttributeError, OSError):
            self.std_handle = None
    
    def emit(self, record):
        """Emit a record with color."""
        if self.std_handle:
            color = self.COLORS.get(record.levelno, FOREGROUND_WHITE)
            ctypes.windll.kernel32.SetConsoleTextAttribute(self.std_handle, color)
        
        super().emit(record)
        
        if self.std_handle:
            ctypes.windll.kernel32.SetConsoleTextAttribute(
                self.std_handle, FOREGROUND_WHITE
            )


class LoggerFactory:
    """
    Logger factory for creating configured loggers.
    
    Provides consistent logging setup across the application.
    """
    
    _configured_loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        serial_number: Optional[str] = None,
        level: int = logging.INFO,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG
    ) -> logging.Logger:
        """
        Get or create a configured logger.
        
        Args:
            name: Logger name
            serial_number: Device serial number (for file naming)
            level: Overall logger level
            console_level: Console handler level
            file_level: File handler level
        
        Returns:
            Configured logger instance
        """
        logger_key = f'{name}_{serial_number}' if serial_number else name
        
        if logger_key in cls._configured_loggers:
            return cls._configured_loggers[logger_key]
        
        logger = logging.getLogger(logger_key)
        logger.setLevel(level)
        logger.propagate = False
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = ColoredConsoleHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if serial number provided)
        if serial_number:
            log_dir = Path('RelayLog')
            log_dir.mkdir(exist_ok=True)
            
            date_str = time.strftime('%Y%m%d', time.localtime())
            log_file = log_dir / f'relay_{serial_number}_{date_str}.log'
            
            file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._configured_loggers[logger_key] = logger
        return logger
    
    @classmethod
    def get_server_logger(cls, level: int = logging.INFO) -> logging.Logger:
        """
        Get server logger with daily rotating log file.
        
        Args:
            level: Logger level
        
        Returns:
            Configured server logger
        """
        logger = logging.getLogger('relay.server')
        logger.setLevel(level)
        logger.propagate = False
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = ColoredConsoleHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path('RelayLog')
        log_dir.mkdir(exist_ok=True)
        
        date_str = time.strftime('%Y%m%d', time.localtime())
        log_file = log_dir / f'relay_server_{date_str}.log'
        
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

