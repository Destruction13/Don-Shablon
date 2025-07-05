from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from .session import SessionStorage
from .utils import process_image, build_actualization_message, build_exchange_message

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


@router.message(lambda m: m.text in {"Актуализация", "Обмен", "Организация встречи", "Другое"})
async def theme_selected(message: types.Message) -> None:
    session = sessions.get(message.from_user.id)
    session.theme = message.text
    session.my_room = None
    session.awaiting_my_room = False
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
    if session.theme == "Обмен" and session.awaiting_my_room:
        await message.answer("Сначала отправь название своей переговорки")
        return
    file = message.photo[-1] if message.photo else message.document
    file_bytes = await message.bot.download(file.file_id)
    data = file_bytes.getvalue()
    fields, meeting_type = await process_image(data)
    if session.theme == "Актуализация":
        text = build_actualization_message(fields, meeting_type)
    elif session.theme == "Обмен":
        text = build_exchange_message(fields, meeting_type, session.my_room or "")
    else:
        text = "Эта тема пока не поддерживается"
    await message.answer(text)
    sessions.reset(message.from_user.id)


@router.message()
async def catch_all(message: types.Message) -> None:
    await message.answer("Сначала выбери тему, братан \uD83D\uDE0E")

