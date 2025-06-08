import os
import sys
import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# stub PySide6 for headless test environment
qt_widgets = types.ModuleType('PySide6.QtWidgets')
qt_widgets.QComboBox = object
sys.modules['PySide6.QtWidgets'] = qt_widgets

from logic.room_filter import filter_rooms

rooms = ["1.Кофе", "1.Чай", "2.Близнецы"]


def test_prefix_filter():
    assert filter_rooms(rooms, "1.") == ["1.Кофе", "1.Чай"]


def test_substring_filter():
    assert filter_rooms(rooms, "Бли") == ["2.Близнецы"]


def test_layout_correction():
    assert filter_rooms(rooms, "<kb") == ["2.Близнецы"]
