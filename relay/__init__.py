# -*- coding: utf-8 -*-
"""
USB Relay Controller Package

A Python package for controlling USB relay boards to automate device testing
and ADB connection recovery.
"""

__version__ = '1.0.0'
__author__ = 'Kyrie Liu'
__license__ = 'MIT'

from relay.constants import (
    RELAY_DISCONNECT_MSG,
    RELAY_CONNECT_MSG,
    RELAY_DISCONNECT_MSG_SEC,
    RELAY_CONNECT_MSG_SEC,
    RELAY_GET_STATE_MSG,
    RELAY_SET_STATE_MSG,
)

__all__ = [
    'RELAY_DISCONNECT_MSG',
    'RELAY_CONNECT_MSG',
    'RELAY_DISCONNECT_MSG_SEC',
    'RELAY_CONNECT_MSG_SEC',
    'RELAY_GET_STATE_MSG',
    'RELAY_SET_STATE_MSG',
    '__version__',
]

