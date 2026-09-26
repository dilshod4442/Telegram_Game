import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from loader import db, bot
from keyboards.inline.social import (
    social_menu_markup,
    anon_chat_active_markup,
    anon_search_markup,
    leaderboard_markup,
)
from states.features import SocialState
from utils.misc.anon_chat import (
    start_search,
    stop_search,
    get_partner,
    end_chat,
    is_in_chat,
)
from keyboards.reply.registration import cancel_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("social"))
@router.message(F.text == "👥 Социум & Чат")
@router.callback_query(F.data == "social:menu")
async def show_social_hub(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    bot_info = await bot.me()

    text = (
        "👥 <b>Социальный Центр и Общение</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Общайтесь, находите новых друзей и соревнуйтесь в рейтингах!\n\n"
        "💬 <b>Анонимный чат</b> — случайный диалог один на один в реальном времени.\n"
        "📨 <b>Анонимные сообщения</b> — получите личную ссылку, чтобы другие могли писать вам тайные послания.\n"
        "👥 <b>Друзья</b> — сохраняйте контакты интересных пользователей.\n"
        "🏆 <b>Глобальный ТОП</b> — списки лидеров по опыту, монетам и победам.\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Ваша ссылка для анонимных вопросов:</b>\n"
        f"<code>https://t.me/{bot_info.username}?start=anon_{user_id}</code>"
    )

    markup = social_menu_markup(bot_info.username, user_id)
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# =========================================================================
#  1. АНОНИМНЫЙ СЛУЧАЙНЫЙ ЧАТ
# =========================================================================

@router.callback_query(F.data == "social:anon_chat:start")
async def start_anon_chat_search(call: types.CallbackQuery):
    user_id = call.from_user.id

    if is_in_chat(user_id):
        await call.answer("Вы уже находитесь в диалоге!", show_alert=True)
        return

    partner_id = start_search(user_id)
    if partner_id:
        # Пара найдена!
        msg_text = (
            "🎉 <b>Собеседник найден!</b>\n\n"
            "Вы соединены в анонимном чате. Все текстовые сообщения, которые вы отправляете, "
            "передаются вашему собеседнику инкогнито.\n\n"
            "<i>Для завершения диалога нажмите кнопку «Завершить диалог».</i>"
        )
        await call.message.edit_text(msg_text, reply_markup=anon_chat_active_markup(), parse_mode=ParseMode.HTML)
        await call.answer()

        try:
            await bot.send_message(
                chat_id=partner_id,
                text=msg_text,
                reply_markup=anon_chat_active_markup(),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.warning(f"Не удалось отправить уведомление собеседнику {partner_id}: {exc}")
    else:
        # В очереди
        wait_text = (
            "🔍 <b>Поиск случайного собеседника...</b>\n\n"
            "Ожидаем подключения другого пользователя. Пожалуйста, подождите."
        )
        await call.message.edit_text(wait_text, reply_markup=anon_search_markup(), parse_mode=ParseMode.HTML)
        await call.answer()


@router.callback_query(F.data == "social:anon_chat:cancel_search")
async def cancel_anon_search(call: types.CallbackQuery, state: FSMContext):
    stop_search(call.from_user.id)
    await call.answer("Поиск отменен.")
    await show_social_hub(call, state)


@router.callback_query(F.data == "social:anon_chat:stop")
async def stop_anon_chat(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    partner_id = end_chat(user_id)

    await call.message.edit_text("⏹ <b>Диалог завершен.</b>", parse_mode=ParseMode.HTML)
    await call.answer("Диалог завершен.")

    if partner_id:
        try:
            await bot.send_message(
                chat_id=partner_id,
                text="⏹ <b>Собеседник завершил анонимный диалог.</b>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    await show_social_hub(call, state)


@router.callback_query(F.data == "social:anon_chat:next")
async def next_anon_chat(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    partner_id = end_chat(user_id)

    if partner_id:
        try:
            await bot.send_message(
                chat_id=partner_id,
                text="⏹ <b>Собеседник переключился на поиск следующего контакта.</b>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    await start_anon_chat_search(call)


# =========================================================================
#  2. ДРУЗЬЯ (FRIENDS)
# =========================================================================

@router.callback_query(F.data == "social:friends:list")
async def list_friends(call: types.CallbackQuery):
    user_id = call.from_user.id
    friends = await db.get_friends(user_id)

    if not friends:
        text = (
            "👥 <b>Список друзей пуст!</b>\n\n"
            "Вы можете добавить друга, зная его <b>Telegram ID</b> или <b>Username</b>."
        )
    else:
        lines = ["👥 <b>Ваши друзья:</b>\n━━━━━━━━━━━━━━━━━━━━━"]
        for f in friends:
            uname = f"@{f['username']}" if f.get("username") else "нет username"
            name = f.get("first_name") or f.get("full_name") or "Друг"
            lines.append(f"• <b>{name}</b> ({uname}) — Ур. {f.get('level', 1)} | XP: {f.get('xp', 0)}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        text = "\n".join(lines)

    buttons = [
        [types.InlineKeyboardButton(text="➕ Добавить друга", callback_data="social:friends:add")],
        [types.InlineKeyboardButton(text="🔙 Меню социума", callback_data="social:menu")],
    ]
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await call.answer()


@router.callback_query(F.data == "social:friends:add")
async def add_friend_prompt(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(SocialState.waiting_friend_id)
    await call.message.answer(
        "➕ <b>Добавление в друзья:</b>\n\n"
        "Введите <b>Telegram ID</b> пользователя или его <b>@username</b>:\n"
        "<i>(Для отмены введите /cancel)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.message(SocialState.waiting_friend_id, F.text)
async def process_add_friend(message: types.Message, state: FSMContext):
    query = message.text.strip()
    target_user = await db.search_user(query)

    if not target_user:
        await message.answer(
            f"❌ Пользователь «{query}» не найден в базе данных бота.\n"
            "Убедитесь, что он хотя бы раз запускал этого бота.",
            reply_markup=cancel_keyboard(),
        )
        return

    user_id = message.from_user.id
    target_id = target_user["telegram_id"]

    if user_id == target_id:
        await message.answer("😅 Нельзя добавить самого себя в друзья!", reply_markup=cancel_keyboard())
        return

    await db.add_friend(user_id, target_id)
    await state.clear()

    target_name = target_user.get("first_name") or target_user.get("full_name") or "Пользователь"
    await message.answer(
        f"✅ <b>{target_name}</b> успешно добавлен в ваш список друзей!",
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  3. ГЛОБАЛЬНЫЙ ТОП (LEADERBOARD)
# =========================================================================

@router.callback_query(F.data.startswith("social:top:"))
async def show_leaderboard(call: types.CallbackQuery):
    cat = call.data.split(":")[2]
    leaders = await db.get_leaderboard(category=cat, limit=10)

    cat_titles = {
        "xp": "⭐️ Топ-10 по Опыту (XP)",
        "coins": "💰 Топ-10 по Монетам",
        "wins": "🏆 Топ-10 по Победам в Играх",
        "streak": "🔥 Топ-10 по Ежедневному Стрику",
    }
    title = cat_titles.get(cat, "Топ игроков")

    lines = [f"🏆 <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    if not leaders:
        lines.append("<i>Список лидеров формируется...</i>")
    else:
        for idx, u in enumerate(leaders):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}."
            name = u.get("name") or "Игрок"
            if cat == "xp":
                val = f"{u.get('xp', 0)} XP (Ур. {u.get('level', 1)})"
            elif cat == "coins":
                val = f"{u.get('coins', 0)} 💰"
            elif cat == "wins":
                val = f"{u.get('games_won', 0)} побед"
            elif cat == "streak":
                val = f"{u.get('daily_streak', 0)} дн. 🔥"
            else:
                val = ""
            lines.append(f"{medal} <b>{name}</b> — {val}")

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    await call.message.edit_text("\n".join(lines), reply_markup=leaderboard_markup(cat), parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  4. ДОСТАВКА АНОНИМНЫХ СООБЩЕНИЙ
# =========================================================================

@router.message(SocialState.waiting_anon_text, F.text)
async def deliver_anon_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("anon_recipient_id")
    await state.clear()

    if not target_id:
        await message.answer("⚠️ Получатель не найден.")
        return

    text = message.text.strip()
    try:
        await bot.send_message(
            chat_id=target_id,
            text=(
                "📨 <b>Вам пришло новое анонимное сообщение!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>«{text}»</i>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Отправитель сохранил полную анонимность.</i>"
            ),
            parse_mode=ParseMode.HTML,
        )
        await message.answer(
            "✅ <b>Ваше анонимное сообщение успешно доставлено!</b>\n"
            "Получатель никогда не узнает, кто его отправил.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        logger.warning(f"Не удалось отправить анонимное сообщение {target_id}: {exc}")
        await message.answer("❌ Не удалось доставить сообщение (возможно, пользователь заблокировал бота).")

