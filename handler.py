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


class Handler:
    def __init__(self):
        self.base_path = './videos/'
        self._videos = self._load_videos()
        self._users = []
        self._online_users = []
        self._admins_token = []
        self._manager_token = None
        self._register_user('manager', 'supreme_manager#2022', admin=2)
        self._append_lock = threading.Lock()

    def process(self, req, client):
        if req['type'] == 'login':
            response = self._login_user(req['username'], req['password'])
        elif req['type'] == 'register':
            response = self._register_user(req['username'], req['password'], req['amdin'])
        elif req['type'] == 'list-videos':
            response = self._list_videos()
        elif req['type'] == 'get-video':
            response = self._get_video(req['video-id'])
        elif req['type'] == 'stream':
            response = self._stream_video(req['video-id'], client)
        elif req['type'] == 'upload':
            response = self._upload_video(req['token'], req['username'], req['video_name'], req['len'], client)
        elif req['type'] == 'like':
            response = self._add_like(req['token'], req['username'], req['video-id'], req['kind'])
        elif req['type'] == 'comment':
            response = self._add_comment(req['token'], req['username'], req['video-id'], req['content'])
        elif req['type'] == 'restrict':
            response = self._restrict_vidoe(req['token'], req['video-id'])
        elif req['type'] == 'block':
            response = self._block_video(req['token'], req['video-id'])
        elif req['type'] == 'unstrike':
            response = self._unstrike_user(req['token'], req['username'])
        elif req['type'] == 'list-admins':
            response = self._list_admins(req['token'])
        elif req['type'] == 'accept':
            response = self._accept_admin(req['token'], req['username'])
        else:
            response = {
                'type': 'error',
                'message': f"request with \'{req['type']}\' type not supported!"
            }

        return response

    def _load_videos(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            return []

        videos = []
        return videos
        with os.scandir(self.base_path) as entries:
            for entry in entries:
                id = self._generate_video_id()
                user = User()  # todo
                v = Video(user, entry.name, self.base_path + entry.name + id)
                videos.append(v)
        return videos

    def _generate_token(type):
        size = 32
        if type == 'amdin':
            size = 48
        elif type == 'manager':
            size = 64
        source = string.ascii_letters + string.digits
        return ''.join(np.random.choice(source, replace=True, size=size))

    def _login_user(self, username, password):
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        if user.password != password:
            return {'type': 'error', 'message': 'username of password is wrong!'}

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
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}

        # process
        return {'type': 'ok', 'content': video}

    def _upload_video(self, token, username, video_name, data_len, client):
        if token not in self._online_users:
            return {'type': 'error', 'message': 'you need to login first!'}

        ack = {'type': 'ok'}
        client.send(pickle.dumps(ack))

        with open(self.base_path + video_name, 'wb') as video:
            while True:
                buffer = client.recv(2048)
                size = min(len(buffer), data_len)
                video.write(buffer[:size])
                data_len -= size
                if data_len <= 0:
                    break

        user = find_user(username, self._users)
        self._append_lock.acquire()
        v_id = self._generate_video_id()
        video = Video(user, video_name, self.base_path + video_name, v_id)
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

        while vid.isOpened():
            _, frame = vid.read()

            a = pickle.dumps(frame)
            message_a = struct.pack("Q", len(a)) + a
            client.sendall(message_a)
        vid.release()

    def _restrict_vidoe(self, token, video_id):
        # validation
        if token not in self._admins_token:
            return {'type': 'error', 'message': 'access denied!'}
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID'}

        # process
        video.set_restricted()
        return {'type': 'ok'}

    def _block_video(self, token, video_id):
        # validation
        if token not in self._admins_token:
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

    def _unstrike_user(self, token, username):
        # validation
        if token not in self._admins_token:
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
        
        response = [user.username for user in self._users if user.role == 'admin']
        return {'type': 'ok', 'content': response}

    def _accept_admin(self, token, username):
        # validation
        if token != self._manager_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'no user with username!'}

        # process
        token = self._generate_token(type='admin')
        # send to proxy
        #
        #

        return {'type': 'ok'}
