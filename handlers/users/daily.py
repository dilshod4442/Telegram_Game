from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

from loader import db

router = Router()


@router.message(Command("daily"))
@router.message(F.text == "🎁 Награда")
@router.message(F.text == "🎁 Забрать награду")
async def daily_reward_handler(message: types.Message):
    user_id = message.from_user.id
    status = await db.get_daily_status(user_id)

    streak_visual = {
        1: "1️⃣ День 1 (+50 💰)",
        2: "2️⃣ День 2 (+75 💰)",
        3: "3️⃣ День 3 (+100 💰)",
        4: "4️⃣ День 4 (+125 💰)",
        5: "5️⃣ День 5 (+150 💰)",
        6: "6️⃣ День 6 (+200 💰)",
        7: "7️⃣ День 7 (+300 💰 🔥 Джекпот!)",
    }

    if not status["can_claim"]:
        rem = status["remaining_seconds"]
        hours = rem // 3600
        mins = (rem % 3600) // 60
        streak = status["streak"]

        lines = [
            "⏰ <b>Вы уже забрали сегодняшнюю награду!</b>\n",
            f"Текущий стрик: <b>{streak} дн. подряд 🔥</b>\n",
            f"Следующая награда будет доступна через: <b>{hours} ч. {mins} мин.</b>\n",
            "━━━━━━━━━━━━━━━━━━━━━",
            "📅 <b>График наград за активность:</b>",
        ]
        for d, name in streak_visual.items():
            check = "✅ " if d <= streak else "🔒 "
            lines.append(f"{check}{name}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append("<i>Заходите каждый день, чтобы не потерять стрик наград!</i>")

        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    # Забираем награду
    res = await db.claim_daily_reward(user_id)
    streak = res["streak"]

    lines = [
        "🎉 <b>ПОЗДРАВЛЯЕМ! ЕЖЕДНЕВНАЯ НАГРАДА ПОЛУЧЕНА!</b>\n",
        f"📅 День стрика: <b>{streak} из 7 🔥</b>",
        f"💰 Получено монет: <b>+{res['coins']} coins</b>",
        f"⭐️ Получено опыта: <b>+{res['xp']} XP</b>\n",
        f"💳 Новый баланс: <b>{res['total_coins']} монет</b>",
        f"🎖 Текущий уровень: <b>{res['level']}</b> (XP: {res['total_xp']})\n",
        "━━━━━━━━━━━━━━━━━━━━━",
        "📅 <b>Прогресс недели:</b>",
    ]
    for d, name in streak_visual.items():
        check = "✅ " if d <= streak else "🔒 "
        lines.append(f"{check}{name}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Возвращайтесь завтра за следующей порцией бонусов!</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
