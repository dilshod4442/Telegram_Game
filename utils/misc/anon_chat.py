from typing import Optional, Dict, Set
import asyncio

# Хранилище в памяти
_search_queue: Set[int] = set()
_active_chats: Dict[int, int] = {}


def start_search(user_id: int) -> Optional[int]:
    """
    Добавляет пользователя в очередь поиска.
    Если в очереди есть другой пользователь, соединяет их и возвращает ID партнера.
    """
    if user_id in _active_chats:
        end_chat(user_id)

    # Ищем партнера, не равного текущему
    for partner_id in list(_search_queue):
        if partner_id != user_id:
            _search_queue.remove(partner_id)
            _active_chats[user_id] = partner_id
            _active_chats[partner_id] = user_id
            return partner_id

    _search_queue.add(user_id)
    return None


def stop_search(user_id: int):
    """Удаляет пользователя из очереди поиска"""
    _search_queue.discard(user_id)


def get_partner(user_id: int) -> Optional[int]:
    """Возвращает ID собеседника в активном анонимном чате"""
    return _active_chats.get(user_id)


def end_chat(user_id: int) -> Optional[int]:
    """Завершает активный анонимный диалог"""
    partner_id = _active_chats.pop(user_id, None)
    if partner_id:
        _active_chats.pop(partner_id, None)
    _search_queue.discard(user_id)
    return partner_id


def is_in_chat(user_id: int) -> bool:
    return user_id in _active_chats
