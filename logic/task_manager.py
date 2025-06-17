import json
import os
import time
import webbrowser
from typing import List, Dict, Any

from PySide6.QtCore import QObject, QTimer, Signal


class TaskManager(QObject):
    """Manage user tasks with reminders."""

    task_changed = Signal()

    def __init__(self, ctx, path: str = "tasks.json") -> None:
        super().__init__()
        self.ctx = ctx
        self.path = os.path.join(os.path.dirname(os.path.dirname(__file__)), path)
        self.tasks: List[Dict[str, Any]] = []
        self.timers: Dict[int, QTimer] = {}
        self.notifications_enabled: bool = True
        self.load()

    def load(self) -> None:
        """Load tasks from json file and schedule reminders."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception:
                self.tasks = []
        else:
            self.tasks = []
        for task in self.tasks:
            task.setdefault("duration", max(1, int(task["remind_at"] - time.time())))
            task.setdefault("starred", False)
            self._schedule(task)

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_task(self, link: str, desc: str, minutes: int, color: str = "") -> Dict[str, Any]:
        task_id = int(time.time() * 1000)
        duration = minutes * 60
        task = {
            "id": task_id,
            "link": link,
            "desc": desc,
            "remind_at": time.time() + duration,
            "color": color,
            "duration": duration,
            "starred": False,
        }
        self.tasks.append(task)
        self.save()
        self._schedule(task)
        self.task_changed.emit()
        return task

    def update_task(self, task_id: int, link: str, desc: str, minutes: int, color: str) -> None:
        for task in self.tasks:
            if task["id"] == task_id:
                duration = minutes * 60
                task.update({
                    "link": link,
                    "desc": desc,
                    "remind_at": time.time() + duration,
                    "color": color,
                    "duration": duration,
                })
                self.save()
                self._schedule(task)
                self.task_changed.emit()
                break

    def postpone_task(self, task_id: int, minutes: int) -> None:
        for task in self.tasks:
            if task["id"] == task_id:
                duration = minutes * 60
                task["remind_at"] = time.time() + duration
                task["duration"] = duration
                self.save()
                self._schedule(task)
                break

    def star_task(self, task_id: int, starred: bool) -> None:
        for task in self.tasks:
            if task["id"] == task_id:
                task["starred"] = starred
                self.save()
                self.task_changed.emit()
                break

    def set_notifications_enabled(self, enabled: bool) -> None:
        self.notifications_enabled = enabled
        self.task_changed.emit()

    def remove_task(self, task_id: int) -> None:
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        timer = self.timers.pop(task_id, None)
        if timer:
            timer.stop()
        self.save()
        self.task_changed.emit()

    # Internal helpers
    def _schedule(self, task: Dict[str, Any]) -> None:
        delay = max(0, int((task["remind_at"] - time.time()) * 1000))
        timer = self.timers.get(task["id"])
        if timer is None:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda tid=task["id"]: self._notify(tid))
            self.timers[task["id"]] = timer
        else:
            timer.stop()
            timer.timeout.disconnect()
            timer.timeout.connect(lambda tid=task["id"]: self._notify(tid))
        timer.start(delay)

    def _notify(self, task_id: int) -> None:
        if not self.notifications_enabled:
            return
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        from gui.tasks_window import show_task_notification

        show_task_notification(self.ctx, self, task)

