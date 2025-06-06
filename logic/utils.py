import os
import urllib.parse
from datetime import datetime, timedelta
import requests
import pygame
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QGuiApplication

from logic.app_state import UIContext

months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

days = [
    "понедельник", "вторник", "среду", "четверг",
    "пятницу", "субботу", "воскресенье",
]

DEEPL_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")


def toggle_music(button, ctx: UIContext):
    if not ctx.music_path:
        return
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(ctx.music_path)
        except Exception as e:
            QMessageBox.critical(ctx.window, "Ошибка", f"Музыка недоступна:\n{e}")
            return
    if not ctx.music_state["playing"]:
        pygame.mixer.music.play(-1)
        button.setText("⏸")
        ctx.music_state["playing"] = True
        ctx.music_state["paused"] = False
    elif not ctx.music_state["paused"]:
        pygame.mixer.music.pause()
        button.setText("▶️")
        ctx.music_state["paused"] = True
    else:
        pygame.mixer.music.unpause()
        button.setText("⏸")
        ctx.music_state["paused"] = False


def parse_yandex_calendar_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    event_date = query.get("event_date", [""])[0]
    if not event_date:
        return None, None
    try:
        dt = datetime.fromisoformat(event_date)
        return dt.strftime("%d.%m.%Y"), dt.strftime("%H:%M")
    except Exception:
        return None, None


def format_date_ru(date_obj):
    if not date_obj:
        return ""
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    date_clean = date_obj.date() if hasattr(date_obj, "date") else date_obj
    if date_clean == today:
        return "сегодня"
    if date_clean == tomorrow:
        return "завтра"
    day_name = days[date_obj.weekday()]
    day = date_obj.day
    month = months[date_obj.month - 1]
    preposition = "во" if day_name == "вторник" else "в"
    return f"{preposition} {day_name}, {day} {month}"


def translate_to_english(ctx: UIContext):
    text = ctx.output_text.toPlainText().strip()
    if not text or not DEEPL_API_KEY:
        return
    params = {"auth_key": DEEPL_API_KEY, "text": text, "target_lang": "EN"}
    try:
        response = requests.post(DEEPL_URL, data=params)
        response.raise_for_status()
        translated = response.json()["translations"][0]["text"]
        ctx.output_text.setPlainText(translated)
    except Exception as e:
        QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось перевести текст:\n{e}")


def copy_generated_text(ctx: UIContext):
    text = ctx.output_text.toPlainText().strip()
    if text:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
