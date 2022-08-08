from threading import Thread
import datetime
import telnetlib
from time import sleep

BLOCK = -1
ALLOW = 1

class DDOS:
    def __init__(self,blacklist_threshold, time_interval):
        self.blacklist_threshold = blacklist_threshold
        self.time_interval = time_interval
        self.connection_log = []
        self.blacklist = []



    def add_connection(self, ip_address):
        if ip_address in self.blacklist:
            return BLOCK
        # removes the expired connections
        while len(self.connection_log) > 0 and datetime.datetime.now() - self.connection_log[0]['time'] > self.time_interval:
            self.connection_log.pop(0)

        # adds the new connection
        self.connection_log.append({'ip':ip_address, 'time':datetime.datetime.now()})

        # checks for threshold
        count = 0
        for connection in self.connection_log:
            if connection['ip'] == ip_address:
                count += 1
        
        if count >= self.blacklist_threshold:
            return BLOCK
        return ALLOW



ddos = DDOS(3,datetime.timedelta(0,10,0),1,'facebook.com',8080)


