import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.handlers import router

TOKEN = os.getenv("BOT_TOKEN")


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable not set")
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

