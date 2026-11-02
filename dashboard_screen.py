"""
dashboard_screen.py
The Home screen: greeting, progress ring, today's tasks, and upcoming schedules.
All the numbers come from the Dashboard class in dashboard.py.
"""

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout

from dashboard import Dashboard
from task import TaskManager
from theme import PINK, PURPLE_MID, WHITE, LogoMark, RoundedButton, Text, rgba
from widgets import (
    MainScreen, ProgressRing, ScheduleCard, TaskRow, make_empty_state,
    make_section_header,
)


class DashboardScreen(MainScreen):
    def __init__(self, **kwargs):
        super().__init__(active_tab="dashboard", hero_height=dp(300), **kwargs)

        # --- header row: greeting on the left, logo + logout on the right ---
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(100))
        left = BoxLayout(orientation="vertical")
        self.date_label = Text(text="", font_size=sp(11), color=(1, 1, 1, 0.65))
        self.greeting_label = Text(text="Good Morning,", font_size=sp(22), bold=True,
                                   color=rgba(WHITE))
        self.name_label = Text(text="", font_size=sp(22), bold=True, color=rgba(PINK))
        self.sub_label = Text(text="Let's get things done.", font_size=sp(12),
                              color=(1, 1, 1, 0.65))
        for label in (self.date_label, self.greeting_label, self.name_label, self.sub_label):
            left.add_widget(label)
        header.add_widget(left)

        right = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(78),
                          spacing=dp(8))
        logo_holder = AnchorLayout(anchor_x="right", anchor_y="top",
                                   size_hint_y=None, height=dp(48))
        logo_holder.add_widget(LogoMark(size=(dp(44), dp(44))))
        right.add_widget(logo_holder)
        logout = RoundedButton(text="Logout", bg=PURPLE_MID, radius=10, font_size=sp(11),
                               size_hint=(1, None), height=dp(28))
        logout.bind(on_release=self.do_logout)
        right.add_widget(logout)
        header.add_widget(right)
        self.hero.add_widget(header)

        # --- progress ring ---
        ring_holder = AnchorLayout(anchor_x="center", anchor_y="center",
                                   size_hint_y=None, height=dp(140))
        self.ring = ProgressRing()
        ring_holder.add_widget(self.ring)
        self.hero.add_widget(ring_holder)
        self.hero.add_widget(Text(text="Tasks Completed", font_size=sp(12), bold=True,
                                  color=(1, 1, 1, 0.75), halign="center"))

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        """Read fresh numbers from the database and redraw the screen."""
        app = App.get_running_app()
        if not app.user.is_logged_in():
            return

        summary = Dashboard(app.db, app.user).get_summary()
        self.date_label.text = summary["today"]
        self.greeting_label.text = summary["greeting"] + ","
        self.name_label.text = summary["name"] + "!"
        self.ring.set_progress(summary["completed_count"], summary["total_tasks"])

        self.body.clear_widgets()
        self.body.add_widget(make_section_header(
            summary["task_list_title"], lambda *a: app.go("tasks")))
        if summary["task_list"]:
            for task in summary["task_list"]:
                self.body.add_widget(TaskRow(task, self.toggle_task, shadow=True))
        else:
            self.body.add_widget(make_empty_state("No tasks yet"))

        self.body.add_widget(make_section_header("Upcoming", lambda *a: app.go("schedule")))
        if summary["upcoming_schedules"]:
            for schedule in summary["upcoming_schedules"]:
                self.body.add_widget(ScheduleCard(schedule))
        else:
            self.body.add_widget(make_empty_state("No upcoming schedules"))

    def toggle_task(self, task):
        """Tick or untick a task, then redraw so the ring updates."""
        app = App.get_running_app()
        TaskManager(app.db, app.user.id).toggle_task(task.id)
        self.refresh()

    def do_logout(self, *args):
        app = App.get_running_app()
        app.user.logout()
        app.go("login")