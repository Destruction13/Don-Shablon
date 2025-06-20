from __future__ import annotations

import time
import webbrowser
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QDialogButtonBox,
    QMenu,
    QWidget,
    QToolButton,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QColorDialog
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QTimer
from gui.animations import setup_animation

# Цветовые схемы: фон и цвет текста
COLOR_SCHEMES = {
    "": ("", ""),
    "Красный": ("#6e1e1e", "#f0f0f0"),
    "Жёлтый": ("#777726", "#fefefe"),
    "Синий": ("#1f3a6e", "#f0f0f0"),
    "Розовый": ("#82365b", "#fefefe"),
    "Фиолетовый": ("#3d2b5c", "#f0f0f0"),
    "Оранжевый": ("#875229", "#fefefe"),
    "Зелёный": ("#305830", "#f0f0f0"),
    "Бирюзовый": ("#2a6e6e", "#f0f0f0"),
    "Серый": ("#555555", "#fefefe"),
    "Коричневый": ("#5b4032", "#f0f0f0"),
}


class TaskItemWidget(QWidget):
    def __init__(self, task: dict, edit_cb, delete_cb, star_cb, ctx=None):
        super().__init__()
        self.setObjectName("taskBlock")
        self.task = task
        self.star_cb = star_cb
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        self.setMinimumHeight(80)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)


        title_row = QHBoxLayout()
        self.link_label = QLabel(f"<b>{task['link']}</b>")
        self.link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.link_label.setOpenExternalLinks(True)
        self.link_label.setStyleSheet("""
                                        QLabel {
                                            padding: 6px 10px;
                                            background-color: rgba(255,255,255,0.07);
                                            border: 1px solid rgba(255,255,255,0.2);
                                            border-radius: 6px;
                                            color: #5ddcff;
                                            font-weight: bold;
                                            text-decoration: underline;
                                        }
                                        QLabel:hover {
                                            color: #00ffff;
                                            background-color: rgba(0,255,255,0.1);
                                        }
                                    """)

        
        self.link_label.mousePressEvent = lambda event: webbrowser.open(task["link"])
        self.link_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.link_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_row.addWidget(self.link_label)
        title_row.addStretch()
        outer.addLayout(title_row)



        row = QHBoxLayout()
        self.desc_label = QLabel(task["desc"])
        self.desc_label = QLabel(task["desc"])
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.desc_label.setStyleSheet("""
            QLabel {
                padding: 6px 10px;
                background-color: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
            }
        """)
        row.addWidget(self.desc_label)
        row.addStretch()

        self.time_label = QLabel()
        self.time_label.setFixedWidth(80)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self.time_label)

        self.star_btn = QToolButton()
        self.star_btn.setText("⭐" if task.get("starred", False) else "☆")
        self.star_btn.setCheckable(True)
        self.star_btn.setChecked(task.get("starred", False))
        self.star_btn.setStyleSheet(
            "QToolButton{min-height:24px;padding:4px 8px;border-radius:4px;}"
            "QToolButton:hover{background-color:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            " stop:0 #5a5a5a, stop:1 #3a3a3a);}"
        )
        self.star_btn.toggled.connect(
            lambda checked: self.star_btn.setText("⭐" if checked else "☆")
        )
        self.star_btn.clicked.connect(lambda checked: self.star_cb(checked))
        if ctx:
            setup_animation(self.star_btn, ctx)
        row.addWidget(self.star_btn)

        edit_btn = QToolButton()
        edit_btn.setText("✏️")
        edit_btn.setStyleSheet(
            "QToolButton{min-height:24px;padding:4px 8px;border-radius:4px;}"
            "QToolButton:hover{background-color:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            " stop:0 #5a5a5a, stop:1 #3a3a3a);}"
        )
        edit_btn.clicked.connect(lambda _=False: edit_cb())
        if ctx:
            setup_animation(edit_btn, ctx)
        row.addWidget(edit_btn)

        del_btn = QToolButton()
        del_btn.setText("🗑️")
        del_btn.setStyleSheet(
            "QToolButton{min-height:24px;padding:4px 8px;border-radius:4px;}"
            "QToolButton:hover{background-color:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            " stop:0 #5a5a5a, stop:1 #3a3a3a);}"
        )
        del_btn.clicked.connect(lambda _=False: delete_cb())
        if ctx:
            setup_animation(del_btn, ctx)
        row.addWidget(del_btn)
        outer.addLayout(row)

        color_val = task.get("color", "")
        bg = color_val
        fg = ""
        if color_val in COLOR_SCHEMES:
            bg, fg = COLOR_SCHEMES[color_val]
        else:
            for _name, (b, f) in COLOR_SCHEMES.items():
                if b == color_val:
                    fg = f
                    break
        base = [
            "background-color: rgba(255,255,255,0.06);"
            "border: 1px solid rgba(255,255,255,0.15);"
            "border-radius: 10px;"
            "padding: 12px 16px;"
        ]


        style = " ".join(base)
        if bg:
            color = QColor(bg)
            if not fg:
                brightness = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
                fg = "#000000" if brightness > 186 else "#ffffff"
            style = " ".join([
                f"background-color:{color.name()};",
                f"color:{fg};",
                "border:1px solid rgba(255,255,255,0.15);",
                "border-radius:10px;",
                "padding:12px 16px;",
            ])

        self.setStyleSheet(style)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(18)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(0, 255, 255, 60))
        self.shadow.setEnabled(False)
        self.setGraphicsEffect(self.shadow)
        # Do not apply hover animations to the whole widget
        # to avoid replacing our drop shadow effect

        self._duration = task.get("duration", max(1, int(task["remind_at"] - time.time())))
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.update_timer)
        self.update_timer()
        self._timer.start()

    def open_link(self):
        if self.task.get("link"):
            webbrowser.open(self.task["link"])

    def enterEvent(self, event):
        try:
            self.shadow.setEnabled(True)
        except RuntimeError:
            pass
        super().enterEvent(event)

    def leaveEvent(self, event):
        try:
            self.shadow.setEnabled(False)
        except RuntimeError:
            pass
        super().leaveEvent(event)

    def update_timer(self):
        remaining = max(0, int(self.task["remind_at"] - time.time()))
        minutes = remaining // 60
        seconds = remaining % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        if remaining <= 0:
            self._timer.stop()



