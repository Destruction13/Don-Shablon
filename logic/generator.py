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
    QToolButton,
    QFormLayout,
    QMessageBox,
    QCheckBox,
)
try:
    from PySide6.QtCore import QDate, Qt, QTime, QTimer
except Exception:  # test fallback
    class QDate:
        def __init__(self, *args, **kwargs):
            pass

    class QTime:
        def __init__(self, h=0, m=0):
            self._h = h
            self._m = m
    class Qt:
        NoFocus = 0

from logic.room_filter import FilteringComboBox

from logic.app_state import UIContext
from constants import rooms_by_bz
from logic.utils import (
    format_date_ru,
    parse_yandex_calendar_url,
    copy_generated_text,
)
from gui.animations import setup_animation
from logic.templates import OTHER_TEMPLATES, generate_from_category

ICON_MAP = {
    "Имя": "🧑\u200d💼",
    "Ссылка": "🔗",
    "Дата": "📅",
    "Время": "⏰",
    "БЦ": "🏢",
    "Переговорка": "💬",
    "Тип встречи": "📌",
    "Название встречи": "📝",
}

def label_with_icon(text: str) -> QLabel:
    base = text.rstrip(":")
    emoji = None
    for key, ico in ICON_MAP.items():
        if base.startswith(key):
            emoji = ico
            break
    if emoji:
        return QLabel(f"{emoji} {text}")
    return QLabel(text)


class ClickableDateEdit(QDateEdit):
    """Date edit that opens the calendar when focused or clicked."""

    def _open_calendar(self):
        """Open the calendar popup reliably across Qt versions."""
        self.setCalendarPopup(True)

        def show():
            cal = self.calendarWidget()
            if cal:
                cal.show()
                cal.setFocus()

        QTimer.singleShot(100, show)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._open_calendar()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._open_calendar()


