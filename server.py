import socket
import argparse
import json
from threading import Thread
from handler import Handler

PORT = 8080
HOST = '127.0.0.1'

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=int, default=PORT,
                    help='port number of server')
args = parser.parse_args()
PORT = args.port


class Server(Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.handler = Handler()

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

        while True:
            print('Server is listening ...')
            client, address = server.accept()
            print(f'Client accepted with address: {address}')
            client_thread = Thread(
                target=self._client_handler,
                args=(client,)
            )
            client_thread.start()

    def _client_handler(self, client):
        while True:
            try:
                req = self._read_from(client)
                response = self.handler.process(req, client)
                self._write_to(client, response)
            except Exception as e:
                print(str(e))
                client.close()
                break

    def _read_from(self, src):
        return json.dumps(src.recv(2048).decode('ascii'))
        # response = bytearray()
        # buffer = src.recv(2048)
        # while buffer:
        #     response.extend(buffer)
        #     buffer = src.recv(2048)
        # return json.loads(response.decode('ascii'))

    def _write_to(self, des, data):
        des.sendall(json.dumps(data).encode('ascii'))


if __name__ == '__main__':
    Server(HOST, PORT).start()
    # .setDaemon(True).start()
    # input()
