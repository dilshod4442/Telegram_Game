import re
import time
import random
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from loader import db
from data.config import ADMINS
from states.registration import EditProfileState
from keyboards.reply.main_menu import get_main_menu, get_unregistered_menu
from keyboards.reply.registration import (
    phone_share_keyboard,
    location_share_keyboard,
    gender_keyboard,
    cancel_keyboard,
)
from keyboards.inline.profile import profile_inline_markup, edit_profile_menu_markup
from keyboards.inline.registration import email_verification_inline_markup
from utils.misc.mailer import send_verification_email
from utils.misc.geocoder import reverse_geocode

logger = logging.getLogger(__name__)
router = Router()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")

FIELD_NAMES = {
    "first_name": "👤 Имя",
    "last_name": "👥 Фамилия",
    "phone": "📱 Номер телефона",
    "email": "📧 Email",
    "age": "🎂 Возраст",
    "gender": "🚻 Пол",
    "location": "📍 Локация / Город",
    "bio": "📝 О себе",
}


def build_profile_text(user: dict) -> str:
    """Формирует красивую карточку профиля в HTML"""
    first_name = user.get("first_name") or user.get("full_name") or "Не указано"
    last_name = user.get("last_name") or "—"
    username = f"@{user['username']}" if user.get("username") else "Не установлен"
    phone = user.get("phone") or "—"
    email = user.get("email") or "—"
    is_verified = user.get("is_email_verified", False)
    email_status = "✅ Подтвержден" if is_verified else "⚠️ Не подтвержден"
    
    age = user.get("age") or "—"
    gender = user.get("gender") or "—"
    location_address = user.get("location_address") or "—"
    bio = user.get("bio") or "—"

    reg_date = user.get("created_at")
    reg_date_str = reg_date.strftime("%d.%m.%Y %H:%M") if reg_date else "Неизвестно"

    text = (
        "👤 <b>Ваш персональный профиль:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Имя:</b> {first_name}\n"
        f"• <b>Фамилия:</b> {last_name}\n"
        f"• <b>Username:</b> {username}\n"
        f"• <b>Telegram ID:</b> <code>{user.get('telegram_id')}</code>\n"
        f"• <b>Телефон:</b> <code>{phone}</code>\n"
        f"• <b>Email:</b> <code>{email}</code> ({email_status})\n"
        f"• <b>Возраст:</b> {age}\n"
        f"• <b>Пол:</b> {gender}\n"
        f"• <b>Локация:</b> {location_address}\n"
        f"• <b>О себе:</b> {bio}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗓 <b>Дата регистрации:</b> {reg_date_str}\n\n"
        "<i>Вы можете в любой момент изменить данные анкеты кнопкой ниже.</i>"
    )
    return text


# =========================================================================
#  ПРОСМОТР ПРОФИЛЯ
# =========================================================================

@router.message(Command("profile"))
@router.message(F.text.in_({"👤 Мой профиль", "Мой профиль", "мой профиль", "Профиль", "профиль"}))
async def show_profile_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user or not user.get("is_registered"):
        await message.answer(
            "⚠️ <b>Вы ещё не зарегистрированы!</b>\n\n"
            "Пройдите простую регистрацию, чтобы получить доступ к своему профилю и всем возможностям.",
            reply_markup=get_unregistered_menu(),
            parse_mode=ParseMode.HTML,
        )
        return

    text = build_profile_text(dict(user))
    lat = user.get("location_lat")
    lon = user.get("location_lon")

    await message.answer(
        text,
        reply_markup=profile_inline_markup(lat=lat, lon=lon),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "refresh_profile")
