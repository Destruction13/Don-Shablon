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
import json
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
            .replace("3", "з")
    )


def normalize_generic(text: str) -> str:
    return text.lower().strip()


def fix_ocr_time_garbage(text: str) -> str:
    """Replace common OCR misreads in time strings."""
    return (
        text.replace("з", "3")
        .replace("o", "0")
        .replace("l", "1")
    )


def clean_name(text: str) -> str:
    """Remove duration suffixes from organizer name."""
    return re.sub(r"\s*(?:-?\d+ч|\(.*?ч\)|на \d+ч).*", "", text).strip()


def normalize_time(text: str) -> str | None:
    """Normalize various time formats to HH:MM."""
    txt = fix_ocr_time_garbage(text).replace(".", ":")
    if re.fullmatch(r"\d{1,2}:\d{2}", txt):
        h, m = txt.split(":")
        return f"{int(h):02d}:{m}"
    if re.fullmatch(r"\d{3,4}", txt):
        if len(txt) == 3:
            txt = "0" + txt
        return f"{txt[:2]}:{txt[2:]}"
    return None


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
        Lines with score below this value will be kept but marked as low score.

    Returns
    -------
    List[Dict]
        Each dict contains ``text``, ``score`` and ``bbox``. Low confidence
        entries have ``low_score`` set to ``True``.
    """

    reader = _init_ocr()
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    result = reader.readtext(np.array(image))
    logging.debug("[OCR] RAW EasyOCR result: %s", result)

    lines: List[Dict] = []
    for bbox, text, score in result:
        low_score = score < ignore_threshold
        if low_score:
            logging.warning("[OCR] Low confidence %.2f for text '%s'", score, text)
        bbox_int = [[int(x), int(y)] for x, y in bbox]
        lines.append({
            "text": text.strip(),
            "score": float(score),
            "bbox": bbox_int,
            "raw_text": text.strip(),
            "low_score": low_score,
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


def is_any_label(text: str, labels: List[str]) -> bool:
    """Return True if text is similar to any label from the list."""
    return any(is_label_like(text, lbl) for lbl in labels)

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


def extract_bc_and_room(lines: List[Dict], known_bz: List[str]) -> Tuple[str, str]:
    """Try to extract business center and room from OCR lines."""
    bz_raw = ""
    room_raw = ""

    for i, line in enumerate(lines):
        lower = line["text"].lower()

        # Находим подходящий БЦ
        matched_bz = None
        for bz in known_bz:
            if bz.lower() in lower:
                matched_bz = bz
                break

        if matched_bz:
            bz_raw = matched_bz

            # Попробуем взять переговорку на следующих 1–3 строках
            for j in range(i + 1, min(len(lines), i + 4)):
                candidate = lines[j]["text"].strip()
                if candidate:
                    room_raw = candidate
                    break
            break  # Выход из цикла — нашли

    return bz_raw, room_raw




# -----------------------------------------------
# Основной парсер
# -----------------------------------------------
def parse_fields(ocr_lines: list, *, return_scores: bool = False):
    """Parse OCR lines into structured fields.

    Parameters
    ----------
    ocr_lines : list
        Output from :func:`run_ocr`.
    return_scores : bool
        Also return confidence score for each field.
    """

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
    scores = {"name": 0.0, "bz_raw": 0.0, "room_raw": 0.0, "date": 0.0, "start": 0.0, "end": 0.0}

    bz_idx = None

    for i, line in enumerate(lines):
        txt_norm = line["norm"]

        if is_label_like(txt_norm, "организатор"):
            if line["score"] < SCORE_THRESHOLD:
                logging.warning(
                    "[OCR] Low confidence label 'Организатор' (%.2f)", line["score"]
                )
            parts = []
            part_scores = []
            for j in range(i + 1, i + 3):
                if j >= len(lines):
                    break
                jnorm = lines[j]["norm"]
                if (
                    is_label_like(jnorm, "участники")
                    or "участник" in jnorm
                    or is_any_label(jnorm, [
                        "время",
                        "время и дата",
                        "дата",
                        "дата и время",
                        "переговорка",
                        "место",
                        "адрес",
                        "бц",
                    ])
                ):
                    break
                parts.append(lines[j]["text"])
                part_scores.append(lines[j]["score"])
            if parts:
                # Используем только первое слово для большей стабильности
                first_word = parts[0].split()[0]
                fields["name"] = clean_name(first_word)
                scores["name"] = part_scores[0]
            continue

        if is_any_label(txt_norm, ["время", "время и дата", "дата и время"]):
            time_scores = []
            times = []
            for j in range(i + 1, i + 5):  # allow for date line in between
                if j >= len(lines):
                    break
                t = normalize_time(lines[j]["raw_text"])
                if t:
                    times.append(t)
                    time_scores.append(lines[j]["score"])
            if times:
                fields["start"] = times[0]
                scores["start"] = time_scores[0]
                if len(times) > 1:
                    fields["end"] = times[1]
                    scores["end"] = time_scores[1]
            continue

        if is_label_like(txt_norm, "дата") and not fields["date"]:
            for j in range(i + 1, i + 3):
                if j >= len(lines):
                    break
                candidate = lines[j]["raw_text"]
                if re.match(r"\d{2}\.\d{2}\.\d{2,4}", candidate):
                    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
                        try:
                            datetime.strptime(candidate, fmt)
                            fields["date"] = candidate
                            scores["date"] = lines[j]["score"]
                            break
                        except ValueError:
                            continue
                if fields["date"]:
                    break
            continue

        if ("бц" in txt_norm or txt_norm.startswith("бц")) and not fields["bz_raw"]:
            fields["bz_raw"] = line["text"]
            scores["bz_raw"] = line["score"]
            bz_idx = i
            continue

        if is_label_like(txt_norm, "переговорка") and not fields["room_raw"]:
            room_parts = []
            room_scores = []
            for j in range(i + 1, i + 4):
                if j >= len(lines):
                    break
                jnorm = lines[j]["norm"]
                candidate_text = lines[j]["text"].strip()
                if (
                    is_label_like(jnorm, "адрес")
                    or "выбрать" in jnorm
                    or "бц" in jnorm
                    or len(candidate_text) <= 2
                ):
                    continue
                room_parts.append(candidate_text)
                room_scores.append(lines[j]["score"])
            if room_parts:
                fields["room_raw"] = " ".join(room_parts)
                scores["room_raw"] = min(room_scores)
            continue


    if bz_idx is not None and (not fields["room_raw"] or "бц" in normalize_generic(fields["room_raw"])):
        for j in range(bz_idx + 1, min(len(lines), bz_idx + 4)):
            if is_label_like(lines[j]["norm"], "адрес") or "выбрать" in lines[j]["norm"]:
                continue
            fields["room_raw"] = lines[j]["text"]
            scores["room_raw"] = lines[j]["score"]
            break

    if not fields["start"] or not fields["end"]:
        time_re = re.compile(r"\d{2}[:\.]\d{2}")
        found: list[tuple[str, float]] = []
        for line in ocr_lines:
            text = line["text"].strip()
            if not re.fullmatch(r"\d{1,2}[:\.]\d{2}", text):
                continue
            t = normalize_time(line["text"].strip())
            if not t:
                continue
            if not found or found[-1][0] != t:
                found.append((t, line["score"]))
        if found:
            if not fields["start"]:
                fields["start"], scores["start"] = found[0]
            if len(found) > 1 and not fields["end"]:
                start_val = fields["start"]
                idx = next((i for i, (tt, _) in enumerate(found) if tt == start_val), 0)
                if idx + 1 < len(found):
                    fields["end"], scores["end"] = found[idx + 1]

    if not fields["date"]:
        for line in ocr_lines:
            if line.get("score", 0) < 0.45:
                continue
            if re.match(r"\d{2}\.\d{2}\.\d{2,4}", line["text"]):
                for fmt in ("%d.%m.%Y", "%d.%m.%y"):
                    try:
                        datetime.strptime(line["text"], fmt)
                        fields["date"] = line["text"]
                        scores["date"] = line["score"]
                        break
                    except ValueError:
                        continue
                if fields["date"]:
                    break

    if not fields["bz_raw"] or not fields["room_raw"]:
        known_bz = list(rooms_by_bz.keys())
        bz_raw, room_raw = extract_bc_and_room(lines, known_bz)
        if bz_raw and not fields["bz_raw"]:
            fields["bz_raw"] = bz_raw
        if room_raw and not fields["room_raw"]:
            fields["room_raw"] = room_raw

    logging.debug("[OCR] Parsed fields: %s", fields)
    if return_scores:
        return fields, scores
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
    cleanup = lambda t: [w for w in re.findall(r"\w+", t.lower()) if w not in {"этаж", "мест", "место", "этажей"} and not w.isdigit()]
    tokens_room = set(cleanup(room))
    tokens_cand = set(cleanup(candidate))
    if not tokens_room:
        return 0.0
    return len(tokens_room & tokens_cand) / len(tokens_room)


from difflib import SequenceMatcher

def best_match(target, candidates):
    def score(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return max(candidates, key=lambda c: score(target, c), default=None)

def validate_with_rooms(
    fields: Dict[str, str],
    rooms: Dict[str, List[str]],
    *,
    fuzzy_threshold: float = FUZZY_THRESHOLD,
    override_bz: str | None = None,
) -> Dict[str, str]:
    """Validate and match BZ and room using fuzzy search."""

    bz_raw = fields.get("bz_raw", "")
    room_raw = fields.get("room_raw", "")

    matched_bz = None
    for bz in rooms:
        if SequenceMatcher(None, bz_raw.lower(), bz.lower()).ratio() >= fuzzy_threshold:
            matched_bz = bz
            break

    if not matched_bz and override_bz and override_bz in rooms:
        matched_bz = override_bz

    matched_room = None
    if matched_bz:
        candidates = rooms[matched_bz]
        best = None
        best_score = 0.0
        for cand in candidates:
            ratio = _room_token_ratio(room_raw, cand)
            if ratio > best_score:
                best_score = ratio
                best = cand
        if best and best_score >= 0.4:
            matched_room = best
        else:
            short = room_raw.split('.')[-1].split()[0].lower()
            if len(short) > 3:
                for cand in candidates:
                    if short in cand.lower():
                        matched_room = cand
                        logging.warning(
                            "[OCR] Room matched by short word '%s' despite low fuzzy score %.2f",
                            short,
                            best_score,
                        )
                        break

    if not matched_bz:
        logging.warning("[OCR] Failed to match business center for '%s'", bz_raw)
    if matched_bz and not matched_room and room_raw:
        logging.warning("[OCR] Failed to match room '%s' in BZ '%s'", room_raw, matched_bz)

    logging.debug("[OCR] Final matched BZ: %s", matched_bz)
    logging.debug("[OCR] Final matched Room: %s", matched_room)

    return {
        "name": fields.get("name", ""),
        "date": fields.get("date", ""),
        "start": fields.get("start", ""),
        "end": fields.get("end", ""),
        "bz": matched_bz or "",
        "room": matched_room or "",
    }



def update_gui_fields(
    data: Dict[str, str],
    ctx: UIContext,
    *,
    scores: Dict[str, float] | None = None,
) -> None:
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

    try:
        with open("final_fields.json", "w", encoding="utf-8") as f:
            json.dump({"fields": data, "scores": scores or {}}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("[OCR] Failed to write final_fields.json: %s", e)


def on_clipboard_button_click(ctx: UIContext) -> None:
    """Entry point for the clipboard OCR workflow."""
    img = get_image_from_clipboard()
    if img is None:
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
        return

    def worker():
        lines = run_ocr(img)
        print("[DEBUG] OCR lines:", lines)
        parsed, scores = parse_fields(lines, return_scores=True)
        print("[DEBUG] Parsed fields:", parsed)
        validated = validate_with_rooms(parsed, rooms_by_bz, fuzzy_threshold=FUZZY_THRESHOLD)
        print("[DEBUG] Validated fields:", validated)
        return validated, scores

    def on_finish(result_error):
        print("[DEBUG] on_finish called with:", result_error)
        result_tuple, error = result_error
        if error:
            logging.error("[OCR] Pipeline failed: %s", error)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{error}")
            return
        result, scores = result_tuple
        if not any(result.values()):
            QMessageBox.information(ctx.window, "Предупреждение", "Не удалось распознать данные")
            return
        update_gui_fields(result, ctx, scores=scores)

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
        result_tuple, error = result_error
        if error:
            logging.error("[OCR] OCR failed: %s", error)
            QMessageBox.critical(ctx.window, "Ошибка", f"Не удалось распознать изображение:\n{error}")
            return
        try:
            lines = result_tuple
            logging.debug("[OCR] Lines: %s", lines)
            parsed, scores = parse_fields(lines, return_scores=True)
            validated = validate_with_rooms(parsed, rooms_by_bz)
            if not any(validated.values()):
                QMessageBox.information(ctx.window, "Предупреждение", "Не удалось распознать данные")
                return
            update_gui_fields(validated, ctx, scores=scores)
        except Exception as e:
            logging.exception("[OCR] Parsing failed: %s", e)
            QMessageBox.critical(ctx.window, "Ошибка", f"Ошибка при разборе OCR-результата:\n{e}")

    run_in_thread(do_ocr, on_result)

