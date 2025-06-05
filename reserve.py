import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import locale
import random
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import re
import urllib.parse
from datetime import datetime
import requests
import os
import sys
import pygame

pygame.init()
pygame.mixer.init()

music_path = None  # по умолчанию

try:
    # Определяем базовую директорию
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Путь к mp3
    music_filename = "James_Brown_Fred_Wesley_The_JBs_-_People_Get_Up_And_Drive_Your_Funky_Soul_Remix_Remix_71148482.mp3"
    music_path = os.path.join(base_dir, music_filename)

    # Пробуем загрузить
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
    else:
        print(f"[WARNING] Музыка не найдена: {music_path}")
        music_path = None
except Exception as e:
    print(f"[ERROR] Ошибка при загрузке музыки: {e}")
    music_path = None





def get_resource_path(relative_path):
    """Определяет путь к ресурсу внутри .exe или рядом с ним"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


music_playing = False
music_paused = False

def toggle_music():
    global music_playing, music_paused

    if not music_path:
        print("[INFO] Музыка не загружена — ничего не делаем.")
        return

    if not music_playing:
        pygame.mixer.music.play(-1)
        music_button.config(text="⏸")  # показать паузу
        music_playing = True
        music_paused = False
    elif not music_paused:
        pygame.mixer.music.pause()
        music_button.config(text="▶️")  # показать play
        music_paused = True
    else:
        pygame.mixer.music.unpause()
        music_button.config(text="⏸")
        music_paused = False



DEEPL_API_KEY = "69999737-95c3-440e-84bc-96fb8550f83a:fx"
DEEPL_URL = "https://api-free.deepl.com/v2/translate"



import difflib
import easyocr

reader = easyocr.Reader(['ru', 'en'])

def extract_fields_from_text(texts, rooms_by_bz):
    name = ""
    bz = ""
    room = ""
    start_time = ""
    end_time = ""
    date = ""

    # 1. Имя организатора (ищем рядом с "Организатор")
    for i, txt in enumerate(texts):
        if "организатор" in txt.lower() and i+1 < len(texts):
            full_name = texts[i+1]
            name = full_name.split()[0]

    
    # 2. Дата и время 
    found_times = []
    for txt in texts:
        cleaned = txt.strip()
        cleaned = re.sub(r"[^\d]", ":", cleaned)  # всё, что не цифра — заменяем на ":"
        if re.fullmatch(r"\d{2}:\d{2}", cleaned):
            found_times.append(cleaned)
            if len(found_times) == 2:
                break

    if len(found_times) == 2:
        start_time, end_time = found_times

    # Теперь ищем первую подходящую дату
    for txt in texts:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", txt.strip()):
            date = txt.strip()
            break

    # 3. БЦ (ищем по слову "БЦ")
    for txt in texts:
        if "морозов" in txt.lower():
            bz = "БЦ Морозов"


    # 4. Переговорка (ищем по частичному совпадению)
    flat_rooms = []
    for bz_key, rooms in rooms_by_bz.items():
        for room_name in rooms:
            flat_rooms.append((bz_key, room_name))

    # проходим по текстам и ищем совпадение с последним словом из названия переговорки
    for txt in texts:
        txt_lower = txt.lower()
        for bz_key, room_name in flat_rooms:
            short = room_name.split(".")[-1].split()[0].lower()
            if short and short in txt_lower and len(short) > 3:
                room = room_name
                bz = bz_key
                break

    return name, bz, room, date, start_time, end_time

from PIL import Image
from PIL import ImageDraw



def is_checkbox_checked(image, x, y, size=12, threshold=200, fill_threshold=0.2):
    # Обрезаем область чекбокса
    cropped = image.crop((x, y, x + size, y + size)).convert("L")  # L = grayscale
    pixels = cropped.getdata()

    # Считаем сколько тёмных пикселей
    dark_pixels = sum(1 for p in pixels if p < threshold)
    total_pixels = len(pixels)

    fill_ratio = dark_pixels / total_pixels
    print(f"[DEBUG] fill_ratio: {fill_ratio:.2f}")

    # Если больше 10% тёмных — галка стоит
    return fill_ratio > fill_threshold


from PIL import ImageDraw

def detect_repeat_checkbox(image_path, ocr_results):
    image = Image.open(image_path)
    print("[DEBUG] Начинаем поиск чекбокса...")

    for bbox, text, _ in ocr_results:
        print(f"[OCR] Найден текст: '{text}' с bbox: {bbox}")

        if text.strip().lower() == "повторять":
            print("[DEBUG] Найдено слово 'повторять'")

            x = int(bbox[0][0]) - 15
            y = int(bbox[0][1]) + 11

            print(f"[DEBUG] Координаты для анализа чекбокса: x={x}, y={y}")

            # Дебаг-рамка
            draw = ImageDraw.Draw(image)
            draw.rectangle([x - 10, y - 10, x + 10, y + 10], outline="red")
            image.save("checkbox_debug.png")

            return is_checkbox_checked(image, x, y)

    print("[DEBUG] Слово 'повторять' не найдено вообще.")
    return False



from PIL import ImageGrab

def import_from_clipboard_image():
    meeting_type = type_var.get()
    print(f"[DEBUG] Тип встречи: {meeting_type}")
    image = ImageGrab.grabclipboard()
    if isinstance(image, Image.Image):
        image_path = "clipboard_temp.png"
        image.save(image_path)

        results = reader.readtext(image_path)
        texts = [x[1] for x in results]

        name, bz, room, date, start_time, end_time = extract_fields_from_text(texts, rooms_by_bz)

        is_regular = "Регулярная" if detect_repeat_checkbox(image_path, results) else "Обычная"

        if "name" in fields and name:
            fields["name"].delete(0, tk.END)
            fields["name"].insert(0, name)

        # Если BZ не в словаре — добавим временно
        if bz and bz not in rooms_by_bz:
            rooms_by_bz[bz] = []

        # Заполним поля (BZ — обязательно первым)
        if "bz" in fields:
            fields["bz"].set(bz)

        # Обновим списки для AutocompleteCombobox ПЕРЕД вставкой переговорок
        if meeting_type == "Обмен" and "bz" in fields and "his_room" in fields and "my_room" in fields:
            current_bz = fields["bz"].get()
            full_list = rooms_by_bz.get(current_bz, [])
            fields["his_room"].set_completion_list(full_list)
            fields["my_room"].set_completion_list(full_list)

        # Теперь безопасно вставляем переговорки
        if meeting_type == "Обмен":
            if "his_room" in fields and room:
                fields["his_room"].set(room)
        else:
            if "room" in fields and room:
                fields["room"].set(room)


        if "datetime" in fields and date:
            try:
                fields["datetime"].set_date(datetime.strptime(date, "%d.%m.%Y"))
            except Exception as e:
                print("Ошибка даты:", e)

        if "start_time" in fields and start_time:
            fields["start_time"].set(start_time)

        if "end_time" in fields and end_time:
            fields["end_time"].set(end_time)

        if "regular" in fields:
            fields["regular"].set(is_regular)

    else:
        messagebox.showerror("Ошибка", "Буфер обмена не содержит изображения.")








class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        # Устанавливаем кастомный стиль Combobox по умолчанию
        kwargs.setdefault("style", "Custom.TCombobox")
        super().__init__(master, **kwargs)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self._handle_keyrelease)
        self.bind('<Return>', self._handle_accept)
        self.bind('<Tab>', self._handle_tab)
        self['values'] = self._completion_list

    def _handle_keyrelease(self, event):
        if event.keysym in ("BackSpace", "Left", "Right", "Down", "Up", "Return", "Tab"):
            return

        typed = self.get().lower()
        self._hits = [item for item in self._completion_list if typed in item.lower()]
        self['values'] = self._hits or self._completion_list

    def _handle_accept(self, event):
        if self._hits:
            self.set(self._hits[0])
            self.icursor(tk.END)
        self.tk_focusNext().focus()
        return "break"

    def _handle_tab(self, event):
        self.event_generate('<Down>')  # просто открывает список
        return "break"

def translate_to_english():
    text = output_text.get("1.0", tk.END).strip()
    if not text:
        return

    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": "EN"
    }

    try:
        response = requests.post(DEEPL_URL, data=params)
        response.raise_for_status()
        result = response.json()
        translated_text = result["translations"][0]["text"]

        # Вставим поверх
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, translated_text)
    except Exception as e:
        messagebox.showerror("Ошибка перевода", f"Не удалось перевести текст:\n{e}")


def add_field_with_clear_button(label_text, var_name):
    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)

    frame = ttk.Frame(fields_frame, style="Custom.TFrame")
    frame.pack(fill="x", padx=10, pady=2)

    entry_var = link_var if var_name == "link" else tk.StringVar()
    entry = ttk.Entry(frame, textvariable=entry_var, style="TEntry")
    entry.pack(side="left", fill="x", expand=True)

    def clear_entry():
        entry_var.set("")

    clear_btn = ttk.Button(frame, text="✖", width=2, command=clear_entry)
    clear_btn.pack(side="left", padx=(5, 0))

    fields[var_name] = entry
    input_fields.append(entry)

    def focus_next(event, current=entry):
        i = input_fields.index(current)
        if i + 1 < len(input_fields):
            input_fields[i + 1].focus_set()
        return "break"

    entry.bind("<Return>", focus_next)
    enable_ctrl_v(entry)



rooms_by_bz = {
    "БЦ Морозов": [
        "1.Чай", "1.Кофе", "1.Абылайша (домик)", "1.Аил (домик)", "1.Red Hot Chili Peppers",
        "1.Красная дорожка", "1.Мачу-Пикчу (домик)", "2.Гай Ричи (домик)", "2.Забота (домик)", "2.Деньги",
        "2.Карты", "2.Ствола", "2.Вежа (домик)", "2.Капитана", "2.В одном", "2.Близнецы", "2.Из ларца",
        "2.Дяолоу (домик)", "2.Конак (домик)", "2.Ледяная (домик)", "2.Порт-Ройал (домик)", "2.Оранжевый галстук",
        "2.Оранжевый гусь", "2.Оранжевое настроение", "2.Orange Soda - 2", "2.Orange soda - 1",
        "2.Оранжевый — хит сезона", "2.Оранжевые песни", "2.Оранжевые мамы", "2.Оранжевый верблюд - 1", "2.Оранжевый верблюд - 1",
        "2.Оранжевое море - 1", "2.Оранжевое море - 2", "2.Фанза (домик)", "2.Netcat", "2.Аннапурна (домик)",
        "2.Кажим (домик)", "2.Кью", "3.Пуэблито (домик)", "3.Поросенка", "3.14", "3.Бурама (домик)",
        "3.Сакля (домик)", "3.Богатыря", "3.Медведя", "3.Третьяковка", "3.Мушкетера", "3.Кита",
        "3.Тополя на Плющихе", "3.Сёстры", "3.XXX", "3.Танкиста", "3.В лодке", "3.Green dollar",
        "3.Васаби (домик)", "3.Гренландия (домик)", "3.Подорожник (домик)", "3.Укроп (домик)", "3.Юрта (домик)",
        "3.Зелёная лампа", "3.Зелёный фонарь", "3.Зелёный свет", "3.Зелёный горошек - 1", "3.Зелёный горошек - 2",
        "3.Зелёный фургон", "3.Green card", "3.Green day", "3.Зелёный лук - 1", "3.Зелёный лук - 2",
        "3.Зелёная трава", "3.Зелёные человечки", "3.Сельдерей (домик)", "4.Сыра", "4.Квадро", "4.The Beatles",
        "4.MatrixNet (домик)", "4.Валкаран (домик)", "4.Интент (домик)", "4.Времени года", "4.Стороны Света",
        "4.Квартал", "4.Квартет", "4.Хорошо", "4.Комнаты", "4.2 х 2", "4.Апрель", "4.Марс", "4.404",
        "4.Барабора (домик)", "4.Кносс (домик)", "4.Кунашир", "4.Троя (домик)", "4.Туэдзи (домик)",
        "4.Жёлтые тюльпаны", "4.Жёлтые ботинки", "4.Жёлтые штаны", "4.Жёлтый дом-1", "4.Жёлтый дом-2",
        "4.Жёлтый лист осенний", "4.Yellow river", "4.Yellow submarine", "4.Жёлтый полосатик",
        "4.Жёлтая пресса", "4.Жёлтые страницы - 1", "4.Жёлтые страницы - 2", "5.Петра (домик)",
        "5.Вавилон-5", "5.The Jackson 5", "5.Maroon 5", "5.Трулло (домик)", "5.Колесо", "5.Колонна",
        "5.Аргентина-Ямайка", "5.O'clock", "5.Отлично", "5.Звёзд", "5.Элемент", "5.Точка", "5.Ураса (домик)", "6.Грот (домик)",
        "6.Сатурн", "6.Континенты", "6.Гекзаметр", "6.Морда (домик)", "6.Пальейру (домик)",
        "6.Пальясо (домик)", "6.Яранга (домик)", "6.Серафим", "6.Шива", "6.Соток", "6.Палата",
        "7.Карфаген (домик)", "7.Неделька", "7.Ноября", "7.40", "7.Нянек"
    ],
    "БЦ Бенуа": [
        "1.1703", "1.Заячий Остров", "1.Монетный Двор", "1.Пляж",
        "2.Белые ночи", "2.Братство Плюса", "2.Бродский", "2.Весёлый посёлок",
        "2.Довлатов", "2.Дом Кино", "2.Достоевский", "2.КиШ (домик)", "2.Кибердеревня", "2.Князь (домик)",
        "2.Колдун (домик)", "2.Ларек (домик)", "2.Ленинград", "2.Марсово", "2.Питер FM", "2.Полюстрово",
        "2.Сосновый Бор", "2.Сплин", "2.Шалаш", "2.Гостинка", "2.Елисеевский", "2.Зингер", "2.Невский",
        "2.Обводный", "2.Поребрик (домик)",
        "3.Домик Петра (домик)", "3.Иглу (домик)", "3.Каретник (домик)", "3.Остров Котлин (домик)",
        "3.ПУНК (Домик)", "3.Самба", "3.Секретный дом (домик)", "3.Стрельна", "3.Психотерапевт",
        "3.Финбан", "3.Румба", "3.Адмиралтейство", "3.Грибоедов", "3.Маринка", "3.Ладога",
        "3.Пальмира", "3.Венеция",
        "4.Ботный домик (домик)", "4.Думская", "4.Зимний", "4.Колодец (Домик)", "4.Корюшка", "4.Летний",
        "4.Первый мед", "4.Подъезд", "4.Ротонда (домик)", "4.Эрмитаж", "4.Зал для танцев (не домик)",
        "4.Медицинский кабинет", "4.Аврора", "4.Чижик-Пыжик", "4.Лисий Нос", "4.Парадная", "4.Булочная",
        "4.Кронштадт", "4.Мойка",
        "5.Автово", "5.Греча (Домик)", "5.Карповка", "5.Кура (домик)", "5.Настольный теннис",
        "5.Парнас (Домик)", "5.Рюмочная (домик)", "5.Шаверма (Домик)", "5.Pac-Man", "5.Купчино",
        "5.Пять Углов", "5.Фонтанка", "5.XML",
        "8.Атланты", "8.Башня Грифонов", "8.Двенадцать коллегий", "8.Елагин (домик)",
        "8.Измайловский (домик)", "8.Исаакиевская", "8.Кронверкский (домик)", "8.Лахта", "8.Охта",
        "8.Петропавловская", "8.Пулково", "8.Тучков (домик)", "8.Флагшток"
    ],
    "БЦ Мамонтов": [
        "2.Инспектор Гаджет", "2.Кава (домик)", "2.Коркамурт (домик)", "2.Кувавса (домик)", "2.Кузя (домик)",
        "2.Пуаро", "2.Коломбо", "2.Пинкертон", "2.Гриффиндор", "2.Когтевран", "2.Пуффендуй", "2.Слизерин",
        "3.Алеаторная",
        "3.Вардо (домик)", "3.Виндикация", "3.Делькредере", "3.Икукване (домик)", "3.Лепа-лепа (домик)",
        "3.Мэрилэнд", "3.Рондавель (домик)", "3.Сервитут", "3.Узуфрукт", "3.Эстоппель", "3.Монтана",
        "3.Миннесота", "3.Учительская", "3.Лекторий",
        "4.Alpha cube (домик)", "4.Индийский чай", "4.Лубяная (домик)", "4.Льдинка (домик)", "4.Мадагаскар",
        "4.Майорка (домик)", "4.Мамонтёнок (домик)", "4.Миконос", "4.Мозамбик", "4.Моська", "4.Посудная лавка",
        "4.Саванна", "4.Слон", "4.Мальта",
        "5.Golden Hind (domik)", "5.Jesus of Lübeck (domik)", "5.Level up", "5.Васко да Гама",
        "5.Дядюшка Ау (домик)", "5.Мальдивский хаб", "5.Нафаня (домик)", "5.Помпеи", "5.Потолки", "5.Преломление",
        "5.Ухура (домик)", "5.Фале (домик)", "5.Хоган (домик)", "5.Шатёр (домик)",
        "5.Яндекс.Пробки", "5.Хэдкаунт", "5.Сортировочная", "5.Справочная", "5.Чулан", "5.Магеллан", "5.Хокинс",
        "5.Крузенштерн", "5.Беллинсгаузен", "5.Лазарев"
    ],
    "БЦ Строганов": [
        "2.Арнаутовка", "2.Батур (Домик)", "2.Везувий (домик)", "2.Воскресение (домик)", "2.Девятнадцать зим",
        "2.Килиманджаро (домик)", "2.Крейцерова соната (домик)", "2.Лев Николаевич", "2.Мак-Кинли (домик)",
        "2.Миссури (домик)", "2.Монблан (домик)", "2.Плоды просвещения (домик)", "2.Софья Андреевна",
        "2.Так что же нам делать? (домик)", "2.Этна (домик)", "2.Парфюмерия", "2.Аптека", "2.Ювелирный",
        "2.Цветы", "2.Супермаркет",
        "3.Ателье", "3.ВХУТЕМАС (домик)", "3.Виникунка (домик)", "3.Дейнека", "3.Зоомагазин", "3.Коровин",
        "3.Костюмы", "3.Маяковский", "3.Обувной", "3.Подарки", "3.Простачок (домик)", "3.Родченко",
        "3.Соня (домик)", "3.Строгановка", "3.Фишт (домик)", "3.Фудзи (домик)", "3.Шехтель (домик)", "3.Щусев",
        "3.Электроника",
        "4.Белуха (домик)", "4.Изба (домик)", "4.Конгур (домик)", "4.Кракатау (домик)", "4.Умник (домик)",
        "4.Спорттовары", "4.Книжный",
        "5.Весельчак (домик)", "5.Миелофон (домик)", "5.Игрушки",
        "5А.Винотека", "5А.Фудкорт", "5А.Боулинг", "5А.У фонтана", "5А.Кинотеатр", "5А.Кондитерская"
    ],
    "БЦ Аврора": [
        "1D.Aston Martin", "1E.Абрикосовая", "1E.Виноградная", "1E.Вишнёвая", "1E.Грушевая", "1E.Звукозапись (домик)",
        "1E.Зелёная", "1E.Квас (домик)", "1E.Мороженое (домик)", "1E.Прохладная", "1E.Союзпечать (домик)",
        "1E.Табак (домик)", "1E.Тенистая", "2A.Брамбл (домик)", "2A.Друзья", "2A.Мартинез (домик)",
        "2A.Палома", "2A.Сазерак (домик)", "2A.Чудотворцы", "2B.Аферист (домик)", "2B.Безумные деньги",
        "2B.Бильярд", "2B.Горшочек лепрекона", "2B.Гостиная дядюшки Скруджа", "2B.Деньгохранилище Скруджа",
        "2B.Золотая лихорадка", "2B.Игра на понижение (домик)", "2B.Клуб миллиардеров",
        "2B.Миллиарды (домик)", "2B.Озарк (домик)", "2B.Пещера Аладдина",
        "2B.Подпольная империя", "2B.Предел риска (домик)", "2B.Уолл-стрит", "2B.Чеканная монета",
        "2B.Чёрный ящик (домик)", "2B.Чужие деньги", "2D.Куба Либре", "2D.Негрони", "2E.CashFlow",
        "2E.Бабушкин ремонт", "2E.Бамблби (домик)", "2E.Горячая", "2E.Два разраба", "2E.Зато своя! (домик)",
        "2E.Квадратный метр", "2E.Коммуналка (домик)", "2E.Новостройка", "2E.Сталинка", "2E.Хата с краю",
        "2E.Хатка бобра (домик)", "2E.Холодная", "2E.Человейник", "3A.9999", "3A.Contact rate (домик)",
        "3A.PROграмма", "3A.TRUST me", "3A.Автопополнение", "3A.Время-деньги (домик)", "3A.Ключевая ставка",
        "3A.Копилка", "3A.Промоставка (домик)", "3A.Раскрути выгоду", "3A.Топчан", "3A.QR (домик)",
        "3B.Бельдяжки", "3B.Высота (домик)", "3B.Геосфера (домик)", "3B.Глубина (домик)", "3B.Долгота (домик)",
        "3B.Кибер-Спасское", "3B.Кинопаркинг", "3B.Классный час", "3B.Отель Гранд Будапешт", "3B.Сново-Здорово",
        "3B.Тормозное шоссе", "3B.Улица Поисковая", "3B.Улица Программирования", "3B.Широта (домик)",
        "3B.Юго-Северная", "3D.Saint-Barth", "3D.Ибица", "3D.Канкун", "3D.Майами", "3D.Монако", "3E.VIN Дизель",
        "3E.АРБ (домик)", "3E.Бортжурнал (домик)", "3E.Буханка (домик)", "3E.Бэтмобиль (домик)", "3E.Кабриолет",
        "3E.Не бита", "3E.Не крашена", "3E.Нива", "3E.Пикап", "3E.Седан", "3E.Хэтчбек", "3E.Шоурум",
        "4A.ID меня", "4A.Банковская тайна", "4A.Банковская ячейка", "4A.Банкомат (домик)", "4A.Дебет",
        "4A.Идентификация личности", "4A.Когда пластик?", "4A.Копеечка (домик)", "4A.Кредит",
        "4A.Пенсионный домик", "4A.Потрачено", "4A.Токен (домик)", "4B.Домик в деревне", "4B.Свободная", "4D.Four Seasons", "4D.Ritz Carlton", "4D.Savoy", "4E.All inclusive",
        "4E.Yaustal", "4E.Горизонтали (домик)", "4E.Гусь-Хрустальный", "4E.Даша Путешественница", "4E.Зал ожидания",
        "4E.Купе", "4E.Мальдивы", "4E.Плацкарт (домик)", "4E.Ржев (домик)",
        "4E.Станция Петушки", "4E.Сутулыч (домик)", "4E.Тридевятое царство", "4E.Тридесятое государство",
        "4E.Трёп", "5A.АЗС", "5A.Аэропорт", "5A.Безумный Макс", "5A.Вигвам (домик)", "5A.Землянка (домик)",
        "5A.Игры", "5A.Конец света (домик)", "5A.Скорость", "5A.Тулоу (домик)", "5A.Таксопарк", "5A.Терминал",
        "5A.Типи (домик)", "5A.Форсаж", "5A.Шоураннер", "5B.Клетка Фарадея", "5B.Консерватория",
        "5B.Кот Шрёдингера", "5B.Овинник (домик)", "5B.Петля гистерезиса", "5B.Резонанс (домик)", "5B.Угол фи",
        "5B.Яблоко Ньютона", "5D.Burj Khalifa", "5D.Marina Bay Sands", "5D.Международка",
        "5E.Асфальт Реальности", "5E.Двойной листочек", "5E.Задача со звёздочкой", "5E.Кураторская",
        "5E.Мне ко второй", "5E.Последняя парта", "5E.Продленка", "5E.Рескилка", "5E.Родительское собрание",
        "5E.Сон Менделеева", "5E.Точка роста", "5E.Ума палата", "5E.Шалость удалась",
        "6A.АИ-80 (домик)", "6A.АИ-92 (домик)", "6A.АИ-95 (домик)", "6A.Вотсхир", "6A.ГУ", "6A.ДТ (домик)",
        "6A.Драгозум", "6A.Индор", "6A.Последняя миля",
        "7A.Дружочки", "7A.Круассаны", "7A.Мы вам перезвоним", "7A.Пирожочки", "7A.Просекко",
        "7A.Слабоумиe и Отвага", "7A.Таков путь", "7A.Финал",
        "8A.Керф", "8A.Личный кабинет", "8A.Попугаи",
        "9A.Бронепароходы", "9A.Майор Гром (домик)", "9A.Морти (домик)", "9A.Рик (домик)", "9A.Снайдеркат",
        "9A.ТОПИ", "9A.Я не шучу! (домик)", "10A.Твин Пикс", "10A.Sleep no more", "10A.Братья Коэн (домик)"
    ]

}




months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

days = [
    "понедельник", "вторник", "среду", "четверг",
    "пятницу", "субботу", "воскресенье"
]

def format_date_ru(date_obj):
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    date_clean = date_obj.date() if hasattr(date_obj, "date") else date_obj

    if date_clean == today:
        return "сегодня"
    elif date_clean == tomorrow:
        return "завтра"
    else:
        day_name = days[date_obj.weekday()]
        day = date_obj.day
        month = months[date_obj.month - 1]
        return f"в {day_name}, {day} {month}"


def add_time_range_dropdown(label_text_start, label_text_end, var_start, var_end):
    from datetime import time

    def create_time_selector(label_text, combo_var):
        frame = ttk.Frame(fields_frame)  # не tk.Frame, а ttk.Frame

        label = ttk.Label(frame, text=label_text, style="TLabel")
        label.pack(side="left")

        combo = ttk.Combobox(frame, state="readonly", width=10, style="Custom.TCombobox")
        combo.pack(side="left", fill="x", expand=True, padx=(5, 0))

        clear_btn = ttk.Button(frame, text="✖", width=2, command=lambda: combo.set(""))
        clear_btn.pack(side="left", padx=(5, 0))

        frame.pack(fill="x", padx=10, pady=2)

        # сохраняем сам frame для дальнейшего применения темы
        input_fields.append(frame)
        return combo


    start_combo = create_time_selector(label_text_start, var_start)
    end_combo = create_time_selector(label_text_end, var_end)

    def generate_time_slots(start_hour=8, end_hour=22):
        slots = []
        for h in range(start_hour, end_hour):
            slots.append(f"{h:02d}:00")
            slots.append(f"{h:02d}:30")
        return slots

    all_slots = generate_time_slots()
    start_combo["values"] = all_slots

    def update_end_times(event=None):
        selected = start_combo.get()
        if selected:
            h, m = map(int, selected.split(":"))
            idx = all_slots.index(f"{h:02d}:{m:02d}")
            end_combo["values"] = all_slots[idx + 1:]
            if end_combo.get() not in end_combo["values"]:
                end_combo.set("")

    start_combo.bind("<<ComboboxSelected>>", update_end_times)

    for widget in (start_combo, end_combo):
        widget.bind("<Button-1>", lambda e, w=widget: w.event_generate('<Down>'))
        input_fields.append(widget)
        widget.bind("<Return>", lambda e, w=widget: focus_next(e, w))

    fields[var_start] = start_combo
    fields[var_end] = end_combo




root = tk.Tk()
root.title("Генератор шаблонов встреч")
root.configure(bg="white")



themes = {
    "Светлая": {
        "bg": "white",
        "fg": "black",
        "entry_bg": "white",
        "entry_fg": "black",
        "highlight": "#fff8d4"
    },
    "Тёмная": {
        "bg": "#1e1e1e",
        "fg": "#f2f2f2",
        "entry_bg": "#2e2e2e",
        "entry_fg": "#f5f5f5",
        "highlight": "#573c3c"
    },
    "Гёрли-пак": {
        "bg": "#fff0f5",  # лаванда
        "fg": "#8b008b",  # тёмно-фиолетовый
        "entry_bg": "#ffe4f3",
        "entry_fg": "#8b008b",
        "highlight": "#ffb6c1"  # светло-розовый
    },
    "Киберпанк": {
        "bg": "#0f0f1a",
        "fg": "#39ff14",  # неоново-зелёный
        "entry_bg": "#1a1a2e",
        "entry_fg": "#00fff7",  # неоново-голубой
        "highlight": "#ff00c8"  # неоново-розовый
    },
    "Минимализм": {
        "bg": "#f0f0f0",
        "fg": "#222222",
        "entry_bg": "#ffffff",
        "entry_fg": "#222222",
        "highlight": "#c7ecee"
    },
    "Ретро DOS": {
        "bg": "#000000",
        "fg": "#00ff00",  # зелёный терминал
        "entry_bg": "#000000",
        "entry_fg": "#00ff00",
        "highlight": "#005500"
    }
}


style = ttk.Style()
style.theme_use("clam")  # фиксированно, ты не переключаешь на system themes
current_theme_name = "Светлая"
theme = themes[current_theme_name]  # используется для первой инициализации



fields = {}

# === В apply_theme уже без повторного ttk.Style() ===

def apply_theme():
    style = ttk.Style()
    theme = themes[current_theme_name]
    root.configure(bg=theme["bg"])
    style.configure("Custom.TFrame", background=theme["bg"])
    frame = ttk.Frame(fields_frame, style="Custom.TFrame")
    

    # Стили для стандартных элементов
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
    style.configure("TEntry", fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])
    style.configure("TButton", background=theme["entry_bg"], foreground=theme["entry_fg"])
    style.configure("Error.TEntry", fieldbackground=theme["highlight"], foreground=theme["fg"])
    style.configure("Error.TCombobox", fieldbackground=theme["highlight"], foreground=theme["fg"])

    # Кастомные стили
    style.configure("Custom.TCombobox",
                    padding=3,
                    foreground=theme["entry_fg"],
                    background=theme["entry_bg"],
                    fieldbackground=theme["entry_bg"],
                    borderwidth=1,
                    relief="solid")
    
    style.configure("Custom.TButton",
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        borderwidth=1,
        focusthickness=1,
        focuscolor=theme["highlight"])

    style.map("Custom.TButton",
        background=[("active", theme["highlight"])],
        foreground=[("active", theme["fg"])])
  

    style.configure("Custom.DateEntry",
                    fieldbackground=theme["entry_bg"],
                    background=theme["entry_bg"],
                    foreground=theme["entry_fg"])
    style.configure("Custom.TFrame", background=theme["bg"])

    style.map("Custom.TCombobox",
        # было
        fieldbackground=[
            ("readonly", theme["entry_bg"]),
            # 👇 добавляем
            ("!readonly", theme["entry_bg"])
        ],
        background=[
            ("readonly", theme["entry_bg"]),
            ("!readonly", theme["entry_bg"])
        ],
        foreground=[
            ("readonly", theme["entry_fg"]),
            ("!readonly", theme["entry_fg"])
        ],
        selectforeground=[("readonly", theme["entry_fg"])],
        selectbackground=[("readonly", theme["entry_bg"])]
    )




    # Применяем стили к каждому виджету
    for widget in input_fields:
        if not widget.winfo_exists():
            continue  # Пропустить мёртвые виджеты

        try:
            widget.configure(background=theme["entry_bg"], foreground=theme["entry_fg"])
        except:
            pass

        # Только внутри этого цикла можно обращаться к widget
        if isinstance(widget, AutocompleteCombobox):
            widget.configure(style="Custom.TCombobox")
        elif isinstance(widget, ttk.Combobox):
            widget.configure(style="Custom.TCombobox")
        elif widget.winfo_class() == "DateEntry":
            widget.configure(style="Custom.DateEntry")
        elif isinstance(widget, ttk.Frame):
            widget.configure(style="Custom.TFrame")

    # Настройка output_text
    output_text.configure(bg=theme["entry_bg"],
                          fg=theme["entry_fg"],
                          insertbackground=theme["fg"])
   





selected_theme = tk.StringVar(value=current_theme_name)

def apply_theme_from_dropdown(*_):
    global current_theme_name
    current_theme_name = selected_theme.get()
    apply_theme()

theme_selector = ttk.Combobox(root, textvariable=selected_theme, values=list(themes.keys()), state="readonly", style="Custom.TCombobox")
theme_selector.pack(pady=(0, 5))
theme_selector.bind("<<ComboboxSelected>>", apply_theme_from_dropdown)


def clear_frame():
    for widget in fields_frame.winfo_children():
        widget.destroy()
    fields.clear()

def add_date_field(label_text, var_name):
    from tkcalendar import DateEntry

    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    date_entry = DateEntry(fields_frame, date_pattern='dd.mm.yyyy', style="Custom.DateEntry", locale='ru_RU')
    date_entry.pack(fill="x", padx=10, pady=2)

    def show_calendar(event):
        try:
            # Координаты относительно экрана
            x = date_entry.winfo_rootx()
            y = date_entry.winfo_rooty() + date_entry.winfo_height()
            date_entry._top_cal.geometry(f"+{x}+{y}")
            date_entry._top_cal.deiconify()
        except Exception:
            date_entry.event_generate('<Down>')

    date_entry.bind("<Button-1>", show_calendar)

    fields[var_name] = date_entry
    input_fields.append(date_entry)

    def focus_next(event, current=date_entry):
        i = input_fields.index(current)
        if i + 1 < len(input_fields):
            input_fields[i + 1].focus_set()
        return "break"

    date_entry.bind("<Return>", focus_next)


def focus_next(event, current):
    i = input_fields.index(current)
    if i + 1 < len(input_fields):
        input_fields[i + 1].focus_set()
    return "break"


def add_meeting_room_field(label_bz, label_room, var_bz, var_room, rooms_data):
    # Label для БЦ
    ttk.Label(fields_frame, text=label_bz, style="TLabel").pack(anchor="w", padx=10)
    bz_combo = ttk.Combobox(fields_frame, values=list(rooms_data.keys()), state="readonly", style="Custom.TCombobox")
    bz_combo.pack(fill="x", padx=10, pady=2)

    # Label для переговорки
    ttk.Label(fields_frame, text=label_room, style="TLabel").pack(anchor="w", padx=10)
    room_var = tk.StringVar()
    room_combo = ttk.Combobox(fields_frame, textvariable=room_var, style="Custom.TCombobox")
    room_combo.pack(fill="x", padx=10, pady=2)

    def update_room_options(event=None):
        selected_bz = bz_combo.get()
        room_list = rooms_data.get(selected_bz, [])
        room_combo["values"] = room_list
        room_combo.set("")  # сброс

    def filter_rooms(*args):
        selected_bz = bz_combo.get()
        all_rooms = rooms_data.get(selected_bz, [])
        input_val = room_var.get().lower()
        filtered = [r for r in all_rooms if input_val in r.lower()]
        room_combo["values"] = filtered if filtered else all_rooms

    bz_combo.bind("<<ComboboxSelected>>", update_room_options)
    room_var.trace_add("write", filter_rooms)

    def auto_dropdown(combo):
    # Запускаем через after — безопасно и без багов
        combo.after(10, lambda: combo.event_generate('<Down>'))

    for widget in [bz_combo, room_combo]:
        widget.bind("<ButtonRelease-1>", lambda e, w=widget: auto_dropdown(w))
        input_fields.append(widget)
        widget.bind("<Return>", lambda e, w=widget: focus_next(e, w))


    fields[var_bz] = bz_combo
    fields[var_room] = room_combo

def add_smart_filter_field(label_text, var_name, bz_var_name):
    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    
    var = tk.StringVar()
    combo = AutocompleteCombobox(fields_frame, textvariable=var)
    combo.pack(fill="x", padx=10, pady=2)

    def update_rooms(*_):
        current_bz = fields[bz_var_name].get()
        full_list = rooms_by_bz.get(current_bz, [])
        combo.set_completion_list(full_list)
        combo.set("")  # очистим поле
        combo.focus_set()

    fields[bz_var_name].bind("<<ComboboxSelected>>", update_rooms)
    combo.bind("<Return>", lambda e: combo.tk_focusNext().focus())  # переход дальше
    combo.bind("<Tab>", lambda e: combo.tk_focusNext().focus())
    
    fields[var_name] = combo
    input_fields.append(combo)


def validate_fields(required_keys):
    valid = True
    for key in required_keys:
        widget = fields.get(key)
        value = widget.get().strip()

        # Вернём стиль по умолчанию
        if isinstance(widget, ttk.Combobox):
            widget.configure(style="Custom.TCombobox")   # наш базовый стиль
        else:
            widget.configure(style="TEntry")

        # Удалим старую ошибку, если есть
        if hasattr(widget, 'error_label'):
            widget.error_label.destroy()

        # Если пустое поле — подсветим
        if not value:
            valid = False
            style_name = "Error.TCombobox" if isinstance(widget, ttk.Combobox) else "Error.TEntry"
            widget.configure(style=style_name)

            # Надпись под полем
            err_label = ttk.Label(fields_frame, text="Поле обязательно", foreground="red", background="#eeeeee", font=("Arial", 8))
            err_label.pack(after=widget, anchor="w", padx=10)
            widget.error_label = err_label
    return valid





input_fields = []

def add_dropdown_field(label_text, var_name, values):
    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    combo = ttk.Combobox(fields_frame, values=values, state="readonly", style="Custom.TCombobox")
    combo.pack(fill="x", padx=10, pady=2)
    combo.bind("<Button-1>", lambda e: combo.event_generate('<Down>'))
    fields[var_name] = combo
    input_fields.append(combo)

    def focus_next(event, current=combo):
        i = input_fields.index(current)
        if i + 1 < len(input_fields):
            input_fields[i + 1].focus_set()
        return "break"

    combo.bind("<Return>", focus_next)


def add_field(label_text, var_name):
    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    entry = ttk.Entry(fields_frame)
    entry.pack(fill="x", padx=10, pady=2)

    enable_ctrl_v(entry)  # поддержка Ctrl+V
    fields[var_name] = entry
    input_fields.append(entry)

    def focus_next(event, current=entry):
        i = input_fields.index(current)
        if i + 1 < len(input_fields):
            input_fields[i + 1].focus_set()
        return "break"

    entry.bind("<Return>", focus_next)

def parse_yandex_calendar_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    event_date = query.get("event_date", [""])[0]  # Пример: 2025-05-31T14:00:00

    if not event_date:
        return None, None

    try:
        # Не трогаем никакие .astimezone()
        dt = datetime.fromisoformat(event_date)
        date_str = dt.strftime("%d.%m.%Y")
        time_str = dt.strftime("%H:%M")
        return date_str, time_str
    except Exception as e:
        print("Ошибка парсинга даты:", e)
        return None, None


def add_name_field_with_asya(label_text="Имя:", var_name="name"):
    ttk.Label(fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)

    name_var = tk.StringVar()

    frame = ttk.Frame(fields_frame, style="Custom.TFrame")
    frame.pack(fill="x", padx=10, pady=2)

    name_var = tk.StringVar()
    name_entry = ttk.Entry(frame, textvariable=name_var, style="TEntry")
    name_entry.pack(side="left", fill="x", expand=True)

    # Кнопка "Ася +"
    asya_check = ttk.Checkbutton(frame, text="Ася +", variable=asya_mode, style="TCheckbutton")
    asya_check.pack(side="left", padx=(5, 0))

    fields["name"] = name_entry
    input_fields.append(name_entry)
    input_fields.append(asya_check)

    def focus_next(event):
        name_entry.tk_focusNext().focus()
        return "break"

    name_entry.bind("<Return>", focus_next)
    enable_ctrl_v(name_entry)



def generate_message():
    typ = type_var.get()
    field_values = {k: v.get().strip() for k, v in fields.items()}
    start = field_values.get("start_time", "").strip()
    end = field_values.get("end_time", "").strip()

    if typ == "Обмен":
        required_keys = ["name", "his_room", "my_room"]
    elif typ == "Актуализация":
        required_keys = ["name", "room"]
    elif typ == "Разовая встреча":
        required_keys = ["name", "meeting_name", "duration", "client_name"]
    else:
        required_keys = []

    if not validate_fields(required_keys):
        return

    if start and end:
        time_part = f", в {start} — {end}"
    elif start:
        time_part = f", в {start}"
    else:
        time_part = ""

    name = field_values.get("name", "")
    raw_date = fields["datetime"].get_date()
    formatted = format_date_ru(raw_date)
    link = field_values.get("link", "")
    link_part = f" ({link})" if link else ""

    asya_on = asya_mode.get()
    custom_asya_on = is_custom_asya.get()

    if custom_asya_on:
        asya_name = asya_name_var.get().strip() or "Ася"
        gender = asya_gender_var.get().strip().lower()
        greeting = f"Привет, {name}! Я {asya_name}, ассистент. Приятно познакомиться!"
        gender_word1 = "признателен" if gender == "мужской" else "признательна"
        gender_word2 = "сам" if gender == "мужской" else "сама"
    elif asya_on:
        greeting = f"Привет, {name}! Я Ася, ассистент. Приятно познакомиться!"
        gender_word1 = "признательна"
        gender_word2 = "сама"
    else:
        greeting = f"Привет, {name}!"
        gender_word1 = "признательна"
        gender_word2 = "сама"

    if typ == "Актуализация":
        room = field_values.get("room", "")
        regular = field_values.get("regular", "")
        is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
        share_word = "разово поделиться" if regular.lower() == "регулярная" else "поделиться"

        msg = f"""{greeting}

