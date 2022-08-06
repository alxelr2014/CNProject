import enum


class TicketState(enum.Enum):
    NEW = 0
    PENDING = 1
    SOLVED = 2
    CLOSED = 3


class Ticket:
    def __init__(self, owner, state, content):
        self.owner = owner
        self.state = state
        self.content = content
