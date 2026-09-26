from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.enums.parse_mode import ParseMode
from data.config import ADMINS

router = Router()


@router.message(Command("help"))
async def bot_help(message: types.Message):
    is_admin = str(message.from_user.id) in ADMINS

    lines = [
        "📖 <b>Полный справочник команд бота:</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔹 /start — Главное меню и запуск бота",
        "🔹 /profile — Мой персональный профиль",
        "🔹 /register — Начать или перезапустить регистрацию",
        "🔹 /edit — Редактировать поля анкеты",
        "🔹 /location — Просмотр сохраненной геопозиции",
        "🔹 /games — Мини-игры (Кубик, КНБ, Викторина, Орёл/Решка)",
        "🔹 /rpg — RPG-модуль (Герой, Мировой Босс, Инвентарь, PvP)",
        "🔹 /daily — Забрать ежедневную награду (Streak 7 дней)",
        "🔹 /ai — Вопрос интеллектуальному AI-ассистенту",
        "🔹 /code — Проверка синтаксиса Python-кода",
        "🔹 /social — Анонимный чат, друзья и глобальный ТОП",
        "🔹 /stats — Детальная личная и общая статистика",
        "🔹 /news — Лента новостей (Tech, Games, Python, AI, World)",
        "🔹 /cancel — Отмена любого текущего ввода",
        "🔹 /help — Показать эту справку",
    ]

    if is_admin:
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━",
            "👑 <b>Команды администратора:</b>",
            "🔸 /admin — Панель управления ботом и статистика",
            "🔸 /user &lt;id&gt; — Карточка пользователя по ID или @username",
            "🔸 /allusers — Выгрузить полную базу в Excel (.xlsx)",
            "🔸 /reklama — Массовая рассылка сообщений",
            "🔸 /cleandb — Очистить базу данных",
        ])

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>Всеми функциями также удобно управлять через кнопки меню внизу!</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
