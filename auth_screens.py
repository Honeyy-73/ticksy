"""
auth_screens.py
The first three screens of Ticksy: Splash, Login, and Sign Up.
They talk to the User class from user.py - no database code lives here.
"""

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from theme import (
    PINK, PURPLE, PURPLE_MID, WHITE, MUTED, LogoMark, LabeledInput,
    MessageLabel, RoundedButton, Text, make_scroll_body, rgba,
)


def build_hero(tagline, height):
    """The purple top part: logo, TICKSY, and a tagline."""
    hero = BoxLayout(orientation="vertical", size_hint_y=None, height=height,
                     padding=[0, dp(20), 0, dp(10)], spacing=dp(6))
    logo_holder = AnchorLayout(anchor_x="center", anchor_y="center",
                               size_hint_y=None, height=dp(92))
    logo_holder.add_widget(LogoMark())
    hero.add_widget(logo_holder)
    hero.add_widget(Text(text="TICKSY", font_size=sp(26), bold=True,
                         color=rgba(WHITE), halign="center"))
    hero.add_widget(Text(text=tagline, font_size=sp(12), bold=True,
                         color=rgba(PINK), halign="center"))
    return hero


class AuthScreen(Screen):
    """Shared layout: purple hero on top, rounded white card below."""

    def __init__(self, tagline, title, subtitle, hero_height, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*rgba(PURPLE))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        root = BoxLayout(orientation="vertical")
        root.add_widget(build_hero(tagline, hero_height))

        # The white card. Its rounded shape is drawn a little below the
        # window edge so only the top corners look rounded.
        card = BoxLayout(orientation="vertical")
        with card.canvas.before:
            Color(*rgba(WHITE))
            self._card_bg = RoundedRectangle(pos=card.pos, size=card.size,
                                             radius=[dp(28)])
        card.bind(pos=self._update_card, size=self._update_card)

        scroll, self.body = make_scroll_body([dp(24), dp(22), dp(24), dp(24)], dp(12))
        card.add_widget(scroll)
        root.add_widget(card)
        self.add_widget(root)

        self.body.add_widget(Text(text=title, font_size=sp(22), bold=True))
        self.body.add_widget(Text(text=subtitle, font_size=sp(12), color=rgba(MUTED)))
        self.message = MessageLabel()
        self.body.add_widget(self.message)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _update_card(self, card, *args):
        extra = dp(40)
        self._card_bg.pos = (card.x, card.y - extra)
        self._card_bg.size = (card.width, card.height + extra)

    @staticmethod
    def focus_later(field):
        Clock.schedule_once(lambda dt: setattr(field.input, "focus", True), 0.05)


