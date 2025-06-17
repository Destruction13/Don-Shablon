from PySide6.QtWidgets import QApplication
import sys
import logging
from logic.app_state import UIContext
from logic.task_manager import TaskManager
from gui.main_window import MainWindow


logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ctx = UIContext()
    ctx.app = app
    ctx.task_manager = TaskManager(ctx)
    window = MainWindow(ctx)
    window.show()
    sys.exit(app.exec())
