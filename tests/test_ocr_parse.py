import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide minimal stubs for PySide6 when running headless tests
import types
qt_gui = types.ModuleType('PySide6.QtGui')
qt_gui.QGuiApplication = object
sys.modules.setdefault('PySide6.QtGui', qt_gui)
qt_widgets = types.ModuleType('PySide6.QtWidgets')
qt_widgets.QMessageBox = object
qt_widgets.QApplication = object
qt_widgets.QDialog = object
qt_widgets.QVBoxLayout = object
qt_widgets.QTextEdit = object
qt_widgets.QPushButton = object
sys.modules.setdefault('PySide6.QtWidgets', qt_widgets)
qt_core = types.ModuleType('PySide6.QtCore')
qt_core.QDate = object
qt_core.QRunnable = object
qt_core.QObject = object

class Signal:
    def __init__(self, *args, **kwargs):
        pass
    def connect(self, *args, **kwargs):
        pass
    def emit(self, *args, **kwargs):
        pass

def Slot(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

qt_core.Signal = Signal
qt_core.Slot = Slot

class _DummyPool:
    @staticmethod
    def start(*args, **kwargs):
        pass

class _DummyQThreadPool:
    @staticmethod
    def globalInstance():
        return _DummyPool()

qt_core.QThreadPool = _DummyQThreadPool
sys.modules.setdefault('PySide6.QtCore', qt_core)

# Stub easyocr so importing logic.ocr_paddle doesn't try to load heavy packages
easyocr_stub = types.ModuleType('easyocr')
easyocr_stub.Reader = object
sys.modules.setdefault('easyocr', easyocr_stub)

from logic.ocr_paddle import parse_fields, validate_with_rooms

rooms = {"БЦ Морозов": ["1.Кофе", "1.Чай"]}

sample_lines = [
    {"text": "Организатор", "score": 0.95, "bbox": [[0,0],[100,0],[100,20],[0,20]]},
    {"text": "Наталья", "score": 0.96, "bbox": [[0,25],[60,25],[60,45],[0,45]]},
    {"text": "Шевченко", "score": 0.94, "bbox": [[65,25],[150,25],[150,45],[65,45]]},
    {"text": "БЦ Морозов", "score": 0.93, "bbox": [[0,60],[120,60],[120,80],[0,80]]},
    {"text": "1.Кофе", "score": 0.92, "bbox": [[0,85],[80,85],[80,105],[0,105]]},
]

def test_parse_and_validate():
    parsed = parse_fields(sample_lines)
    validated = validate_with_rooms(parsed, rooms)
    assert validated["name"] == "Наталья Шевченко"
    assert validated["bz"] == "БЦ Морозов"
    assert validated["room"] == "1.Кофе"

