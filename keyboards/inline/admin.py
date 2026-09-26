from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_panel_markup() -> InlineKeyboardMarkup:
    """Кнопки главной панели администратора"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="📥 Выгрузка в Excel", callback_data="admin_export_excel"),
            ],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="🗑 Очистить базу", callback_data="admin_cleandb_ask"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"),
            ],
        ]
    )
