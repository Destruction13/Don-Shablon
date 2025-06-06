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
        "overlay_alpha": 0.3,
    },
    "Гёрлпанк": {
        "bg": "#fff0f5",
        "fg": "#8b008b",
        "entry_bg": "#ffe4f3",
        "entry_fg": "#8b008b",
        "highlight": "#ffb6c1",
        "font": ("Comic Sans MS", 10),
        "background_image": os.path.join("assets", "girlpunk.jpg"),
        "overlay_alpha": 0.3,
    },
    "Айс-минимал": {
        "bg": "#eaf6ff",
        "fg": "#0a2c47",
        "entry_bg": "#ffffff",
        "entry_fg": "#0a2c47",
        "highlight": "#b9d8e8",
        "font": ("Helvetica", 10),
        "background_image": os.path.join("assets", "ice_minimal.jpg"),
        "overlay_alpha": 0.3,
    },
    "Японский дзен": {
        "bg": "#f5f5f5",
        "fg": "#6b705c",
        "entry_bg": "#ffffff",
        "entry_fg": "#6b705c",
        "highlight": "#c8e6c9",
        "font": ("Arial", 10),
        "background_image": os.path.join("assets", "japan_dzen.jpg"),
        "overlay_alpha": 0.3,
    },
    "Корпоратив": {
        "bg": "#f1f4f8",
        "fg": "#203864",
        "entry_bg": "#ffffff",
        "entry_fg": "#203864",
        "highlight": "#b0c4de",
        "font": ("Verdana", 10),
        "background_image": os.path.join("assets", "corporate.jpg"),
        "overlay_alpha": 0.3,
    },
    "Ретро 80-х": {
        "bg": "#2d0036",
        "fg": "#ff77ff",
        "entry_bg": "#3a0057",
        "entry_fg": "#ff77ff",
        "highlight": "#00e1ff",
        "font": ("Courier New", 10),
        "background_image": os.path.join("assets", "retro.jpg"),
        "overlay_alpha": 0.3,
    },
    "Моночёрный": {
        "bg": "#000000",
        "fg": "#ffffff",
        "entry_bg": "#1b1b1b",
        "entry_fg": "#ffffff",
        "highlight": "#666666",
        "font": ("Arial", 10),
        "background_image": os.path.join("assets", "monoblack.jpg"),
        "overlay_alpha": 0.3,
    }
}

def apply_theme(ctx: UIContext):
    style = ttk.Style()
    theme = themes[ctx.current_theme_name]

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
    alpha = theme.get("overlay_alpha", 0.3)
    overlay = blend(base_overlay, theme["bg"], alpha)
    entry_overlay = blend(base_overlay, theme["entry_bg"], alpha)

    ctx.root.configure(bg=overlay)
    if ctx.asya_popup:
        ctx.asya_popup.configure(bg=overlay)
    style.configure("Custom.TFrame", background=overlay)
    

    # Стили для стандартных элементов
    style.configure(
        "TLabel",
        background=overlay,
        foreground=theme["fg"],
        font=theme.get("font")
    )
    style.configure(
        "TEntry",
        fieldbackground=entry_overlay,
        foreground=theme["entry_fg"],
        font=theme.get("font")
    )
    style.configure(
        "TButton",
        background=entry_overlay,
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
                    background=entry_overlay,
                    fieldbackground=entry_overlay,
                    borderwidth=1,
                    relief="solid",
                    font=theme.get("font"))
    
    style.configure("Custom.TButton",
        background=entry_overlay,
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
                    fieldbackground=entry_overlay,
                    background=entry_overlay,
                    foreground=theme["entry_fg"],
                    font=theme.get("font"))
    style.configure("Custom.TFrame", background=overlay)

    style.map(
        "Custom.TCombobox",
        fieldbackground=[
            ("readonly", entry_overlay),
            ("!readonly", entry_overlay),
        ],
        background=[
            ("readonly", entry_overlay),
            ("!readonly", entry_overlay),
        ],
        foreground=[
            ("readonly", theme["entry_fg"]),
            ("!readonly", theme["entry_fg"]),
        ],
        selectforeground=[("readonly", theme["entry_fg"])],
        selectbackground=[("readonly", entry_overlay)],
    )




    # Применяем стили к каждому виджету
    for widget in ctx.input_fields:
        if not widget.winfo_exists():
            continue  # Пропустить мёртвые виджеты

        try:
            widget.configure(
                background=entry_overlay,
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
        bg=entry_overlay,
        fg=theme["entry_fg"],
        insertbackground=theme["fg"],
        font=theme.get("font")
    )

    # Применяем полупрозрачный фон блоков
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
    if ctx.bg_update_after_id is not None:
        ctx.root.after_cancel(ctx.bg_update_after_id)
        ctx.bg_update_after_id = None
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
                ctx.bg_resize_cache = {}
            w, h = ctx.root.winfo_width(), ctx.root.winfo_height()
            if w > 0 and h > 0 and ctx.bg_image_raw:
                key = (w, h)
                if key not in ctx.bg_resize_cache:
                    resized = ctx.bg_image_raw.resize((w, h), Image.LANCZOS)
                    ctx.bg_resize_cache[key] = ImageTk.PhotoImage(resized)
                ctx.bg_image_tk = ctx.bg_resize_cache[key]
                ctx.bg_label.configure(image=ctx.bg_image_tk)
                ctx.bg_label.lower()
        except Exception as e:
            print(f"[ERROR] Cannot load background: {e}")
            ctx.bg_label.configure(image="")
    else:
        ctx.bg_label.configure(image="")
        ctx.bg_image_raw = None
        ctx.bg_image_tk = None
        ctx.bg_resize_cache = {}


def _run_bg_update(ctx: UIContext):
    ctx.bg_update_after_id = None
    update_background(ctx)


def debounced_update_background(ctx: UIContext, delay: int = 100):
    """Schedule background update with debounce."""
    if ctx.bg_update_after_id is not None:
        ctx.root.after_cancel(ctx.bg_update_after_id)
    ctx.bg_update_after_id = ctx.root.after(delay, lambda: _run_bg_update(ctx))
