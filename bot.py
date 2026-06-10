"""
🧘 ERP Yoga Bot (@SAPyogaBOT)
Keep Calm and Get Advice

Стек: aiogram 3.x · FSM · Claude API
Деплой: Railway (Dockerfile в корне)
"""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from ai_service import get_ai_recommendation, get_partner_advice
from data import get_top3, get_visible_steps, format_top3_text, build_plain_brief

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

ITEMS_PER_PAGE = 8


# ── FSM ──────────────────────────────────────────────────────────────────────

class Survey(StatesGroup):
    question = State()   # анкета
    region   = State()   # опциональный вопрос о регионе для поиска партнёров
    result   = State()   # показан результат, ждём действий


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def _opts_kbd(opts: list[str], q_type: str, selected: list[str],
              page: int = 0, step_idx: int = 0) -> InlineKeyboardMarkup:
    """callback_data = opt:{step_idx}:{opt_idx} — числовые индексы, макс. ~10 байт."""
    start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    rows = []

    for abs_idx in range(start, min(end, len(opts))):
        opt = opts[abs_idx]
        prefix = "✅ " if opt in selected else ""
        rows.append([InlineKeyboardButton(
            text=prefix + opt,
            callback_data=f"opt:{step_idx}:{abs_idx}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"page:{page-1}"))
    if end < len(opts):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"page:{page+1}"))
    if nav:
        rows.append(nav)

    if q_type == "multi":
        rows.append([InlineKeyboardButton(text="✔️ Готово", callback_data="done")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _result_kbd() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать бриф",          callback_data="copy_brief")],
        [InlineKeyboardButton(text="🌍 Найти партнёров в регионе", callback_data="find_partners")],
        [InlineKeyboardButton(text="🔄 Пройти заново",             callback_data="restart")],
    ])


def _back_kbd() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="restart")]
    ])


# ── Step rendering ────────────────────────────────────────────────────────────

BLOCK_LABELS = {
    "main":    "📊 Профиль проекта",
    "infra":   "🏢 Инфраструктура",
    "partner": "🤝 Подбор партнёра",
}


def _step_text(step: dict, num: int, total: int, selected: list[str]) -> str:
    block   = BLOCK_LABELS.get(step.get("block", "main"), "")
    sub     = f"\n_{step['sub']}_" if step.get("sub") else ""
    sel_txt = ""
    if step["type"] == "multi" and selected:
        sel_txt = "\n\n*Выбрано:* " + ", ".join(selected)
    return f"*{block}* · {num}/{total}\n\n{step['q']}{sub}{sel_txt}"


async def _render_step(message: Message, state: FSMContext, edit: bool = False) -> None:
    data    = await state.get_data()
    answers = data.get("answers", {})
    visible = get_visible_steps(answers)
    idx     = data.get("step", 0)

    if idx >= len(visible):
        await _show_result(message, state, edit)
        return

    step     = visible[idx]
    selected = answers.get(step["id"], [])
    if isinstance(selected, str): selected = [selected]
    page = data.get("page", 0)

    text = _step_text(step, idx + 1, len(visible), selected)
    kbd  = _opts_kbd(step["opts"], step["type"], selected, page, step_idx=idx)

    try:
        if edit: await message.edit_text(text, reply_markup=kbd)
        else:    await message.answer(text, reply_markup=kbd)
    except Exception:
        await message.answer(text, reply_markup=kbd)


# ── /start ────────────────────────────────────────────────────────────────────

@(dp := Dispatcher(storage=MemoryStorage())).message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(step=0, answers={}, page=0)
    await state.set_state(Survey.question)
    await message.answer(
        "🧘 *Добро пожаловать в ERP Yoga Bot!*\n\n"
        "_Keep Calm and Get Advice_\n\n"
        "Я помогу подобрать оптимальную ERP-систему из *Top-12 мировых решений*. "
        "Анкета займёт ~2 минуты. 🚀",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать", callback_data="start_survey")]
        ]),
    )


