import json
import random
import re
import pytest

from logic.ocr_paddle import validate_with_rooms  # Импортируй свою функцию

# OCR-искажения
ocr_misreads = {
    "О": "0", "о": "0", "Х": "X", "х": "x", "М": "M", "м": "m",
    "Н": "H", "н": "h", "Р": "P", "р": "p", "К": "K", "к": "k",
    "Е": "E", "е": "e", "А": "A", "а": "a", "С": "C", "с": "c",
    "В": "B", "в": "b", "Т": "T", "т": "t", "Ц": "L", "ц": "l",
}

def introduce_ocr_noise(text: str) -> str:
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < 0.2:
            if chars[i] in ocr_misreads:
                chars[i] = ocr_misreads[chars[i]]
        if random.random() < 0.05:
            chars[i] = chars[i].upper() if chars[i].islower() else chars[i].lower()
    noisy = ''.join(chars)
    if random.random() < 0.5:
        noisy += f" {random.randint(3, 9)} этаж; {random.randint(2, 12)} мест"
    return noisy

# Загрузи путь к своему rooms.json
with open("data/rooms.json", "r", encoding="utf-8") as f:
    rooms_data = json.load(f)

# Генерация кейсов
test_cases = []
for bz, room_list in rooms_data.items():
    for room in room_list:
        test_cases.append((bz, room, introduce_ocr_noise(room)))

@pytest.mark.parametrize("bz,expected_room,noisy_input", test_cases)
def test_room_recognition(bz, expected_room, noisy_input):
    fields = {
        "bz_raw": bz,
        "room_raw": noisy_input
    }

    validate_with_rooms(fields, rooms_data)
    matched = fields.get("room")
    assert matched == expected_room, f"FAIL: expected '{expected_room}', got '{matched}' from noisy input '{noisy_input}'"
    print(f"[TEST] Input: {noisy_input} | Expected: {expected_room} | Matched: {matched}")




