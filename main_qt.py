from core.qt_app_state import QtUIContext
from qt_ui import build_ui


def main():
    ctx = QtUIContext()
    build_ui(ctx)
    ctx.window.setWindowTitle("Генератор шаблонов встреч (Qt)")
    ctx.window.show()
    ctx.app.exec()


if __name__ == "__main__":
    main()
