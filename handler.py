import numpy as np
import string
import cv2
import pickle
import struct
import json

from account import *
from video import *

PATH = './videos/'


class Handler:
    def __init__(self):
        self._users = []
        self._videos = []
        self._online_users = []
        self._admins_token = []
        self._delimieter = '\t\n'

    def process(self, req, client):
        response = {'type': 'error',
                    'message': f"no req with \'{req['type']}\' type supported!e"}
        if req['type'] == 'login':
            response = self._login_user(req['username'], req['password'])
        elif req['type'] == 'register':
            response = self._register_user(
                req['username'], req['username'], req['amdin'])
        elif req['type'] == 'show-all':
            pass
        elif req['type'] == 'show-video':
            pass
        elif req['type'] == 'upload':
            pass
        elif req['type'] == 'like':
            pass
        elif req['type'] == 'stream':
            response = self._stream_video(req['video-id'], client)
        else:
            response = {
                'type': 'error', 'message': f"no req with \'{req['type']}\' type supported!e"}

        return response

    def _generate_token():
        source = string.ascii_letters + string.digits
        return ''.join(np.random.choice(source, replace=True, size=32))

    def _login_user(self, username, password):
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'username of password is wrong!'}
        if user.password != password:
            return {'type': 'error', 'message': 'username of password is wrong!'}

        token = self._generate_token()
        self._online_users.append(token)
        return {'type': 'ok', 'token': token, 'role': user.role}

    def _register_user(self, username, password, level):
        user = find_user(username, self._users)
        if user != None:
            return {'type': 'error', 'message': 'username not available!'}
        if level == 'manager':
            return {'type': 'error', 'message': 'access denied!'}

        user = User(username, password, level)
        self._users.append(user)
        return {'type': 'ok'}

    def _add_comment(self, token, video_id, content):
        if token not in self._online_users:
            return {'type': 'error', 'message': 'login required!'}

        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}

        video.add_comment(content)
        return {'type': 'ok'}

    def _add_like(self, token, video_id, kind, value):
        # validation
        if token not in self._online_users:
            return {'type': 'error', 'message': 'you need to login first!'}

        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID!'}

        # process and validation
        if kind == 'like':
            if value == '+':
                video.add_like()
            elif value == '-':
                video.remove_like()
            else:
                return {'type': 'error', 'message': f"no value '\{value}\' is supported!"}
        elif kind == 'dislike':
            if value == '+':
                video.add_dislike()
            elif value == '-':
                video.remove_dislike()
            else:
                return {'type': 'error', 'message': f"no value '\{value}\' is supported!"}
        else:
            return {'type': 'error', 'message': f"Error: no kind \'{kind}\' is supported!"}

        return {'type': 'ok'}

    def _upload_video(self, token, username, video_name, data_len, client):  # todo
        if token not in self._online_users:
            return {'type': 'error', 'message': 'you need to login first!'}

        ack = {'type': 'ok'}
        client.send(json.dumps(ack))

        with open(PATH + video_name, 'wb') as video:
            while True:
                buffer = client.recv(2048)
                size = min(len(buffer), data_len)
                video.write(buffer[:size])
                data_len -= len(buffer)
                if data_len <= 0:
                    break

        user = find_user(username, self._users)
        v_id = self._generate_video_id()
        video = Video(user, video_name, PATH + video_name, v_id)

    def _stream_video(self, video_id, client):
        video = find_video(video_id, self._videos)
        if video == None:
            return {'type': 'error', 'message': 'no video with this ID'}

        vid = cv2.VideoCapture(video.path)
        while vid.isOpened():
            _, frame = vid.read()

            a = pickle.dumps(frame)
            message_a = struct.pack("Q", len(a))+a
            client.sendall(message_a)
            self.send_to_socket(client, message_a)
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

    def _accept_admin(self, token, username):
        # validation
        if token not in self._admins_token:
            return {'type': 'error', 'message': 'access denied!'}
        user = find_user(username, self._users)
        if user == None:
            return {'type': 'error', 'message': 'no user with username'}

        # process
        token = self._generate_token()
        # send to proxy
        #
        #

        return {'type': 'ok'}
