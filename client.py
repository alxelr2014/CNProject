import socket
import json
import os

from menu import *

SERVER_IP = 'localhost'
SERVER_PORT = 8080

client_token = None
client_role = 'user'
client_username = None

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
    request = {'type': 'register', 'username': username, 'password': password, 'admin': admin}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Registered successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def login():
    username = input('Enter your username: ')
    password = input('Enter your password: ')
    request = {'type': 'login', 'username': username, 'password': password}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        global client_token, client_role, client_username
        client_token = response['token']
        client_role = response['role']
        client_username = username
    else:
        error = response['message']
        print(f'Error: {error}')


def upload():
    if client_token is None:
        print('You need to login in order to upload a video.')
        return
    path = input('Enter path to the video:\n')
    with open(path, "rb") as video:
        buffer = video.read()
        request = {'type': 'upload', 'token': client_token, 'username': client_username, 'name': os.path.basename(path),
                   'len': len(buffer)}
        send(request)
        response = receive()
        if response['type'] == 'ok':
            sock.sendall(buffer)
        else:
            error = response['message']
            print(f'Error: {error}')
        # TODO: works alright?


signup_menu = Menu('Sign-up', action=signup)
login_menu = Menu('Login', action=login)
upload_menu = Menu('Upload a video', action=upload)


def show_videos_menu():
    pass
    # TODO: get videos list


videos_menu = Menu('Watch Videos', action=show_videos_menu)


def watch():
    pass


def show_comments():
    pass


def show_likes():
    pass


def add_comment():
    pass


def like():
    pass


def dislike():
    pass


video_menu = Menu('VIDEO_NAME', parent=videos_menu)
watch_video_menu = Menu('Watch', action=watch, parent=video_menu)
show_comments_menu = Menu('Show comments', action=show_comments, parent=video_menu)
show_like_menu = Menu('Show likes and dislikes', action=show_likes, parent=video_menu)
add_comment_menu = Menu('Add comments', action=add_comment, parent=video_menu)
like_menu = Menu('Like', action=like, parent=video_menu)
dislike_menu = Menu('Dislike', action=dislike, parent=video_menu)
video_menu.submenus = [watch_video_menu, show_comments, show_like_menu, add_comment_menu, like_menu, dislike_menu]

user_menu = Menu('Main Menu', [signup_menu, login_menu, upload_menu, videos_menu])

main_menu = Menu('Main Menu')

while True:
    main_menu.run()
