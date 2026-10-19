import unittest
from campusflow.reports import report_summary, report_by_assignee

class TestReports(unittest.TestCase):
    def test_summary_with_tickets(self):
        tickets = [
            {
                "id": "T001",
                "title": "WiFi down",
                "category": "Network",
                "urgency": "high",
                "affected_users": 10,
                "priority": "critical",
                "status": "open",
                "assigned_to": None
            },
            {
                "id": "T002",
                "title": "Broken keyboard",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "resolved",
                "assigned_to": "Temple"
            }
        ]

        result = report_summary(tickets)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["by_status"]["open"], 1)
        self.assertEqual(result["by_status"]["resolved"], 1)
        self.assertEqual(result["by_priority"]["critical"], 1)
        self.assertEqual(result["by_priority"]["low"], 1)

    def test_summary_with_no_tickets(self):
        result = report_summary([])

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_status"]["open"], 0)
        self.assertEqual(result["by_status"]["in_progress"], 0)
        self.assertEqual(result["by_status"]["resolved"], 0)
        self.assertEqual(result["by_priority"]["critical"], 0)
        self.assertEqual(result["by_priority"]["high"], 0)
        self.assertEqual(result["by_priority"]["medium"], 0)
        self.assertEqual(result["by_priority"]["low"], 0)

if __name__ == "__main__":
    unittest.main()


class TestStaffWorkload(unittest.TestCase):
    def _tickets(self):
        return [
            {"id": "T001", "status": "open", "assigned_to": "Ada"},
            {"id": "T002", "status": "in_progress", "assigned_to": "Ada"},
            {"id": "T003", "status": "resolved", "assigned_to": "Ada"},
            {"id": "T004", "status": "open", "assigned_to": "Grace"},
            {"id": "T005", "status": "open", "assigned_to": None},
        ]

    def test_counts_and_active_total(self):
        rows = report_by_assignee(self._tickets())
        ada = next(r for r in rows if r["staff"] == "Ada")
        self.assertEqual(ada["active"], 2)
        self.assertEqual((ada["open"], ada["in_progress"], ada["resolved"]), (1, 1, 1))

    def test_most_loaded_first(self):
        rows = report_by_assignee(self._tickets())
        self.assertEqual([r["staff"] for r in rows][0], "Ada")

    def test_unassigned_excluded(self):
        rows = report_by_assignee(self._tickets())
        self.assertEqual([r["staff"] for r in rows], ["Ada", "Grace"])
