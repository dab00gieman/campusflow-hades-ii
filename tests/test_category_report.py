import unittest

from campusflow.reports import report_by_category
from campusflow.tickets import create_ticket


class TestCategoryReport(unittest.TestCase):

    def test_counts_per_category(self):
        tickets = []
        create_ticket("A", "Network", "low", 1, tickets)
        create_ticket("B", "Network", "low", 1, tickets)
        create_ticket("C", "Hardware", "low", 1, tickets)
        rows = report_by_category(tickets)
        by_cat = {r["category"]: r["count"] for r in rows}
        self.assertEqual(by_cat, {"Network": 2, "Hardware": 1})

    def test_sorted_highest_first(self):
        tickets = []
        for i in range(3):
            create_ticket(f"HW{i}", "Hardware", "low", 1, tickets)
        create_ticket("Net", "Network", "low", 1, tickets)
        rows = report_by_category(tickets)
        self.assertEqual(rows[0]["category"], "Hardware")

    def test_share_percentages(self):
        tickets = []
        create_ticket("A", "Network", "low", 1, tickets)
        create_ticket("B", "Hardware", "low", 1, tickets)
        rows = report_by_category(tickets)
        shares = {r["category"]: r["share"] for r in rows}
        self.assertEqual(shares, {"Network": 50.0, "Hardware": 50.0})

    def test_empty_list(self):
        self.assertEqual(report_by_category([]), [])

    def test_tie_breaks_alphabetically(self):
        tickets = []
        create_ticket("A", "Other", "low", 1, tickets)
        create_ticket("B", "Hardware", "low", 1, tickets)
        rows = report_by_category(tickets)
        self.assertEqual(
            [r["category"] for r in rows], ["Hardware", "Other"]
        )


if __name__ == "__main__":
    unittest.main()
