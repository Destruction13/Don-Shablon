import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

import numpy as np
from PIL import Image, ImageGrab, ImageQt, ImageDraw, ImageFont
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDate
from pathlib import Path

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread

# --- OCR configuration ---
# Threshold below which OCR results are ignored
SCORE_IGNORE_THRESHOLD = 0.7
# Threshold for accepting a value without fuzzy matching
SCORE_THRESHOLD = 0.82
# Fuzzy matching acceptance level
FUZZY_THRESHOLD = 0.75
# How far in pixels two boxes may be on Y to be considered on one line
BBOX_Y_TOLERANCE = 25
# Maximum horizontal gap between splitted tokens
SPLIT_TOKEN_MAX_GAP = 70
# Force fuzzy matching even for low score items (debug)
FORCE_FUZZY = True

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



from typing import Any

_ocr_instance: Any = None


def _init_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        logging.debug("[OCR] Initializing EasyOCR")
        try:
            import easyocr
        except Exception as e:
            logging.error("[OCR] Failed to import EasyOCR: %s", e)
            raise
        _ocr_instance = easyocr.Reader(['ru'], gpu=False)
        logging.debug("[OCR] EasyOCR successfully initialized")

    return _ocr_instance


def _normalize(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9а-яА-Я]", "", text).lower()


def normalize_russian(text: str) -> str:
    return (
        text.replace("A", "А")
            .replace("B", "В")
            .replace("E", "Е")
            .replace("K", "К")
            .replace("M", "М")
            .replace("H", "Н")
            .replace("O", "О")
            .replace("P", "Р")
            .replace("C", "С")
            .replace("T", "Т")
            .replace("Y", "У")
            .replace("X", "Х")
            .replace("a", "а")
            .replace("e", "е")
            .replace("o", "о")
            .replace("p", "р")
            .replace("c", "с")
            .replace("x", "х")
    )


def normalize_generic(text: str) -> str:
    return text.lower().strip()


def has_organizer_typo(text: str) -> bool:
    return (
        "рганизатор" in text
        or "рганизатop" in text
        or SequenceMatcher(None, text, "организатор").ratio() > 0.75
    )


def _extract_text_lines(result) -> List[str]:
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, list):
            return [line[1][0] for line in first]
    if isinstance(result, list):
        return [str(r) for r in result]
    return []



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


def run_ocr(image: Image.Image, *, ignore_threshold: float = SCORE_IGNORE_THRESHOLD) -> List[Dict]:
    """Recognize text lines from an image using EasyOCR.

    Parameters
    ----------
    image: PIL.Image
        Image to process.
    ignore_threshold: float
        Lines with score below this value will be discarded.

    Returns
    -------
    List[Dict]
        Each dict contains ``text``, ``score`` and ``bbox``.
    """

    reader = _init_ocr()
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    result = reader.readtext(np.array(image))
    logging.debug("[OCR] RAW EasyOCR result: %s", result)

    lines: List[Dict] = []
    for bbox, text, score in result:
        if score < ignore_threshold:
            continue
        bbox_int = [[int(x), int(y)] for x, y in bbox]
        lines.append({
            "text": text.strip(),
            "score": float(score),
            "bbox": bbox_int,
            "raw_text": text.strip(),
        })

    save_debug_ocr_image(image, lines)
    return lines


def merge_split_lines(lines: List[Dict]) -> List[Dict]:
    """Merge neighbouring OCR lines that likely belong to the same word."""
    if not lines:
        return []

    lines = sorted(lines, key=lambda l: min(y for x, y in l["bbox"]))
    merged: List[Dict] = []
    for line in lines:
        if merged:
            prev = merged[-1]
            prev_y = min(y for x, y in prev["bbox"])
            line_y = min(y for x, y in line["bbox"])
            if abs(line_y - prev_y) <= BBOX_Y_TOLERANCE:
                prev_right = max(x for x, y in prev["bbox"])
                line_left = min(x for x, y in line["bbox"])
                if 0 <= line_left - prev_right <= SPLIT_TOKEN_MAX_GAP:
                    new_text = f"{prev['text']} {line['text']}"
                    logging.debug("[OCR] Merging '%s' + '%s' -> '%s'", prev['text'], line['text'], new_text)
                    prev['text'] = new_text
                    prev['score'] = min(prev['score'], line['score'])
                    xs = [p[0] for p in prev['bbox']] + [p[0] for p in line['bbox']]
                    ys = [p[1] for p in prev['bbox']] + [p[1] for p in line['bbox']]
                    prev['bbox'] = [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]
                    continue
        merged.append(dict(line))
    return merged

