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
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QDialogButtonBox,
    QMenu,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt


class TaskEditDialog(QDialog):
    def __init__(self, parent: Optional[QDialog] = None, task: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить задачу" if task is None else "Редактировать задачу")
        self._task = task or {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ссылка на задачу"))
        self.link_edit = QLineEdit(self._task.get("link", ""))
        layout.addWidget(self.link_edit)
        layout.addWidget(QLabel("Описание задачи"))
        self.desc_edit = QLineEdit(self._task.get("desc", ""))
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
        self.color_combo.addItems(["", "red", "green", "blue", "yellow"])
        self.color_combo.setCurrentText(self._task.get("color", ""))
        layout.addWidget(self.color_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def data(self) -> dict:
        return {
            "link": self.link_edit.text().strip(),
            "desc": self.desc_edit.text().strip(),
            "minutes": self.min_spin.value(),
            "color": self.color_combo.currentText(),
        }


class TasksDialog(QDialog):
    def __init__(self, ctx, manager, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.manager = manager
        self.setWindowTitle("Мои задачи")
        layout = QVBoxLayout(self)
        self.add_btn = QPushButton("+ Добавить задачу")
        self.add_btn.clicked.connect(self.add_task)
        layout.addWidget(self.add_btn)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.edit_task)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_menu)
        layout.addWidget(self.list)
        self.manager.task_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for task in sorted(self.manager.tasks, key=lambda t: t["remind_at"]):
            item = QListWidgetItem(f"{task['desc']} ({task['link']})")
            item.setData(Qt.UserRole, task["id"])
            color = task.get("color")
            if color:
                item.setBackground(QColor(color))
            self.list.addItem(item)

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

    def show_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_act = menu.addAction("Удалить")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == delete_act:
            tid = item.data(Qt.UserRole)
            self.manager.remove_task(tid)


def show_task_notification(ctx, manager, task):
    dlg = QDialog(ctx.window if ctx else None)
    dlg.setWindowTitle("Напоминание")
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel(f"Напоминание по задаче: {task['desc']} ({task['link']})"))
    btn_row = QHBoxLayout()
    open_btn = QPushButton("Открыть задачу")
    postpone_btn = QPushButton("Отложить на 5 минут")
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

