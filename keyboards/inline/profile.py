from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def profile_inline_markup(lat: Optional[float] = None, lon: Optional[float] = None) -> InlineKeyboardMarkup:
    """Кнопки в просмотре профиля"""
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile"),
        ]
    ]

    if lat is not None and lon is not None:
        buttons.append([
            InlineKeyboardButton(
                text="🗺 Посмотреть на Google Maps",
                url=f"https://www.google.com/maps?q={lat},{lon}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔄 Обновить профиль", callback_data="refresh_profile"),
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_profile_menu_markup() -> InlineKeyboardMarkup:
    """Выбор поля профиля для редактирования"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Имя", callback_data="edit_field:first_name"),
                InlineKeyboardButton(text="👥 Фамилия", callback_data="edit_field:last_name"),
            ],
            [
                InlineKeyboardButton(text="📱 Номер телефона", callback_data="edit_field:phone"),
                InlineKeyboardButton(text="📧 Email", callback_data="edit_field:email"),
            ],
            [
                InlineKeyboardButton(text="🎂 Возраст", callback_data="edit_field:age"),
                InlineKeyboardButton(text="🚻 Пол", callback_data="edit_field:gender"),
            ],
            [
                InlineKeyboardButton(text="📍 Локация / Город", callback_data="edit_field:location"),
                InlineKeyboardButton(text="📝 О себе", callback_data="edit_field:bio"),
            ],
            [
                InlineKeyboardButton(text="🔙 Вернуться в профиль", callback_data="cancel_edit"),
            ],
        ]
    )
