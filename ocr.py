import re


def extract_fields_from_text(texts, rooms_by_bz):
    """Parse common fields from plain OCR text list."""
    name = ""
    bz = ""
    room = ""
    start_time = ""
    end_time = ""
    date = ""

    # 1. Имя организатора (ищем рядом со словом "Организатор")
    for i, txt in enumerate(texts):
        if "организатор" in txt.lower() and i + 1 < len(texts):
            full_name = texts[i + 1]
            name = full_name.split()[0]

    # 2. Дата и время
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

    # 3. БЦ (ищем по ключевому слову)
    for txt in texts:
        if "морозов" in txt.lower():
            bz = "БЦ Морозов"

    # 4. Переговорка (по частичному совпадению)
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
