# encoding: utf-8
"""
Created on 2016-11-3  
@author:  Kyrie Liu  
@description:  serial communication
"""
import serial
from serial.tools.list_ports import comports
import array
import time
from Config import Config


class SerialComm(Config):
    def __init__(self, flag):
        Config.__init__(self, flag)
        port = SerialComm.get_ports()
        assert len(port) > 0, 'Not found serial ports'
        self.__serial = serial.Serial(
            port[-1],
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            xonxoff=0,
            timeout=0
        )

    @staticmethod
    def get_ports(flag='Serial'):
        return [port for port, desc, _ in sorted(comports()) if flag in desc]

    def is_opened(self):
        return self.__serial.isOpen()

    def send_hex_data(self, frame_data):
        self.log.info('[UART_TXD] - {}'.format(self.string(frame_data)))
        self.__serial.write(array.array('B', frame_data))
        self.__serial.flush()

    def rec_hex_data(self):
        output = self.__serial.readall()
        result = self.string(output) if len(output) > 1 else ''
        self.log.info('[UART_RXD] - {}'.format(result))
        return result

    def usb_on(self, index):
        self.log.info('[BOX_STAT] - Power  on relay port[%s]' % index)
        return self.switcher(self.frame_usb_on_by_index(index))

    def usb_off(self, index):
        self.log.info('[BOX_STAT] - Power off relay port[%s]' % index)
        return self.switcher(self.frame_usb_off_by_index(index))

    def usb_on_sec(self, value):
        self.log.info('[BOX_STAT] - Connect USB cable [%s]' % value)
        return self.switcher(self.frame_usb_on_by_value(value))

    def usb_off_sec(self, value):
        self.log.info('[BOX_STAT] - Disconnect USB cable [%s]' % value)
        return self.switcher(self.frame_usb_off_by_value(value))

    def get_relay_port_states(self):
        self.log.info('[BOX_STAT] - Read all relay port states')
        return self.switcher(self.frame_relay_port_states()).split(' ')[4:9]

    def set_relay_port_state(self, index, value):
        self.log.info('[BOX_STAT] - Set mapper relay port[%s]-ID[%s]' % (index, value))
        return self.switcher(self.frame_set_relay_port_state(index, value))

    def switcher(self, frame_data):
        self.send_hex_data(frame_data)
        time.sleep(0.1)
        return self.rec_hex_data()

    def close(self):
        self.log.info('[SER_STAT] - SerialComm.close')
        self.__del__()

    def __del__(self):
        if self.__serial.isOpen():
            self.log.info('[SER_STAT] - SerialComm.__serial.__del__')
            self.__serial.close()
