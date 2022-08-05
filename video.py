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
        self._blocked = False

    def add_comment(self, comment):
        self.comments.append(comment)

    def add_like(self):
        self.likes += 1

    def remove_like(self):
        self.likes = max(0, self.likes - 1)

    def add_dislike(self):
        self.dislikes += 1

    def remove_dislike(self):
        self.dislikes = max(0, self.dislikes - 1)

    def set_restricted(self):
        self._restricted = True
    
    def set_block(self):
        self._blocked = True


def find_video(id, all_videos):
    for video in all_videos:
        if video.id == id:
            return video
    return None
