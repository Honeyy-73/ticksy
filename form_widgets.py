"""
form_widgets.py
Widgets used by the Tasks, Schedule and Add/Edit screens: search box, floating
"+" button, date and time pickers, category chips, and the confirm / success
pop-ups.
"""

import calendar
from datetime import datetime

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from theme import (
    CATEGORY_COLORS, LAVENDER, MUTED, PURPLE_MID, RED, TEXT, WHITE,
    RoundedButton, Text, rgba, short,
)
from validators import CATEGORIES, format_time_12h
from widgets import Card

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


# ---------------------------------------------------------------------------
# Search box and floating "+" button
# ---------------------------------------------------------------------------
class SearchBox(BoxLayout):
    """A translucent rounded search field for the purple header."""

    def __init__(self, hint, on_text, **kwargs):
        super().__init__(size_hint_y=None, height=dp(42), padding=[dp(14), 0], **kwargs)
        with self.canvas.before:
            self._fill = Color(1, 1, 1, 0.16)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.input = TextInput(
            hint_text=hint, multiline=False, write_tab=False,
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=(1, 1, 1, 1), hint_text_color=(1, 1, 1, 0.55),
            cursor_color=(1, 1, 1, 1), font_size=sp(14),
            padding=[0, dp(11), 0, dp(9)],
        )
        self.input.bind(text=lambda instance, value: on_text(value))
        self.input.bind(focus=self._on_focus)
        self.add_widget(self.input)

    @property
    def text(self):
        return self.input.text

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _on_focus(self, instance, focused):
        Animation.cancel_all(self._fill)
        Animation(a=0.26 if focused else 0.16, duration=0.18).start(self._fill)


# soft purple glow under the + button: (opacity, spread, drop) in dp
FAB_SHADOW = ((0.05, 8, 5), (0.07, 5, 3.5), (0.10, 2.5, 2))


class FabButton(ButtonBehavior, Widget):
    """The round purple '+' button that floats at the bottom right."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(56), dp(56)))
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, state=self._draw)
        self._draw()

    def _draw(self, *args):
        """Redraw from scratch so the circle and the + can never get out of sync."""
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        cx, cy = self.center
        arm = w * 0.2
        fill = "#5E2F94" if self.state == "down" else PURPLE_MID
        with self.canvas:
            for alpha, spread, drop in FAB_SHADOW:
                grow = dp(spread)
                Color(0.36, 0.18, 0.56, alpha)
                Ellipse(pos=(x - grow, y - grow - dp(drop)),
                        size=(w + 2 * grow, h + 2 * grow))
            Color(*rgba(fill))
            Ellipse(pos=self.pos, size=self.size)
            Color(1, 1, 1, 1)
            Line(points=[cx - arm, cy, cx + arm, cy], width=dp(2.2), cap="round")
            Line(points=[cx, cy - arm, cx, cy + arm], width=dp(2.2), cap="round")


# ---------------------------------------------------------------------------
# Pop-up dialogs
# ---------------------------------------------------------------------------
class BaseDialog(ModalView):
    """A dimmed background with a rounded white card in the middle."""

    def __init__(self, height, **kwargs):
        super().__init__(size_hint=(0.86, None), height=height, background="",
                         background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.5),
                         **kwargs)
        self.card = Card(orientation="vertical", padding=dp(20), spacing=dp(10), radius=22)
        self.add_widget(self.card)


class ConfirmDialog(BaseDialog):
    """'Delete this item?' with Cancel and Delete buttons."""

    def __init__(self, title, message, on_confirm, confirm_text="Delete", **kwargs):
        super().__init__(height=dp(190), **kwargs)
        self.on_confirm = on_confirm
        self.card.add_widget(Text(text=title, bold=True, font_size=sp(17), halign="center"))
        self.card.add_widget(Text(text=message, font_size=sp(12), color=rgba(MUTED),
                                  halign="center"))
        self.card.add_widget(Widget())

        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel = RoundedButton(text="Cancel", bg=LAVENDER, text_color=PURPLE_MID,
                               font_size=sp(14))
        confirm = RoundedButton(text=confirm_text, bg=RED, font_size=sp(14))
        cancel.bind(on_release=lambda *a: self.dismiss())
        confirm.bind(on_release=self._confirm)
        buttons.add_widget(cancel)
        buttons.add_widget(confirm)
        self.card.add_widget(buttons)

    def _confirm(self, *args):
        self.dismiss()
        self.on_confirm()


class SuccessMark(Widget):
    """A purple circle with a white check, for the 'Task Created!' pop-up."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(64), dp(64)))
        super().__init__(**kwargs)
        with self.canvas:
            Color(*rgba(PURPLE_MID))
            self._circle = Ellipse()
            Color(1, 1, 1, 1)
            self._check = Line(points=[0, 0, 0, 0, 0, 0], width=dp(3),
                               cap="round", joint="round")
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        x, y = self.pos
        w, h = self.size
        self._circle.pos = self.pos
        self._circle.size = self.size
        self._check.points = [x + w * 0.28, y + h * 0.52, x + w * 0.43, y + h * 0.36,
                              x + w * 0.72, y + h * 0.66]


