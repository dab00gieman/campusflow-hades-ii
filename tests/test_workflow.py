import unittest
from datetime import date, timedelta
from campusflow.workflow import assign_ticket, get_ticket, reopen_ticket, resolve_ticket, stale_tickets, start_ticket, work_queue

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.ticket = {
            "id": "T001",
            "title": "WiFi down",
            "category": "Network",
            "urgency": "high",
            "affected_users": 10,
            "priority": "critical",
            "status": "open",
            "assigned_to": None
        }
        self.tickets = [self.ticket]

    def test_get_ticket(self):
        result = get_ticket(self.tickets, "T001")
        self.assertEqual(result["title"], "WiFi down")

    def test_unknown_ticket(self):
        with self.assertRaises(ValueError):
            get_ticket(self.tickets, "T999")

    def test_assign_ticket(self):
        assign_ticket(self.ticket, "Temple")
        self.assertEqual(self.ticket["assigned_to"], "Temple")

    def test_reject_empty_staff(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.ticket, " ")

    def test_start_ticket(self):
        assign_ticket(self.ticket, "Temple")
        start_ticket(self.ticket)
        self.assertEqual(self.ticket["status"], "in_progress")

    def test_cannot_start_unassigned_ticket(self):
        with self.assertRaises(ValueError):
            start_ticket(self.ticket)

    def test_resolve_ticket(self):
        assign_ticket(self.ticket, "Temple")
        start_ticket(self.ticket)
        resolve_ticket(self.ticket)
        self.assertEqual(self.ticket["status"], "resolved")

    def test_reopen_ticket(self):
        assign_ticket(self.ticket, "Temple")
        start_ticket(self.ticket)
        resolve_ticket(self.ticket)
        reopen_ticket(self.ticket)
        self.assertEqual(self.ticket["status"], "open")

    def test_work_queue(self):
        result = work_queue(self.tickets)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "T001")

    def test_work_queue_excludes_in_progress(self):
        assign_ticket(self.ticket, "Temple")
        start_ticket(self.ticket)
        self.assertEqual(work_queue(self.tickets), [])

if __name__ == "__main__":
    unittest.main()

class TestStaleTickets(unittest.TestCase):
    def make(self, age_days, status="open", stamp=True):
        ticket = {
            "id": "T%03d" % age_days,
            "title": "aged %d" % age_days,
            "status": status,
        }
        if stamp:
            ticket["created_at"] = (
                date.today() - timedelta(days=age_days)
            ).isoformat()
        return ticket

    def test_stale_only_past_threshold(self):
        rows = stale_tickets(
            [self.make(10), self.make(3)], today=date.today()
        )
        self.assertEqual([r["id"] for r in rows], ["T010"])

    def test_resolved_never_stale(self):
        rows = stale_tickets(
            [self.make(30, status="resolved")], today=date.today()
        )
        self.assertEqual(rows, [])

    def test_unstamped_records_skipped(self):
        rows = stale_tickets([self.make(0, stamp=False)], today=date.today())
        self.assertEqual(rows, [])

    def test_boundary_age_equals_days_not_stale(self):
        rows = stale_tickets([self.make(7)], today=date.today())
        self.assertEqual(rows, [])

    def test_sorted_most_stale_first(self):
        rows = stale_tickets(
            [self.make(9), self.make(30), self.make(20)], today=date.today()
        )
        self.assertEqual([r["age"] for r in rows], [30, 20, 9])

    def test_row_shape(self):
        rows = stale_tickets([self.make(12)], today=date.today())
        self.assertEqual(
            set(rows[0]),
            {"id", "title", "status", "created_at", "age"},
        )

    def test_in_progress_counts_as_stale(self):
        rows = stale_tickets(
            [self.make(15, status="in_progress")], today=date.today()
        )
        self.assertEqual(len(rows), 1)
