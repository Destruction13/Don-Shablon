import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from core.app_state import UIContext
from widgets import AutocompleteCombobox  # если ты вынес его туда
import os



themes = {
    "Светлая": {
        "bg": "#ffffff",
        "fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "highlight": "#e0e0e0",
        "font": ("Arial", 10),
        "background_image": None,
    },
    "Тёмная": {
        "bg": "#1e1e1e",
        "fg": "#f2f2f2",
        "entry_bg": "#2e2e2e",
        "entry_fg": "#f5f5f5",
        "highlight": "#444444",
        "font": ("Arial", 10),
        "background_image": None,
    },
    "Киберпанк": {
        "bg": "#0f0f1a",
        "fg": "#39ff14",
        "entry_bg": "#1a1a2e",
        "entry_fg": "#00fff7",
        "highlight": "#ff00c8",
        "font": ("Courier New", 10),
        "background_image": os.path.join("assets", "cyberpunk.jpg"),
    },
    "Гёрлпанк": {
        "bg": "#fff0f5",
        "fg": "#8b008b",
        "entry_bg": "#ffe4f3",
        "entry_fg": "#8b008b",
        "highlight": "#ffb6c1",
        "font": ("Comic Sans MS", 10),
        "background_image": os.path.join("assets", "girlpunk.jpg"),
    },
    "Айс-минимал": {
        "bg": "#eaf6ff",
        "fg": "#0a2c47",
        "entry_bg": "#ffffff",
        "entry_fg": "#0a2c47",
        "highlight": "#b9d8e8",
        "font": ("Helvetica", 10),
        "background_image": os.path.join("assets", "ice_minimal.jpg"),
    },
    "Японский дзен": {
        "bg": "#f5f5f5",
        "fg": "#6b705c",
        "entry_bg": "#ffffff",
        "entry_fg": "#6b705c",
        "highlight": "#c8e6c9",
        "font": ("Arial", 10),
        "background_image": os.path.join("assets", "japan_dzen.jpg"),
    },
    "Корпоратив": {
        "bg": "#f1f4f8",
        "fg": "#203864",
        "entry_bg": "#ffffff",
        "entry_fg": "#203864",
        "highlight": "#b0c4de",
        "font": ("Verdana", 10),
        "background_image": os.path.join("assets", "corporate.jpg"),
    },
    "Ретро 80-х": {
        "bg": "#2d0036",
        "fg": "#ff77ff",
        "entry_bg": "#3a0057",
        "entry_fg": "#ff77ff",
        "highlight": "#00e1ff",
        "font": ("Courier New", 10),
        "background_image": os.path.join("assets", "retro.jpg"),
    },
    "Моночёрный": {
        "bg": "#000000",
        "fg": "#ffffff",
        "entry_bg": "#1b1b1b",
        "entry_fg": "#ffffff",
        "highlight": "#666666",
        "font": ("Arial", 10),
        "background_image": os.path.join("assets", "monoblack.jpg"),
    }
}

def apply_theme(ctx: UIContext):
    style = ttk.Style()
    theme = themes[ctx.current_theme_name]
    ctx.root.configure(bg=theme["bg"])
    if ctx.asya_popup:
        ctx.asya_popup.configure(bg=theme["bg"])
    style.configure("Custom.TFrame", background=theme["bg"])
    

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

    # Полупрозрачный фон блоков (имитируем 70% прозрачность без alpha-канала)

    def brightness(hex_color: str) -> float:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b

    def hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return "#%02X%02X%02X" % rgb

    def blend(fg: str, bg: str, alpha: float) -> str:
        r1, g1, b1 = hex_to_rgb(fg)
        r2, g2, b2 = hex_to_rgb(bg)
        r = int(alpha * r1 + (1 - alpha) * r2)
        g = int(alpha * g1 + (1 - alpha) * g2)
        b = int(alpha * b1 + (1 - alpha) * b2)
        return rgb_to_hex((r, g, b))

    base_overlay = "#000000" if brightness(theme["fg"]) > 128 else "#FFFFFF"
    overlay = blend(base_overlay, theme["bg"], 0.3)  # 70% прозрачность
    if ctx.fields_frame:
        ctx.fields_frame.configure(bg=overlay)
    if ctx.action_frame:
        ctx.action_frame.configure(bg=overlay)
    if ctx.output_text:
        ctx.output_text.master.configure(bg=overlay)

    # Обновляем фон
    update_background(ctx)

def apply_theme_from_dropdown(*_, ctx: UIContext):
    ctx.current_theme_name = ctx.selected_theme.get()
    apply_theme(ctx)


def update_background(ctx: UIContext):
    """Resize and set the background image according to current theme."""
    theme = themes.get(ctx.current_theme_name, {})
    path = theme.get("background_image")
    if not ctx.bg_label:
        return
    if path:
        try:
            if not os.path.isabs(path):
                base = os.path.dirname(os.path.abspath(__file__))
                path_full = os.path.join(base, path)
            else:
                path_full = path
            if path_full != ctx.bg_image_path:
                ctx.bg_image_raw = Image.open(path_full)
                ctx.bg_image_path = path_full
            w, h = ctx.root.winfo_width(), ctx.root.winfo_height()
            if w > 0 and h > 0 and ctx.bg_image_raw:
                resized = ctx.bg_image_raw.resize((w, h), Image.LANCZOS)
                ctx.bg_image_tk = ImageTk.PhotoImage(resized)
                ctx.bg_label.configure(image=ctx.bg_image_tk)
                ctx.bg_label.lower()
        except Exception as e:
            print(f"[ERROR] Cannot load background: {e}")
            ctx.bg_label.configure(image="")
    else:
        ctx.bg_label.configure(image="")
        ctx.bg_image_raw = None
        ctx.bg_image_tk = None
