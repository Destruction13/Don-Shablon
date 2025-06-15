import os
import urllib.parse
from datetime import datetime, timedelta
import requests
import logging
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QRunnable, QThreadPool, Slot, QTimer

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
    """Задача для выполнения функции в рабочем потоке."""

    def __init__(self, func, callback):
        super().__init__()
        self.func = func
        self.callback = callback

    @Slot()
    def run(self):
        logging.debug("[POOL] Задача запущена")
        result = None
        error = None
        try:
            result = self.func()
        except Exception as e:
            error = e
        logging.debug("[POOL] Задача завершена")
        QTimer.singleShot(
            0,
            QApplication.instance(),
            lambda r=result, e=error: self.callback((r, e)),
        )


def run_in_thread(func, callback):
    """Запустить функцию в отдельном потоке."""
    logging.debug("[POOL] Запуск в отдельном потоке")
    _threadpool.start(_Task(func, callback))



def parse_yandex_calendar_url(url):
    """Извлечь дату и время из ссылки на Яндекс.Календарь."""
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
    """Вернуть дату в человекочитаемом виде на русском."""
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
    """Перевести текст из выходного поля на английский."""
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
    """Скопировать сгенерированный текст в буфер обмена."""
    text = ctx.output_text.toPlainText().strip()
    if text:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)


def copy_report_text(ctx: UIContext) -> None:
    """Скопировать текст автоотчёта в буфер обмена."""
    if getattr(ctx, "report_text", None):
        text = ctx.report_text.toPlainText().strip()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
