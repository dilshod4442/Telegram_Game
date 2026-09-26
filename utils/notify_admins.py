import logging
from aiogram import Bot
from data.config import ADMINS

logger = logging.getLogger(__name__)


async def on_startup_notify(bot: Bot):
    """Уведомление администраторов о запуске бота"""
    for admin in ADMINS:
        try:
            bot_properties = await bot.me()
            message = [
                "🚀 <b>Бот успешно запущен и готов к работе!</b>\n",
                f"🤖 <b>Bot Username:</b> @{bot_properties.username}",
                f"🆔 <b>Bot ID:</b> <code>{bot_properties.id}</code>",
                f"💾 <b>База данных:</b> PostgreSQL подключена",
            ]
            await bot.send_message(int(admin), "\n".join(message))
        except Exception as err:
            logger.warning(f"Не удалось отправить уведомление о запуске админу {admin}: {err}")
