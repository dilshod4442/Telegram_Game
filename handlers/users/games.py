import asyncio
import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

from loader import db, bot
from keyboards.inline.games import (
    games_main_markup,
    rps_markup,
    coinflip_markup,
    quiz_markup,
)
from keyboards.inline.rpg import rpg_menu_markup
from utils.misc.quiz_data import QUIZ_QUESTIONS

router = Router()


@router.message(Command("games"))
@router.message(F.text == "🎮 Игры и RPG")
@router.callback_query(F.data == "games:back")
async def show_games_menu(event: types.Message | types.CallbackQuery):
    text = (
        "🎮 <b>Игровой Центр и Мини-Игры</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Испытайте свою удачу, зарабатывайте монеты 💰 и прокачивайте уровень персонажа ⭐️!\n\n"
        "🎲 <b>Кубик</b> — бросьте кости против бота\n"
        "✊ <b>Камень-Ножницы-Бумага</b> — классическая дуэль\n"
        "❓ <b>Викторина</b> — проверьте знания по IT и Python\n"
        "🪙 <b>Орёл / Решка</b> — удвойте свою ставку\n"
        "⚔️ <b>RPG & Битва с Боссом</b> — прокачка героя, инвентарь и магазин\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Выберите игру ниже:</i>"
    )
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=games_main_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=games_main_markup(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=games_main_markup(), parse_mode=ParseMode.HTML)


# =========================================================================
#  1. КУБИК (DICE)
# =========================================================================

