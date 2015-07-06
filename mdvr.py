#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from socket import socket, AF_INET, SOCK_STREAM,error
from threading import Thread
from time import ctime, strftime, sleep
import re
from uuid import uuid1

REGCJI = re.compile(r',\w{10},[^,]*,(C\d{1,3}),.*')
REGCOUNT = re.compile(r',\w{10},([^,]*),C\d{1,3},\d+ \d+,.*')
REGSERVERTIME = re.compile(r',\w{10},[^,]*,C\d{1,3},(\d+ \d+),.*')
REGTRAFFICFENCE = re.compile(r',\w{10},[^,]*,C107,\d+ \d+,(\d*),(\d),.*')
COMMONVMESSAGE = ',%s,%s,%s,%s,%s,%s,%s,%s,%s,8100000000000000,0000000000000000,46.00,999.00,01000000.0000,,,0,0,0,'
SENDMESSAGE = {'V1': '0.0.3.08,0101,%s:%s,0,2,,%s#',
               'V30': '%d#',
               'V61': ',,,,,,,,,,,,,,,,%d,1,1,PB1#',
               'V79': ',,,,,,,,,,,,,,,,%s,1,1,%d,%s,,,%d,%d%s#',
               'V77': '02000000,,#',
               'V600': '''3,1,1327,1327,<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<MDVRBus version="1.0">
    <CheckInfo UNIT_ID="%s" _TIME_="2015/05/25 10:33:18 MON" _ZONE_="-4:30">
        <InfoClass _TYPE_="InspectInfo">
            <InfoList>
                <_INFO_ _NAME_="_SN_" _STAT_="%s" />
                <_INFO_ _NAME_="_TIME_" _STAT_="2015/05/25 10:33:18 MON" />
                <_INFO_ _NAME_="RecSD" _STAT_="E" />
                <_INFO_ _NAME_="GPSINFO" _STAT_="%s" />
                <_INFO_ _NAME_="Sensor1" _STAT_="FAIL" />
                <_INFO_ _NAME_="Sensor2" _STAT_="NOEXIST" />
                <_INFO_ _NAME_="Sensor3" _STAT_="NOEXIST" />
                <_INFO_ _NAME_="StandbyPower" _STAT_="10.00V" />
                <_INFO_ _NAME_="3GModule" _STAT_="OK" />
                <_INFO_ _NAME_="Channel1" _STAT_="OK" />
                <_INFO_ _NAME_="Channel2" _STAT_="OK" />
                <_INFO_ _NAME_="Channel3" _STAT_="OK" />
                <_INFO_ _NAME_="Channel4" _STAT_="OK" />
                <_INFO_ _NAME_="CurInTemperature" _STAT_="46.0" />
                <_INFO_ _NAME_="SIM" _STAT_="VALID" />
                <_INFO_ _NAME_="CurVoltage" _STAT_="11.0V" />
                <_INFO_ _NAME_="SdCapacity" _STAT_="500.1G" />
            </InfoList>
        </InfoClass>
    </CheckInfo>
</MDVRBus>
#'''}
REPLYMESSAGE = {'C70': '%s,,#',
                'C107': '%s,1%s#'}
ERRORCODE = {'00030011': 'area limited by adding',
             '00030012': 'area existing by adding',
             '00030021': 'not exist by modifying',
             '00030031': 'not exist by deleting'}

mdvrList = {}


