from PySide6.QtWidgets import QApplication
import sys
import logging
from logic.app_state import UIContext
from gui.main_window import MainWindow

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    ctx = UIContext()
    ctx.app = app
    window = MainWindow(ctx)
    window.show()
    sys.exit(app.exec())
