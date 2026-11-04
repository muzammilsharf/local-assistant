import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

from .config import HISTORY_LIMIT  # noqa: E402
from .llm import stream_chat  # noqa: E402
from .memory import add_fact, check_remember, load_history, save_history  # noqa: E402


class ChatWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Assistant")
        self.set_default_size(720, 620)
        self.history = load_history()
        self.stop_event = threading.Event()
        self.busy = False

        header = Gtk.HeaderBar()
        new_chat = Gtk.Button(label="New chat")
        new_chat.connect("clicked", self.on_new_chat)
        header.pack_start(new_chat)
        self.set_titlebar(header)

        # Chat area
        self.buffer = Gtk.TextBuffer()
        self.buffer.create_tag("you", weight=Pango.Weight.BOLD, foreground="#3584e4")
        self.buffer.create_tag("bot", weight=Pango.Weight.BOLD, foreground="#26a269")
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
                self.append("Assistant\n", "bot")
            self.append(m["content"] + "\n\n")

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
        self.append("Assistant\n", "bot")

        fact = check_remember(text)
        if fact:
            add_fact(fact)
            self.append(f"Saved: {fact}\n\n")
            return

        self.busy = True
        self.stop_event.clear()
        self.send_btn.set_label("Stop")
        threading.Thread(target=self.worker, args=(text,), daemon=True).start()

    def worker(self, text):
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
        GLib.idle_add(self.finish, text, reply)

    def finish(self, text, reply):
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

    def do_activate(self):
        win = self.props.active_window or ChatWindow(self)
        win.present()


def run():
    AssistantApp().run(None)
