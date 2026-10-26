import unittest
from datetime import date, timedelta
from campusflow.reports import report_due, report_summary, report_by_assignee

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


class TestReportDue(unittest.TestCase):
    TODAY = date(2026, 10, 26)

    def ticket(self, days_offset, status="open", priority="high", tid="T001", title="Lab PC"):
        due = self.TODAY + timedelta(days=days_offset)
        return {"id": tid, "title": title, "priority": priority, "status": status,
                "due_date": due.isoformat()}

    def test_overdue_tickets_are_reported(self):
        report = report_due([self.ticket(-2)], today=self.TODAY)
        self.assertEqual(report["overdue_count"], 1)
        self.assertEqual(report["overdue"][0]["days"], -2)

    def test_due_soon_within_window(self):
        report = report_due([self.ticket(2)], today=self.TODAY)
        self.assertEqual(report["due_soon_count"], 1)
        self.assertEqual(report["overdue_count"], 0)

    def test_due_today_counts_as_due_soon(self):
        report = report_due([self.ticket(0)], today=self.TODAY)
        self.assertEqual(report["due_soon"][0]["days"], 0)

    def test_boundary_included_last_day_of_window(self):
        report = report_due([self.ticket(3)], today=self.TODAY)
        self.assertEqual(report["due_soon_count"], 1)

    def test_beyond_window_excluded(self):
        report = report_due([self.ticket(4)], today=self.TODAY)
        self.assertEqual(report["due_soon_count"], 0)
        self.assertEqual(report["overdue_count"], 0)

    def test_resolved_tickets_excluded(self):
        report = report_due([self.ticket(-1, status="resolved")], today=self.TODAY)
        self.assertEqual(report["overdue_count"], 0)

    def test_tickets_without_due_date_excluded(self):
        report = report_due([{"id": "T002", "title": "x", "priority": "low",
                              "status": "open", "due_date": None}], today=self.TODAY)
        self.assertEqual(report["overdue_count"], 0)
        self.assertEqual(report["due_soon_count"], 0)

    def test_sorted_most_overdue_first(self):
        tickets = [self.ticket(-1, tid="T001"), self.ticket(-5, tid="T002")]
        report = report_due(tickets, today=self.TODAY)
        self.assertEqual([row["id"] for row in report["overdue"]], ["T002", "T001"])
