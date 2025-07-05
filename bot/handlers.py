from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
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
        session.awaiting_auto_login = True
        await message.answer("Введите логин организатора")


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
    session.auto_enabled = True
    await message.answer("Автоотчёты включены")


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
    if session.theme == "Актуализация":
        text = build_actualization_message(fields, meeting_type, session.meeting_link)
    elif session.theme == "Обмен":
        text = build_exchange_message(
            fields, meeting_type, session.my_room or "", session.meeting_link
        )
    else:
        text = "Эта тема пока не поддерживается"
    buttons = [
        InlineKeyboardButton(text="Скопировать шаблон", callback_data="copy"),
    ]
    if session.auto_enabled and session.organizer_tg:
        buttons.append(
            InlineKeyboardButton(text="Написать организатору", url=session.organizer_tg)
        )
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    sent = await message.answer(text, reply_markup=markup)
    if session.auto_enabled:
        report = build_report(fields, meeting_type, session)
        await message.answer(report, parse_mode=None)
    sessions.reset(message.from_user.id)


@router.callback_query(lambda c: c.data == "copy")
async def copy_template(callback: CallbackQuery) -> None:
    await callback.answer("Скопировано")
    await callback.bot.copy_message(
        chat_id=callback.message.chat.id,
        from_chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )


@router.message()
async def catch_all(message: types.Message) -> None:
    await message.answer("Сначала выбери тему, братан \uD83D\uDE0E")

