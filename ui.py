from tkinter import ttk, messagebox
import tkinter as tk
from themes import (
    themes,
    apply_theme_from_dropdown,
    debounced_update_background,
)
from logic import (
    generate_message,
    update_fields,
    on_link_change,
    toggle_custom_asya,
    save_custom_asya,
    update_asya_button,
    toggle_asya_mode,
    update_asya_mode_button,
)
from ocr import import_from_clipboard_image
from utils import toggle_music, copy_generated_text, translate_to_english
from ui_helpers import clear_frame, focus_next, enable_ctrl_v, enable_ctrl_c
from core.app_state import UIContext
from config import DEEPL_API_KEY, DEEPL_URL
from widgets import AutocompleteCombobox
from constants import rooms_by_bz
import os
import pygame
import sys




def init_music(filename: str) -> str | None:
    try:
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            return path
        else:
            print(f"[WARNING] Музыка не найдена: {path}")
            return None
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке музыки: {e}")
        return None


def build_ui(ctx: UIContext):
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"[ERROR] Failed to init mixer: {e}")

    ctx.music_path = init_music(ctx.music_path)

    style = ttk.Style()
    style.theme_use("clam")

    # --- Background image holder ---
    ctx.bg_label = tk.Label(ctx.root)
    ctx.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    ctx.bg_label.lower()
    ctx.root.bind("<Configure>", lambda e: debounced_update_background(ctx))

    # === Тема ===
    ctx.current_theme_name = "Светлая"
    ctx.selected_theme = tk.StringVar(value=ctx.current_theme_name)
    theme = themes[ctx.current_theme_name]

    theme_selector = ttk.Combobox(
        ctx.root,
        textvariable=ctx.selected_theme,
        values=list(themes.keys()),
        state="readonly",
        style="Custom.TCombobox"
    )
    theme_selector.pack(pady=(0, 5))
    theme_selector.bind("<<ComboboxSelected>>", lambda *_: apply_theme_from_dropdown(ctx=ctx))

    # === Тип встречи ===
    ctx.type_var = tk.StringVar()
    ctx.type_var.trace_add("write", lambda *_: update_fields(ctx=ctx))

    ttk.Label(ctx.root, text="Тип встречи:", style="TLabel").pack(anchor="w", padx=10, pady=(10, 0))

    type_combo = ttk.Combobox(
        ctx.root,
        textvariable=ctx.type_var,
        values=["Актуализация", "Обмен", "Разовая встреча"],
        state="readonly",
        style="Custom.TCombobox"
    )
    type_combo.pack(fill="x", padx=10)
    type_combo.bind("<Button-1>", lambda e: type_combo.event_generate('<Down>'))

    # === Ссылка ===
    ctx.link_var = tk.StringVar()
    ctx.link_var.trace_add("write", lambda *_: on_link_change(ctx=ctx))

    # === Ася блок ===
    ctx.asya_mode = tk.BooleanVar(value=False)
    ctx.asya_name_var = tk.StringVar()
    ctx.asya_gender_var = tk.StringVar()
    ctx.asya_popup = None
    ctx.asya_extra_frame = None


    def brightness(hex_color: str) -> float:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b

    def hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip('#')
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return '#%02X%02X%02X' % rgb

    def blend(fg: str, bg: str, alpha: float) -> str:
        r1, g1, b1 = hex_to_rgb(fg)
        r2, g2, b2 = hex_to_rgb(bg)
        r = int(alpha * r1 + (1 - alpha) * r2)
        g = int(alpha * g1 + (1 - alpha) * g2)
        b = int(alpha * b1 + (1 - alpha) * b2)
        return rgb_to_hex((r, g, b))

    base_overlay = '#000000' if brightness(theme['fg']) > 128 else '#FFFFFF'
    overlay = blend(base_overlay, theme['bg'], 0.3)

    # === Поля ===
    ctx.fields_frame = tk.Frame(ctx.root, bg=overlay)
    ctx.fields_frame.pack(fill="x", expand=True, padx=10, pady=10)

    # === Кнопки ===
    ctx.action_frame = tk.Frame(ctx.root, bg=overlay)
    ctx.action_frame.pack(pady=(5, 2))

    generate_button = ttk.Button(ctx.action_frame, text="Сгенерировать сообщение", command=lambda: generate_message(ctx))
    ctx.asya_button = ttk.Button(
        ctx.action_frame,
        text="ЛС",
        command=lambda: toggle_custom_asya(ctx),
        style="Custom.TButton",
    )
    ctx.asya_mode_button = ttk.Button(
        ctx.action_frame,
        text="Ася +",
        command=lambda: toggle_asya_mode(ctx),
        style="Custom.TButton",
    )
    copy_button = ttk.Button(ctx.root, text="Скопировать текст", command=lambda: copy_generated_text(ctx, ctx.root))

    music_button = ttk.Button(
        ctx.root,
        text="🎵",
        width=3,
        command=lambda: toggle_music(music_button, ctx),
        style="Custom.TButton"
    )
    music_button.pack(anchor="ne", padx=10, pady=(0, 5))

    clipboard_button = ttk.Button(
        ctx.root,
        text="📋 Из буфера",
        command=lambda: import_from_clipboard_image(ctx),
        style="Custom.TButton"
    )
    clipboard_button.pack(anchor="e", padx=10, pady=(0, 5))
    ctx.input_fields.append(clipboard_button)

    generate_button.pack(side="left")
    ctx.asya_button.pack(side="left", padx=(5, 0))
    ctx.asya_mode_button.pack(side="left", padx=(5, 0))
    update_asya_button(ctx)
    update_asya_mode_button(ctx)

    copy_button.pack(pady=(0, 10))

    # === Output ===
    output_frame = tk.Frame(ctx.root, bg=overlay)
    output_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    ctx.output_text = tk.Text(
        output_frame,
        height=14,
        wrap="word",
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["fg"],
        highlightthickness=0,
        bd=0,
        relief="flat"
    )
    ctx.output_text.pack(fill="both", expand=True)

    translate_button = ttk.Button(
        output_frame,
        text="EN",
        width=3,
        command=lambda: translate_to_english(ctx, DEEPL_API_KEY, DEEPL_URL),
        style="Custom.TButton"
    )
    translate_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

    # === Горячие клавиши ===
    ctx.root.bind("<Control-Return>", lambda e: generate_message(ctx))
    ctx.root.bind("<Control-Shift-C>", lambda e: copy_generated_text(ctx, ctx.root))
    ctx.root.bind("<Control-e>", lambda e: translate_to_english(ctx, DEEPL_API_KEY, DEEPL_URL))

    # === Ctrl+C ===
    enable_ctrl_c(ctx.output_text, ctx.root)

    # Initial theme application
    apply_theme_from_dropdown(ctx=ctx)
