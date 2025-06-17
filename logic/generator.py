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
    QGroupBox,
    QApplication,
)

try:
    from PySide6.QtCore import QDate, Qt, QTime, QTimer, QEvent
    from PySide6.QtGui import QKeyEvent
except Exception:

    class QDate:
        def __init__(self, *args, **kwargs):
            pass

    class QTime:
        def __init__(self, h=0, m=0):
            self._h = h
            self._m = m

    class Qt:
        NoFocus = 0
        Key_F4 = 0

    class QEvent:
        MouseButtonPress = 0

    class QKeyEvent:
        def __init__(self, *args, **kwargs):
            pass

    class QTimer:
        @staticmethod
        def singleShot(msec, func):
            func()


from logic.room_filter import FilteringComboBox

from logic.app_state import UIContext
from constants import rooms_by_bz
from logic.utils import (
    format_date_ru,
    parse_yandex_calendar_url,
    copy_generated_text,
)
from gui.animations import setup_animation
from gui import ToggleSwitch
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

HELP_TEXTS = {
    "name": "Имя человека, к которому мы обращаемся с вопросом. Заполняется автоматически.",
    "link": "Ссылка на встречу, по которой запрашиваем информацию",
    "datetime": "Дата встречи. Заполняется автоматически.",
    "start_time": "Время начала и окончания встречи. Заполняется автоматически.",
    "bz": "Наименование БЦ. Заполняется автоматически.",
    "room": "Наименование переговорной. Заполняется автоматически. Переговорные выводятся в соответствии с выбранным БЦ.",
    "regular": "Выбор регулярности встречи",
    "his_room": "Наименование переговорной человека, к которому обращаемся. Заполняется автоматически.",
    "my_room": "Наименование переговорной, которую хотим предложить на обмен. Заполняется только вручную.",
    "meeting_name": "Наименование названия встречи. Заполняется вручную.",
    "duration": "Выбор продолжительности встречи",
    "client_name": "Имя и фамилия заказчика в родительном падеже (Например: Артура Пирожкова, Синуса Косинова, Тангенса Катангенсова)",
    "reg_count": "Выбор количества встреч (Пример: 1 раз, 2 раза, 3 раза, 4 раза)",
    "reg_period": "Выбор периодичности (Пример: раз в неделю, раз в месяц)",
    "reg_day": "Выбор дня недели для проведения встречи (Пример: по понедельникам, по вторникам)",
}


def add_help_icon(label: QLabel, help_text: str, ctx: UIContext) -> QWidget:
    """Вернуть виджет с подсказкой, если она включена."""
    if not getattr(ctx, "show_help_icons", True):
        return label

    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(label)
    btn = QToolButton()
    btn.setText("❔")
    btn.setToolTip(help_text)
    hl.addWidget(btn)
    return container


