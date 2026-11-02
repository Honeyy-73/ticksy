"""
widgets.py
Widgets shared by the main screens: cards, category badges, task rows,
schedule cards, progress ring, bottom navigation, and the MainScreen layout.
"""

from datetime import datetime

from kivy.animation import Animation
from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import escape_markup

from theme import (
    BG, CATEGORY_COLORS, LAVENDER, MUTED, PINK, PURPLE, PURPLE_MID, RED, TEXT, WHITE,
    RoundedButton, Text, make_scroll_body, rgba, short,
)
from validators import format_date_friendly


# Soft layered shadow: (opacity, spread, drop) in dp. Biggest and faintest first.
SHADOW_LAYERS = ((0.025, 5, 4), (0.035, 3, 3), (0.045, 1.2, 1.5))


class Card(BoxLayout):
    """A box with a rounded colored background (and an optional soft shadow)."""

    def __init__(self, bg=WHITE, radius=16, shadow=False, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        self._shadows = []
        with self.canvas.before:
            if shadow:
                for alpha, spread, drop in SHADOW_LAYERS:
                    Color(0.17, 0.06, 0.25, alpha)
                    self._shadows.append(
                        RoundedRectangle(radius=[self._radius + dp(spread)]))
            Color(*rgba(bg))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[self._radius])
        self.bind(pos=self._update_bg, size=self._update_bg)
        self._update_bg()

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        x, y = self.pos
        w, h = self.size
        for rect, (alpha, spread, drop) in zip(self._shadows, SHADOW_LAYERS):
            grow = dp(spread)
            rect.pos = (x - grow, y - grow - dp(drop))
            rect.size = (w + 2 * grow, h + 2 * grow)


class CategoryBadge(Label):
    """The small colored pill that shows School / Personal / Work..."""

    def __init__(self, category, **kwargs):
        background, foreground = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Personal"])
        super().__init__(text=category, font_size=sp(10), bold=True,
                         color=rgba(foreground), size_hint=(None, None), **kwargs)
        with self.canvas.before:
            Color(*rgba(background))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(texture_size=self._fit, pos=self._update_bg, size=self._update_bg)
        self.texture_update()
        self._fit()

    def _fit(self, *args):
        self.size = (self.texture_size[0] + dp(20), dp(22))

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class CheckCircle(ButtonBehavior, Widget):
    """The round tick box. Empty circle = active, purple with a check = done."""

    def __init__(self, checked=False, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(34), dp(34)))
        super().__init__(**kwargs)
        self.checked = checked
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        diameter = dp(24)
        cx, cy = self.center
        with self.canvas:
            if self.checked:
                Color(*rgba(PURPLE_MID))
                Ellipse(pos=(cx - diameter / 2, cy - diameter / 2), size=(diameter, diameter))
                Color(1, 1, 1, 1)
                Line(points=[cx - diameter * 0.22, cy, cx - diameter * 0.05, cy - diameter * 0.18,
                             cx + diameter * 0.25, cy + diameter * 0.2],
                     width=dp(2), cap="round", joint="round")
            else:
                Color(*rgba("#D9C7E6"))
                Line(circle=(cx, cy, diameter / 2), width=dp(1.6))


class TaskRow(Card):
    """One task: tick box, title, date and time, and a category badge."""

    def __init__(self, task, on_toggle, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(66),
                         padding=[dp(8), dp(8), dp(12), dp(8)], spacing=dp(6), **kwargs)
        self.task = task

        check_holder = AnchorLayout(size_hint_x=None, width=dp(40))
        check = CheckCircle(checked=task.completed)
        check.bind(on_release=lambda *a: on_toggle(task))
        check_holder.add_widget(check)
        self.add_widget(check_holder)

        info = BoxLayout(orientation="vertical", spacing=dp(2), padding=[0, dp(6), 0, dp(6)])
        title = escape_markup(short(task.title, 22))
        if task.completed:
            title = "[s]" + title + "[/s]"
        info.add_widget(Text(text=title, markup=True, bold=True, font_size=sp(14),
                             color=rgba(MUTED if task.completed else TEXT)))
        when = f"{format_date_friendly(task.date)}  \u2022  {task.time_display}"
        overdue = task.is_overdue()
        info.add_widget(Text(text=when + ("  \u2022  Overdue" if overdue else ""),
                             font_size=sp(11), color=rgba(RED if overdue else MUTED)))
        self.add_widget(info)

        badge_holder = AnchorLayout(anchor_x="right", anchor_y="center",
                                    size_hint_x=None, width=dp(82))
        badge_holder.add_widget(CategoryBadge(task.category))
        self.add_widget(badge_holder)


