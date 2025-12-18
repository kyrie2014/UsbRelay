# -*- coding: utf-8 -*-
"""
Device Recovery Controller

Handles automatic recovery of lost ADB connections using USB relay.
"""

import os
import time
import socket
import pickle
from typing import Optional, List
from pathlib import Path

from relay.core.base import BaseRelayController, ADBCommandMixin
from relay.utils.relay_utils import Device, Task
from relay.utils.database import DatabaseManager
from relay.utils.usb_info import USBDeviceInfo
from relay.constants import (
    RELAY_DISCONNECT_MSG,
    RELAY_CONNECT_MSG,
    RELAY_DISCONNECT_MSG_SEC,
    RELAY_CONNECT_MSG_SEC,
    RELAY_GET_STATE_MSG,
)


class DeviceRecoveryController(BaseRelayController, ADBCommandMixin):
    """
    Controller for recovering lost ADB connections.
    
    Automatically detects ADB connection loss and attempts recovery
    by controlling USB relay to disconnect/reconnect the device.
    """
    
    def __init__(self, serial_number: str):
        """
        Initialize recovery controller.
        
        Args:
            serial_number: Device serial number
        """
        super().__init__(serial_number)
        
        self.pkl_file = Path('JPORTS.PKL')
        self.usb_info: Optional[USBDeviceInfo] = None
        self.db: Optional[DatabaseManager] = None
        
        # Device state
        self.hub_value: Optional[int] = None
        self.hub_value_str: str = ''
        self.relay_port_states: List[str] = []
        
        # Database fields
        self.current_date = time.strftime('%Y%m%d', time.localtime())
        self.hostname = socket.gethostname()
        self.build_info = 'N/A'
    
    def initialize(self) -> bool:
        """
        Initialize controller resources.
        
        Returns:
            True if initialization successful
        """
        self.log_section('Initializing Recovery Controller')
        
        try:
            # Initialize USB info
            self.usb_info = USBDeviceInfo()
            self.logger.info('USB device info initialized')
            
            # Initialize database
            db_config = self.config.database
            self.db = DatabaseManager(
                host=db_config.host,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
                port=db_config.port
            )
            self.logger.info('Database connection established')
            
            # Get relay port states
            self.relay_port_states = self._get_relay_port_states()
            
            # Get USB hub value
            self._update_hub_value()
            
            # Get build info
            self.build_info = self._get_build_info()
            
            return True
            
        except Exception as e:
            self.logger.error(f'Initialization failed: {e}', exc_info=True)
            return False
    
    def execute(self) -> bool:
        """
        Execute device recovery procedure.
        
        Returns:
            True if recovery successful
        """
        self.log_section('Device Recovery')
        
        # Update database: total lost count
        self._update_database('TotalLost=TotalLost+1')
        
        # Check if device is already connected
        if self.is_adb_connected():
            self.logger.info('Device is already connected via ADB')
            return True
        
        # Try recovery from invalid device state
        if not self.hub_value and not self._recover_invalid_device():
            self.logger.error('Device not found and recovery failed')
            return False
        
        # Update database: ADB lost count
        self._update_database('AdbLost=AdbLost+1')
        
        # Attempt recovery
        max_attempts = self.config.max_recovery_attempts
        success = self._recover_adb_connection(max_attempts)
        
        if success:
            self.logger.info('Device recovered successfully')
            self._update_database('AdbRecovery=AdbRecovery+1')
            return True
        else:
            self.logger.error('Device recovery failed')
            return False
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.db:
            self.db.close()
            self.db = None
        
        self.logger.info('Recovery controller cleaned up')
    
    def _update_hub_value(self) -> None:
        """Update USB hub value from device."""
        if not self.usb_info:
            return
        
        self.hub_value = self.usb_info.get_usb_hub_id(self.serial_number)
        if not self.hub_value:
            self.hub_value = self.usb_info.get_usb_hub_id_method2(self.serial_number)
        
        self.hub_value_str = f'{self.hub_value:02x}' if self.hub_value else ''
        self.logger.debug(f'Hub value: {self.hub_value} (0x{self.hub_value_str})')
    
    def _get_build_info(self) -> str:
        """Get build information from Jenkins config file."""
        config_file = Path(f'{self.serial_number}_Jenkins.txt')
        
        if not config_file.exists():
            return 'N/A'
        
        try:
            try:
                import configparser
            except ImportError:
                import ConfigParser as configparser
            
            config = configparser.ConfigParser()
            config.read(str(config_file))
            
            path = config.get('Setting', 'Path', fallback='')
            pac = config.get('Setting', 'Pac', fallback='')
            
            return f'{path}+{pac}' if path and pac else 'N/A'
            
        except Exception as e:
            self.logger.warning(f'Failed to read build info: {e}')
            return 'N/A'
    
    def _get_relay_port_states(self) -> List[str]:
        """Get current relay port states from server."""
        try:
            task = Task(Device(self.serial_number), RELAY_GET_STATE_MSG)
            response = self._send_relay_request(task)
            
            if isinstance(response, str):
                # Parse response string
                return response.strip('[]').replace("'", '').split(', ')
            elif isinstance(response, list):
                return response
            else:
                return []
                
        except Exception as e:
            self.logger.error(f'Failed to get relay states: {e}')
            return []
    
    def _recover_invalid_device(self) -> bool:
        """
        Attempt to recover device from invalid state.
        
        Returns:
            True if recovery successful
        """
        self.log_section('Invalid Device Recovery')
        
        # Check if device is valid
        if self.usb_info and self.usb_info.is_valid_device(self.serial_number):
            return True
        
        if self.wait_for_adb(timeout=1):
            return True
        
        # Load device bindings
        if not self.pkl_file.exists():
            self.logger.warning('Device binding file not found')
            return False
        
        try:
            with open(self.pkl_file, 'rb') as f:
                devices = pickle.load(f)
        except Exception as e:
            self.logger.error(f'Failed to load device bindings: {e}')
            return False
        
        if self.serial_number not in devices:
            self.logger.warning('Device not found in bindings')
            return False
        
        pc_hub_id, relay_port = devices[self.serial_number]
        
        if pc_hub_id == 0:
            self.logger.warning('Device hub ID is invalid')
            return False
        
        # Attempt recovery by toggling relay port
        device = Device(self.serial_number, index=relay_port)
        
        for attempt in range(2):
            self.logger.info(f'Recovery attempt {attempt + 1}/2')
            
            # Disconnect
            task_disconnect = Task(device, RELAY_DISCONNECT_MSG)
            self._send_relay_request(task_disconnect)
            time.sleep(1)
            
            # Reconnect
            task_connect = Task(device, RELAY_CONNECT_MSG)
            self._send_relay_request(task_connect)
            
            # Wait for ADB
            if self.wait_for_adb(timeout=self.config.adb_timeout):
                self.logger.info('Device recovered from invalid state')
                self._update_database('AdbLost=AdbLost+1, AdbRecovery=AdbRecovery+1')
                return True
        
        return False
    
    def _recover_adb_connection(self, max_attempts: int) -> bool:
        """
        Recover ADB connection by toggling USB relay.
        
        Args:
            max_attempts: Maximum recovery attempts
        
        Returns:
            True if recovery successful
        """
        # Update hub value if needed
        if not self.hub_value:
            self._update_hub_value()
        
        if not self.hub_value:
            self.logger.error('Cannot determine USB hub value')
            return False
        
        device = Device(self.serial_number, value=self.hub_value)
        
        for attempt in range(max_attempts):
            self.logger.info(f'Recovery attempt {attempt + 1}/{max_attempts}')
            
            # Check current ADB state
            adb_state = self.get_adb_state()
            
            if adb_state == 'device':
                self.logger.info('Device is already connected')
                return True
            
            elif adb_state == 'offline':
                self.logger.warning('Device is offline, restarting ADB server')
                self.restart_adb_server()
            
            # Disconnect USB
            task_disconnect = Task(device, RELAY_DISCONNECT_MSG_SEC)
            self._send_relay_request(task_disconnect)
            time.sleep(1)
            
            # Reconnect USB
            task_connect = Task(device, RELAY_CONNECT_MSG_SEC)
            self._send_relay_request(task_connect)
            
            # Wait for ADB connection
            if self.wait_for_adb(timeout=self.config.adb_timeout):
                self.logger.info('ADB connection restored')
                return True
        
        return False
    
    def _send_relay_request(self, task: Task) -> Any:
        """
        Send relay control request to server.
        
        Args:
            task: Task to send
        
        Returns:
            Response from server
        """
        from relay.client import RelayClient
        
        client = RelayClient(
            host=self.config.server.host,
            port=self.config.server.port
        )
        
        return client.send_request(task)
    
    def _update_database(self, update_clause: str) -> None:
        """
        Update database with recovery statistics.
        
        Args:
            update_clause: SQL UPDATE clause (e.g., 'AdbLost=AdbLost+1')
        """
        if not self.db:
            return
        
        try:
            # Ensure row exists
            condition = (
                f'Date="{self.current_date}" AND '
                f'Serial="{self.serial_number}" AND '
                f'PC="{self.hostname}" AND '
                f'Build="{self.build_info}"'
            )
            
            if not self.db.has_row(self.config.database.table_name, condition):
                # Insert new row
                self.db.insert_row(
                    self.config.database.table_name,
                    [
                        0,  # ID (auto-increment)
                        self.current_date,
                        self.hostname,
                        'N/A',  # Chipset
                        self.serial_number,
                        'N/A',  # IMEI
                        0,  # AdbLost
                        0,  # AdbRecovery
                        self.build_info,
                        0,  # TotalRun
                        0,  # TotalLost
                        'None',  # Comment
                        0,  # RebootTimes
                    ]
                )
            
            # Update row
            self.db.update_row(
                self.config.database.table_name,
                update_clause,
                condition
            )
            
        except Exception as e:
            self.logger.error(f'Database update failed: {e}', exc_info=True)

