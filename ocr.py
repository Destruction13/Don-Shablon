import re
from PIL import Image, ImageDraw
from PIL import ImageGrab
from tkinter import messagebox
import tkinter as tk
from datetime import datetime
from constants import rooms_by_bz
# In the updated project the UI context lives under logic.app_state
from logic.app_state import UIContext

import easyocr

_reader = None


def get_reader():
    """Lazily initialize and return the OCR reader."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['ru', 'en'])
    return _reader


def extract_fields_from_text(texts, rooms_by_bz):
    name = ""
    bz = ""
    room = ""
    start_time = ""
    end_time = ""
    date = ""

    # 1. Имя организатора (ищем рядом с "Организатор")
    for i, txt in enumerate(texts):
        if "организатор" in txt.lower() and i+1 < len(texts):
            full_name = texts[i+1]
            name = full_name.split()[0]

    
    # 2. Дата и время 
    found_times = []
    for txt in texts:
        cleaned = txt.strip()
        cleaned = re.sub(r"[^\d]", ":", cleaned)  # всё, что не цифра — заменяем на ":"
        if re.fullmatch(r"\d{2}:\d{2}", cleaned):
            found_times.append(cleaned)
            if len(found_times) == 2:
                break

    if len(found_times) == 2:
        start_time, end_time = found_times

    # Теперь ищем первую подходящую дату
    for txt in texts:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", txt.strip()):
            date = txt.strip()
            break

    # 3. БЦ (ищем по слову "БЦ")
    for txt in texts:
        if "морозов" in txt.lower():
            bz = "БЦ Морозов"


    # 4. Переговорка (ищем по частичному совпадению)
    flat_rooms = []
    for bz_key, rooms in rooms_by_bz.items():
        for room_name in rooms:
            flat_rooms.append((bz_key, room_name))

    # проходим по текстам и ищем совпадение с последним словом из названия переговорки
    for txt in texts:
        txt_lower = txt.lower()
        for bz_key, room_name in flat_rooms:
            short = room_name.split(".")[-1].split()[0].lower()
            if short and short in txt_lower and len(short) > 3:
                room = room_name
                bz = bz_key
                break

    return name, bz, room, date, start_time, end_time

def is_checkbox_checked(image, x, y, size=12, threshold=200, fill_threshold=0.2):
    # Обрезаем область чекбокса
    cropped = image.crop((x, y, x + size, y + size)).convert("L")  # L = grayscale
    pixels = cropped.getdata()

    # Считаем сколько тёмных пикселей
    dark_pixels = sum(1 for p in pixels if p < threshold)
    total_pixels = len(pixels)

    fill_ratio = dark_pixels / total_pixels
    print(f"[DEBUG] fill_ratio: {fill_ratio:.2f}")

    # Если больше 10% тёмных — галка стоит
    return fill_ratio > fill_threshold

def detect_repeat_checkbox(image_path, ocr_results):
    image = Image.open(image_path)
    print("[DEBUG] Начинаем поиск чекбокса...")

    for bbox, text, _ in ocr_results:
        print(f"[OCR] Найден текст: '{text}' с bbox: {bbox}")

        if text.strip().lower() == "повторять":
            print("[DEBUG] Найдено слово 'повторять'")

            x = int(bbox[0][0]) - 15
            y = int(bbox[0][1]) + 11

            print(f"[DEBUG] Координаты для анализа чекбокса: x={x}, y={y}")

            # Дебаг-рамка
            draw = ImageDraw.Draw(image)
            draw.rectangle([x - 10, y - 10, x + 10, y + 10], outline="red")
            image.save("checkbox_debug.png")

            return is_checkbox_checked(image, x, y)

    print("[DEBUG] Слово 'повторять' не найдено вообще.")
    return False

def import_from_clipboard_image(ctx: UIContext):
    """Fill form fields with data extracted from an image in the clipboard."""
    meeting_type = ctx.type_var.get()
    print(f"[DEBUG] Тип встречи: {meeting_type}")
    image = ImageGrab.grabclipboard()
    if isinstance(image, Image.Image):
        image_path = "clipboard_temp.png"
        image.save(image_path)

        results = get_reader().readtext(image_path)
        texts = [x[1] for x in results]

        name, bz, room, date, start_time, end_time = extract_fields_from_text(texts, rooms_by_bz)

        is_regular = "Регулярная" if detect_repeat_checkbox(image_path, results) else "Обычная"

        if "name" in ctx.fields and name:
            ctx.fields["name"].delete(0, tk.END)
            ctx.fields["name"].insert(0, name)

        # Если BZ не в словаре — добавим временно
        if bz and bz not in rooms_by_bz:
            rooms_by_bz[bz] = []

        # Заполним поля (BZ — обязательно первым)
        if "bz" in ctx.fields:
            ctx.fields["bz"].set(bz)

        # Обновим списки для AutocompleteCombobox ПЕРЕД вставкой переговорок
        if meeting_type == "Обмен" and "bz" in ctx.fields and "his_room" in ctx.fields and "my_room" in ctx.fields:
            current_bz = ctx.fields["bz"].get()
            full_list = rooms_by_bz.get(current_bz, [])
            ctx.fields["his_room"].set_completion_list(full_list)
            ctx.fields["my_room"].set_completion_list(full_list)

        # Теперь безопасно вставляем переговорки
        if meeting_type == "Обмен":
            if "his_room" in ctx.fields and room:
                ctx.fields["his_room"].set(room)
        else:
            if "room" in ctx.fields and room:
                ctx.fields["room"].set(room)


        if "datetime" in ctx.fields and date:
            try:
                ctx.fields["datetime"].set_date(datetime.strptime(date, "%d.%m.%Y"))
            except Exception as e:
                print("Ошибка даты:", e)

        if "start_time" in ctx.fields and start_time:
            ctx.fields["start_time"].set(start_time)

        if "end_time" in ctx.fields and end_time:
            ctx.fields["end_time"].set(end_time)

        if "regular" in ctx.fields:
            ctx.fields["regular"].set(is_regular)

    else:
        messagebox.showerror("Ошибка", "Буфер обмена не содержит изображения.")