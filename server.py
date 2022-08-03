from socket import *
from config import SERVER_PORT,SERVER_IP
import logging
import threading
import coloredlogs
import cv2
from termcolor import colored

import pickle 
import struct
import time

def logger_config(name=None):
    """
        Setup the logging environment
    """
    if not name:
        log = logging.getLogger()  # root logger
    else:
        log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    coloredlogs.DEFAULT_FIELD_STYLES['levelname']['color'] = 'white'
    coloredlogs.install(level='INFO')
    return log


class WebServer:
    def __init__(self):
        self.maxListen = 3

        self.log = logger_config()

        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.bind((SERVER_IP, SERVER_PORT))
        self.clientSocket.listen(self.maxListen)
        self.log.info("Client socket is created.")

    def run(self):
        clientThread = threading.Thread(target=self.client_handler)
        clientThread.start()

    def client_handler(self):
        self.log.info("Client thread is running.")
        while True:
            new_client = self.clientSocket.accept()
            # creates a new thread per client
            threading.Thread(target=self.client_connected, args=(new_client,)).start()

    def client_connected(self, client: tuple[socket, any]):
        self.log.info("Client " + colored(str(client[1]), 'grey', 'on_yellow') + " connected.")
        while True: # TODO: It should be changed to while client is ALIVE
            source_msg = self.receive_from_socket(client).decode()
            self.request_handler(client,source_msg)

        client[0].close()
        self.log.info("Client " + colored(str(client[1]), 'grey', 'on_yellow') + " closed.")

    def request_handler(self,client: tuple[socket, any],request: str):
        if request=="ShowShittyVideo":
           self.stream_video(client,"videos/test.mp4") 
        return None

    def stream_video(self,client: tuple[socket, any],video_addr):
        vid = cv2.VideoCapture(video_addr)
        # player = MediaPlayer(video_addr)
        while vid.isOpened():
            img,frame = vid.read()
            # audio_frame, val = player.get_frame()

            a = pickle.dumps(frame)
            message_a = struct.pack("Q",len(a))+a
            self.send_to_socket(client,message_a)

            """b = pickle.dumps(audio_frame)
            message_b = struct.pack("Q",len(b))+b
            self.send_to_socket(client,message_b)

            c = pickle.dumps(val)
            message_c = struct.pack("Q",len(c))+c
            self.send_to_socket(client,message_c)"""
        vid.release() 
    

    def receive_from_socket(self, client: tuple[socket, any], debug=False, retry_count=0):
        # tries to receive something from the client; if debug is set, appropriate logs will be printed; retry_count determines 
        # the number of retry attempts that failed; max retry_count is 5; 
        try:
            source_msg = client[0].recv(4096)
            if debug:
                self.log.info("The message " + colored(source_msg, 'grey', 'on_yellow')
                              + " was received from " + colored(str(client[1]), 'grey', 'on_yellow'))
            return source_msg
        except OSError as e:
            if retry_count >= 5:
                self.log.warning("Was not able to receive any messages from " +
                                 colored(str(client[1]), 'grey', 'on_yellow'))
                self.log.warning(e)
                return None
            time.sleep(200)
            self.receive_from_socket(client, debug, retry_count + 1)
        return None

    def send_to_socket(self, client: tuple[socket, any], message: str, debug=False, retry_count=0):
        # tries to send something to the client; if debug is set, appropriate logs will be printed; retry_count determines 
        # the number of retry attempts that failed; max retry_count is 5; 
        try:
            client[0].sendall(message)
            if debug:
                self.log.info("The message " + colored(message, 'grey', 'on_yellow')
                              + " was sent to " + colored(str(client[1]), 'grey', 'on_yellow'))
            return True
        except OSError as e:
            if retry_count >= 5:
                self.log.warning("Was not able to send message to " + colored(str(client[1]), 'grey', 'on_yellow'))
                self.log.warning(e)
                return None
            time.sleep(200)
            self.send_to_socket(client, message, debug, retry_count + 1)
        return False

    



WebServer().run()