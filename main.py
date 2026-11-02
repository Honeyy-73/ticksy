"""
main.py
Start the Ticksy app by running this file.
"""

from kivy.config import Config

# Phone-sized window. These must be set before the rest of Kivy is imported.
Config.set("graphics", "width", "380")
Config.set("graphics", "height", "640")
Config.set("input", "mouse", "mouse,multitouch_on_demand")  # no red dots on right-click

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from auth_screens import LoginScreen, SignUpScreen, SplashScreen
from dashboard_screen import DashboardScreen
from database import Database
from form_screen import ScheduleFormScreen, TaskFormScreen
from schedule_screen import ScheduleScreen
from task_screens import TasksScreen
from theme import BG, rgba
from user import User


class TicksyApp(App):
    title = "Ticksy"

    def build(self):
        Window.clearcolor = rgba(BG)
        self.db = Database()
        self.user = User(self.db)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self.sm.add_widget(SplashScreen(name="splash"))
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(SignUpScreen(name="signup"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(TasksScreen(name="tasks"))
        self.sm.add_widget(ScheduleScreen(name="schedule"))
        self.sm.add_widget(TaskFormScreen(name="task_form"))
        self.sm.add_widget(ScheduleFormScreen(name="schedule_form"))
        return self.sm

    def go(self, screen_name):
        self.sm.current = screen_name

    def open_task_form(self, task=None):
        """Open the Create Task form (or Edit Task when a task is given)."""
        form = self.sm.get_screen("task_form")
        form.open_edit(task) if task else form.open_new()
        self.go("task_form")

    def open_schedule_form(self, schedule=None):
        """Open the Create Schedule form (or Edit Schedule when one is given)."""
        form = self.sm.get_screen("schedule_form")
        form.open_edit(schedule) if schedule else form.open_new()
        self.go("schedule_form")


if __name__ == "__main__":
    TicksyApp().run()