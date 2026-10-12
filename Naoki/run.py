"""Naoki's chat GUI.

tkinter only, no customtkinter: it is stdlib and already in the venv, and a
nicer skin is not worth a dependency plus its bundled binaries.

The graph runs on a worker thread because app.invoke blocks for the whole
model response -- on the Tk thread it would freeze the window solid. The
llm node prints stream chunks to stdout, so _Stdout bridge repoints that into
the text widget instead of duplicating the loop here.
"""


import io
import json
import queue
import sys
import threading
import tkinter as tk
from rag import index
from agent import app, CONFIG
from config import CHAT_LOG


_lock = threading.Lock()


def _index_bg():
    with _lock:
        try:
            index()
        except Exception as e:
            print(f"[index failed: {type(e).__name__}: {e}]", file=sys.stderr)


class Gui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Naoki")
        self.geometry("900x640")

        self.chat = tk.Text(self, wrap="word", state="disabled", font=("", 11))
        self.chat.pack(fill="both", expand=True, padx=8, pady=8)

        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        self.entry = tk.Entry(bar, font=("", 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus_set()
        self.send = tk.Button(bar, text="Send", command=self.on_send)
        self.send.pack(side="left", padx=(8, 0))

        self.entry.bind("<Return>", lambda _e: self.on_send())
        self.written = 0  # how many messages are already in CHAT_LOG
        self.q = queue.Queue()
        self.busy = False

    def echo(self, who, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}: {text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def on_send(self):
        line = self.entry.get().strip()
        if not line or self.busy:
            return
        self.entry.delete(0, "end")
        self.echo("you", line)
        self.echo("naoki", "")  # prefix; the stream fills in after it
        self.busy = True
        self.send.config(state="disabled")

        # Swap stdout for a thread-safe bridge so the llm node's streaming
        # prints land in the widget instead of the terminal.
        real = sys.stdout
        sys.stdout = _Bridge(self.q)
        threading.Thread(target=self.work, args=(line, real), daemon=True).start()

    def work(self, line, real):
        try:
            app.invoke({"messages": [{"role": "user", "content": line}]}, CONFIG)
            self.archive()
            threading.Thread(target=_index_bg, daemon=True).start()
        except Exception as e:
            self.q.put(f"[{type(e).__name__}: {e}]\n\n")
        finally:
            sys.stdout = real
            self.q.put("__done__")

    def archive(self):
        """Append whatever is new to CHAT_LOG, so a crash keeps the log."""
        CHAT_LOG.parent.mkdir(parents=True, exist_ok=True)
        full = app.get_state(CONFIG).values["messages"]
        with CHAT_LOG.open("a", encoding="utf-8") as f:
            f.writelines(
                json.dumps({"role": m.type, "content": m.content}) + "\n"
                for m in full[self.written:]
            )
        self.written = len(full)

    def poll(self):
        """Drain the worker queue on the Tk thread, every 50ms."""
        try:
            while True:
                msg = self.q.get_nowait()
                if msg == "__done__":
                    self.busy = False
                    self.send.config(state="normal")
                    self.entry.focus_set()
                else:
                    self.chat.configure(state="normal")
                    self.chat.insert("end", msg)
                    self.chat.see("end")
                    self.chat.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(50, self.poll)


class _Bridge:
    """Minimal write-only stdout that hands text to a queue."""

    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(s)

    def flush(self):
        pass


if __name__ == "__main__":
    gui = Gui()
    gui.after(50, gui.poll)
    gui.mainloop()
