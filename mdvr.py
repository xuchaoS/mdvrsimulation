#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from socket import socket, AF_INET, SOCK_STREAM,error
from threading import Thread
from time import ctime, strftime, sleep
import re
from uuid import uuid1
import cx_Oracle
import traceback
import ConfigParser

REGCJI = re.compile(r',\w{10},[^,]*,(C\d{1,3}),.*')
REGCOUNT = re.compile(r',\w{10},([^,]*),C\d{1,3},\d+ \d+,.*')
REGSERVERTIME = re.compile(r',\w{10},[^,]*,C\d{1,3},(\d+ \d+),.*')
REGTRAFFICFENCE = re.compile(r',\w{10},[^,]*,C107,\d+ \d+,(\d*),(\d),.*')
REGSPEEDRULE = re.compile(r',\w{10},[^,]*,C68,\d+ \d+,(\d),(\d+),(\d+),(\d+)\#')
REGNORMALGPS = re.compile(r',\w{10},[^,]*,C30,\d+ \d+,(\d),(\d+),(\d+),(\d+),.*')
COMMONVMESSAGE = ',%s,%s,%s,%s,%s,%s,%s,%s,%s,8100000000000000,0000000000000000,46.00,999.00,01000000.0000,,,0,0,0,'
SENDMESSAGE = {'V1': '0.0.3.08,0101,%s:%s,0,2,,%s#',
               'V30': '%d#',
               'V61': ',,,,,,,,,,,,,,,,%d,1,1,PB1#',
               'V63': ',,,,,,,,,,,,,,,,%s,1,%s#',
               'V68': ',,,,,,,,,,,,,,,,%s,1,%d,%.2f,%.2f,%.2f,1,%d,0.00,99.99#',
               'V69': ',,,,,,,,,,,,,,,,%s,1,1,%s,%s#',
               'V70': ',,,,,,,,,,,,,,,,%s,1,%.2f,%.2f,%.2f,%d,1,1,0.00,199.99#',
               'V75': ',,,,,,,,,,,,,,,,%s,1,%d,%s,%s,%s#,',
               'V79': ',,,,,,,,,,,,,,,,%s,1,1,%d,%s,,,%d,%d%s#',
               'V77': '02000000,,#',
               'V78': ',,,,,,,,,,,,,,,,%s,1,%d,%d,%d,1,%d,10,360#',
               'V600': '''3,1,1327,1327,<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<MDVRBus version="1.0">
    <CheckInfo UNIT_ID="%s" _TIME_="%s" _ZONE_="+8">
        <InfoClass _TYPE_="InspectInfo">
            <InfoList>
                <_INFO_ _NAME_="_SN_" _STAT_="%s" />
                <_INFO_ _NAME_="_TIME_" _STAT_="%s" />
                <_INFO_ _NAME_="RecSD" _STAT_="E" />
                <_INFO_ _NAME_="GPSINFO" _STAT_="%s" />
                <_INFO_ _NAME_="Sensor1" _STAT_="OK" />
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
                'C68': '%s,%s,,#',
                'C30': '%s,%s,,#',
                'C107': '%s,1%s#'}
ERRORCODE = {'00030011': 'area limited by adding',
             '00030012': 'area existing by adding',
             '00030021': 'not exist by modifying',
             '00030031': 'not exist by deleting'}
STORAGEERRORCODE = {'00000001': 'storage not exist',
                    '00000002': 'storage cannot record',
                    '00000003': 'storage space filled',
                    '00000004': 'storage is not formated',
                    '00000005': 'storage read or write abnormal'}

mdvrList = {}


class MDVR(object):
    def __init__(self, mdvrid, carid, ip='127.0.0.1', port=9876, gps1='', gps2='', speed='0', direction='0'):
        super(MDVR, self).__init__()
        self.config = ConfigParser.ConfigParser()
        self.ip = ip
        self.port = port
        self.mdvrID = mdvrid
        self.carID = carid
        self.config.read("etc/%s_config.ini" % (self.mdvrID))
        self.gpsinfo = ['V', gps1, gps2, speed, direction]
        self.setgps(gps1, gps2, speed, direction)
        self.bianhao = 0
        self.connect = False
        self.onekeyalarmed = False
        self.onekeyalarmtimes = 0
        mdvrList[self.mdvrID] = self
        self.trafficfenceid = []
        self.speedrule = (False, 0, 0, 0)
        try:
            # for i in self.config.options('trafficfenceid'):
            #     self.trafficfenceid.append(self.config.get('trafficfenceid', i))
            self.trafficfenceid = [self.config.get('trafficfenceid', i) for i in self.config.options('trafficfenceid')]
            self.speedrule = (self.config.getboolean('speedrule', 'speedrule0'), self.config.getfloat('speedrule', 'speedrule1'), self.config.getfloat('speedrule', 'speedrule2'), self.config.getfloat('speedrule', 'speedrule3'))
        except ConfigParser.NoSectionError:
            pass
        self.sendnormalgpsd = False
        self.lastreceive = ''


    def start(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.sock.connect((self.ip, self.port))
        except error:
            self.log('Connect fail!!!')
            return -1
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
        self.onekeyalarmed = False
        self.sock.close()
        if 'trafficfenceid' not in self.config.sections():
            self.config.add_section('trafficfenceid')
        if 'speedrule' not in self.config.sections():
            self.config.add_section('speedrule')
        for i in range(len(self.trafficfenceid)):
            self.config.set('trafficfenceid', 'trafficfenceid%d' % i, self.trafficfenceid[i])
        for i in range(len(self.speedrule)):
            self.config.set('speedrule', 'speedrule%d' % i, self.speedrule[i])
        # self.config.set('CONFIG', 'trafficfenceid', self.trafficfenceid)
        # self.config.set('CONFIG', 'speedrule', self.speedrule)
        f = open("etc/%s_config.ini" % (self.mdvrID), "w+")
        self.config.write(f)
        f.close()

    def __del__(self):
        self.stop()

    def sendselfcheck(self):
        currenttime = strftime('%Y/%m/%d %H:%M:%S %a').upper()
        self.send('V600', self.mdvrID, currenttime, self.mdvrID, currenttime, self.gpsinfo[0])

    def sendonekeyalarm(self):
        self.send('V61', self.onekeyalarmtimes)
        self.onekeyalarmtimes += 1

    def sendV63(self, video):
        if video == (False, False, False, False) or len(video) != 4:
            return -1
        else:
            tmp = 0
            for i in range(4):
                if video[i]:
                    tmp += 2 ** i
            extmsg = ('%02x' % tmp).upper() + '00'
            self.send('V63', uuid1(), extmsg)

    def sendV75(self, alerttype=2, historytime='', historygps1='', historygps2=''):
        if alerttype == 0:
            self.send('V75', uuid1(), alerttype, '', '', '')
        else:
            self.send('V75', uuid1(), alerttype, historytime, '%.4f' % float(historygps1), '%.4f' % float(historygps2))

    def sendV79(self, inout, trafficfenceid, subtype,
                speedoverlower=None, minspeed=0, maxspeed=0, duringtime=0, alarmminspeed=0, alarmmaxspeed=0):
        parameternum = 0
        substr = ''
        if subtype == 12:
            inout = 1
        elif subtype == 13:
            parameternum = 7
            substr = ',%s,%.2f,%.2f,%s,%d,%.2f,%.2f' % (speedoverlower, float(minspeed), float(maxspeed), self.gpsinfo[3], int(duringtime), float(alarmminspeed), float(alarmmaxspeed))
        self.send('V79', uuid1(), inout, trafficfenceid, subtype, parameternum, substr)

    def sendgps(self, gpstype):
        self.send('V30', gpstype)

    def sendV70(self, speedmin, speedmax, duringtime):
        self.send('V70', uuid1(), float(self.gpsinfo[3]), float(speedmin), float(speedmax), int(duringtime))

    def sendV68(self, temperaturetype, currenttemperature, mintemperature, maxtemperature, alerttype):
        self.send('V68', uuid1(), int(temperaturetype), float(currenttemperature), float(mintemperature), float(maxtemperature), int(alerttype))

    def sendV69(self, errorcode):
        if len(errorcode) > 0:
            errmsg = '|'.join([STORAGEERRORCODE[i] for i in errorcode])
            errcode = '|'.join(errorcode)
            self.send('V69', uuid1(), errcode, errmsg)

    def sendV78(self, currentvoltage, minvoltage, maxvoltage, alerttype):
        self.send('V78', uuid1(), int(currentvoltage), int(minvoltage), int(maxvoltage), int(alerttype))

    def _onekeyalarm(self):
        self.sendonekeyalarm()
        if not self.onekeyalarmed:
            self.onekeyalarmed = True
            for i in xrange(2400):
                if self.onekeyalarmed and self.connect:
                    self.sendgps(4)
                    sleep(1)
                else:
                    break

    def onekeyalarm(self):
        oka = Thread(target=self._onekeyalarm)
        oka.setDaemon(True)
        oka.start()

    def receive(self):
        while self.connect:
            rec1 = self.sock.recv(4)
            if rec1 == '90dc':
                self.log('receive:', rec1)
            elif rec1 == '99dc':
                rec2 = self.sock.recv(4)
                leaveLen = int(rec2)
                rec3 = self.sock.recv(leaveLen)
                self.log('receive:', rec1, rec2, rec3)
                self.lastreceive = rec1 + rec2 + rec3
                tmp = Thread(target=self.dataanalysis, args=(rec3,))
                tmp.start()

    def dataanalysis(self, data):
        analysised = self.stranalysis(data)
        try:
            servertime = analysised['servertime']
            count = analysised['count']
        except KeyError, e:
            print 'KeyError:', e.message
        else:
            try:
                cji = analysised['cji']
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
                elif cji == 'C68':
                    self.analysisC68(data, count, servertime)
                elif cji == 'C30':
                    self.analysisC30(data, count, servertime)

    def analysisC30(self, data, count, servertime):
        try:
            normalgps = REGNORMALGPS.match(data)
            #self.replyC30(count, servertime, '1', normalgps.group(1))
            if normalgps.group(1) == '1' and self.sendnormalgpsd == False:
                tmp = Thread(target=self.sendnormalgps, args=(normalgps.group(3), normalgps.group(4)))
                tmp.setDaemon(True)
                tmp.start()
                self.sendnormalgpsd = True
            self.replyC30(count, servertime, '1', normalgps.group(1))
        except AttributeError:
            pass

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

    def analysisC68(self, data, count, servertime):
        try:
            speedrule = REGSPEEDRULE.match(data)
            if speedrule.group(1) == '0':
                self.speedrule = (False, 0, 0, 0)
            elif speedrule.group(1) == '1':
                self.speedrule = (True, int(speedrule.group(2)), int(speedrule.group(3)), int(speedrule.group(4)))
            self.replyC68(count, servertime, '1', speedrule.group(1))
        except AttributeError:
            pass

    def replyC68(self, count, servertime, success, onoff):
        self.reply('C68', count, servertime, success, onoff)

    def replyC30(self, count, servertime, success, onoff):
        self.reply('C30', count, servertime, success, onoff)

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
        message = ''.join([ctime(), ' '] + list(args) + ['\n'])
        print message,

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

    def insertvideotodatabase(self, databaseip, instancename, username='vms', password='vms'):
        try:
            conn = cx_Oracle.connect('%s/%s@%s/%s' % (username, password, databaseip, instancename))
            cursor = conn.cursor()
            cursor.execute('''select video_file from vms.ALARM_VIDEO''')
            filename = cursor.fetchone()[0]
            cursor.execute('''insert into vms.ALARM_VIDEO
            (uuid, mdvr_id, channel_id, stream_id, alarm_id, start_time, end_time, video_size, video_file)
            values('%s', '%s', 0, 2, '%s', to_date('%s','yyyymmddhh24miss'), to_date('%s','yyyymmddhh24miss'), 10240, '%s')'''
                           % (uuid1(), self.mdvrID, self.onekeyalarmtimes, strftime('%Y%m%d%H%M%S'), strftime('%Y%m%d%H%M%S'), filename))
            conn.commit()
            conn.close()
            self.log('Insert video file to database, filename is: %s' % filename)
            return filename
        except cx_Oracle.DatabaseError, e:
            traceback.print_exc()
            raise

    def sendnormalgps(self, delay, count):
        for i in range(int(count)):
            self.sendgps(0)
            sleep(int(delay))
        self.sendnormalgpsd = False