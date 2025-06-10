import os
import urllib.parse
from datetime import datetime, timedelta
import requests
import logging
import pygame
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QRunnable, QThreadPool, Slot, QTimer
import logging

from logic.app_state import UIContext

logging.basicConfig(level=logging.DEBUG)
_threadpool = QThreadPool.globalInstance()

months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

days = [
    "понедельник", "вторник", "среду", "четверг",
    "пятницу", "субботу", "воскресенье",
]

DEEPL_URL = "https://api-free.deepl.com/v2/translate"
GOOGLE_URL = "https://translate.googleapis.com/translate_a/single"


class _Task(QRunnable):
    """Simple QRunnable that executes a function in a worker thread."""

    def __init__(self, func, callback):
        super().__init__()
        self.func = func
        self.callback = callback

    @Slot()
    def run(self):
        logging.debug("[POOL] Task running")
        result = None
        error = None
        try:
            result = self.func()
        except Exception as e:
            error = e
        logging.debug("[POOL] Task done")
        QTimer.singleShot(
            0,
            QApplication.instance(),
            lambda r=result, e=error: self.callback((r, e)),
        )


def run_in_thread(func, callback):
    logging.debug("[POOL] Submitting task to thread pool")
    _threadpool.start(_Task(func, callback))


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
    if not text:
        QMessageBox.warning(ctx.window, "Предупреждение", "Нет текста для перевода")
        return

    translator = getattr(ctx, "translator", "Google")

    def do_translate_deepl() -> str:
        logging.debug("[DEEPL] Sending translation request")
        params = {"text": text, "target_lang": "EN"}
        headers = {"Authorization": f"DeepL-Auth-Key {ctx.deepl_api_key}"}
        response = requests.post(DEEPL_URL, data=params, headers=headers, timeout=10)
        logging.debug("[DEEPL] Status %s", response.status_code)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response.json()["translations"][0]["text"]

    def do_translate_google() -> str:
        logging.debug("[Google] Sending translation request")
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "en",
            "dt": "t",
            "q": text,
        }
        response = requests.get(GOOGLE_URL, params=params, timeout=10)
        logging.debug("[Google] Status %s", response.status_code)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        return "".join(seg[0] for seg in data[0])

    if translator == "DeepL":
        if not ctx.deepl_api_key:
            QMessageBox.warning(ctx.window, "Ошибка", "Не указан ключ DeepL API")
            return
        task = do_translate_deepl
    else:
        task = do_translate_google

    @Slot(object)
    def show_result(result_error):
        result, error = result_error
        if error:
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось перевести текст:\n{error}")
            return
        ctx.output_text.setPlainText(result)

    run_in_thread(task, show_result)


def copy_generated_text(ctx: UIContext):
    text = ctx.output_text.toPlainText().strip()
    if text:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)


def copy_report_text(ctx: UIContext) -> None:
    """Copy auto-report text to the clipboard."""
    if getattr(ctx, "report_text", None):
        text = ctx.report_text.toPlainText().strip()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
