"""
schedule_screen.py
The Schedule screen: a vertical timeline of schedules (earliest first), each
with Edit and Delete buttons. Talks to ScheduleManager from schedule.py.
"""

from kivy.app import App
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import escape_markup

from form_widgets import ConfirmDialog, FabButton, short
from schedule import ScheduleManager
from task_screens import make_actions_row
from theme import MUTED, PINK, PURPLE_MID, TEXT, WHITE, Text, rgba
from validators import format_date_friendly
from widgets import Card, CategoryBadge, MainScreen, make_empty_state


class TimelineRail(Widget):
    """The left side of a timeline row: the time, a dot, and the line."""

    def __init__(self, time_text, first, last, **kwargs):
        super().__init__(size_hint_x=None, width=dp(66), **kwargs)
        self.first = first
        self.last = last
        with self.canvas:
            Color(*rgba("#D9C7E6"))
            self._line = Line(points=[0, 0, 0, 0], width=dp(1.5))
            Color(*rgba(PINK))
            self._dot = Ellipse(size=(dp(12), dp(12)))
        self.label = Label(text=time_text, font_size=sp(10), bold=True,
                           color=rgba(PURPLE_MID), size_hint=(None, None))
        self.add_widget(self.label)
        self.label.texture_update()
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        cx = self.x + dp(56)  # the line sits 56dp from the left edge
        dot_y = self.top - dp(30)
        top = dot_y if self.first else self.top
        bottom = dot_y if self.last else self.y
        self._line.points = [cx, top, cx, bottom]
        self._dot.pos = (cx - dp(6), dot_y - dp(6))
        self.label.size = self.label.texture_size
        self.label.center = (self.x + dp(27), dot_y)


class TimelineItem(BoxLayout):
    """One schedule: the rail on the left and a white card on the right."""

    def __init__(self, schedule, first, last, on_edit, on_delete, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(124), **kwargs)
        self.add_widget(TimelineRail(schedule.time_display, first, last))

        holder = BoxLayout(padding=[0, 0, 0, dp(10)])
        card = Card(bg=WHITE, orientation="vertical", padding=[dp(12), dp(10), 0, dp(8)],
                    spacing=dp(2), shadow=True)

        # right padding keeps the badge from touching the card edge
        top = BoxLayout(size_hint_y=None, height=dp(24), padding=[0, 0, dp(12), 0])
        top.add_widget(Text(text=escape_markup(short(schedule.title, 24)), markup=True,
                            bold=True, font_size=sp(14), size_hint_y=1))
        badge_holder = AnchorLayout(anchor_x="right", anchor_y="center",
                                    size_hint_x=None, width=dp(82))
        badge_holder.add_widget(CategoryBadge(schedule.category))
        top.add_widget(badge_holder)
        card.add_widget(top)

        card.add_widget(Text(text=format_date_friendly(schedule.date),
                             font_size=sp(11), color=rgba(MUTED)))
        card.add_widget(Text(text=short(schedule.description, 34) or " ",
                             font_size=sp(11), color=rgba(TEXT)))
        card.add_widget(Widget())
        card.add_widget(make_actions_row(lambda *a: on_edit(schedule),
                                         lambda *a: on_delete(schedule)))
        holder.add_widget(card)
        self.add_widget(holder)


class ScheduleScreen(MainScreen):
    def __init__(self, **kwargs):
        super().__init__(active_tab="schedule", hero_height=dp(104), **kwargs)
        self.hero.add_widget(Text(text="Schedule", font_size=sp(22), bold=True,
                                  color=rgba(WHITE)))
        self.summary_label = Text(text="", font_size=sp(12), color=(1, 1, 1, 0.65))
        self.hero.add_widget(self.summary_label)

        self.fab = FabButton(pos_hint={"right": 0.94, "y": 0.15})
        self.fab.bind(on_release=lambda *a: App.get_running_app().open_schedule_form())
        self.add_widget(self.fab)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        if not app.user.is_logged_in():
            return

        manager = ScheduleManager(app.db, app.user.id)
        schedules = manager.get_schedules()
        upcoming = len(manager.get_upcoming(1000))
        self.summary_label.text = f"{len(schedules)} planned  •  {upcoming} upcoming"

        self.body.clear_widgets()
        if not schedules:
            self.body.add_widget(make_empty_state("No schedules yet. Tap + to add one."))
            return

        # One container for the whole timeline, so the line has no gaps.
        timeline = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
        timeline.bind(minimum_height=timeline.setter("height"))
        last_index = len(schedules) - 1
        for index, schedule in enumerate(schedules):
            timeline.add_widget(TimelineItem(
                schedule, index == 0, index == last_index,
                self.edit_schedule, self.ask_delete))
        self.body.add_widget(timeline)
        # extra room so the + button never covers the last card
        self.body.add_widget(Widget(size_hint_y=None, height=dp(56)))

    def edit_schedule(self, schedule):
        App.get_running_app().open_schedule_form(schedule)

    def ask_delete(self, schedule):
        ConfirmDialog("Delete this item?", f"\"{short(schedule.title, 30)}\" will be removed for good.",
                      lambda: self.delete_schedule(schedule)).open()

    def delete_schedule(self, schedule):
        app = App.get_running_app()
        ScheduleManager(app.db, app.user.id).delete_schedule(schedule.id)
        self.refresh()