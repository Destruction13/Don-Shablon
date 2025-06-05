import os
import sys
import requests
import urllib.parse
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import pygame
from ui_helpers import focus_next
from ui_state import UIContext



# Важно: подключить shared state
from config import DEEPL_API_KEY, DEEPL_URL, days, months


def get_resource_path(relative_path):
    """Определяет путь к ресурсу внутри .exe или рядом с ним"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)

def toggle_music(music_button, ctx: UIContext):
    if not ctx.music_path:
        print("[INFO] Музыка не загружена — ничего не делаем.")
        return

    if not ctx.state["playing"]:
        pygame.mixer.music.play(-1)
        music_button.config(text="⏸")
        ctx.state["playing"] = True
        ctx.state["paused"] = False
    elif not ctx.state["paused"]:
        pygame.mixer.music.pause()
        music_button.config(text="▶️")
        ctx.state["paused"] = True
    else:
        pygame.mixer.music.unpause()
        music_button.config(text="⏸")
        ctx.state["paused"] = False


def parse_yandex_calendar_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    event_date = query.get("event_date", [""])[0]  # Пример: 2025-05-31T14:00:00

    if not event_date:
        return None, None

    try:
        # Не трогаем никакие .astimezone()
        dt = datetime.fromisoformat(event_date)
        date_str = dt.strftime("%d.%m.%Y")
        time_str = dt.strftime("%H:%M")
        return date_str, time_str
    except Exception as e:
        print("Ошибка парсинга даты:", e)
        return None, None
    
    
def format_date_ru(date_obj):
    if not date_obj:
        return ""

    try:
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        date_clean = date_obj.date() if hasattr(date_obj, "date") else date_obj

        if date_clean == today:
            return "сегодня"
        elif date_clean == tomorrow:
            return "завтра"
        else:
            day_name = days[date_obj.weekday()]
            day = date_obj.day
            month = months[date_obj.month - 1]
            return f"в {day_name}, {day} {month}"
    except Exception as e:
        print(f"[ERROR] Невозможно отформатировать дату: {e}")
        return ""



def translate_to_english(ctx: UIContext, api_key, url):
    text = ctx.output_text.get("1.0", tk.END).strip()
    if not text:
        return

    params = {
        "auth_key": api_key,
        "text": text,
        "target_lang": "EN"
    }

    try:
        response = requests.post(url, data=params)
        response.raise_for_status()
        translated_text = response.json()["translations"][0]["text"]

        ctx.output_text.delete("1.0", tk.END)
        ctx.output_text.insert(tk.END, translated_text)
    except Exception as e:
        messagebox.showerror("Ошибка перевода", f"Не удалось перевести текст:\n{e}")


def copy_generated_text(ctx: UIContext, root):
    text = ctx.output_text.get("1.0", tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)

def validate_fields(required_keys, ctx: UIContext):
    valid = True
    for key in required_keys:
        widget = ctx.fields.get(key)
        if not widget or not hasattr(widget, "get"):
            continue

        value = widget.get().strip()

        # Вернём стиль по умолчанию
        if isinstance(widget, ttk.Combobox):
            widget.configure(style="Custom.TCombobox")   # наш базовый стиль
        else:
            widget.configure(style="TEntry")

        # Удалим старую ошибку, если есть
        if hasattr(widget, 'error_label'):
            widget.error_label.destroy()

        # Если пустое поле — подсветим
        if not value:
            valid = False
            style_name = "Error.TCombobox" if isinstance(widget, ttk.Combobox) else "Error.TEntry"
            widget.configure(style=style_name)

            # Надпись под полем
            err_label = ttk.Label(ctx.fields_frame, text="Поле обязательно", foreground="red", background="#eeeeee", font=("Arial", 8))
            err_label.pack(after=widget, anchor="w", padx=10)
            widget.error_label = err_label
    return valid