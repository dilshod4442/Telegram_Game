from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from states.features import AIState
from utils.misc.ai_helper import ask_ai_assistant, analyze_python_code
from keyboards.reply.registration import cancel_keyboard

router = Router()


def ai_menu_markup() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🤖 AI Ассистент (Задать вопрос)",
                    callback_data="ai:ask_question",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="💻 Проверка Python-кода",
                    callback_data="ai:check_code",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="🔙 Главное меню",
                    callback_data="back_to_main",
                ),
            ],
        ]
    )


# =========================================================================
# AI HUB
# =========================================================================

@router.message(Command("ai"))
@router.message(F.text == "🧠 AI & Код")
@router.callback_query(F.data == "ai:menu")
async def ai_hub_handler(
    event: types.Message | types.CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    text = (
        "🧠 <b>Центр Искусственного Интеллекта и Анализа Кода</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Используйте мощные инструменты для решения задач и обучения:\n\n"
        "🤖 <b>AI Assistant</b> — задайте любой вопрос и получите развернутый структурированный ответ.\n"
        "💻 <b>Проверка Python-кода</b> — отправьте фрагмент кода для поиска синтаксических ошибок, багов и советов по рефакторингу.\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Выберите режим работы:</i>"
    )

    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(
                text,
                reply_markup=ai_menu_markup(),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await event.message.answer(
                text,
                reply_markup=ai_menu_markup(),
                parse_mode=ParseMode.HTML,
            )

        await event.answer()

    else:
        await event.answer(
            text,
            reply_markup=ai_menu_markup(),
            parse_mode=ParseMode.HTML,
        )


# =========================================================================
# 1. AI ASSISTANT
# =========================================================================

@router.callback_query(F.data == "ai:ask_question")
async def start_ai_question(
    call: types.CallbackQuery,
    state: FSMContext,
):
    await state.set_state(AIState.waiting_question)

    await call.message.answer(
        "🤖 <b>AI Assistant готов к вопросу!</b>\n\n"
        "Напишите любой интересующий вас вопрос "
        "(по программированию, технологиям, идеям или боту):\n"
        "<i>(Для отмены введите /cancel)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    await call.answer()


@router.message(AIState.waiting_question, F.text)
async def process_ai_question(
    message: types.Message,
    state: FSMContext,
):
    query = message.text.strip()

    if not query:
        await message.answer("❗ Введите вопрос.")
        return

    # Сообщение ожидания
    wait_msg = await message.answer(
        "🤔 <i>Нейросеть генерирует ответ...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        user_name = message.from_user.first_name or "Пользователь"

        # Получаем ответ Gemini
        reply = await ask_ai_assistant(
            query=query,
            user_name=user_name,
        )

    except Exception as e:
        try:
            await wait_msg.delete()
        except Exception:
            pass

        await message.answer(
            "❌ Не удалось получить ответ от AI.\n"
            "Попробуйте ещё раз через несколько секунд."
        )

        print(f"AI ERROR: {e}")
        return

    # Удаляем сообщение "генерирует ответ"
    try:
        await wait_msg.delete()
    except Exception:
        pass

    await state.clear()

    # ВАЖНО:
    # Ответ Gemini отправляем как ОБЫЧНЫЙ ТЕКСТ.
    # Никакого HTML/Markdown здесь нет.
    await message.answer(
        f"🤖 Ответ AI:\n\n{reply}",
        reply_markup=ai_menu_markup(),
        parse_mode=None,
    )


# =========================================================================
# 2. ПРОВЕРКА PYTHON КОДА
# =========================================================================

@router.message(Command("code"))
@router.callback_query(F.data == "ai:check_code")
async def start_code_check(
    event: types.Message | types.CallbackQuery,
    state: FSMContext,
):
    await state.set_state(AIState.waiting_code)

    text = (
        "💻 <b>Проверка и анализ Python-кода</b>\n\n"
        "Отправьте ваш Python-код текстовым сообщением. "
        "Бот проверит синтаксис, укажет точную строку ошибки "
        "и объяснит, как её исправить.\n"
        "<i>(Для отмены введите /cancel)</i>"
    )

    target = (
        event
        if isinstance(event, types.Message)
        else event.message
    )

    if isinstance(event, types.CallbackQuery):
        await event.answer()

    await target.answer(
        text,
        reply_markup=cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(AIState.waiting_code, F.text)
async def process_code_check(
    message: types.Message,
    state: FSMContext,
):
    code = message.text

    # Убираем Markdown code block:
    #
    # ```python
    # print("Hello")
    # ```
    #
    # превращается в:
    #
    # print("Hello")

    if code.startswith("```"):
        lines = code.split("\n")

        if len(lines) > 2:
            code = "\n".join(lines[1:-1])

    wait_msg = await message.answer(
        "🔍 <i>Анализируем синтаксис и структуру кода...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        analysis = await analyze_python_code(code)

    except Exception as e:
        try:
            await wait_msg.delete()
        except Exception:
            pass

        await message.answer(
            "❌ Не удалось проанализировать код.\n"
            "Попробуйте ещё раз."
        )

        print(f"CODE ANALYSIS ERROR: {e}")
        return

    try:
        await wait_msg.delete()
    except Exception:
        pass

    await state.clear()

    # Ответ Gemini тоже отправляем как обычный текст.
    # Поэтому < > ` и другие символы больше не ломают Telegram.
    await message.answer(
        f"💻 Результат анализа кода:\n\n{analysis}",
        reply_markup=ai_menu_markup(),
        parse_mode=None,
    )