def show_success(title, message, on_done, delay=1.2):
    """Show a small 'saved' pop-up, then close it and call on_done."""
    dialog = BaseDialog(height=dp(200), auto_dismiss=False)
    dialog.card.spacing = dp(8)
    dialog.card.add_widget(Widget())
    holder = BoxLayout(size_hint_y=None, height=dp(64))
    holder.add_widget(Widget())
    holder.add_widget(SuccessMark())
    holder.add_widget(Widget())
    dialog.card.add_widget(holder)
    dialog.card.add_widget(Text(text=title, bold=True, font_size=sp(17), halign="center"))
    dialog.card.add_widget(Text(text=message, font_size=sp(12), color=rgba(MUTED),
                                halign="center"))
    dialog.card.add_widget(Widget())

    def finish(dt):
        dialog.dismiss()
        on_done()

    dialog.open()
    Clock.schedule_once(finish, delay)


# ---------------------------------------------------------------------------
# Date and time pickers
# ---------------------------------------------------------------------------
class StepperColumn(BoxLayout):
    """One spinner column: [+] on top, the value, [-] below. Wraps around."""

    def __init__(self, values, index=0, fmt=str, on_change=None, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), **kwargs)
        self.values = list(values)
        self.index = index
        self.fmt = fmt
        self.on_change = on_change

        up = RoundedButton(text="+", bg=LAVENDER, text_color=PURPLE_MID, radius=10,
                           size_hint_y=None, height=dp(40))
        down = RoundedButton(text="-", bg=LAVENDER, text_color=PURPLE_MID, radius=10,
                             size_hint_y=None, height=dp(40))
        self.label = Label(font_size=sp(18), bold=True, color=rgba(TEXT))
        up.bind(on_release=lambda *a: self.step(1))
        down.bind(on_release=lambda *a: self.step(-1))
        self.add_widget(up)
        self.add_widget(self.label)
        self.add_widget(down)
        self._show()

    @property
    def value(self):
        return self.values[self.index]

    def set_values(self, values, index):
        self.values = list(values)
        self.index = max(0, min(index, len(self.values) - 1))
        self._show()

    def step(self, delta):
        self.index = (self.index + delta) % len(self.values)
        self._show()
        if self.on_change:
            self.on_change()

    def _show(self):
        self.label.text = str(self.fmt(self.value))


class PickerDialog(BaseDialog):
    """Title, a row of StepperColumns, and Cancel / OK buttons."""

    def __init__(self, title, columns, on_ok, **kwargs):
        super().__init__(height=dp(290), **kwargs)
        self._on_ok = on_ok
        self.card.add_widget(Text(text=title, bold=True, font_size=sp(16)))
        row = BoxLayout(spacing=dp(10))
        for column in columns:
            row.add_widget(column)
        self.card.add_widget(row)

        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel = RoundedButton(text="Cancel", bg=LAVENDER, text_color=PURPLE_MID,
                               font_size=sp(14))
        ok = RoundedButton(text="OK", font_size=sp(14))
        cancel.bind(on_release=lambda *a: self.dismiss())
        ok.bind(on_release=self._ok)
        buttons.add_widget(cancel)
        buttons.add_widget(ok)
        self.card.add_widget(buttons)

    def _ok(self, *args):
        self.dismiss()
        self._on_ok()


