import copy
import socket
import pickle
import cv2
import struct

from menu import *
from video import Video
from ticket import TicketState

SERVER_IP = 'localhost'
SERVER_PORT = 8080
PROXY_IP = 'localhost'
PROXY_PORT = 8585

client_token = None
client_role = 'user'
client_username = None

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.connect((SERVER_IP, SERVER_PORT))

main_socket = server_sock


def send(message):
    main_socket.send(pickle.dumps(message))


def receive():
    return pickle.loads(main_socket.recv(2048))


def already_signed(proxy=False):
    cond = client_token if proxy else client_token and client_username
    if cond:
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
    global client_token
    if client_token:
        request['token'] = client_token
    send(request)
    response = receive()
    if response['type'] == 'ok':
        global client_role, client_username
        client_role = response['role']
        if client_role == 'admin':
            video_menu.submenus = [watch_video_menu, show_comments_menu, show_like_menu, restrict_menu, block_menu]
        else:
            client_token = response['token']
        client_username = username
        print('Logged-in successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def login_proxy():
    if already_signed(True):
        return
    global main_socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.connect((PROXY_IP, PROXY_PORT))
    main_socket = proxy_socket
    username = input('Enter your proxy username: ')
    password = input('Enter your proxy password: ')
    request = {'type': 'login-proxy', 'username': username, 'password': password}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        global client_token
        client_token = response['token']
        print('Logged-in successfully')
    else:
        main_socket = server_sock
        error = response['message']
        print(f'Error: {error}')


def upload():
    if client_token is None or client_username is None:
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
login_proxy_menu = Menu('Login into proxy', action=login_proxy)
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


def new_ticket():
    ticket_message = input('Enter your ticket message:\n')
    request = {'type': 'add-ticket', 'token': client_token, 'username': client_username, 'message': ticket_message}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Ticket created successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def string_summary(str, max_len=20):
    if len(str) <= max_len:
        return str
    else:
        return f'{str[:max_len]} ...'


def send_ticket(ticket_id):
    request = {'type': 'send-ticket', 'token': client_token, 'ticket-id': ticket_id}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Ticket sent successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def reply_ticket(ticket_id):
    ticket_message = input('Enter your ticket message:\n')
    request = {'type': 'reply-ticket', 'token': client_token, 'ticket-id': ticket_id, 'username': client_username,
               'message': ticket_message}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Ticket sent successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def close_ticket(ticket_id):
    request = {'type': 'close-ticket', 'token': client_token, 'ticket-id': ticket_id, 'username': client_username}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        print('Ticket closed successfully')
    else:
        error = response['message']
        print(f'Error: {error}')


def print_ticket(ticket):
    print(f'owner: {ticket.owner}')
    print(f'id: {ticket.id} - state: {ticket.state.name}')
    for user, message in ticket.content:
        print(f'{user}:\n{message}')
        print('-' * 6)


def see_tickets():
    request = {'type': 'list-ticket', 'token': client_token, 'username': client_username}
    send(request)
    response = receive()
    if response['type'] == 'ok':
        tickets = response['content']
        # tickets_submenus = [Menu(
        #     f'owner: {ticket.owner} - state: {ticket.state.name} - message: {string_summary(ticket.content[0][1])}',
        #     [Menu('Send Ticket', action=lambda: send_ticket(ticket.id))],
        #     action=lambda: print_ticket(ticket), parent=tickets_menu) for ticket in tickets]
        tickets_submenus = []
        for ticket in tickets:
            send_ticket_menu = Menu('Send Ticket', action=send_ticket, arg=ticket.id)
            reply_ticket_menu = Menu('Reply', action=reply_ticket, arg=ticket.id)
            close_ticket_menu = Menu('Close Thread', action=close_ticket, arg=ticket.id)
            if ticket.state == TicketState.NEW:
                submenus = [send_ticket_menu, reply_ticket_menu, close_ticket_menu]
            elif ticket.state == TicketState.CLOSED:
                submenus = []
            else:
                submenus = [reply_ticket_menu, close_ticket_menu]
            one_ticket_menu = Menu(
                f'owner: {ticket.owner} - state: {ticket.state.name} - message: {string_summary(ticket.content[0][1])}',
                submenus, action=print_ticket, parent=tickets_menu)
            one_ticket_menu.extra_arg = ticket
            tickets_submenus.append(one_ticket_menu)

        see_tickets_menu.submenus = tickets_submenus
    else:
        error = response['message']
        print(f'Error: {error}')


def tickets_menu_handler():
    if client_token is None or client_username is None:
        print('You need to login in order to upload a video.')
        main_menu.run()
        return True
    return False


new_ticket_menu = Menu('New Ticket', action=new_ticket)
see_tickets_menu = Menu('See Last Tickets', action=see_tickets)
tickets_menu = Menu('Tickets', [new_ticket_menu, see_tickets_menu], action=tickets_menu_handler)
see_tickets_menu.parent = tickets_menu

user_menu = Menu('Main Menu', [signup_menu, login_menu, login_proxy_menu, upload_menu, videos_menu, tickets_menu])


def process_admin(username, state):
    if state != 'pending':
        return
    while True:
        admin = input('Accept admin? (y/n): ')
        if admin in ['y', 'n']:
            break
    if admin == 'y':
        proxy_username = input("Enter admin's username: ")
        proxy_password = input("Enter admin's password: ")
        request = {'type': 'accept', 'token': client_token, 'admin-username': username,
                   'proxy-username': proxy_username, 'proxy-password': proxy_password}
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
        print('Un-striked successfully.')
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
admin_menu = Menu('Admin Menu', [signout_menu, videos_menu, unstrike_menu, tickets_menu])

admins_requests_menu = Menu('See admin requests', action=show_admin_requests)
manager_menu = Menu('Manager Menu', [signout_menu, admins_requests_menu, tickets_menu])
admins_requests_menu.parent = manager_menu


def run_main_menu():
    if client_role == 'user':
        user_menu.run()
    elif client_role == 'admin':
        admin_menu.run()
    else:
        manager_menu.run()


main_menu = Menu('Main Menu', action=run_main_menu)
tickets_menu.parent = main_menu

while True:
    main_menu.run()
