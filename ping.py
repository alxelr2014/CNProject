from threading import Thread
import telnetlib
import time
import server

def ping(server_ip, server_port, ping_threshold):
    while True:
        try:
            start = time.time()
            with telnetlib.Telnet(server_ip, server_port) as tn:
                end = time.time()
                if end - start > ping_threshold:
                    print("The server is busy, the rtt is ", end - start)
                else:
                    print("The server is free, the rtt is ", end - start)
                tn.close()
        except Exception:
            print("The server is not available.")
        
        time.sleep(0.5)

ping(server.HOST,server.PORT,1.5)


