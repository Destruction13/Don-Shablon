"""Пример переключения тем с динамическим эффектом на кнопках."""
from PySide6.QtWidgets import QApplication, QVBoxLayout, QLabel, QWidget, QComboBox

from gui.widgets import HoverButton
from gui.themes import THEMES
from logic.app_state import UIContext


def main():
    app = QApplication([])
    ctx = UIContext()
    ctx.app = app
    w = QWidget()
    layout = QVBoxLayout(w)

    label = QLabel("Выберите тему:")
    layout.addWidget(label)

    combo = QComboBox()
    combo.addItems(THEMES.keys())
    layout.addWidget(combo)

    btn = HoverButton("Кнопка")
    layout.addWidget(btn)

    ctx.register_button(btn)

    def change(name):
        ctx.current_theme_name = name
        ctx.apply_theme()

    combo.currentTextChanged.connect(change)
    ctx.apply_theme()

    w.show()
    app.exec()


if __name__ == "__main__":
    main()
