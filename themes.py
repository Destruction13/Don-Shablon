import tkinter as tk
from tkinter import ttk

from core.app_state import UIContext
from widgets import AutocompleteCombobox  # если ты вынес его туда



themes = {
    "Светлая": {
        "bg": "#ffffff",
        "fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "highlight": "#e0e0e0",
        "font": ("Arial", 10)
    },
    "Тёмная": {
        "bg": "#1e1e1e",
        "fg": "#f2f2f2",
        "entry_bg": "#2e2e2e",
        "entry_fg": "#f5f5f5",
        "highlight": "#444444",
        "font": ("Arial", 10)
    },
    "Киберпанк": {
        "bg": "#0f0f1a",
        "fg": "#39ff14",
        "entry_bg": "#1a1a2e",
        "entry_fg": "#00fff7",
        "highlight": "#ff00c8",
        "font": ("Courier New", 10)
    },
    "Гёрлпанк": {
        "bg": "#fff0f5",
        "fg": "#8b008b",
        "entry_bg": "#ffe4f3",
        "entry_fg": "#8b008b",
        "highlight": "#ffb6c1",
        "font": ("Comic Sans MS", 10)
    },
    "Айс-минимал": {
        "bg": "#eaf6ff",
        "fg": "#0a2c47",
        "entry_bg": "#ffffff",
        "entry_fg": "#0a2c47",
        "highlight": "#b9d8e8",
        "font": ("Helvetica", 10)
    },
    "Японский дзен": {
        "bg": "#f5f5f5",
        "fg": "#6b705c",
        "entry_bg": "#ffffff",
        "entry_fg": "#6b705c",
        "highlight": "#c8e6c9",
        "font": ("Arial", 10)
    },
    "Корпоратив": {
        "bg": "#f1f4f8",
        "fg": "#203864",
        "entry_bg": "#ffffff",
        "entry_fg": "#203864",
        "highlight": "#b0c4de",
        "font": ("Verdana", 10)
    },
    "Ретро 80-х": {
        "bg": "#2d0036",
        "fg": "#ff77ff",
        "entry_bg": "#3a0057",
        "entry_fg": "#ff77ff",
        "highlight": "#00e1ff",
        "font": ("Courier New", 10)
    },
    "Моночёрный": {
        "bg": "#000000",
        "fg": "#ffffff",
        "entry_bg": "#1b1b1b",
        "entry_fg": "#ffffff",
        "highlight": "#666666",
        "font": ("Arial", 10)
    },
    "Радужный градиент": {
        "bg": "#ffffff",
        "fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "highlight": "#ff5722",
        "font": ("Arial", 10)
    },
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
    style.configure(
        "TLabel",
        background=theme["bg"],
        foreground=theme["fg"],
        font=theme.get("font")
    )
    style.configure(
        "TEntry",
        fieldbackground=theme["entry_bg"],
        foreground=theme["entry_fg"],
        font=theme.get("font")
    )
    style.configure(
        "TButton",
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        font=theme.get("font")
    )
    style.configure(
        "Error.TEntry",
        fieldbackground=theme["highlight"],
        foreground=theme["fg"],
        font=theme.get("font")
    )
    style.configure(
        "Error.TCombobox",
        fieldbackground=theme["highlight"],
        foreground=theme["fg"],
        font=theme.get("font")
    )

    # Кастомные стили
    style.configure("Custom.TCombobox",
                    padding=3,
                    foreground=theme["entry_fg"],
                    background=theme["entry_bg"],
                    fieldbackground=theme["entry_bg"],
                    borderwidth=1,
                    relief="solid",
                    font=theme.get("font"))
    
    style.configure("Custom.TButton",
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        borderwidth=1,
        focusthickness=1,
        focuscolor=theme["highlight"],
        font=theme.get("font"))

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
        font=theme.get("font"),
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme["highlight"])],
        foreground=[("active", theme["fg"])]
    )
  

    style.configure("Custom.DateEntry",
                    fieldbackground=theme["entry_bg"],
                    background=theme["entry_bg"],
                    foreground=theme["entry_fg"],
                    font=theme.get("font"))
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
            widget.configure(
                background=theme["entry_bg"],
                foreground=theme["entry_fg"],
                font=theme.get("font")
            )
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
    ctx.output_text.configure(
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["fg"],
        font=theme.get("font")
    )
    
def apply_theme_from_dropdown(*_, ctx: UIContext):
    ctx.current_theme_name = ctx.selected_theme.get()
    apply_theme(ctx)
