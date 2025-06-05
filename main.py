import tkinter as tk
import pygame

import ui_state
from ui import build_ui, init_music

# Создаём root
ui_state.root = tk.Tk()
ui_state.root.title("Генератор шаблонов встреч")
ui_state.root.configure(bg="white")

# Теперь можно инициализировать tkinter-переменные
ui_state.selected_theme = tk.StringVar(value=ui_state.current_theme_name)
ui_state.type_var = tk.StringVar()
ui_state.link_var = tk.StringVar()
ui_state.asya_mode = tk.BooleanVar()
ui_state.is_custom_asya = tk.BooleanVar()
ui_state.asya_name_var = tk.StringVar()
ui_state.asya_gender_var = tk.StringVar()

# Музыка
pygame.init()
pygame.mixer.init()
if ui_state.music_path:
    init_music(ui_state.music_path)

# Интерфейс
build_ui(ui_state.root)
ui_state.root.mainloop()

