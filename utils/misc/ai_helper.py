import ast
import asyncio
import logging
from typing import Optional

from data import config

logger = logging.getLogger(__name__)


# ============================================================
# GEMINI
# ============================================================

GEMINI_MODEL = "gemini-3.7-flash"
GEMINI_MAX_ATTEMPTS = 3


async def generate_gemini_response(prompt: str) -> Optional[str]:
    """
    Отправляет запрос в Gemini с повторными попытками.

    Если Gemini вернул ошибку 503 или другую временную ошибку,
    бот попробует запрос ещё несколько раз.
    """

    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY не настроен")
        return None

    try:
        from google import genai

        client = genai.Client(
            api_key=config.GEMINI_API_KEY
        )

    except Exception as err:
        logger.error(
            f"Не удалось создать Gemini client: {err}"
        )
        return None

    for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
        try:
            logger.info(
                f"Запрос к Gemini: попытка "
                f"{attempt}/{GEMINI_MAX_ATTEMPTS}"
            )

            # generate_content синхронный,
            # поэтому запускаем его в отдельном потоке,
            # чтобы не блокировать aiogram.
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt,
            )

            if response and response.text:
                logger.info(
                    f"Gemini успешно ответил с попытки {attempt}"
                )
                return response.text

            logger.warning(
                f"Gemini вернул пустой ответ. "
                f"Попытка {attempt}/{GEMINI_MAX_ATTEMPTS}"
            )

        except Exception as err:
            logger.warning(
                f"Ошибка Gemini. "
                f"Попытка {attempt}/{GEMINI_MAX_ATTEMPTS}: {err}"
            )

            # Если это была не последняя попытка,
            # ждём перед повторным запросом.
            if attempt < GEMINI_MAX_ATTEMPTS:
                delay = 2 ** (attempt - 1)

                logger.info(
                    f"Повторная попытка через {delay} сек."
                )

                await asyncio.sleep(delay)

    logger.error(
        "Gemini не ответил после всех попыток"
    )

    return None


# ============================================================
# PYTHON SYNTAX CHECK
# ============================================================

def check_python_syntax(code: str) -> dict:
    """
    Проверяет синтаксис Python-кода с помощью AST.
    """

    try:
        tree = ast.parse(code)

        warnings = []

        for node in ast.walk(tree):

            # Проверяем mutable default arguments
            if isinstance(node, ast.FunctionDef):

                for default in node.args.defaults:

                    if isinstance(
                        default,
                        (ast.List, ast.Dict, ast.Set)
                    ):
                        warnings.append(
                            f"⚠️ В функции "
                            f"<code>{node.name}</code> "
                            f"используется изменяемый аргумент "
                            f"по умолчанию (mutable default). "
                            f"Рекомендуется использовать "
                            f"<code>None</code>."
                        )

            # Проверяем bare except
            if isinstance(node, ast.ExceptHandler):

                if node.type is None:
                    warnings.append(
                        "⚠️ Использование "
                        "'bare except:' перехватывает все "
                        "исключения, включая KeyboardInterrupt. "
                        "Рекомендуется указывать конкретный "
                        "класс ошибки "
                        "(например, Exception)."
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
            "text": e.text.strip() if e.text else "",
            "msg": e.msg,
        }


# ============================================================
# PYTHON CODE ANALYZER
# ============================================================

