# -*- coding: utf-8 -*-
"""
Serial Communication Module

Provides high-level serial communication interface for USB relay hardware.
"""

import array
import time
import logging
from typing import List, Optional
from contextlib import contextmanager

import serial
from serial.tools.list_ports import comports

from relay.hardware.protocol import ProtocolFrameBuilder


class SerialCommunicator:
    """
    High-level serial communication interface for USB relay hardware.
    
    This class handles all serial communication with the relay board,
    including port detection, data transmission, and command execution.
    """
    
    def __init__(
        self,
        name: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = 'N',
        stopbits: int = 1,
        timeout: float = 0,
        auto_connect: bool = True
    ):
        """
        Initialize serial communicator.
        
        Args:
            name: Logger name identifier
            baudrate: Serial baud rate (default: 9600)
            bytesize: Number of data bits (default: 8)
            parity: Parity checking ('N', 'E', 'O')
            stopbits: Number of stop bits (default: 1)
            timeout: Read timeout in seconds (default: 0)
            auto_connect: Auto-connect to first available port
        
        Raises:
            ValueError: If no serial ports found
        """
        self.logger = logging.getLogger(f'relay.serial.{name}')
        self.protocol = ProtocolFrameBuilder()
        self._serial: Optional[serial.Serial] = None
        
        if auto_connect:
            ports = self.find_serial_ports()
            if not ports:
                raise ValueError('No serial ports found for relay communication')
            
            port = ports[-1]  # Use last detected port
            self.logger.info(f'Connecting to serial port: {port}')
            
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                xonxoff=False,
                timeout=timeout
            )
            self.logger.info(f'Serial port opened: {port}')
    
    @staticmethod
    def find_serial_ports(identifier: str = 'Serial') -> List[str]:
        """
        Find available serial ports by identifier.
        
        Args:
            identifier: Port description identifier (default: 'Serial')
        
        Returns:
            List of matching port names
        """
        return [
            port for port, desc, _ in sorted(comports())
            if identifier in desc
        ]
    
    @property
    def is_open(self) -> bool:
        """Check if serial port is open."""
        return self._serial is not None and self._serial.isOpen()
    
    def send_data(self, frame_data: List[int]) -> None:
        """
        Send frame data to relay.
        
        Args:
            frame_data: List of byte values to send
        
        Raises:
            RuntimeError: If port is not open
        """
        if not self.is_open:
            raise RuntimeError('Serial port is not open')
        
        hex_string = self.protocol.bytes_to_hex_string(frame_data)
        self.logger.debug(f'[TX] {hex_string}')
        
        self._serial.write(array.array('B', frame_data))
        self._serial.flush()
    
    def receive_data(self) -> str:
        """
        Receive data from relay.
        
        Returns:
            Hex string representation of received data
        
        Raises:
            RuntimeError: If port is not open
        """
        if not self.is_open:
            raise RuntimeError('Serial port is not open')
        
        output = self._serial.readall()
        result = self.protocol.bytes_to_hex_string(output) if len(output) > 1 else ''
        
        if result:
            self.logger.debug(f'[RX] {result}')
        
        return result
    
    def execute_command(self, frame_data: List[int]) -> str:
        """
        Execute command by sending frame and receiving response.
        
        Args:
            frame_data: Command frame to send
        
        Returns:
            Response hex string
        """
        self.send_data(frame_data)
        time.sleep(0.1)  # Wait for relay to process
        return self.receive_data()
    
    def usb_on(self, port_index: int) -> str:
        """
        Turn USB power ON for specific port.
        
        Args:
            port_index: Relay port index (1-based)
        
        Returns:
            Response from relay
        """
        self.logger.info(f'Power ON relay port [{port_index}]')
        frame = self.protocol.build_usb_on_by_index(port_index)
        return self.execute_command(frame)
    
    def usb_off(self, port_index: int) -> str:
        """
        Turn USB power OFF for specific port.
        
        Args:
            port_index: Relay port index (1-based)
        
        Returns:
            Response from relay
        """
        self.logger.info(f'Power OFF relay port [{port_index}]')
        frame = self.protocol.build_usb_off_by_index(port_index)
        return self.execute_command(frame)
    
    def usb_on_by_value(self, hub_value: int) -> str:
        """
        Connect USB cable by hub value.
        
        Args:
            hub_value: USB hub ID value
        
        Returns:
            Response from relay
        """
        self.logger.info(f'Connect USB cable [0x{hub_value:02x}]')
        frame = self.protocol.build_usb_on_by_value(hub_value)
        return self.execute_command(frame)
    
    def usb_off_by_value(self, hub_value: int) -> str:
        """
        Disconnect USB cable by hub value.
        
        Args:
            hub_value: USB hub ID value
        
        Returns:
            Response from relay
        """
        self.logger.info(f'Disconnect USB cable [0x{hub_value:02x}]')
        frame = self.protocol.build_usb_off_by_value(hub_value)
        return self.execute_command(frame)
    
    def get_all_port_states(self) -> List[str]:
        """
        Query states of all relay ports.
        
        Returns:
            List of hex strings representing each port's state
        """
        self.logger.info('Reading all relay port states')
        frame = self.protocol.build_get_port_states()
        response = self.execute_command(frame)
        
        # Extract port states from response (bytes 4-8)
        return response.split(' ')[4:9] if response else []
    
    def set_port_state(self, port_index: int, hub_value: int) -> str:
        """
        Set port state (bind device to port).
        
        Args:
            port_index: Relay port index (1-based)
            hub_value: USB hub ID value to bind
        
        Returns:
            Response from relay
        """
        self.logger.info(f'Bind port [{port_index}] to hub ID [0x{hub_value:02x}]')
        frame = self.protocol.build_set_port_state(port_index, hub_value)
        return self.execute_command(frame)
    
    def close(self) -> None:
        """Close serial connection."""
        if self._serial and self._serial.isOpen():
            self.logger.info(f'Closing serial port: {self._serial.port}')
            self._serial.close()
            self._serial = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
    
    def __repr__(self):
        """String representation."""
        port = self._serial.port if self._serial else 'disconnected'
        status = 'open' if self.is_open else 'closed'
        return f'SerialCommunicator(port={port}, status={status})'

