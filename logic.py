import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import random
from ui_helpers import (add_field, 
                        clear_frame, 
                        add_dropdown_field, 
                        add_date_field, 
                        add_field_with_clear_button, 
                        add_meeting_room_field, 
                        add_name_field_with_asya, 
                        add_smart_filter_field, 
                        add_time_range_dropdown)


from core.app_state import UIContext

from constants import rooms_by_bz
from utils import parse_yandex_calendar_url, format_date_ru, validate_fields


from themes import apply_theme


def generate_message(ctx: UIContext):
    """Generate a message from the input fields and display it."""
    typ = ctx.type_var.get()
    field_values = {k: v.get().strip() for k, v in ctx.fields.items()}
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

    if not validate_fields(required_keys, ctx):
        return

    if start and end:
        time_part = f", в {start} — {end}"
    elif start:
        time_part = f", в {start}"
    else:
        time_part = ""

    name = field_values.get("name", "")

    if "datetime" not in ctx.fields:
        messagebox.showerror("Ошибка", "Сначала выберите тип встречи")
        return

    raw_date = ctx.fields["datetime"].get_date()
    formatted = format_date_ru(raw_date)
    link = field_values.get("link", "")
    link_part = f" ({link})" if link else ""

    asya_on = ctx.asya_mode.get()
    custom_asya_on = ctx.is_custom_asya.get()

    if custom_asya_on:
        asya_name = ctx.asya_name_var.get().strip() or "Ася"
        gender = ctx.asya_gender_var.get().strip().lower()
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
        raw_date = ctx.fields["datetime"].get_date()
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

    ctx.output_text.delete("1.0", tk.END)
    ctx.output_text.insert(tk.END, msg)


def update_fields(*args, ctx: UIContext):
    """Rebuild the input form according to the selected meeting type."""
    clear_frame(ctx)
    typ = ctx.type_var.get()
    

    if typ == "Актуализация":
        add_name_field_with_asya(ctx, "Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link", ctx)
        add_date_field("Дата (выбери в календаре):", "datetime", ctx)
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time", ctx)
        add_dropdown_field("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)
        add_smart_filter_field("Переговорка:", "room", "bz", ctx)
        add_dropdown_field("Тип встречи (Обычная/Регулярная):", "regular", ["Обычная", "Регулярная"], ctx)

    elif typ == "Обмен":
        add_name_field_with_asya(ctx, "Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link", ctx)
        add_date_field("Дата (выбери в календаре):", "datetime", ctx)
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time", ctx)

        # Один выпадающий список для БЦ
        add_dropdown_field("БЦ:", "bz", list(rooms_by_bz.keys()), ctx)

        # Добавляем оба поля переговорок (his_room и my_room)
        add_smart_filter_field("Его переговорка:", "his_room", "bz", ctx)
        add_smart_filter_field("Твоя переговорка:", "my_room", "bz", ctx)

        # Обновлять оба списка при смене БЦ
        def update_all_rooms(*_):
            current_bz = ctx.fields["bz"].get()
            full_list = rooms_by_bz.get(current_bz, [])
            ctx.fields["his_room"].set_completion_list(full_list)
            ctx.fields["his_room"].set("")
            ctx.fields["my_room"].set_completion_list(full_list)
            ctx.fields["my_room"].set("")

        ctx.fields["bz"].bind("<<ComboboxSelected>>", update_all_rooms)
        update_all_rooms()


        add_dropdown_field("Тип встречи (Обычная/Регулярная):", "regular", ["Обычная", "Регулярная"], ctx)

    elif typ == "Разовая встреча":
        add_name_field_with_asya(ctx, "Имя:", "name")
        add_field_with_clear_button("Ссылка на встречу:", "link", ctx)
        add_field("Название встречи:", "meeting_name", ctx)
        add_field("Продолжительность встречи (например: 30 минут, 1 час, полтора часа):", "duration", ctx)
        add_date_field("Предварительная дата, на которую поставилена встреча:", "datetime", ctx)
        add_time_range_dropdown("Время начала встречи:       ", "Время окончания встречи:", "start_time", "end_time", ctx)
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 1:", "conflict1", ctx)
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 2 (необязательно):", "conflict2", ctx)
        add_field_with_clear_button("Ссылка на пересекающуюся встречу 3 (необязательно):", "conflict3", ctx)
        add_field("Имя и фамилия заказчика в родительном падеже (например: Андрея Романовского):", "client_name", ctx)
    
    apply_theme(ctx)

def on_link_change(*args, ctx: UIContext):
    """Parse date and time from a Yandex Calendar link and populate fields."""

    # === ⛔️ Новое условие: если дата и время уже заданы — ничего не меняем
    if ctx.fields.get("datetime") and ctx.fields["datetime"].get() and ctx.fields["start_time"].get() and ctx.fields["end_time"].get():
        print("[INFO] Дата и время уже заданы вручную — ничего не меняем")
        return

    url = ctx.link_var.get()
    date_str, time_str = parse_yandex_calendar_url(url)

    if date_str and time_str:
        try:
            ctx.fields["datetime"].set_date(datetime.strptime(date_str, "%d.%m.%Y"))
        except Exception as e:
            print("Ошибка при установке даты:", e)

        try:
            # 👉 Добавляем +3 часа к времени
            h, m = map(int, time_str.split(":"))
            h = (h + 3) % 24  # чтобы не вывалиться за 23
            adjusted_time = f"{h:02d}:{m:02d}"

            # Установим время начала
            ctx.fields["start_time"].set(adjusted_time)

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
            ctx.fields["end_time"]["values"] = available_ends

            # 👉 Автоподстановка +1 час, если в списке доступно
            if idx != -1 and idx + 1 < len(all_slots):
                ctx.fields["end_time"].set(all_slots[idx + 1])  # +1 час (2 слота по 30 минут)
            elif available_ends:
                ctx.fields["end_time"].set(available_ends[0])   # если 1 слот доступен — его
            else:
                ctx.fields["end_time"].set("")  # fallback

        except Exception as e:
            print("Ошибка при установке времени:", e)


def toggle_custom_asya(ctx: UIContext):
    """Show or hide additional assistant settings in a popup window."""
    if not ctx.asya_popup or ctx.custom_asya_saved:
        return

    if ctx.is_custom_asya.get():
        if ctx.asya_button:
            x = ctx.asya_button.winfo_rootx()
            y = ctx.asya_button.winfo_rooty() + ctx.asya_button.winfo_height()
            ctx.asya_popup.geometry(f"+{x}+{y}")
        ctx.asya_popup.deiconify()
    else:
        ctx.asya_popup.withdraw()


def save_custom_asya(ctx: UIContext):
    """Store assistant info and hide popup."""
    name = ctx.asya_name_var.get().strip()
    gender = ctx.asya_gender_var.get().strip()
    if not name or not gender:
        messagebox.showerror("Ошибка", "Введите имя и выберите пол")
        return
    ctx.custom_asya_saved = True
    ctx.asya_popup.withdraw()
    ctx.is_custom_asya.set(False)
    if ctx.asya_button:
        ctx.asya_button.config(state="disabled")
