import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from rapidfuzz import fuzz, process
import cv2

import numpy as np
from PIL import Image, ImageGrab, ImageQt, ImageDraw, ImageFont
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMessageBox
try:
    from PySide6.QtCore import QDate, QTime
except Exception:
    class QDate:
        def __init__(self, *args, **kwargs):
            pass

    class QTime:
        def __init__(self, h=0, m=0):
            self._h = h
            self._m = m
import json
from pathlib import Path

from constants import rooms_by_bz
from logic.app_state import UIContext
from logic.utils import run_in_thread


# --- OCR конфигурация ---
SCORE_IGNORE_THRESHOLD = 0.7
SCORE_THRESHOLD = 0.82
FUZZY_THRESHOLD = 0.75
BBOX_Y_TOLERANCE = 25
SPLIT_TOKEN_MAX_GAP = 70
FORCE_FUZZY = True

# Checkbox конфигурация
CHECKBOX_X_OFFSET = 55
CHECKBOX_SIZE = 37
CHECKBOX_THRESHOLD = 170
CHECKBOX_DARK_RATIO = 0.07

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



from typing import Any

_ocr_instance: Any = None


_ocr_gpu = False


def _init_ocr(use_gpu: bool = False):
    global _ocr_instance, _ocr_gpu
    if _ocr_instance is None or _ocr_gpu != use_gpu:
        logging.debug("[OCR] Initializing EasyOCR (GPU=%s)", use_gpu)
        try:
            import easyocr
        except Exception as e:
            logging.error("[OCR] Failed to import EasyOCR: %s", e)
            raise
        _ocr_instance = easyocr.Reader(['ru'], gpu=use_gpu)
        _ocr_gpu = use_gpu
        logging.debug("[OCR] EasyOCR successfully initialized")

    return _ocr_instance


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
    """Исправить типичные ошибки распознавания времени."""
    return (
        text.replace("з", "3")
        .replace("o", "0")
        .replace("l", "1")
    )


def clean_name(text: str) -> str:
    """Убрать указание продолжительности из имени организатора."""
    return re.sub(r"\s*(?:-?\d+ч|\(.*?ч\)|на \d+ч).*", "", text).strip()


def normalize_time(text: str) -> str | None:
    """Преобразовать разные форматы времени к HH:MM."""
    txt = fix_ocr_time_garbage(text).replace(".", ":")
    if re.fullmatch(r"\d{1,2}:\d{2}", txt):
        h, m = txt.split(":")
        return f"{int(h):02d}:{m}"
    if re.fullmatch(r"\d{3,4}", txt):
        if len(txt) == 3:
            txt = "0" + txt
        return f"{txt[:2]}:{txt[2:]}"
    return None



def get_image_from_clipboard() -> Optional[Image.Image]:
    """Получить изображение из буфера обмена или ``None``."""
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


def run_ocr(
    image: Image.Image,
    *,
    ignore_threshold: float = SCORE_IGNORE_THRESHOLD,
    use_gpu: bool = False,
) -> Tuple[List[Dict], str]:
    """Распознать текст на изображении при помощи EasyOCR."""

    reader = _init_ocr(use_gpu)
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    result = reader.readtext(np.array(image))

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

    meeting_type, rep_bbox, cb_bbox = detect_repeat_checkbox(image, lines)
    save_debug_ocr_image(
        image,
        lines,
        repeat_bbox=rep_bbox,
        checkbox_bbox=cb_bbox,
        checkbox_checked=meeting_type == "Регулярная",
    )
    return lines, meeting_type

def extract_fields_from_text(texts, rooms_by_bz):
    """Выделить основные поля из списка строк OCR."""
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


def recognize_from_clipboard(ctx: UIContext) -> None:
    """Распознать встречу по изображению из буфера обмена."""
    img = get_image_from_clipboard()
    if img is None:
        QMessageBox.critical(ctx.window, "Ошибка", "Буфер обмена не содержит изображение.")
        return

    lines, meeting_type = run_ocr(img, use_gpu=ctx.ocr_mode == "GPU")
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
    update_gui_fields(validated, ctx, scores=scores, meeting_type=meeting_type)
    if getattr(ctx, "auto_generate_after_autofill", False):
        from logic.generator import generate_message
        generate_message(ctx)
    
def is_label_like(text, label):
    """Проверить схожесть текста с заданной меткой."""
    return SequenceMatcher(None, text.lower(), label.lower()).ratio() > 0.7


def is_any_label(text: str, labels: List[str]) -> bool:
    """Вернуть ``True``, если текст похож хотя бы на одну метку."""
    return any(is_label_like(text, lbl) for lbl in labels)