class ScheduleCard(Card):
    """One schedule on a purple card: day tile, title, date and time, badge."""

    def __init__(self, schedule, **kwargs):
        super().__init__(bg=PURPLE_MID, orientation="horizontal", size_hint_y=None,
                         height=dp(72), padding=dp(12), spacing=dp(12), **kwargs)
        self.schedule = schedule

        day, month = "--", ""
        try:
            parsed = datetime.strptime(schedule.date, "%Y-%m-%d")
            day, month = str(parsed.day), parsed.strftime("%b").upper()
        except ValueError:
            pass

        tile_holder = AnchorLayout(size_hint_x=None, width=dp(46))
        tile = Card(bg="#9460C8", radius=12, size_hint=(None, None), size=(dp(46), dp(46)))
        tile.add_widget(Label(text=f"[b]{day}[/b]\n{month}", markup=True, halign="center",
                              font_size=sp(11), color=rgba(WHITE)))
        tile_holder.add_widget(tile)
        self.add_widget(tile_holder)

        info = BoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(Text(text=escape_markup(short(schedule.title, 24)), markup=True,
                             bold=True, font_size=sp(14), color=rgba(WHITE)))
        info.add_widget(Text(text=f"{format_date_friendly(schedule.date)}  \u2022  {schedule.time_display}",
                             font_size=sp(11), color=(1, 1, 1, 0.75)))
        self.add_widget(info)

        badge_holder = AnchorLayout(anchor_x="right", anchor_y="center",
                                    size_hint_x=None, width=dp(82))
        badge_holder.add_widget(CategoryBadge(schedule.category))
        self.add_widget(badge_holder)


def make_section_header(title, on_see_all):
    """A heading on the left and a small 'See all' button on the right."""
    row = BoxLayout(size_hint_y=None, height=dp(34))
    row.add_widget(Text(text=title, font_size=sp(15), bold=True, size_hint_y=1))
    holder = AnchorLayout(anchor_x="right", anchor_y="center", size_hint_x=None, width=dp(76))
    button = RoundedButton(text="See all", bg=LAVENDER, text_color=PURPLE_MID, radius=10,
                           font_size=sp(11), size_hint=(None, None), size=(dp(70), dp(28)))
    button.bind(on_release=on_see_all)
    holder.add_widget(button)
    row.add_widget(holder)
    return row


def make_empty_state(message):
    box = BoxLayout(size_hint_y=None, height=dp(56))
    box.add_widget(Text(text=message, halign="center", font_size=sp(12),
                        color=rgba(MUTED), size_hint_y=1))
    return box