У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {room}.

Уточни, пожалуйста, сможешь ли {share_word} переговорной?
Буду очень {gender_word1}!

Если сможешь, то сделаю всё {gender_word2}. Только не удаляй её из встречи, чтобы не потерять :)"""

    elif typ == "Обмен":
        his_room = field_values.get("his_room", "")
        my_room = field_values.get("my_room", "")
        regular = field_values.get("regular", "")
        is_regular = "регулярная встреча" if regular.lower() == "регулярная" else "встреча"
        share_word = "разово обменяться" if regular.lower() == "регулярная" else "обменяться"

        msg = f"""{greeting}

У тебя {formatted}{time_part} состоится {is_regular}{link_part} в переговорной {his_room}.

Уточни, пожалуйста, сможем ли {share_word} на {my_room}?
Буду тебе очень {gender_word1}!

Если сможем, то я всё сделаю {gender_word2} :)"""

    elif typ == "Разовая встреча":
        meeting_name = field_values.get("meeting_name", "")
        duration = field_values.get("duration", "")
        raw_date = fields["datetime"].get_date()
        formatted = format_date_ru(raw_date)
        client_name = field_values.get("client_name", "")
        first_name = client_name.split()[0] if client_name else "клиент"

        conflict_links = [
            field_values.get("conflict1", "").strip(),
            field_values.get("conflict2", "").strip(),
            field_values.get("conflict3", "").strip(),
        ]
        conflict_links = [c for c in conflict_links if c]

        if len(conflict_links) == 0:
            conflict_text = ""
            plural = False
        elif len(conflict_links) == 1:
            conflict_text = f"У тебя образуется пересечение с этой встречей: {conflict_links[0]}"
            plural = False
        else:
            lines = "\n".join(f"{i+1}) {c}" for i, c in enumerate(conflict_links))
            conflict_text = "У тебя образуются пересечения с несколькими встречами:\n" + lines
            plural = True

        single_variants = [
            f"Уточни, пожалуйста, получится ли перенести свою встречу и быть на встрече {first_name} в это время?",
            f"Сможешь ли освободить это время и присоединиться к встрече {first_name}?",
            f"Есть возможность освободить слот и поучаствовать во встрече {first_name}?",
            f"Получится ли освободить время и присутствовать на встрече {first_name}?",
            f"Дай знать, если сможешь подвинуть свою встречу и быть у {first_name}.",
            f"Будет супер, если найдёшь возможность быть на встрече {first_name}."
        ]

        multi_variants = [
            f"Сможешь ли освободить это время и быть на встрече {first_name}?",
            f"Есть шанс, что удастся разрулить пересечения и поучаствовать во встрече {first_name}?",
            f"Сможешь ли освободиться и поучаствовать во встрече у {first_name}?",
            f"Если появится свободное окно — очень выручишь, если подключишься к встрече {first_name}.",
            f"Понимаю, что пересечений много — но если удастся выкроить время на встречу {first_name}, это будет огонь."
        ]

        conclusion = random.choice(multi_variants if plural else single_variants)

        msg = f"""{greeting}

