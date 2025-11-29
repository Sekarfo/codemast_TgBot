import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

from app import db
from app.repository import upsert_user_and_state_on_start


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Upsert user & state in DB when /start is received
    await asyncio.to_thread(
        upsert_user_and_state_on_start,
        message.from_user.id,
        message.from_user.username,
        getattr(message.from_user, "language_code", None),
    )

    await message.answer(
        "информационный бот об экосистеме"
    )


def verify_db_connection() -> None:
    try:
        result = db.check_connection()
        print(f"Database connection OK, SELECT 1 -> {result}")
    except Exception as e:
        print(f"Database connection FAILED: {e}")
        raise


async def main():
    # Initialize DB schema (create tables) and check connectivity once at startup
    db.init_db()
    verify_db_connection()

    bot = Bot(BOT_TOKEN)
    print("bot is running")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
