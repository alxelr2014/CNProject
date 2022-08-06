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
from video import *


def send(sock, message):
    sock.send(pickle.dumps(message))


def receive(sock):
    return pickle.loads(sock.recv(2048))


class Handler:
    def __init__(self):
        self.base_path = './videos/'
        self._videos = self._load_videos()
        self._users = []
        self._online_users = []
        self._admins_token = []
        self._pending_admins = []
        self._manager_token = None
        self._append_lock = threading.Lock()
        self._register_user('manager', 'supreme_manager#2022', admin=2)
        self._upload_limit = 50  # MB
        self._proxy_socket = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_append_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._append_lock = threading.Lock()

    def process(self, req, client):
        print(req)
        if req['type'] == 'login':
            response = self._login_user(req['username'], req['password'])
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
            response = self._accept_admin(req['token'], req['admin-username'])
        elif req['type'] == 'reject':
            response = self._reject_admin(req['token'], req['admin-username'])
        elif req['type'] == 'proxy':
            self._proxy_token = self._generate_token('admin')
            response = {'type': 'ok', 'token': self._proxy_token}
            self._proxy_socket = client
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

    def _login_user(self, username, password):
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        if user.password != password:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        if user in self._pending_admins:
            return {'type': 'error', 'message': 'your request is still in the pending list!'}
        if user.role == 'admin':
            return {'type': 'error', 'message': 'use proxy server'}

        token = self._generate_token(user.role)
        self._append_lock.acquire()
        self._online_users.append(token)
        self._append_lock.release()
        if user.role == 'manager':
            self._manager_token = token
        return {'type': 'ok', 'token': token, 'role': user.role}

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
        if user == None:
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
        if user == None:
            return {'type': 'error', 'message': 'no user with username!'}

        self._append_lock.acquire()
        self._users.remove(user)
        self._pending_admins.remove(user)
        self._append_lock.release()
        return {'type': 'ok'}

    def _accept_admin(self, token, username):
        # validation
        if token != self._manager_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'no user with username!'}

        # process
        self._append_lock.acquire()
        self._pending_admins.remove(user)
        self._append_lock.release()
        # send to proxy
        message = {'type': 'add-admin', 'username': user.username, 'password': user.password}
        send(self._proxy_socket, message)
        proxy_response = receive(self._proxy_socket)
        if proxy_response['type'] == 'ok':
            return {'type': 'ok'}
        else:
            return proxy_response
