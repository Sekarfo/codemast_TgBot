from typing import Sequence
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="search"),
                KeyboardButton(text="chat"),
            ],
            [
                KeyboardButton(text="categories"),
                KeyboardButton(text="latest"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Choose an action",
    )


def categories_inline_keyboard(categories: Sequence) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=getattr(cat, "name", "Без названия"),
                callback_data=f"cat:{getattr(cat, 'id')}",
            )
        ]
        for cat in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_pagination_keyboard(has_next: bool) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if has_next:
        row.append(InlineKeyboardButton(text="▶️ Next", callback_data="cat_next"))
    row.append(InlineKeyboardButton(text="🏠 Menu", callback_data="menu"))
    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

