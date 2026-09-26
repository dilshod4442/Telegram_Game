from aiogram.fsm.state import StatesGroup, State


class AIState(StatesGroup):
    waiting_question = State()
    waiting_code = State()


class SocialState(StatesGroup):
    waiting_friend_id = State()
    waiting_anon_text = State()


class RPGState(StatesGroup):
    waiting_pvp_target = State()
