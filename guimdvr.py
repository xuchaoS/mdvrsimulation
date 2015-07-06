#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from Tkinter import *
from functools import partial
from mdvr import MDVR
from tkMessageBox import showerror
from time import sleep

REGIP = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
REGPORT = re.compile(r'\d{1,5}$')
REGMDVRID = re.compile(r'\w{10}$')
REGCARID = re.compile(r'\w{1,7}$')
REGJINGDU = re.compile(r'-?\d{1,5}(\.\d{1,4})?$')
REGWEIDU = re.compile(r'-?\d{1,4}(\.\d{1,4})?$')
REGSPEEDANDDIRECTION = re.compile(r'\d{1,3}(\.\d{1,2})?$')


class GuiMDVR(object):
    def __init__(self):
        self.root = Tk()
        self.root.title('mdvr模拟器')
        self.frame = []
        self.runtimebutton = []
        self._tmp = ''
        for i in range(10):
            self.frame.append(Frame(self.root))
            self.frame[i].pack()
        self.ip = Entry()
        self.inputbox('ip', 'ip', 'self.frame[0]', 15, 'REGIP', '127.0.0.1')
        self.port = Entry()
        self.inputbox('port', '端口号', 'self.frame[0]', 5, 'REGPORT', '9876')
        self.mdvrid = Entry()
        self.inputbox('mdvrid', 'MDVR芯片号', 'self.frame[0]', 10, 'REGMDVRID', '0072001234')
        self.carid = Entry()
        self.inputbox('carid', '车牌号', 'self.frame[0]', 7, 'REGCARID', 'car1234')

        self.gps1 = Entry()
        self.inputbox('gps1', '经度', 'self.frame[1]', 11, 'REGJINGDU', '11619.6706')
        self.gps2 = Entry()
        self.inputbox('gps2', '纬度', 'self.frame[1]', 10, 'REGWEIDU', '3959.0540')
        self.speed = Entry()
        self.inputbox('speed', '速度', 'self.frame[1]', 6, 'REGSPEEDANDDIRECTION', '0.00')
        self.direction = Entry()
        self.inputbox('direction', '方向', 'self.frame[1]', 6, 'REGSPEEDANDDIRECTION', '0.00')
        self.setgps = Button()
        self.userbutton('setgps', '设置GPS', 'self.frame[1]', 'self.setgpsinfo')

        self.start = Button()
        self.userbutton('start', '开始', 'self.frame[2]', 'self.startmdvr', 'NORMAL')
        self.stop = Button()
        self.userbutton('stop', '停止', 'self.frame[2]', 'self.stopmdvr')
        self.selfcheck = Button()
        self.userbutton('selfcheck', '发送自检', 'self.frame[2]', 'self.sendselfcheck')
        self.startonekeyalarm = Button()
        self.userbutton('startonekeyalarm', '一键报警', 'self.frame[2]', 'self._startonekeyalarm')
        self.stoponekeyalarm = Button()
        self.userbutton('stoponekeyalarm', '停止一键报警', 'self.frame[2]', 'self._stoponekeyalarm')
        self.fencealert = Button()
        self.userbutton('fencealert', '区域围栏告警', 'self.frame[2]', 'self._fencealert')

        Label(self.frame[3], text='已设置电子围栏编号：').pack(side=LEFT)
        self.trafficfenceids = []
        for i in range(10):
            self.trafficfenceids.append(Text(self.frame[3], width=6, height=1, relief=GROOVE, state=DISABLED, bg='lightgray'))
            self.trafficfenceids[i].pack(side=LEFT)
        self.userbutton('trafficfenceidsreflash', '刷新', 'self.frame[3]', 'self._trafficfenceidsreflash')

        self.inout = IntVar()
        self.inout.set(0)
        Label(self.frame[4], text='进出电子围栏告警：').pack(side=LEFT)
        Radiobutton(self.frame[4], variable=self.inout, text='进电子围栏', value=0).pack(side=LEFT)
        Radiobutton(self.frame[4], variable=self.inout, text='出电子围栏', value=1).pack(side=LEFT)
        self.trafficfenceid = Entry()
        self.inputbox('trafficfenceid', '      告警电子围栏编号', 'self.frame[4]', 5, 'REGPORT', '0')

        self.subtype = IntVar()
        self.subtype.set(12)
        Label(self.frame[5], text='区域告警子类型：').pack(side=LEFT)
        Radiobutton(self.frame[5], variable=self.subtype, text='越界告警', value=12, command=self.changesubtype).pack(side=LEFT)
        Radiobutton(self.frame[5], variable=self.subtype, text='围栏内速度告警', value=13, command=self.changesubtype).pack(side=LEFT)
        self.speedoverlower = IntVar()
        self.speedoverlower.set(0)
        Label(self.frame[5], text='    围栏内低速/超速：').pack(side=LEFT)
        self.speedoverlower1 = Radiobutton(self.frame[5], variable=self.speedoverlower, text='低速', value=0, state=DISABLED)
        self.speedoverlower1.pack(side=LEFT)
        self.speedoverlower2 = Radiobutton(self.frame[5], variable=self.speedoverlower, text='超速', value=1, state=DISABLED)
        self.speedoverlower2.pack(side=LEFT)

        self.minspeed = Entry()
        self.inputbox('minspeed', '最小速度', 'self.frame[6]', 6, 'REGSPEEDANDDIRECTION', '0.00', 'DISABLED')
        self.maxspeed = Entry()
        self.inputbox('maxspeed', '最大速度', 'self.frame[6]', 6, 'REGSPEEDANDDIRECTION', '0.00', 'DISABLED')
        self.duringtime = Entry()
        self.inputbox('duringtime', '持续时间', 'self.frame[6]', 6, 'REGSPEEDANDDIRECTION', '0.00', 'DISABLED')
        self.alarmminspeed = Entry()
        self.inputbox('alarmminspeed', '告警最小速度', 'self.frame[6]', 6, 'REGSPEEDANDDIRECTION', '0.00', 'DISABLED')
        self.alarmmaxspeed = Entry()
        self.inputbox('alarmmaxspeed', '告警最大速度', 'self.frame[6]', 6, 'REGSPEEDANDDIRECTION', '0.00', 'DISABLED')


    def userbutton(self, name, tips, father, command, state='DISABLED'):
        exec "self.%s = Button(%s, text='%s', command=%s, state=%s, bd=3)" % (name, father, tips, command, state)
        exec "self.%s.pack(side=LEFT)" % (name)
        exec '''if %s == DISABLED:
            self.runtimebutton.append(self.%s)''' % (state, name)

    def inputbox(self, name, tips, father, limit, checkrule, defaultvalue, state='NORMAL'):
        exec "Label(%s, text=' %s:').pack(side=LEFT)" % (father, tips)
        exec "self.%s = Entry(%s, bg='white', justify=CENTER, width=%d)" % (name, father, limit+5)
        exec "self._bind(self.%s, %s, %s)" % (name, limit, checkrule)
        exec "self.%s.insert(0, '%s')" % (name, defaultvalue)
        exec "self.%s.pack(side=LEFT)" % (name)
        exec "self.%s.config(state=%s)" % (name, state)

    def record(self, limit, ev=None):
        str = ev.widget.get()
        self._tmp = str if len(str) <= limit else self._tmp

    def lenlimit(self, limit, ev=None):
        widget = ev.widget
        str = widget.get()
        if len(str) > limit:
            widget.delete(0, END)
            widget.insert(0, self._tmp)

    def check(self, checkrule, ev=None):
        widget = ev.widget
        str = widget.get()
        if checkrule.match(str) == None:
            widget.config(bg='red', fg='white')
        else:
            widget.config(bg='white', fg='black')

    def _bind(self, obj, limit, checkrule):
        obj.bind('<KeyPress>', lambda ev=None: self.record(limit, ev))
        obj.bind('<KeyRelease>', lambda ev=None: self.lenlimit(limit, ev))
        obj.bind('<FocusOut>', lambda ev=None: self.check(checkrule, ev))

    def startmdvr(self):
        self.mdvrcli = MDVR(self.mdvrid.get(), self.carid.get(), self.ip.get(), int(self.port.get()),
                            self.gps1.get(), self.gps2.get(), self.speed.get(), self.direction.get())
        self.mdvrcli.start()
        self.mdvrid.config(state=DISABLED)
        self.carid.config(state=DISABLED)
        self.ip.config(state=DISABLED)
        self.port.config(state=DISABLED)
        self.start.config(state=DISABLED)
        for i in self.runtimebutton:
            i.config(state=NORMAL)
        self.stoponekeyalarm.config(state=DISABLED)
        self.test()

    def stopmdvr(self):
        self.mdvrcli.stop()
        self.mdvrid.config(state=NORMAL)
        self.carid.config(state=NORMAL)
        self.ip.config(state=NORMAL)
        self.port.config(state=NORMAL)
        self.start.config(state=NORMAL)
        for i in self.runtimebutton:
            i.config(state=DISABLED)

    def setgpsinfo(self):
        self.mdvrcli.setgps(self.gps1.get(), self.gps2.get(), self.speed.get(), self.direction.get())

    def _startonekeyalarm(self):
        self.mdvrcli.onekeyalarm()
        self.stoponekeyalarm.config(state=NORMAL)

    def _stoponekeyalarm(self):
        self.mdvrcli.stoponekeyalarm()
        self.stoponekeyalarm.config(state=DISABLED)

    def sendselfcheck(self):
        self.mdvrcli.sendselfcheck()

    def _trafficfenceidsreflash(self):
        for i in range(10):
            self.trafficfenceids[i].config(state=NORMAL)
            self.trafficfenceids[i].delete(1.0, END)
        for i in range(len(self.mdvrcli.trafficfenceid)):
            self.trafficfenceids[i].insert(1.0, self.mdvrcli.trafficfenceid[i])
        for i in range(10):
            self.trafficfenceids[i].config(state=DISABLED)

    def changesubtype(self):
        state = NORMAL if self.subtype.get() == 13 else DISABLED
        self.minspeed.config(state=state)
        self.maxspeed.config(state=state)
        self.duringtime.config(state=state)
        self.alarmminspeed.config(state=state)
        self.alarmmaxspeed.config(state=state)
        self.speedoverlower1.config(state=state)
        self.speedoverlower2.config(state=state)

    def _fencealert(self):
        if self.subtype.get() == 12:
            print 12
            self.mdvrcli.sendV79(self.inout.get(), self.trafficfenceid.get(), 12)
        elif self.subtype.get() == 13:
            print 13
            self.mdvrcli.sendV79(self.inout.get(), self.trafficfenceid.get(), 13,
                                 self.speedoverlower.get(), self.minspeed.get(), self.maxspeed.get(), self.duringtime.get(), self.alarmminspeed.get(), self.alarmmaxspeed.get())

    def test(self):
        self.mdvrcli.trafficfenceid = ['12345', '23456', '34567', '45678', '56789', '67890', '78901']


if __name__ == '__main__':
    GuiMDVR()
    mainloop()
