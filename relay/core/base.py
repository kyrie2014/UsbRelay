# -*- coding: utf-8 -*-
"""
Base Classes and Abstract Interfaces

Provides base classes and abstract interfaces for relay control.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path

from relay.core.config import ConfigManager, LoggerFactory


class BaseRelayController(ABC):
    """
    Abstract base class for relay controllers.
    
    Provides common functionality and interface for all relay controllers.
    """
    
    def __init__(self, serial_number: str):
        """
        Initialize base relay controller.
        
        Args:
            serial_number: Device serial number
        """
        self.serial_number = serial_number
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = LoggerFactory.get_logger(
            name=self.__class__.__name__,
            serial_number=serial_number
        )
        
        self._state: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the controller.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute main controller logic.
        
        Returns:
            True if execution successful
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get controller state value.
        
        Args:
            key: State key
            default: Default value if key not found
        
        Returns:
            State value
        """
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set controller state value.
        
        Args:
            key: State key
            value: State value
        """
        self._state[key] = value
    
    def log_section(self, title: str, width: int = 40) -> None:
        """
        Log a formatted section header.
        
        Args:
            title: Section title
            width: Total width of header
        """
        self.logger.info('-' * width)
        self.logger.info('|' + title.center(width - 2) + '|')
        self.logger.info('-' * width)
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
    
    def __repr__(self):
        """String representation."""
        return f'{self.__class__.__name__}(serial_number="{self.serial_number}")'


class ADBCommandMixin:
    """
    Mixin class providing ADB command execution functionality.
    
    This mixin can be added to any controller that needs ADB operations.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize mixin."""
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__)
    
    def execute_adb_command(self, command: str) -> str:
        """
        Execute ADB command for device.
        
        Args:
            command: ADB command (without 'adb -s <serial>')
        
        Returns:
            Command output
        """
        import subprocess
        
        if not hasattr(self, 'serial_number'):
            raise AttributeError('Mixin requires serial_number attribute')
        
        full_command = f'adb -s {self.serial_number} {command}'
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f'ADB command timed out: {full_command}')
            return ''
        except Exception as e:
            self.logger.error(f'ADB command failed: {e}')
            return ''
    
    def execute_shell_command(self, command: str) -> str:
        """
        Execute shell command on device via ADB.
        
        Args:
            command: Shell command
        
        Returns:
            Command output
        """
        return self.execute_adb_command(f'shell {command}')
    
    def get_adb_state(self) -> str:
        """
        Get ADB connection state.
        
        Returns:
            ADB state ('device', 'offline', 'unknown', etc.)
        """
        return self.execute_adb_command('get-state')
    
    def is_adb_connected(self) -> bool:
        """
        Check if device is connected via ADB.
        
        Returns:
            True if device state is 'device'
        """
        return self.get_adb_state() == 'device'
    
    def wait_for_adb(self, timeout: int = 10) -> bool:
        """
        Wait for ADB connection to be established.
        
        Args:
            timeout: Maximum wait time in seconds
        
        Returns:
            True if connected within timeout
        """
        import time
        
        for attempt in range(timeout):
            if self.is_adb_connected():
                self.logger.info(f'ADB connected to device: {self.serial_number}')
                return True
            
            self.logger.debug(
                f'Waiting for ADB connection... '
                f'({attempt + 1}/{timeout})'
            )
            time.sleep(1)
        
        self.logger.warning(f'ADB connection timeout for device: {self.serial_number}')
        return False
    
    def restart_adb_server(self) -> bool:
        """
        Restart ADB server.
        
        Returns:
            True if successful
        """
        import subprocess
        
        try:
            self.logger.info('Restarting ADB server...')
            subprocess.run('adb kill-server', shell=True, check=True)
            subprocess.run('adb start-server', shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Failed to restart ADB server: {e}')
            return False

