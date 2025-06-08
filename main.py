from PySide6.QtWidgets import QApplication
import sys
import logging
from logic.app_state import UIContext
from gui.main_window import MainWindow
import logging
import torch
import platform
import sys

print("Python:", sys.version)
print("CUDA доступен:", torch.cuda.is_available())
print("PyTorch:", torch.__version__)
print("OS:", platform.system())


logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True  # 💥 Вот это критично
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ctx = UIContext()
    ctx.app = app
    window = MainWindow(ctx)
    window.show()
    sys.exit(app.exec())