class DatePickerDialog(PickerDialog):
    """Month / Day / Year spinners. Gives back 'YYYY-MM-DD'."""

    def __init__(self, current, on_pick, **kwargs):
        today = datetime.now().date()
        try:
            chosen = datetime.strptime(current, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            chosen = today
        years = list(range(min(chosen.year, today.year - 1),
                           max(chosen.year, today.year + 10) + 1))
        days_in_month = calendar.monthrange(chosen.year, chosen.month)[1]

        month = StepperColumn(MONTHS, chosen.month - 1, size_hint_x=1.2)
        day = StepperColumn(range(1, days_in_month + 1), chosen.day - 1,
                            fmt=lambda d: f"{d:02d}")
        year = StepperColumn(years, years.index(chosen.year), size_hint_x=1.4)
        super().__init__("Pick a date", [month, day, year], lambda: self._pick(), **kwargs)

        self.month_column, self.day_column, self.year_column = month, day, year
        self.on_pick = on_pick
        month.on_change = year.on_change = self._fix_days

    def _fix_days(self):
        """Keep the day valid when the month or year changes (e.g. Feb 30)."""
        days_in_month = calendar.monthrange(
            self.year_column.value, self.month_column.index + 1)[1]
        if len(self.day_column.values) != days_in_month:
            keep = min(self.day_column.value, days_in_month)
            self.day_column.set_values(range(1, days_in_month + 1), keep - 1)

    def _pick(self):
        self.on_pick(f"{self.year_column.value:04d}-{self.month_column.index + 1:02d}-"
                     f"{self.day_column.value:02d}")


class TimePickerDialog(PickerDialog):
    """Hour / Minute / AM-PM spinners. Gives back 24-hour 'HH:MM'."""

    def __init__(self, current, on_pick, **kwargs):
        try:
            chosen = datetime.strptime(current, "%H:%M")
        except (ValueError, TypeError):
            chosen = datetime.strptime("09:00", "%H:%M")
        hour12 = chosen.hour % 12 or 12

        hour = StepperColumn(range(1, 13), hour12 - 1, fmt=lambda h: f"{h:02d}")
        minute = StepperColumn(range(60), chosen.minute, fmt=lambda m: f"{m:02d}")
        meridiem = StepperColumn(("AM", "PM"), 1 if chosen.hour >= 12 else 0)
        super().__init__("Pick a time", [hour, minute, meridiem], lambda: self._pick(), **kwargs)

        self.hour_column, self.minute_column, self.meridiem_column = hour, minute, meridiem
        self.on_pick = on_pick

    def _pick(self):
        hour24 = self.hour_column.value % 12
        if self.meridiem_column.value == "PM":
            hour24 += 12
        self.on_pick(f"{hour24:02d}:{self.minute_column.value:02d}")


class _PressBox(ButtonBehavior, BoxLayout):
    """A box that can be tapped."""


class PickerField(BoxLayout):
    """Looks like LabeledInput, but tapping it opens a date or time picker.
    .text always holds the raw value ('YYYY-MM-DD' or 'HH:MM')."""

    def __init__(self, caption, kind, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(76), spacing=dp(6), **kwargs)
        self.kind = kind
        self._value = ""

        self.caption = Text(text=caption.upper(), font_size=sp(11), bold=True,
                            color=rgba(MUTED))
        self.add_widget(self.caption)

        self.box = _PressBox(size_hint_y=None, height=dp(48), padding=[dp(14), 0])
        with self.box.canvas.before:
            Color(*rgba("#F8F3FA"))
            self._bg = RoundedRectangle(pos=self.box.pos, size=self.box.size,
                                        radius=[dp(12)])
            Color(*rgba("#E8DDF0"))
            self._border = Line(rounded_rectangle=(0, 0, 10, 10, dp(12)), width=1)

        self.display = Label(halign="left", valign="middle", font_size=sp(15),
                             color=rgba(TEXT))
        self.display.bind(size=lambda inst, size: setattr(inst, "text_size", size))
        self.box.add_widget(self.display)
        self.add_widget(self.box)

        self.box.bind(pos=self._redraw, size=self._redraw)
        self.box.bind(on_release=self.open_picker)
        self._show()

    @property
    def text(self):
        return self._value

    @text.setter
    def text(self, value):
        self._value = value or ""
        self._show()

    def _show(self):
        if not self._value:
            self.display.text = "Select"
            self.display.color = rgba("#B9A6BC")
            return
        self.display.color = rgba(TEXT)
        try:
            if self.kind == "date":
                self.display.text = datetime.strptime(self._value, "%Y-%m-%d").strftime("%b %d, %Y")
            else:
                self.display.text = format_time_12h(self._value)
        except ValueError:
            self.display.text = self._value

    def _redraw(self, *args):
        x, y = self.box.pos
        w, h = self.box.size
        self._bg.pos = (x, y)
        self._bg.size = (w, h)
        self._border.rounded_rectangle = (x, y, w, h, dp(12))

    def open_picker(self, *args):
        dialog_class = DatePickerDialog if self.kind == "date" else TimePickerDialog
        dialog_class(self._value, self._picked).open()

    def _picked(self, value):
        self.text = value


# ---------------------------------------------------------------------------
# Category chips
# ---------------------------------------------------------------------------
class CategoryChip(ButtonBehavior, Label):
    """One tappable category pill."""

    def __init__(self, category, **kwargs):
        super().__init__(text=category, font_size=sp(12), bold=True, **kwargs)
        self.category = category
        self.selected = False
        self._light, self._dark = CATEGORY_COLORS[category]
        with self.canvas.before:
            self._fill = Color(*rgba("#F8F3FA"))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self._update, size=self._update)
        self.set_selected(False)

    def set_selected(self, selected):
        self.selected = selected
        self._fill.rgba = rgba(self._dark if selected else self._light)
        self.color = rgba(WHITE if selected else self._dark)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class CategoryChips(GridLayout):
    """School / Personal / Important / Work / Health - pick exactly one."""

    def __init__(self, **kwargs):
        super().__init__(cols=3, spacing=dp(8), size_hint_y=None, height=dp(76), **kwargs)
        self.chips = {}
        for category in CATEGORIES:
            chip = CategoryChip(category, size_hint_y=None, height=dp(34))
            chip.bind(on_release=lambda instance: self.select(instance.category))
            self.chips[category] = chip
            self.add_widget(chip)
        self.value = CATEGORIES[1]
        self.select(self.value)

    def select(self, category):
        self.value = category
        for name, chip in self.chips.items():
            chip.set_selected(name == category)