import logging
import asyncio
import os
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from loader import db, bot
from keyboards.inline.buttons import are_you_sure_markup
from keyboards.inline.admin import admin_panel_markup
from states.test import AdminState
from filters.admin import IsBotAdminFilter
from data.config import ADMINS
from utils.pgtoexcel import export_to_excel
from keyboards.reply.registration import cancel_keyboard

logger = logging.getLogger(__name__)
router = Router()


# =========================================================================
#  ГЛАВНАЯ АДМИН-ПАНЕЛЬ
# =========================================================================

@router.message(Command("admin"), IsBotAdminFilter(ADMINS))
@router.message(F.text.in_({"👑 Админ-панель", "Админ-панель", "админ", "Админ"}), IsBotAdminFilter(ADMINS))
async def admin_dashboard(message: types.Message):
    total = await db.count_users()
    registered = await db.count_registered_users()
    verified_email = await db.count_verified_emails()
    g_stats = await db.get_global_stats()

    text = (
        "👑 <b>Панель администратора</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Всего пользователей в БД:</b> {total:,}\n"
        f"📝 <b>Завершили регистрацию:</b> {registered:,}\n"
        f"📧 <b>Подтвердили Email:</b> {verified_email:,}\n"
        f"⚡️ <b>Активных сегодня:</b> {g_stats['active_today']:,}\n"
        f"💬 <b>Сообщений сегодня:</b> {g_stats['messages_today']:,}\n"
        f"🎮 <b>Всего сыграно игр:</b> {g_stats['games']:,}\n"
        f"💾 <b>База данных:</b> PostgreSQL (Активна ✅)\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Используйте кнопки ниже или команду /user &lt;id&gt; для поиска:</i>"
    )
    await message.answer(text, reply_markup=admin_panel_markup(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin_stats", IsBotAdminFilter(ADMINS))
async def admin_stats_callback(call: types.CallbackQuery):
    total = await db.count_users()
    registered = await db.count_registered_users()
    verified_email = await db.count_verified_emails()
    g_stats = await db.get_global_stats()

    text = (
        "👑 <b>Панель администратора (Обновлено)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Всего пользователей в БД:</b> {total:,}\n"
        f"📝 <b>Завершили регистрацию:</b> {registered:,}\n"
        f"📧 <b>Подтвердили Email:</b> {verified_email:,}\n"
        f"⚡️ <b>Активных сегодня:</b> {g_stats['active_today']:,}\n"
        f"💬 <b>Сообщений сегодня:</b> {g_stats['messages_today']:,}\n"
        f"🎮 <b>Всего сыграно игр:</b> {g_stats['games']:,}\n"
        f"💾 <b>База данных:</b> PostgreSQL (Активна ✅)\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Используйте кнопки ниже:</i>"
    )
    try:
        await call.message.edit_text(text, reply_markup=admin_panel_markup(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await call.answer("Статистика обновлена!")


# =========================================================================
#  ПОИСК ПОЛЬЗОВАТЕЛЯ (/user <id_or_username>)
# =========================================================================

@router.message(Command("user"), IsBotAdminFilter(ADMINS))
async def admin_search_user(message: types.Message, command: CommandObject):
    query = command.args
    if not query:
        await message.answer(
            "ℹ️ <b>Формат команды:</b> <code>/user &lt;ID или @username&gt;</code>\n"
            "Например: <code>/user 5786425491</code> или <code>/user @Dilshod_py</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    u = await db.search_user(query)
    if not u:
        await message.answer(f"❌ Пользователь «{query}» не найден в базе данных.")
        return

    created_str = u["created_at"].strftime("%d.%m.%Y %H:%M") if u.get("created_at") else "Неизвестно"
    email_status = "✅ Подтвержден" if u.get("is_email_verified") else "⚠️ Не подтвержден"
    reg_status = "✅ Зарегистрирован" if u.get("is_registered") else "❌ Не завершена"

    text = (
        "👤 <b>Карточка пользователя</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{u['telegram_id']}</code>\n"
        f"👤 <b>Имя:</b> {u.get('first_name') or u.get('full_name') or '—'}\n"
        f"👥 <b>Фамилия:</b> {u.get('last_name') or '—'}\n"
        f"🔗 <b>Username:</b> @{u.get('username') or 'нет_username'}\n"
        f"📋 <b>Статус анкеты:</b> {reg_status}\n"
        f"🗓 <b>Регистрация:</b> {created_str}\n\n"
        f"📱 <b>Телефон:</b> <code>{u.get('phone') or '—'}</code>\n"
        f"📧 <b>Email:</b> <code>{u.get('email') or '—'}</code> ({email_status})\n"
        f"📍 <b>Локация:</b> {u.get('location_address') or '—'}\n"
        f"🎂 <b>Возраст:</b> {u.get('age') or '—'} | <b>Пол:</b> {u.get('gender') or '—'}\n"
        f"📝 <b>О себе:</b> {u.get('bio') or '—'}\n\n"
        f"💰 <b>Баланс:</b> {u.get('coins', 0)} монет\n"
        f"⭐️ <b>Уровень:</b> {u.get('level', 1)} (XP: {u.get('xp', 0)})\n"
        f"❤️ <b>HP:</b> {u.get('hp', 100)} / {u.get('max_hp', 100)}\n"
        f"🗡 <b>Атака:</b> {u.get('attack', 15)} | 🛡 <b>Защита:</b> {u.get('defense', 10)}\n"
        f"🎮 <b>Игры:</b> {u.get('games_played', 0)} (Побед: {u.get('games_won', 0)})\n"
        f"💬 <b>Всего сообщений:</b> {u.get('total_messages', 0)}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


# =========================================================================
#  ВЫГРУЗКА В EXCEL
# =========================================================================

@router.message(Command("allusers"), IsBotAdminFilter(ADMINS))
@router.callback_query(F.data == "admin_export_excel", IsBotAdminFilter(ADMINS))
async def get_all_users_export(event: types.Message | types.CallbackQuery):
    msg_target = event if isinstance(event, types.Message) else event.message
    if isinstance(event, types.CallbackQuery):
        await event.answer("Формируем Excel-отчет...")

    wait_msg = await msg_target.answer("⏳ <i>Подготавливаем таблицу пользователей...</i>", parse_mode=ParseMode.HTML)

    users = await db.select_all_users()
    headings = [
        "ID", "Telegram ID", "Имя (TG)", "Username", "Имя", "Фамилия",
        "Телефон", "Email", "Email подтвержден", "Возраст", "Пол",
        "Локация / Город", "О себе", "Зарегистрирован", "Баланс (Coins)",
        "Уровень", "XP", "Сыграно игр", "Побед", "Дата регистрации"
    ]

    export_rows = []
    for u in users:
        u_dict = dict(u)
        created_str = (
            u_dict.get("created_at").strftime("%d.%m.%Y %H:%M")
            if u_dict.get("created_at")
            else ""
        )
        row = [
            u_dict.get("id"),
            u_dict.get("telegram_id"),
            u_dict.get("full_name") or "",
            u_dict.get("username") or "",
            u_dict.get("first_name") or "",
            u_dict.get("last_name") or "",
            u_dict.get("phone") or "",
            u_dict.get("email") or "",
            "Да" if u_dict.get("is_email_verified") else "Нет",
            u_dict.get("age") or "",
            u_dict.get("gender") or "",
            u_dict.get("location_address") or "",
            u_dict.get("bio") or "",
            "Да" if u_dict.get("is_registered") else "Нет",
            u_dict.get("coins", 0),
            u_dict.get("level", 1),
            u_dict.get("xp", 0),
            u_dict.get("games_played", 0),
            u_dict.get("games_won", 0),
            created_str,
        ]
        export_rows.append(row)

    os.makedirs("data", exist_ok=True)
    file_path = "data/users_export.xlsx"

    await export_to_excel(data=export_rows, headings=headings, filepath=file_path)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    count = len(users)
    await msg_target.answer_document(
        types.input_file.FSInputFile(file_path),
        caption=f"📊 <b>Выгрузка базы данных</b>\nВсего пользователей в файле: <b>{count}</b>",
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  НАДЁЖНАЯ РАССЫЛКА СООБЩЕНИЙ (BROADCAST)
# =========================================================================

@router.message(Command("reklama"), IsBotAdminFilter(ADMINS))
@router.callback_query(F.data == "admin_broadcast", IsBotAdminFilter(ADMINS))
async def ask_broadcast_content(event: types.Message | types.CallbackQuery, state: FSMContext):
    msg_target = event if isinstance(event, types.Message) else event.message
    if isinstance(event, types.CallbackQuery):
        await event.answer()

    await msg_target.answer(
        "📢 <b>Режим рассылки сообщений:</b>\n\n"
        "Отправьте любое сообщение (текст, фото с описанием, видео, голосовое или стикер), "
        "которое вы хотите разослать всем пользователям бота.\n\n"
        "<i>Для отмены нажмите кнопку «❌ Отмена» или введите /cancel.</i>",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(AdminState.ask_ad_content)


@router.message(AdminState.ask_ad_content, IsBotAdminFilter(ADMINS))
async def send_broadcast_to_users(message: types.Message, state: FSMContext):
    if message.text in ["/cancel", "❌ Отмена"]:
        await state.clear()
        await message.answer("❌ <b>Рассылка отменена.</b>", parse_mode=ParseMode.HTML)
        return

    users = await db.select_all_users()
    count_total = len(users)
    count_success = 0
    count_blocked = 0

    status_msg = await message.answer(f"⏳ <b>Рассылка запущена...</b> (0 из {count_total})", parse_mode=ParseMode.HTML)

    for idx, user in enumerate(users, start=1):
        u_id = user["telegram_id"]
        try:
            await message.send_copy(chat_id=u_id)
            count_success += 1
        except Exception as error:
            logger.info(f"Failed broadcast to user {u_id}: {error}")
            count_blocked += 1

        # Обновляем статус каждые 15 пользователей
        if idx % 15 == 0 or idx == count_total:
            try:
                await status_msg.edit_text(
                    f"⏳ <b>Идет рассылка...</b>\n"
                    f"Обработано: <b>{idx} из {count_total}</b>\n"
                    f"• Доставлено: <b>{count_success}</b>\n"
                    f"• Ошибок: <b>{count_blocked}</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

        await asyncio.sleep(0.04)

    await status_msg.edit_text(
        f"✅ <b>Рассылка успешно завершена!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Всего пользователей: <b>{count_total}</b>\n"
        f"• Успешно доставлено: <b>{count_success}</b>\n"
        f"• Ошибок (заблокировали бота): <b>{count_blocked}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML,
    )
    await state.clear()


# =========================================================================
#  ОЧИСТКА БАЗЫ ДАННЫХ
# =========================================================================

@router.message(Command("cleandb"), IsBotAdminFilter(ADMINS))
@router.callback_query(F.data == "admin_cleandb_ask", IsBotAdminFilter(ADMINS))
async def ask_are_you_sure(event: types.Message | types.CallbackQuery, state: FSMContext):
    msg_target = event if isinstance(event, types.Message) else event.message
    if isinstance(event, types.CallbackQuery):
        await event.answer()

    msg = await msg_target.answer(
        "⚠️ <b>Внимание!</b>\nВы действительно хотите удалить всех пользователей из базы данных?",
        reply_markup=are_you_sure_markup,
        parse_mode=ParseMode.HTML,
    )
    await state.update_data(msg_id=msg.message_id)
    await state.set_state(AdminState.are_you_sure)


@router.callback_query(AdminState.are_you_sure, IsBotAdminFilter(ADMINS))
async def clean_db(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_id")

    if call.data == "yes":
        await db.delete_users()
        text = "🗑 <b>База данных успешно очищена!</b>"
    else:
        text = "❌ Действие отменено."

    try:
        await bot.edit_message_text(
            text=text,
            chat_id=call.message.chat.id,
            message_id=msg_id,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await call.message.answer(text, parse_mode=ParseMode.HTML)

    await state.clear()
    await call.answer()
