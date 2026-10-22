from campusflow.tickets import create_ticket, days_until_due, parse_due_date, search_tickets
from campusflow.workflow import (
    get_ticket,
    assign_ticket,
    start_ticket,
    resolve_ticket,
    reopen_ticket,
    work_queue,
)
from campusflow.reports import report_summary, report_by_assignee
from campusflow.storage import load_tickets, save_tickets, export_tickets_csv


DATA_PATH = "data/tickets.json"

CATEGORIES = ["Network", "Hardware", "Software", "Other"]
URGENCIES = ["low", "medium", "high"]
CANCEL_WORD = "back"


class CancelledInput(Exception):
    """Raised when the user types the cancel word at a prompt."""


def ask(prompt, parse):
    """Re-ask the same question until parse() accepts the answer.

    parse receives the raw text and returns the cleaned value, or raises
    ValueError with a message. Typing 'back' abandons the current action
    and returns to the main menu.
    """
    while True:
        raw = input(f"{prompt} (or '{CANCEL_WORD}' to cancel): ")
        if raw.strip().lower() == CANCEL_WORD:
            raise CancelledInput()
        try:
            return parse(raw)
        except ValueError as error:
            print(f"  Invalid input: {error}. Please try again.")


def parse_title(raw):
    if not raw.strip():
        raise ValueError("Title cannot be empty")
    return raw.strip()


def parse_choice(options, label, transform):
    def parse(raw):
        value = transform(raw.strip())
        if value not in options:
            raise ValueError(f"{label} must be one of: {', '.join(options)}")
        return value
    return parse


def parse_affected_users(raw):
    try:
        number = int(raw.strip())
    except ValueError:
        raise ValueError("Affected users must be a whole number")
    if number < 1:
        raise ValueError("Affected users must be at least 1")
    return number


def parse_staff(raw):
    if not raw.strip():
        raise ValueError("Staff name cannot be empty")
    return raw.strip()


def ask_ticket(tickets):
    """Ask for a ticket ID until it matches an existing ticket."""
    def parse(raw):
        return get_ticket(tickets, raw.strip().upper())
    return ask("Ticket ID", parse)


def parse_optional_due_date(raw):
    """Accept a blank due date (None) or a valid YYYY-MM-DD future date."""
    if not raw.strip():
        return None
    return parse_due_date(raw)


def display_ticket(ticket):
    print("\n--- Ticket Details ---")
    print(f"ID: {ticket['id']}")
    print(f"Title: {ticket['title']}")
    print(f"Category: {ticket['category']}")
    print(f"Urgency: {ticket['urgency']}")
    print(f"Affected users: {ticket['affected_users']}")
    print(f"Priority: {ticket['priority']}")
    print(f"Status: {ticket['status']}")
    print(f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}")
    if ticket.get("due_date"):
        days = days_until_due(ticket)
        if days is None:
            pass
        elif days < 0:
            print(f"Due: {ticket['due_date']} — OVERDUE by {-days} day(s)")
        elif days == 0:
            print(f"Due: {ticket['due_date']} — due TODAY")
        else:
            print(f"Due: {ticket['due_date']} — in {days} day(s)")


def list_tickets(tickets):
    if not tickets:
        print("\nNo tickets found.")
        return

    for ticket in tickets:
        display_ticket(ticket)


def create_new_ticket(tickets):
    title = ask("Ticket title", parse_title)
    category = ask(
        "Category (Network/Hardware/Software/Other)",
        parse_choice(CATEGORIES, "Category", str.title),
    )
    urgency = ask(
        "Urgency (low/medium/high)",
        parse_choice(URGENCIES, "Urgency", str.lower),
    )
    affected_users = ask("Number of affected users", parse_affected_users)
    due_date = ask("Due date, YYYY-MM-DD (blank for none)", parse_optional_due_date)

    ticket = create_ticket(
        title,
        category,
        urgency,
        affected_users,
        tickets,
        due_date=due_date,
    )

    save_tickets(tickets, DATA_PATH)
    print(f"\nTicket created successfully: {ticket['id']}")
    display_ticket(ticket)


def assign_existing_ticket(tickets):
    ticket = ask_ticket(tickets)
    ticket_id = ticket["id"]

    staff = ask("Staff member's name", parse_staff)
    assign_ticket(ticket, staff)

    save_tickets(tickets, DATA_PATH)
    print(f"\nTicket {ticket_id} assigned successfully.")


