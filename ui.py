from tkinter import ttk, messagebox
import tkinter as tk
from themes import themes, apply_theme_from_dropdown
from logic import generate_message, update_fields, on_link_change, toggle_custom_asya
from ocr import import_from_clipboard_image
from utils import toggle_music, copy_generated_text, translate_to_english
from ui_helpers import clear_frame, focus_next, enable_ctrl_v, enable_ctrl_c
from ui_state import input_fields, fields, fields_frame, link_var, asya_mode, type_var
import ui_state
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


def build_ui(root):
    import ui_state
    from logic import (
        generate_message, update_fields, on_link_change,
        toggle_custom_asya
    )
    from ocr import import_from_clipboard_image
    from themes import themes, apply_theme_from_dropdown
    from utils import copy_generated_text, translate_to_english
    from ui_helpers import enable_ctrl_c

    style = ttk.Style()
    style.theme_use("clam")

    # === Тема ===
    ui_state.current_theme_name = "Светлая"
    ui_state.selected_theme = tk.StringVar(value=ui_state.current_theme_name)
    theme = themes[ui_state.current_theme_name]

    theme_selector = ttk.Combobox(
        root,
        textvariable=ui_state.selected_theme,
        values=list(themes.keys()),
        state="readonly",
        style="Custom.TCombobox"
    )
    theme_selector.pack(pady=(0, 5))
    theme_selector.bind("<<ComboboxSelected>>", apply_theme_from_dropdown)

    # === Тип встречи ===
    ui_state.type_var = tk.StringVar()
    ui_state.type_var.trace_add("write", update_fields)

    ttk.Label(root, text="Тип встречи:", style="TLabel").pack(anchor="w", padx=10, pady=(10, 0))

    type_combo = ttk.Combobox(
        root,
        textvariable=ui_state.type_var,
        values=["Актуализация", "Обмен", "Разовая встреча"],
        state="readonly",
        style="Custom.TCombobox"
    )
    type_combo.pack(fill="x", padx=10)
    type_combo.bind("<Button-1>", lambda e: type_combo.event_generate('<Down>'))

    # === Ссылка ===
    ui_state.link_var = tk.StringVar()
    ui_state.link_var.trace_add("write", on_link_change)

    # === Ася блок ===
    ui_state.asya_mode = tk.BooleanVar(value=False)
    ui_state.is_custom_asya = tk.BooleanVar(value=False)
    ui_state.asya_name_var = tk.StringVar()
    ui_state.asya_gender_var = tk.StringVar()

    ui_state.asya_extra_frame = ttk.Frame(root, style="Custom.TFrame")
    ttk.Label(ui_state.asya_extra_frame, text="Твоё имя (ассистент):", style="TLabel").pack(anchor="w")
    ttk.Entry(ui_state.asya_extra_frame, textvariable=ui_state.asya_name_var, style="TEntry").pack(fill="x", pady=2)

    ttk.Label(ui_state.asya_extra_frame, text="Пол:", style="TLabel").pack(anchor="w")
    ttk.Combobox(
        ui_state.asya_extra_frame,
        values=["женский", "мужской"],
        state="readonly",
        textvariable=ui_state.asya_gender_var,
        style="Custom.TCombobox"
    ).pack(fill="x", pady=2)

    ttk.Checkbutton(
        root,
        text="ЛС",
        variable=ui_state.is_custom_asya,
        command=toggle_custom_asya,
        style="TCheckbutton"
    ).pack(anchor="e", padx=10)

    # === Поля ===
    ui_state.fields_frame = ttk.Frame(root, style="Custom.TFrame")
    ui_state.fields_frame.pack(fill="x", expand=True, padx=10, pady=10)

    # === Кнопки ===
    generate_button = ttk.Button(root, text="Сгенерировать сообщение", command=generate_message)
    copy_button = ttk.Button(root, text="Скопировать текст", command=copy_generated_text)

    music_button = ttk.Button(
        root,
        text="🎵",
        width=3,
        command=lambda: toggle_music(music_button, ui_state.music_path, ui_state),
        style="Custom.TButton"
    )
    music_button.pack(anchor="ne", padx=10, pady=(0, 5))

    clipboard_button = ttk.Button(
        root,
        text="📋 Из буфера",
        command=import_from_clipboard_image,
        style="Custom.TButton"
    )
    clipboard_button.pack(anchor="e", padx=10, pady=(0, 5))
    ui_state.input_fields.append(clipboard_button)

    generate_button.pack(pady=(5, 2))
    copy_button.pack(pady=(0, 10))

    # === Output ===
    output_frame = tk.Frame(root, bg=theme["bg"])
    output_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    ui_state.output_text = tk.Text(
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
    ui_state.output_text.pack(fill="both", expand=True)

    translate_button = ttk.Button(
        output_frame,
        text="EN",
        width=3,
        command=translate_to_english,
        style="Custom.TButton"
    )
    translate_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

    # === Горячие клавиши ===
    root.bind("<Control-Return>", lambda e: generate_message())
    root.bind("<Control-Shift-C>", lambda e: copy_generated_text())
    root.bind("<Control-e>", lambda e: translate_to_english())

    # === Ctrl+C ===
    enable_ctrl_c(ui_state.output_text, root)
