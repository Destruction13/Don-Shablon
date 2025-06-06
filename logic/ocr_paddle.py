import re
import logging
from datetime import datetime

import numpy as np
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDate
from PIL import Image, ImageQt, ImageDraw
from paddleocr import PaddleOCR

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(use_angle_cls=True, lang="ru")
    return _ocr


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


def detect_repeat_checkbox(image: Image.Image, ocr_results) -> bool:
    for item in ocr_results:
        bbox = item[0]
        text = item[1][0]
        if text.strip().lower() == "повторять":
            x = int(bbox[0][0]) - 15
            y = int(bbox[0][1]) + 11
            return is_checkbox_checked(image, x, y)
    return False


def extract_data_from_screenshot(ctx: UIContext):
    logging.debug("[OCR] Кнопка нажата")
    image = QGuiApplication.clipboard().image()
    if image.isNull():
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображения.")
        return
    pil_image = ImageQt.fromqimage(image)

    def do_ocr():
        logging.debug("[OCR] OCR thread running")
        ocr = get_ocr()
        return ocr.ocr(np.array(pil_image), cls=True)

    def handle(result, error):
        logging.debug("[OCR] handle result error=%s", error)
        try:
            if error:
                raise error
            texts = [r[1][0] for r in result]
            name, bz, room, date, start_time, end_time = extract_fields_from_text(texts, rooms_by_bz)
            is_reg = detect_repeat_checkbox(pil_image, result)
            if "name" in ctx.fields and name:
                ctx.fields["name"].setText(name)
            if bz:
                if bz not in rooms_by_bz:
                    rooms_by_bz[bz] = []
                if "bz" in ctx.fields:
                    ctx.fields["bz"].setCurrentText(bz)
            if ctx.type_combo.currentText() == "Обмен":
                if "his_room" in ctx.fields and room:
                    ctx.fields["his_room"].setEditText(room)
            else:
                if "room" in ctx.fields and room:
                    ctx.fields["room"].setEditText(room)
            if "datetime" in ctx.fields and date:
                try:
                    dt = datetime.strptime(date, "%d.%m.%Y")
                    ctx.fields["datetime"].setDate(QDate(dt.year, dt.month, dt.day))
                except Exception:
                    pass
            if "start_time" in ctx.fields and start_time:
                ctx.fields["start_time"].setCurrentText(start_time)
            if "end_time" in ctx.fields and end_time:
                ctx.fields["end_time"].setCurrentText(end_time)
            if "regular" in ctx.fields:
                ctx.fields["regular"].setCurrentText("Регулярная" if is_reg else "Обычная")
        except Exception as e:
            logging.debug("[OCR] Failed: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{e}")

    run_in_thread(do_ocr, handle)
    logging.debug("[OCR] Thread started")
