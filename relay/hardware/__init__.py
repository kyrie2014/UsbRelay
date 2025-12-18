# -*- coding: utf-8 -*-
"""
Hardware Communication Modules

This package contains hardware-specific communication modules:
- Serial communication with relay boards
- Protocol frame building
- Hardware configuration
"""

from relay.hardware.serial_comm import SerialCommunicator
from relay.hardware.protocol import ProtocolFrameBuilder

__all__ = [
    'SerialCommunicator',
    'ProtocolFrameBuilder',
]

