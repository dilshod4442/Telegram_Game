from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class IsBotAdminFilter(BaseFilter):
    def __init__(self, user_ids: list):
        self.user_ids = [int(i) for i in user_ids if str(i).isdigit()]

    async def __call__(self, event: TelegramObject) -> bool:
        from_user = getattr(event, "from_user", None)
        if not from_user:
            return False
        return from_user.id in self.user_ids

