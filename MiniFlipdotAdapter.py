#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import threading
import Queue

from SchleuseUdpReceiver import SchleuseUdpReceiver
from FlipdotAPI.FlipdotMatrix import FlipdotMatrix

class MiniFlipdotAdapter(threading.Thread):
    def __init__(self, queue, flipdotMatrix = FlipdotMatrix()):
        threading.Thread.__init__(self)
        self.__flipdotMatrix = flipdotMatrix
        self.__oldHqStatus = None
        self.__queue = queue

    def runOnce(self):
        hqstatus = self.getHqStatusFromUberbus()
        self.showStatusTextWithoutBeginningHq(hqstatus)
        
       
    def run(self):
        while True:
            newHqStatus = self.getHqStatusFromUberbus()
            print(newHqStatus)
            if (newHqStatus != self.__oldHqStatus): 
                print "flipdot display: ", newHqStatus,  self.__oldHqStatus
            # quickfix: allways send new status, so that display get's also set when power down during status change
            if ( 1 or newHqStatus != self.__oldHqStatus): 
                self.showStatusTextWithoutBeginningHq(newHqStatus)
                self.__oldHqStatus = newHqStatus
            time.sleep(5.0)
        
    def getHqStatusFromUberbus(self):
        try:
            return self.__queue.get()
        except:
            return "No network  (FNORD)"

    def showStatusTextWithoutBeginningHq(self, hqstatus):
        hqstatus = hqstatus.split(' ')[-1]
        self.showStatusText(hqstatus) 
        
    def showStatusText(self, hqstatus):
        self.__flipdotMatrix.showText('\x01 state    ' + hqstatus, linebreak=True, xPos=2, yPos=1)
 
#main
if __name__ == "__main__":
    # SchleuseUDP receives UDP broadcast packets and delivers it to message_queue
    queue = Queue.Queue(5)

    # connect consumers with Schleuse UDP receiver
    #SchleuseUdpReceiver([queue]).start()
    # this does not work, as only one process can listen per UDP port per device

    # start adapter
    MiniFlipdotAdapter(queue).run()