async def refresh_profile_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = await db.get_user(user_id)

    if not user or not user.get("is_registered"):
        await call.answer("Профиль не найден.", show_alert=True)
        return

    text = build_profile_text(dict(user))
    lat = user.get("location_lat")
    lon = user.get("location_lon")

    try:
        await call.message.edit_text(
            text,
            reply_markup=profile_inline_markup(lat=lat, lon=lon),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
    await call.answer("Профиль обновлен! 🔄")


# =========================================================================
#  МЕНЮ РЕДАКТИРОВАНИЯ ПРОФИЛЯ
# =========================================================================

@router.message(Command("edit"))
@router.message(F.text.in_({"✏️ Редактировать", "Редактировать", "редактировать", "✏️ Редактировать профиль", "Редактировать профиль", "редактировать профиль"}))
@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await db.get_user(user_id)

    if not user or not user.get("is_registered"):
        msg = "⚠️ Сначала необходимо зарегистрироваться!"
        if isinstance(event, types.CallbackQuery):
            await event.answer(msg, show_alert=True)
        else:
            await event.answer(msg, reply_markup=get_unregistered_menu())
        return

    text = (
        "✏️ <b>Редактирование профиля:</b>\n\n"
        "Выберите поле, которое вы хотите изменить:"
    )

    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=edit_profile_menu_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=edit_profile_menu_markup(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=edit_profile_menu_markup(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await refresh_profile_callback(call)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    is_admin = str(user_id) in ADMINS
    user = await db.get_user(user_id)
    is_registered = user and user.get("is_registered")

    try:
        await call.message.delete()
    except Exception:
        pass

    menu = get_main_menu(is_admin) if is_registered else get_unregistered_menu()
    await call.message.answer("Главное меню открыто.", reply_markup=menu)
    await call.answer()


# =========================================================================
#  ВЫБОР ПОЛЯ ДЛЯ РЕДАКТИРОВАНИЯ
# =========================================================================

@router.callback_query(F.data.startswith("edit_field:"))
async def edit_field_selected(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]
    field_label = FIELD_NAMES.get(field, field)
    await state.update_data(editing_field=field)
    await state.set_state(EditProfileState.waiting_value)

    try:
        await call.message.delete()
    except Exception:
        pass

    if field == "first_name":
        prompt = "👤 Введите ваше новое <b>имя</b>:"
        kb = cancel_keyboard()
    elif field == "last_name":
        prompt = "👥 Введите вашу новую <b>фамилию</b> (или напишите «-», чтобы очистить):"
        kb = cancel_keyboard()
    elif field == "phone":
        prompt = "📱 Отправьте новый <b>номер телефона</b> с помощью кнопки или напишите вручную:"
        kb = phone_share_keyboard()
    elif field == "email":
        prompt = (
            "📧 Введите новый <b>адрес электронной почты</b>:\n\n"
            "<i>(Мы отправим проверочный код для подтверждения нового email)</i>"
        )
        kb = cancel_keyboard()
    elif field == "age":
        prompt = "🎂 Введите ваш новый <b>возраст</b> числом (от 10 до 110):"
        kb = cancel_keyboard()
    elif field == "gender":
        prompt = "🚻 Выберите ваш <b>пол</b>:"
        kb = gender_keyboard()
    elif field == "location":
        prompt = "📍 Поделитесь новой <b>геопозицией</b> с телефона или напишите город текстом:"
        kb = location_share_keyboard()
    elif field == "bio":
        prompt = "📝 Напишите новый рассказ <b>о себе</b> (до 500 символов) или «-» для очистки:"
        kb = cancel_keyboard()
    else:
        prompt = f"Введите новое значение для <b>{field_label}</b>:"
        kb = cancel_keyboard()

    await call.message.answer(prompt, reply_markup=kb, parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  ОБРАБОТКА НОВОГО ЗНАЧЕНИЯ ПОЛЯ
# =========================================================================

@router.message(EditProfileState.waiting_value, F.location)
async def process_edit_location_coords(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    if field != "location":
        await message.answer("⚠️ Ожидалось текстовое значение.", reply_markup=cancel_keyboard())
        return

    lat = message.location.latitude
    lon = message.location.longitude
    wait_msg = await message.answer("📍 <i>Определяем адрес...</i>", parse_mode=ParseMode.HTML)
    address = await reverse_geocode(lat, lon)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    user_id = message.from_user.id
    await db.update_user_field(user_id, "location_lat", lat)
    await db.update_user_field(user_id, "location_lon", lon)
    await db.update_user_field(user_id, "location_address", address)

    await state.clear()
    is_admin = str(user_id) in ADMINS
    await message.answer(
        f"✅ <b>Локация обновлена:</b> {address}",
        reply_markup=get_main_menu(is_admin),
        parse_mode=ParseMode.HTML,
    )
    await show_profile_handler(message)


@router.message(EditProfileState.waiting_value, F.contact)
async def process_edit_phone_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    if field != "phone":
        await message.answer("⚠️ Ожидалось текстовое значение.", reply_markup=cancel_keyboard())
        return

    phone = message.contact.phone_number.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    user_id = message.from_user.id
    await db.update_user_field(user_id, "phone", phone)

    await state.clear()
    is_admin = str(user_id) in ADMINS
    await message.answer(
        f"✅ <b>Номер телефона обновлен:</b> <code>{phone}</code>",
        reply_markup=get_main_menu(is_admin),
        parse_mode=ParseMode.HTML,
    )
    await show_profile_handler(message)


@router.message(EditProfileState.waiting_value, F.text)
async def process_edit_text_value(message: types.Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    field = data.get("editing_field")
    user_id = message.from_user.id
    is_admin = str(user_id) in ADMINS

    if field == "first_name":
        if len(text) < 2 or len(text) > 60:
            await message.answer("⚠️ Имя должно содержать от 2 до 60 символов:", reply_markup=cancel_keyboard())
            return
        await db.update_user_field(user_id, "first_name", text)
        await db.update_user_field(user_id, "full_name", text)

    elif field == "last_name":
        val = None if text in ["-", "–", "нет", "none"] else text
        if val and (len(val) < 2 or len(val) > 60):
            await message.answer("⚠️ Фамилия должна быть от 2 до 60 символов:", reply_markup=cancel_keyboard())
            return
        await db.update_user_field(user_id, "last_name", val)

    elif field == "phone":
        cleaned = re.sub(r"[\s\-\(\)]", "", text)
        if not PHONE_REGEX.match(cleaned) or len(cleaned) < 8 or len(cleaned) > 18:
            await message.answer(
                "⚠️ Некорректный номер телефона (например: <code>+998901234567</code>):",
                reply_markup=phone_share_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        await db.update_user_field(user_id, "phone", cleaned)

    elif field == "email":
        email = text.lower()
        if not EMAIL_REGEX.match(email):
            await message.answer(
                "⚠️ Некорректный формат email. Введите правильный адрес:",
                reply_markup=cancel_keyboard(),
            )
            return

        code = f"{random.randint(100000, 999999)}"
        wait_msg = await message.answer("⏳ <i>Отправляем код подтверждения...</i>", parse_mode=ParseMode.HTML)
        success, info = await send_verification_email(to_email=email, code=code, user_name=message.from_user.first_name or "")
        try:
            await wait_msg.delete()
        except Exception:
            pass

        await state.update_data(
            new_email=email,
            email_code=code,
            code_time=time.time(),
            code_attempts=0,
        )
        await state.set_state(EditProfileState.waiting_email_code)

        if success:
            prompt = (
                f"📨 Код отправлен на <code>{email}</code>.\n"
                "Введите 6-значный код из письма:"
            )
        elif info == "NOT_CONFIGURED":
            prompt = (
                f"📨 Код для подтверждения <code>{email}</code>:\n"
                f"🔑 Ваш код: <b><code>{code}</code></b>\n\n"
                "Введите этот код для сохранения email:"
            )
        else:
            prompt = (
                f"⚠️ Ошибка SMTP: {info}\n"
                f"Тестовый код: <b><code>{code}</code></b>\nВведите его:"
            )

        await message.answer(prompt, reply_markup=email_verification_inline_markup(), parse_mode=ParseMode.HTML)
        return

    elif field == "age":
        if not text.isdigit() or not (10 <= int(text) <= 110):
            await message.answer("⚠️ Введите корректный возраст от 10 до 110 лет:", reply_markup=cancel_keyboard())
            return
        await db.update_user_field(user_id, "age", int(text))

    elif field == "gender":
        if "Мужской" in text:
            val = "Мужской"
        elif "Женский" in text:
            val = "Женский"
        else:
            await message.answer("⚠️ Выберите «👨 Мужской» или «👩 Женский»:", reply_markup=gender_keyboard())
            return
        await db.update_user_field(user_id, "gender", val)

    elif field == "location":
        val = None if text in ["-", "–", "нет", "none"] else text
        await db.update_user_field(user_id, "location_address", val)
        await db.update_user_field(user_id, "location_lat", None)
        await db.update_user_field(user_id, "location_lon", None)

    elif field == "bio":
        val = None if text in ["-", "–", "нет", "none"] else text
        if val and len(val) > 500:
            await message.answer("⚠️ Описание не должно превышать 500 символов:", reply_markup=cancel_keyboard())
            return
        await db.update_user_field(user_id, "bio", val)

    await state.clear()
    await message.answer(
        f"✅ Поле <b>{FIELD_NAMES.get(field, field)}</b> успешно обновлено!",
        reply_markup=get_main_menu(is_admin),
        parse_mode=ParseMode.HTML,
    )
    await show_profile_handler(message)


# =========================================================================
#  ПОДТВЕРЖДЕНИЕ НОВОГО EMAIL ПРИ РЕДАКТИРОВАНИИ
# =========================================================================

@router.message(EditProfileState.waiting_email_code, F.text)
async def process_edit_email_code(message: types.Message, state: FSMContext):
    user_input = message.text.strip().replace(" ", "")
    data = await state.get_data()
    expected_code = data.get("email_code")
    new_email = data.get("new_email")
    code_time = data.get("code_time", 0)
    attempts = data.get("code_attempts", 0) + 1
    await state.update_data(code_attempts=attempts)

    if time.time() - code_time > 600:
        await message.answer("⏰ Время действия кода истекло. Запросите код повторно.", reply_markup=email_verification_inline_markup())
        return

    if user_input != expected_code:
        if attempts >= 5:
            await message.answer("❌ Слишком много неверных попыток. Изменение email отменено.")
            await state.clear()
            return
        await message.answer(f"❌ Неверный код (попытка {attempts} из 5). Попробуйте еще раз:")
        return

    # Успешная верификация
    user_id = message.from_user.id
    await db.update_user_field(user_id, "email", new_email)
    await db.update_user_field(user_id, "is_email_verified", True)

    await state.clear()
    is_admin = str(user_id) in ADMINS

    await message.answer(
        f"✅ <b>Email успешно подтвержден и обновлен:</b> <code>{new_email}</code>",
        reply_markup=get_main_menu(is_admin),
        parse_mode=ParseMode.HTML,
    )
    await show_profile_handler(message)
