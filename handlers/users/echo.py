from aiogram import Router, types
from aiogram.enums.parse_mode import ParseMode

from loader import db, bot
from data.config import ADMINS
from keyboards.reply.main_menu import get_main_menu, get_unregistered_menu
from utils.misc.anon_chat import get_partner, is_in_chat

router = Router()


@router.message()
async def smart_fallback_handler(message: types.Message):
    user_id = message.from_user.id

    # 1. Если пользователь находится в активном анонимном чате — пересылаем сообщение собеседнику!
    partner_id = get_partner(user_id)
    if partner_id:
        try:
            await message.send_copy(chat_id=partner_id)
            return
        except Exception:
            pass

    # 2. Иначе — подсказка и меню
    user = await db.get_user(user_id)
    is_registered = user and user.get("is_registered")
    is_admin = str(user_id) in ADMINS

    reply_kb = get_main_menu(is_admin) if is_registered else get_unregistered_menu()

    await message.answer(
        "🤔 Я не распознал команду или сообщение.\n\n"
        "Пожалуйста, воспользуйтесь кнопками меню внизу или введите команду /help для справки.",
        reply_markup=reply_kb,
        parse_mode=ParseMode.HTML,
    )
