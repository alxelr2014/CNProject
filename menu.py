import os


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


class Menu:
    def __init__(self, name, submenus=None, action=None, parent=None):
        self.name = name
        self.submenus = [] if submenus is None else submenus
        self.action = action
        self.parent = parent

    def add_submenu(self, submenu):
        self.submenus.append(submenu)

    def run(self):
        if self.action:
            self.action()
            if not self.submenus and self.parent:
                self.parent.run()
        elif self.submenus:
            print(f'\n{self.name}:')
            for i, subm in enumerate(self.submenus):
                print(f'{i}. {subm.name}')
            par_num = self.submenus
            if self.parent:
                print(f'{par_num}. Back')
            i = int(input())
            if i == par_num:
                self.parent.run()
            else:
                self.submenus[i].run()
