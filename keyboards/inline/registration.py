from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def email_verification_inline_markup() -> InlineKeyboardMarkup:
    """Кнопки управления при подтверждении Email"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Отправить код повторно",
                    callback_data="resend_email_code",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить email",
                    callback_data="change_reg_email",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить регистрацию",
                    callback_data="cancel_registration",
                )
            ],
        ]
    )


def confirm_registration_inline_markup() -> InlineKeyboardMarkup:
    """Кнопки финального подтверждения анкеты"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Всё верно, сохранить!",
                    callback_data="reg_confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Заполнить заново",
                    callback_data="reg_restart",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_registration",
                )
            ],
        ]
    )
