"""
task.py
Task: represents one daily task (title, description, date, time, category, completed).
TaskManager: add, view (with tabs and search), edit, tick/untick, and delete tasks.
"""

import os
from datetime import datetime, timedelta

from database import Database
from user import User
from validators import (
    CATEGORIES, format_time_12h, normalize_date, normalize_time,
    validate_category, validate_date, validate_time, validate_title,
)

TABS = ("All", "Active", "Completed")


class Task:
    """One task. Holds the data and knows how to validate itself."""

    def __init__(self, id, user_id, title, description, date, time, category, completed):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.date = date
        self.time = time
        self.category = category
        self.completed = completed

    @classmethod
    def from_row(cls, row):
        """Build a Task from a database row."""
        return cls(
            row["id"], row["user_id"], row["title"], row["description"],
            row["date"], row["time"], row["category"], bool(row["completed"]),
        )

    @staticmethod
    def validate(title, date, time, category):
        """Return an error message, or None if the data is valid."""
        return (
            validate_title(title, "Task title")
            or validate_date(date)
            or validate_time(time)
            or validate_category(category)
        )

    @property
    def time_display(self):
        """Time shown on the screen, like '1:00 PM'."""
        return format_time_12h(self.time)

    def is_overdue(self):
        """Still active and its date/time has already passed."""
        if self.completed:
            return False
        return f"{self.date} {self.time}" < datetime.now().strftime("%Y-%m-%d %H:%M")


class TaskManager:
    """Does all task operations for one logged-in user."""

    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    # ---------- CREATE ----------
    def add_task(self, title, description, date, time, category="Personal"):
        """Add a new task. Returns (success, message)."""
        error = Task.validate(title, date, time, category)
        if error:
            return False, error

        self.db.execute(
            "INSERT INTO tasks (user_id, title, description, date, time, category, completed) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (self.user_id, title.strip(), (description or "").strip(),
             normalize_date(date), normalize_time(time), category),
        )
        return True, "Task added successfully."

    # ---------- READ ----------
    def get_tasks(self, tab="All", search=""):
        """Return Task objects, earliest first.
        tab: 'All', 'Active' or 'Completed'.  search: part of the title."""
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [self.user_id]

        tab = (tab or "All").capitalize()
        if tab == "Active":
            query += " AND completed = 0"
        elif tab == "Completed":
            query += " AND completed = 1"

        if search and search.strip():
            query += " AND INSTR(LOWER(title), LOWER(?)) > 0"
            params.append(search.strip())

        query += " ORDER BY date ASC, time ASC, id ASC"
        return [Task.from_row(row) for row in self.db.fetch_all(query, tuple(params))]

    def get_task(self, task_id):
        """Return one Task (only if it belongs to this user) or None."""
        row = self.db.fetch_one(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, self.user_id)
        )
        return Task.from_row(row) if row else None

    def get_today_tasks(self):
        return [t for t in self.get_tasks() if t.date == datetime.now().strftime("%Y-%m-%d")]

    def count_tasks(self, tab="All"):
        return len(self.get_tasks(tab))

    # ---------- UPDATE ----------
    def update_task(self, task_id, title, description, date, time, category):
        """Edit an existing task. Returns (success, message)."""
        if self.get_task(task_id) is None:
            return False, "Task not found."

        error = Task.validate(title, date, time, category)
        if error:
            return False, error

        self.db.execute(
            "UPDATE tasks SET title = ?, description = ?, date = ?, time = ?, category = ? "
            "WHERE id = ? AND user_id = ?",
            (title.strip(), (description or "").strip(), normalize_date(date),
             normalize_time(time), category, task_id, self.user_id),
        )
        return True, "Task updated successfully."

    def toggle_task(self, task_id):
        """Tick or untick a task. Returns (success, message)."""
        task = self.get_task(task_id)
        if task is None:
            return False, "Task not found."

        new_value = 0 if task.completed else 1
        self.db.execute(
            "UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?",
            (new_value, task_id, self.user_id),
        )
        return True, "Task completed." if new_value else "Task marked as active."

    # ---------- DELETE ----------
    def delete_task(self, task_id):
        """Delete a task. Returns (success, message)."""
        if self.get_task(task_id) is None:
            return False, "Task not found."

        self.db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, self.user_id)
        )
        return True, "Task deleted successfully."


# Quick self-test: run this file directly
if __name__ == "__main__":
    d = lambda days: (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    test_db = Database("test_task_check.db")

    User(test_db).register("symon@gmail.com", "Symon Cortez", "secret1", "secret1")
    User(test_db).register("maria_s", "Maria Santos", "secret2", "secret2")
    symon_id = test_db.fetch_one("SELECT id FROM users WHERE username='symon@gmail.com'")["id"]
    maria_id = test_db.fetch_one("SELECT id FROM users WHERE username='maria_s'")["id"]

    tasks = TaskManager(test_db, symon_id)
    other = TaskManager(test_db, maria_id)

    print("1. Empty title      ->", tasks.add_task("", "", d(1), "08:00", "School"))
    print("2. Bad date         ->", tasks.add_task("Study", "", "2026-13-45", "08:00", "School"))
    print("3. Bad time         ->", tasks.add_task("Study", "", d(1), "8am", "School"))
    print("4. Bad category     ->", tasks.add_task("Study", "", d(1), "08:00", "Fun"))
    print("5. Add 4 tasks      ->",
          tasks.add_task("Finish Research Paper", "Methodology", d(-2), "08:00", "School")[0],
          tasks.add_task("Buy Groceries", "Milk, eggs", d(0), "17:00", "Personal")[0],
          tasks.add_task("Submit Assignment 3", "Before midnight", d(1), "23:00", "Important")[0],
          tasks.add_task("Team Meeting", "", d(3), "9:30", "Work")[0])

    print("6. All tasks:")
    for t in tasks.get_tasks():
        print(f"   [{t.id}] {t.date} {t.time_display:>8} | {t.title} | {t.category} | "
              f"done={t.completed} | overdue={t.is_overdue()}")

    print("7. Tick task 1      ->", tasks.toggle_task(1))
    print("   Tabs -> All:", tasks.count_tasks("All"), "| Active:", tasks.count_tasks("Active"),
          "| Completed:", tasks.count_tasks("Completed"))
    print("   Untick task 1    ->", tasks.toggle_task(1))
    print("8. Search 'meeting' ->", [t.title for t in tasks.get_tasks(search="meeting")])
    print("   Search 'GROC'    ->", [t.title for t in tasks.get_tasks(search="GROC")])
    print("   Search 'xyz'     ->", [t.title for t in tasks.get_tasks(search="xyz")])
    print("9. Update task 2    ->", tasks.update_task(2, "Buy Groceries & Fruits", "More", d(0), "18:00", "Health"))
    print("   Today's tasks    ->", [t.title for t in tasks.get_today_tasks()])
    print("10. Delete task 4   ->", tasks.delete_task(4), "| again ->", tasks.delete_task(4))
    print("    Maria sees      ->", len(other.get_tasks()), "tasks (should be 0)")
    print("    Maria ticks Symon's ->", other.toggle_task(1))
    print("    Remaining       ->", [t.title for t in tasks.get_tasks()])

    os.remove(test_db.db_path)
    print("Task OK - test database removed.")