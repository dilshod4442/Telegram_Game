from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def rpg_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚔️ Профиль героя", callback_data="rpg:profile"),
                InlineKeyboardButton(text="👹 Мировой Босс", callback_data="rpg:boss"),
            ],
            [
                InlineKeyboardButton(text="🎒 Инвентарь", callback_data="rpg:inventory"),
                InlineKeyboardButton(text="🏪 Магазин", callback_data="rpg:shop"),
            ],
            [
                InlineKeyboardButton(text="⚔️ Найти бой (PvP)", callback_data="rpg:pvp_search"),
                InlineKeyboardButton(text="🏆 Топ игроков", callback_data="social:top:xp"),
            ],
            [
                InlineKeyboardButton(text="🔙 В игры", callback_data="games:back"),
            ],
        ]
    )


def boss_battle_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚔️ Атаковать Босса!", callback_data="rpg:attack_boss"),
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить статус", callback_data="rpg:boss"),
                InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu"),
            ],
        ]
    )


def shop_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗡 Железный меч (+10 ATK) — 150💰", callback_data="shop:buy:sword_iron:150"),
            ],
            [
                InlineKeyboardButton(text="🛡 Стальной щит (+8 DEF) — 200💰", callback_data="shop:buy:shield_steel:200"),
            ],
            [
                InlineKeyboardButton(text="🧪 Зелье здоровья (+50 HP) — 50💰", callback_data="shop:buy:health_potion:50"),
            ],
            [
                InlineKeyboardButton(text="💎 Алмаз удачи — 300💰", callback_data="shop:buy:diamond:300"),
            ],
            [
                InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu"),
            ],
        ]
    )


def inventory_markup(items: list) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"✨ Использовать {item['item_name']} (x{item['quantity']})",
                callback_data=f"rpg:use:{item['item_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
