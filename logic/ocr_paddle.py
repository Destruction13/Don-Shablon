import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

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

        det_path = models_dir / "det" / "Multilingual_PP-OCRv3_det_infer"
        rec_path = models_dir / "rec" / "cyrillic_PP-OCRv3_rec_infer"
        cls_path = models_dir / "cls" / "ch_ppocr_mobile_v2.0_cls_infer"

        required_files = [
            det_path / "inference.pdmodel",
            det_path / "inference.pdiparams",
            rec_path / "inference.pdmodel",
            rec_path / "inference.pdiparams",
            cls_path / "inference.pdmodel",
            cls_path / "inference.pdiparams",
        ]

        for file in required_files:
            if not file.exists():
                raise FileNotFoundError(f"[OCR] ❌ Модель не найдена: {file}")

        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang='ru',
            ocr_version='PP-OCRv3',  # 🔥 Обязательно!
            det_model_dir=str(det_path),
            rec_model_dir=str(rec_path),
            cls_model_dir=str(cls_path),
            drop_score=0.5,  # ⬅️ помогает отсеивать мусор
            use_gpu=False     # ⬅️ убери, если запускаешь с GPU
        )

        logging.debug("[OCR] PaddleOCR успешно инициализирован")

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


def get_image_from_clipboard() -> Optional[Image.Image]:
    """Return an image from clipboard or ``None`` if not available."""
    try:
        img = ImageGrab.grabclipboard()
    except Exception as e:
        logging.error("[OCR] Failed to grab from clipboard: %s", e)
        img = None

    if isinstance(img, list) or img is None:
        qimg = QGuiApplication.clipboard().image()
        if qimg.isNull():
            return None
        return ImageQt.fromqimage(qimg).convert("RGB")
    if isinstance(img, Image.Image):
        return img.convert("RGB")
    return None


def run_ocr(image: Image.Image) -> List[str]:
    """Recognize text lines from an image using PaddleOCR."""
    ocr = _init_ocr()
    result = ocr.ocr(np.array(image), cls=True)
    return _extract_text_lines(result)


def parse_fields(ocr_lines: List[str]) -> Dict[str, str]:
    """Extract fields from OCR text lines."""
    fields = {
        "name": "",
        "date": "",
        "start": "",
        "end": "",
        "bz_raw": "",
        "room_raw": "",
    }

    lines = [l.strip() for l in ocr_lines if l.strip()]

    for i, line in enumerate(lines):
        lower = line.lower()
        if "организатор" in lower:
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                fields["name"] = parts[1].strip().split()[0]
            elif i + 1 < len(lines):
                fields["name"] = lines[i + 1].strip().split()[0]
            break

    date_pattern = re.compile(r"\b(\d{2}\.\d{2}\.\d{2,4})\b")
    for line in lines:
        m = date_pattern.search(line)
        if m:
            fields["date"] = m.group(1)
            break

    time_pattern = re.compile(r"\b\d{1,2}:\d{2}\b")
    times: List[str] = []
    for line in lines:
        times.extend(time_pattern.findall(line))
    if times:
        fields["start"] = times[0]
    if len(times) > 1:
        fields["end"] = times[1]

    bc_pattern = re.compile(r"б[цc]\s*[\"«]?([^\"»]+)[\"»]?(.*)", re.IGNORECASE)
    for idx, line in enumerate(lines):
        m = bc_pattern.search(line)
        if m:
            fields["bz_raw"] = m.group(1).strip()
            rest = m.group(2).strip(" ,")
            if rest:
                fields["room_raw"] = rest
            elif idx + 1 < len(lines):
                fields["room_raw"] = lines[idx + 1].strip()
            break

    return fields