class TimeInput(QLineEdit):
    """Simple line edit for time with HH:mm format."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInputMask("00:00")
        self.setText("08:00")

    def time(self) -> QTime:
        return QTime.fromString(self.text(), "HH:mm")

    def setTime(self, t: QTime):
        self.setText(t.toString("HH:mm"))

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.layout():
            clear_layout(item.layout())
        widget = item.widget()
        if widget:
            widget.deleteLater()


def add_field(label: str, name: str, ctx: UIContext, builtin_clear: bool = False):
    edit = QLineEdit()
    if builtin_clear:
        try:
            edit.setClearButtonEnabled(True)
        except Exception:
            pass
    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(edit)
    ctx.fields[name] = edit
    ctx.field_containers[name] = container
    lab = label_with_icon(label)
    ctx.labels[name] = lab
    ctx.fields_layout.addRow(lab, container)
    setup_animation(edit, ctx)
    if name == "link":
        edit.textChanged.connect(lambda _: on_link_change(ctx))


def add_name_field(ctx: UIContext):
    edit = QLineEdit()
    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(edit)
    if ctx.btn_ls:
        hl.addWidget(ctx.btn_ls)
        ctx.btn_ls.setParent(container)
    if ctx.btn_asya_plus:
        hl.addWidget(ctx.btn_asya_plus)
        ctx.btn_asya_plus.setParent(container)
    ctx.fields["name"] = edit
    ctx.field_containers["name"] = container
    lab = label_with_icon("Имя:")
    ctx.labels["name"] = lab
    ctx.fields_layout.addRow(lab, container)
    setup_animation(edit, ctx)


def add_checkbox(label: str, name: str, ctx: UIContext):
    cb = QCheckBox(label)
    ctx.fields[name] = cb
    ctx.field_containers[name] = cb
    ctx.fields_layout.addRow(cb)
    setup_animation(cb, ctx)
    return cb


def add_combo(label: str, name: str, values: list[str], ctx: UIContext):
    combo = QComboBox()
    combo.addItems(values)
    ctx.fields[name] = combo
    lab = label_with_icon(label)
    ctx.labels[name] = lab
    ctx.fields_layout.addRow(lab, combo)
    setup_animation(combo, ctx)


def add_room_field(label: str, name: str, bz_name: str, ctx: UIContext):
    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    combo = FilteringComboBox()

    def update_rooms():
        bz = ctx.fields.get(bz_name).currentText() if bz_name in ctx.fields else ''
        rooms = rooms_by_bz.get(bz, [])
        combo.set_items(rooms)

    if bz_name in ctx.fields:
        ctx.fields[bz_name].currentTextChanged.connect(update_rooms)
    update_rooms()

    hl.addWidget(combo)
    btn = QToolButton()
    btn.setText("✖")
    btn.setFocusPolicy(Qt.NoFocus)
    btn.clicked.connect(lambda: combo.setEditText(""))
    hl.addWidget(btn)
    ctx.fields[name] = combo
    lab = label_with_icon(label)
    ctx.labels[name] = lab
    ctx.fields_layout.addRow(lab, container)
    setup_animation(combo, ctx)
    setup_animation(btn, ctx)


def add_date(name: str, ctx: UIContext):
    date_edit = ClickableDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("dd.MM.yyyy")
    date_edit.setDate(QDate.currentDate())
    ctx.fields[name] = date_edit
    lab = label_with_icon("Дата:")
    ctx.labels[name] = lab
    ctx.fields_layout.addRow(lab, date_edit)
    setup_animation(date_edit, ctx)


def add_time_range(start_name: str, end_name: str, ctx: UIContext):
    start_edit = TimeInput()
    end_edit = TimeInput()
    start_edit.setTime(QTime(8, 0))
    end_edit.setTime(QTime(8, 30))

    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(QLabel("\u23F1\ufe0f \u0441"))
    hl.addWidget(start_edit)
    hl.addWidget(QLabel("\u0434\u043e"))
    hl.addWidget(end_edit)

    ctx.fields[start_name] = start_edit
    ctx.fields[end_name] = end_edit
    lab = label_with_icon("Время:")
    ctx.labels[start_name] = lab
    ctx.fields_layout.addRow(lab, container)
    setup_animation(start_edit, ctx)
    setup_animation(end_edit, ctx)

    def on_start_changed():
        st = start_edit.time()
        et = end_edit.time()
        new_end = st.addSecs(30 * 60)
        if not et.isValid() or et <= st:
            end_edit.setTime(new_end)

    def on_end_changed():
        st = start_edit.time()
        et = end_edit.time()
        if et <= st:
            end_edit.setTime(st.addSecs(30 * 60))

    start_edit.editingFinished.connect(on_start_changed)
    end_edit.editingFinished.connect(on_end_changed)


def number_to_words(n: int) -> str:
    return {
        1: "один",
        2: "два",
        3: "три",
        4: "четыре",
        5: "пять",
    }.get(n, str(n))


def plural_raz(n: int) -> str:
    if n == 1:
        return "раз"
    elif 2 <= n <= 4:
        return "раза"
    else:
        return "раз"


def weekday_to_plural(word: str) -> str:
    mapping = {
        "понедельник": "понедельникам",
        "вторник": "вторникам",
        "среда": "средам",
        "четверг": "четвергам",
        "пятница": "пятницам",
        "суббота": "субботам",
        "воскресенье": "воскресеньям",
    }
    return mapping.get(word.lower(), word)





def update_fields(ctx: UIContext):
    if ctx.btn_ls:
        ctx.btn_ls.setParent(None)
    if ctx.btn_asya_plus:
        ctx.btn_asya_plus.setParent(None)
    clear_layout(ctx.fields_layout)
    ctx.fields.clear()
    typ = ctx.type_combo.currentText()

    if typ == "Актуализация":
        add_name_field(ctx)
        add_field("Ссылка:", "link", ctx, builtin_clear=True)
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_combo("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)
        add_room_field("Переговорка:", "room", "bz", ctx)
        add_combo("Тип встречи:", "regular", ["Обычная", "Регулярная"], ctx)
    elif typ == "Обмен":
        add_name_field(ctx)
        add_field("Ссылка:", "link", ctx, builtin_clear=True)
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_combo("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)
        add_room_field("Его переговорка:", "his_room", "bz", ctx)
        add_room_field("Твоя переговорка:", "my_room", "bz", ctx)
        add_combo("Тип встречи:", "regular", ["Обычная", "Регулярная"], ctx)
    elif typ == "Организация встречи":
        add_name_field(ctx)
        add_field("Ссылка:", "link", ctx, builtin_clear=True)
        add_field("Название встречи:", "meeting_name", ctx)
        add_combo(
            "Продолжительность встречи:",
            "duration",
            ["30 минут", "1 час", "1.5 часа", "2 часа"],
            ctx,
        )
        add_date("datetime", ctx)
        add_time_range("start_time", "end_time", ctx)
        add_field("Ссылка на пересечение №1:", "conflict1", ctx, builtin_clear=True)
        cb = add_checkbox("Несколько пересечений", "multi_conflicts", ctx)
        add_field("Ссылка на пересечение №2:", "conflict2", ctx, builtin_clear=True)
        add_field("Ссылка на пересечение №3:", "conflict3", ctx, builtin_clear=True)
        add_field(
            "Имя и фамилия заказчика (в род. падеже):",
            "client_name",
            ctx,
        )
        # hide extra conflict links until checkbox checked
        ctx.field_containers["conflict2"].setVisible(False)
        ctx.labels["conflict2"].setVisible(False)
        ctx.field_containers["conflict3"].setVisible(False)
        ctx.labels["conflict3"].setVisible(False)

        def toggle_extra(val):
            vis = bool(val)
            ctx.field_containers["conflict2"].setVisible(vis)
            ctx.labels["conflict2"].setVisible(vis)
            ctx.field_containers["conflict3"].setVisible(vis)
            ctx.labels["conflict3"].setVisible(vis)

        cb.stateChanged.connect(toggle_extra)
    elif typ == "Другое":
        add_field("Имя:", "other_name", ctx)
        add_combo("Пол:", "gender", ["Мужской", "Женский"], ctx)
        from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        for i, key in enumerate(OTHER_TEMPLATES.keys()):
            btn = QPushButton(key)
            btn.clicked.connect(lambda _=False, k=key: generate_other_category(ctx, k))
            setup_animation(btn, ctx)
            grid.addWidget(btn, i // 2, i % 2)
        ctx.field_containers["other_buttons"] = grid_container
        ctx.fields_layout.addRow(grid_container)

    # rename fields depending on type
    if "client_name" in ctx.fields:
        lab = ctx.labels.get("client_name")
        if lab:
            if typ == "Организация встречи":
                lab.setText("🧑\u200d💼 Имя и фамилия заказчика (в род. падеже):")
            else:
                lab.setText("🧑\u200d💼 Имя заказчика:")
    if "meeting_name" in ctx.fields:
        lab = ctx.labels.get("meeting_name")
        if lab:
            lab.setText("📝 Название встречи:")


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
            ctx.fields["start_time"].setTime(QTime(h, m))
        except Exception:
            pass


def generate_message(ctx: UIContext):
    typ = ctx.type_combo.currentText()
    def get(name: str):
        widget = ctx.fields.get(name)
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if hasattr(widget, "time"):
            return widget.time().toString("HH:mm")
        return ""
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
    elif typ == "Организация встречи":
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
        regular_one = regular_two = ""
        if ctx.regular_meeting_enabled:
            count = ctx.regular_count.value()
            count_word = number_to_words(count)
            raz_form = plural_raz(count)
            period = ctx.regular_period.currentText().strip().lower()
            day = ctx.regular_day.currentText().strip().lower()
            plural_day = weekday_to_plural(day)
            regular_one = (
                f"Она будет проводиться регулярно {count_word} {raz_form} в {period} "
                f"по {plural_day}."
            )
            regular_two = (
                f"Если всё устроит, встреча будет повторяться {count_word} {raz_form} "
                f"в {period} в это же время."
            )

        msg = f"""{greeting}

Подбираю оптимальное время для проведения встречи {client_name} «{meeting_name}»{link_part} продолжительностью в {duration}.
{regular_one}

Сейчас она стоит {formatted}{time_part}
{regular_two}

{conflict_text}

{conclusion}"""
    else:
        msg = "Тип встречи не выбран"


    ctx.output_text.setPlainText(msg)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)

def generate_other_category(ctx: UIContext, category: str) -> None:
    """Generate text for the "Другое" tab."""
    name_field = ctx.fields.get("other_name")
    gender_field = ctx.fields.get("gender")
    name = name_field.text().strip() if name_field else ""
    gender = "ж"
    if isinstance(gender_field, QComboBox):
        gender = "ж" if gender_field.currentText().startswith("Ж") else "м"
    text = generate_from_category(category, name, gender)
    ctx.output_text.setPlainText(text)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)
