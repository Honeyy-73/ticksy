"""
task_screens.py
The Daily Tasks screen: search, All / Active / Completed tabs, and a list of
tasks with Edit and Delete buttons. Talks to TaskManager from task.py.
"""

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from form_widgets import ConfirmDialog, FabButton, SearchBox, short
from task import TABS, TaskManager
from theme import LAVENDER, PURPLE_MID, RED, WHITE, RoundedButton, Text, rgba
from widgets import Card, MainScreen, TaskRow, make_empty_state


def make_small_button(text, bg, text_color, on_release):
    """The little Edit / Delete buttons shown under each item."""
    button = RoundedButton(text=text, bg=bg, text_color=text_color, radius=9,
                           font_size=sp(11), size_hint=(None, None),
                           size=(dp(64), dp(26)))
    button.bind(on_release=on_release)
    return button


def make_actions_row(on_edit, on_delete):
    """A row with Edit and Delete buttons on the right."""
    row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8),
                    padding=[dp(12), 0, dp(12), 0])
    row.add_widget(Widget())
    row.add_widget(make_small_button("Edit", LAVENDER, PURPLE_MID, on_edit))
    row.add_widget(make_small_button("Delete", "#FDECEC", RED, on_delete))
    return row


class TaskCard(Card):
    """A TaskRow with its Edit / Delete buttons underneath."""

    def __init__(self, task, on_toggle, on_edit, on_delete, **kwargs):
        super().__init__(bg=WHITE, orientation="vertical", size_hint_y=None,
                         height=dp(104), padding=[0, 0, 0, dp(8)], shadow=True, **kwargs)
        self.add_widget(TaskRow(task, on_toggle))
        self.add_widget(make_actions_row(lambda *a: on_edit(task),
                                         lambda *a: on_delete(task)))


class TasksScreen(MainScreen):
    def __init__(self, **kwargs):
        super().__init__(active_tab="tasks", hero_height=dp(186), **kwargs)
        self.tab = "All"

        self.hero.add_widget(Text(text="Daily Tasks", font_size=sp(22), bold=True,
                                  color=rgba(WHITE)))
        self.summary_label = Text(text="", font_size=sp(12), color=(1, 1, 1, 0.65))
        self.hero.add_widget(self.summary_label)

        self.search = SearchBox("Search tasks...", lambda value: self.refresh())
        self.hero.add_widget(self.search)

        tabs = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.tab_buttons = {}
        for name in TABS:
            button = RoundedButton(text=name, radius=14, font_size=sp(12))
            button.bind(on_release=lambda instance, tab=name: self.set_tab(tab))
            self.tab_buttons[name] = button
            tabs.add_widget(button)
        self.hero.add_widget(tabs)
        self._style_tabs()

        self.fab = FabButton(pos_hint={"right": 0.94, "y": 0.15})
        self.fab.bind(on_release=lambda *a: App.get_running_app().open_task_form())
        self.add_widget(self.fab)

    # ---------- tabs ----------
    def _style_tabs(self):
        for name, button in self.tab_buttons.items():
            if name == self.tab:
                button.restyle(WHITE, PURPLE_MID)
            else:
                button.restyle("#7B4DB0", WHITE)

    def set_tab(self, tab):
        self.tab = tab
        self._style_tabs()
        self.refresh()

    # ---------- showing the list ----------
    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        if not app.user.is_logged_in():
            return

        manager = TaskManager(app.db, app.user.id)
        tasks = manager.get_tasks(self.tab, self.search.text)
        self.summary_label.text = (f"{manager.count_tasks('Active')} active  •  "
                                   f"{manager.count_tasks('Completed')} completed")

        self.body.clear_widgets()
        if tasks:
            for task in tasks:
                self.body.add_widget(TaskCard(task, self.toggle_task,
                                              self.edit_task, self.ask_delete))
        elif self.search.text.strip():
            self.body.add_widget(make_empty_state("No tasks match your search"))
        else:
            self.body.add_widget(make_empty_state("No tasks here yet. Tap + to add one."))
        # extra room so the + button never covers the last card
        self.body.add_widget(Widget(size_hint_y=None, height=dp(56)))

    # ---------- actions ----------
    def toggle_task(self, task):
        app = App.get_running_app()
        TaskManager(app.db, app.user.id).toggle_task(task.id)
        self.refresh()

    def edit_task(self, task):
        App.get_running_app().open_task_form(task)

    def ask_delete(self, task):
        ConfirmDialog("Delete this item?", f"\"{short(task.title, 30)}\" will be removed for good.",
                      lambda: self.delete_task(task)).open()

    def delete_task(self, task):
        app = App.get_running_app()
        TaskManager(app.db, app.user.id).delete_task(task.id)
        self.refresh()