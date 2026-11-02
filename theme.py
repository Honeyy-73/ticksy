"""
theme.py
Ticksy colors and reusable widgets (text, buttons, input fields, logo).
Every screen imports from here so the whole app looks consistent.
"""

import os

from kivy.animation import Animation
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

# ---------- brand colors (taken from your Figma design) ----------
PURPLE = "#5B2D8E"
PURPLE_MID = "#7B3DB4"
PINK = "#C9619A"
LAVENDER = "#F0E8FA"
BG = "#F5F5F5"
TEXT = "#2A1040"
MUTED = "#B89AB9"
WHITE = "#FFFFFF"
RED = "#D32F2F"
GREEN = "#2E7D32"

# Category badge colors: (background, text)
CATEGORY_COLORS = {
    "School": ("#EDE7F6", "#5E35B1"),
    "Personal": ("#FCE4EC", "#C2185B"),
    "Important": ("#FFF3E0", "#E65100"),
    "Work": ("#E3F2FD", "#1565C0"),
    "Health": ("#E8F5E9", "#2E7D32"),
}

# Put your logo picture in the same folder as this file and name it logo.jpg
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.jpg")


def rgba(hex_color):
    """'#5B2D8E' -> (r, g, b, a) numbers that Kivy understands."""
    return get_color_from_hex(hex_color)


def short(text, limit):
    """Cut long text so it fits on one line: 'Finish the res...'."""
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit - 3].rstrip() + "..."


# Set to False once scrolling works. While True, every click/wheel over a list
# prints one line in the terminal so we can see what the scroll area receives.
DEBUG_SCROLL = True


class TicksyScroll(ScrollView):
    """A normal ScrollView that can report the touches it receives."""

    def on_touch_down(self, touch):
        handled = super().on_touch_down(touch)
        if DEBUG_SCROLL and self.collide_point(*touch.pos):
            content = self.children[0] if self.children else None
            print("[scroll] button=%s handled=%s view_h=%d content_h=%d scroll_y=%.2f "
                  "effect_min=%s effect_max=%s" % (
                      getattr(touch, "button", None), handled, self.height,
                      content.height if content else -1, self.scroll_y,
                      getattr(self.effect_y, "min", None),
                      getattr(self.effect_y, "max", None)))
        return handled


def make_scroll_body(padding, spacing):
    """A ScrollView plus the column inside it. Returns (scroll, body).

    - items stack from the TOP
    - the column's height is worked out from the items themselves, so there is
      always something to scroll when they don't fit
    - mouse wheel, dragging, and a thin purple scroll bar all work
    """
    scroll = TicksyScroll(
        do_scroll_x=False, bar_width=dp(3), bar_margin=dp(2),
        bar_color=(0.48, 0.24, 0.71, 0.6), bar_inactive_color=(0.48, 0.24, 0.71, 0.25),
        scroll_type=["bars", "content"], scroll_wheel_distance=dp(50))
    body = GridLayout(cols=1, size_hint_y=None, padding=padding, spacing=spacing)

    def fit(*args):
        kids = body.children
        needed = (sum(k.height for k in kids) + spacing * max(len(kids) - 1, 0)
                  + padding[1] + padding[3])
        body.height = max(body.minimum_height, needed, scroll.height)

    body.bind(minimum_height=fit, children=fit)
    scroll.bind(height=fit)
    scroll.add_widget(body)
    return scroll, body


class Text(Label):
    """A label that wraps to its width and grows to fit its text."""

    def __init__(self, **kwargs):
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("color", rgba(TEXT))
        kwargs.setdefault("font_size", sp(14))
        super().__init__(**kwargs)
        self.bind(width=self._wrap, texture_size=self._fit)
        self._wrap()

    def _wrap(self, *args):
        self.text_size = (self.width, None)

    def _fit(self, *args):
        self.height = max(self.texture_size[1], dp(16))


class MessageLabel(Text):
    """Shows an error (red) or success (green) message. Takes no space when empty."""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", sp(12))
        super().__init__(**kwargs)
        self.height = 0

    def _fit(self, *args):
        self.height = (self.texture_size[1] + dp(10)) if self.text else 0

    def show(self, message, ok=False):
        """Fade the message in so it doesn't just pop onto the screen."""
        Animation.cancel_all(self, "opacity")
        self.color = rgba(GREEN if ok else RED)
        self.opacity = 0
        self.text = message
        Animation(opacity=1, duration=0.25, t="out_quad").start(self)

    def clear(self):
        Animation.cancel_all(self, "opacity")
        self.opacity = 1
        self.text = ""
        self.height = 0


