import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

from loader import db
from keyboards.inline.rpg import (
    rpg_menu_markup,
    boss_battle_markup,
    shop_markup,
    inventory_markup,
)

router = Router()


def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    fraction = min(1.0, max(0.0, current / total))
    filled = int(fraction * length)
    return "█" * filled + "░" * (length - filled)


@router.message(Command("rpg"))
@router.callback_query(F.data == "rpg:menu")
async def show_rpg_menu(event: types.Message | types.CallbackQuery):
    text = (
        "⚔️ <b>RPG Королевство и Приключения</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Сражайтесь плечом к плечу с другими игроками против Мирового Босса, "
        "покупайте снаряжение в магазине и бросайте вызов в PvP!\n\n"
        "• <b>⚔️ Профиль героя</b> — ваши характеристики (HP, Атака, Защита)\n"
        "• <b>👹 Мировой Босс</b> — общий рейд для всех игроков\n"
        "• <b>🎒 Инвентарь</b> — используйте зелья и снаряжение\n"
        "• <b>🏪 Магазин</b> — покупайте мечи, щиты и артефакты\n"
        "• <b>⚔️ PvP</b> — сражения между игроками\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=rpg_menu_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=rpg_menu_markup(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=rpg_menu_markup(), parse_mode=ParseMode.HTML)


# =========================================================================
#  ПРОФИЛЬ ГЕРОЯ
# =========================================================================

@router.callback_query(F.data == "rpg:profile")
async def show_hero_profile(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await call.answer("Профиль не найден.", show_alert=True)
        return

    level = user.get("level", 1)
    xp = user.get("xp", 0)
    coins = user.get("coins", 0)
    hp = user.get("hp", 100)
    max_hp = user.get("max_hp", 100)
    attack = user.get("attack", 15)
    defense = user.get("defense", 10)

    xp_next_level = level * 100
    current_level_xp = xp % 100
    bar_xp = make_progress_bar(current_level_xp, 100)
    bar_hp = make_progress_bar(hp, max_hp)

    text = (
        f"⚔️ <b>Профиль Героя: {call.from_user.first_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐️ <b>Уровень (Level):</b> {level}\n"
        f"✨ <b>Опыт (XP):</b> {xp} / {xp_next_level}\n"
        f"Прогресс: <code>[{bar_xp}]</code> {current_level_xp}%\n\n"
        f"❤️ <b>Здоровье (HP):</b> {hp} / {max_hp}\n"
        f"Шкала HP: <code>[{bar_hp}]</code>\n\n"
        f"🗡 <b>Атака (Attack):</b> {attack}\n"
        f"🛡 <b>Защита (Defense):</b> {defense}\n"
        f"💰 <b>Монеты:</b> {coins} coins\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Повышайте уровень в битвах и мини-играх, чтобы усиливать характеристики!</i>"
    )

    buttons = [[types.InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu")]]
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  МИРОВОЙ БОСС (WORLD BOSS)
# =========================================================================

@router.callback_query(F.data == "rpg:boss")
async def show_world_boss(call: types.CallbackQuery):
    boss = await db.get_world_boss()
    hp_bar = make_progress_bar(boss["current_hp"], boss["max_hp"])
    pct = int((boss["current_hp"] / boss["max_hp"]) * 100) if boss["max_hp"] > 0 else 0

    text = (
        f"👹 <b>Мировой Рейдовый Босс</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Имя:</b> {boss['boss_name']}\n"
        f"❤️ <b>Здоровье:</b> {boss['current_hp']} / {boss['max_hp']} HP ({pct}%)\n"
        f"<code>[{hp_bar}]</code>\n\n"
        "⚡️ <i>Все игроки наносят урон этому боссу сообща! За каждый удар вы получаете монеты 💰 и опыт ⭐️, а добивший забирает супер-награду (+500 монет)!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(text, reply_markup=boss_battle_markup(), parse_mode=ParseMode.HTML)
    await call.answer()


@router.callback_query(F.data == "rpg:attack_boss")
async def attack_boss_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    atk = user.get("attack", 15) if user else 15

    # Случайный критический удар
    crit = random.choice([1.0, 1.0, 1.2, 1.5])
    actual_dmg = int(atk * crit)

    res = await db.attack_world_boss(user_id, actual_dmg)
    hp_bar = make_progress_bar(res["current_hp"], res["max_hp"])

    crit_text = " 💥 <b>КРИТИЧЕСКИЙ УДАР!</b>" if crit > 1.0 else ""
    if res["is_defeated"]:
        msg = (
            f"🎉 <b>БОСС ПОВЕРЖЕН!</b>\n\n"
            f"Вы нанесли сокрушительный финальный удар на <b>{actual_dmg} урона</b>{crit_text}!\n\n"
            f"👑 <b>Супер-награда победителя:</b> +{res['reward_coins']} монет 💰 и +{res['reward_xp']} XP ⭐️!\n\n"
            f"Появился новый, более могущественный босс!"
        )
    else:
        msg = (
            f"⚔️ <b>Вы атаковали босса!</b>\n\n"
            f"Нанесенный урон: <b>-{actual_dmg} HP</b>{crit_text}\n"
            f"У босса осталось: <b>{res['current_hp']} / {res['max_hp']} HP</b>\n"
            f"<code>[{hp_bar}]</code>\n\n"
            f"🎁 Награда за удар: <b>+{res['reward_coins']} монет 💰</b> и <b>+{res['reward_xp']} XP ⭐️</b>!"
        )

    await call.message.edit_text(msg, reply_markup=boss_battle_markup(), parse_mode=ParseMode.HTML)
    await call.answer("Удар нанесен!")


# =========================================================================
#  МАГАЗИН (SHOP)
# =========================================================================

@router.callback_query(F.data == "rpg:shop")
async def show_shop(call: types.CallbackQuery):
    user = await db.get_user(call.from_user.id)
    coins = user.get("coins", 0) if user else 0

    text = (
        "🏪 <b>Магазин снаряжения и зелий</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"Ваш кошелек: <b>{coins} монет 💰</b>\n\n"
        "🗡 <b>Железный меч:</b> +10 к атаке навсегда (150💰)\n"
        "🛡 <b>Стальной щит:</b> +8 к защите навсегда (200💰)\n"
        "🧪 <b>Зелье здоровья:</b> восстанавливает +50 HP (50💰)\n"
        "💎 <b>Алмаз удачи:</b> редкий драгоценный камень (300💰)\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(text, reply_markup=shop_markup(), parse_mode=ParseMode.HTML)
    await call.answer()


@router.callback_query(F.data.startswith("shop:buy:"))
async def buy_item_handler(call: types.CallbackQuery):
    parts = call.data.split(":")
    item_id = parts[2]
    price = int(parts[3])

    user_id = call.from_user.id
    user = await db.get_user(user_id)
    current_coins = user.get("coins", 0) if user else 0

    if current_coins < price:
        await call.answer("❌ У вас недостаточно монет для покупки!", show_alert=True)
        return

    items_info = {
        "sword_iron": ("Железный меч", "weapon"),
        "shield_steel": ("Стальной щит", "shield"),
        "health_potion": ("Зелье здоровья", "potion"),
        "diamond": ("Алмаз удачи", "gem"),
    }
    item_name, item_type = items_info.get(item_id, ("Предмет", "misc"))

    # Списываем монеты
    await db.execute(
        "UPDATE Users SET coins = coins - $1 WHERE telegram_id = $2",
        price, user_id, execute=True
    )
    await db.add_transaction(user_id, -price, "shop_buy", f"Покупка: {item_name}")

    # Добавляем в инвентарь
    await db.add_inventory_item(user_id, item_id, item_name, item_type, quantity=1)

    await call.answer(f"✅ Вы успешно приобрели {item_name}!", show_alert=True)
    await show_shop(call)


# =========================================================================
#  ИНВЕНТАРЬ (INVENTORY)
# =========================================================================

@router.callback_query(F.data == "rpg:inventory")
async def show_inventory(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = await db.get_inventory(user_id)

    if not items:
        text = (
            "🎒 <b>Ваш инвентарь пуст!</b>\n\n"
            "Загляните в 🏪 <b>Магазин</b>, чтобы приобрести оружие, броню и зелья."
        )
        buttons = [[types.InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu")]]
        await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
        await call.answer()
        return

    lines = ["🎒 <b>Ваш инвентарь:</b>\n━━━━━━━━━━━━━━━━━━━━━"]
    for it in items:
        lines.append(f"• <b>{it['item_name']}</b> — {it['quantity']} шт.")
    lines.append("━━━━━━━━━━━━━━━━━━━━━\n<i>Нажмите на предмет ниже, чтобы применить его:</i>")

    await call.message.edit_text("\n".join(lines), reply_markup=inventory_markup(items), parse_mode=ParseMode.HTML)
    await call.answer()


@router.callback_query(F.data.startswith("rpg:use:"))
async def use_item_handler(call: types.CallbackQuery):
    item_id = call.data.split(":")[2]
    user_id = call.from_user.id
    res = await db.use_inventory_item(user_id, item_id)

    if res["success"]:
        await call.answer(res["message"], show_alert=True)
    else:
        await call.answer(res["message"], show_alert=True)

    await show_inventory(call)


# =========================================================================
#  PVP БОИ
# =========================================================================

@router.callback_query(F.data == "rpg:pvp_search")
async def pvp_search_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = await db.get_user(user_id)

    my_attack = user.get("attack", 15) if user else 15
    my_level = user.get("level", 1) if user else 1

    # Ищем случайного соперника из базы
    opponents = await db.execute(
        "SELECT * FROM Users WHERE telegram_id != $1 AND is_registered = TRUE ORDER BY RANDOM() LIMIT 1",
        user_id, fetchrow=True
    )

    if not opponents:
        opp_name = "Гладиатор Арены (Бот)"
        opp_level = my_level
        opp_attack = my_attack - random.randint(-5, 5)
    else:
        opp_name = opponents["first_name"] or opponents["full_name"] or "Воин"
        opp_level = opponents["level"] or 1
        opp_attack = opponents["attack"] or 15

    # Симуляция дуэли
    my_roll = my_attack + random.randint(1, 20)
    opp_roll = opp_attack + random.randint(1, 20)

    if my_roll >= opp_roll:
        coins_win = 40
        xp_win = 30
        status = "🏆 <b>ВЫ ОДЕРЖАЛИ ПОБЕДУ В ДУЭЛИ!</b>"
        await db.record_game(user_id, won=True, coins_delta=coins_win, xp_delta=xp_win, game_name="PvP Дуэль")
        reward_text = f"+{coins_win} монет 💰 и +{xp_win} XP ⭐️"
    else:
        xp_loss = 10
        status = "💀 <b>ВЫ ПОТЕРПЕЛИ ПОРАЖЕНИЕ В ДУЭЛИ!</b>"
        await db.record_game(user_id, won=False, coins_delta=0, xp_delta=xp_loss, game_name="PvP Дуэль")
        reward_text = f"+{xp_loss} XP ⭐️"

    text = (
        "⚔️ <b>PvP Арена: Результат боя</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Вы</b> (Ур. {my_level}) — Мощь удара: <b>{my_roll}</b>\n"
        f"🆚 <b>{opp_name}</b> (Ур. {opp_level}) — Мощь удара: <b>{opp_roll}</b>\n\n"
        f"{status}\n\n"
        f"🎁 <b>Награда:</b> {reward_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    buttons = [
        [types.InlineKeyboardButton(text="⚔️ Сразиться снова", callback_data="rpg:pvp_search")],
        [types.InlineKeyboardButton(text="🔙 Меню RPG", callback_data="rpg:menu")],
    ]
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await call.answer()
