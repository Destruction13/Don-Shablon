# core/app_state.py
import tkinter as tk
from tkinter import ttk


class UIContext:
    """Centralized storage for UI state and widgets."""
    def __init__(self):
        # Основной root
        self.root = tk.Tk()
        self.root.title("Генератор шаблонов встреч")
        self.root.configure(bg="white")

        # Переменные интерфейса
        self.type_var = tk.StringVar()
        self.link_var = tk.StringVar()
        self.asya_mode = tk.BooleanVar(value=False)
        self.asya_name_var = tk.StringVar()
        self.asya_gender_var = tk.StringVar()
        self.current_theme_name = "Светлая"
        self.selected_theme = tk.StringVar(value=self.current_theme_name)

        # Хранилище виджетов
        self.fields: dict[str, tk.Widget] = {}
        self.input_fields: list[tk.Widget] = []

        # Отдельные блоки UI
        self.fields_frame: tk.Frame | None = None
        self.output_text: tk.Text | None = None
        self.asya_extra_frame: ttk.Frame | None = None  # legacy, no longer packed
        self.asya_popup: tk.Toplevel | None = None
        self.asya_button: ttk.Button | None = None
        self.asya_mode_button: ttk.Button | None = None
        self.action_frame: tk.Frame | None = None
        self.custom_asya_saved: bool = False
        self.custom_asya_on: bool = False

        # Музыка
        self.music_path = "James.mp3"
        self.music_state = {
            "playing": False,
            "paused": False
        }

        # Фон и картинка
        self.bg_label: tk.Label | None = None
        self.bg_image_raw = None
        self.bg_image_tk = None
        self.bg_image_path: str | None = None

        # Кеширование и дебаунс фоновой картинки
        self.bg_resize_cache: dict = {}
        self.bg_update_after_id: str | None = None

    def reset_fields(self):
        """Полностью очищает поля формы"""
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.fields.clear()



