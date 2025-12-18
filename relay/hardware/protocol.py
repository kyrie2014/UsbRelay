# -*- coding: utf-8 -*-
"""
Relay Protocol Frame Builder

Defines the communication protocol for USB relay boards.
"""

try:
    # Python 3
    from functools import reduce
except ImportError:
    # Python 2 (reduce is built-in)
    pass


class ProtocolFrameBuilder:
    """
    USB Relay communication protocol frame builder.
    
    This class implements the frame structure for communicating with
    USB relay hardware over serial connection.
    
    Frame Format: [HEAD][LEN][INDEX][MODE][STATE][XOR][END]
    """
    
    # Protocol Constants
    FRAME_HEAD = 126
    FRAME_LENGTH = 7
    FRAME_END = 85
    FRAME_RESPONSE = 255
    FRAME_SUCCESS = 0
    
    CMD_CONTROL = 33
    CMD_ALL = 64
    CMD_USB = 16
    CMD_OFF = 0
    CMD_ON = 255
    
    def __init__(self):
        """Initialize protocol frame builder."""
        pass
    
    @staticmethod
    def calculate_xor(data_list):
        """
        Calculate XOR checksum for data list.
        
        Args:
            data_list (list): List of byte values
        
        Returns:
            int: XOR checksum
        """
        return reduce(lambda x, y: x ^ y, data_list, 0)
    
    @staticmethod
    def bytes_to_hex_string(data_list):
        """
        Convert byte list to hex string representation.
        
        Args:
            data_list (list): List of byte values or characters
        
        Returns:
            str: Space-separated hex string
        """
        hex_values = []
        for data in data_list:
            if isinstance(data, str):
                hex_values.append('%02x' % ord(data))
            else:
                hex_values.append('%02x' % data)
        return ' '.join(hex_values)
    
    def build_basic_frame(self, index, mode, state):
        """
        Build basic control frame.
        
        Args:
            index (int): Port index
            mode (int): Control mode
            state (int): Desired state
        
        Returns:
            list: Frame byte list
        """
        frame = [self.FRAME_HEAD, self.FRAME_LENGTH, index, mode, state]
        frame.append(self.calculate_xor(frame))
        frame.append(self.FRAME_END)
        return frame
    
    def build_usb_on_by_value(self, hub_value):
        """
        Build frame to turn USB on by hub value.
        
        Args:
            hub_value (int): USB hub value
        
        Returns:
            list: Frame byte list
        """
        frame = [
            self.FRAME_HEAD, 8, self.CMD_CONTROL,
            hub_value, self.CMD_USB, self.CMD_ON
        ]
        frame.append(self.calculate_xor(frame))
        frame.append(self.FRAME_END)
        return frame
    
    def build_usb_off_by_value(self, hub_value):
        """
        Build frame to turn USB off by hub value.
        
        Args:
            hub_value (int): USB hub value
        
        Returns:
            list: Frame byte list
        """
        frame = [
            self.FRAME_HEAD, 8, self.CMD_CONTROL,
            hub_value, self.CMD_USB, self.CMD_OFF
        ]
        frame.append(self.calculate_xor(frame))
        frame.append(self.FRAME_END)
        return frame
    
    def build_usb_on_by_index(self, port_index):
        """
        Build frame to turn USB on by port index.
        
        Args:
            port_index (int): Relay port index
        
        Returns:
            list: Frame byte list
        """
        return self.build_basic_frame(port_index, self.CMD_ALL, self.CMD_ON)
    
    def build_usb_off_by_index(self, port_index):
        """
        Build frame to turn USB off by port index.
        
        Args:
            port_index (int): Relay port index
        
        Returns:
            list: Frame byte list
        """
        return self.build_basic_frame(port_index, self.CMD_ALL, self.CMD_OFF)
    
    def build_success_response(self, param):
        """
        Build success response frame.
        
        Args:
            param (int): Response parameter
        
        Returns:
            str: Hex string response
        """
        frame = [
            self.FRAME_HEAD, self.FRAME_RESPONSE,
            self.FRAME_LENGTH, param, self.FRAME_SUCCESS
        ]
        frame.append(self.calculate_xor(frame))
        frame.append(self.FRAME_END)
        return self.bytes_to_hex_string(frame)
    
    def build_get_port_states(self):
        """
        Build frame to query all port states.
        
        Returns:
            list: Frame byte list
        """
        return [self.FRAME_HEAD, self.FRAME_LENGTH, 6, 0, 0, 127, self.FRAME_END]
    
    def build_set_port_state(self, port_index, value):
        """
        Build frame to set port state (bind device).
        
        Args:
            port_index (int): Relay port index
            value (int): Hub ID value to bind
        
        Returns:
            list: Frame byte list
        """
        frame = [self.FRAME_HEAD, self.FRAME_LENGTH, 32, port_index, value]
        frame.append(self.calculate_xor(frame))
        frame.append(self.FRAME_END)
        return frame

