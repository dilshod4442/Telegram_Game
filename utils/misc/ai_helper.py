import ast
import logging
from typing import Optional
from data import config

logger = logging.getLogger(__name__)


def check_python_syntax(code: str) -> dict:
    """Проверяет синтаксис Python-кода с помощью AST"""
    try:
        tree = ast.parse(code)
        # Дополнительный анализ частых ошибок
        warnings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        warnings.append(f"⚠️ В функции <code>{node.name}</code> используется изменяемый аргумент по умолчанию (mutable default). Рекомендуется использовать <code>None</code>.")
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    warnings.append("⚠️ Использование 'bare except:' перехватывает все исключения, включая KeyboardInterrupt. Рекомендуется указывать конкретный класс ошибки (например, Exception).")

        return {"valid": True, "warnings": warnings}
    except SyntaxError as e:
        return {
            "valid": False,
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text.strip() if e.text else "",
            "msg": e.msg,
        }


async def analyze_python_code(code: str) -> str:
    """Анализирует код пользователя и даёт подробное объяснение"""
    syntax_res = check_python_syntax(code)

    # Если есть Gemini API ключ, получаем ответ от нейросети
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            prompt = (
                "Ты профессиональный Senior Python-разработчик. Проанализируй следующий Python-код, "
                "найди синтаксические и логические ошибки, объясни их простым языком и покажи исправленный вариант кода.\n\n"
                f"Код:\n```python\n{code}\n```"
            )
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text
        except Exception as err:
            logger.warning(f"Ошибка вызова Gemini при анализе кода: {err}")

    # Локальный статический анализатор (работает без API-ключа)
    if not syntax_res["valid"]:
        line = syntax_res.get("line")
        offset = syntax_res.get("offset")
        bad_text = syntax_res.get("text")
        msg = syntax_res.get("msg")
        return (
            f"❌ <b>Обнаружена синтаксическая ошибка (SyntaxError)!</b>\n\n"
            f"📍 <b>Строка:</b> <code>{line}</code>, позиция: <code>{offset}</code>\n"
            f"🔍 <b>Фрагмент:</b> <code>{bad_text}</code>\n"
            f"⚠️ <b>Причина:</b> <i>{msg}</i>\n\n"
            "💡 <b>Совет по исправлению:</b>\n"
            "• Проверьте наличие двоеточия <code>:</code> в конце строк <code>if</code>, <code>def</code>, <code>for</code>, <code>while</code>, <code>class</code>\n"
            "• Убедитесь, что все круглые, квадратные и фигурные скобки закрыты\n"
            "• Проверьте соответствие отступов (4 пробела)"
        )
    else:
        warnings_str = ""
        if syntax_res.get("warnings"):
            warnings_str = "\n\n<b>Замечания по стилю и надежности:</b>\n" + "\n".join(syntax_res["warnings"])

        return (
            "✅ <b>Синтаксических ошибок не обнаружено!</b>\n"
            "Код успешно компилируется парсером Python."
            f"{warnings_str}\n\n"
            "💡 <i>(Для глубокого семантического анализа добавьте GEMINI_API_KEY в .env)</i>"
        )


async def ask_ai_assistant(query: str, user_name: str = "Пользователь") -> str:
    """Обрабатывает вопросы к AI-ассистенту"""
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            sys_instruction = (
                "Ты дружелюбный, умный и полезный AI-ассистент в Telegram-боте. "
                "Отвечай структурированно, грамотно и кратко, используй эмодзи и форматирование."
            )
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{sys_instruction}\n\nВопрос от {user_name}: {query}",
            )
            if response and response.text:
                return response.text
        except Exception as err:
            logger.warning(f"Ошибка вызова Gemini AI Assistant: {err}")

    # Встроенные ответы на популярные вопросы при отсутствии API-ключа
    q_low = query.lower()
    if any(k in q_low for k in ["привет", "здравствуй", "кто ты", "что умеешь"]):
        return (
            f"👋 Привет, {user_name}! Я встроенный интеллектуальный ассистент бота.\n\n"
            "Я могу помочь с вопросами по программированию на Python, мини-играм, RPG-механикам "
            "и использованию бота!\n\n"
            "💡 <i>Для подключения нейросети Gemini укажите GEMINI_API_KEY в файле .env.</i>"
        )
    elif "python" in q_low or "питон" in q_low:
        return (
            "🐍 <b>Python</b> — высокоуровневый язык программирования с акцентом на читаемость кода.\n\n"
            "• Отправьте код через <b>💻 Проверка кода</b> для проверки синтаксиса.\n"
            "• Этот бот написан на <b>Python 3.12 + Aiogram 3</b>!\n\n"
            "💡 Задайте более конкретный вопрос или пришлите фрагмент кода."
        )
    else:
        return (
            f"🤖 <b>Ответ ассистента:</b>\n\n"
            f"Вы спросили: <i>«{query}»</i>\n\n"
            "Спасибо за ваш вопрос! Чтобы получить подробный ответ от нейросети в реальном времени, "
            "пожалуйста, настройте <code>GEMINI_API_KEY</code> в файле конфигурации <code>.env</code>."
        )