class MDVR(Thread):
    def __init__(self, mdvrid, carid, ip='127.0.0.1', port=9876, gps1='', gps2='', speed='0', direction='0'):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.mdvrID = mdvrid
        self.carID = carid
        self.gpsinfo = ['V', gps1, gps2, speed, direction]
        self.setgps(gps1, gps2, speed, direction)
        self.bianhao = 0
        self.connect = False
        self.onekeyalarmed = False
        self.onekeyalarmtimes = 0
        self.setName(self.mdvrID)
        mdvrList[self.mdvrID] = self
        self.trafficfenceid = []

    def run(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.sock.connect((self.ip, self.port))
        except error:
            self.log('Connect fail!!!')
        else:
            self.connect = True
            receive = Thread(target=self.receive)
            receive.setDaemon(True)
            receive.start()
            self.sendonline()
            self.sendselfcheck()
            heartbeat = Thread(target=self.heartbeat)
            heartbeat.setDaemon(True)
            heartbeat.start()

    def sendonline(self):
        self.send('V1', self.ip, self.port, self.carID)

    def heartbeat(self, delay=60):
        sleep(delay)
        while True:
            if self.connect and not self.onekeyalarmed:
                self.sock.send('90dc')
                self.log('send   :', '90dc')
                sleep(delay)

    def stop(self):
        self.connect = False
        self.sock.close()

    def sendselfcheck(self):
        self.send('V600', self.mdvrID, self.mdvrID, self.gpsinfo[0])

    def sendonekeyalarm(self):
        self.send('V61', self.onekeyalarmtimes)
        self.onekeyalarmtimes += 1

    def sendV79(self, inout, trafficfenceid, subtype,
                speedoverlower=None, minspeed=0, maxspeed=0, duringtime=0, alarmminspeed=0, alarmmaxspeed=0):
        parameternum = 0
        substr = ''
        if subtype == 12:
            pass
        elif subtype == 13:
            parameternum = 7
            substr = ',%s,%.2f,%.2f,%s,%.2f,%.2f,%.2f' % (speedoverlower, float(minspeed), float(maxspeed), self.gpsinfo[3], float(duringtime), float(alarmminspeed), float(alarmmaxspeed))
        self.send('V79', uuid1(), inout, trafficfenceid, subtype, parameternum, substr)

    def sendgps(self, gpstype):
        self.send('V30', gpstype)

    def _onekeyalarm(self):
        self.sendonekeyalarm()
        if not self.onekeyalarmed:
            self.onekeyalarmed = True
            for i in xrange(2400):
                if self.onekeyalarmed:
                    self.sendgps(4)
                    sleep(1)
                else:
                    break

    def onekeyalarm(self):
        oka = Thread(target=self._onekeyalarm)
        oka.setDaemon(True)
        oka.start()

    def receive(self):
        while True:
            rec1 = self.sock.recv(4)
            if rec1 == '90dc':
                self.log('receive:', rec1)
            elif rec1 == '99dc':
                rec2 = self.sock.recv(4)
                leaveLen = int(rec2)
                rec3 = self.sock.recv(leaveLen)
                self.log('receive:', rec1, rec2, rec3)
                tmp = Thread(target=self.dataanalysis, args=(rec3,))
                tmp.start()

    def dataanalysis(self, data):
        analysised = self.stranalysis(data)
        try:
            servertime = analysised['servertime']
            count = analysised['count']
            # print 'mdvrtime and count'
        except KeyError, e:
            print 'KeyError:', e.message
        else:
            try:
                cji = analysised['cji']
                # print 'vji'
            except KeyError, e:
                print 'KeyError:', e.message
            else:
                if cji == 'C0':
                    pass
                elif cji == 'C70':
                    self.replyC70(count, servertime, '1')
                    self.stoponekeyalarm()
                elif cji == 'C107':
                    self.analysisC107(data, count, servertime)
                    # self.replyC107(count, servertime, '1')
                    # try:
                    #     trafficfence = REGTRAFFICFENCE.match(data)
                    #     if trafficfence.group(2) == '1':
                    #         if trafficfence.group(1) not in self.trafficfenceid:
                    #             self.trafficfenceid.append(trafficfence.group(1))
                    #     elif trafficfence.group(2) == '3':
                    #         try:
                    #             self.trafficfenceid.remove(trafficfence.group(1))
                    #         except ValueError:
                    #             pass
                    # except AttributeError:
                    #     pass


    def analysisC107(self, data, count, servertime):
        success = '0'
        errorcode = ''
        extramessage = ''

        try:
            trafficfence = REGTRAFFICFENCE.match(data)
            if trafficfence.group(2) == '1':
                if len(self.trafficfenceid) >=10:
                    errorcode = '00030011'
                elif trafficfence.group(1) in self.trafficfenceid:
                    errorcode = '00030012'
                else:
                    self.trafficfenceid.append(trafficfence.group(1))
                    success = '1'
            elif trafficfence.group(2) == '2':
                if trafficfence.group(1) in self.trafficfenceid:
                    success = '1'
                else:
                    errorcode = '00030021'
            elif trafficfence.group(2) == '3':
                try:
                    self.trafficfenceid.remove(trafficfence.group(1))
                    success = '1'
                except ValueError:
                    errorcode = '00030031'
            if success == '0':
                extramessage = '1,1,1,%s,%s' % (errorcode, ERRORCODE[errorcode])
            elif success == '1':
                extramessage = ''
            self.replyC107(count, servertime, success, extramessage)
        except AttributeError:
            pass

    def replyC70(self, count, servertime, success):
        self.reply('C70', count, servertime, success)

    def replyC107(self, count, servertime, success, extramessage):
        self.reply('C107', count, servertime, success, extramessage)

    def stoponekeyalarm(self):
        if self.onekeyalarmed:
            self.onekeyalarmed = False
            self.send('V77')

    def stranalysis(self, data):
        result = {}
        keys = ['cji', 'count', 'servertime']
        cji = REGCJI.match(data)
        count = REGCOUNT.match(data)
        servertime = REGSERVERTIME.match(data)
        for i in keys:
            try:
                result[i] = eval(i).group(1)
            except AttributeError:
                pass
        return result

    def log(self, *args):
        message = ''.join([ctime(), ' '] + list(args))
        print message

    def send(self, vji, *args):
        if self.connect:
            output = [self.mdvrID, self.bianhao, vji, strftime('%y%m%d %H%M%S')] + self.gpsinfo + list(args)
            sendmessage = (COMMONVMESSAGE + SENDMESSAGE[vji]) % tuple(output)
            sendmessage = '%s%04d%s' % ('99dc', len(sendmessage), sendmessage)
            self.sock.send(sendmessage)
            self.bianhao += 1
            if self.bianhao > 65535:
                self.bianhao = 0
            self.log('send   :', sendmessage)
        else:
            self.log('Send %s fail!!! Please connect to server first!!!' % vji)

    def reply(self, cji, count, servertime, *args):
        output = [self.mdvrID, count, 'V0', strftime('%y%m%d %H%M%S')] + self.gpsinfo + list(args)
        sendmessage = (COMMONVMESSAGE + ('%s,%s,0,' % (cji, servertime)) + REPLYMESSAGE[cji]) % tuple(output)
        sendmessage = '%s%04d%s' % ('99dc', len(sendmessage), sendmessage)
        self.sock.send(sendmessage)
        self.log('send   :', sendmessage)

    def setgps(self, gps1='', gps2='', speed='0', direction='0'):
        if len(gps1) == 0:
            self.gpsinfo[1] = '-00000.0000'
        else:
            self.gpsinfo[1] = '%.4f' % float(gps1)
        if len(gps2) == 0:
            self.gpsinfo[2] = '-0000.0000'
        else:
            self.gpsinfo[2] = '%.4f' % float(gps2)
        self.gpsinfo[3] = '%.2f' % float(speed)
        self.gpsinfo[4] = '%.2f' % float(direction)
        self.gpsinfo[0] = 'V' if len(gps1) == 0 and len(gps2) == 0 else 'A'
