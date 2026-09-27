import ast
import asyncio
import logging
from typing import Optional

from data import config


logger = logging.getLogger(__name__)


# ============================================================
# GEMINI SETTINGS
# ============================================================

# Модели идут по порядку.
# Если первая временно недоступна — пробуем следующую.
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]

# Сколько раз пробовать одну модель
GEMINI_ATTEMPTS_PER_MODEL = 2

# Сколько секунд ждать между попытками
GEMINI_RETRY_DELAY = 2


# ============================================================
# GEMINI CLIENT
# ============================================================

def create_gemini_client():
    """
    Создаёт Gemini client.
    """

    if not config.GEMINI_API_KEY:
        logger.warning(
            "GEMINI_API_KEY не настроен."
        )
        return None

    try:
        from google import genai

        client = genai.Client(
            api_key=config.GEMINI_API_KEY
        )

        return client

    except Exception as err:
        logger.error(
            f"Ошибка создания Gemini client: {err}"
        )

        return None


# ============================================================
# GEMINI REQUEST
# ============================================================

async def generate_gemini_response(
    prompt: str
) -> Optional[str]:
    """
    Отправляет запрос в Gemini.

    Использует несколько моделей.
    Если одна модель возвращает ошибку,
    автоматически пробует следующую.

    Также используется retry для временных ошибок 503/429.
    """

    client = create_gemini_client()

    if client is None:
        return None

    # --------------------------------------------------------
    # ПРОБУЕМ МОДЕЛИ ПО ОЧЕРЕДИ
    # --------------------------------------------------------

    for model in GEMINI_MODELS:

        logger.info(
            f"🤖 Пробуем Gemini модель: {model}"
        )

        # ----------------------------------------------------
        # RETRY ДЛЯ ОДНОЙ МОДЕЛИ
        # ----------------------------------------------------

        for attempt in range(
            1,
            GEMINI_ATTEMPTS_PER_MODEL + 1
        ):

            try:

                logger.info(
                    f"Gemini {model}: "
                    f"попытка "
                    f"{attempt}/"
                    f"{GEMINI_ATTEMPTS_PER_MODEL}"
                )

                # generate_content является синхронным
                # методом SDK.
                #
                # Поэтому запускаем его в отдельном
                # потоке, чтобы Telegram-бот
                # не зависал во время запроса.
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                )

                # ------------------------------------------------
                # УСПЕШНЫЙ ОТВЕТ
                # ------------------------------------------------

                if response and response.text:

                    logger.info(
                        f"✅ Gemini успешно ответил. "
                        f"Модель: {model}"
                    )

                    return response.text

                logger.warning(
                    f"⚠️ Gemini вернул пустой ответ. "
                    f"Модель: {model}"
                )

            except Exception as err:

                error_text = str(err)

                logger.warning(
                    f"❌ Ошибка Gemini.\n"
                    f"Модель: {model}\n"
                    f"Попытка: "
                    f"{attempt}/"
                    f"{GEMINI_ATTEMPTS_PER_MODEL}\n"
                    f"Ошибка: {error_text}"
                )

                # --------------------------------------------
                # ЕСЛИ ЕСТЬ ЕЩЁ ПОПЫТКА
                # --------------------------------------------

                if attempt < GEMINI_ATTEMPTS_PER_MODEL:

                    logger.info(
                        f"🔄 Повторяем запрос "
                        f"через {GEMINI_RETRY_DELAY} сек."
                    )

                    await asyncio.sleep(
                        GEMINI_RETRY_DELAY
                    )

        # ----------------------------------------------------
        # МОДЕЛЬ НЕ ОТВЕТИЛА
        # ----------------------------------------------------

        logger.warning(
            f"⚠️ Модель {model} недоступна. "
            f"Переходим к следующей модели."
        )

    # --------------------------------------------------------
    # ВСЕ МОДЕЛИ НЕ ОТВЕТИЛИ
    # --------------------------------------------------------

    logger.error(
        "❌ Все Gemini модели недоступны."
    )

    return None


# ============================================================
# PYTHON SYNTAX CHECK
# ============================================================

