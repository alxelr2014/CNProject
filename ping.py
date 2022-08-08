from threading import Thread
import telnetlib
import time

class Ping:
    def __init__(self, server_ip,server_port,ping_threshold=0):

        ping_thread = Thread(
                    target=self.ping,
                    args=(server_ip,server_port,ping_threshold))
        ping_thread.start()



    def ping(self,server_ip,server_port,ping_threshold):
        n = 10
        while n:
            n-=1
            try:
                start = time.time()
                with telnetlib.Telnet(server_ip,server_port) as tn:
                    end = time.time()
                    if end-start > ping_threshold:
                        print("ali gir nade! ",end-start)
                        pass
                    else:
                        print('hi')
                    tn.close()
            except Exception:
                print("bye")
                pass
           
            time.sleep(0.5)


ddos = Ping('127.0.0.1',8080)


