import json
import tempfile
import os
import unittest
from pathlib import Path

from campusflow.storage import export_tickets_csv, load_tickets, save_tickets


class TestStorage(unittest.TestCase):
    def test_load_missing_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"

            self.assertEqual(load_tickets(path), [])

    def test_save_and_load_tickets(self):
        tickets = [
            {
                "id": "T001",
                "title": "WiFi down",
                "category": "Network",
                "urgency": "high",
                "affected_users": 10,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "tickets.json"

            save_tickets(tickets, path)

            self.assertEqual(load_tickets(path), tickets)

    def test_load_malformed_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            path.write_text("{not valid json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Invalid ticket data"):
                load_tickets(path)

    def test_load_non_list_data_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            path.write_text(json.dumps({"id": "T001"}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "expected a list of tickets"):
                load_tickets(path)


if __name__ == "__main__":
    unittest.main()

class TestAtomicSave(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tickets.json")
        self.addCleanup(self.tmp.cleanup)

    def test_save_leaves_no_temp_file(self):
        save_tickets([], self.path)
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_overwrite_keeps_data_valid(self):
        save_tickets([{"id": "T001", "title": "old", "status": "open"}], self.path)
        save_tickets([], self.path)
        self.assertEqual(load_tickets(self.path), [])

class TestExportCsv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tickets.csv")
        self.addCleanup(self.tmp.cleanup)

    def test_returns_row_count(self):
        rows = [
            {"id": "T001", "title": "WiFi, lab 2", "category": "Network"},
            {"id": "T002", "title": "Broken screen", "category": "Hardware"},
        ]
        self.assertEqual(export_tickets_csv(rows, self.path), 2)

    def test_header_and_quoting(self):
        export_tickets_csv(
            [{"id": "T001", "title": "WiFi, lab 2", "category": "Network"}],
            self.path,
        )
        lines = open(self.path, encoding="utf-8").read().splitlines()
        self.assertEqual(lines[0].split(",")[:3], ["id", "title", "category"])
        self.assertIn('"WiFi, lab 2"', lines[1])

    def test_empty_export_writes_only_header(self):
        self.assertEqual(export_tickets_csv([], self.path), 0)
        lines = open(self.path, encoding="utf-8").read().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("id"))