Подбираю оптимальное время для проведения встречи {client_name} «{meeting_name}»{link_part} продолжительностью в {duration}.

Сейчас она стоит {formatted}{time_part}

{conflict_text}

{conclusion}"""

    else:
        msg = "Тип встречи не выбран"

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, msg)


def update_fields(*args):
    clear_frame()
    typ = type_var.get()
    

    if typ == "Актуализация":
        add_name_field_with_asya("Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link")
        add_date_field("Дата (выбери в календаре):", "datetime")
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time")
        add_dropdown_field("БЦ:", "bz", list(rooms_by_bz.keys()))
        add_smart_filter_field("Переговорка:", "room", "bz")
        add_dropdown_field("Тип встречи (Обычная/Регулярная):", "regular", ["Обычная", "Регулярная"])

    elif typ == "Обмен":
        add_name_field_with_asya("Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link")
        add_date_field("Дата (выбери в календаре):", "datetime")
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time")

        # Один выпадающий список для БЦ
        add_dropdown_field("БЦ:", "bz", list(rooms_by_bz.keys()))

        # Добавляем оба поля переговорок (his_room и my_room)
        add_smart_filter_field("Его переговорка:", "his_room", "bz")
        add_smart_filter_field("Твоя переговорка:", "my_room", "bz")

        # Обновлять оба списка при смене БЦ
        def update_all_rooms(*_):
            current_bz = fields["bz"].get()
            full_list = rooms_by_bz.get(current_bz, [])
            fields["his_room"].set_completion_list(full_list)
            fields["his_room"].set("")
            fields["my_room"].set_completion_list(full_list)
            fields["my_room"].set("")

        fields["bz"].bind("<<ComboboxSelected>>", update_all_rooms)
        update_all_rooms()


        add_dropdown_field("Тип встречи (Обычная/Регулярная):", "regular", ["Обычная", "Регулярная"])

    elif typ == "Разовая встреча":
        add_name_field_with_asya("Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link")
        add_field("Название встречи:", "meeting_name")
        add_field("Продолжительность встречи (например: 30 минут, 1 час, полтора часа):", "duration")
        add_date_field("Предварительная дата, на которую поставилена встреча:", "datetime")
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time")
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 1:", "conflict1")
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 2 (необязательно):", "conflict2")
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 3 (необязательно):", "conflict3")
        add_field("Имя и фамилия заказчика в родительном падеже (например: Андрея Романовского):", "client_name")
    
    apply_theme()





type_var = tk.StringVar()
type_var.trace_add("write", update_fields)
link_var = tk.StringVar()
asya_mode = tk.BooleanVar(value=False)



asya_extra_frame = ttk.Frame(root, style="Custom.TFrame")

ttk.Label(asya_extra_frame, text="Твоё имя (ассистент):", style="TLabel").pack(anchor="w")
asya_name_var = tk.StringVar()
asya_name_entry = ttk.Entry(asya_extra_frame, textvariable=asya_name_var, style="TEntry")
asya_name_entry.pack(fill="x", pady=2)

ttk.Label(asya_extra_frame, text="Пол:", style="TLabel").pack(anchor="w")
asya_gender_var = tk.StringVar()
asya_gender_combo = ttk.Combobox(asya_extra_frame, values=["женский", "мужской"], state="readonly", textvariable=asya_gender_var, style="Custom.TCombobox")
asya_gender_combo.pack(fill="x", pady=2)

is_custom_asya = tk.BooleanVar(value=False)

def toggle_custom_asya():
    if is_custom_asya.get():
        asya_extra_frame.pack(fill="x", padx=10, pady=(0, 5))
    else:
        asya_extra_frame.pack_forget()

lsa_button = ttk.Checkbutton(root, text="ЛС", variable=is_custom_asya, command=toggle_custom_asya, style="TCheckbutton")
lsa_button.pack(anchor="e", padx=10)




def on_link_change(*args):

    # === ⛔️ Новое условие: если дата и время уже заданы — ничего не меняем
    if fields.get("datetime") and fields["datetime"].get() and fields["start_time"].get() and fields["end_time"].get():
        print("[INFO] Дата и время уже заданы вручную — ничего не меняем")
        return

    url = link_var.get()
    date_str, time_str = parse_yandex_calendar_url(url)

    if date_str and time_str:
        try:
            fields["datetime"].set_date(datetime.strptime(date_str, "%d.%m.%Y"))
        except Exception as e:
            print("Ошибка при установке даты:", e)

        try:
            # 👉 Добавляем +3 часа к времени
            h, m = map(int, time_str.split(":"))
            h = (h + 3) % 24  # чтобы не вывалиться за 23
            adjusted_time = f"{h:02d}:{m:02d}"

            # Установим время начала
            fields["start_time"].set(adjusted_time)

            # Вычисляем список всех слотов
            all_slots = [f"{h_:02d}:{m_:02d}" for h_ in range(8, 22) for m_ in (0, 30)]

            # Парсим сдвинутое время
            if adjusted_time in all_slots:
                idx = all_slots.index(adjusted_time)
                available_ends = all_slots[idx + 1:]
            else:
                available_ends = []
                idx = -1  # фиктивное значение

            # Обновляем доступные значения для окончания
            fields["end_time"]["values"] = available_ends

            # 👉 Автоподстановка +1 час, если в списке доступно
            if idx != -1 and idx + 1 < len(all_slots):
                fields["end_time"].set(all_slots[idx + 1])  # +1 час (2 слота по 30 минут)
            elif available_ends:
                fields["end_time"].set(available_ends[0])   # если 1 слот доступен — его
            else:
                fields["end_time"].set("")  # fallback

        except Exception as e:
            print("Ошибка при установке времени:", e)




link_var.trace_add("write", on_link_change)


# === сам комбо «Тип встречи» ===
ttk.Label(root, text="Тип встречи:", style="TLabel").pack(anchor="w", padx=10, pady=(10, 0))
type_combo = ttk.Combobox(root,
                          textvariable=type_var,
                          values=["Актуализация", "Обмен", "Разовая встреча"],
                          state="readonly",
                          style="Custom.TCombobox")
type_combo.pack(fill="x", padx=10)
type_combo.bind("<Button-1>", lambda e: type_combo.event_generate('<Down>'))



fields_frame = ttk.Frame(root, style="Custom.TFrame")
fields_frame.pack(fill="x", expand=True, padx=10, pady=10)



def copy_generated_text():
    text = output_text.get("1.0", tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)

generate_button = ttk.Button(root, text="Сгенерировать сообщение", command=generate_message)
copy_button = ttk.Button(root, text="Скопировать текст", command=copy_generated_text)
music_button = ttk.Button(root, text="🎵", width=3, command=toggle_music, style="Custom.TButton")
music_button.pack(anchor="ne", padx=10, pady=(0, 5))


clipboard_button = ttk.Button(root, text="📋 Из буфера", command=import_from_clipboard_image, style="Custom.TButton")
clipboard_button.pack(anchor="e", padx=10, pady=(0, 5))
input_fields.append(clipboard_button)



generate_button.pack(pady=(5, 2))
copy_button.pack(pady=(0, 10))

output_frame = tk.Frame(root, bg=theme["bg"])
output_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

output_text = tk.Text(output_frame,
                      height=14,
                      wrap="word",
                      bg=theme["entry_bg"],
                      fg=theme["entry_fg"],
                      insertbackground=theme["fg"],
                      highlightthickness=0,
                      bd=0,
                      relief="flat")
output_text.pack(fill="both", expand=True)


translate_button = ttk.Button(output_frame,
                              text="EN",
                              width=3,
                              command=translate_to_english,
                              style="Custom.TButton")

translate_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)  # ⬅ вот оно, бля!



root.bind("<Control-Return>", lambda e: generate_message())
root.bind("<Control-Shift-C>", lambda e: copy_generated_text())
root.bind("<Control-e>", lambda e: translate_to_english())



def enable_ctrl_c(widget):
    def copy_selection(event=None):
        try:
            selected = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            root.clipboard_clear()
            root.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def on_ctrl_keypress(event):
        if event.state & 0x4:  # Ctrl
            if event.keycode == 67:  # физическая клавиша C/С
                return copy_selection()

    widget.bind("<Control-KeyPress>", on_ctrl_keypress)
    widget.bind("<Command-c>", copy_selection)

    # ПКМ → Копировать
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Копировать", command=copy_selection)

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    widget.bind("<Button-3>", show_menu)

# применяем к output_text
enable_ctrl_c(output_text)

def enable_ctrl_v(widget):
    def paste_clipboard(event=None):
        try:
            widget.insert(tk.INSERT, root.clipboard_get())
        except:
            pass
        return "break"

    def on_ctrl_keypress(event):
        # проверяем keycode клавиши V/М (физически это одна клавиша, обычно 86)
        if event.state & 0x4:  # Ctrl is pressed
            if event.keycode == 86:  # V/М physical key
                return paste_clipboard()

    widget.bind("<Control-KeyPress>", on_ctrl_keypress)
    widget.bind("<Command-v>", paste_clipboard)



root.mainloop()