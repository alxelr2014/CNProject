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
        if username in self.disliked_users:
            self.disliked_users = self.disliked_users.remove(username)
        if username in self.liked_users:
            self.liked_users = self.liked_users.remove(username)
        else:
            self.liked_users = self.liked_users.add(username)
        
        self.likes = len(self.liked_users)

    def add_dislike(self, username):
        if username in self.liked_users:
            self.liked_users = self.liked_users.remove(username)
        if username in self.disliked_users:
            self.disliked_users = self.disliked_users.remove(username)
        else:
            self.disliked_users = self.disliked_users.add(username)
        
        self.dislikes = len(self.disliked_users)

    def set_restricted(self):
        self._restricted = True
    
    def set_block(self):
        self.blocked = True


def find_video(id, all_videos):
    for video in all_videos:
        if video.id == id:
            return video
    return None