@router.callback_query(F.data == "game:dice")
async def play_dice(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    await call.message.answer("🎲 <b>Вы бросаете кубик...</b>", parse_mode=ParseMode.HTML)
    user_dice = await bot.send_dice(chat_id=chat_id, emoji="🎲")
    user_score = user_dice.dice.value

    await asyncio.sleep(2.5)

    await call.message.answer("🤖 <b>Бот бросает кубик...</b>", parse_mode=ParseMode.HTML)
    bot_dice = await bot.send_dice(chat_id=chat_id, emoji="🎲")
    bot_score = bot_dice.dice.value

    await asyncio.sleep(2.5)

    if user_score > bot_score:
        coins_reward = 35
        xp_reward = 20
        res_text = (
            f"🎉 <b>ПОБЕДА!</b>\n"
            f"Ваш результат: <b>{user_score}</b> | Бот: <b>{bot_score}</b>\n\n"
            f"🎁 Награда: <b>+{coins_reward} монет 💰</b> и <b>+{xp_reward} XP ⭐️</b>!"
        )
        await db.record_game(user_id, won=True, coins_delta=coins_reward, xp_delta=xp_reward, game_name="Кубик")
    elif user_score < bot_score:
        xp_reward = 5
        res_text = (
            f"😔 <b>Поражение!</b>\n"
            f"Ваш результат: <b>{user_score}</b> | Бот: <b>{bot_score}</b>\n\n"
            f"Утешительный бонус: <b>+{xp_reward} XP ⭐️</b>."
        )
        await db.record_game(user_id, won=False, coins_delta=0, xp_delta=xp_reward, game_name="Кубик")
    else:
        coins_reward = 10
        xp_reward = 10
        res_text = (
            f"🤝 <b>НИЧЬЯ!</b>\n"
            f"Оба выбросили <b>{user_score}</b>.\n\n"
            f"Бонус за ничью: <b>+{coins_reward} монет 💰</b> и <b>+{xp_reward} XP ⭐️</b>!"
        )
        await db.record_game(user_id, won=False, coins_delta=coins_reward, xp_delta=xp_reward, game_name="Кубик")

    await call.message.answer(res_text, reply_markup=games_main_markup(), parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  2. КАМЕНЬ - НОЖНИЦЫ - БУМАГА
# =========================================================================

@router.callback_query(F.data == "game:rps")
async def start_rps(call: types.CallbackQuery):
    await call.message.edit_text(
        "✊ <b>Камень, Ножницы, Бумага</b>\n\n"
        "Сделайте ваш выбор кнопкой ниже:",
        reply_markup=rps_markup(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("rps:"))
async def play_rps(call: types.CallbackQuery):
    user_choice = call.data.split(":")[1]
    bot_choice = random.choice(["rock", "scissors", "paper"])

    labels = {
        "rock": "🪨 Камень",
        "scissors": "✂️ Ножницы",
        "paper": "📄 Бумага",
    }

    user_label = labels.get(user_choice, user_choice)
    bot_label = labels.get(bot_choice, bot_choice)
    user_id = call.from_user.id

    if user_choice == bot_choice:
        res = "🤝 <b>Ничья!</b>"
        coins = 10
        xp = 10
        won = False
    elif (
        (user_choice == "rock" and bot_choice == "scissors")
        or (user_choice == "scissors" and bot_choice == "paper")
        or (user_choice == "paper" and bot_choice == "rock")
    ):
        res = "🎉 <b>Вы победили!</b>"
        coins = 40
        xp = 25
        won = True
    else:
        res = "😔 <b>Бот победил!</b>"
        coins = 0
        xp = 5
        won = False

    await db.record_game(user_id, won=won, coins_delta=coins, xp_delta=xp, game_name="КНБ")

    text = (
        f"✊ <b>Результат игры:</b>\n\n"
        f"Ваш ход: {user_label}\n"
        f"Ход бота: {bot_label}\n\n"
        f"{res}\n\n"
        f"🎁 <b>Награда:</b> +{coins} 💰 | +{xp} ⭐️ XP"
    )

    await call.message.edit_text(text, reply_markup=rps_markup(), parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  3. ОРЁЛ ИЛИ РЕШКА
# =========================================================================

@router.callback_query(F.data == "game:coinflip")
async def start_coinflip(call: types.CallbackQuery):
    user = await db.get_user(call.from_user.id)
    coins = user.get("coins", 0) if user else 0

    await call.message.edit_text(
        f"🪙 <b>Орёл или Решка</b>\n\n"
        f"Ваш текущий баланс: <b>{coins} монет 💰</b>\n"
        f"Ставка: <b>25 монет</b> (при победе вы получаете <b>+50 монет</b>!).\n\n"
        "На что ставите?",
        reply_markup=coinflip_markup(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("coin:"))
async def play_coinflip(call: types.CallbackQuery):
    choice = call.data.split(":")[1]
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    current_coins = user.get("coins", 0) if user else 0

    bet = 25
    if current_coins < bet:
        await call.answer("❌ У вас недостаточно монет для ставки (нужно 25)!", show_alert=True)
        return

    outcome = random.choice(["heads", "tails"])
    labels = {"heads": "🦅 Орёл", "tails": "🪙 Решка"}

    if choice == outcome:
        delta = bet
        xp = 25
        won = True
        status = "🎉 <b>Вы угадали и выиграли +50 монет!</b>"
    else:
        delta = -bet
        xp = 5
        won = False
        status = "😔 <b>Вы не угадали и потеряли ставку 25 монет.</b>"

    await db.record_game(user_id, won=won, coins_delta=delta, xp_delta=xp, game_name="Орёл/Решка")
    fresh_user = await db.get_user(user_id)

    text = (
        f"🪙 <b>Монета подброшена в воздух...</b>\n\n"
        f"Выпало: <b>{labels[outcome]}</b>!\n"
        f"Ваш выбор: <b>{labels[choice]}</b>\n\n"
        f"{status}\n\n"
        f"💰 Новый баланс: <b>{fresh_user.get('coins', 0)} монет</b>"
    )

    await call.message.edit_text(text, reply_markup=coinflip_markup(), parse_mode=ParseMode.HTML)
    await call.answer()


# =========================================================================
#  4. ВИКТОРИНА (QUIZ)
# =========================================================================

@router.callback_query(F.data == "game:quiz")
async def start_quiz(call: types.CallbackQuery):
    q = random.choice(QUIZ_QUESTIONS)
    text = (
        f"❓ <b>IT & Python Викторина</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Вопрос:</b> {q['question']}\n\n"
        f"💰 Награда за правильный ответ: <b>+50 монет</b> и <b>+30 XP</b>!\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(
        text,
        reply_markup=quiz_markup(q["id"], q["options"]),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("quiz_ans:"))
async def process_quiz_answer(call: types.CallbackQuery):
    parts = call.data.split(":")
    q_id = int(parts[1])
    ans_idx = int(parts[2])

    q = next((item for item in QUIZ_QUESTIONS if item["id"] == q_id), None)
    if not q:
        await call.answer("Вопрос устарел.", show_alert=True)
        return

    user_id = call.from_user.id
    if ans_idx == q["correct"]:
        await db.record_game(user_id, won=True, coins_delta=50, xp_delta=30, game_name="Викторина")
        result_text = (
            "🎉 <b>ПРАВИЛЬНО!</b>\n\n"
            f"✅ <i>{q['explanation']}</i>\n\n"
            "🎁 Награда: <b>+50 монет 💰</b> и <b>+30 XP ⭐️</b>!"
        )
    else:
        correct_answer = q["options"][q["correct"]]
        await db.record_game(user_id, won=False, coins_delta=0, xp_delta=5, game_name="Викторина")
        result_text = (
            "❌ <b>НЕВЕРНО!</b>\n\n"
            f"Правильный ответ: <b>{correct_answer}</b>\n"
            f"💡 <i>{q['explanation']}</i>\n\n"
            "Утешительный бонус: <b>+5 XP ⭐️</b>."
        )

    buttons = [
        [types.InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="game:quiz")],
        [types.InlineKeyboardButton(text="🔙 В меню игр", callback_data="games:back")],
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(result_text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await call.answer()
