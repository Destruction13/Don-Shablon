from tkinter import ttk, messagebox
import tkinter as tk
from widgets import AutocompleteCombobox
from ui_state import input_fields, fields, fields_frame, link_var, asya_mode, type_var
from constants import rooms_by_bz
from ui_state import UIContext

def add_time_range_dropdown(label_text_start: str, label_text_end: str, var_start: str, var_end: str, ctx: UIContext):
    start_combo = _create_time_selector(label_text_start)
    end_combo = _create_time_selector(label_text_end)

    time_slots = _generate_time_slots()
    start_combo["values"] = time_slots

    def update_end_times(event=None):
        selected = start_combo.get()
        if selected:
            try:
                h, m = map(int, selected.split(":"))
                idx = time_slots.index(f"{h:02d}:{m:02d}")
                end_combo["values"] = time_slots[idx + 1:]
                if end_combo.get() not in end_combo["values"]:
                    end_combo.set("")
            except ValueError:
                end_combo["values"] = []

    start_combo.bind("<<ComboboxSelected>>", update_end_times)

    for widget in (start_combo, end_combo):
        _configure_combobox_behavior(widget)
        ctx.input_fields.append(widget)

    ctx.fields[var_start] = start_combo
    ctx.fields[var_end] = end_combo

def _create_time_selector(label_text: str, ctx: UIContext) -> ttk.Combobox:
    frame = ttk.Frame(ctx.fields_frame)

    label = ttk.Label(frame, text=label_text, style="TLabel")
    label.pack(side="left")

    combo = ttk.Combobox(frame, state="readonly", width=10, style="Custom.TCombobox")
    combo.pack(side="left", fill="x", expand=True, padx=(5, 0))

    clear_btn = ttk.Button(frame, text="✖", width=2, command=lambda: combo.set(""))
    clear_btn.pack(side="left", padx=(5, 0))

    frame.pack(fill="x", padx=10, pady=2)
    ctx.input_fields.append(frame)

    return combo


def _generate_time_slots(start_hour: int = 8, end_hour: int = 22) -> list[str]:
    return [f"{h:02d}:{m:02d}" for h in range(start_hour, end_hour) for m in (0, 30)]


def _configure_combobox_behavior(widget: ttk.Combobox):
    widget.bind("<Button-1>", lambda e, w=widget: w.event_generate('<Down>'))
    widget.bind("<Return>", lambda e, w=widget: focus_next(e, w))


def focus_next(event, current, ctx: UIContext):
    i = ctx.input_fields.index(current)
    if i + 1 < len(ctx.input_fields):
        ctx.input_fields[i + 1].focus_set()
    return "break"

def clear_frame(ctx: UIContext):
    for widget in ctx.fields_frame.winfo_children():
        widget.destroy()
    ctx.fields.clear()

def enable_ctrl_c(widget, root):
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

def enable_ctrl_v(widget, root):
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

def add_field(label_text, var_name, ctx: UIContext):
    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    entry = ttk.Entry(ctx.fields_frame)
    entry.pack(fill="x", padx=10, pady=2)

    enable_ctrl_v(entry)  # поддержка Ctrl+V
    ctx.fields[var_name] = entry
    ctx.input_fields.append(entry)

    def focus_next(event, current=entry):
        i = ctx.input_fields.index(current)
        if i + 1 < len(ctx.input_fields):
            ctx.input_fields[i + 1].focus_set()
        return "break"

    entry.bind("<Return>", focus_next)

def add_field_with_clear_button(label_text, var_name, ctx: UIContext):
    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)

    frame = ttk.Frame(ctx.fields_frame, style="Custom.TFrame")
    frame.pack(fill="x", padx=10, pady=2)

    entry_var = link_var if var_name == "link" else tk.StringVar()
    entry = ttk.Entry(frame, textvariable=entry_var, style="TEntry")
    entry.pack(side="left", fill="x", expand=True)

    def clear_entry():
        entry_var.set("")

    clear_btn = ttk.Button(frame, text="✖", width=2, command=clear_entry)
    clear_btn.pack(side="left", padx=(5, 0))

    ctx.fields[var_name] = entry
    ctx.input_fields.append(entry)

    def focus_next(event, current=entry):
        i = ctx.input_fields.index(current)
        if i + 1 < len(ctx.input_fields):
            ctx.input_fields[i + 1].focus_set()
        return "break"

    entry.bind("<Return>", focus_next)
    enable_ctrl_v(entry)



