from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

from keyboards.inline.news import news_categories_markup, news_detail_markup
from utils.misc.news_data import get_news_by_category

router = Router()

CAT_NAMES = {
    "tech": "🚀 Технологии",
    "games": "🎮 Игры",
    "python": "🐍 Python",
    "ai": "🤖 Искусственный интеллект",
    "world": "🌍 В мире",
}


@router.message(Command("news"))
@router.message(F.text.in_({"📰 Новости", "Новости", "новости"}))
@router.callback_query(F.data == "news:back")
async def show_news_categories(event: types.Message | types.CallbackQuery):
    text = (
        "📰 <b>Лента новостей и технологических трендов</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите интересующую вас категорию статей и дайджестов:\n\n"
        "• <b>🚀 Технологии</b> — гаджеты, чипы, интернет\n"
        "• <b>🎮 Игры</b> — релизы, индустрия, киберспорт\n"
        "• <b>🐍 Python</b> — обновления языка, библиотеки, фичи\n"
        "• <b>🤖 AI</b> — нейросети, LLM, автоматизация\n"
        "• <b>🌍 В мире</b> — главные мировые события науки и жизни\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=news_categories_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=news_categories_markup(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=news_categories_markup(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("news:cat:"))
async def show_news_list(call: types.CallbackQuery):
    cat = call.data.split(":")[2]
    cat_title = CAT_NAMES.get(cat, "Новости")
    articles = get_news_by_category(cat)

    if not articles:
        await call.answer("В этой категории пока нет новостей.", show_alert=True)
        return

    lines = [f"📰 <b>{cat_title}</b>\n━━━━━━━━━━━━━━━━━━━━━"]
    for a in articles:
        lines.append(f"📌 <b>{a['title']}</b>")
        lines.append(f"🗓 <i>{a['date']}</i>")
        lines.append(f"{a['summary']}\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=news_detail_markup(),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()
