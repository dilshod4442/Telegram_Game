from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню для зарегистрированного пользователя"""
    keyboard = [
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="🎮 Игры и RPG"),
        ],
        [
            KeyboardButton(text="🎁 Награда"),
            KeyboardButton(text="🧠 AI & Код"),
        ],
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="👥 Социум & Чат"),
        ],
        [
            KeyboardButton(text="📰 Новости"),
            KeyboardButton(text="📍 Моя локация"),
        ],
        [
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="📞 Поддержка"),
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="👑 Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Выберите нужный раздел в меню...",
    )


def get_unregistered_menu() -> ReplyKeyboardMarkup:
    """Меню для незарегистрированного пользователя"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Зарегистрироваться")],
            [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="📞 Поддержка")],
        ],
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Нажмите «Зарегистрироваться» для старта...",
    )
