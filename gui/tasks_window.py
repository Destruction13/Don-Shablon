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
    QFrame,
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
    def __init__(self, task: dict, edit_cb, delete_cb, ctx=None):
        super().__init__()
        self.task = task
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        self.setMinimumHeight(80)

        title_row = QHBoxLayout()
        self.link_label = QLabel(f"<b>{task['link']}</b>")
        self.link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.link_label.setOpenExternalLinks(True)
        title_row.addWidget(self.link_label)
        title_row.addStretch()
        link_btn = QToolButton()
        link_btn.setText("🔗 Перейти по ссылке")
        link_btn.clicked.connect(lambda: self.open_link())
        if ctx:
            setup_animation(link_btn, ctx)
        title_row.addWidget(link_btn)
        outer.addLayout(title_row)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        outer.addWidget(line)

        row = QHBoxLayout()
        self.desc_label = QLabel(task["desc"])
        row.addWidget(self.desc_label)
        row.addStretch()

        self.time_label = QLabel()
        self.time_label.setFixedWidth(60)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self.time_label)

        edit_btn = QToolButton()
        edit_btn.setText("✏️")
        edit_btn.clicked.connect(lambda _=False: edit_cb())
        if ctx:
            setup_animation(edit_btn, ctx)
        row.addWidget(edit_btn)

        del_btn = QToolButton()
        del_btn.setText("🗑️")
        del_btn.clicked.connect(lambda _=False: delete_cb())
        if ctx:
            setup_animation(del_btn, ctx)
        row.addWidget(del_btn)
        outer.addLayout(row)

        bg = task.get("color", "")
        fg = ""
        for _name, (b, f) in COLOR_SCHEMES.items():
            if b == bg:
                fg = f
                break
        style = "border:1px solid #555;border-radius:6px;"
        if bg:
            color = QColor(bg)
            darker = color.darker(110)
            style = f"background-color:{darker.name()};color:{fg};" + style
        self.setStyleSheet(style)
        if ctx:
            setup_animation(self, ctx)

        self._duration = task.get("duration", max(1, int(task["remind_at"] - time.time())))
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.update_timer)
        self.update_timer()
        self._timer.start()

    def open_link(self):
        if self.task.get("link"):
            webbrowser.open(self.task["link"])

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
        for name, (bg, _fg) in COLOR_SCHEMES.items():
            if bg == current:
                self.color_combo.setCurrentText(name)
                break
        layout.addWidget(self.color_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def data(self) -> dict:
        return {
            "link": self.link_edit.text().strip(),
            "desc": self.desc_edit.toPlainText().strip(),
            "minutes": self.min_spin.value(),
            "color": COLOR_SCHEMES.get(self.color_combo.currentText(), ("", ""))[0],
        }


class TasksDialog(QDialog):
    def __init__(self, ctx, manager, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.manager = manager
        self.setWindowTitle("Мои задачи")
        self.resize(800, 1000)
        layout = QVBoxLayout(self)
        self.add_btn = QPushButton("＋ Добавить задачу")
        self.add_btn.clicked.connect(self.add_task)
        self.add_btn.setStyleSheet("min-height:36px;padding:8px 12px;font-size:14px;")
        setup_animation(self.add_btn, ctx)
        layout.addWidget(self.add_btn)
        self.list = QListWidget()
        self.list.setStyleSheet(
            "QListWidget::item{border:none;border-radius:6px;margin:4px;padding:10px;}"
        )
        self.list.setSpacing(6)
        self.list.itemDoubleClicked.connect(self.edit_task)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_menu)
        layout.addWidget(self.list)
        self.manager.task_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for task in sorted(self.manager.tasks, key=lambda t: t["remind_at"]):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, task["id"])
            widget = TaskItemWidget(
                task,
                lambda tid=task["id"]: self.edit_task_by_id(tid),
                lambda tid=task["id"]: self.confirm_delete_task(tid),
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


def show_task_notification(ctx, manager, task):
    dlg = QDialog(ctx.window if ctx else None)
    dlg.setWindowTitle("Напоминание")
    dlg.setWindowFlag(Qt.WindowStaysOnTopHint)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel(f"Напоминание по задаче: {task['desc']} ({task['link']})"))
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

