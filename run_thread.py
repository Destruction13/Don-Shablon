import logging
import sys
import time

from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PySide6.QtCore import QRunnable, QThreadPool, QObject, Signal, Slot

logging.basicConfig(level=logging.DEBUG)

# Глобальный пул потоков
_threadpool = QThreadPool.globalInstance()

class _TaskSignals(QObject):
    finished = Signal(object)

class _Task(QRunnable):
    def __init__(self, func, callback):
        super().__init__()
        self.func = func
        self.signals = _TaskSignals()
        self.signals.finished.connect(callback)

    @Slot()
    def run(self):
        logging.debug("[POOL] Task running")
        result = None
        error = None
        try:
            result = self.func()
        except Exception as e:
            error = e
        logging.debug("[POOL] Task done")
        self.signals.finished.emit((result, error))

def run_in_thread(func, callback):
    logging.debug("[POOL] Submitting task to thread pool")
    task = _Task(func, callback)
    _threadpool.start(task)

# Пример функции
def my_func():
    logging.debug("[MYFUNC] Started")
    time.sleep(1)
    logging.debug("[MYFUNC] Finished")
    return "Done!"

# Окно с кнопкой
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thread Test")
        layout = QVBoxLayout()
        btn = QPushButton("Run OCR Thread Test")
        btn.clicked.connect(lambda: run_in_thread(my_func, self.on_result))
        layout.addWidget(btn)
        self.setLayout(layout)

    def on_result(self, result_error):
        result, error = result_error
        print("Result:", result, "| Error:", error)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())


