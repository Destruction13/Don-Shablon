import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageGrab, ImageQt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDate
from paddleocr import PaddleOCR
from pathlib import Path

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread


_ocr_instance: PaddleOCR | None = None


def _init_ocr() -> PaddleOCR:
    global _ocr_instance
    if _ocr_instance is None:
        logging.debug("[OCR] Initializing PaddleOCR")
        models_dir = Path(__file__).resolve().parent.parent / "data" / "ocr_models"
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="ru",
            use_gpu=False,
            det_model_dir=str(models_dir / "det"),
            rec_model_dir=str(models_dir / "rec"),
            cls_model_dir=str(models_dir / "cls"),
        )
    return _ocr_instance


def _normalize(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9а-яА-Я]", "", text).lower()


def _extract_text_lines(result) -> List[str]:
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, list):
            return [line[1][0] for line in first]
    if isinstance(result, list):
        return [str(r) for r in result]
    return []


def _parse_fields(texts: List[str]) -> Dict[str, str]:
    fields = {"name": "", "date": "", "start": "", "end": "", "bz": "", "room": ""}

    # Имя организатора
    for i, t in enumerate(texts):
        if "организатор" in t.lower():
            after_colon = t.split(":", 1)
            if len(after_colon) == 2 and after_colon[1].strip():
                fields["name"] = after_colon[1].strip().split()[0]
            elif i + 1 < len(texts):
                fields["name"] = texts[i + 1].strip().split()[0]
            break

    # Время начала и конца
    time_pattern = re.compile(r"\b\d{1,2}:\d{2}\b")
    all_times = []
    for t in texts:
        all_times.extend(time_pattern.findall(t))
    if len(all_times) >= 2:
        fields["start"], fields["end"] = all_times[0], all_times[1]

    # Дата
    date_pattern = re.compile(r"\b(\d{2}\.\d{2}\.\d{2,4})\b")
    for t in texts:
        m = date_pattern.search(t)
        if m:
            fields["date"] = m.group(1)
            break

    # Бизнес-центр и переговорка
    flat_rooms: List[Tuple[str, str, str]] = []
    for bz, rooms in rooms_by_bz.items():
        for room in rooms:
            flat_rooms.append((bz, room, _normalize(room)))
    for t in texts:
        norm = _normalize(t)
        for bz, room, room_norm in flat_rooms:
            if room_norm and room_norm in norm:
                fields["room"] = room
                fields["bz"] = bz
                break
        if not fields["bz"]:
            for bz in rooms_by_bz:
                if _normalize(bz) in norm:
                    fields["bz"] = bz
                    break
    return fields


def _validate_room(fields: Dict[str, str]) -> None:
    bz = fields.get("bz")
    room = fields.get("room")
    if not bz or bz not in rooms_by_bz:
        logging.warning("[OCR] Unknown business center: %s", bz)
        fields["bz"] = ""
        fields["room"] = "" if room and bz else room
        return
    if room and room not in rooms_by_bz[bz]:
        logging.warning("[OCR] Room '%s' not found in BZ '%s'", room, bz)
        fields["room"] = ""


def _apply_fields(ctx: UIContext, fields: Dict[str, str]) -> None:
    logging.info("[OCR] Parsed fields: %s", fields)
    if fields.get("name") and "name" in ctx.fields:
        ctx.fields["name"].setText(fields["name"])
    if fields.get("bz") and "bz" in ctx.fields:
        ctx.fields["bz"].setCurrentText(fields["bz"])
    if ctx.type_combo.currentText() == "Обмен":
        target = "his_room"
    else:
        target = "room"
    if fields.get("room") and target in ctx.fields:
        ctx.fields[target].setEditText(fields["room"])
    if fields.get("date") and "datetime" in ctx.fields:
        try:
            dt = datetime.strptime(fields["date"], "%d.%m.%Y")
        except ValueError:
            try:
                dt = datetime.strptime(fields["date"], "%d.%m.%y")
            except ValueError:
                dt = None
        if dt:
            ctx.fields["datetime"].setDate(QDate(dt.year, dt.month, dt.day))
    if fields.get("start") and "start_time" in ctx.fields:
        ctx.fields["start_time"].setCurrentText(fields["start"])
    if fields.get("end") and "end_time" in ctx.fields:
        ctx.fields["end_time"].setCurrentText(fields["end"])
    if "regular" in ctx.fields:
        ctx.fields["regular"].setCurrentText("Обычная")


def ocr_pipeline(ctx: UIContext) -> None:
    logging.debug("[OCR] Start pipeline")

    img = ImageGrab.grabclipboard()
    if isinstance(img, list) or img is None:
        qimg = QGuiApplication.clipboard().image()
        if qimg.isNull():
            QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
            return
        img = ImageQt.fromqimage(qimg).convert("RGB")
    else:
        if not isinstance(img, Image.Image):
            QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
            return
        img = img.convert("RGB")

    def do_ocr():
        ocr = _init_ocr()
        return ocr.ocr(np.array(img), cls=True)

    def on_result(result_error):
        result, error = result_error
        if error:
            logging.error("[OCR] OCR failed: %s", error)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{error}")
            return
        try:
            texts = _extract_text_lines(result)
            logging.debug("[OCR] Text lines: %s", texts)
            fields = _parse_fields(texts)
            _validate_room(fields)
            _apply_fields(ctx, fields)
        except Exception as e:
            logging.exception("[OCR] Parsing failed: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Ошибка при разборе OCR-результата:\n{e}")

    run_in_thread(do_ocr, on_result)

