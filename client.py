import socket
import pickle
import cv2
import struct

from menu import *
from video import Video

SERVER_IP = 'localhost'
SERVER_PORT = 8080
PROXY_IP = 'localhost'
PROXY_PORT = 8585

client_token = None
client_role = 'user'
client_username = None

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.connect((SERVER_IP, SERVER_PORT))

proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_sock.connect((PROXY_IP, PROXY_PORT))

main_socket = server_sock


def send(message):
    main_socket.send(pickle.dumps(message))


def receive():
    return pickle.loads(main_socket.recv(2048))


def already_signed():
    if client_token:
        print('You are already signed-in.')
        while True:
            out = input('Do you want to sign out? (y/n): ')
            if out in ['y', 'n']:
                break
        if out == 'y':
            signout()
            main_menu.run()
        return True
    return False


def signup():
    if already_signed():
        return
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


def signout():
    global client_token, client_role, client_username, main_socket
    client_token = None
    client_role = 'user'
    client_username = None
    main_socket = server_sock
    video_menu.submenus = [watch_video_menu, show_comments_menu, show_like_menu, add_comment_menu, like_menu,
                           dislike_menu]
    main_menu.run()


def login():
    if already_signed():
        return
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
        if error == 'use proxy server':
            global main_socket
            main_socket = proxy_sock
            send(request)
            response = receive()
            if response['type'] == 'ok':
                client_token = response['token']
                client_role = response['role']
                client_username = username
                print('Logged-in successfully')
                video_menu.submenus = [watch_video_menu, show_comments_menu, show_like_menu, restrict_menu, block_menu]
            else:
                error = response['message']
                main_socket = server_sock
                print(f'Error: {error}')
        else:
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
            main_socket.sendall(buffer)
            response = receive()
            if response['type'] == 'ok':
                print('Uploaded successfully')
            else:
                error = response['message']
                print(f'Error: {error}')
        else:
            error = response['message']
            print(f'Error: {error}')


signout_menu = Menu('Sign-out', action=signout)
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
            stream_data += main_socket.recv(4096)
        packed_msg_size = stream_data[:payload_size]
        stream_data = stream_data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(stream_data) < msg_size:
            stream_data += main_socket.recv(4096)
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
        if video._restricted:
            video_menu.name = f'{video.name}\n☠️Attention: this video may be inappropriate for some users ☠️'
        else:
            video_menu.name = video.name
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


def process_admin(username, state):
    if state != 'pending':
        return
    while True:
        admin = input('Accept admin? (y/n): ')
        if admin in ['y', 'n']:
            break
    if admin == 'y':
        request = {'type': 'accept', 'token': client_token, 'admin-username': username}
    else:
        request = {'type': 'reject', 'token': client_token, 'admin-username': username}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print(f'{"Accepted" if admin == "y" else "Rejected"} request successfully.')
    else:
        error = response['message']
        print(f'Error: {error}')


def show_admin_requests():
    request = {'type': 'list-admins', 'token': client_token}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        admins = response['content']
        admins_requests_menu.submenus = [
            Menu(f'{admin}: {state}', action=lambda: process_admin(admin, state), parent=admins_requests_menu)
            for admin, state in admins]
    else:
        error = response['message']
        print(f'Error: {error}')


def add_restricted_tag():
    request = {'type': 'restrict', 'video-id': video_id, 'token': client_token}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Restricted successfully.')
    else:
        error = response['message']
        print(f'Error: {error}')


def unstrike_user(user):
    request = {'type': 'unstrike', 'username': user, 'token': client_token}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Restricted successfully.')
    else:
        error = response['message']
        print(f'Error: {error}')


def block_video():
    request = {'type': 'block', 'video-id': video_id, 'token': client_token}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Blocked successfully.')
        videos_menu.run()
    else:
        error = response['message']
        print(f'Error: {error}')
        video_menu.run()


def unstrike():
    request = {'type': 'list-strike', 'token': client_token}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        striked_users = response['content']
        unstrike_menu.submenus = [Menu(user, action=lambda: unstrike_user(user), parent=unstrike_menu)
                                  for user in striked_users]
    else:
        error = response['message']
        print(f'Error: {error}')


block_menu = Menu('Block Video', action=block_video)
restrict_menu = Menu('Restrict Video', action=add_restricted_tag, parent=video_menu)
unstrike_menu = Menu('Un-strike users', action=unstrike)
admin_menu = Menu('Admin Menu', [signout_menu, videos_menu, unstrike_menu])

admins_requests_menu = Menu('See admin requests', action=show_admin_requests)
manager_menu = Menu('Manager Menu', [signout_menu, admins_requests_menu])
admins_requests_menu.parent = manager_menu


def run_main_menu():
    if client_role == 'user':
        user_menu.run()
    elif client_role == 'admin':
        admin_menu.run()
    else:
        manager_menu.run()


main_menu = Menu('Main Menu', action=run_main_menu)

while True:
    main_menu.run()
