from menu import *
import socket
import cv2
import pickle
import struct
from ffpyplayer.player import MediaPlayer
from config import SERVER_IP,SERVER_PORT


def make_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    return s


def login():
    username = input("Enter username: ")
    password = input("\nEnter password: ")


def signup():
    username = input("Enter username: ")
    password = input("\nEnter password: ")
    is_admin = input("\nAre you an admin?")



def search():
    pass

login_menu = Menu("login_menu",None,login)
signup_menu = Menu("Signup_menu",None,signup)
search_menu = Menu("Search",None,search)


main_menu = Menu("main_menu",[login_menu,signup_menu,search_menu])


def get_packet(server_socket: socket, stream_data):
    
    payload_size = struct.calcsize("Q") 
    while len(stream_data) < payload_size:
        stream_data += server_socket.recv(4096)
    packed_msg_size = stream_data[:payload_size]
    stream_data = stream_data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]
    while len(stream_data) < msg_size:
        stream_data += server_socket.recv(4096)
    received_data = stream_data[:msg_size]
    stream_data = stream_data[msg_size:]
    return received_data, stream_data

def test_watching_video():
    my_socket = make_connection()
    my_socket.sendall("ShowShittyVideo".encode())
    flag = True
    stream_data = b''
    while True:
        frame_data,stream_data = get_packet(my_socket,stream_data)
        #audio_data,stream_data = get_packet(my_socket,stream_data)
        #val_data,stream_data = get_packet(my_socket,stream_data)

        frame=pickle.loads(frame_data)
        #audio_frame=pickle.loads(audio_data)
        #val=pickle.loads(val_data)
        cv2.imshow("Video", frame)
        #if val != 'eof' and audio_frame is not None:
            #audio
        #    img, t = audio_frame
        cv2.waitKey(1)


test_watching_video()