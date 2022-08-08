from threading import Thread
import telnetlib
import time
from xmlrpc.client import Server
import server
class Ping:
    def __init__(self, server_ip,server_port,ping_threshold=0):

        ping_thread = Thread(
                    target=self.ping,
                    args=(server_ip,server_port,ping_threshold))
        ping_thread.start()



    def ping(self,server_ip,server_port,ping_threshold):
        n = 10
        while n > 0:
            n-=1
            try:
                start = time.time()
                with telnetlib.Telnet(server_ip,server_port) as tn:
                    end = time.time()
                    if end-start > ping_threshold:
                        print("The server is busy, the rtt is ",end-start)
                    else:
                        print("The server is free, the rtt is ",end-start)
                    tn.close()
            except Exception:
                print("The server is not available.")
           
            # time.sleep(0.5)


ddos = Ping(server.HOST,server.PORT,1.5)


