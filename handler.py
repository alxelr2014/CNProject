import copy
import numpy as np
import string
import cv2
import pickle
import struct
import json
import os
import threading

from account import *
from ticket import Ticket, TicketState, find_ticket
from video import *
from token import *

def send(sock, message):
    sock.send(pickle.dumps(message))


def receive(sock):
    return pickle.loads(sock.recv(2048))


class Handler:
    def __init__(self):
        self.base_path = './videos/'
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self._videos = []
        self._users = []
        self._online_users = []
        self._tickets = []
        self._pending_admins = []
        self._manager_token = None
        self._append_lock = threading.Lock()
        self._register_user('manager', 'supreme_manager#2022', admin=2)
        self._upload_limit = 50  # MB
        self._proxy_socket = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_append_lock']
        del state['_proxy_socket']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._append_lock = threading.Lock()
        self._proxy_socket = None

    def process(self, req, client):
        print(req)
        if req['type'] == 'login':
            response = self._login_user(req['username'], req['password'], req)
        elif req['type'] == 'register':
            response = self._register_user(req['username'], req['password'], req['admin'])
        elif req['type'] == 'list-videos':
            response = self._list_videos()
        elif req['type'] == 'get-video':
            response = self._get_video(req['video-id'])
        elif req['type'] == 'stream':
            response = self._stream_video(req['video-id'], client)
        elif req['type'] == 'upload':
            response = self._upload_video(req['token'], req['username'], req['video-name'], req['len'], client)
        elif req['type'] == 'like':
            response = self._add_like(req['token'], req['username'], req['video-id'], req['kind'])
        elif req['type'] == 'comment':
            response = self._add_comment(req['token'], req['username'], req['video-id'], req['content'])
        elif req['type'] == 'restrict':
            response = self._restrict_vidoe(req['token'], req['video-id'])
        elif req['type'] == 'block':
            response = self._block_video(req['token'], req['video-id'])
        elif req['type'] == 'list-strike':
            response = self._list_strikes(req['token'])
        elif req['type'] == 'unstrike':
            response = self._unstrike_user(req['token'], req['username'])
        elif req['type'] == 'list-admins':
            response = self._list_admins(req['token'])
        elif req['type'] == 'accept':
            response = self._accept_admin(req['token'], req['admin-username'], req['proxy-username'], req['proxy-password'])
        elif req['type'] == 'reject':
            response = self._reject_admin(req['token'], req['admin-username'])
        elif req['type'] == 'proxy':
            self._handle_proxy(client)
            raise Exception('proxy thread terminated!')
        elif req['type'] == 'add-ticket':
            response = self._add_ticket(req['token'], req['username'], req['message'])
        elif req['type'] == 'send-ticket':
            response = self._send_ticke(req['token'], req['ticket-id'])
        elif req['type'] == 'reply-ticket':
            response = self._reply_ticket(req['token'], req['ticket-id'], req['message'], req['username'])
        elif req['type'] == 'close-ticket':
            response = self._close_ticket(req['token'], req['ticket-id'], req['username'])
        elif req['type'] == 'list-ticket':
            response = self._list_tickets(req['token'], req['username'])
        else:
            response = {
                'type': 'error',
                'message': f"request with \'{req['type']}\' type not supported!"
            }

        return response

    def _generate_token(self, type):
        size = 32
        if type == 'admin':
            size = 48
        elif type == 'manager':
            size = 64
        source = list(string.ascii_letters + string.digits)
        token = ''.join(np.random.choice(source, replace=True, size=size))
        return token

    def _handle_proxy(self, client):
        self._proxy_socket = client
        self._proxy_token = self._generate_token('admin')
        response = {'type': 'ok', 'token': self._proxy_token}
        send(client, response)

    def _login_user(self, username, password, req):
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        if user.password != password:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        role = user.role
        through_proxy = False
        if user.role == 'admin':
            try:
                token = req['token']
                if token != self._proxy_token:
                    return {'type': 'error', 'message': 'invalid proxy token!'}
                through_proxy = True
            except:
                role = 'user'

        if through_proxy:
            return {'type': 'ok', 'role': role}
        token = self._generate_token(user.role)
        self._append_lock.acquire()
        self._online_users.append(token)
        self._append_lock.release()
        if user.role == 'manager':
            self._manager_token = token
        return {'type': 'ok', 'token': token, 'role': role}

    def _register_user(self, username, password, admin):
        user = find_user(username, self._users)
        if user != None:
            return {'type': 'error', 'message': 'username not available!'}

        admin = int(admin)
        role = 'user'
        if admin == 1:
            role = 'admin'
        elif admin == 2:
            role = 'manager'
        user = User(username, password, role)
        if role == 'admin':
            self._append_lock.acquire()
            self._pending_admins.append(user)
            self._append_lock.release()
            id = self._generate_ticket_id()
            self._add_ticket(id, username, 'proxy info')

        self._append_lock.acquire()
        self._users.append(user)
        self._append_lock.release()
        return {'type': 'ok'}

    def _add_comment(self, token, username, video_id, content):
        if token not in self._online_users:
            return {'type': 'error', 'message': 'login required!'}

        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}

        video.lock.acquire()
        video.add_comment(username, content)
        video.lock.release()
        return {'type': 'ok'}

    def _add_like(self, token, username, video_id, kind):
        # validation
        if token not in self._online_users:
            return {'type': 'error', 'message': 'you need to login first!'}

        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}

        # process and validation
        video.lock.acquire()
        if kind == 'like':
            video.add_like(username)
        elif kind == 'dislike':
            video.add_dislike(username)
        else:
            return {'type': 'error', 'message': f"Error: no kind \'{kind}\' is supported!"}
        video.lock.release()

        return {'type': 'ok'}

    def _list_videos(self):
        response = [(v.id, v.name) for v in self._videos if not v.blocked]
        return {'type': 'ok', 'content': response}

    def _get_video(self, video_id):
        # validation
        video: Video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}
        video = copy.deepcopy(video)
        video.path = None
        video.lock = None
        video.liked_users = None
        video.disliked_users = None

        return {'type': 'ok', 'content': video}

    def _upload_video(self, token, username, video_name, data_len, client):
        if token not in self._online_users:
            return {'type': 'error', 'message': 'you need to login first!'}
        if data_len > self._upload_limit * 1024 * 1024:
            return {'type': 'error', 'message': 'file size above upload limit!'}
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'no user with username'}
        if user.is_strike:
            return {'type': 'error', 'message': 'you have been striked 😒'}

        ack = {'type': 'ok'}
        client.send(pickle.dumps(ack))

        v_id = self._generate_video_id()
        path = self.base_path + str(v_id) + video_name
        with open(path, 'wb') as video:
            while True:
                buffer = client.recv(2048)
                size = min(len(buffer), data_len)
                video.write(buffer[:size])
                data_len -= size
                if data_len <= 0:
                    break

        print('Received video successfully')
        user = find_user(username, self._users)
        self._append_lock.acquire()
        video = Video(user, video_name, path, v_id)
        self._videos.append(video)
        self._append_lock.release()
        return {'type': 'ok'}

    def _generate_video_id(self):
        return len(self._videos)

    def _stream_video(self, video_id, client):
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID'}

        vid = cv2.VideoCapture(video.path)
        n_frame = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        ack = {'type': 'ok', 'frame-count': n_frame}
        client.send(pickle.dumps(ack))

        for i in range(n_frame):
            _, frame = vid.read()

            a = pickle.dumps(frame)
            message_a = struct.pack("Q", len(a)) + a
            client.sendall(message_a)
        vid.release()
        print('Stream ended successfully.')

    def _restrict_vidoe(self, token, video_id):
        # validation
        if token != self._proxy_token:
            return {'type': 'error', 'message': 'access denied!'}
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID'}

        # process
        video.set_restricted()
        return {'type': 'ok'}

    def _block_video(self, token, video_id):
        # validation
        if token != self._proxy_token:
            return {'type': 'error', 'message': 'access denied!'}
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID'}

        # process
        video.set_blocked()
        video.user.add_block()
        if video.user.block_count == 2:
            video.user.set_strike()
        return {'type': 'ok'}

    def _list_strikes(self, token):
        # validation
        if token != self._proxy_token:
            return {'type': 'error', 'message': 'access denied!'}

        # process
        response = [user.username for user in self._users if user.is_strike]
        return {'type': 'ok', 'content': response}

    def _unstrike_user(self, token, username):
        # validation
        if token != self._proxy_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'no user with username'}

        # process
        user.unstrike()
        return {'type': 'ok'}

    def _list_admins(self, token):
        if token != self._manager_token:
            return {'type': 'error', 'message': 'access denied!'}

        response = [(user.username, 'accepted') for user in self._users if
                    (user.role == 'admin' and user not in self._pending_admins)]
        response += [(user.username, 'pending') for user in self._pending_admins]
        return {'type': 'ok', 'content': response}

    def _reject_admin(self, token, username):
        if token != self._manager_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'no user with username!'}

        self._append_lock.acquire()
        self._users.remove(user)
        self._pending_admins.remove(user)
        self._append_lock.release()
        return {'type': 'ok'}

    def _accept_admin(self, token, admin_name, username, password):
        # validation
        if token != self._manager_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(admin_name, self._users)
        if user is None:
            return {'type': 'error', 'message': 'no user with username!'}

        # process
        self._append_lock.acquire()
        self._pending_admins.remove(user)
        self._append_lock.release()
        # send to proxy
        message = {'type': 'add-admin', 'username': username, 'password': password}
        self._update_proxy_ticket(admin_name, username, password)
        try:
            send(self._proxy_socket, message)
            proxy_response = receive(self._proxy_socket)
            if proxy_response['type'] == 'ok':
                return {'type': 'ok'}
            else:
                return proxy_response
        except:
            print('Run proxy server!')
            return {'type': 'error', 'message': 'Proxy server is down.'}

    def _update_proxy_ticket(self, admin_name, username, password):
        ticket = None
        for t in self._tickets:
            if t.owner == admin_name:
                if t.content[0][1].startswidth('proxy'):
                    ticket = t
                    break
        message = f'your proxy info, username: {username}, pass:{password}'
        ticket.add_message('MANAGER', message)
        ticket.state = TicketState.CLOSED

    def _generate_ticket_id(self):
        return len(self._tickets)

    def _add_ticket(self, token, username, message):
        if token not in self._online_users and token != self._proxy_token:
            return (False, {'type': 'error', 'message': 'you need to login first!'})
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'username not exists!'}
        
        self._append_lock.acquire()
        id = self._generate_ticket_id()
        ticket = Ticket(id, username, message)
        self._tickets.append(ticket)
        self._append_lock.release()
        
        return {'type': 'ok'}

    def _send_ticket(self, token, ticket_id):
        if token not in self._online_users and token != self._proxy_token:
            return {'type': 'error', 'message': 'you need to login first!'}
        ticket = find_ticket(ticket_id, self._tickets)
        if ticket is None:
            return {'type': 'error', 'message': 'no ticket with this ID!'}

        ticket.state = TicketState.PENDING
        return {'type': 'ok'}

    def _reply_ticket(self, token, ticket_id, message, username):
        if token not in self._online_users and token != self._proxy_token:
            return {'type': 'error', 'message': 'you need to login first!'}
        ticket = find_ticket(ticket_id, self._tickets)
        if ticket is None:
            return {'type': 'error', 'message': 'no ticket with this ID!'}
        
        ticket.add_message(username, message)
        if ticket.owner != username:
            ticket.state = TicketState.SOLVED
        elif ticket.owner == username:
            ticket.state = TicketState.PENDING
        return {'type': 'ok'}

    def _close_ticket(self, token, ticket_id, username):
        if token not in self._online_users and token != self._proxy_token:
            return {'type': 'error', 'message': 'you need to login first!'}
        ticket = find_ticket(ticket_id, self._tickets)
        if ticket is None:
            return {'type': 'error', 'message': 'no ticket with this ID!'}
        if ticket.owner != username:
            return {'type': 'error', 'message': 'only the owner of ticket can close it!'}
        
        ticket.state = TicketState.CLOSED
        return {'type': 'ok'}

    def _list_tickets(self, token, username):
        if token not in self._online_users and token != self._proxy_token:
            return {'type': 'error', 'message': 'you need to login first!'}
        user = find_user(username, self._users)
        if user is None:
            return {'type': 'error', 'message': 'username not exists!'}
        
        mask = []
        if user.role == 'manager':
            mask = ['admin']
        elif user.role == 'admin':
            through_proxy = token == self._proxy_token
            if through_proxy:
                mask = ['admin', 'user']
            else:
                mask = []
        
        tickets = [t for t in self._tickets if t.owner == username]
        tickets += [t for t in self._tickets if find_user(t.owner, self._users).role in mask and t.state == TicketState.PENDING]
        
        return {'type': 'ok', 'content': tickets}