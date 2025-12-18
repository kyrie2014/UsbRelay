# encoding: utf-8
"""
Created on 2016-11-3  
@author:  Kyrie Liu  
@description:  usb relay
"""
from RelayConst import Const
import time
import os
import sys
import re
from Config import Config
from RelayUtils import *
import pickle
import socket


class Relay(Config):
    def __init__(self, sn):
        Config.__init__(self, sn)
        self.sn, self.pkl_file = sn, 'JPORTS.PKL'
        from UsbInfo import USBInfo
        self.dll = USBInfo()
        from DatabaseUtils import DatabaseUtils
        self.db = DatabaseUtils(
            Const.HOST,
            Const.USER,
            Const.PASSWD,
            Const.DB_NAME,
            Const.PORT
        )
        self.table = Const.DB_TABLE_NAME
        self.cur_date = time.strftime("%Y%m%d", time.localtime())
        self.hostname = socket.gethostname()
        self.build_node = self.get_running_build()
        self.condition = 'Date="{}" and Serial="{}" and PC="{}" and Build="{}"'.format(
            self.cur_date,
            self.sn,
            self.hostname,
            self.build_node
        )
        dev = Device(self.sn, index=6, value=0)
        self.state = self.relay_request(Task(dev, Const.RELAY_GET_STATE_MSG))
        value = self.dll.get_usb_hub_id(self.sn)
        self.value = value if value else self.dll.get_usb_hub_id2(self.sn)
        self.str_value = '%02x' % self.value if self.value else ''

    def recovery_invalid_device(self):
        self.log.info('[DBUG_INFO] - ' + '-' * 40)
        self.log.info('[DBUG_INFO] - |' + 'Invalid Device Recovery'.center(38) + '|')
        self.log.info('[DBUG_INFO] - ' + '-' * 40)

        if self.dll.is_valid_device(self.sn) or self.is_enable_adb(1):
            return True

        self.log.info('[BOX_STATE] - Current devices connection is invalid [%s]' % self.sn)
        if not os.path.exists(self.pkl_file):
            return False
        try:
            with open(self.pkl_file, 'rb') as op:
                devices = pickle.load(op)
        except IOError:
            self.log.error('[IOError] - Not opened "%s"' % self.pkl_file)
            devices = None
        # un-bond device    
        if not devices or self.sn not in devices:
            return False

        pc_hub_id, relay_port = devices[self.sn]
        # un-bond device
        if pc_hub_id == 0:
            return False

        dev = Device(self.sn, index=relay_port)
        for _ in range(2):
            self.relay_request(Task(dev, Const.RELAY_DISCONNT_MSG))
            time.sleep(1)
            self.relay_request(Task(dev, Const.RELAY_CONNECT_MSG))
            if not self.is_enable_adb(10):
                continue
            self.log.info('[BOX_STATE] - Device is recovered [%s]' % self.sn)
            self.db.update_value_of_row(self.table,
                                        'AdbLost=AdbLost+1, AdbRecovery=AdbRecovery+1',
                                        self.condition)
            return True
        return False

    def get_running_build(self):
        file_name = '{}_Jenkins.txt'.format(self.sn)
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser
        if not os.path.exists(file_name):
            return 'N/A'
        config = configparser.ConfigParser()
        config.read(file_name)
        return config.get('Setting', 'Path') + r'+' + config.get('Setting', 'Pac')

    @staticmethod
    def exec_command(cmd):
        from subprocess import Popen
        from subprocess import PIPE
        result = ''
        process = Popen(cmd, shell=True, stdout=PIPE)
        while True:
            data = process.stdout.readline()
            if len(data) == 0:
                break
            result += (data.strip() + '\n')
        return result

    def exec_shell_command(self, cmd):
        return self.exec_command('adb -s {} shell {}'.format(self.sn, cmd))

    def exec_adb_command(self, cmd):
        return self.exec_command('adb -s {} {}'.format(self.sn, cmd))

    def relay_request(self, task):
        self.log.info('[BOX_STATE] - RELAY_EVENT_TPYE --> %s' % task.msg)
        sock, result = None, None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 11222))
            data = pickle.dumps(task)
            sock.send(data)
            result = pickle.loads(sock.recv(1024))
        except socket.error as msg:
            self.log.error(msg)
        finally:
            if sock is not None:
                sock.close()
        return result

    def get_adb_state(self):
        return self.exec_adb_command('get-state').strip()

    def get_devices(self):
        return re.findall('\\w?\\n(\\S*)\\s+device', self.exec_command('adb devices'))

    def is_enable_adb(self, wait_time):
        for _ in range(wait_time):
            self.log.info('[ADB_STATE] - Not found DUT [%s]' % self.sn)
            try:
                if self.sn in self.get_devices():
                    self.log.info('[ADB_STATE] - Found DUT [%s]' % self.sn)
                    flag = True
                    break
                time.sleep(1)
            except Exception as err:
                self.log.error(err)
        else:
            flag = False
        return flag

    def recv_adb_connection(self, times):

        if not self.value:
            self.value = self.dll.get_usb_hub_id(self.sn)
            self.value = self.value if self.value else self.dll.get_usb_hub_id2(self.sn)

        if not self.value:
            self.logg.info('[BOX_STATE] - Device maybe unplugged out [%s]' % self.sn)
            sys.exit(0)
        dev = Device(self.sn, value=self.value)
        for _ in range(times):
            state = self.get_adb_state()
            if 'device' == state:
                return True
            elif 'offline' == state:
                self.log.info('[SERIAL] - {} offline'.format(self.sn))
                self.exec_adb_command('kill-server')
                self.exec_adb_command('start-server')
            self.relay_request(Task(dev, Const.RELAY_DISCONNT_MSG_SEC))
            time.sleep(1)
            self.relay_request(Task(dev, Const.RELAY_CONNECT_MSG_SEC))
            if self.is_enable_adb(10):
                return True
        return False

    def get_relay_port_id(self):
        for i, v in enumerate(self.state):
            if v in self.str_value:
                return i + 1
        return None

    def report(self, msg):
        self.log.info('Total test is {}'.format(msg))


def init_option():
    from optparse import OptionParser
    parser = OptionParser(
        usage="%program -s [sn]",
        description="bind or release usb port for relay."
    )
    parser.add_option("-s", "--serial", dest="sn",
                      help="disconnect or connect usb cable", metavar="SN")
    (options, args) = parser.parse_args()
    return options.sn if options.sn else sys.exit()


if __name__ == '__main__':
    __sn = init_option()
    relay = Relay(__sn)
    relay.log.info('[DBUG_INFO] - ' + '-' * 40)
    relay.log.info('[DBUG_INFO] - |' + 'Recovery Device'.center(38) + '|')
    relay.log.info('[DBUG_INFO] - ' + '-' * 40)

    # total lost times
    relay.db.update_value_of_row(relay.table, 'TotalLost=TotalLost+1', relay.condition)

    # update relay database
    if not relay.value and not relay.recovery_invalid_device():
        sys.exit(0)

    relay.db.update_value_of_row(relay.table, 'AdbLost=AdbLost+1', relay.condition)
    if relay.recv_adb_connection(3):
        relay.log.info('[ADB_STATE] - Device recovered')
        relay.db.update_value_of_row(relay.table, 'AdbRecovery=AdbRecovery+1', relay.condition)
    else:
        relay.log.error('[ADB_STATE] - Device not recovery [%s]' % __sn)
