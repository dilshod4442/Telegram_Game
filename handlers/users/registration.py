import re
import time
import random
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from loader import db, bot
from data.config import ADMINS
from states.registration import RegistrationState
from keyboards.reply.main_menu import get_main_menu, get_unregistered_menu
from keyboards.reply.registration import (
    phone_share_keyboard,
    location_share_keyboard,
    gender_keyboard,
    skip_or_cancel_keyboard,
    cancel_keyboard,
)
from keyboards.inline.registration import (
    email_verification_inline_markup,
    confirm_registration_inline_markup,
)
from utils.misc.mailer import send_verification_email, is_smtp_configured
from utils.misc.geocoder import reverse_geocode

logger = logging.getLogger(__name__)
router = Router()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")


# =========================================================================
#  СТАРТ РЕГИСТРАЦИИ И ОТМЕНА
# =========================================================================

@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    """Отмена текущего действия FSM"""
    current_state = await state.get_state()
    if current_state is None:
        user = await db.get_user(message.from_user.id)
        is_registered = user and user.get("is_registered")
        is_admin = str(message.from_user.id) in ADMINS
        reply_kb = get_main_menu(is_admin) if is_registered else get_unregistered_menu()
        await message.answer("Нет активных действий для отмены.", reply_markup=reply_kb)
        return

    await state.clear()
    user = await db.get_user(message.from_user.id)
    is_registered = user and user.get("is_registered")
    is_admin = str(message.from_user.id) in ADMINS
    reply_kb = get_main_menu(is_admin) if is_registered else get_unregistered_menu()

    await message.answer(
        "❌ <b>Действие отменено.</b>\nВы вернулись в главное меню.",
        reply_markup=reply_kb,
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "cancel_registration")
async def cancel_reg_callback(call: types.CallbackQuery, state: FSMContext):
    """Отмена регистрации по кнопке inline"""
    await state.clear()
    user = await db.get_user(call.from_user.id)
    is_registered = user and user.get("is_registered")
    is_admin = str(call.from_user.id) in ADMINS
    reply_kb = get_main_menu(is_admin) if is_registered else get_unregistered_menu()

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        "❌ <b>Регистрация отменена.</b>\nВы можете начать её заново в любой момент нажав «🚀 Зарегистрироваться».",
        reply_markup=reply_kb,
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.message(Command("register"))
@router.message(F.text == "🚀 Зарегистрироваться")
@router.message(F.text == "🚀 Начать регистрацию")
@router.callback_query(F.data == "start_registration")
async def start_registration_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    """Инициализация процесса регистрации"""
    user_id = event.from_user.id
    user = await db.get_user(user_id)
    is_admin = str(user_id) in ADMINS

    if user and user.get("is_registered"):
        msg_text = (
            "ℹ️ <b>Вы уже зарегистрированы!</b>\n\n"
            "Ваша анкета сохранена. Вы можете посмотреть или изменить свои данные в разделе <b>👤 Мой профиль</b>."
        )
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(msg_text, reply_markup=get_main_menu(is_admin), parse_mode=ParseMode.HTML)
            await event.answer()
        else:
            await event.answer(msg_text, reply_markup=get_main_menu(is_admin), parse_mode=ParseMode.HTML)
        return

    # Начинаем пошаговую регистрацию
    default_name = event.from_user.first_name or ""
    text = (
        "🚀 <b>Добро пожаловать в регистрацию!</b>\n\n"
        "Заполнение профиля займет всего около 1-2 минут.\n\n"
        "Шаг <b>1 из 8</b>: <b>Как вас зовут?</b>\n"
        f"<i>(Введите ваше имя или подтвердите: <code>{default_name}</code>)</i>"
    )

    await state.set_state(RegistrationState.first_name)
    await state.update_data(first_name_default=default_name)

    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.delete()
        except Exception:
            pass
        await event.message.answer(text, reply_markup=cancel_keyboard(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=cancel_keyboard(), parse_mode=ParseMode.HTML)


# =========================================================================
#  ШАГ 1: ИМЯ (FIRST NAME)
# =========================================================================

@router.message(RegistrationState.first_name, F.text)
async def process_first_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer(
            "⚠️ Пожалуйста, введите корректное имя (от 2 до 60 символов):",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(first_name=name)
    await state.set_state(RegistrationState.last_name)

    await message.answer(
        f"Приятно познакомиться, <b>{name}</b>! 👋\n\n"
        "Шаг <b>2 из 8</b>: <b>Какая у вас фамилия?</b>\n"
        "<i>(Введите фамилию или нажмите «➡️ Пропустить»)</i>",
        reply_markup=skip_or_cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 2: ФАМИЛИЯ (LAST NAME)
# =========================================================================

@router.message(RegistrationState.last_name, F.text)
async def process_last_name(message: types.Message, state: FSMContext):
    text = message.text.strip()
    last_name = None if text in ["➡️ Пропустить", "Пропустить", "-", "–"] else text

    if last_name and (len(last_name) < 2 or len(last_name) > 60):
        await message.answer(
            "⚠️ Пожалуйста, введите корректную фамилию или нажмите «➡️ Пропустить»:",
            reply_markup=skip_or_cancel_keyboard(),
        )
        return

    await state.update_data(last_name=last_name)
    await state.set_state(RegistrationState.phone)

    await message.answer(
        "Шаг <b>3 из 8</b>: <b>Ваш номер телефона 📱</b>\n\n"
        "Нажмите кнопку <b>«📱 Отправить контакт»</b> ниже или введите номер вручную "
        "(например: <code>+998901234567</code> или <code>+79991234567</code>):",
        reply_markup=phone_share_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 3: НОМЕР ТЕЛЕФОНА (PHONE)
# =========================================================================

@router.message(RegistrationState.phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(RegistrationState.email)

    await message.answer(
        f"✅ Номер <code>{phone}</code> принят!\n\n"
        "Шаг <b>4 из 8</b>: <b>Укажите ваш действующий Email 📧</b>\n\n"
        "На эту почту мы отправим 6-значный код подтверждения безопасности.",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(RegistrationState.phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    raw_phone = message.text.strip()
    cleaned = re.sub(r"[\s\-\(\)]", "", raw_phone)

    if not PHONE_REGEX.match(cleaned) or len(cleaned) < 8 or len(cleaned) > 18:
        await message.answer(
            "⚠️ Пожалуйста, введите корректный номер телефона (например: <code>+998901234567</code>) "
            "или используйте кнопку «📱 Отправить контакт»:",
            reply_markup=phone_share_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    await state.update_data(phone=cleaned)
    await state.set_state(RegistrationState.email)

    await message.answer(
        f"✅ Номер <code>{cleaned}</code> принят!\n\n"
        "Шаг <b>4 из 8</b>: <b>Укажите ваш действующий Email 📧</b>\n\n"
        "На эту почту мы отправим 6-значный код подтверждения безопасности.",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 4: EMAIL И ОТПРАВКА КОДА
# =========================================================================

@router.message(RegistrationState.email, F.text)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip().lower()

    if not EMAIL_REGEX.match(email):
        await message.answer(
            "⚠️ <b>Некорректный формат email.</b>\n"
            "Пожалуйста, введите правильный адрес (например: <code>user@example.com</code>):",
            reply_markup=cancel_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # Генерируем 6-значный код
    code = f"{random.randint(100000, 999999)}"
    data = await state.get_data()
    user_name = data.get("first_name", "Пользователь")

    wait_msg = await message.answer(
        "⏳ <i>Отправляем проверочный код на вашу почту...</i>",
        parse_mode=ParseMode.HTML,
    )

    success, result_info = await send_verification_email(to_email=email, code=code, user_name=user_name)

    await state.update_data(
        email=email,
        email_code=code,
        code_time=time.time(),
        code_attempts=0,
    )
    await state.set_state(RegistrationState.email_code)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    if success:
        text = (
            f"📨 <b>Код подтверждения успешно отправлен!</b>\n\n"
            f"Мы отправили 6-значный проверочный код на <code>{email}</code>.\n"
            f"⏱ Код действителен 10 минут. Не забудьте проверить папку <i>«Спам»</i>.\n\n"
            f"<b>Введите 6-значный код из письма:</b>"
        )
    elif result_info == "NOT_CONFIGURED":
        # Если SMTP еще не настроен администратором в .env, выводим код прямо в боте для тестирования
        text = (
            f"📨 <b>Проверочный код сгенерирован!</b>\n\n"
            f"Почта: <code>{email}</code>\n"
            f"<i>(ℹ️ SMTP-сервер пока не настроен в .env, поэтому для теста код показан здесь)</i>\n\n"
            f"🔑 Ваш код: <b><code>{code}</code></b>\n\n"
            f"<b>Введите этот 6-значный код для продолжения:</b>"
        )
    else:
        text = (
            f"⚠️ <b>Не удалось отправить письмо через SMTP ({result_info})</b>.\n\n"
            f"Для тестирования используйте сгенерированный код: <b><code>{code}</code></b>\n\n"
            f"<b>Введите этот код:</b>"
        )

    await message.answer(
        text,
        reply_markup=email_verification_inline_markup(),
        parse_mode=ParseMode.HTML,
    )


# Повторная отправка кода по кнопке
@router.callback_query(RegistrationState.email_code, F.data == "resend_email_code")
async def resend_email_code_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    email = data.get("email")
    code_time = data.get("code_time", 0)

    # Cooldown 30 секунд
    now = time.time()
    if now - code_time < 30:
        remaining = int(30 - (now - code_time))
        await call.answer(f"Подождите {remaining} сек. перед повторной отправкой.", show_alert=True)
        return

    new_code = f"{random.randint(100000, 999999)}"
    user_name = data.get("first_name", "Пользователь")

    success, result_info = await send_verification_email(to_email=email, code=new_code, user_name=user_name)

    await state.update_data(
        email_code=new_code,
        code_time=now,
        code_attempts=0,
    )

    if success:
        text = (
            f"🔄 <b>Новый код отправлен на {email}!</b>\n\n"
            f"Введите полученный 6-значный проверочный код:"
        )
    elif result_info == "NOT_CONFIGURED":
        text = (
            f"🔄 <b>Новый тестовый код сгенерирован:</b> <b><code>{new_code}</code></b>\n\n"
            f"Введите его в чат:"
        )
    else:
        text = (
            f"⚠️ Ошибка SMTP: {result_info}\n"
            f"Код для тестирования: <b><code>{new_code}</code></b>"
        )

    await call.message.edit_text(
        text,
        reply_markup=email_verification_inline_markup(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer("Код отправлен повторно!")


# Изменение email в процессе подтверждения
@router.callback_query(RegistrationState.email_code, F.data == "change_reg_email")
async def change_reg_email_handler(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationState.email)
    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        "✏️ <b>Введите новый адрес электронной почты:</b>",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


# =========================================================================
#  ШАГ 5: ПРОВЕРКА КОДА EMAIL (EMAIL CODE)
# =========================================================================

@router.message(RegistrationState.email_code, F.text)
async def process_email_code(message: types.Message, state: FSMContext):
    user_input = message.text.strip().replace(" ", "")
    data = await state.get_data()
    expected_code = data.get("email_code")
    code_time = data.get("code_time", 0)
    attempts = data.get("code_attempts", 0) + 1
    await state.update_data(code_attempts=attempts)

    # Проверка на истечение времени (10 минут = 600 секунд)
    if time.time() - code_time > 600:
        await message.answer(
            "⏰ <b>Время действия кода истекло (10 минут).</b>\n"
            "Нажмите «🔄 Отправить код повторно» для получения нового кода.",
            reply_markup=email_verification_inline_markup(),
            parse_mode=ParseMode.HTML,
        )
        return

    if user_input != expected_code:
        if attempts >= 5:
            await message.answer(
                "❌ Слишком много неверных попыток ввода кода.\n"
                "Вы можете запросить новый код или изменить email:",
                reply_markup=email_verification_inline_markup(),
            )
            return

        await message.answer(
            f"❌ <b>Неверный код.</b> (Попытка {attempts} из 5)\n"
            "Пожалуйста, проверьте код из письма и введите его снова:",
            reply_markup=email_verification_inline_markup(),
            parse_mode=ParseMode.HTML,
        )
        return

    # Код верный!
    await state.update_data(is_email_verified=True)
    await state.set_state(RegistrationState.age)

    await message.answer(
        "🎉 <b>Email успешно подтвержден!</b> ✅\n\n"
        "Шаг <b>5 из 8</b>: <b>Укажите ваш возраст 🎂</b>\n"
        "<i>(Например: <code>25</code> или дата рождения <code>15.06.2001</code>. Либо нажмите «➡️ Пропустить»)</i>",
        reply_markup=skip_or_cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 6: ВОЗРАСТ (AGE)
# =========================================================================

@router.message(RegistrationState.age, F.text)
async def process_age(message: types.Message, state: FSMContext):
    text = message.text.strip()
    age = None

    if text not in ["➡️ Пропустить", "Пропустить", "-", "–"]:
        # Проверяем, введено ли число (возраст)
        if text.isdigit():
            val = int(text)
            if 10 <= val <= 110:
                age = val
            else:
                await message.answer(
                    "⚠️ Пожалуйста, укажите реалистичный возраст (от 10 до 110 лет) или нажмите «➡️ Пропустить»:",
                    reply_markup=skip_or_cancel_keyboard(),
                )
                return
        else:
            # Проверяем формат даты ДД.ММ.ГГГГ
            date_match = re.match(r"^(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})$", text)
            if date_match:
                year = int(date_match.group(3))
                current_year = 2026
                calculated_age = current_year - year
                if 10 <= calculated_age <= 110:
                    age = calculated_age
                else:
                    await message.answer(
                        "⚠️ Пожалуйста, проверьте год рождения или нажмите «➡️ Пропустить»:",
                        reply_markup=skip_or_cancel_keyboard(),
                    )
                    return
            else:
                await message.answer(
                    "⚠️ Пожалуйста, введите ваш возраст числом (например: <code>23</code>) "
                    "или нажмите «➡️ Пропустить»:",
                    reply_markup=skip_or_cancel_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
                return

    await state.update_data(age=age)
    await state.set_state(RegistrationState.gender)

    await message.answer(
        "Шаг <b>6 из 8</b>: <b>Укажите ваш пол 🚻</b>\n"
        "<i>(Выберите вариант с помощью кнопок ниже или пропустите)</i>",
        reply_markup=gender_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 7: ПОЛ (GENDER)
# =========================================================================

@router.message(RegistrationState.gender, F.text)
async def process_gender(message: types.Message, state: FSMContext):
    text = message.text.strip()
    gender = None

    if "Мужской" in text:
        gender = "Мужской"
    elif "Женский" in text:
        gender = "Женский"
    elif text in ["➡️ Пропустить", "Пропустить", "-", "–"]:
        gender = None
    else:
        await message.answer(
            "⚠️ Пожалуйста, выберите пол кнопкой «👨 Мужской» / «👩 Женский» или нажмите «❌ Отмена»:",
            reply_markup=gender_keyboard(),
        )
        return

    await state.update_data(gender=gender)
    await state.set_state(RegistrationState.location)

    await message.answer(
        "Шаг <b>7 из 8</b>: <b>Ваша локация или город 📍</b>\n\n"
        "• Нажмите <b>«📍 Поделиться геопозицией»</b> (с телефона)\n"
        "• Или просто напишите название вашего города текстом (например: <code>Ташкент</code>, <code>Самарканд</code>, <code>Москва</code>)\n"
        "• Или нажмите «➡️ Пропустить»:",
        reply_markup=location_share_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 8: ЛОКАЦИЯ (LOCATION)
# =========================================================================

@router.message(RegistrationState.location, F.location)
async def process_location_coords(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude

    wait_msg = await message.answer("📍 <i>Определяем адрес по координатам...</i>", parse_mode=ParseMode.HTML)
    address = await reverse_geocode(lat, lon)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    await state.update_data(
        location_lat=lat,
        location_lon=lon,
        location_address=address,
    )
    await state.set_state(RegistrationState.bio)

    await message.answer(
        f"📍 Определена локация: <b>{address}</b>\n\n"
        "Шаг <b>8 из 8</b>: <b>Расскажите немного о себе (О себе / Биография) 📝</b>\n\n"
        "Напишите пару слов о ваших интересах, профессии или хобби <i>(или нажмите «➡️ Пропустить»)</i>:",
        reply_markup=skip_or_cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(RegistrationState.location, F.text)
async def process_location_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    address = None if text in ["➡️ Пропустить", "➡️ Пропустить / Ввести город", "Пропустить", "-", "–"] else text

    await state.update_data(
        location_lat=None,
        location_lon=None,
        location_address=address,
    )
    await state.set_state(RegistrationState.bio)

    loc_str = f"<b>{address}</b>" if address else "<i>Не указана</i>"
    await message.answer(
        f"📍 Локация: {loc_str}\n\n"
        "Шаг <b>8 из 8</b>: <b>Расскажите немного о себе (О себе / Биография) 📝</b>\n\n"
        "Напишите пару слов о ваших интересах, профессии или хобби <i>(или нажмите «➡️ Пропустить»)</i>:",
        reply_markup=skip_or_cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ШАГ 9: О СЕБЕ (BIO) И ПРЕДПРОСМОТР АНКЕТЫ
# =========================================================================

@router.message(RegistrationState.bio, F.text)
async def process_bio(message: types.Message, state: FSMContext):
    text = message.text.strip()
    bio = None if text in ["➡️ Пропустить", "Пропустить", "-", "–"] else text
    if bio and len(bio) > 500:
        await message.answer(
            "⚠️ Пожалуйста, напишите краткое описание до 500 символов или нажмите «➡️ Пропустить»:",
            reply_markup=skip_or_cancel_keyboard(),
        )
        return

    await state.update_data(bio=bio)
    await state.set_state(RegistrationState.confirm)

    data = await state.get_data()
    first_name = data.get("first_name", "—")
    last_name = data.get("last_name") or "—"
    phone = data.get("phone", "—")
    email = data.get("email", "—")
    age = data.get("age") or "—"
    gender = data.get("gender") or "—"
    loc_address = data.get("location_address") or "—"
    bio_text = data.get("bio") or "—"

    preview_text = (
        "📋 <b>Пожалуйста, проверьте вашу анкету перед сохранением:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {first_name}\n"
        f"👥 <b>Фамилия:</b> {last_name}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"📧 <b>Email:</b> <code>{email}</code> (✅ Подтвержден)\n"
        f"🎂 <b>Возраст:</b> {age}\n"
        f"🚻 <b>Пол:</b> {gender}\n"
        f"📍 <b>Локация:</b> {loc_address}\n"
        f"📝 <b>О себе:</b> {bio_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Если всё верно, нажмите «✅ Всё верно, сохранить!».</i>"
    )

    await message.answer(
        preview_text,
        reply_markup=confirm_registration_inline_markup(),
        parse_mode=ParseMode.HTML,
    )


# =========================================================================
#  ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ И СОХРАНЕНИЕ
# =========================================================================

@router.callback_query(RegistrationState.confirm, F.data == "reg_confirm")
async def confirm_registration_callback(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = call.from_user.id
    username = call.from_user.username
    full_telegram_name = call.from_user.full_name

    first_name = data.get("first_name", call.from_user.first_name or "Пользователь")
    last_name = data.get("last_name")
    phone = data.get("phone")
    email = data.get("email")
    is_email_verified = data.get("is_email_verified", True)
    age = data.get("age")
    gender = data.get("gender")
    location_lat = data.get("location_lat")
    location_lon = data.get("location_lon")
    location_address = data.get("location_address")
    bio = data.get("bio")

    # Убеждаемся, что запись пользователя существует в БД
    await db.add_user(
        full_name=full_telegram_name,
        username=username,
        telegram_id=user_id,
    )

    # Сохраняем анкету
    await db.save_registration(
        telegram_id=user_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        is_email_verified=is_email_verified,
        age=age,
        gender=gender,
        location_lat=location_lat,
        location_lon=location_lon,
        location_address=location_address,
        bio=bio,
    )

    await state.clear()
    is_admin = str(user_id) in ADMINS

    try:
        await call.message.delete()
    except Exception:
        pass

    success_msg = (
        "🎉 <b>Поздравляем! Регистрация успешно завершена!</b>\n\n"
        f"Добро пожаловать в систему, <b>{first_name}</b>! ✨\n"
        "Теперь вам доступны все функции и удобное меню бота.\n\n"
        "Используйте кнопки меню ниже для управления вашим профилем и сервисами."
    )

    await call.message.answer(
        success_msg,
        reply_markup=get_main_menu(is_admin),
        parse_mode=ParseMode.HTML,
    )
    await call.answer("Профиль сохранен!")

    # Уведомление администраторам о новой регистрации
    admin_notify = (
        "🔔 <b>Новая регистрация в боте!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {first_name} {last_name or ''}\n"
        f"🔗 <b>Пользователь:</b> @{username or 'нет_username'} (ID: <code>{user_id}</code>)\n"
        f"📱 <b>Телефон:</b> <code>{phone or '—'}</code>\n"
        f"📧 <b>Email:</b> <code>{email or '—'}</code> (✅ Подтвержден)\n"
        f"🎂 <b>Возраст:</b> {age or '—'}\n"
        f"🚻 <b>Пол:</b> {gender or '—'}\n"
        f"📍 <b>Локация:</b> {location_address or '—'}\n"
        f"📝 <b>О себе:</b> {bio or '—'}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=admin, text=admin_notify, parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.warning(f"Не удалось уведомить админа {admin}: {exc}")


@router.callback_query(RegistrationState.confirm, F.data == "reg_restart")
async def restart_registration_callback(call: types.CallbackQuery, state: FSMContext):
    """Перезапуск процесса регистрации"""
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await start_registration_handler(call, state)
