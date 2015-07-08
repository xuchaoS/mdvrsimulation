#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from Tkinter import *
from shangxcgui import ShangxcGUI

# REGJINGDU = re.compile(r'-?\d{1,3}(\.\d{1,6})?$')
# REGWEIDU = re.compile(r'-?\d{1,2}(\.\d{1,6})?$')
# REGNO = re.compile(r'.*')
REGJINGDU = r'-?\d{1,3}(\.\d{1,6})?$'
REGWEIDU = r'-?\d{1,2}(\.\d{1,6})?$'
REGNO = r'.*'

class GPSexchange(ShangxcGUI):
    def __init__(self):
        super(GPSexchange, self).__init__()
        # self._tmp = ''
        # self.root = Tk()
        self.root.title('GPS转换器')
        self.frame = []
        for i in range(10):
            self.frame.append(Frame(self.root))
            self.frame[i].pack()
        Label(self.frame[0], text='转换前      ').pack(side=LEFT)
        self.gps1before = Entry()
        self.inputbox('gps1before', '经度', 'self.frame[0]', 11, REGJINGDU, '0')
        self.gps2before = Entry()
        self.inputbox('gps2before', '纬度', 'self.frame[0]', 10, REGWEIDU, '0')
        self.speed = Entry()

        Label(self.frame[1], text='转换后      ').pack(side=LEFT)
        Label(self.frame[1], text=' 经度:').pack(side=LEFT)
        self.gps1after = Text(self.frame[1], width=16, height=1, relief=GROOVE, state=DISABLED, bg='lightgray')
        self.gps1after.pack(side=LEFT)
        Label(self.frame[1], text=' 纬度:').pack(side=LEFT)
        self.gps2after = Text(self.frame[1], width=15, height=1, relief=GROOVE, state=DISABLED, bg='lightgray')
        self.gps2after.pack(side=LEFT)

        self.exchange = Button()
        self.userbutton('exchange', '转换', 'self.frame[2]', 'self._exchange', 'NORMAL')

    # def userbutton(self, name, tips, father, command, state='DISABLED'):
    #     exec "self.%s = Button(%s, text='%s', command=%s, state=%s, bd=3)" % (name, father, tips, command, state)
    #     exec "self.%s.pack(side=LEFT)" % (name)
    #     exec '''if %s == DISABLED:
    #         self.runtimebutton.append(self.%s)''' % (state, name)
    #
    # def inputbox(self, name, tips, father, limit, checkrule, defaultvalue, state='NORMAL'):
    #     exec "Label(%s, text=' %s:').pack(side=LEFT)" % (father, tips)
    #     exec "self.%s = Entry(%s, bg='white', justify=CENTER, width=%d)" % (name, father, limit+5)
    #     exec "self._bind(self.%s, %s, %s)" % (name, limit, checkrule)
    #     exec "self.%s.insert(0, '%s')" % (name, defaultvalue)
    #     exec "self.%s.pack(side=LEFT)" % (name)
    #     exec "self.%s.config(state=%s)" % (name, state)
    #
    # def lenlimit(self, limit, checkrule=REGNO, ev=None):
    #     widget = ev.widget
    #     str = widget.get()
    #     if len(str) > limit:
    #         widget.delete(0, END)
    #         widget.insert(0, self._tmp)
    #     self.check(checkrule,ev)
    #
    # def check(self, checkrule, ev=None):
    #     widget = ev.widget
    #     str = widget.get()
    #     if checkrule.match(str) == None:
    #         widget.config(bg='red', fg='white')
    #     else:
    #         widget.config(bg='white', fg='black')
    #
    # def _bind(self, obj, limit, checkrule):
    #     obj.bind('<KeyPress>', lambda ev=None: self.record(limit, ev))
    #     obj.bind('<KeyRelease>', lambda ev=None: self.lenlimit(limit, checkrule, ev))
    #
    # def _exchange(self):
    #     tmp = (float(self.gps1before.get()), float(self.gps2before.get()))
    #     for i, j in zip((self.gps1after, self.gps2after),(0,1)):
    #         i.config(state=NORMAL)
    #         i.delete(1.0, END)
    #         i.insert(1.0, '%.4f' % (int(tmp[j])*100+(tmp[j]-int(tmp[j]))*60))
    #         i.config(state=DISABLED)

    def record(self, limit, ev=None):
        str = ev.widget.get()
        self._tmp = str if len(str) <= limit else self._tmp

if __name__ == '__main__':
    GPSexchange()
    mainloop()