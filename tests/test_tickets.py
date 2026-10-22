import unittest
from campusflow.tickets import (
    calculate_priority,
    create_ticket,
    days_until_due,
    next_id,
    parse_due_date,
    search_tickets,
)

class TestTickets(unittest.TestCase):
    def test_critical_priority(self):
        result = calculate_priority("high", 10)
        self.assertEqual(result, "critical")

    def test_high_priority(self):
        result = calculate_priority("high", 2)
        self.assertEqual(result, "high")

    def test_medium_priority(self):
        result = calculate_priority("medium", 3)
        self.assertEqual(result, "medium")

    def test_low_priority(self):
        result = calculate_priority("low", 2)
        self.assertEqual(result, "low")

    def test_first_ticket_id(self):
        result = next_id([])
        self.assertEqual(result, "T001")

    def test_create_ticket(self):
        tickets = []
        ticket = create_ticket("WiFi down", "Network", "high", 10, tickets)
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(len(tickets), 1)

if __name__ == "__main__":
    unittest.main()

class TestSearchTickets(unittest.TestCase):
    def _sample(self):
        tickets = []
        create_ticket("WiFi down in lab", "Network", "high", 10, tickets)
        create_ticket("Broken laptop screen", "Hardware", "medium", 1, tickets)
        create_ticket("Python venv broken", "Software", "low", 1, tickets)
        return tickets

    def test_matches_title_case_insensitively(self):
        results = search_tickets(self._sample(), "WIFI")
        self.assertEqual([t["id"] for t in results], ["T001"])

    def test_matches_category(self):
        results = search_tickets(self._sample(), "hardware")
        self.assertEqual([t["id"] for t in results], ["T002"])

    def test_status_filter_narrows(self):
        results = search_tickets(self._sample(), "e", status="open")
        self.assertTrue(results)
        self.assertTrue(all(t["status"] == "open" for t in results))

    def test_unknown_status_raises(self):
        with self.assertRaises(ValueError):
            search_tickets(self._sample(), "e", status="closed")

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            search_tickets(self._sample(), "  ")

    def test_no_match_returns_empty(self):
        self.assertEqual(search_tickets(self._sample(), "zebra"), [])


class DueDateTest(unittest.TestCase):
    def test_create_with_valid_due_date(self):
        tickets = []
        t = create_ticket("Email down", "Network", "high", 30, tickets,
                          due_date="2026-12-25")
        self.assertEqual(t["due_date"], "2026-12-25")

    def test_create_without_due_date(self):
        tickets = []
        t = create_ticket("Email down", "Network", "high", 30, tickets)
        self.assertIsNone(t["due_date"])

    def test_rejects_past_date(self):
        with self.assertRaises(ValueError):
            create_ticket("x", "Other", "low", 1, [], due_date="2020-01-01")

    def test_rejects_bad_format(self):
        with self.assertRaises(ValueError):
            create_ticket("x", "Other", "low", 1, [], due_date="25/12/2026")

    def test_days_until_due_math(self):
        from datetime import date
        t = {"due_date": "2026-11-01"}
        self.assertEqual(days_until_due(t, today=date(2026, 10, 31)), 1)
        self.assertEqual(days_until_due(t, today=date(2026, 11, 2)), -1)
        self.assertIsNone(days_until_due({}))
