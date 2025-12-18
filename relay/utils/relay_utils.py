# -*- coding: utf-8 -*-
"""
Device and Task Wrapper Classes

This module provides data structures for managing relay devices and tasks.
"""


class Device:
    """
    Represents a device connected to a relay port.
    
    Attributes:
        serial_no (str): Device serial number
        index (int): Relay port index (1-based)
        value (int): USB hub ID value
    """
    
    def __init__(self, serial_no='', index=6, value=0):
        """
        Initialize a Device instance.
        
        Args:
            serial_no (str): Device serial number
            index (int): Relay port index
            value (int): USB hub ID value
        """
        self.serial_no = serial_no
        self.index = index
        self.value = value
    
    def set_index(self, index):
        """Set the relay port index."""
        self.index = index
    
    def set_value(self, value):
        """Set the USB hub ID value."""
        self.value = value
    
    @property
    def serial_no(self):
        """Get device serial number."""
        return self._serial_no
    
    @serial_no.setter
    def serial_no(self, value):
        """Set device serial number."""
        if not isinstance(value, str):
            raise TypeError('Serial number must be a string')
        self._serial_no = value
    
    @serial_no.deleter
    def serial_no(self):
        """Delete device serial number."""
        del self._serial_no
    
    def __eq__(self, other):
        """Check equality based on serial number."""
        if not isinstance(other, Device):
            return False
        return self.serial_no == other.serial_no
    
    def __repr__(self):
        """String representation of device."""
        return f'Device(index={self.index}, serial_no="{self.serial_no}", value={self.value})'
    
    def __str__(self):
        """Human-readable string representation."""
        return f'[Port-{self.index}, SN:"{self.serial_no}"]'


class Task:
    """
    Represents a relay control task.
    
    Attributes:
        device (Device): Target device
        message (int): Command message type
        priority (int): Task priority (lower is higher priority)
        index (int): Relay port index from device
        value (int): USB hub ID value from device
    """
    
    def __init__(self, device, message, priority=0):
        """
        Initialize a Task instance.
        
        Args:
            device (Device): Target device
            message (int): Command message type
            priority (int): Task priority (default: 0)
        """
        self.priority = priority
        self.device = device
        self.index = device.index
        self.value = device.value
        self.msg = message  # Keep 'msg' for backward compatibility
        self.message = message
    
    def __lt__(self, other):
        """Compare tasks by priority (for priority queue)."""
        return self.priority < other.priority
    
    def __eq__(self, other):
        """Check task equality."""
        if not isinstance(other, Task):
            return False
        return (self.device == other.device and 
                self.message == other.message and 
                self.priority == other.priority)
    
    def __repr__(self):
        """String representation of task."""
        return f'Task(priority={self.priority}, device={self.device}, message={self.message})'
    
    def __str__(self):
        """Human-readable string representation."""
        return f'[P{self.priority}, {self.device}, MSG={self.message}]'

