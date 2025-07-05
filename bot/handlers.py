from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from .session import SessionStorage
from .utils import (
    process_image,
    build_actualization_message,
    build_exchange_message,
    build_report,
)

router = Router()

sessions = SessionStorage()

theme_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Актуализация"),
            KeyboardButton(text="Обмен"),
        ],
        [
            KeyboardButton(text="Организация встречи"),
            KeyboardButton(text="Другое"),
        ],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    sessions.reset(message.from_user.id)
    await message.answer(
        "Выбери тему:", reply_markup=theme_keyboard
    )


@router.message(Command("auto"))
async def toggle_auto(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    if session.auto_enabled or session.awaiting_auto_login or session.awaiting_auto_tg:
        session.auto_enabled = False
        session.awaiting_auto_login = False
        session.awaiting_auto_tg = False
        await message.answer("Автоотчёты выключены")
    else:
        session.auto_enabled = True
        await message.answer("Автоотчёты включены")


@router.message(lambda m: sessions.get(m.from_user.id).awaiting_auto_login and m.text)
async def set_auto_login(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.organizer_login = message.text.strip().lstrip("@")
    session.awaiting_auto_login = False
    session.awaiting_auto_tg = True
    await message.answer("Введите ссылку на Telegram организатора")


@router.message(lambda m: sessions.get(m.from_user.id).awaiting_auto_tg and m.text)
async def set_auto_tg(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.organizer_tg = message.text.strip()
    session.awaiting_auto_tg = False
    if session.main_message_id:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="Написать организатору", url=session.organizer_tg)
            ]]
        )
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=session.main_message_id,
                reply_markup=markup,
            )
        except Exception:
            pass
    if session.pending_fields:
        report = build_report(session.pending_fields, session.pending_type, session)
        await message.answer(report, parse_mode=None)
        sessions.reset(message.from_user.id)
    else:
        await message.answer("Сохранено")


@router.message(lambda m: m.text in {"Актуализация", "Обмен", "Организация встречи", "Другое"})
async def theme_selected(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.theme = message.text
    session.my_room = None
    session.awaiting_my_room = False
    session.meeting_link = None
    session.awaiting_link = True
    await message.answer("Вставьте ссылку на встречу")


@router.message(lambda m: sessions.get(m.from_user.id).awaiting_link and m.text)
async def set_meeting_link(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.meeting_link = message.text.strip()
    session.awaiting_link = False
    if session.theme == "Обмен":
        session.awaiting_my_room = True
        await message.answer("Введите название вашей переговорки")
    else:
        await message.answer("Теперь отправь скриншот")


@router.message(lambda m: sessions.get(m.from_user.id).awaiting_my_room and m.text)
async def set_my_room(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.my_room = message.text.strip()
    session.awaiting_my_room = False
    await message.answer("Отлично! Теперь отправь скриншот")


@router.message(lambda m: m.photo or m.document)
async def handle_image(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    if not session.theme:
        await message.answer("Сначала выбери тему, братан \uD83D\uDE0E")
        return
    if session.awaiting_link:
        await message.answer("Сначала отправь ссылку на встречу")
        return
    if session.theme == "Обмен" and session.awaiting_my_room:
        await message.answer("Сначала отправь название своей переговорки")
        return
    file = message.photo[-1] if message.photo else message.document
    file_bytes = await message.bot.download(file.file_id)
    data = file_bytes.getvalue()
    fields, meeting_type = await process_image(data)
    session.pending_fields = fields
    session.pending_type = meeting_type
    session.awaiting_mode = True
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ася", callback_data="mode_asya"),
            InlineKeyboardButton(text="Личное сообщение", callback_data="mode_ls"),
        ]]
    )
    await message.answer("Выберите стиль сообщения:", reply_markup=markup)


@router.callback_query(lambda c: c.data in {"mode_asya", "mode_ls"})
async def choose_mode(callback: types.CallbackQuery) -> None:
    await callback.answer()
    session = sessions.get(callback.from_user.id)
    if not session.pending_fields:
        await callback.message.answer("Данные не найдены, отправь скриншот заново")
        return
    asya = callback.data == "mode_asya"
    speaker_name = None
    speaker_gender = None
    if not asya:
        if session.user_gender is None:
            session.awaiting_gender = True
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="Мужской", callback_data="gender_m"),
                    InlineKeyboardButton(text="Женский", callback_data="gender_f"),
                ]]
            )
            await callback.message.answer(
                "Выберите свой пол:", reply_markup=markup
            )
            return
        speaker_name = callback.from_user.first_name
        speaker_gender = session.user_gender
    fields = session.pending_fields
    meeting_type = session.pending_type
    if session.theme == "Актуализация":
        text = build_actualization_message(
            fields,
            meeting_type,
            session.meeting_link,
            speaker_name,
            speaker_gender,
        )
    elif session.theme == "Обмен":
        text = build_exchange_message(
            fields,
            meeting_type,
            session.my_room or "",
            session.meeting_link,
            speaker_name,
            speaker_gender,
        )
    else:
        text = "Эта тема пока не поддерживается"
    sent = await callback.message.answer(text, parse_mode="Markdown")
    session.main_message_id = sent.message_id
    if session.auto_enabled:
        session.awaiting_auto_login = True
        await callback.message.answer("Введите логин организатора")
    else:
        sessions.reset(callback.from_user.id)


@router.callback_query(lambda c: c.data in {"gender_m", "gender_f"})
async def set_gender(callback: types.CallbackQuery) -> None:
    await callback.answer()
    session = sessions.get(callback.from_user.id)
    session.user_gender = "м" if callback.data == "gender_m" else "ж"
    session.awaiting_gender = False
    fields = session.pending_fields
    meeting_type = session.pending_type
    if not fields:
        await callback.message.answer("Данные не найдены, отправь скриншот заново")
        return
    text = build_actualization_message(
        fields,
        meeting_type,
        session.meeting_link,
        callback.from_user.first_name,
        session.user_gender,
    ) if session.theme == "Актуализация" else build_exchange_message(
        fields,
        meeting_type,
        session.my_room or "",
        session.meeting_link,
        callback.from_user.first_name,
        session.user_gender,
    )
    sent = await callback.message.answer(text, parse_mode="Markdown")
    session.main_message_id = sent.message_id
    if session.auto_enabled:
        session.awaiting_auto_login = True
        await callback.message.answer("Введите логин организатора")
    else:
        sessions.reset(callback.from_user.id)


@router.message()
async def catch_all(message: types.Message) -> None:
    await message.answer("Сначала выбери тему, братан \uD83D\uDE0E")

