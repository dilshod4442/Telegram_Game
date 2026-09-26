QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Какой тип данных в Python является неизменяемым (immutable)?",
        "options": ["list", "tuple", "dict", "set"],
        "correct": 1,  # tuple
        "explanation": "Кортежи (tuple), строки (str) и числа (int/float) в Python неизменяемы.",
    },
    {
        "id": 2,
        "question": "Что выведет выражение bool([]) в Python?",
        "options": ["True", "False", "None", "Error"],
        "correct": 1,  # False
        "explanation": "Пустые коллекции (списки, строки, словари) приводятся к False.",
    },
    {
        "id": 3,
        "question": "Какой HTTP метод используется для полного обновления ресурса по стандарту REST?",
        "options": ["GET", "POST", "PUT", "PATCH"],
        "correct": 2,  # PUT
        "explanation": "PUT используется для полной замены/создания ресурса, а PATCH — для частичного обновления.",
    },
    {
        "id": 4,
        "question": "Какая временная сложность поиска элемента по ключу в словаре Python (dict) в среднем?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
        "correct": 0,  # O(1)
        "explanation": "Словари в Python реализованы через хеш-таблицы, поэтому среднее время поиска составляет O(1).",
    },
    {
        "id": 5,
        "question": "Какой декоратор используется в Aiogram 3 для регистрации команды /start?",
        "options": ["@dp.message_handler()", "@router.message(CommandStart())", "@bot.on_start()", "@app.route('/start')"],
        "correct": 1,  # @router.message(CommandStart())
        "explanation": "В Aiogram 3 используются роутеры и фильтр CommandStart() из aiogram.filters.",
    },
    {
        "id": 6,
        "question": "Какой порт по умолчанию используется СУБД PostgreSQL?",
        "options": ["3306", "5432", "27017", "6379"],
        "correct": 1,  # 5432
        "explanation": "По умолчанию PostgreSQL слушает порт 5432 (3306 — MySQL, 6379 — Redis).",
    },
]
