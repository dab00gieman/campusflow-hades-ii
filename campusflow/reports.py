def report_summary(tickets):
    status_counts = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0
    }

    priority_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for ticket in tickets:
        status_counts[ticket["status"]] += 1
        priority_counts[ticket["priority"]] += 1

    return {
        "total": len(tickets),
        "by_status": status_counts,
        "by_priority": priority_counts
    }

def report_by_assignee(tickets):
    """Per-staff workload: status counts for every assigned ticket.

    Rows are sorted by active load (open + in_progress) so the most
    loaded staff member is first. Unassigned tickets are excluded —
    the queue view is where those live.
    """
    load = {}
    for ticket in tickets:
        staff = ticket.get("assigned_to")
        if not staff:
            continue
        row = load.setdefault(staff, {"staff": staff, "open": 0,
                                      "in_progress": 0, "resolved": 0})
        if ticket["status"] in row:
            row[ticket["status"]] += 1
    rows = sorted(load.values(),
                  key=lambda r: (-(r["open"] + r["in_progress"]), r["staff"]))
    for row in rows:
        row["active"] = row["open"] + row["in_progress"]
    return rows