class SplashScreen(Screen):
    """Shown for a couple of seconds when the app starts."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*rgba(PURPLE))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.box = BoxLayout(orientation="vertical", spacing=dp(8), opacity=0)
        self.box.add_widget(Widget())
        logo_holder = AnchorLayout(anchor_x="center", anchor_y="center",
                                   size_hint_y=None, height=dp(110))
        logo_holder.add_widget(LogoMark(size=(dp(100), dp(100))))
        self.box.add_widget(logo_holder)
        self.box.add_widget(Text(text="TICKSY", font_size=sp(34), bold=True,
                                 color=rgba(WHITE), halign="center"))
        self.box.add_widget(Text(text="Plan it. Tick it. Done.", font_size=sp(14),
                                 bold=True, color=rgba(PINK), halign="center"))
        self.box.add_widget(Widget())
        self.add_widget(self.box)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def on_enter(self, *args):
        self.box.opacity = 0
        Animation(opacity=1, duration=0.9).start(self.box)
        Clock.schedule_once(self._next, 2.6)

    def on_leave(self, *args):
        Clock.unschedule(self._next)

    def _next(self, *args):
        App.get_running_app().go("login")


class LoginScreen(AuthScreen):
    def __init__(self, **kwargs):
        super().__init__(
            tagline="Plan it. Tick it. Done.", title="Welcome Back",
            subtitle="Stay organized. Stay on track.", hero_height=dp(230), **kwargs)

        self.id_field = LabeledInput("Email / Username", "hello@ticksy.app")
        self.pw_field = LabeledInput("Password", "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
                                     password=True)
        self.body.add_widget(self.id_field)
        self.body.add_widget(self.pw_field)

        self.login_button = RoundedButton(text="Login", size_hint_y=None, height=dp(50))
        self.login_button.bind(on_release=self.do_login)
        self.body.add_widget(self.login_button)

        link = Text(
            text="Don't have an account? [ref=signup][b][color=#C9619A]Sign Up[/color][/b][/ref]",
            markup=True, halign="center", font_size=sp(12), color=rgba(MUTED))
        link.bind(on_ref_press=lambda *a: App.get_running_app().go("signup"))
        self.body.add_widget(link)

        # Enter key: ID -> password -> login
        self.id_field.input.bind(on_text_validate=lambda *a: self.focus_later(self.pw_field))
        self.pw_field.input.bind(on_text_validate=self.do_login)

    def on_pre_enter(self, *args):
        self.message.clear()

    def do_login(self, *args):
        self.message.clear()
        app = App.get_running_app()
        ok, message = app.user.login(self.id_field.text, self.pw_field.text)
        if ok:
            self.pw_field.text = ""
            app.go("dashboard")
        else:
            self.message.show(message)


class SignUpScreen(AuthScreen):
    def __init__(self, **kwargs):
        super().__init__(
            tagline="Create your account", title="Get Started",
            subtitle="Fill in your details to register.", hero_height=dp(190), **kwargs)

        dots = "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
        self.name_field = LabeledInput("Full Name", "e.g. John Santos")
        self.id_field = LabeledInput("Email / Username", "hello@ticksy.app")
        self.pw_field = LabeledInput("Password", "Min. 6 characters", password=True)
        self.confirm_field = LabeledInput("Confirm Password", dots, password=True)
        for field in (self.name_field, self.id_field, self.pw_field, self.confirm_field):
            self.body.add_widget(field)

        self.create_button = RoundedButton(text="Create Account", size_hint_y=None,
                                           height=dp(50))
        self.create_button.bind(on_release=self.do_register)
        self.body.add_widget(self.create_button)

        link = Text(
            text="Already have an account? [ref=login][b][color=#C9619A]Login[/color][/b][/ref]",
            markup=True, halign="center", font_size=sp(12), color=rgba(MUTED))
        link.bind(on_ref_press=lambda *a: App.get_running_app().go("login"))
        self.body.add_widget(link)

        # Enter key moves down the form, and the last field submits
        self.name_field.input.bind(on_text_validate=lambda *a: self.focus_later(self.id_field))
        self.id_field.input.bind(on_text_validate=lambda *a: self.focus_later(self.pw_field))
        self.pw_field.input.bind(on_text_validate=lambda *a: self.focus_later(self.confirm_field))
        self.confirm_field.input.bind(on_text_validate=self.do_register)

    def on_pre_enter(self, *args):
        self.message.clear()
        self.create_button.disabled = False

    def clear_form(self):
        for field in (self.name_field, self.id_field, self.pw_field, self.confirm_field):
            field.text = ""

    def do_register(self, *args):
        self.message.clear()
        app = App.get_running_app()
        login_id = self.id_field.text
        ok, message = app.user.register(
            login_id, self.name_field.text, self.pw_field.text, self.confirm_field.text)
        if not ok:
            self.message.show(message)
            return

        self.message.show("Account created! Redirecting to login...", ok=True)
        self.create_button.disabled = True
        Clock.schedule_once(lambda dt: self._go_login(login_id.strip()), 1.3)

    def _go_login(self, login_id):
        self.clear_form()
        login_screen = App.get_running_app().sm.get_screen("login")
        login_screen.id_field.text = login_id
        login_screen.pw_field.text = ""
        App.get_running_app().go("login")