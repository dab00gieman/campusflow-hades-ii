from datetime import date

def stale_tickets(tickets, days=7, today=None):
    """Open/in-progress tickets older than `days`, most stale first.

    WHY tickets without created_at are skipped: aging stamps land on
    newly created tickets (parity with zeus-ii #14); records saved
    before stamping have no baseline date, so aging them would be a
    guess, not a fact.
    """
    today = today or date.today()
    rows = []
    for ticket in tickets:
        created = ticket.get("created_at")
        if not created or ticket["status"] == "resolved":
            continue
        age = (today - date.fromisoformat(created)).days
        if age > days:
            rows.append({
                "id": ticket["id"],
                "title": ticket["title"],
                "status": ticket["status"],
                "created_at": created,
                "age": age,
            })
    return sorted(rows, key=lambda row: row["age"], reverse=True)


def get_ticket(tickets, ticket_id):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Unknown ticket ID: {ticket_id}")

def assign_ticket(ticket, staff):
    if not staff or not staff.strip():
        raise ValueError("Staff name cannot be empty")
    ticket["assigned_to"] = staff.strip()
    return ticket

def start_ticket(ticket):
    if ticket["status"] != "open":
        raise ValueError("Only open tickets can be started")
    if not ticket["assigned_to"]:
        raise ValueError("Ticket must be assigned before starting")
    ticket["status"] = "in_progress"
    return ticket

def resolve_ticket(ticket):
    if ticket["status"] != "in_progress":
        raise ValueError("Only in-progress tickets can be resolved")
    ticket["status"] = "resolved"
    return ticket


def reopen_ticket(ticket):
    if ticket["status"] != "resolved":
        raise ValueError("Only resolved tickets can be reopened")
    ticket["status"] = "open"
    return ticket

def work_queue(tickets):
    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3
    }

    queue = [
        ticket for ticket in tickets
        if ticket["status"] == "open"
    ]

    return sorted(
        queue,
        key=lambda ticket: (
            priority_order[ticket["priority"]],
            int(ticket["id"][1:])
        )
    )