from aiogram import Bot
from aiogram.methods.set_my_commands import BotCommand
from aiogram.types import BotCommandScopeAllPrivateChats


async def set_default_commands(bot: Bot):
    """Установка списка команд бота в Telegram"""
    commands = [
        BotCommand(command="start", description="Главное меню / Старт"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="games", description="Мини-игры и RPG"),
        BotCommand(command="daily", description="Ежедневная награда"),
        BotCommand(command="ai", description="AI-ассистент"),
        BotCommand(command="code", description="Проверка Python-кода"),
        BotCommand(command="social", description="Анонимный чат и друзья"),
        BotCommand(command="stats", description="Статистика и расходы"),
        BotCommand(command="news", description="IT-новости"),
        BotCommand(command="help", description="Помощь и команды"),
        BotCommand(command="cancel", description="Отмена действия"),
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