class ProgressRing(Widget):
    """The ring on the dashboard: how many tasks are done out of all tasks."""

    shown = NumericProperty(0)  # fraction (0..1) currently drawn; animated

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(132), dp(132)))
        super().__init__(**kwargs)
        self.done = 0
        self.total = 0
        with self.canvas:
            Color(1, 1, 1, 0.18)
            self._track = Line(circle=(0, 0, 10, 0, 360), width=dp(8))
            self._arc_color = Color(*rgba(PINK))
            self._arc = Line(circle=(0, 0, 10, 0, 1), width=dp(8), cap="round")

        self.count_label = Label(text="0", font_size=sp(36), bold=True,
                                 color=(1, 1, 1, 1), size_hint=(None, None))
        self.sub_label = Label(text="of 0 done", font_size=sp(11),
                               color=(1, 1, 1, 0.7), size_hint=(None, None))
        self.add_widget(self.count_label)
        self.add_widget(self.sub_label)
        self.count_label.texture_update()
        self.sub_label.texture_update()
        self.bind(pos=self._update, size=self._update, shown=self._update)
        self._update()

    def set_progress(self, done, total):
        self.done, self.total = done, total
        self.count_label.text = str(done)
        self.sub_label.text = f"of {total} done"
        self.count_label.texture_update()
        self.sub_label.texture_update()
        # glide the ring to its new value instead of jumping
        Animation.cancel_all(self, "shown")
        target = (done / total) if total else 0
        Animation(shown=target, duration=0.6, t="out_cubic").start(self)
        self._update()

    def _update(self, *args):
        cx, cy = self.center
        radius = min(self.width, self.height) / 2 - dp(8)
        self._track.circle = (cx, cy, radius, 0, 360)

        fraction = self.shown
        self._arc_color.a = 1 if fraction > 0.002 else 0
        self._arc.circle = (cx, cy, radius, 0, max(fraction * 360, 1))

        self.count_label.size = self.count_label.texture_size
        self.sub_label.size = self.sub_label.texture_size
        self.count_label.center = (cx, cy + dp(8))
        self.sub_label.center = (cx, cy - dp(20))


class BottomNav(BoxLayout):
    """Home / Tasks / Schedule bar at the bottom of every main screen."""

    TABS = (("dashboard", "Home"), ("tasks", "Tasks"), ("schedule", "Schedule"))

    def __init__(self, active, **kwargs):
        super().__init__(size_hint_y=None, height=dp(84),
                         padding=[dp(16), dp(6), dp(16), dp(16)], **kwargs)
        bar = Card(bg=WHITE, radius=24, orientation="horizontal",
                   padding=dp(6), spacing=dp(6), shadow=True)
        for name, label in self.TABS:
            is_active = name == active
            button = RoundedButton(
                text=label, bg=LAVENDER if is_active else WHITE,
                text_color=PURPLE_MID if is_active else MUTED,
                radius=18, font_size=sp(13))
            button.bind(on_release=lambda instance, target=name: App.get_running_app().go(target))
            bar.add_widget(button)
        self.add_widget(bar)


class MainScreen(Screen):
    """Layout for Home, Tasks and Schedule: purple header, light sheet, bottom nav."""

    def __init__(self, active_tab, hero_height, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*rgba(PURPLE))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        root = BoxLayout(orientation="vertical")
        self.hero = BoxLayout(orientation="vertical", size_hint_y=None, height=hero_height,
                              padding=[dp(22), dp(16), dp(22), dp(6)], spacing=dp(6))
        root.add_widget(self.hero)

        # The light sheet. Its rounded shape is drawn below the window edge
        # so that only the top corners look rounded.
        sheet = BoxLayout(orientation="vertical")
        with sheet.canvas.before:
            Color(*rgba(BG))
            self._sheet_bg = RoundedRectangle(pos=sheet.pos, size=sheet.size, radius=[dp(28)])
        sheet.bind(pos=self._update_sheet, size=self._update_sheet)

        scroll, self.body = make_scroll_body([dp(18), dp(20), dp(18), dp(10)], dp(10))
        sheet.add_widget(scroll)
        sheet.add_widget(BottomNav(active_tab))
        root.add_widget(sheet)
        self.add_widget(root)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _update_sheet(self, sheet, *args):
        extra = dp(40)
        self._sheet_bg.pos = (sheet.x, sheet.y - extra)
        self._sheet_bg.size = (sheet.width, sheet.height + extra)

    def set_simple_hero(self, title, subtitle):
        """A plain purple header with a title (used by Tasks and Schedule)."""
        self.hero.add_widget(Text(text=title, font_size=sp(22), bold=True, color=rgba(WHITE)))
        self.hero.add_widget(Text(text=subtitle, font_size=sp(12), color=(1, 1, 1, 0.65)))