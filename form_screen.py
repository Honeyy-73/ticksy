"""
form_screen.py
The Create / Edit form shared by Tasks and Schedules.
ItemFormScreen holds the layout; TaskFormScreen and ScheduleFormScreen only
say which manager to call when Save is pressed.
"""

from datetime import datetime

from kivy.app import App
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from form_widgets import CategoryChips, PickerField, show_success
from schedule import ScheduleManager
from task import TaskManager
from theme import (
    LAVENDER, MUTED, PURPLE, PURPLE_MID, WHITE, LabeledInput, MessageLabel,
    RoundedButton, Text, make_scroll_body, rgba,
)


class ItemFormScreen(Screen):
    """Purple header with a back button, white form card, Cancel + Save bar."""

    def __init__(self, noun, back_screen, **kwargs):
        super().__init__(**kwargs)
        self.noun = noun                  # "Task" or "Schedule"
        self.back_screen = back_screen    # where Cancel / Save returns to
        self.editing_id = None

        with self.canvas.before:
            Color(*rgba(PURPLE))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        root = BoxLayout(orientation="vertical")

        # --- header: back button + title ---
        header = BoxLayout(size_hint_y=None, height=dp(96),
                           padding=[dp(18), dp(24), dp(18), dp(10)], spacing=dp(12))
        back = RoundedButton(text="<", bg=PURPLE_MID, radius=12, font_size=sp(18),
                             size_hint=(None, None), size=(dp(38), dp(38)))
        back.bind(on_release=self.cancel)
        header.add_widget(back)
        titles = BoxLayout(orientation="vertical")
        self.title_label = Text(text="", font_size=sp(21), bold=True, color=rgba(WHITE))
        self.sub_label = Text(text="", font_size=sp(12), color=(1, 1, 1, 0.65))
        titles.add_widget(self.title_label)
        titles.add_widget(self.sub_label)
        header.add_widget(titles)
        root.add_widget(header)

        # --- white card ---
        card = BoxLayout(orientation="vertical")
        with card.canvas.before:
            Color(*rgba(WHITE))
            self._card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(28)])
        card.bind(pos=self._update_card, size=self._update_card)

        scroll, self.body = make_scroll_body([dp(24), dp(22), dp(24), dp(12)], dp(10))
        card.add_widget(scroll)

        self.message = MessageLabel()
        self.body.add_widget(self.message)
        self.title_field = LabeledInput(f"{noun} Title", f"e.g. {self.example_title()}")
        self.desc_field = LabeledInput("Description", "Optional details")
        self.body.add_widget(self.title_field)
        self.body.add_widget(self.desc_field)

        when_row = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(12))
        self.date_field = PickerField("Date", "date")
        self.time_field = PickerField("Time", "time")
        when_row.add_widget(self.date_field)
        when_row.add_widget(self.time_field)
        self.body.add_widget(when_row)

        self.body.add_widget(Text(text="CATEGORY", font_size=sp(11), bold=True,
                                  color=rgba(MUTED)))
        self.chips = CategoryChips()
        self.body.add_widget(self.chips)

        # --- bottom bar ---
        bar = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(12),
                        padding=[dp(24), dp(10), dp(24), dp(14)])
        cancel = RoundedButton(text="Cancel", bg=LAVENDER, text_color=PURPLE_MID,
                               font_size=sp(14))
        cancel.bind(on_release=self.cancel)
        self.save_button = RoundedButton(text="Save", font_size=sp(14))
        self.save_button.bind(on_release=self.save)
        bar.add_widget(cancel)
        bar.add_widget(self.save_button)
        card.add_widget(bar)

        root.add_widget(card)
        self.add_widget(root)

        self.title_field.input.bind(
            on_text_validate=lambda *a: setattr(self.desc_field.input, "focus", True))

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _update_card(self, card, *args):
        extra = dp(40)
        self._card_bg.pos = (card.x, card.y - extra)
        self._card_bg.size = (card.width, card.height + extra)

    # ---------- things the subclasses fill in ----------
    def example_title(self):
        return "Finish research paper"

    def save_item(self, title, description, date, time, category):
        """Add or update through the right manager. Returns (success, message)."""
        raise NotImplementedError

    # ---------- opening the form ----------
    def open_new(self):
        """Blank form for a new item."""
        self.editing_id = None
        self.title_label.text = f"Create {self.noun}"
        self.sub_label.text = "Fill in the details below."
        self.save_button.text = f"Create {self.noun}"
        self.title_field.text = ""
        self.desc_field.text = ""
        self.date_field.text = datetime.now().strftime("%Y-%m-%d")
        self.time_field.text = "09:00"
        self.chips.select("Personal")
        self.message.clear()

    def open_edit(self, item):
        """Form filled with an existing task or schedule."""
        self.editing_id = item.id
        self.title_label.text = f"Edit {self.noun}"
        self.sub_label.text = "Change the details below."
        self.save_button.text = f"Update {self.noun}"
        self.title_field.text = item.title
        self.desc_field.text = item.description or ""
        self.date_field.text = item.date
        self.time_field.text = item.time
        self.chips.select(item.category)
        self.message.clear()

    def on_pre_enter(self, *args):
        self.save_button.disabled = False

    # ---------- buttons ----------
    def cancel(self, *args):
        App.get_running_app().go(self.back_screen)

    def save(self, *args):
        self.message.clear()
        ok, message = self.save_item(
            self.title_field.text, self.desc_field.text, self.date_field.text,
            self.time_field.text, self.chips.value)
        if not ok:
            self.message.show(message)
            return

        self.save_button.disabled = True
        word = "Updated" if self.editing_id else "Created"
        show_success(f"{self.noun} {word}!", message,
                     lambda: App.get_running_app().go(self.back_screen))


class TaskFormScreen(ItemFormScreen):
    def __init__(self, **kwargs):
        super().__init__("Task", "tasks", **kwargs)

    def save_item(self, title, description, date, time, category):
        app = App.get_running_app()
        manager = TaskManager(app.db, app.user.id)
        if self.editing_id:
            return manager.update_task(self.editing_id, title, description, date, time, category)
        return manager.add_task(title, description, date, time, category)


class ScheduleFormScreen(ItemFormScreen):
    def __init__(self, **kwargs):
        super().__init__("Schedule", "schedule", **kwargs)

    def example_title(self):
        return "Biology lecture"

    def save_item(self, title, description, date, time, category):
        app = App.get_running_app()
        manager = ScheduleManager(app.db, app.user.id)
        if self.editing_id:
            return manager.update_schedule(self.editing_id, title, description, date, time, category)
        return manager.add_schedule(title, description, date, time, category)