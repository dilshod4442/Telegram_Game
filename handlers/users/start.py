import logging
import html
from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import db, bot
from data.config import ADMINS
from keyboards.reply.main_menu import get_main_menu, get_unregistered_menu
from keyboards.reply.registration import cancel_keyboard
from states.features import SocialState

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def do_start(message: types.Message, command: CommandObject, state: FSMContext):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name or "Пользователь"
    username = message.from_user.username
    is_admin = str(telegram_id) in ADMINS

    # Добавляем или обновляем базовую информацию в БД
    try:
        await db.add_user(telegram_id=telegram_id, full_name=full_name, username=username)
    except Exception as error:
        logger.error(f"Error adding/upserting user: {error}")

    # Проверка на deep link для анонимных сообщений (например: /start anon_123456789)
    args = command.args
    if args and args.startswith("anon_"):
        target_str = args.replace("anon_", "")
        if target_str.isdigit():
            target_id = int(target_str)
            target_user = await db.get_user(target_id)
            if target_user and target_id != telegram_id:
                await state.set_state(SocialState.waiting_anon_text)
                await state.update_data(anon_recipient_id=target_id)
                target_name = target_user.get("first_name") or target_user.get("full_name") or "Пользователь"
                await message.answer(
                    f"📨 <b>Отправка анонимного сообщения для: {target_name}</b>\n\n"
                    "Напишите текст вашего послания прямо сейчас. Получатель получит его инкогнито и не узнает, кто вы!\n"
                    "<i>(Для отмены нажмите «❌ Отмена» или введите /cancel)</i>",
                    reply_markup=cancel_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
                return

    user = await db.get_user(telegram_id)
    is_registered = user and user.get("is_registered")
    safe_name = html.escape(user.get("first_name") or full_name)

    if is_registered:
        welcome_text = (
            f"👋 С возвращением, <b>{safe_name}</b>!\n\n"
            "Рады видеть вас снова. Используйте удобное меню ниже для навигации по всем разделам бота:\n\n"
            "• <b>👤 Мой профиль</b> — ваша анкета и карта\n"
            "• <b>🎮 Игры и RPG</b> — Кубик, КНБ, Викторина, Босс, PvP\n"
            "• <b>🎁 Награда</b> — ежедневные бонусы со стриком\n"
            "• <b>🧠 AI & Код</b> — умный ассистент и проверка Python\n"
            "• <b>👥 Социум & Чат</b> — анонимное общение и друзья\n"
            "• <b>📊 Статистика</b> — личные и глобальные показатели"
        )
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode=ParseMode.HTML,
        )
    else:
        invite_text = (
            f"👋 Здравствуйте, <b>{safe_name}</b>!\n\n"
            "Добро пожаловать в нашего бота! Для получения доступа ко всем сервисам, играм и функциям "
            "пройдите быструю и безопасную регистрацию.\n\n"
            "📋 <b>Что потребуется указать:</b>\n"
            "• Имя и фамилию\n"
            "• Номер телефона (удобно в 1 клик)\n"
            "• Email (с отправкой 6-значного проверочного кода)\n"
            "• Возраст и пол\n"
            "• Локацию / город\n"
            "• Краткое описание о себе\n\n"
            "<i>Это займет не более 1-2 минут!</i>"
        )
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Пройти регистрацию прямо сейчас",
                        callback_data="start_registration",
                    )
                ]
            ]
        )
        await message.answer(
            invite_text,
            reply_markup=get_unregistered_menu(),
            parse_mode=ParseMode.HTML,
        )
        await message.answer(
            "Нажмите кнопку ниже для старта регистрации 👇",
            reply_markup=inline_kb,
        )
