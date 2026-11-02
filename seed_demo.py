"""
seed_demo.py
OPTIONAL helper: adds sample tasks and schedules to an account so you can
see a filled-in dashboard before the Add forms are built.
Run it once with the Run button, then type your email/username.
"""

from datetime import datetime, timedelta

from database import Database
from schedule import ScheduleManager
from task import TaskManager


def day(offset):
    return (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")


db = Database()
login_id = input("Type the email/username you signed up with: ").strip()
row = db.fetch_one("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (login_id,))

if row is None:
    print("No account found with that name. Sign up in the app first.")
else:
    tasks = TaskManager(db, row["id"])
    schedules = ScheduleManager(db, row["id"])
    if tasks.count_tasks() or schedules.get_schedules():
        print("That account already has data, so nothing was added.")
    else:
        tasks.add_task("Finish Research Paper", "Methodology section", day(0), "08:00", "School")
        tasks.add_task("Study for Midterms", "Chapters 4-7", day(0), "13:00", "School")
        tasks.add_task("Buy Groceries", "Milk, eggs, bread", day(0), "17:00", "Personal")
        tasks.add_task("Submit Assignment 3", "Before midnight", day(1), "23:00", "Important")
        tasks.add_task("Team Project Meeting", "Zoom call", day(3), "15:00", "Work")
        tasks.toggle_task(1)
        tasks.toggle_task(2)
        schedules.add_schedule("Biology Lecture", "Room 204, Main Building", day(0), "10:00", "School")
        schedules.add_schedule("Study Session", "Library, Room B", day(1), "13:00", "School")
        schedules.add_schedule("Workout", "Sports complex", day(2), "16:00", "Health")
        print("Done! Sample data added. Run main.py and log in.")