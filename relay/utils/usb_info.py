# -*- coding: utf-8 -*-
"""
USB Device Information Module

Provides Windows USB device information through Win32 DLL calls.
"""

import ctypes
import re
from ctypes.wintypes import BYTE, INT


# Define C++ data types
INT = ctypes.c_int
PWCTSTR = ctypes.c_wchar_p
PTSTR = ctypes.c_void_p


class USBDeviceInfo:
    """
    USB device information extractor using Windows DLL.
    
    This class interfaces with UsbDll.dll to retrieve USB device
    information such as COM ports, parent IDs, and hub locations.
    """
    
    def __init__(self, dll_path='UsbDll.dll'):
        """
        Initialize USB DLL interface.
        
        Args:
            dll_path (str): Path to USB DLL file (default: 'UsbDll.dll')
        
        Raises:
            OSError: If DLL cannot be loaded
        """
        try:
            self.usb_dll = ctypes.cdll.LoadLibrary(dll_path)
        except OSError as e:
            raise OSError(
                f"Failed to load USB DLL '{dll_path}'. "
                f"Please ensure the DLL is in the project root or system PATH. "
                f"Error: {e}"
            )
    
    @staticmethod
    def create_byte_buffer(length):
        """
        Create a byte buffer of specified length.
        
        Args:
            length (int): Buffer size
        
        Returns:
            ctypes array: Byte buffer
        """
        return (BYTE * length)()
    
    @staticmethod
    def buffer_to_string(buffer):
        """
        Convert byte buffer to string.
        
        Args:
            buffer: Byte buffer
        
        Returns:
            str: Decoded string
        """
        chars = []
        for byte in buffer:
            if byte == 0:
                break
            # Convert signed to unsigned with & 0xff
            chars.append(chr(byte & 0xff))
        return ''.join(chars)
    
    def is_valid_device(self, serial_number):
        """
        Check if device with given serial number is valid (has COM ports).
        
        Args:
            serial_number (str): Device serial number
        
        Returns:
            bool: True if device has valid COM ports
        """
        get_com_ports = self.usb_dll.COM_GetComPorts
        get_com_ports.argtypes = [PWCTSTR, PTSTR, INT]
        
        ports_buffer = self.create_byte_buffer(250)
        get_com_ports(
            PWCTSTR(serial_number),
            ctypes.byref(ports_buffer),
            ctypes.sizeof(ports_buffer) - 1
        )
        
        ports_str = self.buffer_to_string(ports_buffer)
        regex_pattern = re.compile(r'(COM\d+)')
        
        return bool(regex_pattern.findall(ports_str))
    
    def get_parent_id(self, com_port):
        """
        Get parent device ID for a COM port.
        
        Args:
            com_port (str): COM port name (e.g., 'COM3')
        
        Returns:
            str: Parent device ID
        """
        get_parent_id_func = self.usb_dll.COM_GetParentID
        get_parent_id_func.argtypes = [PWCTSTR, PTSTR, INT]
        
        parent_buffer = self.create_byte_buffer(250)
        get_parent_id_func(
            PWCTSTR(com_port),
            ctypes.byref(parent_buffer),
            ctypes.sizeof(parent_buffer) - 1
        )
        
        return self.buffer_to_string(parent_buffer)
    
    def get_usb_hub_id_method2(self, serial_number):
        """
        Get USB hub ID using location path method.
        
        Args:
            serial_number (str): Device serial number
        
        Returns:
            int or None: USB hub port number
        """
        get_location_paths = self.usb_dll.COM_GetLocationPaths
        get_location_paths.argtypes = [PWCTSTR, PTSTR, INT]
        
        location_buffer = self.create_byte_buffer(250)
        get_location_paths(
            PWCTSTR(serial_number),
            ctypes.byref(location_buffer),
            ctypes.sizeof(location_buffer) - 1
        )
        
        location_str = self.buffer_to_string(location_buffer)
        regex_pattern = re.compile(r'USB\((\d+)\)')
        matches = regex_pattern.findall(location_str)
        
        return int(matches[-1]) if matches else None
    
    def get_usb_hub_id(self, serial_number):
        """
        Get USB hub ID using location info method.
        
        Args:
            serial_number (str): Device serial number
        
        Returns:
            int or None: USB hub port number
        """
        get_location_info = self.usb_dll.COM_GetLocationInfo
        get_location_info.argtypes = [PWCTSTR, PTSTR, INT]
        
        location_buffer = self.create_byte_buffer(250)
        get_location_info(
            PWCTSTR(serial_number),
            ctypes.byref(location_buffer),
            ctypes.sizeof(location_buffer) - 1
        )
        
        location_str = self.buffer_to_string(location_buffer)
        parts = location_str.split('.')
        
        # Get non-zero port numbers from middle sections
        if len(parts) > 4:
            port_numbers = [int(p) for p in parts[3:-1] if p != '000']
            return port_numbers[-1] if port_numbers else None
        
        return None
    
    def get_device_info(self, serial_number):
        """
        Get comprehensive device information.
        
        Args:
            serial_number (str): Device serial number
        
        Returns:
            dict: Device information dictionary
        """
        return {
            'serial_number': serial_number,
            'is_valid': self.is_valid_device(serial_number),
            'hub_id': self.get_usb_hub_id(serial_number),
            'hub_id_alt': self.get_usb_hub_id_method2(serial_number),
        }
    
    def __repr__(self):
        """String representation."""
        return f'USBDeviceInfo(dll={self.usb_dll._name})'

