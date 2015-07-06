__author__ = 'shangxc'

import unittest
import server
import mdvr
from threading import Thread
from time import sleep

class MyTestCase(unittest.TestCase):
    def test_connect(self):
        ser = Thread(target=server.main)
        ser.setDaemon(True)
        ser.start()
        mdvr1 = mdvr.MDVR('1234567890', '1234567')
        mdvr1.setDaemon(True)
        mdvr1.start()
        sleep(1)
        self.assertEqual(mdvr1.getName(), '1234567890')
        self.assertEqual(mdvr1.connect, True)
        self.assertEqual(isinstance(server.mdvrList['1234567890'],server.Client), True)
        mdvr1.onekeyalarm()
        sleep(1)
        self.assertEqual(mdvr1.onekeyalarmed, True)
        sleep(2)
        server.mdvrList['1234567890'].sendC70()
        sleep(2)
        self.assertEqual(mdvr1.onekeyalarmed, False)

        server.mdvrList['1234567890'].sendC107(1)
        sleep(2)
        self.assertEqual(len(mdvr1.trafficfenceid),1)
        self.assertEqual(mdvr1.trafficfenceid[0], '13816')

        server.mdvrList['1234567890'].sendC107(3)
        sleep(2)
        self.assertEqual(len(mdvr1.trafficfenceid),0)

        server.mdvrList['1234567890'].sendC107(1)
        sleep(1)
        mdvr1.sendV79(1, mdvr1.trafficfenceid[0], 12)
        mdvr1.sendV79(1, mdvr1.trafficfenceid[0], 13, 1)


if __name__ == '__main__':
    unittest.main()