def check_python_syntax(
    code: str
) -> dict:
    """
    Проверяет синтаксис Python-кода
    с помощью AST.
    """

    try:

        tree = ast.parse(code)

        warnings = []

        # ----------------------------------------------------
        # ПРОВЕРКА AST
        # ----------------------------------------------------

        for node in ast.walk(tree):

            # -----------------------------------------------
            # MUTABLE DEFAULT ARGUMENTS
            # -----------------------------------------------

            if isinstance(
                node,
                ast.FunctionDef
            ):

                for default in node.args.defaults:

                    if isinstance(
                        default,
                        (
                            ast.List,
                            ast.Dict,
                            ast.Set
                        )
                    ):

                        warnings.append(
                            f"⚠️ В функции "
                            f"<code>{node.name}</code> "
                            f"используется изменяемый "
                            f"аргумент по умолчанию "
                            f"(mutable default).\n"
                            f"Рекомендуется использовать "
                            f"<code>None</code>."
                        )

            # -----------------------------------------------
            # BARE EXCEPT
            # -----------------------------------------------

            if isinstance(
                node,
                ast.ExceptHandler
            ):

                if node.type is None:

                    warnings.append(
                        "⚠️ Использование "
                        "'bare except:' "
                        "перехватывает все исключения, "
                        "включая KeyboardInterrupt.\n"
                        "Рекомендуется указывать "
                        "конкретный класс ошибки, "
                        "например "
                        "<code>Exception</code>."
                    )

        return {
            "valid": True,
            "warnings": warnings
        }

    except SyntaxError as e:

        return {
            "valid": False,
            "line": e.lineno,
            "offset": e.offset,
            "text": (
                e.text.strip()
                if e.text
                else ""
            ),
            "msg": e.msg,
        }


# ============================================================
# PYTHON CODE ANALYZER
# ============================================================

async def analyze_python_code(
    code: str
) -> str:
    """
    Анализирует Python-код пользователя.

    Сначала выполняется локальная проверка
    синтаксиса.

    Затем Gemini делает глубокий анализ.
    """

    # --------------------------------------------------------
    # LOCAL AST CHECK
    # --------------------------------------------------------

    syntax_res = check_python_syntax(code)

    # --------------------------------------------------------
    # GEMINI ANALYSIS
    # --------------------------------------------------------

    if config.GEMINI_API_KEY:

        prompt = (
            "Ты профессиональный Senior "
            "Python-разработчик.\n\n"

            "Проанализируй следующий Python-код.\n\n"

            "Твоя задача:\n"

            "1. Найди синтаксические ошибки.\n"

            "2. Найди логические ошибки.\n"

            "3. Найди потенциальные баги.\n"

            "4. Объясни ошибки простым языком.\n"

            "5. Покажи исправленный вариант кода.\n"

            "6. Если код правильный — объясни, "
            "почему он работает.\n\n"

            "Отвечай структурированно "
            "и понятно.\n\n"

            f"Код:\n"
            f"```python\n"
            f"{code}\n"
            f"```"
        )

        ai_response = await generate_gemini_response(
            prompt
        )

        if ai_response:

            return ai_response

    # --------------------------------------------------------
    # LOCAL ANALYSIS IF GEMINI FAILED
    # --------------------------------------------------------

    if not syntax_res["valid"]:

        line = syntax_res.get(
            "line"
        )

        offset = syntax_res.get(
            "offset"
        )

        bad_text = syntax_res.get(
            "text"
        )

        msg = syntax_res.get(
            "msg"
        )

        return (
            "❌ <b>Обнаружена "
            "синтаксическая ошибка "
            "(SyntaxError)!</b>\n\n"

            f"📍 <b>Строка:</b> "
            f"<code>{line}</code>\n"

            f"📌 <b>Позиция:</b> "
            f"<code>{offset}</code>\n"

            f"🔍 <b>Фрагмент:</b> "
            f"<code>{bad_text}</code>\n"

            f"⚠️ <b>Причина:</b> "
            f"<i>{msg}</i>\n\n"

            "💡 <b>Совет по исправлению:</b>\n"

            "• Проверьте наличие "
            "двоеточия <code>:</code> "
            "после <code>if</code>, "
            "<code>def</code>, "
            "<code>for</code>, "
            "<code>while</code>, "
            "<code>class</code>\n"

            "• Убедитесь, что все "
            "круглые, квадратные и "
            "фигурные скобки закрыты\n"

            "• Проверьте правильность "
            "отступов "
            "(обычно 4 пробела)"
        )

    # --------------------------------------------------------
    # CODE IS VALID
    # --------------------------------------------------------

    warnings_str = ""

    if syntax_res.get(
        "warnings"
    ):

        warnings_str = (
            "\n\n"
            "<b>⚠️ Замечания по стилю "
            "и надёжности:</b>\n"
            + "\n".join(
                syntax_res["warnings"]
            )
        )

    return (
        "✅ <b>Синтаксических ошибок "
        "не обнаружено!</b>\n\n"

        "Код успешно разбирается "
        "парсером Python."

        f"{warnings_str}\n\n"

        "💡 <i>Gemini временно "
        "недоступен, поэтому выполнена "
        "локальная проверка Python-кода.</i>"
    )


