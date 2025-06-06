from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QDateEdit
)
from datetime import datetime

from constants import rooms_by_bz
from core.qt_app_state import QtUIContext
from ocr_tesseract import import_from_clipboard_image


def _generate_time_slots(start_hour: int = 8, end_hour: int = 22):
    return [f"{h:02d}:{m:02d}" for h in range(start_hour, end_hour) for m in (0, 30)]


def build_ui(ctx: QtUIContext):
    layout = QVBoxLayout(ctx.window)

    ctx.type_box = QComboBox()
    ctx.type_box.addItems(["Актуализация", "Обмен", "Разовая встреча"])
    layout.addWidget(QLabel("Тип встречи"))
    layout.addWidget(ctx.type_box)

    ctx.fields['name'] = QLineEdit()
    layout.addWidget(QLabel("Имя"))
    layout.addWidget(ctx.fields['name'])

    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDate(datetime.today())
    ctx.fields['datetime'] = date_edit
    layout.addWidget(QLabel("Дата"))
    layout.addWidget(date_edit)

    start_combo = QComboBox(); start_combo.addItems(_generate_time_slots())
    end_combo = QComboBox(); end_combo.addItems(_generate_time_slots())
    ctx.fields['start_time'] = start_combo
    ctx.fields['end_time'] = end_combo
    layout.addWidget(QLabel("Время начала"))
    layout.addWidget(start_combo)
    layout.addWidget(QLabel("Время конца"))
    layout.addWidget(end_combo)

    bz_combo = QComboBox(); bz_combo.addItems(list(rooms_by_bz.keys()))
    ctx.fields['bz'] = bz_combo
    layout.addWidget(QLabel("Бизнес-центр"))
    layout.addWidget(bz_combo)

    room_combo = QComboBox(); room_combo.addItems(sum(rooms_by_bz.values(), []))
    ctx.fields['room'] = room_combo
    layout.addWidget(QLabel("Переговорка"))
    layout.addWidget(room_combo)

    reg_combo = QComboBox(); reg_combo.addItems(["Обычная", "Регулярная"])
    ctx.fields['regular'] = reg_combo
    layout.addWidget(QLabel("Тип"))
    layout.addWidget(reg_combo)

    btn = QPushButton("📋 Из буфера")
    btn.clicked.connect(lambda: import_from_clipboard_image(ctx))
    layout.addWidget(btn)

    ctx.window.setLayout(layout)
