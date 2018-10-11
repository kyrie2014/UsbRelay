# encoding: utf-8
"""
Created on 2016-12-9
@author:  Kyrie Liu
@description:  init relay
"""
from Relay import *
import time
import os
import sys
import pickle
import win32com.client


class InitRelay(Relay):

    def __init__(self, sn):
        Relay.__init__(self, sn)
        from RelayConst import Const
        self.chipset = self.exec_shell_command(Const.GETPROP_PRODUCT).strip()
        if not self.str_value:
            self.recovery_invalid_device()
            _value = self.dll.get_usb_hub_id(self.sn)
            self.value = _value if _value else self.dll.get_usb_hub_id2(self.sn)
            self.str_value = '%02x' % self.value if self.value else ''

    def pickle_bonded_device(self, pc_hub_id, relay_port):
        devices = dict()
        if os.path.exists(self.pkl_file):
            try:
                with open(self.pkl_file, 'rb') as op:
                    devices = pickle.load(op)
            except IOError:
                self.log.error('[IOError] - Not opened "%s"' % self.pkl_file)
        with open(self.pkl_file, 'wb') as op:
            devices[self.sn] = (pc_hub_id, relay_port)
            pickle.dump(devices, op)

    @property
    def inquiry_unbonded_relay_ports(self):
        """
        match device on un-bonded Relay Ports
        """
        self.log.info('[DBUG_INFO] - Inquiry all free Relay Ports')

        for i in self.get_unbond_relay_ports():
            if self.enabled_adb_on_relay_port(i):
                self.log.info('[DBUG_INFO] - Found adb enabled on Relay Port[%d]' % i)
                dev = Device(self.sn, index=i, value=self.value)
                self.relay_request(Task(dev, Const.RELAY_SET_STATE_MSG))
                self.pickle_bonded_device(self.value, i)
                return True
            time.sleep(0.5)
        else:
            self.log.info('[DBUG_INFO] - Device is not on Relay Port')
        return False

    @property
    def inquiry_bonded_relay_ports(self):
        """
        match device on bonded relay_ports
        """
        self.log.info('[DBUG_INFO] - Inquiry bonded Relay Ports')
        ports = [(v, i + 1) for i, v in enumerate(self.state) if v != '00']
        for v, i in ports:
            if self.enabled_adb_on_relay_port(i):
                self.log.info('[DBUG_INFO] - Found device [%s] on Relay Port[%d]' % (v, i))
                dev = Device(self.sn, index=i, value=self.value)
                self.relay_request(Task(dev, Const.RELAY_SET_STATE_MSG))
                self.pickle_bonded_device(self.value, i)
                return True
            time.sleep(0.5)
        else:
            self.log.info('[DBUG_INFO] - Device is un-bonded on Relay Port')
        return False

    def enabled_adb_on_relay_port(self, index, times=1):

        dev = Device(self.sn, index=index)
        self.log.info('[DBUG_INFO] - ' + '-'*35)
        for _ in range(times):
            self.relay_request(Task(dev, Const.RELAY_DISCONNT_MSG))
            time.sleep(2)
            if self.sn not in self.get_devices():
                self.relay_request(Task(dev, Const.RELAY_CONNECT_MSG))
                if self.is_enable_adb(90):
                    return True
            else:
                self.log.info('[DBUG_INFO] - Not found device on Relay Port[{}]'.format(index))
                self.relay_request(Task(dev, Const.RELAY_CONNECT_MSG))
        return False
    
    @property
    def is_bonded_index(self):
        """
        match device on bonded relay ports and release the same index
        """
        flag = False
        ports = [i + 1 for i, v in enumerate(self.state) if self.str_value == v]
        for i in ports:
            if not flag and self.enabled_adb_on_relay_port(i, 3):
                self.log.info('[DBUG_INFO] - Found device on relay port[%d]' % i)
                self.pickle_bonded_device(self.value, i)
                flag = True
                continue
            dev = Device(self.sn, index=i, value=0)
            self.relay_request(Task(dev, Const.RELAY_SET_STATE_MSG))
            self.pickle_bonded_device(0, i)
        else:
            self.log.info('[DBUG_INFO] - Updated bonded ports')
        return flag

    def get_unbond_relay_ports(self):
        __port = [i + 1 for i, v in enumerate(self.state) if '00' == v] if len(self.state) > 0 else []
        self.log.info('[DBUG_INFO] - Get free port {}'.format(__port))
        return __port

    def rel_bonded_relay_port(self, index):

        self.log.info('[DBUG_INFO] - Release relay port[{}]'.format(index))
        dev = Device(self.sn, index=index, value=0)
        if 'OK' == self.relay_request(Task(dev, Const.RELAY_SET_STATE_MSG)):
            self.log.info('[DBUG_INFO] - Released relay port[{}] success'.format(index))
            return True
        self.pickle_bonded_device(0, index)
        return False

    def bonded_relay_port_with_dev(self):

        # insert new row of database
        if not self.db.is_has_row_in_table(self.table, self.condition):
            self.db.insert_row_to_table(
                self.table,
                [0,              # index
                 self.cur_date,  # current date
                 self.hostname,  # pc hostname
                 self.chipset,   # chipset name
                 self.sn,        # serial NO.
                 'N/A',          # IMEI NO.
                 0,              # adb lost times
                 0,              # adb recovery times
                 self.build_node,# build info
                 1,              # total running times
                 0,              # total exception times
                 'None',         # comment
                 0]              # PC reboot times  
                )
        else:
            self.db.update_value_of_row(self.table, 'TotalRun=TotalRun+1', self.condition)

        if self.str_value in self.state and self.is_bonded_index:
            return

        elif not self.inquiry_unbonded_relay_ports:

            while self.check_process_exists('ResearchDownload.exe'):
                self.log.info('[WARNING] - Downloading Build...')
                time.sleep(15)

            if not self.inquiry_bonded_relay_ports:
                self.log.info('[DBUG_INFO] - Not found device on relay port')

    def check_process_exists(self, process_name):

        try:
            wmi = win32com.client.GetObject('winmgmts:')
            ret = wmi.ExecQuery('select * from Win32_Process where Name="%s"' % process_name)
        except Exception, e:
            self.log.error('[EXCEPTION] - %s : %s' % (process_name, e))
            return False
        return True if len(ret) > 0 else False

    def report(self, result):
        self.log.info('[DBUG_INFO] - Total test is %s' % result)


def init_option():
    from optparse import OptionParser
    parser = OptionParser(
        usage='%prog -p [bind|release] [sn]',
        description='bind or release usb port for relay.'
    )
    parser.add_option(
        '-p',
        '--param',
        dest='param',
        nargs=2,
        action='store',
        help='bind or release ports',
        metavar='PARAM'
     )
    (options, args) = parser.parse_args()
    return options.param if options.param else sys.exit()


if __name__ == '__main__':
    param, sn = init_option()
    init = InitRelay(sn)
    init.log.info('[DBUG_INFO] - ' + '-' * 40)
    init.log.info('[DBUG_INFO] - |' + (param.capitalize() + ' Relay Port').center(38) + '|')
    init.log.info('[DBUG_INFO] - ' + '-' * 40)
    if 'bind' == param:
        init.log.info('[DBUG_INFO] - Bond Relay Port with device [%s]' % sn)
        init.bonded_relay_port_with_dev()
    elif 'release' == param:
        init.log.info('[DBUG_INFO] - Release function is abandoned')
    init.report('pass')
