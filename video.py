class Video:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.comments = []
        self.likes = 0
        self.dislikes = 0

    def add_comment(self, comment):
        self.comments.add(comment)

    def add_like(self):
        self.likes += 1

    def remove_like(self):
        if self.likes > 0:
            self.likes -= 1

    def add_dislike(self):
        self.dislikes += 1

    def remove_dislike(self):
        if self.dislikes > 0:
            self.dislikes -= 1
