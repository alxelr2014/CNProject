import socket
import pickle
import os
import cv2
import struct

from menu import *
from video import Video

SERVER_IP = 'localhost'
SERVER_PORT = 8080

client_token = None
client_role = 'user'
client_username = None

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))


def send(message, s=sock):
    s.send(pickle.dumps(message))


def receive(s=sock):
    return pickle.loads(s.recv(2048))


def signup():
    username = input('Enter your username: ')
    password = input('Enter your password: ')
    while True:
        admin = input('Request to be an admin? (y/n): ')
        if admin in ['y', 'n']:
            break
    admin = (admin == 'y') * 1
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
        print('Logged-in successfully')
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
        request = {'type': 'upload', 'token': client_token, 'username': client_username,
                   'video-name': os.path.basename(path), 'len': len(buffer)}
        send(request)
        response = receive()
        if response['type'] == 'ok':
            sock.sendall(buffer)
            response = receive()
            if response['type'] == 'ok':
                print('Uploaded successfully')
            else:
                error = response['message']
                print(f'Error: {error}')
            # TODO: works alright?
        else:
            error = response['message']
            print(f'Error: {error}')
        # TODO: works alright?


signup_menu = Menu('Sign-up', action=signup)
login_menu = Menu('Login', action=login)
upload_menu = Menu('Upload a video', action=upload)

video_name, video_id = None, None
video: Video = None


def show_videos_menu():
    request = {'type': 'list-videos'}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        videos = response['content']
        for i, (id, name) in enumerate(videos):
            print(f'{i}. {name}')
        i = input('Enter video\'s number: ')
        if not i.isnumeric() or not 0 <= int(i) < len(videos):
            return
        i = int(i)
        id, name = videos[i]
        global video_name, video_id
        video_name, video_id = name, id
        video_menu.name = video_name
        video_menu.run()
    else:
        error = response['message']
        print(f'Error: {error}')


videos_menu = Menu('Watch Videos', action=show_videos_menu)


def get_video_and_stream(n_frame):
    stream_data = b''
    payload_size = struct.calcsize("Q")
    for i in range(n_frame):
        while len(stream_data) < payload_size:
            stream_data += sock.recv(4096)
        packed_msg_size = stream_data[:payload_size]
        stream_data = stream_data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(stream_data) < msg_size:
            stream_data += sock.recv(4096)
        frame_data = stream_data[:msg_size]
        stream_data = stream_data[msg_size:]

        frame = pickle.loads(frame_data)
        cv2.imshow(video_name, frame)
        cv2.waitKey(1)
    cv2.destroyWindow(video_name)


def watch():
    request = {'type': 'stream', 'video-id': video_id}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        get_video_and_stream(response['frame-count'])
    else:
        error = response['message']
        print(f'Error: {error}')


def show_comments():
    for username, comment in video.comments:
        print(f'"{username}":\n{comment}\n')


def show_likes():
    print(f'This video has {video.get_likes()} likes and {video.get_dislikes()} dislikes.')


def add_comment():
    comment = input('Enter your comment:\n')
    request = {'type': 'comment', 'username': client_username, 'token': client_token, 'video-id': video_id,
               'content': comment}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Comment added successfully.')
    else:
        error = response['message']
        print(f'Error: {error}')


def like():
    request = {'type': 'like', 'username': client_username, 'token': client_token, 'video-id': video_id,
               'kind': 'like'}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        pass
    else:
        error = response['message']
        print(f'Error: {error}')


def dislike():
    request = {'type': 'like', 'username': client_username, 'token': client_token, 'video-id': video_id,
               'kind': 'dislike'}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        pass
    else:
        error = response['message']
        print(f'Error: {error}')


def get_video_attrs():
    request = {'type': 'get-video', 'video-id': video_id}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        global video
        video = response['content']
    else:
        error = response['message']
        print(f'Error: {error}')


video_menu = Menu('VIDEO_NAME', parent=videos_menu, action=get_video_attrs)
watch_video_menu = Menu('Watch', action=watch, parent=video_menu)
show_comments_menu = Menu('Show comments', action=show_comments, parent=video_menu)
show_like_menu = Menu('Show likes and dislikes', action=show_likes, parent=video_menu)
add_comment_menu = Menu('Add comments', action=add_comment, parent=video_menu)
like_menu = Menu('Like', action=like, parent=video_menu)
dislike_menu = Menu('Dislike', action=dislike, parent=video_menu)
video_menu.submenus = [watch_video_menu, show_comments_menu, show_like_menu, add_comment_menu, like_menu, dislike_menu]

user_menu = Menu('Main Menu', [signup_menu, login_menu, upload_menu, videos_menu])

manager_menu = Menu('')

def run_main_menu():
    if client_role == 'user':
        user_menu.run()
    elif client_role == 'admin':
        pass
    else:
        pass


main_menu = Menu('Main Menu', action=run_main_menu)

while True:
    main_menu.run()
