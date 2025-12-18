# -*- coding: utf-8 -*-
"""
Created on 2017-2-3  
@author:  Kyrie Liu  
@description:  usb relay trigger
"""
from RelayConst import Const
from SerialComm import SerialComm
from RelayUtils import *
import socket
import pickle


class TaskManager:
    def __init__(self):
        self.ot = None
        self.serial = SerialComm('server')
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(('localhost', 11222))
            self.sock.listen(5)
        except socket.error as msg:
            self.serial.log.info(msg)
            sys.exit(1)

    def out_task(self):
        ret = 'KO'
        while self.serial.is_opened():
            task = yield ret
            ret = self.__handle(task)
            self.serial.log.info('[OUT_TASK] - Finshed task "%s"...' % task)

    def in_task(self):
        self.ot = self.out_task()
        ret = self.ot.send(None)
        while True:
            self.serial.log.info('[ IN_TASK] - Waiting connection...')
            connt, address = self.sock.accept()
            buf = connt.recv(1024)
            if buf is not None:
                task = pickle.loads(buf)
                self.serial.log.info('[ IN_TASK] - ----------------------------------')
                self.serial.log.info('[ IN_TASK] - New task, turn to task "%s"' % task)
                ret = self.ot.send(task)
                connt.send(pickle.dumps(ret))

    def __handle(self, task):

        ret = 'OK'
        event, index, value = task.msg, task.index, task.value

        # disconnect usb port
        if event == Const.RELAY_DISCONNT_MSG:
            self.serial.usb_off(index)
        # connect usb port
        elif event == Const.RELAY_CONNECT_MSG:
            self.serial.usb_on(index)
        elif event == Const.RELAY_SET_STATE_MSG:
            self.serial.set_relay_port_state(index, value)
        elif event == Const.RELAY_GET_STATE_MSG:
            ret = self.serial.get_relay_port_states()
        elif event == Const.RELAY_DISCONNT_MSG_SEC:
            self.serial.usb_off_sec(value)
        elif event == Const.RELAY_CONNECT_MSG_SEC:
            self.serial.usb_on_sec(value)
        return ret

    def __del__(self):
        if self.ot is not None:
            self.ot.close()


def center_window(root, w, h):
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))


if __name__ == '__main__':
    try:
        tm = TaskManager()
        tm.in_task()
    except Exception as err:
        print('Exception: ' + str(err))
        try:
            import tkinter as tk
        except ImportError:
            import Tkinter as tk
        window = tk.Tk()
        window.title('继电器异常')
        window.resizable(0, 0)
        window.wm_attributes('-topmost', 1)
        center_window(window, 250, 120)
        var = tk.StringVar()
        var.set(u'错误信息: \n'+
                u'"RelayServer.exe"服务已断开!\n'+
                u'请重新启动 "RelayServer.exe"')
        label = tk.Label(window,
                         textvariable=var,
                         font=('Arial', 10),
                         width=250,
                         height=4)
        label.pack()
        import sys
        btn = tk.Button(window,
                        text='取消',
                        width=8,
                        height=1,
                        command=sys.exit)
        btn.place(x=88, y=70)
        window.mainloop()