class TaskEditDialog(QDialog):
    def __init__(self, parent: Optional[QDialog] = None, task: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить задачу" if task is None else "Редактировать задачу")
        self.resize(450, 300)
        self._task = task or {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ссылка на задачу"))
        self.link_edit = QLineEdit(self._task.get("link", ""))
        layout.addWidget(self.link_edit)
        layout.addWidget(QLabel("Описание задачи"))
        self.desc_edit = QTextEdit(self._task.get("desc", ""))
        self.desc_edit.setMinimumHeight(100)
        layout.addWidget(self.desc_edit)
        layout.addWidget(QLabel("Через сколько минут напомнить"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 10080)
        if task:
            remaining = max(1, int((task["remind_at"] - time.time()) / 60))
            self.min_spin.setValue(remaining)
        else:
            self.min_spin.setValue(10)
        layout.addWidget(self.min_spin)
        layout.addWidget(QLabel("Цветовая метка"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(COLOR_SCHEMES.keys())

        current = self._task.get("color", "")
        self.custom_color = ""
        if current:
            if current in COLOR_SCHEMES:
                self.color_combo.setCurrentText(current)
            else:
                for name, (bg, _fg) in COLOR_SCHEMES.items():
                    if bg == current:
                        self.color_combo.setCurrentText(name)
                        break
                else:
                    self.custom_color = current

        layout.addWidget(self.color_combo)

        self.color_btn = QPushButton("🎨 Выбрать цвет")
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        self.color_combo.currentIndexChanged.connect(self.reset_custom_color)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.custom_color or "#ffffff"), self, "Выбор цвета")
        if color.isValid():
            self.custom_color = color.name()
            self.color_btn.setStyleSheet(f"background-color:{self.custom_color};")

    def reset_custom_color(self, *_):
        self.custom_color = ""
        self.color_btn.setStyleSheet("")

    @property
    def data(self) -> dict:
        return {
            "link": self.link_edit.text().strip(),
            "desc": self.desc_edit.toPlainText().strip(),
            "minutes": self.min_spin.value(),
            "color": self.custom_color
            or COLOR_SCHEMES.get(self.color_combo.currentText(), ("", ""))[0],
        }

IS_DARK_THEME = True
class TasksDialog(QDialog):
    def __init__(self, ctx, manager, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.manager = manager
        self.setWindowTitle("Мои задачи")
        self.resize(800, 1000)
        layout = QVBoxLayout(self)
        self.add_btn = QPushButton("＋ Добавить задачу")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_task)
        self.add_btn.setStyleSheet("""
                                        QPushButton {
                                            min-height: 26px;
                                            padding: 8px 12px;
                                            font-size: 30px;
                                            border: 2px solid rgba(130, 40, 10, 0.5);
                                            border-radius: 16px;
                                        }
                                        QPushButton:hover {
                                            background-color: qlineargradient(
                                                x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #5a5a5a,
                                                stop:1 #3a3a3a
                                            );
                                        }
                                    """)

        self.add_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        setup_animation(self.add_btn, ctx)

        header_widget = QWidget()
        header_layout = QGridLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.add_btn, 0, 0)

        self.notify_btn = QToolButton()
        self.notify_btn.setText("🔔" if self.manager.notifications_enabled else "🔇")
        self.notify_btn.setCheckable(True)
        self.notify_btn.setChecked(self.manager.notifications_enabled)
        self.notify_btn.clicked.connect(self.toggle_notifications)
        header_layout.addWidget(self.notify_btn, 0, 0, Qt.AlignRight | Qt.AlignTop)

        layout.addWidget(header_widget)
        self.list = QListWidget()
        self.list.setStyleSheet(
            "QListWidget::item{border:none;margin:0;padding:0;}"
        )
        self.list.setSpacing(16)
        self.list.itemDoubleClicked.connect(self.edit_task)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_menu)
        layout.addWidget(self.list)
        self.manager.task_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for task in sorted(
            self.manager.tasks,
            key=lambda t: (not t.get("starred", False), t["remind_at"]),
        ):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, task["id"])
            widget = TaskItemWidget(
                task,
                lambda tid=task["id"]: self.edit_task_by_id(tid),
                lambda tid=task["id"]: self.confirm_delete_task(tid),
                lambda checked, tid=task["id"]: self.manager.star_task(tid, checked),
                ctx=self.ctx,
            )
            self.list.addItem(item)
            item.setSizeHint(widget.sizeHint())
            self.list.setItemWidget(item, widget)

    def add_task(self):
        dlg = TaskEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.data
            if not data["desc"]:
                QMessageBox.warning(self, "Ошибка", "Введите описание")
                return
            self.manager.add_task(data["link"], data["desc"], data["minutes"], data["color"])

    def edit_task(self, item: QListWidgetItem):
        tid = item.data(Qt.UserRole)
        self.edit_task_by_id(tid)

    def edit_task_by_id(self, tid: int):
        task = next((t for t in self.manager.tasks if t["id"] == tid), None)
        if not task:
            return
        dlg = TaskEditDialog(self, task)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.data
            if not data["desc"]:
                QMessageBox.warning(self, "Ошибка", "Введите описание")
                return
            self.manager.update_task(tid, data["link"], data["desc"], data["minutes"], data["color"])

    def confirm_delete_task(self, tid: int):
        reply = QMessageBox.question(
            self,
            "Удаление",
            "Вы точно хотите удалить эту задачу?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.manager.remove_task(tid)

    def show_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_act = menu.addAction("Удалить")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == delete_act:
            tid = item.data(Qt.UserRole)
            self.confirm_delete_task(tid)

    def toggle_notifications(self, checked: bool):
        self.manager.set_notifications_enabled(checked)
        self.notify_btn.setText("🔔" if checked else "🔇")


def show_task_notification(ctx, manager, task):
    dlg = QDialog(ctx.window if ctx else None)
    dlg.setWindowTitle("Напоминание")
    dlg.setWindowFlag(Qt.WindowStaysOnTopHint)
    layout = QVBoxLayout(dlg)
    msg_label = QLabel(f"Напоминание по задаче:\n{task['desc']}\n\n{task['link']}")
    msg_label.setWordWrap(True)
    msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    msg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    layout.addWidget(msg_label)
    btn_row = QHBoxLayout()
    open_btn = QPushButton("Открыть задачу")
    postpone_btn = QPushButton("Отложить на 5 минут")
    for b in (open_btn, postpone_btn):
        b.setStyleSheet("min-height:36px;padding:8px 12px;font-size:14px;")
        if ctx:
            setup_animation(b, ctx)
    btn_row.addWidget(open_btn)
    btn_row.addWidget(postpone_btn)
    layout.addLayout(btn_row)

    def open_task():
        if task["link"]:
            webbrowser.open(task["link"])
        dlg.accept()

    def postpone():
        manager.postpone_task(task["id"], 5)
        dlg.accept()

    open_btn.clicked.connect(open_task)
    postpone_btn.clicked.connect(postpone)
    dlg.exec()