def label_with_icon(text: str) -> QLabel:
    """Создать QLabel с иконкой-эмодзи в начале текста."""
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
    """Поле даты, автоматически открывающее календарь."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setCalendarPopup(True)
        self.lineEdit().installEventFilter(self)

    def _open_calendar(self) -> None:
        """Открыть всплывающий календарь."""

        def trigger():
            evt = QKeyEvent(QEvent.KeyPress, Qt.Key_F4, Qt.NoModifier)
            QApplication.postEvent(self, evt)

        QTimer.singleShot(0, trigger)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            self._open_calendar()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._open_calendar()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._open_calendar()


class TimeInput(QLineEdit):
    """Поле ввода времени в формате HH:mm."""

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
    """Удалить все виджеты и вложенные слои из макета."""
    while layout.count():
        item = layout.takeAt(0)
        if item.layout():
            clear_layout(item.layout())
        widget = item.widget()
        if widget:
            widget.deleteLater()


def add_field(
    label: str,
    name: str,
    ctx: UIContext,
    builtin_clear: bool = False,
    help_text: str | None = None,
):
    """Добавить текстовое поле в форму и вернуть его."""
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
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, container)
    setup_animation(edit, ctx)
    if name == "link":
        edit.textChanged.connect(lambda _: on_link_change(ctx))


def add_name_field(ctx: UIContext, help_text: str | None = None):
    """Добавить поле для имени пользователя."""
    edit = QLineEdit()
    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(edit)
    ctx.fields["name"] = edit
    ctx.field_containers["name"] = container
    lab = label_with_icon("Имя:")
    ctx.labels["name"] = lab
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, container)
    setup_animation(edit, ctx)


def add_checkbox(label: str, name: str, ctx: UIContext):
    """Создать и добавить флажок."""
    cb = QCheckBox(label)
    ctx.fields[name] = cb
    ctx.field_containers[name] = cb
    ctx.fields_layout.addRow(cb)
    setup_animation(cb, ctx)
    return cb


def add_combo(
    label: str,
    name: str,
    values: list[str],
    ctx: UIContext,
    help_text: str | None = None,
):
    """Добавить выпадающий список с заданными значениями."""
    combo = QComboBox()
    combo.addItems(values)
    ctx.fields[name] = combo
    lab = label_with_icon(label)
    ctx.labels[name] = lab
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, combo)
    setup_animation(combo, ctx)


def add_room_field(
    label: str,
    name: str,
    bz_name: str,
    ctx: UIContext,
    help_text: str | None = None,
):
    """Добавить поле выбора переговорной с очисткой."""
    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    combo = FilteringComboBox()

    def update_rooms():
        bz = ctx.fields.get(bz_name).currentText() if bz_name in ctx.fields else ""
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
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, container)
    setup_animation(combo, ctx)
    setup_animation(btn, ctx)


def add_date(name: str, ctx: UIContext, help_text: str | None = None):
    """Добавить поле выбора даты."""
    date_edit = ClickableDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("dd.MM.yyyy")
    date_edit.setDate(QDate.currentDate())
    ctx.fields[name] = date_edit
    lab = label_with_icon("Дата:")
    ctx.labels[name] = lab
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, date_edit)
    setup_animation(date_edit, ctx)


def add_time_range(
    start_name: str,
    end_name: str,
    ctx: UIContext,
    help_text: str | None = None,
):
    """Добавить два поля для ввода времени начала и конца."""
    start_edit = TimeInput()
    end_edit = TimeInput()
    start_edit.setTime(QTime(8, 0))
    end_edit.setTime(QTime(8, 30))

    container = QWidget()
    hl = QHBoxLayout(container)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(QLabel("\u23f1\ufe0f \u0441"))
    hl.addWidget(start_edit)
    hl.addWidget(QLabel("\u0434\u043e"))
    hl.addWidget(end_edit)

    ctx.fields[start_name] = start_edit
    ctx.fields[end_name] = end_edit
    lab = label_with_icon("Время:")
    ctx.labels[start_name] = lab
    label_widget = add_help_icon(lab, help_text, ctx) if help_text else lab
    ctx.fields_layout.addRow(label_widget, container)
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
    """Вернуть словесное представление числа от 1 до 5."""
    return {
        1: "один",
        2: "два",
        3: "три",
        4: "четыре",
        5: "пять",
    }.get(n, str(n))


def plural_raz(n: int) -> str:
    """Склонение слова 'раз' по числу."""
    if n == 1:
        return "раз"
    elif 2 <= n <= 4:
        return "раза"
    else:
        return "раз"


def weekday_to_plural(word: str) -> str:
    """Вернуть форму дня недели во множественном числе."""
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
    """Перестроить набор полей в зависимости от выбранного типа."""
    clear_layout(ctx.fields_layout)
    ctx.fields.clear()
    ctx.labels.clear()
    ctx.field_containers.clear()
    typ = ctx.type_combo.currentText()

    if typ == "Актуализация":
        add_name_field(ctx, HELP_TEXTS["name"])
        add_field(
            "Ссылка:", "link", ctx, builtin_clear=True, help_text=HELP_TEXTS["link"]
        )
        add_date("datetime", ctx, help_text=HELP_TEXTS["datetime"])
        add_time_range(
            "start_time", "end_time", ctx, help_text=HELP_TEXTS["start_time"]
        )
        add_combo(
            "БЦ:", "bz", list(rooms_by_bz.keys()), ctx, help_text=HELP_TEXTS["bz"]
        )
        add_room_field("Переговорка:", "room", "bz", ctx, help_text=HELP_TEXTS["room"])
        add_combo(
            "Тип встречи:",
            "regular",
            ["Обычная", "Регулярная"],
            ctx,
            help_text=HELP_TEXTS["regular"],
        )
    elif typ == "Обмен":
        add_name_field(ctx, HELP_TEXTS["name"])
        add_field(
            "Ссылка:", "link", ctx, builtin_clear=True, help_text=HELP_TEXTS["link"]
        )
        add_date("datetime", ctx, help_text=HELP_TEXTS["datetime"])
        add_time_range(
            "start_time", "end_time", ctx, help_text=HELP_TEXTS["start_time"]
        )
        add_combo(
            "БЦ:", "bz", list(rooms_by_bz.keys()), ctx, help_text=HELP_TEXTS["bz"]
        )
        add_room_field(
            "Его переговорка:", "his_room", "bz", ctx, help_text=HELP_TEXTS["his_room"]
        )
        add_room_field(
            "Твоя переговорка:", "my_room", "bz", ctx, help_text=HELP_TEXTS["my_room"]
        )
        add_combo(
            "Тип встречи:",
            "regular",
            ["Обычная", "Регулярная"],
            ctx,
            help_text=HELP_TEXTS["regular"],
        )
    elif typ == "Организация встречи":
        add_name_field(ctx, HELP_TEXTS["name"])
        add_field(
            "Ссылка:", "link", ctx, builtin_clear=True, help_text=HELP_TEXTS["link"]
        )
        add_field(
            "Название встречи:",
            "meeting_name",
            ctx,
            help_text=HELP_TEXTS["meeting_name"],
        )
        add_combo(
            "Продолжительность встречи:",
            "duration",
            ["30 минут", "1 час", "1.5 часа", "2 часа"],
            ctx,
            help_text=HELP_TEXTS["duration"],
        )
        add_date("datetime", ctx, help_text=HELP_TEXTS["datetime"])
        add_time_range(
            "start_time", "end_time", ctx, help_text=HELP_TEXTS["start_time"]
        )
        add_field(
            "Ссылка на пересечение №1:",
            "conflict1",
            ctx,
            builtin_clear=True,
        )
        cb = add_checkbox("Несколько пересечений", "multi_conflicts", ctx)
        add_field(
            "Ссылка на пересечение №2:",
            "conflict2",
            ctx,
            builtin_clear=True,
        )
        add_field(
            "Ссылка на пересечение №3:",
            "conflict3",
            ctx,
            builtin_clear=True,
        )
        add_field(
            "Имя и фамилия заказчика (в род. падеже):",
            "client_name",
            ctx,
            help_text=HELP_TEXTS["client_name"],
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
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QPushButton,
            QVBoxLayout,
            QFormLayout,
            QHBoxLayout,
        )

        info_box = QGroupBox()
        info_box.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 6px; margin-top: 6px; }"
        )
        info_layout = QFormLayout(info_box)
        name_container = QWidget()
        name_hl = QHBoxLayout(name_container)
        name_hl.setContentsMargins(0, 0, 0, 0)
        name_edit = QLineEdit()
        gender_switch = ToggleSwitch()
        name_hl.addWidget(name_edit)
        name_hl.addStretch()
        name_hl.addWidget(QLabel("Мужское"))
        name_hl.addWidget(gender_switch)
        name_hl.addWidget(QLabel("Женское"))
        ctx.fields["other_name"] = name_edit
        ctx.fields["gender"] = gender_switch
        info_layout.addRow(label_with_icon("Имя:"), name_container)
        ctx.fields_layout.addRow(info_box)

        grid_box = QGroupBox()
        grid_box.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 6px; margin-top: 6px; }"
        )
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        idx = 0
        for key in OTHER_TEMPLATES.keys():
            btn = QPushButton(key)
            btn.clicked.connect(lambda _=False, k=key: generate_other_category(ctx, k))
            setup_animation(btn, ctx)
            grid.addWidget(btn, idx // 2, idx % 2)
            idx += 1

        grid_box.setLayout(grid)
        ctx.field_containers["other_buttons"] = grid_box
        ctx.fields_layout.addRow(grid_box)
        act_box = QGroupBox()
        act_box.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 6px; margin-top: 6px; }"
        )
        act_layout = QVBoxLayout(act_box)
        act_btn = QPushButton("Написали по актуальности")
        act_btn.setMinimumHeight(40)
        act_btn.clicked.connect(lambda: show_actuality_dialog(ctx))
        setup_animation(act_btn, ctx)
        act_layout.addWidget(act_btn)
        ctx.fields_layout.addRow(act_box)

        exch_box = QGroupBox()
        exch_box.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 6px; margin-top: 6px; }"
        )
        exch_layout = QVBoxLayout(exch_box)
        exch_btn = QPushButton("Написали по обмену")
        exch_btn.setMinimumHeight(40)
        exch_btn.clicked.connect(lambda: show_exchange_dialog(ctx))
        setup_animation(exch_btn, ctx)
        exch_layout.addWidget(exch_btn)
        ctx.fields_layout.addRow(exch_box)

        custom_box = QGroupBox()
        custom_box.setTitle("Пользовательские шаблоны")
        custom_box.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 6px; margin-top: 6px; }"
        )
        custom_layout = QVBoxLayout(custom_box)
        custom_layout.setContentsMargins(9, 15, 9, 9)
        my_btn = QPushButton("Мои шаблоны")
        my_btn.setMinimumHeight(40)
        my_btn.clicked.connect(lambda: show_user_templates_dialog(ctx))
        setup_animation(my_btn, ctx)
        custom_layout.addWidget(my_btn)
        ctx.fields_layout.addRow(custom_box)

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
    """Обновить дату и время по ссылке из Яндекс.Календаря."""
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


def _get_value(ctx: UIContext, name: str) -> str:
    """Вернуть строковое значение виджета по его имени."""
    widget = ctx.fields.get(name)
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if hasattr(widget, "time"):
        return widget.time().toString("HH:mm")
    return ""


def _build_greeting(ctx: UIContext, name: str) -> tuple[str, str]:
    """Сформировать приветствие и пол в зависимости от настроек."""
    greeting = f"Привет, {name}!"
    gender = "ж"
    if ctx.ls_active and ctx.ls_saved:
        greeting = f"Привет, {name}! Я {ctx.user_name}, ассистент. Приятно познакомиться!"
        gender = ctx.user_gender
    elif ctx.asya_mode:
        greeting = f"Привет, {name}! Я Ася, ассистент. Приятно познакомиться!"
        gender = "ж"
    return greeting, gender


def _make_time_part(start: str, end: str) -> str:
    """Сформировать текстовую часть со временем встречи."""
    if start and end:
        return f", в {start} — {end}"
    if start:
        return f", в {start}"
    return ""


def _generate_actualization(greeting: str, formatted: str, time_part: str, link_part: str,
                            room: str, regular: str, thanks_word: str, myself_word: str) -> str:
    """Собрать сообщение для запроса актуальности."""
    is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
    share_word = "разово поделиться" if regular.lower() == "регулярная" else "поделиться"
    return (
        f"{greeting}\n\n"
        f"У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {room}.\n\n"
        f"Уточни, пожалуйста, сможешь ли {share_word} переговорной?\n"
        f"Буду очень {thanks_word}!\n\n"
        f"Если сможешь, то сделаю всё {myself_word}. Только не удаляй её из встречи, чтобы не потерять :)"
    )


def _generate_exchange(greeting: str, formatted: str, time_part: str, link_part: str,
                       his_room: str, my_room: str, regular: str,
                       thanks_word: str, myself_word: str) -> str:
    """Собрать сообщение для предложения обмена."""
    is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
    share_word = "разово обменяться" if regular.lower() == "регулярная" else "обменяться"
    return (
        f"{greeting}\n\n"
        f"У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {his_room}.\n\n"
        f"Уточни, пожалуйста, сможем ли {share_word} на {my_room}?\n"
        f"Буду тебе очень {thanks_word}!\n\n"
        f"Если сможем, то я всё сделаю {myself_word} :)"
    )


def _generate_meeting(ctx: UIContext, greeting: str, formatted: str, time_part: str,
                      link_part: str, meeting_name: str, duration: str,
                      client_name: str, conflict_links: list[str],
                      thanks_word: str, myself_word: str) -> str:
    """Собрать текст для организации встречи."""
    first_name = client_name.split()[0] if client_name else "клиент"
    conflicts = [c for c in conflict_links if c]
    if len(conflicts) == 0:
        conflict_text = ""
        plural = False
    elif len(conflicts) == 1:
        conflict_text = f"У тебя образуется пересечение с этой встречей: {conflicts[0]}"
        plural = False
    else:
        lines = "\n".join(f"{i+1}) {c}" for i, c in enumerate(conflicts))
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

    return (
        f"{greeting}\n\n"
        f"Подбираю оптимальное время для проведения встречи {client_name} «{meeting_name}»{link_part} продолжительностью в {duration}.\n"
        f"{regular_one}\n\n"
        f"Сейчас она стоит {formatted}{time_part}\n"
        f"{regular_two}\n\n"
        f"{conflict_text}\n\n"
        f"{conclusion}"
    )


def generate_message(ctx: UIContext):
    """Сформировать текст сообщения на основе заполненных полей."""
    typ = ctx.type_combo.currentText()

    start = _get_value(ctx, "start_time")
    end = _get_value(ctx, "end_time")
    time_part = _make_time_part(start, end)
    name = _get_value(ctx, "name")
    if not name or (
        (typ == "Актуализация" and not _get_value(ctx, "room"))
        or (typ == "Обмен" and (not _get_value(ctx, "his_room") or not _get_value(ctx, "my_room")))
    ):
        QMessageBox.warning(ctx.window, "Предупреждение", "Заполните имя и переговорку")
        return
    if "datetime" not in ctx.fields:
        QMessageBox.critical(ctx.window, "Ошибка", "Сначала выберите тип встречи")
        return

    raw_date = ctx.fields["datetime"].date().toPython()
    formatted = format_date_ru(raw_date)
    link = _get_value(ctx, "link")
    link_part = f" ({link})" if link else ""
    greeting, gender = _build_greeting(ctx, name)
    thanks_word = "признательна" if gender == "ж" else "признателен"
    myself_word = "сама" if gender == "ж" else "сам"

    if typ == "Актуализация":
        room = _get_value(ctx, "room")
        regular = _get_value(ctx, "regular")
        msg = _generate_actualization(greeting, formatted, time_part, link_part, room, regular, thanks_word, myself_word)
    elif typ == "Обмен":
        his_room = _get_value(ctx, "his_room")
        my_room = _get_value(ctx, "my_room")
        regular = _get_value(ctx, "regular")
        msg = _generate_exchange(greeting, formatted, time_part, link_part, his_room, my_room, regular, thanks_word, myself_word)
    elif typ == "Организация встречи":
        meeting_name = _get_value(ctx, "meeting_name")
        duration = _get_value(ctx, "duration")
        client_name = _get_value(ctx, "client_name")
        conflicts = [
            _get_value(ctx, "conflict1"),
            _get_value(ctx, "conflict2"),
            _get_value(ctx, "conflict3"),
        ]
        msg = _generate_meeting(
            ctx,
            greeting,
            formatted,
            time_part,
            link_part,
            meeting_name,
            duration,
            client_name,
            conflicts,
            thanks_word,
            myself_word,
        )
    else:
        msg = "Тип встречи не выбран"

    try:
        date_str = ctx.fields["datetime"].date().toString("dd.MM.yyyy")
        record = {
            "type": typ.lower(),
            "name": name,
            "date": date_str,
            "start": start,
            "end": end,
        }
        if typ == "Актуализация":
            record["room"] = room
        elif typ == "Обмен":
            record["his_room"] = his_room
            record["my_room"] = my_room
        ctx.history.add_record(record)
    except Exception:
        pass

    ctx.output_text.setPlainText(msg)
    if getattr(ctx, "auto_report_enabled", False):
        result = show_auto_report_dialog(ctx)
        if result is None and getattr(ctx, "auto_copy_enabled", False):
            copy_generated_text(ctx)
    elif getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)


def generate_other_category(ctx: UIContext, category: str) -> None:
    """Сгенерировать текст для вкладки "Другое"."""
    name_field = ctx.fields.get("other_name")
    gender_field = ctx.fields.get("gender")
    name = name_field.text().strip() if name_field else ""
    gender = "ж"
    if isinstance(gender_field, QComboBox):
        gender = "ж" if gender_field.currentText().startswith("Ж") else "м"
    elif hasattr(gender_field, "isChecked"):
        gender = "ж" if gender_field.isChecked() else "м"
    text = generate_from_category(category, name, gender)
    ctx.output_text.setPlainText(text)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)


def _format_short_date(date_str: str) -> str:
    """Преобразовать строку даты в формат "Д месяц"."""
    try:
        from datetime import datetime
        from .utils import months

        dt = datetime.strptime(date_str, "%d.%m.%Y")
        return f"{dt.day} {months[dt.month - 1]}"
    except Exception:
        return date_str


def show_actuality_dialog(ctx: UIContext) -> None:
    """Диалог по шаблону "Написали по актуальности"."""
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QFormLayout,
        QLineEdit,
        QRadioButton,
        QButtonGroup,
        QWidget,
        QHBoxLayout,
        QPushButton,
    )

    dlg = QDialog(ctx.window)
    dlg.setWindowTitle("Написали по актуальности")
    layout = QVBoxLayout(dlg)
    form = QFormLayout()

    login_edit = QLineEdit()
    date_edit = QLineEdit()
    time_edit = QLineEdit()
    room_edit = QLineEdit()
    link_edit = QLineEdit()
    tg_edit = QLineEdit()
    channel_group = QButtonGroup(dlg)
    asya_radio = QRadioButton("Ася")
    ls_radio = QRadioButton("ЛС")
    asya_radio.setChecked(True)
    channel_group.addButton(asya_radio)
    channel_group.addButton(ls_radio)
    ch_widget = QWidget()
    ch_layout = QHBoxLayout(ch_widget)
    ch_layout.setContentsMargins(0, 0, 0, 0)
    ch_layout.addWidget(asya_radio)
    ch_layout.addWidget(ls_radio)
    recent_combo = QComboBox()

    recs = ctx.history.get_recent_by_type("актуализация")
    if recs:
        recent_combo.addItem("Выбрать...", {})
        for r in recs:
            label = f"{r.get('room','')}, {_format_short_date(r['date'])} {r.get('start','')}\u2013{r.get('end','')}"
            recent_combo.addItem(label, r)
    else:
        recent_combo.addItem("Нет сохранённых встреч", {})

    def on_recent(idx: int) -> None:
        data = recent_combo.itemData(idx)
        if not isinstance(data, dict):
            return
        date_edit.setText(_format_short_date(data.get("date", "")))
        time_edit.setText(f"{data.get('start','')} — {data.get('end','')}")
        room_edit.setText(data.get("room", ""))

    recent_combo.currentIndexChanged.connect(on_recent)

    form.addRow("Логин:", login_edit)
    form.addRow("Дата:", date_edit)
    form.addRow("Время:", time_edit)
    form.addRow("Переговорка:", room_edit)
    form.addRow("Ссылка на встречу:", link_edit)
    form.addRow("Ссылка на Telegram:", tg_edit)
    form.addRow("Канал:", ch_widget)
    form.addRow("Последние встречи:", recent_combo)
    layout.addLayout(form)

    ok_btn = QPushButton("OK")
    ok_btn.clicked.connect(dlg.accept)
    layout.addWidget(ok_btn)

    if dlg.exec() != QDialog.Accepted:
        return

    date = date_edit.text().strip()
    time = time_edit.text().strip()
    room = room_edit.text().strip()
    login = login_edit.text().strip()
    link = link_edit.text().strip()
    tg = tg_edit.text().strip()
    ch = "Ася" if asya_radio.isChecked() else "ЛС"
    pref = "Уточняю с Аси" if ch == "Ася" else "Уточняю с ЛС"
    text = (
        f"{pref} актуальность по [встрече]({link}), которая пройдёт {date} "
        f"в {time} в переговорной **{room}** у @{login}"
        f"\n[Моё сообщение в Telegram]({tg}).\nОтвет:"
    )
    ctx.output_text.setPlainText(text)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)


def show_exchange_dialog(ctx: UIContext) -> None:
    """Диалог по шаблону "Написали по обмену"."""
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QFormLayout,
        QLineEdit,
        QRadioButton,
        QButtonGroup,
        QWidget,
        QHBoxLayout,
        QPushButton,
    )

    dlg = QDialog(ctx.window)
    dlg.setWindowTitle("Написали по обмену")
    layout = QVBoxLayout(dlg)
    form = QFormLayout()

    login_edit = QLineEdit()
    date_edit = QLineEdit()
    time_edit = QLineEdit()
    his_room_edit = QLineEdit()
    my_room_edit = QLineEdit()
    link_edit = QLineEdit()
    tg_edit = QLineEdit()
    channel_group = QButtonGroup(dlg)
    asya_radio = QRadioButton("Ася")
    ls_radio = QRadioButton("ЛС")
    asya_radio.setChecked(True)
    channel_group.addButton(asya_radio)
    channel_group.addButton(ls_radio)
    ch_widget = QWidget()
    ch_layout = QHBoxLayout(ch_widget)
    ch_layout.setContentsMargins(0, 0, 0, 0)
    ch_layout.addWidget(asya_radio)
    ch_layout.addWidget(ls_radio)
    recent_combo = QComboBox()

    recs = ctx.history.get_recent_by_type("обмен")
    if recs:
        recent_combo.addItem("Выбрать...", {})
        for r in recs:
            label = (
                f"{r.get('his_room','')} \u2192 {r.get('my_room','')}, "
                f"{_format_short_date(r['date'])} {r.get('start','')}\u2013{r.get('end','')}"
            )
            recent_combo.addItem(label, r)
    else:
        recent_combo.addItem("Нет сохранённых встреч", {})

    def on_recent(idx: int) -> None:
        data = recent_combo.itemData(idx)
        if not isinstance(data, dict):
            return
        date_edit.setText(_format_short_date(data.get("date", "")))
        time_edit.setText(f"{data.get('start','')} — {data.get('end','')}")
        his_room_edit.setText(data.get("his_room", ""))
        my_room_edit.setText(data.get("my_room", ""))

    recent_combo.currentIndexChanged.connect(on_recent)

    form.addRow("Логин:", login_edit)
    form.addRow("Дата:", date_edit)
    form.addRow("Время:", time_edit)
    form.addRow("Его переговорка:", his_room_edit)
    form.addRow("Твоя переговорка:", my_room_edit)
    form.addRow("Ссылка на встречу:", link_edit)
    form.addRow("Ссылка на Telegram:", tg_edit)
    form.addRow("Канал:", ch_widget)
    form.addRow("Последние встречи:", recent_combo)
    layout.addLayout(form)

    ok_btn = QPushButton("OK")
    ok_btn.clicked.connect(dlg.accept)
    layout.addWidget(ok_btn)

    if dlg.exec() != QDialog.Accepted:
        return

    date = date_edit.text().strip()
    time = time_edit.text().strip()
    his_room = his_room_edit.text().strip()
    my_room = my_room_edit.text().strip()
    login = login_edit.text().strip()
    link = link_edit.text().strip()
    tg = tg_edit.text().strip()
    ch = "Ася" if asya_radio.isChecked() else "ЛС"
    pref = "Предлагаю обмен с Аси" if ch == "Ася" else "Предлагаю обмен с ЛС"
    text = (
        f"{pref} по [встрече]({link}), которая пройдёт {date}, в {time} "
        f"в переговорной **{his_room}** на свою **{my_room}**. Пишу @{login}"
        f"\n[Моё сообщение в Telegram]({tg}).\nОтвет: "
    )
    ctx.output_text.setPlainText(text)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)


def show_auto_report_dialog(ctx: UIContext) -> bool | None:
    """Диалог автозаполнения отчёта после генерации текста.

    Возвращает ``True`` если отчёт подтверждён, ``False`` при отмене и ``None``
    если окно не было показано (тип шаблона не поддерживается).
    """
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QFormLayout,
        QLineEdit,
        QPushButton,
    )

    typ = ctx.type_combo.currentText()
    if typ not in {"Обмен", "Актуализация"}:
        return None

    dlg = QDialog(ctx.window)
    dlg.setWindowTitle("Авто-отчёт")
    layout = QVBoxLayout(dlg)
    form = QFormLayout()

    login_edit = QLineEdit()
    link_edit = QLineEdit()
    tg_edit = QLineEdit()

    form.addRow("Логин:", login_edit)
    form.addRow("Ссылка на встречу:", link_edit)
    form.addRow("Telegram:", tg_edit)
    layout.addLayout(form)

    ok_btn = QPushButton("Подтвердить")
    ok_btn.clicked.connect(dlg.accept)
    layout.addWidget(ok_btn)

    if dlg.exec() != QDialog.Accepted:
        return False

    login = login_edit.text().strip()
    link = link_edit.text().strip()
    tg = tg_edit.text().strip()

    date = (
        ctx.fields["datetime"].date().toString("dd.MM.yyyy")
        if "datetime" in ctx.fields
        else ""
    )
    start = (
        ctx.fields["start_time"].time().toString("HH:mm")
        if "start_time" in ctx.fields
        else ""
    )
    end = (
        ctx.fields["end_time"].time().toString("HH:mm")
        if "end_time" in ctx.fields
        else ""
    )
    time = f"{start} — {end}" if start and end else start

    if typ == "Обмен":
        his_room = ctx.fields.get("his_room")
        my_room = ctx.fields.get("my_room")
        his_room_val = (
            his_room.currentText()
            if hasattr(his_room, "currentText")
            else getattr(his_room, "text", lambda: "")()
        )
        my_room_val = (
            my_room.currentText()
            if hasattr(my_room, "currentText")
            else getattr(my_room, "text", lambda: "")()
        )
        text = (
            f"Предлагаю обмен по [встрече]({link}), которая пройдёт {date}, в {time} "
            f"в переговорной **{his_room_val}** на свою **{my_room_val}**. Пишу @{login}\n"
            f"[Моё сообщение в Telegram]({tg}).\nОтвет: "
        )
    else:  # Актуализация
        room = ctx.fields.get("room")
        room_val = (
            room.currentText()
            if hasattr(room, "currentText")
            else getattr(room, "text", lambda: "")()
        )
        text = (
            f"Уточняю актуальность по [встрече]({link}), которая пройдёт {date} "
            f"в {time} в переговорной **{room_val}** у @{login}\n"
            f"[Моё сообщение в Telegram]({tg}).\nОтвет:"
        )

    if ctx.report_text:
        ctx.report_text.setPlainText(text)
        ctx.report_text.setVisible(True)
    if getattr(ctx, "auto_copy_enabled", False):
        copy_generated_text(ctx)
    return True


def add_user_template_dialog(ctx: UIContext, parent=None) -> bool:
    """Диалог создания нового пользовательского шаблона."""
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QLineEdit,
        QTextEdit,
        QLabel,
        QPushButton,
        QMessageBox,
    )

    dlg = QDialog(parent or ctx.window)
    dlg.setWindowTitle("Новый шаблон")
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("ТЕГ"))
    tag_edit = QLineEdit()
    layout.addWidget(tag_edit)
    layout.addWidget(QLabel("Текст шаблона"))
    text_edit = QTextEdit()
    layout.addWidget(text_edit)
    ok_btn = QPushButton("OK")
    layout.addWidget(ok_btn)

    result = {"added": False}

    def on_ok():
        tag = tag_edit.text().strip()
        text = text_edit.toPlainText().strip()
        if not tag or not text:
            QMessageBox.warning(dlg, "Ошибка", "Введите тег и текст шаблона")
            return
        ctx.user_templates.add_template(tag, text)
        result["added"] = True
        dlg.accept()

    ok_btn.clicked.connect(on_ok)
    dlg.exec()
    return result["added"]


def show_user_templates_dialog(ctx: UIContext) -> None:
    """Список пользовательских шаблонов и управление ими."""
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QPushButton,
        QToolButton,
        QSizePolicy,
        QScrollArea,
        QWidget,
        QLabel,
    )

    dlg = QDialog(ctx.window)
    dlg.setWindowTitle("Мои шаблоны")
    dlg.resize(600, 400)
    layout = QVBoxLayout(dlg)
    top = QHBoxLayout()
    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Поиск по тегу...")
    add_btn = QPushButton("➕ Добавить новый шаблон")
    top.addWidget(search_edit)
    top.addStretch()
    top.addWidget(add_btn)
    layout.addLayout(top)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet(
        "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }"
    )
    container = QWidget()
    vbox = QVBoxLayout(container)
    scroll.setWidget(container)
    layout.addWidget(scroll)

    def refresh():
        for i in reversed(range(vbox.count())):
            item = vbox.takeAt(i)
            w = item.widget()
            if w:
                w.deleteLater()
        items = ctx.user_templates.filter_by_tag(search_edit.text().strip())
        for tpl in items:
            idx = ctx.user_templates.templates.index(tpl)
            row = QWidget()
            hl = QHBoxLayout(row)
            btn = QPushButton(tpl.get("tag", ""))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(
                lambda _=False, t=tpl.get("text", ""): ctx.output_text.setPlainText(t)
            )
            hl.addWidget(btn)

            info_btn = QToolButton()
            info_btn.setText("?")
            info_btn.setToolTip(tpl.get("text", ""))
            hl.addWidget(info_btn)

            hl.addStretch()
            del_btn = QToolButton()
            del_btn.setText("🗑")
            del_btn.clicked.connect(
                lambda _=False, i=idx: (
                    ctx.user_templates.remove_template(i),
                    refresh(),
                )
            )
            hl.addWidget(del_btn)
            vbox.addWidget(row)
        vbox.addStretch()

    search_edit.textChanged.connect(refresh)

    def on_add():
        if add_user_template_dialog(ctx, dlg):
            refresh()

    add_btn.clicked.connect(on_add)
    refresh()
    dlg.exec()