async def analyze_python_code(code: str) -> str:
    """
    Анализирует Python-код пользователя.

    Сначала выполняется локальная проверка AST.
    Затем Gemini пытается сделать глубокий анализ.
    """

    syntax_res = check_python_syntax(code)

    # --------------------------------------------------------
    # GEMINI ANALYSIS
    # --------------------------------------------------------

    if config.GEMINI_API_KEY:

        prompt = (
            "Ты профессиональный Senior Python-разработчик.\n\n"
            "Проанализируй следующий Python-код.\n\n"
            "Твоя задача:\n"
            "1. Найти синтаксические ошибки.\n"
            "2. Найти логические ошибки.\n"
            "3. Найти потенциальные баги.\n"
            "4. Объяснить ошибки простым языком.\n"
            "5. Показать исправленный вариант кода.\n"
            "6. Если код правильный — объяснить, почему он работает.\n\n"
            "Отвечай структурированно и понятно.\n\n"
            f"Код:\n```python\n{code}\n```"
        )

        ai_response = await generate_gemini_response(
            prompt
        )

        if ai_response:
            return ai_response

    # --------------------------------------------------------
    # LOCAL STATIC ANALYZER
    # --------------------------------------------------------

    if not syntax_res["valid"]:

        line = syntax_res.get("line")
        offset = syntax_res.get("offset")
        bad_text = syntax_res.get("text")
        msg = syntax_res.get("msg")

        return (
            "❌ <b>Обнаружена синтаксическая ошибка "
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

            "• Проверьте наличие двоеточия "
            "<code>:</code> после "
            "<code>if</code>, "
            "<code>def</code>, "
            "<code>for</code>, "
            "<code>while</code>, "
            "<code>class</code>\n"

            "• Убедитесь, что все круглые, "
            "квадратные и фигурные скобки закрыты\n"

            "• Проверьте правильность отступов "
            "(обычно 4 пробела)"
        )

    # --------------------------------------------------------
    # CODE IS VALID
    # --------------------------------------------------------

    warnings_str = ""

    if syntax_res.get("warnings"):

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

        "💡 <i>Gemini временно недоступен, "
        "поэтому выполнена локальная "
        "проверка Python-кода.</i>"
    )


# ============================================================
# AI ASSISTANT
# ============================================================

async def ask_ai_assistant(
    query: str,
    user_name: str = "Пользователь"
) -> str:
    """
    Обрабатывает вопросы пользователя через Gemini.
    """

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    if config.GEMINI_API_KEY:

        sys_instruction = (
            "Ты дружелюбный, умный и полезный "
            "AI-ассистент в Telegram-боте.\n\n"

            "Отвечай структурированно, грамотно "
            "и понятно.\n"

            "Используй эмодзи там, где это уместно.\n"

            "Если пользователь спрашивает "
            "о программировании — показывай код "
            "и объясняй его.\n"

            "Если вопрос сложный — разбивай ответ "
            "на простые шаги."
        )

        prompt = (
            f"{sys_instruction}\n\n"
            f"Вопрос от {user_name}:\n"
            f"{query}"
        )

        ai_response = await generate_gemini_response(
            prompt
        )

        if ai_response:
            return ai_response

        # Gemini был настроен, но временно не ответил
        return (
            "⚠️ <b>Gemini временно недоступен.</b>\n\n"
            "Я попробовал отправить запрос "
            "несколько раз, но сервис пока "
            "не ответил.\n\n"
            "🔄 Попробуйте отправить вопрос "
            "ещё раз через несколько секунд."
        )

    # --------------------------------------------------------
    # FALLBACK БЕЗ GEMINI
    # --------------------------------------------------------

    q_low = query.lower()

    if any(
        k in q_low
        for k in [
            "привет",
            "здравствуй",
            "кто ты",
            "что умеешь"
        ]
    ):

        return (
            f"👋 Привет, {user_name}!\n\n"

            "Я встроенный интеллектуальный "
            "ассистент бота.\n\n"

            "Я могу помочь с:\n"
            "🐍 Python\n"
            "🤖 программированием\n"
            "🎮 мини-играми\n"
            "⚔️ RPG-механиками\n"
            "💡 идеями для проектов\n"
            "🧠 различными вопросами"
        )

    elif (
        "python" in q_low
        or "питон" in q_low
    ):

        return (
            "🐍 <b>Python</b> — "
            "высокоуровневый язык программирования "
            "с простым и читаемым синтаксисом.\n\n"

            "Ты можешь отправить Python-код "
            "через кнопку:\n\n"

            "💻 <b>Проверка Python-кода</b>\n\n"

            "Там бот проверит синтаксис "
            "и найдёт распространённые ошибки."
        )

    else:

        return (
            "🤖 <b>AI Assistant</b>\n\n"

            "Сейчас нейросеть Gemini "
            "не подключена.\n\n"

            "Для работы AI необходимо указать "
            "<code>GEMINI_API_KEY</code> "
            "в конфигурации."
        )