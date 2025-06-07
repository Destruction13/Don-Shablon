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
try:
    from paddleocr import PaddleOCR
except Exception:  # pragma: no cover - optional dependency for tests
    PaddleOCR = None
from pathlib import Path

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread
import logging

# --- OCR configuration ---
# Threshold below which OCR results are ignored
SCORE_IGNORE_THRESHOLD = 0.7
# Threshold for accepting a value without fuzzy matching
SCORE_THRESHOLD = 0.82
# Fuzzy matching acceptance level
FUZZY_THRESHOLD = 0.72
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



_ocr_instance: Optional[PaddleOCR] = None


def _init_ocr() -> PaddleOCR:
    global _ocr_instance
    if _ocr_instance is None:
        if PaddleOCR is None:
            raise ImportError("PaddleOCR library is required for OCR operations")
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
            use_gpu=False     # ⬅️ убери, если запускаешь с GPU
        )

        logging.debug("[OCR] PaddleOCR успешно инициализирован")

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
    """Recognize text lines from an image using PaddleOCR.

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

    ocr = _init_ocr()
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    result = ocr.ocr(np.array(image), cls=True)
    logging.debug("[OCR] RAW PaddleOCR result: %s", result)

    lines: List[Dict] = []
    if isinstance(result, list) and result:
        for box, (txt, score) in result[0]:
            if score < ignore_threshold:
                continue
            lines.append({"text": txt.strip(), "score": float(score), "bbox": box})

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

def is_label_like(text, label, threshold: float = FUZZY_THRESHOLD) -> bool:
    return SequenceMatcher(None, text.lower(), label.lower()).ratio() > threshold

def save_debug_ocr_image(image: Image.Image, lines: List[Dict], path="ocr_debug_output.jpg"):
    """Save OCR debugging overlay and JSON info."""
    from paddleocr import draw_ocr

    if not lines:
        return

    boxes = [l["bbox"] for l in lines]
    txts = [l.get("text", "") for l in lines]
    scores = [l.get("score", 0.0) for l in lines]

    img_with_ocr = draw_ocr(np.array(image), boxes, txts, scores, font_path="C:/Windows/Fonts/arial.ttf")
    Image.fromarray(img_with_ocr).save(path)

    debug_info = []
    for line in lines:
        debug_info.append({
            "text": line.get("text", ""),
            "raw_text": line.get("raw_text", line.get("text", "")),
            "score": line.get("score", 0.0),
            "bbox": line["bbox"],
            "matched_field": line.get("matched_field", ""),
        })
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
    """Clean typical OCR mistakes in time strings."""
    cleaned = (
        text.replace("з", "3")
             .replace("o", "0")
             .replace("l", "1")
    )
    if re.fullmatch(r"\d:\d", cleaned):
        h, m = cleaned.split(":")
        cleaned = f"1{h}:{m}0"
    match = re.match(r"\d{1,2}:\d{2}", cleaned)
    return match.group(0) if match else cleaned

def is_label_like(text, label, threshold: float = FUZZY_THRESHOLD) -> bool:
    return SequenceMatcher(None, text.lower(), label.lower()).ratio() > threshold

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
    """Parse key fields from OCR results using bbox positions."""
    merged = merge_split_lines(ocr_lines)

    lines = []
    for l in merged:
        raw = l["text"].strip()
        if not raw:
            continue
        xs = [p[0] for p in l["bbox"]]
        ys = [p[1] for p in l["bbox"]]
        norm_generic = normalize_generic(raw)
        label_norm = normalize_russian(norm_generic)
        lines.append({
            "raw_text": raw,
            "text": norm_generic,
            "label_norm": label_norm,
            "score": float(l["score"]),
            "bbox": l["bbox"],
            "left": min(xs),
            "top": min(ys),
            "right": max(xs),
            "bottom": max(ys),
            "matched_field": "",
        })

    fields = {"name": "", "bz_raw": "", "room_raw": "", "date": "", "start": "", "end": ""}
    all_rooms = [r for rooms in rooms_by_bz.values() for r in rooms]

    for i, line in enumerate(lines):
        txt = line["label_norm"]
        base_x = line["left"]
        base_y = line["bottom"]

        if is_label_like(txt, "организатор") or has_organizer_typo(txt):
            parts = []
            for cand in lines[i+1:i+4]:
                if cand["score"] < 0.85:
                    continue
                if abs(cand["top"] - base_y) > 30 or abs(cand["left"] - base_x) > 200:
                    continue
                if any(is_label_like(cand["label_norm"], w) for w in ["участник", "опционал", "дата", "время"]):
                    continue
                parts.append(cand["raw_text"])
                cand["matched_field"] = "name"
                if len(parts) >= 3:
                    break
            if parts:
                fields["name"] = " ".join(parts)
                line["matched_field"] = "label"
                logging.info(
                    "[OCR] FIELD name='%s' from bbox=(%d, %d, %d, %d)",
                    fields["name"], line["left"], line["top"], line["right"], line["bottom"],
                )

        if is_label_like(txt, "дата"):
            for cand in lines[i+1:]:
                if abs(cand["top"] - base_y) > 50 or abs(cand["left"] - base_x) > 200:
                    continue
                m = re.search(r"\d{2}\.\d{2}\.\d{2,4}", cand["raw_text"])
                if m:
                    fields["date"] = m.group(0)
                    cand["matched_field"] = "date"
                    line["matched_field"] = "label"
                    logging.info(
                        "[OCR] FIELD date='%s' from bbox=(%d, %d, %d, %d)",
                        fields["date"], cand["left"], cand["top"], cand["right"], cand["bottom"],
                    )
                    break

        if is_label_like(txt, "время"):
            times = []
            for cand in lines[i+1:]:
                if abs(cand["top"] - base_y) > 50 or abs(cand["left"] - base_x) > 200:
                    continue
                val = fix_ocr_time_garbage(cand["raw_text"])
                if re.match(r"\d{1,2}:\d{2}", val):
                    times.append(val)
                    cand["matched_field"] = "time"
                    if len(times) == 2:
                        break
            if times:
                fields["start"] = times[0]
                if len(times) > 1:
                    fields["end"] = times[1]
                line["matched_field"] = "label"
                logging.info(
                    "[OCR] FIELD time='%s %s' from bbox=(%d, %d, %d, %d)",
                    fields["start"], fields["end"], line["left"], line["top"], line["right"], line["bottom"],
                )

        if is_label_like(txt, "бц") and i + 1 < len(lines):
            cand = lines[i + 1]
            if abs(cand["top"] - base_y) <= 50 and abs(cand["left"] - base_x) <= 200:
                fields["bz_raw"] = cand["raw_text"]
                cand["matched_field"] = "bz"
                line["matched_field"] = "label"
                logging.info(
                    "[OCR] FIELD bz='%s' from bbox=(%d, %d, %d, %d)",
                    fields["bz_raw"], cand["left"], cand["top"], cand["right"], cand["bottom"],
                )
                if i + 2 < len(lines) and not fields["room_raw"]:
                    next_room = lines[i + 2]
                    match = fuzzy_best_match(next_room["raw_text"], all_rooms, FUZZY_THRESHOLD)
                    if match:
                        fields["room_raw"] = next_room["raw_text"]
                        next_room["matched_field"] = "room"
        elif "бц" in line["raw_text"].lower() or "морозов" in line["raw_text"].lower():
            fields["bz_raw"] = line["raw_text"]
            line["matched_field"] = "bz"
            logging.info(
                "[OCR] FIELD bz='%s' from bbox=(%d, %d, %d, %d)",
                fields["bz_raw"], line["left"], line["top"], line["right"], line["bottom"],
            )
            if i + 1 < len(lines) and not fields["room_raw"]:
                next_room = lines[i + 1]
                match = fuzzy_best_match(next_room["raw_text"], all_rooms, FUZZY_THRESHOLD)
                if match:
                    fields["room_raw"] = next_room["raw_text"]
                    next_room["matched_field"] = "room"

        if is_label_like(txt, "переговорка"):
            candidate_parts = []
            for cand in lines[i+1:]:
                if abs(cand["top"] - base_y) > 50 or abs(cand["left"] - base_x) > 200:
                    continue
                if any(is_label_like(cand["label_norm"], w) for w in ["адрес", "параметр", "выбрать"]):
                    continue
                candidate_parts.append(cand)
                if len(candidate_parts) >= 2:
                    break
            if candidate_parts:
                candidate_text = " ".join(p["raw_text"] for p in candidate_parts)
                match = fuzzy_best_match(candidate_text, all_rooms, FUZZY_THRESHOLD)
                if match:
                    fields["room_raw"] = candidate_text
                    for p in candidate_parts:
                        p["matched_field"] = "room"
                    line["matched_field"] = "label"
                    logging.info(
                        "[OCR] Fuzzy matched '%s' -> '%s' (score=%.2f)",
                        candidate_text, match, SequenceMatcher(None, candidate_text.lower(), match.lower()).ratio(),
                    )
                else:
                    logging.info("[OCR] Room candidate '%s' rejected", candidate_text)

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

