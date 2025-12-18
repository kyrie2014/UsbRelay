# encoding: utf-8
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  config command structure
"""
import time
import os
import logging
import ctypes
import threading

FOREGROUND_WHITE = 0x0007
FOREGROUND_BLUE = 0x01  # text color contains blue.
FOREGROUND_GREEN = 0x02  # text color contains green.
FOREGROUND_RED = 0x04  # text color contains red.
FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN

STD_OUTPUT_HANDLE = -11
std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


class Config(object):
    def __init__(self, sn):
        self.__init_log(sn)
        self.__init_params()

    def __init_params(self):
        """refer to usb relay communication protocol"""
        self.__head, self.__len, self.__end, self.__resp, self.__suc  = (126, 7, 85, 255, 0)
        self.__control, self.__all, self.__usb, self.__off, self.__on = (33, 64, 16, 0, 255)

    def frame_struct(self, index, mode, state):
        lst = list([self.__head, self.__len, index, mode, state])
        lst.append(self.xor(lst))
        lst.append(self.__end)
        return lst

    def frame_usb_on_by_value(self, value):
        lst = list([self.__head, 8, self.__control, value, self.__usb, self.__on])
        lst.append(self.xor(lst))
        lst.append(self.__end)
        return lst

    def frame_usb_off_by_value(self, value):
        lst = list([self.__head, 8, self.__control, value, self.__usb, self.__off])
        lst.append(self.xor(lst))
        lst.append(self.__end)
        return lst

    def frame_usb_on_by_index(self, index):
        return self.frame_struct(index, self.__all, self.__on)

    def frame_usb_off_by_index(self, index):
        return self.frame_struct(index, self.__all, self.__off)

    def frame_success(self, param):
        lst = list([self.__head, self.__resp, self.__len, param, self.__suc])
        lst.append(self.xor(lst))
        lst.append(self.__end)
        return Config.string(lst)

    def frame_relay_port_states(self):
        return [self.__head, self.__len, 6, 0, 0, 127, self.__end]

    def frame_set_relay_port_state(self, index, value):
        lst = list([self.__head, self.__len, 32, index, value])
        lst.append(self.xor(lst))
        lst.append(self.__end)
        return lst

    @staticmethod
    def string(lst):
        return ' '.join(['%02x' % ord(d) if str == type(d) else '%02x' % d for d in lst])

    @classmethod
    def xor(cls, lst):
        try:
            # Python 2
            return reduce(lambda x, y=0: y ^ x, lst)
        except NameError:
            # Python 3
            from functools import reduce
            return reduce(lambda x, y=0: y ^ x, lst)

    def __init_log(self, sn):
        logfile = 'relay_%s_%s.log' % (sn, time.strftime("%Y%m%d", time.localtime()))
        path = os.path.join(os.getcwd(), 'RelayLog')
        if not os.path.exists(path):
            os.mkdir(path)
        self.log = Logger(path=os.path.join(path, logfile), name='Relay')


class Singleton(type):
    mutex = threading.Lock()

    def __init__(cls, name, bases, dicts):
        super(Singleton, cls).__init__(name, bases, dicts)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            Singleton.mutex.acquire()
            if cls.instance is None:
                cls.instance = super(Singleton, cls).__call__(*args, **kw)
            Singleton.mutex.release()
        return cls.instance


class Logger(object):
    # singleton pattern for solving repetitive log   
    __metaclass__ = Singleton

    def __init__(self, path="", name="Log", clevel=logging.DEBUG, flevel=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        logging.Formatter.converter = time.localtime
        fmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # set cmd log
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(clevel)
        # set file log
        fh = logging.FileHandler(path)
        fh.setFormatter(fmt)
        fh.setLevel(flevel)
        self.logger.addHandler(sh)
        self.logger.addHandler(fh)

    def debug(self, message, color=FOREGROUND_WHITE):
        Logger.set_color(color)
        self.logger.debug(message)
        Logger.set_color(FOREGROUND_WHITE)

    def info(self, message, color=FOREGROUND_GREEN):
        Logger.set_color(color)
        self.logger.info(message)
        Logger.set_color(FOREGROUND_WHITE)

    def warn(self, message, color=FOREGROUND_YELLOW):
        Logger.set_color(color)
        self.logger.warn(message)
        Logger.set_color(FOREGROUND_WHITE)

    def error(self, message, color=FOREGROUND_RED):
        Logger.set_color(color)
        self.logger.error(message)
        Logger.set_color(FOREGROUND_WHITE)

    def critical(self, message, color=FOREGROUND_RED):
        Logger.set_color(color)
        self.logger.critical(message)
        Logger.set_color(FOREGROUND_WHITE)

    @staticmethod
    def set_color(color, handle=std_out_handle):
        return ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)