def is_label_like(text, label):
    return SequenceMatcher(None, text.lower(), label.lower()).ratio() > 0.7

def save_debug_ocr_image(image: Image.Image, lines: List[Dict], path="ocr_debug_output.jpg"):
    """Save OCR debugging overlay and JSON info."""

    if not lines:
        return

    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    for line in lines:
        bbox = [tuple(p) for p in line["bbox"]]
        draw.polygon(bbox, outline="red", width=2)
        text = f"{line['text']} {line['score']:.2f}"
        draw.text((bbox[0][0], bbox[0][1] - 15), text, fill="red", font=font)

    img_copy.save(path)

    debug_info = [
        {"text": line["text"], "score": line["score"], "bbox": line["bbox"]}
        for line in lines
    ]
    with open(Path(path).with_suffix(".json"), "w", encoding="utf-8") as f:
        import json
        json.dump(debug_info, f, ensure_ascii=False, indent=2)


def extract_bc_and_room(lines: List[Dict]) -> Tuple[str, str]:
    """Try to extract business center and room from OCR lines."""
    bz_raw = ""
    room_raw = ""

    for i, line in enumerate(lines):
        lower = line["text"].lower()
        if "морозов" in lower or "бц" in lower or "мopозов" in lower:
            bz_raw = "БЦ Морозов"
            if i + 1 < len(lines):
                room_raw = lines[i + 1]["text"].strip()
            break

    return bz_raw, room_raw


def normalize_russian(text: str) -> str:
    return (
        text.replace("A", "А")
            .replace("B", "В")
            .replace("E", "Е")
            .replace("K", "К")
            .replace("M", "М")
            .replace("H", "Н")
            .replace("O", "О")
            .replace("P", "Р")
            .replace("C", "С")
            .replace("T", "Т")
            .replace("Y", "У")
            .replace("X", "Х")
            .replace("a", "а")
            .replace("e", "е")
            .replace("o", "о")
            .replace("p", "р")
            .replace("c", "с")
            .replace("x", "х")
            .replace("3", "з")
    )

def normalize_generic(text: str) -> str:
    return text.lower().strip()

def fix_ocr_time_garbage(text: str) -> str:
    return (
        text.replace("з", "3")
            .replace("o", "0")
            .replace("l", "1")
    )

def is_label_like(text, label):
    return SequenceMatcher(None, text.lower(), label.lower()).ratio() > 0.7

