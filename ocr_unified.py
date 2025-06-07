import json
import logging
from typing import List

from PySide6.QtWidgets import QMessageBox

from constants import rooms_by_bz
from logic.ocr_paddle import (
    get_image_from_clipboard,
    run_ocr,
    parse_fields,
    validate_with_rooms,
    update_gui_fields,
)
from ocr import extract_fields_from_text
from logic.app_state import UIContext


def recognize_from_clipboard(ctx: UIContext) -> None:
    """Unified OCR workflow with fallback parsing."""
    img = get_image_from_clipboard()
    if img is None:
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
        return

    lines = run_ocr(img)
    parsed, scores = parse_fields(lines, return_scores=True)

    need_fallback = not parsed.get("name") or scores.get("name", 1.0) < 0.5
    if need_fallback:
        texts: List[str] = [l["text"] for l in lines]
        name, bz, room, date, start, end = extract_fields_from_text(texts, rooms_by_bz)
        if name and not parsed.get("name"):
            parsed["name"] = name
        if bz and not parsed.get("bz_raw"):
            parsed["bz_raw"] = bz
        if room and not parsed.get("room_raw"):
            parsed["room_raw"] = room
        if date and not parsed.get("date"):
            parsed["date"] = date
        if start and not parsed.get("start"):
            parsed["start"] = start
        if end and not parsed.get("end"):
            parsed["end"] = end

    validated = validate_with_rooms(parsed, rooms_by_bz, fuzzy_threshold=0.6)
    update_gui_fields(validated, ctx, scores=scores)

    try:
        with open("final_fields.json", "w", encoding="utf-8") as f:
            json.dump({"fields": validated, "scores": scores}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("[OCR] Failed to write final_fields.json: %s", e)
