import asyncio
import os
from typing import List

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

import db
import keyboards
import repository
from chatbot import ask_ecosystem_bot


CATEGORY_PAGE_SIZE = 3
ITEM_SNIPPET_LIMIT = 180


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()


def _shorten(text: str, limit: int = ITEM_SNIPPET_LIMIT) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(" ", 1)[0]
    return truncated + "…"


def _format_items(items: List, start_index: int = 1, include_snippet: bool = True) -> str:
    blocks: list[str] = []
    for idx, item in enumerate(items, start=start_index):
        block = f"{idx}. {item.title}"
        if getattr(item, "source_url", None):
            block += f"\n{item.source_url}"
        snippet = ""
        if include_snippet:
            snippet = _shorten(getattr(item, "content", "") or "")
        if snippet:
            block += f"\n{snippet}"
        blocks.append(block)
    return "\n\n".join(blocks)


def _build_category_message(category_name: str, page: int, items: List) -> str:
    heading = f"Категория: {category_name}\nСтраница {page}"
    body = _format_items(
        items,
        start_index=(page - 1) * CATEGORY_PAGE_SIZE + 1,
        include_snippet=True,
    )
    if body:
        return f"{heading}\n\n{body}"
    return heading


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await asyncio.to_thread(
        repository.upsert_user_and_state_on_start,
        message.from_user.id,
        message.from_user.username,
        getattr(message.from_user, "language_code", None),
    )
    await message.answer(
        "информационный бот об экосистеме",
        reply_markup=keyboards.main_menu_keyboard(),
    )


@dp.message()
async def handle_text(message: types.Message):
    if not message.text:
        return

    text = message.text.strip()
    normalized = text.lower()

    if normalized == "search":
        await asyncio.to_thread(
            repository.set_user_state,
            message.from_user.id,
            "WAIT_QUERY",
            None,
            1,
        )
        await message.answer(
            "Enter the search text.",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    if normalized == "categories":
        categories = await asyncio.to_thread(repository.list_categories)

        await message.answer(
            "Выберите категорию:",
            reply_markup=keyboards.categories_inline_keyboard(categories),
        )
        return

    if normalized == "latest":
        items = await asyncio.to_thread(repository.get_latest_items)

        if not items:
            await message.answer(
                "Пока нет материалов.",
                reply_markup=keyboards.main_menu_keyboard(),
            )
            return

        body = _format_items(items, start_index=1, include_snippet=True)
        await message.answer(
            "Свежие материалы:\n\n" + body,
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    if normalized == "chat":
        await asyncio.to_thread(
            repository.set_user_state,
            message.from_user.id,
            "CHAT",
            None,
            1,
        )
        await message.answer(
            "Задайте вопрос об экосистеме, и я отвечу на него",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    user_state = await asyncio.to_thread(
        repository.get_user_state,
        message.from_user.id,
    )

    if user_state and user_state.state == "CHAT":
        prompt = message.text.strip()
        if not prompt:
            await message.answer("Введите вопрос об экосистеме.")
            return

        try:
            reply = await asyncio.to_thread(ask_ecosystem_bot, prompt)
        except Exception as exc:
            await message.answer(
                "Не удалось получить ответ ИИ. Попробуйте позже.",
                reply_markup=keyboards.main_menu_keyboard(),
            )
            return

        await message.answer(reply, reply_markup=keyboards.main_menu_keyboard())
        return

    if not user_state or user_state.state != "WAIT_QUERY":
        return

    query = message.text.strip()
    if not query:
        await message.answer("Введите текст для поиска.")
        return

    items = await asyncio.to_thread(repository.search_items, query)

    if not items:
        await message.answer("Ничего не найдено по вашему запросу.")
    else:
        await message.answer(_format_items(items))

    await asyncio.to_thread(
        repository.set_user_state,
        message.from_user.id,
        "SEARCH_RESULTS",
        query,
        1,
    )


@dp.callback_query()
async def handle_category_callbacks(callback: types.CallbackQuery):
    data = (callback.data or "").strip()

    if data.startswith("cat:"):
        await callback.answer()
        await _open_category(callback, data.split(":", 1)[1])
        return

    if data == "cat_next":
        await callback.answer()
        await _show_next_category_page(callback)
        return

    if data == "menu":
        await callback.answer()
        await asyncio.to_thread(
            repository.set_user_state,
            callback.from_user.id,
            "MENU",
            None,
            1,
        )
        await callback.message.answer(
            "Вернулись в главное меню.",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    await callback.answer()


async def _open_category(callback: types.CallbackQuery, raw_category_id: str) -> None:
    try:
        category_id = int(raw_category_id)
    except (TypeError, ValueError):
        await callback.message.answer("Категория не найдена.")
        return

    category = await asyncio.to_thread(repository.get_category, category_id)
    if not category:
        await callback.message.answer("Категория не найдена.")
        return

    page = 1
    items, has_next = await asyncio.to_thread(
        repository.get_category_items,
        category_id,
        page,
        CATEGORY_PAGE_SIZE,
    )

    if not items:
        await asyncio.to_thread(
            repository.set_user_state,
            callback.from_user.id,
            "MENU",
            None,
            1,
        )
        await callback.message.answer(
            "В этой категории пока нет материалов.",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    await callback.message.answer(
        _build_category_message(category.name, page, items),
        reply_markup=keyboards.category_pagination_keyboard(has_next),
    )

    await asyncio.to_thread(
        repository.set_user_state,
        callback.from_user.id,
        "CATEGORY_VIEW",
        str(category_id),
        page,
    )


async def _show_next_category_page(callback: types.CallbackQuery) -> None:
    user_state = await asyncio.to_thread(
        repository.get_user_state,
        callback.from_user.id,
    )

    if not user_state or user_state.state != "CATEGORY_VIEW":
        await callback.message.answer(
            "Откройте категорию через меню.",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    try:
        category_id = int(user_state.query_text or "0")
    except (TypeError, ValueError):
        await callback.message.answer("Не удалось определить категорию.")
        return

    category = await asyncio.to_thread(repository.get_category, category_id)
    if not category:
        await callback.message.answer("Категория не найдена.")
        return

    page = max(user_state.page or 1, 1) + 1
    items, has_next = await asyncio.to_thread(
        repository.get_category_items,
        category_id,
        page,
        CATEGORY_PAGE_SIZE,
    )

    if not items:
        await asyncio.to_thread(
            repository.set_user_state,
            callback.from_user.id,
            "MENU",
            None,
            1,
        )
        await callback.message.answer(
            "По этой категории больше материалов нет.",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    await callback.message.answer(
        _build_category_message(category.name, page, items),
        reply_markup=keyboards.category_pagination_keyboard(has_next),
    )

    await asyncio.to_thread(
        repository.set_user_state,
        callback.from_user.id,
        "CATEGORY_VIEW",
        str(category_id),
        page,
    )


def verify_db_connection() -> None:
    try:
        result = db.check_connection()
        print(f"Database connection OK, SELECT 1 -> {result}")
    except Exception as e:
        print(f"Database connection FAILED: {e}")
        raise


async def main():
    verify_db_connection()
    bot = Bot(BOT_TOKEN)
    print("bot is running")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