class RoundedButton(Button):
    """A flat button with rounded corners that darkens when pressed."""

    def __init__(self, bg=PURPLE_MID, text_color=WHITE, radius=14, **kwargs):
        kwargs.setdefault("font_size", sp(15))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = rgba(text_color)

        self._normal = rgba(bg)
        self._pressed = [c * 0.8 for c in self._normal[:3]] + [1]
        with self.canvas.before:
            self._fill = Color(*self._normal)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._update, size=self._update, state=self._on_state)

    def restyle(self, bg, text_color):
        """Change the colors after creation (used by the Tasks tab buttons)."""
        self._normal = rgba(bg)
        self._pressed = [c * 0.8 for c in self._normal[:3]] + [1]
        self._fill.rgba = self._pressed if self.state == "down" else self._normal
        self.color = rgba(text_color)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _on_state(self, *args):
        self._fill.rgba = self._pressed if self.state == "down" else self._normal


class LabeledInput(BoxLayout):
    """A small caption on top of a rounded text box (like your Figma fields)."""

    def __init__(self, caption, hint="", password=False, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(76), spacing=dp(6), **kwargs)
        self.caption = Text(text=caption.upper(), font_size=sp(11), bold=True,
                            color=rgba(MUTED))
        self.add_widget(self.caption)

        self.box = BoxLayout(size_hint_y=None, height=dp(48), padding=[dp(14), 0])
        with self.box.canvas.before:
            Color(*rgba("#F8F3FA"))
            self._bg = RoundedRectangle(pos=self.box.pos, size=self.box.size,
                                        radius=[dp(12)])
            self._border_color = Color(*rgba("#E8DDF0"))
            self._border = Line(rounded_rectangle=(0, 0, 10, 10, dp(12)), width=1)

        self.input = TextInput(
            hint_text=hint, password=password, multiline=False, write_tab=False,
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=rgba(TEXT), hint_text_color=rgba("#B9A6BC"),
            cursor_color=rgba(PURPLE_MID), font_size=sp(15),
            padding=[0, dp(14), 0, dp(10)],
        )
        self.box.add_widget(self.input)
        self.add_widget(self.box)

        self.box.bind(pos=self._redraw, size=self._redraw)
        self.input.bind(focus=self._on_focus)

    @property
    def text(self):
        return self.input.text

    @text.setter
    def text(self, value):
        self.input.text = value

    def _redraw(self, *args):
        x, y = self.box.pos
        w, h = self.box.size
        self._bg.pos = (x, y)
        self._bg.size = (w, h)
        self._border.rounded_rectangle = (x, y, w, h, dp(12))

    def _on_focus(self, instance, focused):
        self.caption.color = rgba(PINK if focused else MUTED)
        # fade the border colour instead of snapping it
        Animation.cancel_all(self._border_color)
        Animation(rgba=rgba(PURPLE_MID if focused else "#E8DDF0"),
                  duration=0.18).start(self._border_color)


class LogoMark(Widget):
    """The Ticksy logo. Uses logo.jpg if it exists, otherwise draws a simple one."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(84), dp(84)))
        super().__init__(**kwargs)
        self._has_image = os.path.exists(LOGO_PATH)
        with self.canvas:
            if self._has_image:
                Color(1, 1, 1, 1)
                self._tile = RoundedRectangle(source=LOGO_PATH, pos=self.pos,
                                              size=self.size, radius=[dp(22)])
                self._check = None
            else:
                Color(*rgba("#8A4FC4"))
                self._tile = RoundedRectangle(pos=self.pos, size=self.size,
                                              radius=[dp(22)])
            Color(1, 1, 1, 0.3)
            self._border = Line(rounded_rectangle=(0, 0, 10, 10, dp(22)), width=1.2)
            if not self._has_image:
                Color(1, 1, 1, 1)
                self._check = Line(points=[0, 0, 0, 0, 0, 0], width=dp(5),
                                   cap="round", joint="round")
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        x, y = self.pos
        w, h = self.size
        radius = min(w, h) * 0.22
        self._tile.pos = self.pos
        self._tile.size = self.size
        self._tile.radius = [radius]
        self._border.rounded_rectangle = (x, y, w, h, radius)
        if self._check is not None:
            self._check.width = max(min(w, h) * 0.06, dp(2))
            self._check.points = [
                x + w * 0.27, y + h * 0.52,
                x + w * 0.43, y + h * 0.34,
                x + w * 0.74, y + h * 0.70,
            ]