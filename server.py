import datetime
import socket
import argparse
import pickle
import os
import sys
from threading import Thread
from handler import Handler
from ddos import DDOS

PORT = 8080
HOST = '127.0.0.1'

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=int, default=PORT, help='port number of server')
parser.add_argument('-n', '--new', action="store_true")
args = parser.parse_args()
PORT = args.port
new_handler = args.new


class Server(Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.resource_path = './resources/'
        self.handler = self._load_resources()
        self.ip_socket_dict = dict()
        self.ddos_handler = DDOS(3, datetime.timedelta(0,10,0))

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind((self.host, self.port))
            server.listen(1)
            print(f'Server is up on address {(self.host, self.port)}')
        except Exception as e:
            print(str(e))
            print(f"server couldn't connect to {(self.host, self.port)}")
            exit()

        try:
            while True:
                print('Server is listening ...')
                client, address = server.accept()
                if not self.ddos_handler.add_connection(address[0]):
                    print('your ip address blocked! ☠️')
                    self._block_ip(address[0])
                    continue
                self.ip_socket_dict[address[0]] = self.ip_socket_dict.get(address[0], []) + [client]
                print(f'Client accepted with address: {address}')
                client_thread = Thread(
                    target=self._client_handler,
                    args=(client,address,)
                )
                client_thread.start()
        except Exception as e:
            print(str(e))
            server.close()
            self.save_state()

    def _block_ip(self, ip_addr):
        for sock in self.ip_socket_dict[ip_addr]:
            sock.close()

    def _read_from(self, src):
        return pickle.loads(src.recv(2048))

    def _write_to(self, des, data):
        des.sendall(pickle.dumps(data))

    def _client_handler(self,client,address):
        while True:
            try:
                req = self._read_from(client)
                response = self.handler.process(req, client)
                self._write_to(client, response)
            except Exception as e:
                print(str(e))
                if not str(e).startswith('proxy'):
                    client.close()
                else:
                    self.ddos_handler.add_to_whitelist(address[0])
                break

    def _load_resources(self):
        if not os.path.exists(self.resource_path):
            os.makedirs(self.resource_path)

        path = self.resource_path + 'handler.pickle'
        load = False
        if new_handler:
            return Handler()
        if os.path.isfile(path):
            try:
                with open(path, 'rb') as f:
                    h = pickle.load(f)
                    print('handler loaded successfully!')
                    load = True
                    return h
            except:
                load = False

        if not load:
            h = Handler()
            with open(path, 'wb') as f:
                pickle.dump(h, f)
            return h

    def save_state(self):
        path = self.resource_path + 'handler.pickle'
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'wb') as f:
            pickle.dump(self.handler, f)
        print('handler state saved successfully!')
        sys.exit()


if __name__ == '__main__':
    server = Server(HOST, PORT)
    server.setDaemon(True)
    server.start()

    while True:
        try:
            c = input()
            if c == 'exit':
                server.save_state()
        except KeyboardInterrupt:
            server.save_state()
