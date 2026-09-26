from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def games_main_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Бросить кубик", callback_data="game:dice"),
                InlineKeyboardButton(text="✊ Камень-Ножницы-Бумага", callback_data="game:rps"),
            ],
            [
                InlineKeyboardButton(text="❓ Викторина", callback_data="game:quiz"),
                InlineKeyboardButton(text="🪙 Орёл или Решка", callback_data="game:coinflip"),
            ],
            [
                InlineKeyboardButton(text="⚔️ RPG и Битва с Боссом", callback_data="rpg:menu"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"),
            ],
        ]
    )


def rps_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🪨 Камень", callback_data="rps:rock"),
                InlineKeyboardButton(text="✂️ Ножницы", callback_data="rps:scissors"),
                InlineKeyboardButton(text="📄 Бумага", callback_data="rps:paper"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в игры", callback_data="games:back"),
            ],
        ]
    )


def coinflip_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🦅 Орёл (Ставка 25💰)", callback_data="coin:heads"),
                InlineKeyboardButton(text="🪙 Решка (Ставка 25💰)", callback_data="coin:tails"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в игры", callback_data="games:back"),
            ],
        ]
    )


def quiz_markup(question_id: int, options: list) -> InlineKeyboardMarkup:
    buttons = []
    for idx, opt in enumerate(options):
        buttons.append([
            InlineKeyboardButton(text=opt, callback_data=f"quiz_ans:{question_id}:{idx}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад в игры", callback_data="games:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
