from datetime import datetime
import random

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QDateEdit,
    QTextEdit,
    QMessageBox,
    QToolButton,
)
from PySide6.QtCore import QDate, Qt

from logic.room_filter import FilteringComboBox

from logic.app_state import UIContext
from constants import rooms_by_bz
from logic.utils import format_date_ru, parse_yandex_calendar_url


class ClickableDateEdit(QDateEdit):
    """Date edit that opens the calendar when focused or clicked."""

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setCalendarPopup(True)
        if self.calendarWidget():
            self.calendarWidget().show()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.setCalendarPopup(True)
        if self.calendarWidget():
            self.calendarWidget().show()


def clear_layout(layout: QVBoxLayout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()


def add_field(label: str, name: str, ctx: UIContext, clear: bool = False):
    container = QWidget()
    hl = QHBoxLayout(container)
    lbl = QLabel(label)
    edit = QLineEdit()
    hl.addWidget(lbl)
    hl.addWidget(edit)
    if clear:
        btn = QToolButton()
        btn.setText("✖")
        btn.setFocusPolicy(Qt.NoFocus)
        btn.clicked.connect(edit.clear)
        hl.addWidget(btn)
    ctx.fields[name] = edit
    ctx.fields_layout.addWidget(container)
    if name == "link":
        edit.textChanged.connect(lambda _: on_link_change(ctx))


def add_combo(label: str, name: str, values: list[str], ctx: UIContext):
    container = QWidget()
    hl = QHBoxLayout(container)
    lbl = QLabel(label)
    combo = QComboBox()
    combo.addItems(values)
    hl.addWidget(lbl)
    hl.addWidget(combo)
    ctx.fields[name] = combo
    ctx.fields_layout.addWidget(container)


def add_room_field(label: str, name: str, bz_name: str, ctx: UIContext):
    container = QWidget()
    hl = QHBoxLayout(container)
    lbl = QLabel(label)
    combo = FilteringComboBox()

    def update_rooms():
        bz = ctx.fields.get(bz_name).currentText() if bz_name in ctx.fields else ''
        rooms = rooms_by_bz.get(bz, [])
        combo.set_items(rooms)

    if bz_name in ctx.fields:
        ctx.fields[bz_name].currentTextChanged.connect(update_rooms)
    update_rooms()

    hl.addWidget(lbl)
    hl.addWidget(combo)
    btn = QToolButton()
    btn.setText("✖")
    btn.setFocusPolicy(Qt.NoFocus)
    btn.clicked.connect(lambda: combo.setEditText(""))
    hl.addWidget(btn)
    ctx.fields[name] = combo
    ctx.fields_layout.addWidget(container)


def add_date(name: str, ctx: UIContext):
    container = QWidget()
    hl = QHBoxLayout(container)
    lbl = QLabel("Дата:")
    date_edit = ClickableDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("dd.MM.yyyy")
    date_edit.setDate(QDate.currentDate())
    hl.addWidget(lbl)
    hl.addWidget(date_edit)
    ctx.fields[name] = date_edit
    ctx.fields_layout.addWidget(container)


def add_time_range(start_name: str, end_name: str, ctx: UIContext):
    container = QWidget()
    hl = QHBoxLayout(container)
    start_combo = QComboBox()
    end_combo = QComboBox()
    start_combo.setEditable(True)
    end_combo.setEditable(True)
    times = [f"{h:02d}:{m:02d}" for h in range(8, 22) for m in (0, 30)]
    start_combo.addItems(times)
    start_combo.currentTextChanged.connect(
        lambda val: update_end_times(val, end_combo, times)
    )
    hl.addWidget(QLabel("Начало:"))
    hl.addWidget(start_combo)
    btn_clear_start = QToolButton()
    btn_clear_start.setText("✖")
    btn_clear_start.setFocusPolicy(Qt.NoFocus)
    btn_clear_start.clicked.connect(lambda: start_combo.setCurrentIndex(-1))
    hl.addWidget(btn_clear_start)
    hl.addWidget(QLabel("Конец:"))
    hl.addWidget(end_combo)
    btn_clear_end = QToolButton()
    btn_clear_end.setText("✖")
    btn_clear_end.setFocusPolicy(Qt.NoFocus)
    btn_clear_end.clicked.connect(lambda: end_combo.setCurrentIndex(-1))
    hl.addWidget(btn_clear_end)
    ctx.fields[start_name] = start_combo
    ctx.fields[end_name] = end_combo
    ctx.fields_layout.addWidget(container)


def update_end_times(start: str, end_combo: QComboBox, all_slots: list[str]):
    if start in all_slots:
        idx = all_slots.index(start)
        end_combo.clear()
        end_combo.addItems(all_slots[idx + 1:])


def update_fields(ctx: UIContext):
    clear_layout(ctx.fields_layout)
    ctx.fields.clear()
    typ = ctx.type_combo.currentText()

    if typ == "Актуализация":
        add_field("Имя:", "name", ctx)
        add_field("Ссылка:", "link", ctx, clear=True)
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_combo("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)
        add_room_field("Переговорка:", "room", "bz", ctx)
        add_combo("Тип встречи:", "regular", ["Обычная", "Регулярная"], ctx)
    elif typ == "Обмен":
        add_field("Имя:", "name", ctx)
        add_field("Ссылка:", "link", ctx, clear=True)
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_combo("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)
        add_room_field("Его переговорка:", "his_room", "bz", ctx)
        add_room_field("Твоя переговорка:", "my_room", "bz", ctx)
        add_combo("Тип встречи:", "regular", ["Обычная", "Регулярная"], ctx)
    elif typ == "Разовая встреча":
        add_field("Имя:", "name", ctx)
        add_field("Ссылка:", "link", ctx, clear=True)
        add_field("Название встречи:", "meeting_name", ctx)
        add_field("Продолжительность:", "duration", ctx)
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_field("Ссылка пересечения 1:", "conflict1", ctx)
        add_field("Ссылка пересечения 2:", "conflict2", ctx)
        add_field("Ссылка пересечения 3:", "conflict3", ctx)
        add_field("Имя заказчика:", "client_name", ctx)


def on_link_change(ctx: UIContext):
    url_widget = ctx.fields.get("link")
    if not url_widget:
        return
    url = url_widget.text()
    date_str, time_str = parse_yandex_calendar_url(url)
    if date_str and time_str and "datetime" in ctx.fields:
        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            ctx.fields["datetime"].setDate(QDate(dt.year, dt.month, dt.day))
        except Exception:
            pass
        try:
            h, m = map(int, time_str.split(":"))
            h = (h + 3) % 24
            start_str = f"{h:02d}:{m:02d}"
            ctx.fields["start_time"].setCurrentText(start_str)
        except Exception:
            pass


def generate_message(ctx: UIContext):
    typ = ctx.type_combo.currentText()
    get = lambda name: ctx.fields.get(name).text() if isinstance(ctx.fields.get(name), QLineEdit) else ctx.fields.get(name).currentText() if isinstance(ctx.fields.get(name), QComboBox) else ''
    start = get("start_time")
    end = get("end_time")
    if start and end:
        time_part = f", в {start} — {end}"
    elif start:
        time_part = f", в {start}"
    else:
        time_part = ""
    name = get("name")
    if not name or ((typ == "Актуализация" and not get("room")) or (typ == "Обмен" and (not get("his_room") or not get("my_room")))):
        QMessageBox.warning(ctx.window, "Предупреждение", "Заполните имя и переговорку")
        return
    if "datetime" not in ctx.fields:
        QMessageBox.critical(ctx.window, "Ошибка", "Сначала выберите тип встречи")
        return
    raw_date = ctx.fields["datetime"].date().toPython()
    formatted = format_date_ru(raw_date)
    link = get("link")
    link_part = f" ({link})" if link else ""
    greeting = f"Привет, {name}!"
    if ctx.ls_active and ctx.ls_saved:
        greeting = f"Привет, {name}! Я {ctx.user_name}, ассистент. Приятно познакомиться!"
        gender = ctx.user_gender
    elif ctx.asya_mode:
        greeting = f"Привет, {name}! Я Ася, ассистент. Приятно познакомиться!"
        gender = "ж"
    else:
        gender = "ж"
    thanks_word = "признательна" if gender == "ж" else "признателен"
    myself_word = "сама" if gender == "ж" else "сам"
    if typ == "Актуализация":
        room = get("room")
        regular = get("regular")
        is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
        share_word = "разово поделиться" if regular.lower() == "регулярная" else "поделиться"
        msg = f"""{greeting}

У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {room}.

Уточни, пожалуйста, сможешь ли {share_word} переговорной?
Буду очень {thanks_word}!

Если сможешь, то сделаю всё {myself_word}. Только не удаляй её из встречи, чтобы не потерять :)"""
    elif typ == "Обмен":
        his_room = get("his_room")
        my_room = get("my_room")
        regular = get("regular")
        is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
        share_word = "разово обменяться" if regular.lower() == "регулярная" else "обменяться"
        msg = f"""{greeting}

У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {his_room}.

Уточни, пожалуйста, сможем ли {share_word} на {my_room}?
Буду тебе очень {thanks_word}!

Если сможем, то я всё сделаю {myself_word} :)"""
    elif typ == "Разовая встреча":
        meeting_name = get("meeting_name")
        duration = get("duration")
        client_name = get("client_name")
        first_name = client_name.split()[0] if client_name else "клиент"
        conflict_links = [get("conflict1"), get("conflict2"), get("conflict3")]
        conflict_links = [c for c in conflict_links if c]
        if len(conflict_links) == 0:
            conflict_text = ""
            plural = False
        elif len(conflict_links) == 1:
            conflict_text = f"У тебя образуется пересечение с этой встречей: {conflict_links[0]}"
            plural = False
        else:
            lines = "\n".join(f"{i+1}) {c}" for i, c in enumerate(conflict_links))
            conflict_text = "У тебя образуются пересечения с несколькими встречами:\n" + lines
            plural = True
        single_variants = [
            f"Уточни, пожалуйста, получится ли перенести свою встречу и быть на встрече {first_name} в это время?",
            f"Сможешь ли освободить это время и присоединиться к встрече {first_name}?",
            f"Есть возможность освободить слот и поучаствовать во встрече {first_name}?",
            f"Получится ли освободить время и присутствовать на встрече {first_name}?",
            f"Дай знать, если сможешь подвинуть свою встречу и быть у {first_name}.",
            f"Будет супер, если найдёшь возможность быть на встрече {first_name}.",
        ]
        multi_variants = [
            f"Сможешь ли освободить это время и быть на встрече {first_name}?",
            f"Есть шанс, что удастся разрулить пересечения и поучаствовать во встрече {first_name}?",
            f"Сможешь ли освободиться и поучаствовать во встрече у {first_name}?",
            f"Если появится свободное окно — очень выручишь, если подключишься к встрече {first_name}.",
            f"Понимаю, что пересечений много — но если удастся выкроить время на встречу {first_name}, это будет огонь.",
        ]
        conclusion = random.choice(multi_variants if plural else single_variants)
        msg = f"""{greeting}

Подбираю оптимальное время для проведения встречи {client_name} «{meeting_name}»{link_part} продолжительностью в {duration}.

Сейчас она стоит {formatted}{time_part}

{conflict_text}

{conclusion}"""
    else:
        msg = "Тип встречи не выбран"
    ctx.output_text.setPlainText(msg)
