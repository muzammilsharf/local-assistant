import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .chat_window import ChatWindow  # noqa: E402
from .picker import ModePicker  # noqa: E402
from .task_window import TaskWindow  # noqa: E402


class AssistantApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.localassistant")
        self.chat_window = None
        self.task_window = None
        self.picker = None

    def do_activate(self):
        self.picker = ModePicker(self, self.open_mode)
        self.picker.present()

    def open_mode(self, mode):
        if mode == "chat":
            if self.chat_window is None:
                self.chat_window = ChatWindow(self)
            self.chat_window.present()
        else:
            if self.task_window is None:
                self.task_window = TaskWindow(self)
            self.task_window.present()


def run():
    AssistantApp().run(None)
