# -*- coding: utf-8 -*-
"""
Global Constants and Configuration

This module defines all constants used throughout the USB Relay Controller.
"""

import sys


class _ConstantsMeta(type):
    """Metaclass to prevent modification of constants after creation."""
    
    class ConstError(TypeError):
        """Exception raised when attempting to modify a constant."""
        pass
    
    def __setattr__(cls, key, value):
        if key in cls.__dict__:
            raise cls.ConstError("Cannot change the value of constant: {}".format(key))
        else:
            super(_ConstantsMeta, cls).__setattr__(key, value)
    
    def __getattr__(cls, key):
        return cls.__dict__.get(key)


# Python 2/3 compatible metaclass syntax
try:
    # Python 3
    class Constants(metaclass=_ConstantsMeta):
        """Container for all system constants."""
        pass
except TypeError:
    # Python 2
    class Constants(object):
        """Container for all system constants."""
        __metaclass__ = _ConstantsMeta


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database Connection Settings
# Override these in config_local.py
Constants.HOST = 'localhost'
Constants.USER = 'relay_user'
Constants.PASSWD = 'password'
Constants.DB_NAME = 'relay_test'
Constants.PORT = 3306

# Database Table Configuration
Constants.DB_TABLE_NAME = 'pm_recoveryadbdata'
Constants.DB_TABLE_KEYS = [
    'ID INTEGER PRIMARY KEY AUTO_INCREMENT',
    'Date DATE',
    'PC VARCHAR(256)',
    'Chipset VARCHAR(256)',
    'Serial VARCHAR(256)',
    'IMEI VARCHAR(256)',
    'AdbLost INTEGER',
    'AdbRecovery INTEGER',
    'Build TEXT',
    'TotalRun INTEGER',
    'TotalLost INTEGER',
    'Comment TEXT',
    'RebootTimes INTEGER'
]

# =============================================================================
# ANDROID DEVICE CONFIGURATION
# =============================================================================

# ADB Shell Commands
Constants.GETPROP_PRODUCT = 'getprop ro.build.product'

# =============================================================================
# RELAY CONTROL MESSAGES
# =============================================================================

# Relay Control Message Types
RELAY_DISCONNECT_MSG = 0      # Disconnect USB by port index
RELAY_CONNECT_MSG = 1         # Connect USB by port index
RELAY_DISCONNECT_MSG_SEC = 2  # Disconnect USB by hub value
RELAY_CONNECT_MSG_SEC = 3     # Connect USB by hub value
RELAY_GET_STATE_MSG = 4       # Get all port states
RELAY_SET_STATE_MSG = 5       # Set port state (bind device)

Constants.RELAY_DISCONNECT_MSG = RELAY_DISCONNECT_MSG
Constants.RELAY_CONNECT_MSG = RELAY_CONNECT_MSG
Constants.RELAY_DISCONNECT_MSG_SEC = RELAY_DISCONNECT_MSG_SEC
Constants.RELAY_CONNECT_MSG_SEC = RELAY_CONNECT_MSG_SEC
Constants.RELAY_GET_STATE_MSG = RELAY_GET_STATE_MSG
Constants.RELAY_SET_STATE_MSG = RELAY_SET_STATE_MSG

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

# Server Network Settings
Constants.SERVER_HOST = 'localhost'
Constants.SERVER_PORT = 11222
Constants.SERVER_BACKLOG = 5

# =============================================================================
# HARDWARE CONFIGURATION
# =============================================================================

# Serial Communication Settings
Constants.SERIAL_BAUDRATE = 9600
Constants.SERIAL_BYTESIZE = 8
Constants.SERIAL_PARITY = 'N'
Constants.SERIAL_STOPBITS = 1
Constants.SERIAL_TIMEOUT = 0

# Relay Protocol Constants
Constants.FRAME_HEAD = 126
Constants.FRAME_LENGTH = 7
Constants.FRAME_END = 85
Constants.FRAME_RESPONSE = 255
Constants.FRAME_SUCCESS = 0

Constants.CMD_CONTROL = 33
Constants.CMD_ALL = 64
Constants.CMD_USB = 16
Constants.CMD_OFF = 0
Constants.CMD_ON = 255

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

Constants.LOG_DIR = 'RelayLog'
Constants.LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =============================================================================
# EXPORT
# =============================================================================

# Make constants available at module level
sys.modules[__name__] = Constants

