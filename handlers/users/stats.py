import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

from loader import db

router = Router()


def make_ratio_bar(val1: int, val2: int, length: int = 12) -> str:
    total = val1 + val2
    if total <= 0:
        return "░" * length
    p1 = int((val1 / total) * length)
    p2 = length - p1
    return "🟩" * p1 + "🟥" * p2


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_statistics_hub(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    g_stats = await db.get_global_stats()
    spending = await db.get_spending_analytics(user_id)

    # 1. Личная статистика
    now = datetime.datetime.now()
    created_at = user.get("created_at") if user else now
    days_used = max(1, (now - created_at).days) if created_at else 1

    games_played = user.get("games_played", 0) if user else 0
    games_won = user.get("games_won", 0) if user else 0
    win_rate = int((games_won / games_played) * 100) if games_played > 0 else 0

    income = spending.get("income", 0)
    expense = spending.get("expense", 0)
    ratio_bar = make_ratio_bar(income, expense)

    text = (
        "📊 <b>Детальная Статистика и Аналитика</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>Ваша личная статистика:</b>\n"
        f"• Дней с ботом: <b>{days_used} дн.</b>\n"
        f"• Уровень героя: <b>{user.get('level', 1)}</b> (XP: {user.get('xp', 0)})\n"
        f"• Баланс: <b>{user.get('coins', 0)} монет 💰</b>\n"
        f"• Сыграно игр: <b>{games_played}</b> (Побед: {games_won}, Винрейт: {win_rate}%)\n"
        f"• Ежедневный стрик: <b>{user.get('daily_streak', 0)} дн. 🔥</b>\n\n"
        "📈 <b>Финансовый баланс аккаунта:</b>\n"
        f"• 🟩 Доходы: <b>+{income}💰</b> | 🟥 Расходы: <b>-{expense}💰</b>\n"
        f"Соотношение: <code>[{ratio_bar}]</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>Глобальная статистика системы:</b>\n"
        f"• 👥 Пользователей всего: <b>{g_stats['users']:,}</b>\n"
        f"• ⚡️ Активных сегодня: <b>{g_stats['active_today']:,}</b>\n"
        f"• 🆕 Новых за сегодня: <b>{g_stats['new_today']:,}</b>\n"
        f"• 💬 Сообщений обработано: <b>{g_stats['messages_today']:,}</b>\n\n"
        "🗄 <b>База данных (PostgreSQL):</b>\n"
        f"Users: <b>{g_stats['users']}</b> | Games: <b>{g_stats['games']}</b> | Transactions: <b>{g_stats['transactions']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    buttons = [
        [types.InlineKeyboardButton(text="📜 История транзакций", callback_data="stats:history")],
        [types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")],
    ]
    await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "stats:history")
async def show_transaction_history(call: types.CallbackQuery):
    user_id = call.from_user.id
    history = await db.get_user_transactions(user_id, limit=8)

    if not history:
        text = "📜 <b>История транзакций пуста.</b>"
    else:
        lines = ["📜 <b>Последние транзакции:</b>\n━━━━━━━━━━━━━━━━━━━━━"]
        for t in history:
            sign = "+" if t["amount"] > 0 else ""
            created = t["created_at"].strftime("%d.%m %H:%M") if t.get("created_at") else ""
            lines.append(f"• <code>{created}</code>: <b>{sign}{t['amount']} 💰</b> — {t.get('description', t['category'])}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        text = "\n".join(lines)

    buttons = [[types.InlineKeyboardButton(text="🔙 Назад к статистике", callback_data="stats:back")]]
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await call.answer()


@router.callback_query(F.data == "stats:back")
async def back_to_stats_callback(call: types.CallbackQuery):
    await call.message.delete()
    await show_statistics_hub(call.message)
