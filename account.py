class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role
        self.block_count = 0
        self.is_strike = False

    def add_block(self):
        self.block_count += 1

    def set_strike(self):
        self.is_strike = True

    def unstrike(self):
        self.is_strike = False
        self.block_count = 0


def find_user(username, all_users):
    for user in all_users:
        if user.username == username:
            return user
    return None
