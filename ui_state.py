import tkinter as tk

root = None

current_theme_name = "Светлая"
selected_theme = None  # ← теперь не создаём сразу!

input_fields = []
fields = {}
fields_frame = None

type_var = None
link_var = None
asya_mode = None
asya_extra_frame = None
output_text = None
music_path = "James.mp3"

is_custom_asya = None
asya_name_var = None
asya_gender_var = None

music_playing = False
music_paused = False

