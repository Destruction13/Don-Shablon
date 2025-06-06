import re
from datetime import datetime
from tempfile import NamedTemporaryFile
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PIL import Image, ImageQt
import easyocr
from constants import rooms_by_bz
from logic.app_state import UIContext

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['ru', 'en'])
    return _reader


def extract_fields_from_text(texts, rooms):
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


def import_from_clipboard_image(ctx: UIContext):
    image = QGuiApplication.clipboard().image()
    if image.isNull():
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображения.")
        return
    pil_image = ImageQt.fromqimage(image)
    with NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pil_image.save(tmp.name)
        results = get_reader().readtext(tmp.name)
    texts = [x[1] for x in results]
    name, bz, room, date, start_time, end_time = extract_fields_from_text(texts, rooms_by_bz)
    if "name" in ctx.fields and name:
        ctx.fields["name"].setText(name)
    if bz and bz not in rooms_by_bz:
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
            ctx.fields["datetime"].setDate(dt.date())
        except Exception:
            pass
    if "start_time" in ctx.fields and start_time:
        ctx.fields["start_time"].setCurrentText(start_time)
    if "end_time" in ctx.fields and end_time:
        ctx.fields["end_time"].setCurrentText(end_time)