def save_debug_ocr_image(
    image: Image.Image,
    lines: List[Dict],
    path: str = "ocr_debug_output.jpg",
    *,
    repeat_bbox: Tuple[int, int, int, int] | None = None,
    checkbox_bbox: Tuple[int, int, int, int] | None = None,
    checkbox_checked: bool | None = None,
):
    """Сохранить изображение с разметкой и JSON для отладки."""

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

    if repeat_bbox:
        x, y, w, h = repeat_bbox
        draw.rectangle([x, y, x + w, y + h], outline="blue", width=2)
    if checkbox_bbox:
        x, y, w, h = checkbox_bbox
        color = "green" if checkbox_checked else "red"
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)

    img_copy.save(path)

    debug_info = [
        {"text": line["text"], "score": line["score"], "bbox": line["bbox"]}
        for line in lines
    ]
    with open(Path(path).with_suffix(".json"), "w", encoding="utf-8") as f:
        import json
        json.dump(debug_info, f, ensure_ascii=False, indent=2)


def detect_repeat_checkbox(
    image: Image.Image, lines: List[Dict]
) -> Tuple[str, Tuple[int, int, int, int] | None, Tuple[int, int, int, int] | None]:
    """Определить тип встречи по чекбоксу рядом с меткой 'Повторять'."""
    meeting_type = "Обычная"
    repeat_bbox = None
    checkbox_bbox = None
    np_img = np.array(image)

    found_repeat = False

    for line in lines:
        if "повторять" in normalize_russian(line["text"]).lower():
            found_repeat = True
            x1 = min(p[0] for p in line["bbox"])
            y1 = min(p[1] for p in line["bbox"])
            x2 = max(p[0] for p in line["bbox"])
            y2 = max(p[1] for p in line["bbox"])
            w = x2 - x1
            h = y2 - y1
            repeat_bbox = (x1, y1, w, h)

            cb_x1 = max(x1 - CHECKBOX_X_OFFSET, 0)
            cb_y1 = max(int(y1 + h / 2 - CHECKBOX_SIZE / 2), 0)
            cb_x2 = min(cb_x1 + CHECKBOX_SIZE, np_img.shape[1])
            cb_y2 = min(cb_y1 + CHECKBOX_SIZE, np_img.shape[0])
            checkbox_bbox = (cb_x1, cb_y1, cb_x2 - cb_x1, cb_y2 - cb_y1)

            roi = np_img[cb_y1:cb_y2, cb_x1:cb_x2]
            if roi.size > 0:
                cv2.imwrite("checkbox_roi.jpg", roi)
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, CHECKBOX_THRESHOLD, 255, cv2.THRESH_BINARY)
                dark_ratio = (gray < CHECKBOX_THRESHOLD).mean()
                # ДЕБАГ
                print(f"[DEBUG] dark_ratio = {dark_ratio:.4f}")
                if dark_ratio > CHECKBOX_DARK_RATIO:
                    meeting_type = "Регулярная"
            break

    if not found_repeat:
        # Поле "Повторять" отсутствует. Это может означать, что встреча регулярная
        # Проверяем блок справа от "Весь день" на наличие текста "Повторять" и его фрагментов
        all_day_boxes = []
        for line in lines:
            norm = normalize_russian(line["text"]).lower()
            if "весь" in norm and "день" in norm:
                all_day_boxes.append(line["bbox"])

        fragments = ["повт", "торят", "повтор"]

        for box in all_day_boxes:
            x_right = max(p[0] for p in box)
            y_top = min(p[1] for p in box)
            y_bottom = max(p[1] for p in box)
            fragment_found = False
            for ln in lines:
                lx1 = min(p[0] for p in ln["bbox"])
                lx2 = max(p[0] for p in ln["bbox"])
                ly1 = min(p[1] for p in ln["bbox"])
                ly2 = max(p[1] for p in ln["bbox"])
                if lx1 >= x_right and ly1 <= y_bottom and ly2 >= y_top:
                    txt_norm = normalize_russian(ln["text"]).lower()
                    if any(frag in txt_norm for frag in fragments):
                        fragment_found = True
                        break
            if not fragment_found:
                meeting_type = "Регулярная"
                break

    return meeting_type, repeat_bbox, checkbox_bbox


def extract_bc_and_room(lines: List[Dict], known_bz: List[str]) -> Tuple[str, str]:
    """Попытаться найти БЦ и переговорку в тексте OCR."""
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
    """Разобрать строки OCR в структурированные поля."""

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
            for j in range(i + 1, i + 5):
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




def _room_token_ratio(room: str, candidate: str) -> float:
    cleanup = lambda t: [w for w in re.findall(r"\w+", t.lower()) if w not in {"этаж", "мест", "место", "этажей"} and not w.isdigit()]
    tokens_room = set(cleanup(room))
    tokens_cand = set(cleanup(candidate))
    if not tokens_room:
        return 0.0
    return len(tokens_room & tokens_cand) / len(tokens_room)