def start_existing_ticket(tickets):
    ticket = ask_ticket(tickets)
    ticket_id = ticket["id"]

    start_ticket(ticket)

    save_tickets(tickets, DATA_PATH)
    print(f"\nTicket {ticket_id} is now in progress.")


def resolve_existing_ticket(tickets):
    ticket = ask_ticket(tickets)
    ticket_id = ticket["id"]

    resolve_ticket(ticket)

    save_tickets(tickets, DATA_PATH)
    print(f"\nTicket {ticket_id} has been resolved.")


def reopen_existing_ticket(tickets):
    ticket = ask_ticket(tickets)
    ticket_id = ticket["id"]

    reopen_ticket(ticket)

    save_tickets(tickets, DATA_PATH)
    print(f"\nTicket {ticket_id} has been reopened.")


def search_for_tickets(tickets):
    query = input("Search (title or category): ").strip()
    status = (
        input("Status filter (open/in_progress/resolved, blank for all): ")
        .strip()
        .lower()
        or None
    )
    results = search_tickets(tickets, query, status)
    if not results:
        print("\nNo tickets matched your search.")
        return
    print(f"\n{len(results)} ticket(s) matched:")
    for ticket in results:
        display_ticket(ticket)


def display_work_queue(tickets):
    queue = work_queue(tickets)

    if not queue:
        print("\nThe work queue is empty.")
        return

    print("\n--- Open Ticket Work Queue ---")

    for ticket in queue:
        print(
            f"{ticket['id']} | "
            f"{ticket['priority'].upper()} | "
            f"{ticket['title']} | "
            f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}"
        )


def export_tickets_to_csv(tickets):
    path = input("Export path (default data/tickets.csv): ").strip() or "data/tickets.csv"
    count = export_tickets_csv(tickets, path)
    print(f"\nExported {count} ticket(s) to {path}.")


def display_reports(tickets):
    report = report_summary(tickets)

    print("\n--- CampusFlow Reports ---")
    print(f"Total tickets: {report['total']}")

    print("\nTickets by status:")
    for status, count in report["by_status"].items():
        print(f"  {status}: {count}")

    print("\nTickets by priority:")
    for priority, count in report["by_priority"].items():
        print(f"  {priority}: {count}")


def display_staff_workload(tickets):
    rows = report_by_assignee(tickets)

    if not rows:
        print("\nNo assigned tickets — nothing to report.")
        return

    print("\n--- Staff Workload ---")
    for row in rows:
        print(f"  {row['staff']}: {row['active']} active "
              f"({row['open']} open, {row['in_progress']} in progress), "
              f"{row['resolved']} resolved")


def display_menu():
    print("\n========== CAMPUSFLOW ==========")
    print("1. Create ticket")
    print("2. List all tickets")
    print("3. Search tickets")
    print("4. View work queue")
    print("5. Assign ticket")
    print("6. Start ticket")
    print("7. Resolve ticket")
    print("8. Reopen ticket")
    print("9. View reports")
    print("10. View staff workload")
    print("11. Export tickets to CSV")
    print("12. Exit")
    print("================================")


def main():
    try:
        tickets = load_tickets(DATA_PATH)
    except (ValueError, OSError) as error:
        print(f"Could not load ticket data: {error}")
        return

    print("Welcome to CampusFlow Helpdesk!")

    while True:
        display_menu()
        choice = input("Choose an option (1-10): ").strip()

        try:
            if choice == "1":
                create_new_ticket(tickets)

            elif choice == "2":
                list_tickets(tickets)

            elif choice == "3":
                search_for_tickets(tickets)

            elif choice == "4":
                display_work_queue(tickets)

            elif choice == "5":
                assign_existing_ticket(tickets)

            elif choice == "6":
                start_existing_ticket(tickets)

            elif choice == "7":
                resolve_existing_ticket(tickets)

            elif choice == "8":
                reopen_existing_ticket(tickets)

            elif choice == "9":
                display_reports(tickets)

            elif choice == "10":
                display_staff_workload(tickets)

            elif choice == "11":
                export_tickets_to_csv(tickets)

            elif choice == "12":
                print("Thanks for using CampusFlow. Goodbye!")
                break

            else:
                print("Invalid option. Choose a number from 1 to 12.")

        except CancelledInput:
            print("Cancelled. Returning to the main menu.")
        except (ValueError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
