import socket
import argparse
import pickle
import string
import sys
from threading import Thread, Lock

import numpy as np

PORT = 8585
SERVER_PORT = 8080
HOST = '127.0.0.1'

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=int, default=PORT,
                    help='port number of server')
args = parser.parse_args()
PORT = args.port


class Proxy(Thread):
    def __init__(self, host, port, server_host, server_port):
        super().__init__()
        self.host = host
        self.port = port
        self.server_host = server_host
        self.server_port = server_port
        self._control_sock = None
        self._users = []
        self._tokens = []
        self._lock = Lock()

    def _connect_for_control(self, host, port):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((host, port))

            identification = {'type': 'proxy', 'message': 'hi this is me!'}
            self._write_to(server, identification)
            msg = self._read_from(server)
            if msg['type'] != 'ok':
                raise Exception("can't connect")
            self._proxy_token = msg['token']
            thread = Thread(target=self._handle_server, args=(server,))
            thread.start()
            return server
        except Exception as e:
            print(str(e))
            sys.exit()

    def _handle_server(self, server):
        while True:
            try:
                req = self._read_from(server)
                if req['type'] == 'add-admin':
                    self._users.append((req['username'], req['password']))
                    response = {'type': 'ok'}
                else:
                    response = {'type': 'error', 'message': 'not supported type!'}
                self._write_to(server, response)
            except Exception as e:
                print(str(e))
                break

    def run(self):
        self._control_sock = self._connect_for_control(self.server_host, self.server_port)
        proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            proxy.bind((self.host, self.port))
            proxy.listen(1)
            print(f'proxy is up on address {(self.host, self.port)}')
        except Exception as e:
            print(str(e))
            print(f"proxy couldn't connect to {(self.host, self.port)}")
            exit()

        try:
            while True:
                print('proxy is listening ...')
                client, address = proxy.accept()
                print(f'Client accepted with address: {address}')
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect((self.server_host, self.server_port))
                client_thread = Thread(
                    target=self._client_handler,
                    args=(client, server,)
                )
                client_thread.start()
        except Exception as e:
            print(f'Inja: {str(e)}')
            server.close()
            # self.save_state()

    def _read_from(self, src):
        return pickle.loads(src.recv(2048))

    def _write_to(self, des, data):
        des.sendall(pickle.dumps(data))

    def _login(self, username, password):
        for user, passw in self._users:
            if user == username:
                if passw == password:
                    return True
                else:
                    return False
        return False

    def _generate_token(self):
        size = 48
        source = list(string.ascii_letters + string.digits)
        token = ''.join(np.random.choice(source, replace=True, size=size))
        print(token)
        return token

    def _transport_to_server(self, server, client):
        while True:
            try:
                raw_req = client.recv(2048)
                req = pickle.loads(raw_req)
                print(req)
                if req['type'] == 'login':
                    if self._login(req['username'], req['password']):
                        token = self._generate_token()
                        self._lock.acquire()
                        self._tokens.append(token)
                        self._lock.release()
                        response = {'type': 'ok', 'token': token, 'role': 'admin'}
                    else:
                        response = {'type': 'error', 'message': 'username or password is wrong!'}
                    self._write_to(client, response)
                else:
                    if 'token' in req:
                        if req['token'] in self._tokens:
                            req['token'] = self._proxy_token
                            self._write_to(server, req)
                        else:
                            response = {'type': 'error', 'message': 'access denied!'}
                            self._write_to(client, response)
                    else:
                        self._write_to(server, req)
            except KeyError as e:
                response = {'type': 'error', 'message': f'request object has no {str(e)}'}
                self._write_to(client, response)
            except pickle.PickleError as e:
                server.sendall(raw_req)
            except Exception as e:
                print(str(e))
                client.close()
                server.close()
                break

    def _transport_to_client(self, client, server):
        while True:
            try:
                req = server.recv(2048)
                client.sendall(req)
            except Exception as e:
                print(str(e))
                break

    def _client_handler(self, client, server):

        client_to_server = Thread(target=self._transport_to_server, args=(server, client,))
        server_to_client = Thread(target=self._transport_to_client, args=(client, server,))

        client_to_server.start()
        server_to_client.start()


if __name__ == '__main__':
    proxy = Proxy(HOST, PORT, HOST, SERVER_PORT)
    proxy.setDaemon(True)
    proxy.start()

    while True:
        try:
            c = input()
            if c == 'exit':
                # proxy.save_state()
                exit()
        except KeyboardInterrupt:
            # proxy.save_state()
            exit()
