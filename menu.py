import os


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


class Menu:
    def __init__(self, name, submenus=None, action=None):
        self.name = name
        self.submenus = [] if submenus is None else submenus
        self.action = action

    def add_submenu(self, submenu):
        self.submenus.append(submenu)

    def run(self):
        if self.action:
            self.action()
        if self.submenus:
            print(f'\n{self.name}:')
            for i, subm in enumerate(self.submenus):
                print(f'{i}. {subm.name}')
            i = int(input())
            self.submenus[i].run()
