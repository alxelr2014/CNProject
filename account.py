class Account:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class User(Account):
    def __init__(self, username, password):
        super().__init__(username, password)


class Admin(Account):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.username = username
        self.password = password


class Manager(Account):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.username = username
        self.password = password
