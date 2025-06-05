from core.app_state import UIContext
from ui import build_ui

if __name__ == "__main__":
    ctx = UIContext()
    ctx.root.title("Генератор шаблонов встреч")
    build_ui(ctx)
    ctx.root.mainloop()


