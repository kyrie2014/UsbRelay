# -*- coding: utf-8 -*-
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  call win32 dll
"""
import ctypes
import re
from ctypes.wintypes import BYTE
from ctypes.wintypes import INT

"""
    define c++ data type
"""
INT = ctypes.c_int
PWCTSTR = ctypes.c_wchar_p
PTSTR = ctypes.c_void_p


class USBInfo(object):

    def __init__(self):
        self.usb = ctypes.cdll.LoadLibrary(r"UsbDll.dll")

    @staticmethod
    def byte_buffer(length):
        """Get a buffer for a string"""
        return (BYTE * length)()

    @staticmethod
    def string(buffer):
        s = []
        for c in buffer:
            if c == 0:
                break
            """ "& 0xff": hack to convert signed to unsigned """
            s.append(chr(c & 0xff))
        return ''.join(s)

    def is_valid_device(self, sn):
        GetComPorts = self.usb.COM_GetComPorts
        GetComPorts.argtypes = [PWCTSTR, PTSTR, INT]
        ports_buffer = USBInfo.byte_buffer(250)
        GetComPorts(PWCTSTR(sn), ctypes.byref(ports_buffer), ctypes.sizeof(ports_buffer) - 1)
        regex_obj = re.compile(r'(COM\d+)')
        return True if regex_obj.findall(USBInfo.string(ports_buffer)) else False

    def get_parent_id(self, port):
        GetParentID = self.usb.COM_GetParentID
        GetParentID.argtypes = [PWCTSTR, PTSTR, INT]
        parent = USBInfo.byte_buffer(250)
        GetParentID(PWCTSTR(port), ctypes.byref(parent), ctypes.sizeof(parent) - 1)
        return USBInfo.string(parent)

    def get_usb_hub_id2(self, sn):
        GetLocationPaths = self.usb.COM_GetLocationPaths
        GetLocationPaths.argtypes = [PWCTSTR, PTSTR, INT]
        location = USBInfo.byte_buffer(250)
        GetLocationPaths(PWCTSTR(sn), ctypes.byref(location), ctypes.sizeof(location) - 1)
        regex_obj = re.compile(r'USB\((\d+)\)')
        index = regex_obj.findall(USBInfo.string(location))
        return int(index[-1]) if index else None

    def get_usb_hub_id(self, sn):
        GetLocationInfo = self.usb.COM_GetLocationInfo
        GetLocationInfo.argtypes = [PWCTSTR, PTSTR, INT]
        location = USBInfo.byte_buffer(250)
        GetLocationInfo(PWCTSTR(sn), ctypes.byref(location), ctypes.sizeof(location) - 1)
        # regex_obj = re.compile(r'\.(0[0-9][1-9])\.')
        local = USBInfo.string(location).split('.')[3:-1]
        index = [i for i in local if i != '000']
        # index = regex_obj.findall(USBInfo.string(location))
        return int(index[-1]) if index else None
