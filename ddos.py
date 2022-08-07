from dataclasses import dataclass
from http import server
from sqlite3 import connect
from threading import Thread
import datetime
import subprocess
import re
from time import sleep

BLOCK = -1
ALLOW = 1

class DDOS:
    def __init__(self,blacklist_threshold, time_interval,ping_threshold, server_ip):
        self.blacklist_threshold = blacklist_threshold
        self.time_interval = time_interval
        self.connection_log = []
        self.blacklist = []
        ping_thread = Thread(
                    target=self.ping,
                    args=(ping_threshold,server_ip))
        ping_thread.start()


    def add_connection(self, ip_address):
        if ip_address in self.blacklist:
            return BLOCK
        # removes the expired connections
        while len(self.connection_log)> 0 and datetime.datetime.now() - self.connection_log[0]['time'] > self.time_interval:
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


    def ping(self,ping_threshold,server_ip):
        return 
        while True:
            p = subprocess.check_output("ping -n 1 " + server_ip)
            timestr = re.compile("time=[0-9]+ms").findall(str(p))
            rtt = int(timestr[0][5:-2])
            if rtt > ping_threshold:
                pass
            sleep(0.5)


# ddos = DDOS(3,datetime.timedelta(0,10,0),1,'google.com')
# print(ddos.add_connection('192.168.9.1'))
# print(ddos.add_connection('192.168.9.2'))
# print(ddos.add_connection('192.168.9.1'))
# print(ddos.add_connection('192.168.9.2'))
# print(ddos.add_connection('192.168.9.3'))
# print(ddos.add_connection('192.168.9.3'))
# print(ddos.add_connection('192.168.9.1'))
# print(ddos.add_connection('192.168.9.4'))
# print(ddos.add_connection('192.168.9.4'))
# print(ddos.add_connection('192.168.9.1'))

