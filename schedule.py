"""
schedule.py
Schedule: represents one scheduled activity (title, description, date, time, category).
ScheduleManager: add, view, edit, and delete a user's schedules.
"""

import os
from datetime import datetime, timedelta

from database import Database
from user import User
from validators import (
    format_time_12h, normalize_date, normalize_time, today_string,
    validate_category, validate_date, validate_time, validate_title,
)


class Schedule:
    """One schedule entry. Holds the data and knows how to validate itself."""

    def __init__(self, id, user_id, title, description, date, time, category):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.date = date
        self.time = time
        self.category = category

    @classmethod
    def from_row(cls, row):
        """Build a Schedule from a database row."""
        return cls(
            row["id"], row["user_id"], row["title"], row["description"],
            row["date"], row["time"], row["category"],
        )

    @staticmethod
    def validate(title, date, time, category):
        """Return an error message, or None if the data is valid."""
        return (
            validate_title(title, "Schedule title")
            or validate_date(date)
            or validate_time(time)
            or validate_category(category)
        )

    @property
    def time_display(self):
        """Time shown on the screen, like '1:00 PM'."""
        return format_time_12h(self.time)


class ScheduleManager:
    """Does all schedule operations for one logged-in user."""

    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    # ---------- CREATE ----------
    def add_schedule(self, title, description, date, time, category="Personal"):
        """Add a new schedule. Returns (success, message)."""
        error = Schedule.validate(title, date, time, category)
        if error:
            return False, error

        self.db.execute(
            "INSERT INTO schedules (user_id, title, description, date, time, category) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (self.user_id, title.strip(), (description or "").strip(),
             normalize_date(date), normalize_time(time), category),
        )
        return True, "Schedule added successfully."

    # ---------- READ ----------
    def get_schedules(self, date=None):
        """Return Schedule objects, earliest first.
        Pass date='YYYY-MM-DD' to get only that day."""
        if date:
            rows = self.db.fetch_all(
                "SELECT * FROM schedules WHERE user_id = ? AND date = ? "
                "ORDER BY time ASC, id ASC",
                (self.user_id, date),
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM schedules WHERE user_id = ? "
                "ORDER BY date ASC, time ASC, id ASC",
                (self.user_id,),
            )
        return [Schedule.from_row(row) for row in rows]

    def get_today_schedules(self):
        return self.get_schedules(today_string())

    def get_upcoming(self, limit=2):
        """Schedules from today onward (used by the dashboard)."""
        rows = self.db.fetch_all(
            "SELECT * FROM schedules WHERE user_id = ? AND date >= ? "
            "ORDER BY date ASC, time ASC, id ASC LIMIT ?",
            (self.user_id, today_string(), limit),
        )
        return [Schedule.from_row(row) for row in rows]

    def get_schedule(self, schedule_id):
        """Return one Schedule (only if it belongs to this user) or None."""
        row = self.db.fetch_one(
            "SELECT * FROM schedules WHERE id = ? AND user_id = ?",
            (schedule_id, self.user_id),
        )
        return Schedule.from_row(row) if row else None

    # ---------- UPDATE ----------
    def update_schedule(self, schedule_id, title, description, date, time, category):
        """Edit an existing schedule. Returns (success, message)."""
        if self.get_schedule(schedule_id) is None:
            return False, "Schedule not found."

        error = Schedule.validate(title, date, time, category)
        if error:
            return False, error

        self.db.execute(
            "UPDATE schedules SET title = ?, description = ?, date = ?, time = ?, "
            "category = ? WHERE id = ? AND user_id = ?",
            (title.strip(), (description or "").strip(), normalize_date(date),
             normalize_time(time), category, schedule_id, self.user_id),
        )
        return True, "Schedule updated successfully."

    # ---------- DELETE ----------
    def delete_schedule(self, schedule_id):
        """Delete a schedule. Returns (success, message)."""
        if self.get_schedule(schedule_id) is None:
            return False, "Schedule not found."

        self.db.execute(
            "DELETE FROM schedules WHERE id = ? AND user_id = ?",
            (schedule_id, self.user_id),
        )
        return True, "Schedule deleted successfully."


# Quick self-test: run this file directly
if __name__ == "__main__":
    d = lambda days: (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    test_db = Database("test_schedule_check.db")

    User(test_db).register("symon@gmail.com", "Symon Cortez", "secret1", "secret1")
    User(test_db).register("maria_s", "Maria Santos", "secret2", "secret2")
    symon_id = test_db.fetch_one("SELECT id FROM users WHERE username='symon@gmail.com'")["id"]
    maria_id = test_db.fetch_one("SELECT id FROM users WHERE username='maria_s'")["id"]

    sched = ScheduleManager(test_db, symon_id)
    other = ScheduleManager(test_db, maria_id)

    print("1. Empty title      ->", sched.add_schedule("", "", d(0), "10:00", "School"))
    print("2. Bad date         ->", sched.add_schedule("Class", "", "2026-02-31", "10:00", "School"))
    print("3. Bad time         ->", sched.add_schedule("Class", "", d(0), "10am", "School"))
    print("4. Bad category     ->", sched.add_schedule("Class", "", d(0), "10:00", "Fun"))
    print("5. Add 4 schedules  ->",
          sched.add_schedule("Study Session", "Library Room B", d(0), "13:00", "School")[0],
          sched.add_schedule("Biology Lecture", "Room 204", d(0), "10:00", "School")[0],
          sched.add_schedule("Workout", "Sports complex", d(0), "16:00", "Health")[0],
          sched.add_schedule("Library Visit", "Return books", d(1), "9:30", "Personal")[0])

    print("6. All schedules (sorted by date, then time):")
    for s in sched.get_schedules():
        print(f"   [{s.id}] {s.date} {s.time_display:>8} | {s.title} | {s.category} | {s.description}")
    print("   Only today       ->", [s.title for s in sched.get_today_schedules()])
    print("7. Upcoming (2)     ->", [s.title for s in sched.get_upcoming(2)])

    print("8. Update id 2      ->", sched.update_schedule(2, "Biology Lecture (moved)", "Room 301", d(0), "11:00", "School"))
    print("9. Delete id 4      ->", sched.delete_schedule(4), "| again ->", sched.delete_schedule(4))
    print("10. Maria sees      ->", len(other.get_schedules()), "schedules (should be 0)")
    print("    Maria deletes Symon's ->", other.delete_schedule(1))
    print("    Remaining       ->", [s.title for s in sched.get_schedules()])

    os.remove(test_db.db_path)
    print("Schedule OK - test database removed.")