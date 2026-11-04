import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from .agent import run_task  # noqa: E402
from .config import ASSISTANT_NAME, TASK_CLOSE_SECONDS  # noqa: E402


class TaskWindow(Gtk.Window):
    """Small command bar: type a task, see the result, window closes itself."""

    def __init__(self, app):
        super().__init__(application=app, title=f"{ASSISTANT_NAME} - Task")
        self.set_default_size(460, -1)
        self.set_resizable(False)
        self.busy = False
        self.closed = False
        self.connect("close-request", self.on_close)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("What should I do?")
        self.entry.connect("activate", self.on_submit)

        self.status = Gtk.Label()
        self.status.set_wrap(True)
        self.status.set_max_width_chars(50)
        self.status.set_xalign(0)
        self.status.set_visible(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(16)
        box.append(self.entry)
        box.append(self.status)
        self.set_child(box)

        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

        self.entry.grab_focus()

    def on_close(self, _window):
        self.closed = True
        self.get_application().task_window = None
        return False

    def on_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def show_status(self, text):
        self.status.set_label(text)
        self.status.set_visible(True)

    def on_submit(self, entry):
        text = entry.get_text().strip()
        if not text or self.busy:
            return
        self.busy = True
        entry.set_sensitive(False)
        self.show_status("Working on it...")
        threading.Thread(target=self.worker, args=(text,), daemon=True).start()

    def worker(self, text):
        try:
            reply = run_task(text)
        except Exception as e:
            reply = f"Something went wrong: {e}"
        GLib.idle_add(self.done, reply)

    def done(self, reply):
        if self.closed:
            return False
        self.show_status(reply)
        GLib.timeout_add_seconds(TASK_CLOSE_SECONDS, self.auto_close)
        return False

    def auto_close(self):
        if not self.closed:
            self.close()
        return False
