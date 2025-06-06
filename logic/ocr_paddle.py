import re
import logging
import traceback
from datetime import datetime

import numpy as np
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDate
from PIL import Image, ImageQt
from paddleocr import PaddleOCR

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        # Initialize PaddleOCR once. Pin to PP-OCRv3 for Russian.
        # The API slightly differs between versions, so we keep args minimal
        # to remain compatible with both 2.x and 3.x releases.
        _ocr = PaddleOCR(use_angle_cls=True, lang="ru")
    return _ocr


def _extract_texts(result) -> list[str]:
    """Return recognized text lines from PaddleOCR result."""
    if not result:
        return []
    if isinstance(result, dict):
        return result.get("rec_texts", [])
    first = result[0]
    if isinstance(first, dict):
        return first.get("rec_texts", [])
    texts = []
    for item in result:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            val = item[1]
            if isinstance(val, (list, tuple)) and val:
                texts.append(str(val[0]))
            else:
                texts.append(str(val))
    return texts


def extract_fields_from_text(texts: list[str], rooms: dict[str, list[str]]):
    name = ""
    bz = ""
    room = ""
    start_time = ""
    end_time = ""
    date = ""

    for i, txt in enumerate(texts):
        if "организатор" in txt.lower() and i + 1 < len(texts):
            full_name = texts[i + 1]
            name = full_name.split()[0]

    found_times = []
    for txt in texts:
        cleaned = re.sub(r"[^\d]", ":", txt.strip())
        if re.fullmatch(r"\d{2}:\d{2}", cleaned):
            found_times.append(cleaned)
            if len(found_times) == 2:
                break
    if len(found_times) == 2:
        start_time, end_time = found_times

    for txt in texts:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", txt.strip()):
            date = txt.strip()
            break

    for txt in texts:
        if "морозов" in txt.lower():
            bz = "БЦ Морозов"

    flat = []
    for bz_key, rooms_list in rooms.items():
        for room_name in rooms_list:
            flat.append((bz_key, room_name))
    for txt in texts:
        txt_l = txt.lower()
        for bz_key, room_name in flat:
            short = room_name.split(".")[-1].split()[0].lower()
            if short and short in txt_l and len(short) > 3:
                room = room_name
                bz = bz_key
                break
    return name, bz, room, date, start_time, end_time


def is_checkbox_checked(image: Image.Image, x: int, y: int, size: int = 12, threshold: int = 200, fill_threshold: float = 0.2) -> bool:
    cropped = image.crop((x, y, x + size, y + size)).convert("L")
    pixels = cropped.getdata()
    dark_pixels = sum(1 for p in pixels if p < threshold)
    total_pixels = len(pixels)
    fill_ratio = dark_pixels / total_pixels
    return fill_ratio > fill_threshold


def detect_repeat_checkbox(image: Image.Image, ocr_result: dict) -> bool:
    texts = ocr_result.get("rec_texts", [])
    boxes = ocr_result.get("rec_boxes", [])
    for i, text in enumerate(texts):
        if text.strip().lower() == "повторять" and i < len(boxes):
            box = boxes[i]
            x = int(box[0]) - 15
            y = int(box[1]) + 11
            return is_checkbox_checked(image, x, y)
    return False


def extract_data_from_screenshot(ctx: UIContext):
    logging.debug("[WTF] Кнопка нажата")

    # Забираем QImage из буфера
    image = QGuiApplication.clipboard().image()
    logging.debug("[OCR] QImage isNull? %s", image.isNull())

    if image.isNull():
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображения.")
        return

    # Конвертируем в PIL.Image сразу, пока мы ещё в главном потоке
    pil_image = ImageQt.fromqimage(image).convert("RGB")
    logging.debug("[OCR] PIL image size: %s, mode: %s", pil_image.size, pil_image.mode)

    # OCR-функция для запуска в потоке
    def do_ocr():
        logging.debug("[OCR] OCR thread running")
        try:
            ocr = get_ocr()
            logging.debug("[OCR] PaddleOCR instance initialized")
            result = ocr.ocr(np.array(pil_image), cls=True, output="dict")
            logging.debug("[OCR] OCR result received")
            return result
        except Exception as e:
            traceback.print_exc()
            logging.error("[OCR] Ошибка при OCR: %s", e)
            raise

    # Callback после выполнения OCR
    def handle(result, error):
        logging.debug("[OCR] handle(result, error=%s) called", error)
        try:
            if error:
                raise error
            if not result:
                raise ValueError("Результат OCR пуст")

            texts = _extract_texts(result)
            logging.debug("[OCR] Распознанные строки: %s", texts)

            name, bz, room, date, start_time, end_time = extract_fields_from_text(texts, rooms_by_bz)

            # Распаковка OCR-результата
            ocr_dict = result if isinstance(result, dict) else result[0] if result and isinstance(result[0], dict) else {}
            is_reg = False  # Пока отключено — detect_repeat_checkbox(pil_image, ocr_dict)

            if name and "name" in ctx.fields:
                logging.debug("[OCR] Установка имени: %s", name)
                ctx.fields["name"].setText(name)

            if bz:
                logging.debug("[OCR] Установка БЦ: %s", bz)
                if bz not in rooms_by_bz:
                    rooms_by_bz[bz] = []
                if "bz" in ctx.fields:
                    ctx.fields["bz"].setCurrentText(bz)

            if ctx.type_combo.currentText() == "Обмен":
                if "his_room" in ctx.fields and room:
                    logging.debug("[OCR] Установка чужой переговорки: %s", room)
                    ctx.fields["his_room"].setEditText(room)
            else:
                if "room" in ctx.fields and room:
                    logging.debug("[OCR] Установка переговорки: %s", room)
                    ctx.fields["room"].setEditText(room)

            if "datetime" in ctx.fields and date:
                try:
                    dt = datetime.strptime(date, "%d.%m.%Y")
                    logging.debug("[OCR] Установка даты: %s", dt)
                    ctx.fields["datetime"].setDate(QDate(dt.year, dt.month, dt.day))
                except Exception as e:
                    logging.warning("[OCR] Невозможно распарсить дату: %s", e)

            if "start_time" in ctx.fields and start_time:
                logging.debug("[OCR] Установка начала: %s", start_time)
                ctx.fields["start_time"].setCurrentText(start_time)

            if "end_time" in ctx.fields and end_time:
                logging.debug("[OCR] Установка конца: %s", end_time)
                ctx.fields["end_time"].setCurrentText(end_time)

            if "regular" in ctx.fields:
                logging.debug("[OCR] Установка регулярности: %s", is_reg)
                ctx.fields["regular"].setCurrentText("Регулярная" if is_reg else "Обычная")

        except Exception as e:
            traceback.print_exc()
            logging.error("[OCR] Обработка результата провалилась: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{e}")

    # Запуск OCR в потоке
    try:
        run_in_thread(do_ocr, handle)
        logging.debug("[OCR] Поток OCR запущен")
    except Exception as e:
        logging.exception("[OCR] Не удалось запустить поток OCR: %s", e)

