from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def social_menu_markup(bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    anon_link = f"https://t.me/{bot_username}?start=anon_{user_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Найти анонимного собеседника", callback_data="social:anon_chat:start"),
            ],
            [
                InlineKeyboardButton(text="📨 Ссылка для анонимных вопросов", url=f"https://t.me/share/url?url={anon_link}&text=Напиши%20мне%20анонимное%20сообщение!"),
            ],
            [
                InlineKeyboardButton(text="👥 Мои друзья", callback_data="social:friends:list"),
                InlineKeyboardButton(text="➕ Добавить друга", callback_data="social:friends:add"),
            ],
            [
                InlineKeyboardButton(text="🏆 Глобальный ТОП", callback_data="social:top:xp"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"),
            ],
        ]
    )


def anon_chat_active_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏹ Завершить диалог", callback_data="social:anon_chat:stop"),
                InlineKeyboardButton(text="⏭ Следующий собеседник", callback_data="social:anon_chat:next"),
            ]
        ]
    )


def anon_search_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить поиск", callback_data="social:anon_chat:cancel_search"),
            ]
        ]
    )


def leaderboard_markup(current_cat: str = "xp") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{'⭐️ ' if current_cat == 'xp' else ''}По опыту (XP)", callback_data="social:top:xp"),
                InlineKeyboardButton(text=f"{'⭐️ ' if current_cat == 'coins' else ''}По монетам", callback_data="social:top:coins"),
            ],
            [
                InlineKeyboardButton(text=f"{'⭐️ ' if current_cat == 'wins' else ''}По победам", callback_data="social:top:wins"),
                InlineKeyboardButton(text=f"{'⭐️ ' if current_cat == 'streak' else ''}По стрику", callback_data="social:top:streak"),
            ],
            [
                InlineKeyboardButton(text="🔙 Меню социума", callback_data="social:menu"),
            ],
        ]
    )
