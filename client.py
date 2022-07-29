from menu import *
SERVER_IP = 'localhost'
SERVER_PORT = 8080


def make_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    return s


def login():
    username = input("Enter username: ")
    password = input("\nEnter password: ")


def signup():
    username = input("Enter username: ")
    password = input("\nEnter password: ")
    is_admin = input("\nAre you an admin?")



def search():
    pass

login_menu = Menu("login_menu",None,login)
signup_menu = Menu("Signup_menu",None,signup)
search_menu = Menu("Search",None,search)


main_menu = Menu("main_menu",[login_menu,signup_menu,search_menu])
