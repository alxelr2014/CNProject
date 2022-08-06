import enum


class TicketState(enum.Enum):
    NEW = 0
    PENDING = 1
    SOLVED = 2
    CLOSED = 3


class Ticket:
    def __init__(self, id, owner, content):
        self.id = id
        self.owner = owner
        self.state = TicketState.NEW
        self.content = [(owner, content)]

    def add_message(self, username, message):
        self.content.append((username, message))


def find_ticket(ticket_id, all_tickets):
    for ticket in all_tickets:
        if ticket.id == ticket_id:
            return ticket
    return None
