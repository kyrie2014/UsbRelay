#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  Device and Task Wrapper Classes
"""

class Device(object):
    def __init__(self, serial_no='', index=6, value=0):
        self.serial_no = serial_no
        self.index = index
        self.value = value

    def set_id(self, index):
        self.index = index

    def set_value(self, value):
        self.value = value

    @property
    def serial_no(self):
        return self.__serial_no

    @serial_no.setter
    def serial_no(self, var):
        if not isinstance(var, str):
            raise TypeError('Must be a type of string')
        self.__serial_no = var

    @serial_no.deleter
    def serial_no(self):
        del self.__serial_no

    def __eq__(self, device):
        return self.serial_no == device.serial_no

    def __repr__(self):
        return '[Index-%d, sn:"%s"]' % (self.index, self.serial_no)


class Task(object):
    def __init__(self, device, msg, priority=0):
        self.priority = priority
        self.device = device
        self.index = device.index
        self.value = device.value
        self.msg = msg

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    def __repr__(self):
        return '[P%d, %s, %s]' % (self.priority, self.device, self.msg)
