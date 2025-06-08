"""Minimal demo for FilteringComboBox."""
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox

from logic.room_filter import FilteringComboBox

rooms_map = {
    "БЦ Морозов": ["1.Кофе", "1.Чай", "2.Близнецы"],
    "БЦ Аврора": ["2B.Гостиная дядюшки Скруджа"],
}


class Demo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.bz_combo = QComboBox()
        self.bz_combo.addItems(rooms_map.keys())

        self.room_combo = FilteringComboBox()

        layout.addWidget(QLabel("БЦ:"))
        layout.addWidget(self.bz_combo)
        layout.addWidget(QLabel("Переговорка:"))
        layout.addWidget(self.room_combo)

        self.bz_combo.currentTextChanged.connect(self.update_rooms)
        self.update_rooms(self.bz_combo.currentText())

    def update_rooms(self, bz):
        self.room_combo.set_items(rooms_map.get(bz, []))


if __name__ == "__main__":
    app = QApplication([])
    demo = Demo()
    demo.show()
    app.exec()
