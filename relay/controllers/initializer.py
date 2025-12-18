# -*- coding: utf-8 -*-
"""
Device Initializer Controller

Handles device binding and initialization with relay ports.
"""

import os
import time
import socket
import pickle
from typing import Optional, List, Tuple
from pathlib import Path

try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from relay.core.base import BaseRelayController, ADBCommandMixin
from relay.utils.relay_utils import Device, Task
from relay.utils.database import DatabaseManager
from relay.utils.usb_info import USBDeviceInfo
from relay.constants import (
    RELAY_DISCONNECT_MSG,
    RELAY_CONNECT_MSG,
    RELAY_SET_STATE_MSG,
    RELAY_GET_STATE_MSG,
)


class DeviceInitializer(BaseRelayController, ADBCommandMixin):
    """
    Controller for initializing and binding devices to relay ports.
    
    Automatically detects devices on relay ports and binds them for
    future recovery operations.
    """
    
    def __init__(self, serial_number: str):
        """
        Initialize device initializer.
        
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
        self.chipset: str = 'N/A'
        
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
        self.log_section('Initializing Device Controller')
        
        try:
            # Initialize USB info
            self.usb_info = USBDeviceInfo()
            
            # Initialize database
            db_config = self.config.database
            self.db = DatabaseManager(
                host=db_config.host,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
                port=db_config.port
            )
            
            # Get relay port states
            self.relay_port_states = self._get_relay_port_states()
            
            # Get USB hub value
            self._update_hub_value()
            
            # Get chipset info
            self.chipset = self.execute_shell_command('getprop ro.build.product').strip()
            
            # Get build info
            self.build_info = self._get_build_info()
            
            # Try recovery if hub value not found
            if not self.hub_value_str:
                self._recover_invalid_device()
                self._update_hub_value()
            
            return True
            
        except Exception as e:
            self.logger.error(f'Initialization failed: {e}', exc_info=True)
            return False
    
    def execute(self) -> bool:
        """
        Execute initialization (alias for bind_device).
        
        Returns:
            True if successful
        """
        return self.bind_device()
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.db:
            self.db.close()
            self.db = None
    
    def bind_device(self, port: Optional[int] = None, force: bool = False) -> bool:
        """
        Bind device to a relay port.
        
        Args:
            port: Specific port to bind (None for auto-detect)
            force: Force binding even if port is occupied
        
        Returns:
            True if binding successful
        """
        self.log_section('Binding Device to Relay Port')
        
        # Update database
        self._ensure_database_row()
        
        # Check if already bound
        if self.hub_value_str in self.relay_port_states and self._is_bonded_to_port():
            self.logger.info('Device is already bound to a relay port')
            return True
        
        # Try to bind to specific port
        if port:
            return self._bind_to_port(port, force)
        
        # Auto-detect: try unbound ports first
        if self._bind_to_unbound_port():
            return True
        
        # Wait for download process if needed
        self._wait_for_download_process()
        
        # Try bound ports
        if self._bind_to_bound_port():
            return True
        
        self.logger.error('Failed to bind device to any relay port')
        return False
    
    def release_device(self) -> bool:
        """
        Release device from relay port.
        
        Returns:
            True if release successful
        """
        self.log_section('Releasing Device from Relay Port')
        
        # Load bindings
        if not self.pkl_file.exists():
            self.logger.warning('No device bindings found')
            return False
        
        try:
            with open(self.pkl_file, 'rb') as f:
                devices = pickle.load(f)
        except Exception as e:
            self.logger.error(f'Failed to load bindings: {e}')
            return False
        
        if self.serial_number not in devices:
            self.logger.warning('Device not found in bindings')
            return False
        
        _, relay_port = devices[self.serial_number]
        
        # Release port
        device = Device(self.serial_number, index=relay_port, value=0)
        task = Task(device, RELAY_SET_STATE_MSG)
        
        response = self._send_relay_request(task)
        
        if response == 'OK':
            # Update bindings
            devices[self.serial_number] = (0, relay_port)
            with open(self.pkl_file, 'wb') as f:
                pickle.dump(devices, f)
            
            self.logger.info(f'Released relay port [{relay_port}]')
            return True
        else:
            self.logger.error('Failed to release relay port')
            return False
    
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
        """Attempt to recover device from invalid state."""
        if self.usb_info and self.usb_info.is_valid_device(self.serial_number):
            return True
        
        if self.wait_for_adb(timeout=1):
            return True
        
        return False
    
    def _is_bonded_to_port(self) -> bool:
        """Check if device is bonded to a relay port."""
        ports = [
            i + 1 for i, v in enumerate(self.relay_port_states)
            if v == self.hub_value_str
        ]
        
        for port in ports:
            if self._test_port_connection(port, times=3):
                self._save_binding(self.hub_value, port)
                return True
        
        return False
    
    def _bind_to_port(self, port: int, force: bool = False) -> bool:
        """
        Bind device to specific port.
        
        Args:
            port: Relay port index (1-based)
            force: Force binding even if port is occupied
        
        Returns:
            True if successful
        """
        if not force and port <= len(self.relay_port_states):
            state = self.relay_port_states[port - 1]
            if state != '00':
                self.logger.warning(f'Port {port} is already occupied')
                return False
        
        if self._test_port_connection(port, times=1):
            self._save_binding(self.hub_value, port)
            return True
        
        return False
    
    def _bind_to_unbound_port(self) -> bool:
        """Try to bind device to an unbound relay port."""
        self.logger.info('Searching for unbound relay ports')
        
        unbound_ports = [
            i + 1 for i, v in enumerate(self.relay_port_states)
            if v == '00'
        ]
        
        self.logger.info(f'Found unbound ports: {unbound_ports}')
        
        for port in unbound_ports:
            if self._test_port_connection(port, times=1):
                self.logger.info(f'Found device on relay port [{port}]')
                self._save_binding(self.hub_value, port)
                return True
            time.sleep(0.5)
        
        return False
    
    def _bind_to_bound_port(self) -> bool:
        """Try to bind device to an already bound relay port."""
        self.logger.info('Searching bonded relay ports')
        
        bound_ports = [
            (v, i + 1) for i, v in enumerate(self.relay_port_states)
            if v != '00'
        ]
        
        for hub_value_str, port in bound_ports:
            if self._test_port_connection(port, times=1):
                self.logger.info(f'Found device on relay port [{port}]')
                self._save_binding(self.hub_value, port)
                return True
            time.sleep(0.5)
        
        return False
    
    def _test_port_connection(self, port: int, times: int = 1) -> bool:
        """
        Test if device is connected on specific relay port.
        
        Args:
            port: Relay port index (1-based)
            times: Number of test attempts
        
        Returns:
            True if device found on port
        """
        device = Device(self.serial_number, index=port)
        
        for attempt in range(times):
            # Disconnect
            task_disconnect = Task(device, RELAY_DISCONNECT_MSG)
            self._send_relay_request(task_disconnect)
            time.sleep(2)
            
            # Check if device disappears
            if self.serial_number not in self._get_adb_devices():
                # Reconnect
                task_connect = Task(device, RELAY_CONNECT_MSG)
                self._send_relay_request(task_connect)
                
                # Wait for ADB
                if self.wait_for_adb(timeout=90):
                    return True
            else:
                self.logger.debug(f'Device not found on relay port [{port}]')
                task_connect = Task(device, RELAY_CONNECT_MSG)
                self._send_relay_request(task_connect)
        
        return False
    
    def _get_adb_devices(self) -> List[str]:
        """Get list of connected ADB devices."""
        import re
        import subprocess
        
        try:
            result = subprocess.run(
                'adb devices',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            pattern = re.compile(r'\n(\S+)\s+device')
            return pattern.findall(result.stdout)
            
        except Exception as e:
            self.logger.error(f'Failed to get ADB devices: {e}')
            return []
    
    def _save_binding(self, hub_value: int, relay_port: int) -> None:
        """
        Save device binding to file.
        
        Args:
            hub_value: USB hub ID value
            relay_port: Relay port index
        """
        devices = {}
        
        if self.pkl_file.exists():
            try:
                with open(self.pkl_file, 'rb') as f:
                    devices = pickle.load(f)
            except Exception as e:
                self.logger.warning(f'Failed to load bindings: {e}')
        
        devices[self.serial_number] = (hub_value, relay_port)
        
        try:
            with open(self.pkl_file, 'wb') as f:
                pickle.dump(devices, f)
            
            self.logger.info(f'Saved binding: {self.serial_number} -> Port {relay_port}')
            
        except Exception as e:
            self.logger.error(f'Failed to save binding: {e}')
    
    def _wait_for_download_process(self) -> None:
        """Wait for download process to finish."""
        process_name = 'ResearchDownload.exe'
        
        while self._check_process_exists(process_name):
            self.logger.info('Waiting for download process to finish...')
            time.sleep(15)
    
    def _check_process_exists(self, process_name: str) -> bool:
        """
        Check if process is running (Windows only).
        
        Args:
            process_name: Process name to check
        
        Returns:
            True if process exists
        """
        if not HAS_WIN32:
            return False
        
        try:
            wmi = win32com.client.GetObject('winmgmts:')
            ret = wmi.ExecQuery(f'select * from Win32_Process where Name="{process_name}"')
            return len(ret) > 0
        except Exception as e:
            self.logger.error(f'Failed to check process: {e}')
            return False
    
    def _send_relay_request(self, task: Task) -> Optional[str]:
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
    
    def _ensure_database_row(self) -> None:
        """Ensure database row exists for device."""
        if not self.db:
            return
        
        try:
            condition = (
                f'Date="{self.current_date}" AND '
                f'Serial="{self.serial_number}" AND '
                f'PC="{self.hostname}" AND '
                f'Build="{self.build_info}"'
            )
            
            if not self.db.has_row(self.config.database.table_name, condition):
                self.db.insert_row(
                    self.config.database.table_name,
                    [
                        0,  # ID
                        self.current_date,
                        self.hostname,
                        self.chipset,
                        self.serial_number,
                        'N/A',  # IMEI
                        0,  # AdbLost
                        0,  # AdbRecovery
                        self.build_info,
                        1,  # TotalRun
                        0,  # TotalLost
                        'None',  # Comment
                        0,  # RebootTimes
                    ]
                )
            else:
                self.db.update_row(
                    self.config.database.table_name,
                    'TotalRun=TotalRun+1',
                    condition
                )
                
        except Exception as e:
            self.logger.error(f'Database operation failed: {e}', exc_info=True)