def _fuzzy_match(value: str, choices: List[str], threshold: float) -> Optional[str]:
    best = None
    best_ratio = 0.0
    for choice in choices:
        ratio = SequenceMatcher(None, value.lower(), choice.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = choice
    if best_ratio >= threshold:
        logging.debug("[OCR] Fuzzy match '%s' -> '%s' (%.2f)", value, best, best_ratio)
        return best
    logging.warning("[OCR] Fuzzy match for '%s' below threshold (%.2f)", value, best_ratio)
    return None


def _room_token_ratio(room: str, candidate: str) -> float:
    tokens_room = set(re.findall(r"\w+", room.lower()))
    tokens_cand = set(re.findall(r"\w+", candidate.lower()))
    if not tokens_room:
        return 0.0
    return len(tokens_room & tokens_cand) / len(tokens_room)


def validate_with_rooms(fields: Dict[str, str], rooms: Dict[str, List[str]]) -> Dict[str, str]:
    """Validate and normalize BC and room using rooms dictionary."""
    result = {
        "name": fields.get("name", ""),
        "date": fields.get("date", ""),
        "start": fields.get("start", ""),
        "end": fields.get("end", ""),
        "bz": "",
        "room": "",
    }

    raw_bz = fields.get("bz_raw", "")
    if raw_bz:
        match = _fuzzy_match(raw_bz, list(rooms.keys()), 0.8)
        if match:
            result["bz"] = match
    if not result["bz"]:
        logging.warning("[OCR] Business center not matched: %s", raw_bz)

    raw_room = fields.get("room_raw", "")
    if result["bz"] and raw_room:
        best_room = None
        best_ratio = 0.0
        for cand in rooms[result["bz"]]:
            ratio = _room_token_ratio(raw_room, cand)
            if ratio > best_ratio:
                best_ratio = ratio
                best_room = cand
        if best_room and best_ratio >= 0.5:
            logging.debug(
                "[OCR] Fuzzy room match '%s' -> '%s' (%.2f)", raw_room, best_room, best_ratio
            )
            result["room"] = best_room
        else:
            logging.warning(
                "[OCR] Room '%s' not matched in BZ '%s'", raw_room, result["bz"]
            )
    return result


def update_gui_fields(data: Dict[str, str], ctx: UIContext) -> None:
    """Fill UI fields with parsed data."""
    logging.info("[OCR] Updating GUI with: %s", data)
    if data.get("name") and "name" in ctx.fields:
        ctx.fields["name"].setText(data["name"])

    if data.get("bz") and "bz" in ctx.fields:
        ctx.fields["bz"].setCurrentText(data["bz"])

    target = "his_room" if ctx.type_combo.currentText() == "Обмен" else "room"
    if data.get("room") and target in ctx.fields:
        ctx.fields[target].setEditText(data["room"])

    if data.get("date") and "datetime" in ctx.fields:
        dt = None
        for fmt in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                dt = datetime.strptime(data["date"], fmt)
                break
            except ValueError:
                continue
        if dt:
            ctx.fields["datetime"].setDate(QDate(dt.year, dt.month, dt.day))

    if data.get("start") and "start_time" in ctx.fields:
        ctx.fields["start_time"].setCurrentText(data["start"])
    if data.get("end") and "end_time" in ctx.fields:
        ctx.fields["end_time"].setCurrentText(data["end"])
    if "regular" in ctx.fields:
        ctx.fields["regular"].setCurrentText("Обычная")


def on_clipboard_button_click(ctx: UIContext) -> None:
    """Entry point for the clipboard OCR workflow."""
    img = get_image_from_clipboard()
    if img is None:
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
        return

    def worker():
        lines = run_ocr(img)
        logging.debug("[OCR] Lines: %s", lines)
        parsed = parse_fields(lines)
        validated = validate_with_rooms(parsed, rooms_by_bz)
        return validated

    def on_finish(result_error):
        result, error = result_error
        if error:
            logging.error("[OCR] Pipeline failed: %s", error)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{error}")
            return
        update_gui_fields(result, ctx)

    run_in_thread(worker, on_finish)


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

