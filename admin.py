

from account import Account


class Admin(Account):
    def __init__(self,username,password):
        self.username = username;
        self.password = password
        
