from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from loader import db
from data.config import ADMINS
from keyboards.reply.main_menu import get_main_menu, get_unregistered_menu
from keyboards.inline.profile import profile_inline_markup

router = Router()


@router.message(Command("location"))
@router.message(F.text.in_({"📍 Моя локация", "Моя локация", "моя локация", "Локация", "локация"}))
async def show_location_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user or not user.get("is_registered"):
        await message.answer(
            "⚠️ Вы еще не зарегистрированы. Нажмите «🚀 Зарегистрироваться», чтобы указать вашу локацию.",
            reply_markup=get_unregistered_menu(),
        )
        return

    address = user.get("location_address")
    lat = user.get("location_lat")
    lon = user.get("location_lon")

    if not address and lat is None:
        await message.answer(
            "📍 <b>Локация пока не указана.</b>\n\n"
            "Вы можете указать её в разделе <b>👤 Мой профиль</b> -> <b>✏️ Редактировать</b> -> <b>📍 Локация</b>.",
            parse_mode=ParseMode.HTML,
        )
        return

    text = (
        "📍 <b>Ваша сохраненная локация:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>Адрес/Город:</b> {address or 'Не указан'}\n"
    )
    if lat is not None and lon is not None:
        text += (
            f"🌐 <b>Координаты:</b> {lat:.5f}, {lon:.5f}\n"
            f"🔗 <a href='https://www.google.com/maps?q={lat},{lon}'>Открыть на Google Maps</a>\n"
        )
    text += (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Чтобы изменить локацию, перейдите в «👤 Мой профиль» -> «✏️ Редактировать».</i>"
    )

    await message.answer(text, reply_markup=profile_inline_markup(lat=lat, lon=lon), parse_mode=ParseMode.HTML)


@router.message(Command("about"))
@router.message(F.text.in_({"ℹ️ О боте", "О боте", "о боте"}))
async def about_bot_handler(message: types.Message):
    text = (
        "🤖 <b>О нашем многофункциональном Telegram-боте</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Этот бот объединяет современные возможности Telegram:\n\n"
        "✅ <b>Верификация Email:</b> 6-значный код безопасности через SMTP\n"
        "✅ <b>Локация:</b> авто-определение координат через GPS и города\n"
        "✅ <b>🎮 Мини-игры:</b> Кубик, КНБ, Викторина, Орёл/Решка\n"
        "✅ <b>⚔️ RPG:</b> Прокачка героя, Мировой Босс, Инвентарь, Магазин и PvP\n"
        "✅ <b>📅 Daily Rewards:</b> ежедневные награды с 7-дневным стриком\n"
        "✅ <b>🧠 AI & Код:</b> AI-ассистент и анализатор синтаксиса Python\n"
        "✅ <b>👥 Социум:</b> анонимный чат, анонимные ссылки, друзья и топ\n"
        "✅ <b>📊 Статистика:</b> учет активности и график расходов/доходов\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡️ Стек: <b>Python 3.12</b>, <b>Aiogram 3</b>, <b>PostgreSQL</b>."
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("support"))
@router.message(F.text.in_({"📞 Поддержка", "Поддержка", "поддержка"}))
async def support_handler(message: types.Message):
    admin_id = ADMINS[0] if ADMINS else None
    contact_link = f"@Dilshod_py" if admin_id else "Администратор"

    text = (
        "📞 <b>Служба поддержки и контакты:</b>\n"
        "\n"
        "Если у вас возникли вопросы, предложения или пожелания по боту:\n\n"
        f"👨‍💻 <b>Контакт:</b> {contact_link}\n"
        "⏰ Ответ обычно приходит в течение пары часов.\n"
        ""
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("settings"))
@router.message(F.text.in_({"⚙️ Настройки", "Настройки", "настройки"}))
async def settings_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    is_reg = user and user.get("is_registered")

    text = (
        "⚙️ <b>Настройки аккаунта:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Статус регистрации:</b> {'Зарегистрирован ✅' if is_reg else 'Не зарегистрирован ⚠️'}\n"
        f"• <b>Баланс:</b> {user.get('coins', 0) if user else 0} монет 💰\n"
        f"• <b>Уровень:</b> {user.get('level', 1) if user else 1} (XP: {user.get('xp', 0) if user else 0})\n"
        f"• <b>Язык интерфейса:</b> Русский 🇷🇺\n"
        f"• <b>Уведомления:</b> Включены 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Для изменения личных данных откройте «👤 Мой профиль».</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)