def add_dropdown_field(label_text, var_name, values, ctx: UIContext):
    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    combo = ttk.Combobox(ctx.fields_frame, values=values, state="readonly", style="Custom.TCombobox")
    combo.pack(fill="x", padx=10, pady=2)
    combo.bind("<Button-1>", lambda e: combo.event_generate('<Down>'))
    ctx.fields[var_name] = combo
    ctx.input_fields.append(combo)

    def focus_next(event, current=combo):
        i = ctx.input_fields.index(current)
        if i + 1 < len(ctx.input_fields):
            ctx.input_fields[i + 1].focus_set()
        return "break"

    combo.bind("<Return>", focus_next)

def add_date_field(label_text, var_name, ctx: UIContext):
    from tkcalendar import DateEntry

    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10, )
    date_entry = DateEntry(ctx.fields_frame, date_pattern='dd.mm.yyyy', style="Custom.DateEntry", locale='ru_RU')
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

    ctx.fields[var_name] = date_entry
    ctx.input_fields.append(date_entry)

    def focus_next(event, current=date_entry):
        i = ctx.input_fields.index(current)
        if i + 1 < len(ctx.input_fields):
            ctx.input_fields[i + 1].focus_set()
        return "break"

    date_entry.bind("<Return>", focus_next)
    

def add_meeting_room_field(label_bz, label_room, var_bz, var_room, rooms_data, ctx: UIContext):
    # Label для БЦ
    ttk.Label(ctx.fields_frame, text=label_bz, style="TLabel").pack(anchor="w", padx=10)
    bz_combo = ttk.Combobox(ctx.fields_frame, values=list(rooms_data.keys()), state="readonly", style="Custom.TCombobox")
    bz_combo.pack(fill="x", padx=10, pady=2)

    # Label для переговорки
    ttk.Label(ctx.fields_frame, text=label_room, style="TLabel").pack(anchor="w", padx=10)
    room_var = tk.StringVar()
    room_combo = ttk.Combobox(ctx.fields_frame, textvariable=room_var, style="Custom.TCombobox")
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
        ctx.input_fields.append(widget)
        widget.bind("<Return>", lambda e, w=widget: focus_next(e, w))


    ctx.fields[var_bz] = bz_combo
    ctx.fields[var_room] = room_combo


def add_smart_filter_field(label_text, var_name, bz_var_name, ctx: UIContext):
    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)
    
    var = tk.StringVar()
    combo = AutocompleteCombobox(ctx.fields_frame, textvariable=var)
    combo.pack(fill="x", padx=10, pady=2)

    def update_rooms(*_):
        current_bz = ctx.fields[bz_var_name].get()
        full_list = rooms_by_bz.get(current_bz, [])
        if not full_list:
            print(f"[DEBUG] Не найдена переговорка в БЦ: {current_bz}")
        combo.set_completion_list(full_list)
        combo.set("")  # очистим поле
        combo.focus_set()

    ctx.fields[bz_var_name].bind("<<ComboboxSelected>>", update_rooms)
    combo.bind("<Return>", lambda e: combo.tk_focusNext().focus())  # переход дальше
    combo.bind("<Tab>", lambda e: combo.tk_focusNext().focus())
    
    ctx.fields[var_name] = combo
    ctx.input_fields.append(combo)




def add_name_field_with_asya(ctx: UIContext, label_text="Имя:", var_name="name"):
    ttk.Label(ctx.fields_frame, text=label_text, style="TLabel").pack(anchor="w", padx=10)

    name_var = tk.StringVar()

    frame = ttk.Frame(ctx.fields_frame, style="Custom.TFrame")
    frame.pack(fill="x", padx=10, pady=2)

    name_var = tk.StringVar()
    name_entry = ttk.Entry(frame, textvariable=name_var, style="TEntry")
    name_entry.pack(side="left", fill="x", expand=True)

    # Кнопка "Ася +"
    asya_check = ttk.Checkbutton(frame, text="Ася +", variable=asya_mode, style="TCheckbutton")
    asya_check.pack(side="left", padx=(5, 0))

    ctx.fields["name"] = name_entry
    ctx.input_fields.append(name_entry)
    ctx.input_fields.append(asya_check)

    def focus_next(event):
        name_entry.tk_focusNext().focus()
        return "break"

    name_entry.bind("<Return>", focus_next)
    enable_ctrl_v(name_entry)