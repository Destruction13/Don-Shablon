from tkinter import ttk
import tkinter as tk

class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        kwargs.setdefault("style", "Custom.TCombobox")
        super().__init__(master, **kwargs)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self._handle_keyrelease)
        self.bind('<Return>', self._handle_accept)
        self.bind('<Tab>', self._handle_tab)
        self['values'] = self._completion_list

    def _handle_keyrelease(self, event):
        if event.keysym in ("BackSpace", "Left", "Right", "Down", "Up", "Return", "Tab"):
            return
        typed = self.get().lower()
        self._hits = [item for item in self._completion_list if typed in item.lower()]
        self['values'] = self._hits or self._completion_list

    def _handle_accept(self, event):
        if self._hits:
            self.set(self._hits[0])
            self.icursor(tk.END)
        self.tk_focusNext().focus()
        return "break"

    def _handle_tab(self, event):
        self.event_generate('<Down>')
        return "break"
