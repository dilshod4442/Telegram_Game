from aiogram import Router
from filters import ChatPrivateFilter


def setup_routers() -> Router:
    from .users import (
        admin,
        registration,
        profile,
        games,
        rpg,
        daily,
        ai_features,
        social,
        stats,
        news,
        menu,
        start,
        help,
        echo,
    )
    from .errors import error_handler

    router = Router()

    # Фильтр только личных чатов для основных веток
    router.message.filter(ChatPrivateFilter(chat_type=["private"]))

    # Подключаем роутеры в строгом порядке приоритетов
    router.include_routers(
        admin.router,
        registration.router,
        profile.router,
        games.router,
        rpg.router,
        daily.router,
        ai_features.router,
        social.router,
        stats.router,
        news.router,
        menu.router,
        start.router,
        help.router,
        echo.router,
        error_handler.router,
    )

    return router
