import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from .config import ASSISTANT_NAME  # noqa: E402


class ModePicker(Gtk.Window):
    """Small popup that asks: Chat or Task?"""

    def __init__(self, app, on_pick):
        super().__init__(application=app, title=ASSISTANT_NAME)
        self.on_pick = on_pick
        self.set_resizable(False)

        question = Gtk.Label(label=f"What do you need from {ASSISTANT_NAME}?")
        chat_btn = Gtk.Button(label="Chat (C)")
        task_btn = Gtk.Button(label="Task (T)")
        chat_btn.add_css_class("suggested-action")
        chat_btn.connect("clicked", lambda _b: self.pick("chat"))
        task_btn.connect("clicked", lambda _b: self.pick("task"))

        buttons = Gtk.Box(spacing=8)
        buttons.set_homogeneous(True)
        buttons.append(chat_btn)
        buttons.append(task_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(20)
        box.append(question)
        box.append(buttons)
        self.set_child(box)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

    def pick(self, mode):
        self.on_pick(mode)
        self.close()

    def on_key(self, controller, keyval, keycode, state):
        name = (Gdk.keyval_name(keyval) or "").lower()
        if name == "c":
            self.pick("chat")
        elif name == "t":
            self.pick("task")
        elif name == "escape":
            self.close()
        else:
            return False
        return True