_CYR_TO_LAT = str.maketrans({
    "а": "a", "А": "A",
    "в": "b", "В": "B",
    "е": "e", "Е": "E",
    "к": "k", "К": "K",
    "м": "m", "М": "M",
    "н": "h", "Н": "H",
    "о": "o", "О": "O",
    "р": "p", "Р": "P",
    "с": "c", "С": "C",
    "т": "t", "Т": "T",
    "у": "y", "У": "Y",
    "х": "x", "Х": "X",
    "ё": "e", "Ё": "E",
})

_OCR_ROOM_FIX = str.maketrans({
    "Х": "X", "х": "x",
    "М": "M", "м": "m",
    "Ц": "L", "ц": "l",
})

def clean_room_for_matching(text: str) -> str:
    """Подготовить название переговорки для сравнения."""
    text = re.sub(r"\s*\d+\s*этаж.*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _normalize_room(text: str) -> str:
    """Привести название переговорки к виду для поиска."""
    text = normalize_russian(text)
    text = text.lower()
    text = re.sub(r"[^a-zа-я0-9]+", "", text)
    return text


def _fix_ocr_room_chars(text: str) -> str:
    """Исправить типичные ошибки распознавания латиницы как кириллицы."""
    return text.translate(_OCR_ROOM_FIX)


def _normalize_room_with_ocr_fixes(text: str) -> str:
    """Нормализовать название переговорки с учётом OCR-исправлений."""
    return _normalize_room(_fix_ocr_room_chars(text))


def _strip_prefix_for_match(text: str) -> str:
    """Убрать префикс вида "<цифра>[буква]." в начале."""
    return re.sub(r"^[1-9][A-ZА-Яа-я]?\.", "", text).strip()


def validate_with_rooms(
    fields: Dict[str, str],
    rooms: Dict[str, List[str]],
    *,
    fuzzy_threshold: float = FUZZY_THRESHOLD,
    override_bz: str | None = None,
) -> Dict[str, str]:
    """Сопоставить БЦ и переговорку с использованием нечёткого поиска."""

    bz_raw = fields.get("bz_raw", "")
    room_raw = fields.get("room_raw", "")

    room_for_match = clean_room_for_matching(_strip_prefix_for_match(room_raw))

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

        if room_raw:
            matches = process.extract(
                room_for_match,
                candidates,
                processor=_normalize_room,
                scorer=fuzz.ratio,
                limit=3,
            )
            top3 = [(m[0], round(m[1] / 100, 2)) for m in matches]
            if matches:
                best_candidate, best_score_raw, _ = matches[0]
                best_score = best_score_raw / 100
                logging.debug(
                    "[OCR] Room fuzzy pass1 '%s' -> '%s' (%.2f), top3=%s",
                    room_raw,
                    best_candidate,
                    best_score,
                    top3,
                )
                if best_score >= fuzzy_threshold:
                    matched_room = best_candidate
            else:
                logging.debug(
                    "[OCR] Room fuzzy matching produced no candidates for '%s'",
                    room_raw,
                )

        if room_raw and not matched_room:
            matches2 = process.extract(
                room_for_match,
                candidates,
                processor=_normalize_room_with_ocr_fixes,
                scorer=fuzz.ratio,
                limit=3,
            )
            top3_2 = [(m[0], round(m[1] / 100, 2)) for m in matches2]
            if matches2:
                cand2, score_raw2, _ = matches2[0]
                score2 = score_raw2 / 100
                logging.debug(
                    "[OCR] Room fuzzy pass2 '%s' -> '%s' (%.2f), top3=%s",
                    room_raw,
                    cand2,
                    score2,
                    top3_2,
                )
                if score2 >= fuzzy_threshold:
                    matched_room = cand2
                else:
                    logging.warning(
                        "[OCR] Room fuzzy score below threshold %.2f after OCR fixes; top3=%s",
                        score2,
                        top3_2,
                    )
            else:
                logging.debug(
                    "[OCR] Room fuzzy (OCR fixes) produced no candidates for '%s'",
                    room_raw,
                )

        if not matched_room:
            best = None
            best_score = 0.0
            for cand in candidates:
                ratio = _room_token_ratio(room_for_match, cand)
                if ratio > best_score:
                    best_score = ratio
                    best = cand
            if best and best_score >= 0.4:
                matched_room = best
            else:
                if room_raw:
                    parts = room_for_match.split('.')
                    last_part = parts[-1] if parts else ""
                    words = last_part.split()
                    if words:
                        short = words[0].lower()
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
    meeting_type: str | None = None,
) -> None:
    """Заполнить элементы интерфейса распознанными данными."""
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
        try:
            h, m = map(int, data["start"].split(":"))
            ctx.fields["start_time"].setTime(QTime(h, m))
        except Exception:
            pass
    if data.get("end") and "end_time" in ctx.fields:
        try:
            h, m = map(int, data["end"].split(":"))
            ctx.fields["end_time"].setTime(QTime(h, m))
        except Exception:
            pass
    if "regular" in ctx.fields:
        value = meeting_type if meeting_type else "Обычная"
        ctx.fields["regular"].setCurrentText(value)



