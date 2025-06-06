import os
import urllib.parse
from datetime import datetime, timedelta
import requests
import logging
import pygame
from PySide6.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QObject, QThread, Signal

from logic.app_state import UIContext

logging.basicConfig(level=logging.DEBUG)

months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

days = [
    "понедельник", "вторник", "среду", "четверг",
    "пятницу", "субботу", "воскресенье",
]

DEEPL_URL = "https://api-free.deepl.com/v2/translate"
# Hardcoded DeepL API key as requested
DEEPL_API_KEY = "69999737-95c3-440e-84bc-96fb8550f83a:fx"

# Keep references to running threads to avoid premature garbage collection
_threads: list[QThread] = []


class _Worker(QObject):
    finished = Signal(object)

    def __init__(self, func):
        super().__init__()
        self._func = func

    def run(self):
        result = None
        error = None
        try:
            result = self._func()
        except Exception as exc:  # capture any exceptions
            error = exc
        self.finished.emit((result, error))


def run_in_thread(func, callback):
    """Execute *func* in a separate thread and call *callback* with (result, error)."""
    logging.debug("[THREAD] Starting new worker thread")
    thread = QThread()
    worker = _Worker(func)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    def handle_done(data):
        logging.debug("[THREAD] Worker finished")
        result, error = data
        callback(result, error)
        thread.quit()

    worker.finished.connect(handle_done)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # keep a reference until finished
    _threads.append(thread)

    def cleanup():
        _threads.remove(thread)

    thread.finished.connect(cleanup)
    thread.start()
    logging.debug("[THREAD] Thread started")


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
    if not DEEPL_API_KEY:
        QMessageBox.warning(ctx.window, "Ошибка", "Не указан ключ DeepL API")
        return

    def do_translate():
        logging.debug("[DEEPL] Sending translation request")
        params = {
            "text": text,
            "target_lang": "EN",
        }
        headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
        logging.debug("[DEEPL] Request params: %s", params)
        response = requests.post(DEEPL_URL, data=params, headers=headers, timeout=10)
        logging.debug("[DEEPL] Status %s, body: %s", response.status_code, response.text)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response.json()["translations"][0]["text"]

    def show_result(result, error):
        logging.debug("[DEEPL] show_result error=%s", error)
        if error:
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось перевести текст:\n{error}")
            return
        translated = result
        logging.debug("[DEEPL] Translation completed")
        dlg = QDialog(ctx.window)
        dlg.setWindowTitle("Перевод")
        v = QVBoxLayout(dlg)
        edit = QTextEdit()
        edit.setPlainText(translated)
        v.addWidget(edit)
        copy_btn = QPushButton("Скопировать")
        v.addWidget(copy_btn)

        def copy_text():
            QGuiApplication.clipboard().setText(edit.toPlainText())

        copy_btn.clicked.connect(copy_text)

        dlg.exec()

    run_in_thread(do_translate, show_result)


def copy_generated_text(ctx: UIContext):
    text = ctx.output_text.toPlainText().strip()
    if text:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
