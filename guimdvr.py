#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from Tkinter import *
from functools import partial
from mdvr import MDVR
from tkMessageBox import showerror
from shangxcgui import ShangxcGUI
from time import strftime

REGIP = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
REGPORT = r'\d{1,5}$'
REGMDVRID = r'\w{10}$'
REGCARID = r'\w{1,7}$'
REGJINGDU = r'-?\d{1,5}(\.\d{1,4})?$'
REGWEIDU = r'-?\d{1,4}(\.\d{1,4})?$'
REGSPEEDANDDIRECTION = r'\d{1,3}(\.\d{1,2})?$'
REGTEMPERATURE = r'-?\d{1,3}(\.\d{1,2})?$'
REGTIME = r'\d{6} \d{6}$'
REGNO = r'.*'


class GuiMDVR(ShangxcGUI):
    def __init__(self):
        super(GuiMDVR, self).__init__()
        self.root.title('mdvr模拟器')
        self.frame = []
        self.runtimebutton = []
        for i in range(20):
            self.frame.append(Frame(self.root))
            self.frame[i].pack()
        self.ip = Entry()
        self.inputbox('ip', 'ip', 'self.frame[0]', 15, REGIP, '127.0.0.1')
        self.port = Entry()
        self.inputbox('port', '端口号', 'self.frame[0]', 5, REGPORT, '9876')
        self.mdvrid = Entry()
        self.inputbox('mdvrid', 'MDVR芯片号', 'self.frame[0]', 10, REGMDVRID, '0072001234')
        self.carid = Entry()
        self.inputbox('carid', '车牌号', 'self.frame[0]', 7, REGCARID, 'CAR1234')

        self.gps1 = Entry()
        self.inputbox('gps1', '经度', 'self.frame[1]', 11, REGJINGDU, '11619.6706')
        self.gps2 = Entry()
        self.inputbox('gps2', '纬度', 'self.frame[1]', 10, REGWEIDU, '3959.0540')
        self.speed = Entry()
        self.inputbox('speed', '速度', 'self.frame[1]', 6, REGSPEEDANDDIRECTION, '0.00')
        self.direction = Entry()
        self.inputbox('direction', '方向', 'self.frame[1]', 6, REGSPEEDANDDIRECTION, '0.00')
        self.setgps = Button()
        self.userbutton('setgps', '设置GPS', 'self.frame[1]', 'self.setgpsinfo')
        self.sendnormalgps = Button()
        self.userbutton('sendnormalgps', '发送GPS', 'self.frame[1]', 'self._sendnormalgps')

        self.databaseip = Entry()
        self.inputbox('databaseip', '数据库IP', 'self.frame[2]', 15, REGIP, '172.16.50.53')
        self.instancename = Entry()
        self.inputbox('instancename', '数据库实例名', 'self.frame[2]', 10, REGMDVRID, 'newsima')
        self.username = Entry()
        self.inputbox('username', '用户名', 'self.frame[2]', 10, REGNO, 'vms')
        self.password = Entry()
        self.inputbox('password', '密码', 'self.frame[2]', 10, REGNO, 'vms')
        self.password.config(show='*')

        self.start = Button()
        self.userbutton('start', '开始', 'self.frame[3]', 'self.startmdvr', 'NORMAL')
        self.stop = Button()
        self.userbutton('stop', '停止', 'self.frame[3]', 'self.stopmdvr')
        self.sendcarid = Button()
        self.userbutton('sendcarid', '设置并发送车牌号', 'self.frame[3]', 'self._sendcarid')
        self.selfcheck = Button()
        self.userbutton('selfcheck', '发送自检', 'self.frame[3]', 'self.sendselfcheck')
        self.insertvideodata = Button()
        self.userbutton('insertvideodata', '插入视频数据', 'self.frame[3]', 'self._insertvideodata')
        self.startonekeyalarm = Button()
        self.userbutton('startonekeyalarm', '一键报警', 'self.frame[3]', 'self._startonekeyalarm')
        self.stoponekeyalarm = Button()
        self.userbutton('stoponekeyalarm', '停止一键报警', 'self.frame[3]', 'self._stoponekeyalarm')
        self.fencealert = Button()
        self.userbutton('fencealert', '区域围栏告警', 'self.frame[3]', 'self._fencealert')
        self.overspeedalert = Button()
        self.userbutton('overspeedalert', '超速告警', 'self.frame[3]', 'self._overspeedalert')

        Label(self.frame[4], text='已设置电子围栏编号：').pack(side=LEFT)
        self.trafficfenceids = []
        for i in range(10):
            self.trafficfenceids.append(Text(self.frame[4], width=6, height=1, relief=GROOVE, state=DISABLED, bg='lightgray'))
            self.trafficfenceids[i].pack(side=LEFT)
        self.trafficfenceidsreflash = Button()
        self.userbutton('trafficfenceidsreflash', '刷新', 'self.frame[4]', 'self._trafficfenceidsreflash')

        Label(self.frame[5], text=' 超速告警参数').pack(side=LEFT)
        Label(self.frame[5], text='       是否开启:').pack(side=LEFT)
        self.speedruleonoff = Label(self.frame[5], relief=RIDGE, width=5)
        self.speedruleonoff.pack(side=LEFT)
        Label(self.frame[5], text=' 低速限制:').pack(side=LEFT)
        self.speedrulemin = Label(self.frame[5], relief=RIDGE, width=5)
        self.speedrulemin.pack(side=LEFT)
        Label(self.frame[5], text=' 高速限制:').pack(side=LEFT)
        self.speedrulemax = Label(self.frame[5], relief=RIDGE, width=5)
        self.speedrulemax.pack(side=LEFT)
        Label(self.frame[5], text=' 持续时间:').pack(side=LEFT)
        self.speedruletime = Label(self.frame[5], relief=RIDGE, width=6)
        self.speedruletime.pack(side=LEFT)
        self.speedrulereflash = Button()
        self.userbutton('speedrulereflash', '刷新', 'self.frame[5]', 'self._speedrulereflash')

        self.inout = IntVar()
        self.inout.set(0)
        Label(self.frame[6], text='进出电子围栏告警：').pack(side=LEFT)
        Radiobutton(self.frame[6], variable=self.inout, text='出电子围栏', value=0).pack(side=LEFT)
        Radiobutton(self.frame[6], variable=self.inout, text='进电子围栏', value=1).pack(side=LEFT)
        self.trafficfenceid = Entry()
        self.inputbox('trafficfenceid', '      告警电子围栏编号', 'self.frame[6]', 5, 'REGPORT', '0')

        self.subtype = IntVar()
        self.subtype.set(12)
        Label(self.frame[7], text='区域告警子类型：').pack(side=LEFT)
        Radiobutton(self.frame[7], variable=self.subtype, text='越界告警', value=12, command=self.changesubtype).pack(side=LEFT)
        Radiobutton(self.frame[7], variable=self.subtype, text='围栏内速度告警', value=13, command=self.changesubtype).pack(side=LEFT)
        self.speedoverlower = IntVar()
        self.speedoverlower.set(0)
        self.speedoverlowertips = Label(self.frame[7], text='          围栏内低速/超速：', fg='gray')
        self.speedoverlowertips.pack(side=LEFT)
        self.speedoverlower1 = Radiobutton(self.frame[7], variable=self.speedoverlower, text='低速', value=0, state=DISABLED)
        self.speedoverlower1.pack(side=LEFT)
        self.speedoverlower2 = Radiobutton(self.frame[7], variable=self.speedoverlower, text='超速', value=1, state=DISABLED)
        self.speedoverlower2.pack(side=LEFT)

        self.minspeed = Entry()
        self.inputbox('minspeed', '最小速度', 'self.frame[8]', 6, REGSPEEDANDDIRECTION, '0.00')
        self.maxspeed = Entry()
        self.inputbox('maxspeed', '最大速度', 'self.frame[8]', 6, REGSPEEDANDDIRECTION, '0.00')
        self.duringtime = Entry()
        self.inputbox('duringtime', '持续时间', 'self.frame[8]', 5, REGPORT, '0')
        self.alarmminspeed = Entry()
        self.inputbox('alarmminspeed', '告警最小速度', 'self.frame[8]', 6, REGSPEEDANDDIRECTION, '0.00')
        self.alarmmaxspeed = Entry()
        self.inputbox('alarmmaxspeed', '告警最大速度', 'self.frame[8]', 6, REGSPEEDANDDIRECTION, '0.00')

        self.temperaturetype = IntVar()
        self.temperaturetype.set(0)
        Label(self.frame[9], text='温度类型：').pack(side=LEFT)
        Radiobutton(self.frame[9], variable=self.temperaturetype, text='安全套件温度', value=0).pack(side=LEFT)
        Radiobutton(self.frame[9], variable=self.temperaturetype, text='发动机温度', value=1).pack(side=LEFT)
        Radiobutton(self.frame[9], variable=self.temperaturetype, text='车厢内温度', value=2).pack(side=LEFT)
        self.temperaturealerttype = IntVar()
        self.temperaturealerttype.set(0)
        Label(self.frame[9], text='          告警类别：').pack(side=LEFT)
        Radiobutton(self.frame[9], variable=self.temperaturealerttype, text='低温告警', value=0).pack(side=LEFT)
        Radiobutton(self.frame[9], variable=self.temperaturealerttype, text='高温告警', value=1).pack(side=LEFT)

        self.currenttemperature = Entry()
        self.inputbox('currenttemperature', '触发时温度', 'self.frame[10]', 7, REGTEMPERATURE, '0.00')
        self.mintemperature = Entry()
        self.inputbox('mintemperature', '温度最低值', 'self.frame[10]', 7, REGTEMPERATURE, '0.00')
        self.maxtemperature = Entry()
        self.inputbox('maxtemperature', '温度最高值', 'self.frame[10]', 7, REGTEMPERATURE, '0.00')
        self.temperaturealert = Button()
        self.userbutton('temperaturealert', '发送温度异常告警', 'self.frame[10]', 'self._temperaturealert')

        self.gpsalerttype = IntVar()
        self.gpsalerttype.set(2)
        Label(self.frame[11], text='          GPS告警类型：').pack(side=LEFT)
        Radiobutton(self.frame[11], variable=self.gpsalerttype, text='信号由有效变无效', value=0, state=DISABLED).pack(side=LEFT)
        Radiobutton(self.frame[11], variable=self.gpsalerttype, text='信号由无效变有效', value=1, state=DISABLED).pack(side=LEFT)
        Radiobutton(self.frame[11], variable=self.gpsalerttype, text='GPS信号接收机故障', value=2).pack(side=LEFT)

        self.histime = Entry()
        self.inputbox('histime', '历史时间', 'self.frame[12]', 13, REGTEMPERATURE, strftime('%y%m%d %H%M%S'))
        self.hisgps1 = Entry()
        self.inputbox('hisgps1', '历史经度', 'self.frame[12]', 11, REGJINGDU, '11619.6706')
        self.hisgps2 = Entry()
        self.inputbox('hisgps2', '历史纬度', 'self.frame[12]', 10, REGWEIDU, '3959.0540')
        self.gpsalert = Button()
        self.userbutton('gpsalert', '发送GPS接收机故障告警', 'self.frame[12]', 'self._gpsalert')

        Label(self.frame[18], text='最后接收指令：').pack(side=LEFT)
        self.lastreceive = Label(self.frame[18],justify=LEFT)
        self.lastreceive.pack(side=LEFT)
        self.lastreflash = Button()
        self.userbutton('lastreflash', '刷新', 'self.frame[18]', 'self._lastreflash')

        # self.tmp = Button()
        # self.userbutton('tmp', 'test', 'self.frame[19]', 'self.test', 'NORMAL')


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

    def record(self, limit, ev=None):
        str = ev.widget.get()
        self._tmp = str if len(str) <= limit else self._tmp

    # def lenlimit(self, limit, checkrule=REGNO, ev=None):
    #     widget = ev.widget
    #     str = widget.get()
    #     if len(str) > limit:
    #         widget.delete(0, END)
    #         widget.insert(0, self._tmp)
    #     self.check(checkrule,ev)

    # def check(self, checkrule, ev=None):
    #     widget = ev.widget
    #     str = widget.get()
    #     if checkrule.match(str) == None:
    #         widget.config(bg='red', fg='white')
    #     else:
    #         widget.config(bg='white', fg='black')

    # def _bind(self, obj, limit, checkrule):
    #     obj.bind('<KeyPress>', lambda ev=None: self.record(limit, ev))
    #     obj.bind('<KeyRelease>', lambda ev=None: self.lenlimit(limit, checkrule, ev))
        # obj.bind('<FocusOut>', lambda ev=None: self.check(checkrule, ev))

    def startmdvr(self):
        self.mdvrcli = MDVR(self.mdvrid.get(), self.carid.get(), self.ip.get(), int(self.port.get()),
                            self.gps1.get(), self.gps2.get(), self.speed.get(), self.direction.get())
        if self.mdvrcli.start() == -1:
            showerror('ERROR', '无法连接，请检查ip、端口号等配置！！！')
        else:
            self.mdvrid.config(state=DISABLED)
            self.ip.config(state=DISABLED)
            self.port.config(state=DISABLED)
            self.start.config(state=DISABLED)
            for i in self.runtimebutton:
                i.config(state=NORMAL)
            self.stoponekeyalarm.config(state=DISABLED)

    def stopmdvr(self):
        self.mdvrcli.stop()
        self.mdvrid.config(state=NORMAL)
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

    def _sendnormalgps(self):
        self.mdvrcli.sendgps(0)

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
        fg = 'black' if state == NORMAL else 'gray'
        self.speedoverlowertips.config(fg=fg)
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

    def _sendcarid(self):
        self.mdvrcli.carID = self.carid.get()
        self.mdvrcli.sendonline()

    def _insertvideodata(self):
        self.mdvrcli.insertvideotodatabase(self.databaseip.get(), self.instancename.get(), self.username.get(), self.password.get())

    def _speedrulereflash(self):
        self.speedruleonoff.config(text='开启' if self.mdvrcli.speedrule[0] else '关闭')
        self.speedrulemin.config(text=self.mdvrcli.speedrule[1])
        self.speedrulemax.config(text=self.mdvrcli.speedrule[2])
        self.speedruletime.config(text=self.mdvrcli.speedrule[3])

    def _overspeedalert(self):
        self.mdvrcli.sendV70(self.minspeed.get(), self.maxspeed.get(), self.duringtime.get())

    def _temperaturealert(self):
        self.mdvrcli.sendV68(self.temperaturetype.get(), self.currenttemperature.get(), self.mintemperature.get(), self.maxtemperature.get(), self.temperaturealerttype.get())

    def test(self):
        self.mdvrcli.trafficfenceid = ['12345', '23456', '34567', '45678', '56789', '67890', '78901']
        self.mdvrcli.speedrule = (True, 0,123,444)

    def _lastreflash(self):
        self.lastreceive.config(text=self.mdvrcli.lastreceive)

    def _gpsalert(self):
        self.mdvrcli.sendV75(self.gpsalerttype.get(), self.histime.get(), self.hisgps1.get(), self.hisgps2.get())


if __name__ == '__main__':
    GuiMDVR()
    mainloop()
