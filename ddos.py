import datetime

BLOCK = False
ALLOW = True


class DDOS:
    def __init__(self, blacklist_threshold, time_interval):
        self.blacklist_threshold = blacklist_threshold
        self.time_interval = time_interval
        self.connection_log = []
        self.blacklist = []
        self.whitelist= []


    def add_to_whitelist(self,ip_address):
        self.whitelist.append(ip_address)

    def add_connection(self, ip_address):
        if ip_address in self.blacklist:
            return BLOCK
        if ip_address in self.whitelist:
            return ALLOW
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
            self.blacklist.append(ip_address)
            return BLOCK
        return ALLOW



ddos = DDOS(3,datetime.timedelta(0,10,0))


