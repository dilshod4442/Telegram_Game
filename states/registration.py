from aiogram.fsm.state import StatesGroup, State


class RegistrationState(StatesGroup):
    """Состояния FSM для пошаговой регистрации пользователя"""
    first_name = State()       # Имя
    last_name = State()        # Фамилия
    phone = State()            # Номер телефона
    email = State()            # Электронная почта
    email_code = State()       # 6-значный код из письма
    age = State()              # Возраст / дата рождения
    gender = State()           # Пол
    location = State()         # Геолокация / Город
    bio = State()              # О себе / биография
    confirm = State()          # Проверка и подтверждение анкеты


class EditProfileState(StatesGroup):
    """Состояния FSM для редактирования отдельных полей профиля"""
    select_field = State()
    waiting_value = State()
    waiting_email_code = State()
