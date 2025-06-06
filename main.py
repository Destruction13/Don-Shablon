from PySide6.QtWidgets import QApplication
import sys
from logic.app_state import UIContext
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ctx = UIContext()
    ctx.app = app
    window = MainWindow(ctx)
    window.show()
    sys.exit(app.exec())