def fuzzy_best_match(text, candidates, threshold=FUZZY_THRESHOLD):
    best_score = 0
    best_match = None
    for c in candidates:
        score = SequenceMatcher(None, text.lower(), c.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = c
    if best_score >= threshold:
        return best_match
    logging.warning("[OCR] Fuzzy match for '%s' below threshold (%.2f)", text, best_score)
    return None

# -----------------------------------------------
# Основной парсер
# -----------------------------------------------
def parse_fields(ocr_lines: list) -> dict:
    lines = []
    for l in ocr_lines:
        raw = l["text"].strip()
        if not raw:
            continue
        norm = normalize_generic(raw)
        if any(k in norm for k in ["организатор", "бц", "место", "дата", "время"]):
            norm = normalize_russian(norm)
        lines.append({**l, "text": raw, "norm": norm, "raw_text": raw})

    fields = {"name": "", "bz_raw": "", "room_raw": "", "date": "", "start": "", "end": ""}

    for i, line in enumerate(lines):
        txt_norm = line["norm"]

        # Организатор
        if is_label_like(txt_norm, "организатор"):
            parts = []
            for j in range(i+1, i+3):
                if j >= len(lines): break
                if lines[j]["score"] >= SCORE_THRESHOLD:
                    parts.append(lines[j]["text"])
            if parts:
                fields["name"] = " ".join(parts)

        # Время и дата
        if is_label_like(txt_norm, "время"):
            for j in range(i+1, i+5):
                if j >= len(lines): break
                raw = fix_ocr_time_garbage(lines[j]["raw_text"])
                if re.match(r"\d{1,2}:\d{2}", raw) and not fields["start"]:
                    fields["start"] = raw
                elif re.match(r"\d{1,2}:\d{2}", raw):
                    fields["end"] = raw
        if is_label_like(txt_norm, "дата"):
            for j in range(i+1, i+4):
                if j >= len(lines): break
                if re.match(r"\d{2}\.\d{2}\.\d{4}", lines[j]["raw_text"]):
                    fields["date"] = lines[j]["raw_text"]

        # БЦ
        if is_label_like(txt_norm, "бц") or txt_norm.startswith("бц"):
            if len(txt_norm.split()) > 1:
                fields["bz_raw"] = line["text"]
            elif i + 1 < len(lines):
                fields["bz_raw"] = f"{line['text']} {lines[i+1]['text']}"

        # Переговорка
        if is_label_like(txt_norm, "переговорка"):
            room_parts = []
            for j in range(i+1, i+4):
                if j >= len(lines): break
                if lines[j]["score"] >= 0.75:
                    room_parts.append(lines[j]["raw_text"])
            fields["room_raw"] = " ".join(room_parts)

    if not fields["bz_raw"] or not fields["room_raw"]:
        bz_raw, room_raw = extract_bc_and_room(lines)
        if bz_raw and not fields["bz_raw"]:
            fields["bz_raw"] = bz_raw
        if room_raw and not fields["room_raw"]:
            fields["room_raw"] = room_raw

    logging.debug("[OCR] Parsed fields: %s", fields)
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


from difflib import SequenceMatcher

def best_match(target, candidates):
    def score(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return max(candidates, key=lambda c: score(target, c), default=None)

def validate_with_rooms(fields, rooms, *, fuzzy_threshold: float = FUZZY_THRESHOLD):
    bz_raw = fields["bz_raw"]
    room_raw = fields["room_raw"]
    matched_bz = None
    matched_room = None

    for bz in rooms:
        if SequenceMatcher(None, bz_raw.lower(), bz.lower()).ratio() >= fuzzy_threshold:
            matched_bz = bz
            break

    if matched_bz:
        room_list = rooms[matched_bz]
        matched_room = _fuzzy_match(room_raw, room_list, fuzzy_threshold)

    logging.debug("[OCR] Final matched BZ: %s", matched_bz)
    logging.debug("[OCR] Final matched Room: %s", matched_room)

    return {
        "name": fields["name"],
        "date": fields["date"],
        "start": fields["start"],
        "end": fields["end"],
        "bz": matched_bz or "",
        "room": matched_room or ""
    }



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
        print("[DEBUG] OCR lines:", lines)
        parsed = parse_fields(lines)
        print("[DEBUG] Parsed fields:", parsed)
        validated = validate_with_rooms(parsed, rooms_by_bz, fuzzy_threshold=FUZZY_THRESHOLD)
        print("[DEBUG] Validated fields:", validated)
        return validated

    def on_finish(result_error):
        print("[DEBUG] on_finish called with:", result_error)
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
        return run_ocr(img)

    def on_result(result_error):
        result, error = result_error
        if error:
            logging.error("[OCR] OCR failed: %s", error)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{error}")
            return
        try:
            lines = result
            logging.debug("[OCR] Lines: %s", lines)
            parsed = parse_fields(lines)
            validated = validate_with_rooms(parsed, rooms_by_bz)
            update_gui_fields(validated, ctx)
        except Exception as e:
            logging.exception("[OCR] Parsing failed: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Ошибка при разборе OCR-результата:\n{e}")

    run_in_thread(do_ocr, on_result)

