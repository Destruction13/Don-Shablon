import io
from datetime import datetime
from typing import Tuple, Dict, Any

from PIL import Image
import torch

from constants import rooms_by_bz
from logic.ocr_paddle import (
    run_ocr,
    parse_fields,
    validate_with_rooms,
    choose_longer_room,
)
from logic.generator import (
    _generate_actualization,
    _generate_exchange,
    _make_time_part,
)
from logic.utils import format_date_ru


def gpu_available() -> bool:
    """Return True if CUDA is available."""
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


async def process_image(data: bytes) -> Tuple[Dict[str, str], str]:
    """Run OCR on image data and return parsed fields and meeting type."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    lines, meeting_type = run_ocr(img, use_gpu=gpu_available())
    parsed = parse_fields(lines)
    if parsed.get("room_raw"):
        texts = [l["text"] for l in lines]
        parsed["room_raw"] = choose_longer_room(parsed["room_raw"], texts)
    validated = validate_with_rooms(parsed, rooms_by_bz, fuzzy_threshold=0.6)
    return validated, meeting_type


def build_greeting(name: str) -> Tuple[str, str]:
    """Simplified greeting builder returning greeting and gender (always male)."""
    greeting = f"Привет, {name}!"
    gender = "м"
    return greeting, gender


def build_actualization_message(fields: Dict[str, str], meeting_type: str) -> str:
    greeting, gender = build_greeting(fields.get("name", ""))
    thanks_word = "признателен" if gender == "м" else "признательна"
    myself_word = "сам" if gender == "м" else "сама"

    date_raw = fields.get("date")
    formatted = ""
    if date_raw:
        try:
            dt = datetime.strptime(date_raw, "%d.%m.%Y")
            formatted = format_date_ru(dt)
        except Exception:
            pass

    time_part = _make_time_part(fields.get("start", ""), fields.get("end", ""))
    return _generate_actualization(
        greeting,
        formatted,
        time_part,
        "",
        fields.get("room", ""),
        meeting_type,
        thanks_word,
        myself_word,
    )


def build_exchange_message(
    fields: Dict[str, str], meeting_type: str, my_room: str
) -> str:
    greeting, gender = build_greeting(fields.get("name", ""))
    thanks_word = "признателен" if gender == "м" else "признательна"
    myself_word = "сам" if gender == "м" else "сама"

    date_raw = fields.get("date")
    formatted = ""
    if date_raw:
        try:
            dt = datetime.strptime(date_raw, "%d.%m.%Y")
            formatted = format_date_ru(dt)
        except Exception:
            pass

    time_part = _make_time_part(fields.get("start", ""), fields.get("end", ""))
    return _generate_exchange(
        greeting,
        formatted,
        time_part,
        "",
        fields.get("room", ""),
        my_room,
        meeting_type,
        thanks_word,
        myself_word,
    )

