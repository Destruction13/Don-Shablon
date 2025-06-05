import tkinter as tk
from tkinter import ttk

from core.app_state import UIContext
from widgets import AutocompleteCombobox  # если ты вынес его туда



themes = {
    "Светлая": {
        "bg": "white",
        "fg": "black",
        "entry_bg": "white",
        "entry_fg": "black",
        "highlight": "#fff8d4"
    },
    "Тёмная": {
        "bg": "#1e1e1e",
        "fg": "#f2f2f2",
        "entry_bg": "#2e2e2e",
        "entry_fg": "#f5f5f5",
        "highlight": "#573c3c"
    },
    "Гёрли-пак": {
        "bg": "#fff0f5",  # лаванда
        "fg": "#8b008b",  # тёмно-фиолетовый
        "entry_bg": "#ffe4f3",
        "entry_fg": "#8b008b",
        "highlight": "#ffb6c1"  # светло-розовый
    },
    "Киберпанк": {
        "bg": "#0f0f1a",
        "fg": "#39ff14",  # неоново-зелёный
        "entry_bg": "#1a1a2e",
        "entry_fg": "#00fff7",  # неоново-голубой
        "highlight": "#ff00c8"  # неоново-розовый
    },
    "Минимализм": {
        "bg": "#f0f0f0",
        "fg": "#222222",
        "entry_bg": "#ffffff",
        "entry_fg": "#222222",
        "highlight": "#c7ecee"
    },
    "Ретро DOS": {
        "bg": "#000000",
        "fg": "#00ff00",  # зелёный терминал
        "entry_bg": "#000000",
        "entry_fg": "#00ff00",
        "highlight": "#005500"
    }
}

def apply_theme(ctx: UIContext):
    style = ttk.Style()
    theme = themes[ctx.current_theme_name]
    ctx.root.configure(bg=theme["bg"])
    if ctx.asya_popup:
        ctx.asya_popup.configure(bg=theme["bg"])
    style.configure("Custom.TFrame", background=theme["bg"])
    frame = ttk.Frame(ctx.fields_frame, style="Custom.TFrame")
    

    # Стили для стандартных элементов
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
    style.configure("TEntry", fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])
    style.configure("TButton", background=theme["entry_bg"], foreground=theme["entry_fg"])
    style.configure("Error.TEntry", fieldbackground=theme["highlight"], foreground=theme["fg"])
    style.configure("Error.TCombobox", fieldbackground=theme["highlight"], foreground=theme["fg"])

    # Кастомные стили
    style.configure("Custom.TCombobox",
                    padding=3,
                    foreground=theme["entry_fg"],
                    background=theme["entry_bg"],
                    fieldbackground=theme["entry_bg"],
                    borderwidth=1,
                    relief="solid")
    
    style.configure("Custom.TButton",
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        borderwidth=1,
        focusthickness=1,
        focuscolor=theme["highlight"])

    style.map("Custom.TButton",
        background=[("active", theme["highlight"])],
        foreground=[("active", theme["fg"])])

    # Accent style for toggle buttons
    style.configure(
        "Accent.TButton",
        background=theme["highlight"],
        foreground=theme["fg"],
        borderwidth=1,
        focusthickness=1,
        focuscolor=theme["highlight"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme["highlight"])],
        foreground=[("active", theme["fg"])]
    )
  

    style.configure("Custom.DateEntry",
                    fieldbackground=theme["entry_bg"],
                    background=theme["entry_bg"],
                    foreground=theme["entry_fg"])
    style.configure("Custom.TFrame", background=theme["bg"])

    style.map("Custom.TCombobox",
        # было
        fieldbackground=[
            ("readonly", theme["entry_bg"]),
            # 👇 добавляем
            ("!readonly", theme["entry_bg"])
        ],
        background=[
            ("readonly", theme["entry_bg"]),
            ("!readonly", theme["entry_bg"])
        ],
        foreground=[
            ("readonly", theme["entry_fg"]),
            ("!readonly", theme["entry_fg"])
        ],
        selectforeground=[("readonly", theme["entry_fg"])],
        selectbackground=[("readonly", theme["entry_bg"])]
    )




    # Применяем стили к каждому виджету
    for widget in ctx.input_fields:
        if not widget.winfo_exists():
            continue  # Пропустить мёртвые виджеты

        try:
            widget.configure(background=theme["entry_bg"], foreground=theme["entry_fg"])
        except:
            pass

        # Только внутри этого цикла можно обращаться к widget
        if isinstance(widget, AutocompleteCombobox):
            widget.configure(style="Custom.TCombobox")
        elif isinstance(widget, ttk.Combobox):
            widget.configure(style="Custom.TCombobox")
        elif widget.winfo_class() == "DateEntry":
            widget.configure(style="Custom.DateEntry")
        elif isinstance(widget, ttk.Frame):
            widget.configure(style="Custom.TFrame")

    # Настройка output_text
    ctx.output_text.configure(bg=theme["entry_bg"],
                          fg=theme["entry_fg"],
                          insertbackground=theme["fg"])
    
def apply_theme_from_dropdown(*_, ctx: UIContext):
    ctx.current_theme_name = ctx.selected_theme.get()
    apply_theme(ctx)
