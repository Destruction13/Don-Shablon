import re
from datetime import datetime

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDate
import logging
from PIL import Image, ImageQt
import pytesseract

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread


def extract_fields_from_text(texts: list[str], rooms: dict[str, list[str]]):
    name = ""
    bz = ""
    room = ""
    start_time = ""
    end_time = ""
    date = ""
    is_regular = False
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
        if "повтор" in txt_l:
            is_regular = True
        for bz_key, room_name in flat:
            short = room_name.split(".")[-1].split()[0].lower()
            if short and short in txt_l and len(short) > 3:
                room = room_name
                bz = bz_key
                break
    return name, bz, room, date, start_time, end_time, is_regular


def extract_data_from_screenshot(ctx: UIContext):
    logging.debug("[OCR] Кнопка нажата")
    print("Запуск OCR из буфера")
    image = QGuiApplication.clipboard().image()
    if image.isNull():
        logging.debug("[OCR] Clipboard is empty")
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображения.")
        return
    pil_image = ImageQt.fromqimage(image)

    def do_ocr():
        logging.debug("[OCR] OCR thread running")
        return pytesseract.image_to_string(pil_image, lang="rus+eng")

    def handle(result, error):
        logging.debug("[OCR] handle result error=%s", error)
        print("OCR raw result:\n", result)
        try:
            if error:
                raise error
            lines = [t.strip() for t in result.splitlines() if t.strip()]
            name, bz, room, date, start_time, end_time, is_reg = extract_fields_from_text(lines, rooms_by_bz)
            result_dict = {
                "name": name,
                "bz": bz,
                "room": room,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "regular": is_reg,
            }
            print("Parsed:", result_dict)
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
            if is_reg and "regular" in ctx.fields:
                ctx.fields["regular"].setCurrentText("Регулярная")
        except Exception as e:
            logging.debug("[OCR] Failed: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{e}")

    run_in_thread(do_ocr, handle)
    logging.debug("[OCR] Thread started")
