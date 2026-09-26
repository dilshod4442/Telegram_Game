from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def news_categories_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Технологии", callback_data="news:cat:tech"),
                InlineKeyboardButton(text="🎮 Игры", callback_data="news:cat:games"),
            ],
            [
                InlineKeyboardButton(text="🐍 Python", callback_data="news:cat:python"),
                InlineKeyboardButton(text="🤖 Искусственный интеллект", callback_data="news:cat:ai"),
            ],
            [
                InlineKeyboardButton(text="🌍 В мире", callback_data="news:cat:world"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"),
            ],
        ]
    )


def news_detail_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 К категориям новостей", callback_data="news:back"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
            ],
        ]
    )
