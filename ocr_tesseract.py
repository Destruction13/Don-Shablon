import re
from datetime import datetime
from typing import List

from PIL import Image, ImageDraw
import pytesseract
from pytesseract import Output
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox

from constants import rooms_by_bz


def grab_clipboard_image() -> Image.Image | None:
    clipboard = QGuiApplication.clipboard()
    if clipboard.mimeData().hasImage():
        qimage = clipboard.image()
        if qimage.isNull():
            return None
        return Image.fromqimage(qimage)
    return None


def extract_fields_from_text(texts: List[str]):
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
        cleaned = re.sub(r"[^0-9]", ":", txt.strip())
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

    flat_rooms = []
    for bz_key, rooms in rooms_by_bz.items():
        for room_name in rooms:
            flat_rooms.append((bz_key, room_name))

    for txt in texts:
        txt_lower = txt.lower()
        for bz_key, room_name in flat_rooms:
            short = room_name.split(".")[-1].split()[0].lower()
            if short and short in txt_lower and len(short) > 3:
                room = room_name
                bz = bz_key
                break

    return name, bz, room, date, start_time, end_time


def is_checkbox_checked(image: Image.Image, x: int, y: int, size: int = 12, threshold: int = 200, fill_threshold: float = 0.2) -> bool:
    cropped = image.crop((x, y, x + size, y + size)).convert("L")
    pixels = list(cropped.getdata())
    dark_pixels = sum(1 for p in pixels if p < threshold)
    fill_ratio = dark_pixels / len(pixels)
    print(f"[DEBUG] fill_ratio: {fill_ratio:.2f}")
    return fill_ratio > fill_threshold


def detect_repeat_checkbox(image: Image.Image, ocr_data) -> bool:
    print("[DEBUG] Начинаем поиск чекбокса...")
    n = len(ocr_data['text'])
    for i in range(n):
        text = ocr_data['text'][i]
        if text and text.strip().lower() == "повторять":
            print("[DEBUG] Найдено слово 'повторять'")
            x = ocr_data['left'][i] - 15
            y = ocr_data['top'][i] + 11
            print(f"[DEBUG] Координаты для анализа чекбокса: x={x}, y={y}")
            draw = ImageDraw.Draw(image)
            draw.rectangle([x - 10, y - 10, x + 10, y + 10], outline="red")
            image.save("checkbox_debug.png")
            return is_checkbox_checked(image, x, y)
    print("[DEBUG] Слово 'повторять' не найдено вообще.")
    return False


def import_from_clipboard_image(ctx):
    meeting_type = ctx.type_box.currentText() if hasattr(ctx, 'type_box') else ''
    print(f"[DEBUG] Тип встречи: {meeting_type}")
    image = grab_clipboard_image()
    if image is None:
        QMessageBox.critical(ctx.window if hasattr(ctx, 'window') else None, "Ошибка", "Буфер обмена не содержит изображения.")
        return
    print("[DEBUG] Буфер получен")
    data = pytesseract.image_to_data(image, lang='rus', output_type=Output.DICT)
    texts = [t for t in data['text'] if t.strip()]
    print("[DEBUG] Текст распознан:", texts)
    name, bz, room, date, start_time, end_time = extract_fields_from_text(texts)
    is_regular = "Регулярная" if detect_repeat_checkbox(image, data) else "Обычная"

    if 'name' in ctx.fields and name:
        ctx.fields['name'].setText(name)
    if bz:
        if bz not in rooms_by_bz:
            rooms_by_bz[bz] = []
        if 'bz' in ctx.fields:
            ctx.fields['bz'].setCurrentText(bz)
    if meeting_type == 'Обмен':
        if 'his_room' in ctx.fields and room:
            ctx.fields['his_room'].setCurrentText(room)
    else:
        if 'room' in ctx.fields and room:
            ctx.fields['room'].setCurrentText(room)
    if 'datetime' in ctx.fields and date:
        try:
            ctx.fields['datetime'].setDate(datetime.strptime(date, "%d.%m.%Y"))
        except Exception as e:
            print("Ошибка даты:", e)
    if 'start_time' in ctx.fields and start_time:
        ctx.fields['start_time'].setCurrentText(start_time)
    if 'end_time' in ctx.fields and end_time:
        ctx.fields['end_time'].setCurrentText(end_time)
    if 'regular' in ctx.fields:
        ctx.fields['regular'].setCurrentText(is_regular)
    print("[DEBUG] Вставка завершена")