# ============================================================
# AI ASSISTANT
# ============================================================

async def ask_ai_assistant(
    query: str,
    user_name: str = "Пользователь"
) -> str:
    """
    Обрабатывает вопрос пользователя
    через Gemini.
    """

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    if config.GEMINI_API_KEY:

        system_instruction = (
            "Ты дружелюбный, умный и полезный "
            "AI-ассистент в Telegram-боте.\n\n"

            "Отвечай структурированно, "
            "грамотно и понятно.\n\n"

            "Используй эмодзи там, где "
            "это уместно.\n\n"

            "Если пользователь спрашивает "
            "о программировании — показывай "
            "код и объясняй его.\n\n"

            "Если вопрос сложный — разбивай "
            "ответ на простые шаги.\n\n"

            "Не говори пользователю, что "
            "ты не настоящий AI.\n\n"

            "Не придумывай факты. Если "
            "не уверен — честно скажи об этом."
        )

        prompt = (
            f"{system_instruction}\n\n"

            f"Имя пользователя: "
            f"{user_name}\n\n"

            f"Вопрос пользователя:\n"
            f"{query}"
        )

        ai_response = await generate_gemini_response(
            prompt
        )

        if ai_response:

            return ai_response

        # ----------------------------------------------------
        # GEMINI НЕ ОТВЕТИЛ
        # ----------------------------------------------------

        return (
            "⚠️ <b>AI временно перегружен.</b>\n\n"

            "Я попробовал несколько Gemini-моделей, "
            "но ни одна сейчас не ответила.\n\n"

            "🔄 Попробуйте отправить вопрос "
            "ещё раз через несколько секунд."
        )

    # --------------------------------------------------------
    # FALLBACK WITHOUT API KEY
    # --------------------------------------------------------

    q_low = query.lower()

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    if any(
        word in q_low
        for word in [
            "привет",
            "здравствуй",
            "кто ты",
            "что умеешь"
        ]
    ):

        return (
            f"👋 <b>Привет, {user_name}!</b>\n\n"

            "Я встроенный AI-ассистент "
            "твоего Telegram-бота.\n\n"

            "Я могу помочь с:\n"
            "🐍 Python\n"
            "💻 программированием\n"
            "🎮 играми\n"
            "⚔️ RPG-механиками\n"
            "💡 идеями для проектов\n"
            "🧠 разными вопросами"
        )

    # --------------------------------------------------------
    # PYTHON
    # --------------------------------------------------------

    elif (
        "python" in q_low
        or "питон" in q_low
    ):

        return (
            "🐍 <b>Python</b> — "
            "высокоуровневый язык "
            "программирования.\n\n"

            "Ты можешь отправить Python-код "
            "через кнопку:\n\n"

            "💻 <b>Проверка Python-кода</b>\n\n"

            "Бот проверит синтаксис "
            "и распространённые ошибки."
        )

    # --------------------------------------------------------
    # DEFAULT FALLBACK
    # --------------------------------------------------------

    return (
        "🤖 <b>AI Assistant</b>\n\n"

        "Gemini API сейчас не настроен.\n\n"

        "Добавьте "
        "<code>GEMINI_API_KEY</code> "
        "в переменные окружения."
    )