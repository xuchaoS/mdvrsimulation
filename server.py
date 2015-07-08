#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'
from socket import socket, AF_INET, SOCK_STREAM, error
from threading import Thread
from time import ctime, strftime
import re

HOST = ''
PORT = 9876
ADDR = (HOST, PORT)
REGMDVRID = re.compile(r',(\w{10}),.*')
REGVJI = re.compile(r',\w{10},[^,]*,(V\d{1,3}),.*')
REGCARID = re.compile(r',.*,(\w{1,10})#')
REGMDVRTIME = re.compile(r',\w{10},[^,]*,V\d{1,3},(\d+ \d+),.*')
REGCOUNT = re.compile(r',\w{10},([^,]*),V\d{1,3},\d+ \d+,.*')
REPLYMESSAGE = {'V1': ',%s,%s,C0,%s,V1,%s,0,%s,#',
                'V77': ',%s,%s,C0,%s,V77,%s,0,#',
               'V600': ''',%s,%s,C0,%s,V600,%s,0,0,0,3,%s,,,<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<MDVRBus version="120825">
<CheckInfo UNIT_ID="%s" _TIME_="2012/04/01 16:10:43 SUN" _ZONE_="+8">
<InfoClass _TYPE_="InspectInfo">
<InfoList>
<_INFO_ _NAME_="InspectResult" _STAT_="pass" />
</InfoList>
</InfoClass>
</CheckInfo>
</MDVRBus>,,#'''}
mdvrList = {}


class Client(Thread):
    def __init__(self, tcpclisock, addr):
        Thread.__init__(self)
        self.tcpCliSock = tcpclisock
        self.addr = addr
        self.mdvrID = ''
        self.carID = ''

    def run(self):
        tmp = Thread(target=self.receive)
        tmp.start()

    def __str__(self):
        return 'MDVRID:%s  CARID:%s  IP:%s  PORT:%d' % (self.mdvrID, self.carID, str(self.addr[0]),  self.addr[1])

    def receive(self):
        try:
            while True:
                rec1 = self.tcpCliSock.recv(4)
                if rec1 == '90dc':
                    self.log('receive:', rec1)
                    self.tcpCliSock.send('90dc')
                    self.log('send   :', '90dc')
                elif rec1 == '99dc':
                    rec2 = self.tcpCliSock.recv(4)
                    leaveLen = int(rec2)
                    rec3 = self.tcpCliSock.recv(leaveLen)
                    self.log('receive:', rec1, rec2, rec3)
                    tmp = Thread(target=self.dataanalysis, args=(rec3,))
                    tmp.start()
        except error:
            del mdvrList[self.mdvrID]
            self.log('Delete MDVR: ',self.mdvrID)

    def send(self, cji, *args):
        if cji == 'C0':
            output = list(args[1:])
            output.insert(0, self.mdvrID)
            output.insert(2, strftime('%y%m%d %H%M%S'))
            output = tuple(output)
            sendmessage = REPLYMESSAGE[args[0]] % output
            sendmessage = '%s%04d%s' % ('99dc', len(sendmessage), sendmessage)
            self.tcpCliSock.send(sendmessage)
            self.log('send   :',sendmessage)
        else:
            pass

    def log(self, *args):
        message = ''.join(['server', ctime(), ' '] + list(args) + ['\n'])
        print message

    def dataanalysis(self, data):
        analysised = self.stranalysis(data)
        try:
            mdvrtime = analysised['mdvrtime']
            count = analysised['count']
            # print 'mdvrtime and count'
        except KeyError, e:
            print 'KeyError:',e.message
        else:
            try:
                vji = analysised['vji']
                # print 'vji'
            except KeyError, e:
                print 'KeyError:',e.message
            else:
                if vji == 'V0':
                    pass
                elif vji == 'V1':
                    try:
                        self.mdvrID = analysised['mdvrid']
                        self.carID = analysised['carid']
                        # print 'mdvrid and carid'
                    except KeyError, e:
                        print 'KeyError:',e.message
                    else:
                        self.setName(self.mdvrID)
                        mdvrList[self.mdvrID] = self
                        self.log('Add to List: ', self.mdvrID)
                        self.send('C0', vji, count, mdvrtime, 1)
                elif vji == 'V600':
                    self.send('C0', vji, count, mdvrtime, 1, self.mdvrID)
                elif vji == 'V77':
                    self.send('C0', vji, count, mdvrtime)

    def stranalysis(self,data):
        result = {}
        keys = ['vji', 'count', 'mdvrtime', 'mdvrid', 'carid']
        vji = REGVJI.match(data)
        count = REGCOUNT.match(data)
        mdvrtime = REGMDVRTIME.match(data)
        mdvrid = REGMDVRID.match(data)
        carid = REGCARID.match(data)
        for i in keys:
            try:
                result[i] = eval(i).group(1)
            except AttributeError:
                pass
        return result

    def sendC70(self):
        self.tcpCliSock.send('99dc0044,%s,,C70,%s,02000000,,,0#' % (self.mdvrID, strftime('%y%m%d %H%M%S')))

    def sendC107(self, type):
        self.tcpCliSock.send('99dc0180,%s,13816:0,C107,%s,13816,%d,41,,00:00-23:59,1,1,1,W06751.1136N00935.7794W06303.8070N01001.7445W06245.1065N00822.7371W06542.7607N00555.1518W06751.1136N00935.7794#' % (self.mdvrID, strftime('%y%m%d %H%M%S'), type))

    def sendC30(self):
        self.tcpCliSock.send('99dc0053,%s,16297,C30,%s,1,50,20,121,0003#' % (self.mdvrID, strftime('%y%m%d %H%M%S')))


def main():
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(ADDR)
    server.listen(5)
    try:
        while True:
            tcpCliSock, addr = server.accept()
            tmp = Client(tcpCliSock,addr)
            tmp.run()
    except KeyboardInterrupt:
        server.close()

if __name__ == '__main__':
    main()
