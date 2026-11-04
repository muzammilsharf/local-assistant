import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

from .agent import run_task  # noqa: E402
from .config import ASSISTANT_NAME, HISTORY_LIMIT  # noqa: E402
from .llm import stream_chat  # noqa: E402
from .memory import add_fact, check_remember, load_history, save_history  # noqa: E402

TASK_HINT = "Task mode. Try: open downloads, pause music, next song."


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


class ChatWindow(Gtk.ApplicationWindow):
    def __init__(self, app, mode):
        super().__init__(application=app, title=ASSISTANT_NAME)
        self.set_default_size(720, 620)
        self.history = load_history()
        self.stop_event = threading.Event()
        self.busy = False
        self.mode = mode
        self.connect("close-request", self.on_close)

        header = Gtk.HeaderBar()
        new_chat = Gtk.Button(label="New chat")
        new_chat.connect("clicked", self.on_new_chat)
        header.pack_start(new_chat)
        self.mode_label = Gtk.Label()
        header.pack_end(self.mode_label)
        self.set_titlebar(header)

        # Chat area
        self.buffer = Gtk.TextBuffer()
        self.buffer.create_tag("you", weight=Pango.Weight.BOLD, foreground="#3584e4")
        self.buffer.create_tag("bot", weight=Pango.Weight.BOLD, foreground="#26a269")
        self.buffer.create_tag("note", style=Pango.Style.ITALIC, foreground="#888888")
        self.view = Gtk.TextView(buffer=self.buffer)
        self.view.set_editable(False)
        self.view.set_cursor_visible(False)
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view.set_left_margin(14)
        self.view.set_right_margin(14)
        self.view.set_top_margin(10)
        self.view.set_bottom_margin(10)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.scroll.set_child(self.view)

        # Input area: Enter sends, Shift+Enter adds a new line
        self.input_buffer = Gtk.TextBuffer()
        self.input = Gtk.TextView(buffer=self.input_buffer)
        self.input.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.input.set_left_margin(8)
        self.input.set_right_margin(8)
        self.input.set_top_margin(8)
        self.input.set_bottom_margin(8)
        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        self.input.add_controller(keys)
        input_scroll = Gtk.ScrolledWindow()
        input_scroll.set_hexpand(True)
        input_scroll.set_min_content_height(56)
        input_scroll.set_max_content_height(160)
        input_scroll.set_child(self.input)

        self.send_btn = Gtk.Button(label="Send")
        self.send_btn.add_css_class("suggested-action")
        self.send_btn.set_valign(Gtk.Align.END)
        self.send_btn.connect("clicked", self.on_send)

        row = Gtk.Box(spacing=8)
        row.set_margin_start(10)
        row.set_margin_end(10)
        row.set_margin_top(8)
        row.set_margin_bottom(10)
        row.append(input_scroll)
        row.append(self.send_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.scroll)
        box.append(row)
        self.set_child(box)

        # Show the earlier conversation
        for m in self.history:
            if m["role"] == "user":
                self.append("You\n", "you")
            else:
                self.append(f"{ASSISTANT_NAME}\n", "bot")
            self.append(m["content"] + "\n\n")

        self.set_mode(mode)

    def on_close(self, _window):
        self.get_application().chat_window = None
        return False

    def set_mode(self, mode):
        if self.busy:
            return
        self.mode = mode
        self.mode_label.set_label("Chat mode" if mode == "chat" else "Task mode")
        if mode == "task":
            self.append(TASK_HINT + "\n\n", "note")
        self.input.grab_focus()

    def append(self, text, tag=None):
        end = self.buffer.get_end_iter()
        if tag:
            self.buffer.insert_with_tags_by_name(end, text, tag)
        else:
            self.buffer.insert(end, text)
        GLib.idle_add(self.scroll_to_end)
        return False

    def scroll_to_end(self):
        adj = self.scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def on_key(self, controller, keyval, keycode, state):
        is_enter = keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter)
        if is_enter and not (state & Gdk.ModifierType.SHIFT_MASK):
            self.on_send(None)
            return True
        return False

    def on_send(self, _btn):
        if self.busy:
            self.stop_event.set()
            return

        text = self.input_buffer.get_text(
            self.input_buffer.get_start_iter(),
            self.input_buffer.get_end_iter(),
            False,
        ).strip()
        if not text:
            return
        self.input_buffer.set_text("")
        self.append("You\n", "you")
        self.append(text + "\n\n")
        self.append(f"{ASSISTANT_NAME}\n", "bot")

        fact = check_remember(text)
        if fact:
            add_fact(fact)
            self.append(f"Saved: {fact}\n\n")
            return

        self.busy = True
        if self.mode == "task":
            self.send_btn.set_sensitive(False)
            threading.Thread(target=self.task_worker, args=(text,), daemon=True).start()
        else:
            self.stop_event.clear()
            self.send_btn.set_label("Stop")
            threading.Thread(target=self.chat_worker, args=(text,), daemon=True).start()

    # Task mode
    def task_worker(self, text):
        try:
            reply = run_task(text)
        except Exception as e:
            reply = f"Something went wrong: {e}"
        GLib.idle_add(self.task_done, reply)

    def task_done(self, reply):
        self.append(reply + "\n\n")
        self.busy = False
        self.send_btn.set_sensitive(True)
        self.input.grab_focus()
        return False

    # Chat mode
    def chat_worker(self, text):
        reply = ""
        stream = stream_chat(self.history, text)
        try:
            for piece in stream:
                if self.stop_event.is_set():
                    break
                reply += piece
                GLib.idle_add(self.append, piece)
        except Exception as e:
            GLib.idle_add(self.append, f"\n[Error: {e}]")
        finally:
            stream.close()
        GLib.idle_add(self.chat_done, text, reply)

    def chat_done(self, text, reply):
        self.append("\n\n")
        if reply:
            self.history += [
                {"role": "user", "content": text},
                {"role": "assistant", "content": reply},
            ]
            self.history = self.history[-HISTORY_LIMIT:]
            save_history(self.history)
        self.busy = False
        self.send_btn.set_label("Send")
        self.input.grab_focus()
        return False

    def on_new_chat(self, _btn):
        if self.busy:
            return
        self.history = []
        save_history([])
        self.buffer.set_text("")


class AssistantApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.localassistant")
        self.chat_window = None
        self.picker = None

    def do_activate(self):
        self.picker = ModePicker(self, self.open_window)
        self.picker.present()

    def open_window(self, mode):
        if self.chat_window is None:
            self.chat_window = ChatWindow(self, mode)
        else:
            self.chat_window.set_mode(mode)
        self.chat_window.present()


def run():
    AssistantApp().run(None)
