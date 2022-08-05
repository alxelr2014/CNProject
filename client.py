import socket
import json

from menu import *

SERVER_IP = 'localhost'
SERVER_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))


def send(message, s=sock):
    s.send(json.dumps(message).encode('ascii'))


def receive(s=sock):
    return json.loads(s.recv(1024).decode('ascii'))


def signup():
    username = input('Enter your username: ')
    password = input('Enter your password: ')
    while True:
        admin = input('Request to be an admin? (y/n): ')
        if admin in ['y', 'n']:
            break
    admin = admin == 'y'
    request = {'type': 'register', 'username':username, 'password': password, 'admin': admin}
    send(request)


def login():
    username = input('Enter your username: ')
    password = input('Enter your password: ')
    request = {'type': 'login', 'username': username, 'password': password}
    send(request)


def upload():
    # TODO: is registered?
    path = input('Enter path to the video:\n')
    # TODO


signup_menu = Menu('Sign-up', action=signup)
login_menu = Menu('Login', action=login)
upload_menu = Menu('Upload a video', action=upload)
videos_menu = Menu('Watch Videos', [])

user_menu = Menu('Main Menu', [signup_menu, login_menu, upload_menu, videos_menu])

main_menu = Menu("main_menu")
