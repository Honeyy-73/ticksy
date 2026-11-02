"""
dashboard.py
Dashboard: builds the overview shown after login
(greeting, progress ring numbers, today's tasks, upcoming schedules).
"""

import os
from datetime import datetime, timedelta

from database import Database
from schedule import ScheduleManager
from task import TaskManager
from user import User


class Dashboard:
    """Collects summary information for the logged-in user."""

    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.tasks = TaskManager(db, user.id)
        self.schedules = ScheduleManager(db, user.id)

    @staticmethod
    def get_greeting():
        hour = datetime.now().hour
        if hour < 12:
            return "Good Morning"
        if hour < 18:
            return "Good Afternoon"
        return "Good Evening"

    def get_summary(self):
        """Return everything the dashboard screen needs as one dictionary."""
        all_tasks = self.tasks.get_tasks()
        completed = [t for t in all_tasks if t.completed]
        active = [t for t in all_tasks if not t.completed]
        overdue = [t for t in active if t.is_overdue()]

        # Show tasks due today. If there are none, show the next active tasks instead.
        today_tasks = self.tasks.get_today_tasks()
        if today_tasks:
            task_list_title, task_list = "Today's Tasks", today_tasks[:3]
        else:
            task_list_title, task_list = "Up Next", active[:3]

        return {
            "greeting": self.get_greeting(),
            "name": self.user.first_name(),
            "today": datetime.now().strftime("%A, %B %d"),
            "total_tasks": len(all_tasks),
            "completed_count": len(completed),
            "active_count": len(active),
            "overdue_count": len(overdue),
            "task_list_title": task_list_title,
            "task_list": task_list,
            "upcoming_schedules": self.schedules.get_upcoming(2),
        }


# Full backend test: run this file directly
if __name__ == "__main__":
    d = lambda days: (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    # ---- Session 1: first time using the app ----
    db = Database("test_dashboard_check.db")
    user = User(db)
    print("1. Register ->", user.register("symon@gmail.com", "Symon Cortez", "secret1", "secret1"))
    print("2. Login    ->", user.login("symon@gmail.com", "secret1"))

    tasks = TaskManager(db, user.id)
    sched = ScheduleManager(db, user.id)
    tasks.add_task("Finish Research Paper", "Methodology", d(-2), "08:00", "School")
    tasks.add_task("Study for Midterms", "Chapters 4-7", d(0), "13:00", "School")
    tasks.add_task("Buy Groceries", "Milk, eggs", d(0), "17:00", "Personal")
    tasks.add_task("Submit Assignment 3", "Before midnight", d(1), "23:00", "Important")
    tasks.add_task("Team Meeting", "", d(3), "15:00", "Work")
    tasks.toggle_task(1)
    tasks.toggle_task(2)
    sched.add_schedule("Biology Lecture", "Room 204", d(0), "10:00", "School")
    sched.add_schedule("Study Session", "Library", d(0), "13:00", "School")
    sched.add_schedule("Workout", "Sports complex", d(1), "16:00", "Health")

    summary = Dashboard(db, user).get_summary()
    print("3. Dashboard (session 1):")
    print("  ", summary["greeting"] + ",", summary["name"] + "!", "-", summary["today"])
    print("   Progress ring   :", summary["completed_count"], "of", summary["total_tasks"], "done")
    print("   Active:", summary["active_count"], "| Overdue:", summary["overdue_count"])
    print("  ", summary["task_list_title"], ":", [t.title for t in summary["task_list"]])
    print("   Upcoming        :", [f"{s.date} {s.time_display} {s.title}" for s in summary["upcoming_schedules"]])

    # ---- Session 2: simulate closing and reopening the app ----
    del db, user, tasks, sched
    db2 = Database("test_dashboard_check.db")
    user2 = User(db2)
    print("4. Login again (new session) ->", user2.login("symon@gmail.com", "secret1"))
    summary2 = Dashboard(db2, user2).get_summary()
    print("5. Data still saved? Ring =", summary2["completed_count"], "of", summary2["total_tasks"],
          "| upcoming =", len(summary2["upcoming_schedules"]))
    print("   Same as before?", summary2["total_tasks"] == summary["total_tasks"]
          and summary2["completed_count"] == summary["completed_count"])

    # ---- Empty account: new user with nothing yet ----
    User(db2).register("newbie", "New User", "secret3", "secret3")
    newbie = User(db2)
    newbie.login("newbie", "secret3")
    empty = Dashboard(db2, newbie).get_summary()
    print("6. New user dashboard ->", empty["completed_count"], "of", empty["total_tasks"],
          "| list:", empty["task_list_title"], empty["task_list"], "| upcoming:", empty["upcoming_schedules"])

    # ---- Cascade: deleting a user removes their data ----
    db2.execute("DELETE FROM users WHERE id = ?", (user2.id,))
    left = db2.fetch_one("SELECT COUNT(*) AS n FROM tasks")["n"]
    left2 = db2.fetch_one("SELECT COUNT(*) AS n FROM schedules")["n"]
    print("7. After deleting the user, tasks left =", left, "| schedules left =", left2)

    os.remove(db2.db_path)
    print("Dashboard OK - backend complete, test database removed.")