import os


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


class Menu:
    def __init__(self, name, submenus=None, action=None, parent=None, arg=None):
        self.name = name
        self.submenus = [] if submenus is None else submenus
        self.action = action
        self.parent = parent
        self.extra_arg = arg

    def add_submenu(self, submenu):
        self.submenus.append(submenu)

    def run(self):
        if self.action:
            if self.extra_arg:
                end = self.action(self.extra_arg)
            else:
                end = self.action()
            if not self.submenus and self.parent:
                self.parent.run()
            if end:
                return
        if self.submenus:
            print(f'\n{self.name}:')
            for i, subm in enumerate(self.submenus):
                print(f'{i}. {subm.name}')
            par_num = len(self.submenus)
            if self.parent:
                print(f'{par_num}. Back')
            while True:
                try:
                    i = int(input())
                    if self.parent and i == par_num:
                        self.parent.run()
                    else:
                        self.submenus[i].run()
                    break
                except (IndexError, ValueError) as e:
                    print(f'Not valid input: {str(e)}')
