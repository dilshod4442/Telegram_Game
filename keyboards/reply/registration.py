from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def phone_share_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки номера телефона"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить контакт", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажмите кнопку или введите номер...",
    )


def location_share_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки геопозиции"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Поделиться геопозицией", request_location=True)],
            [KeyboardButton(text="➡️ Пропустить / Ввести город")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Отправьте локацию или напишите город...",
    )


def gender_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора пола"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨 Мужской"), KeyboardButton(text="👩 Женский")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска или отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Пропустить")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура только с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите ответ или нажмите Отмена...",
    )