@dp.callback_query(F.data == "start_survey")
async def cb_start(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await _render_step(cb.message, state, edit=True)


# ── Option pick ───────────────────────────────────────────────────────────────

@dp.callback_query(Survey.question, F.data.startswith("opt:"))
async def cb_opt(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    parts   = cb.data.split(":")
    opt_idx = int(parts[2]) if len(parts) == 3 else 0

    data    = await state.get_data()
    answers = data.get("answers", {})
    idx     = data.get("step", 0)
    visible = get_visible_steps(answers)
    step    = visible[idx]
    full_val = step["opts"][opt_idx]

    if step["type"] == "single":
        answers[step["id"]] = full_val
        await state.update_data(answers=answers, step=idx + 1, page=0)
        await _render_step(cb.message, state, edit=True)
    else:
        selected = answers.get(step["id"], [])
        if isinstance(selected, str): selected = [selected]
        if full_val in selected: selected.remove(full_val)
        else: selected.append(full_val)
        answers[step["id"]] = selected
        await state.update_data(answers=answers)
        await _render_step(cb.message, state, edit=True)


@dp.callback_query(Survey.question, F.data == "done")
async def cb_done(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data    = await state.get_data()
    answers = data.get("answers", {})
    idx     = data.get("step", 0)
    visible = get_visible_steps(answers)
    step    = visible[idx]

    if not answers.get(step["id"]):
        await cb.answer("Выберите хотя бы один вариант", show_alert=True)
        return

    await state.update_data(answers=answers, step=idx + 1, page=0)
    await _render_step(cb.message, state, edit=True)


@dp.callback_query(Survey.question, F.data.startswith("page:"))
async def cb_page(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.update_data(page=int(cb.data.split(":")[1]))
    await _render_step(cb.message, state, edit=True)


# ── Result ────────────────────────────────────────────────────────────────────

async def _show_result(message: Message, state: FSMContext, edit: bool = False) -> None:
    data    = await state.get_data()
    answers = data.get("answers", {})
    top3    = get_top3(answers)

    # Сохраняем top3 в state для последующих действий
    await state.update_data(top3=[dict(e) for e in top3])
    await state.set_state(Survey.result)

    partner_text = get_partner_advice(answers)
    top3_text    = format_top3_text(top3, answers)

    text = (
        "✅ *Анкета заполнена! Вот ваша рекомендация:*\n\n"
        + top3_text
        + "\n\n━━━━━━━━━━━━━━━━━\n\n"
        + partner_text
    )

    try:
        if edit: await message.edit_text(text, reply_markup=_result_kbd())
        else:    await message.answer(text, reply_markup=_result_kbd())
    except Exception:
        await message.answer(text, reply_markup=_result_kbd())

    # Уведомление менеджеру о новом лиде
    manager_id = os.environ.get("MANAGER_TELEGRAM_ID")
    if manager_id:
        industry = answers.get("industry", "?")
        budgets  = answers.get("budget", [])
        if isinstance(budgets, str): budgets = [budgets]
        top_name = top3[0]["name"] if top3 else "?"
        tg_user  = message.chat.username or str(message.chat.id)
        try:
            await bot.send_message(
                int(manager_id),
                f"🔔 *Новый лид — ERP Yoga Bot*\n\n"
                f"*Telegram:* @{tg_user}\n"
                f"*Отрасль:* {industry}\n"
                f"*#1 ERP:* {top_name}\n"
                f"*Бюджет:* {', '.join(budgets)}",
            )
        except Exception as e:
            log.warning(f"Менеджер не уведомлён: {e}")


# ── Copy brief ────────────────────────────────────────────────────────────────

@dp.callback_query(Survey.result, F.data == "copy_brief")
async def cb_copy_brief(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data    = await state.get_data()
    answers = data.get("answers", {})
    top3    = data.get("top3") or get_top3(answers)

    brief = build_plain_brief(answers, top3)

    await cb.message.answer(
        "📋 *Бриф для отправки партнёру / вендору:*\n\n"
        "Скопируйте текст ниже и отправьте потенциальному поставщику услуг:\n\n"
        "```\n" + brief + "\n```",
        reply_markup=_back_kbd(),
    )


# ── Find partners ─────────────────────────────────────────────────────────────

@dp.callback_query(Survey.result, F.data == "find_partners")
async def cb_find_partners(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(Survey.region)
    await cb.message.answer(
        "🌍 *Укажите страну или регион*\n\n"
        "Напишите название страны или города, "
        "и я помогу найти сертифицированных партнёров по внедрению ERP в вашем регионе.\n\n"
        "_Например: Россия, Казахстан, ОАЭ, Германия, США..._",
    )


@dp.message(Survey.region)
async def handle_region(message: Message, state: FSMContext) -> None:
    region  = message.text.strip()
    data    = await state.get_data()
    answers = data.get("answers", {})
    top3    = data.get("top3") or get_top3(answers)

    top_names = [e["name"] for e in top3[:2]]
    processing = await message.answer(f"🔍 Ищу партнёров в регионе *{region}*...")

    try:
        from ai_service import get_partners_in_region
        result = await get_partners_in_region(region, top_names, answers)
        await processing.delete()
        await message.answer(result, reply_markup=_back_kbd())
    except Exception as e:
        log.error(f"Ошибка поиска партнёров: {e}")
        await processing.delete()
        await message.answer(
            f"❌ Не удалось получить список партнёров: `{e}`",
            reply_markup=_back_kbd(),
        )

    await state.set_state(Survey.result)


# ── Restart ───────────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "restart")
async def cb_restart(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.clear()
    await state.update_data(step=0, answers={}, page=0)
    await state.set_state(Survey.question)
    await cb.message.answer(
        "🔄 *Начинаем заново!*\n\n🧘 _Keep Calm and Get Advice_",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать", callback_data="start_survey")]
        ]),
    )


# ── /help ─────────────────────────────────────────────────────────────────────

@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "🧘 *ERP Yoga Bot (@SAPyogaBOT)*\n"
        "_Keep Calm and Get Advice_\n\n"
        "/start — начать анкету\n"
        "/help — эта справка\n\n"
        "Бот рекомендует Top-3 ERP из 12 мировых систем, "
        "формирует бриф для отправки вендору и помогает найти "
        "партнёров по внедрению в вашем регионе.\n\n"
        "_Рекомендации основаны на официальных сайтах вендоров и аналитических источниках. "
        "Разработан сертифицированными экспертами._"
    )


# ── Fallback ──────────────────────────────────────────────────────────────────

@dp.message()
async def fallback(message: Message, state: FSMContext) -> None:
    if not await state.get_state():
        await message.answer("🧘 Напишите /start чтобы начать подбор ERP-системы.")


@dp.callback_query()
async def cb_fallback(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer("⚠️ Устаревшая кнопка. Нажмите /start", show_alert=True)


# ── Entry point ───────────────────────────────────────────────────────────────

bot = Bot(
    token=os.environ["TELEGRAM_BOT_TOKEN"],
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
)


async def main() -> None:
    log.info("🧘 ERP Yoga Bot (@SAPyogaBOT) запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
