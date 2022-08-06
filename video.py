import threading


class Video:
    def __init__(self, user, name, path, id):
        self.user = user
        self.id = id
        self.name = name
        self.path = path
        self.comments = []
        self.likes = 0
        self.dislikes = 0
        self._restricted = False
        self.blocked = False
        self.liked_users = set()
        self.disliked_users = set()
        self.lock = threading.Lock()

    def add_comment(self, username, comment):
        self.comments.append((username, comment))

    def add_like(self, username):
        self._like_dislike(username, self.liked_users, self.disliked_users)
        return
        if username in self.disliked_users:
            self.disliked_users.remove(username)
        if username in self.liked_users:
            self.liked_users.remove(username)
        else:
            self.liked_users.add(username)

        self.likes = len(self.liked_users)
        self.dislikes = len(self.disliked_users)

    def add_dislike(self, username):
        self._like_dislike(username, self.disliked_users, self.liked_users)
        return
        if username in self.liked_users:
            self.liked_users.remove(username)
        if username in self.disliked_users:
            self.disliked_users.remove(username)
        else:
            self.disliked_users.add(username)

        self.dislikes = len(self.disliked_users)
        self.likes = len(self.liked_users)

    def _like_dislike(self, username, _to, _from):
        if username in _from:
            _from.remove(username)
        if username in _to:
            _to.remove(username)
        else:
            _to.add(username)

        self.dislikes = len(self.disliked_users)
        self.likes = len(self.liked_users)

    def set_restricted(self):
        self._restricted = True

    def set_block(self):
        self.blocked = True

    def get_likes(self):
        return self.likes

    def get_dislikes(self):
        return self.dislikes

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.user, self.id, self.name, self.comments, self.likes, self.dislikes, self._restricted, self.blocked

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.user, self.id, self.name, self.comments, self.likes, self.dislikes, self._restricted, self.blocked = state


def find_video(id, all_videos):
    for video in all_videos:
        if video.id == id:
            return video
    return None
