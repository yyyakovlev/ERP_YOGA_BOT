"""
🧘 ERP Yoga Bot (@SAPyogaBOT)
Keep Calm and Get Advice

Стек: aiogram 3.x · FSM · Claude API · Resend
Деплой: Railway (Dockerfile в корне)

Запуск:
    cp .env.example .env   # заполни переменные
    python bot.py
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
from data import CONTACT_STEPS, get_top3, get_visible_steps, format_top3_text
from email_service import send_brief

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

ITEMS_PER_PAGE = 8


# ── FSM ──────────────────────────────────────────────────────────────────────

class Survey(StatesGroup):
    question = State()
    contact  = State()
    confirm  = State()


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def _opts_kbd(opts: list[str], q_type: str, selected: list[str], page: int = 0) -> InlineKeyboardMarkup:
    start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    rows = []

    for opt in opts[start:end]:
        prefix = "✅ " if opt in selected else ""
        cb = f"opt:{opt[:60]}"
        rows.append([InlineKeyboardButton(text=prefix + opt, callback_data=cb)])

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


def _confirm_kbd() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Отправить бриф партнёру", callback_data="send_brief")],
        [InlineKeyboardButton(text="🔄 Пройти заново",           callback_data="restart")],
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
    block = BLOCK_LABELS.get(step.get("block", "main"), "")
    sub   = f"\n_{step['sub']}_" if step.get("sub") else ""
    sel_txt = ""
    if step["type"] == "multi" and selected:
        sel_txt = "\n\n*Выбрано:* " + ", ".join(selected)
    return f"*{block}* · {num}/{total}\n\n{step['q']}{sub}{sel_txt}"


async def _render_step(message: Message, state: FSMContext, edit: bool = False) -> None:
    data     = await state.get_data()
    answers  = data.get("answers", {})
    visible  = get_visible_steps(answers)
    idx      = data.get("step", 0)

    if idx >= len(visible):
        await _start_contacts(message, state, edit)
        return

    step     = visible[idx]
    selected = answers.get(step["id"], [])
    if isinstance(selected, str): selected = [selected]
    page = data.get("page", 0)

    text = _step_text(step, idx + 1, len(visible), selected)
    kbd  = _opts_kbd(step["opts"], step["type"], selected, page)

    try:
        if edit:
            await message.edit_text(text, reply_markup=kbd)
        else:
            await message.answer(text, reply_markup=kbd)
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
        "Я помогу подобрать оптимальную ERP-систему из *Top-10 мировых решений* "
        "и сформирую готовый бриф для отправки партнёру.\n\n"
        "Анкета займёт ~3 минуты. 🚀",
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
    val  = cb.data[4:]
    data = await state.get_data()
    answers = data.get("answers", {})
    idx     = data.get("step", 0)
    visible = get_visible_steps(answers)
    step    = visible[idx]

    # Restore full value (may have been truncated in callback_data)
    full_val = next((o for o in step["opts"] if o[:60] == val), val)

    if step["type"] == "single":
        answers[step["id"]] = full_val
        await state.update_data(answers=answers, step=idx + 1, page=0)
        await _render_step(cb.message, state, edit=True)
    else:
        selected = answers.get(step["id"], [])
        if isinstance(selected, str): selected = [selected]
        if full_val in selected:
            selected.remove(full_val)
        else:
            selected.append(full_val)
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


# ── Contact collection ────────────────────────────────────────────────────────

async def _start_contacts(message: Message, state: FSMContext, edit: bool = False) -> None:
    await state.update_data(contact_step=0)
    await state.set_state(Survey.contact)
    text = "✅ *Анкета заполнена!*\n\nТеперь укажите контактные данные — они попадут в бриф.\n\n" \
           + CONTACT_STEPS[0]["q"]
    try:
        if edit: await message.edit_text(text, reply_markup=None)
        else:    await message.answer(text)
    except Exception:
        await message.answer(text)


@dp.message(Survey.contact)
async def handle_contact(message: Message, state: FSMContext) -> None:
    data         = await state.get_data()
    contact_step = data.get("contact_step", 0)
    answers      = data.get("answers", {})

    step_info = CONTACT_STEPS[contact_step]
    value     = "" if message.text.strip().lower() == "/skip" else message.text.strip()
    answers[step_info["id"]] = value

    next_step = contact_step + 1
    if next_step < len(CONTACT_STEPS):
        await state.update_data(answers=answers, contact_step=next_step)
        await message.answer(CONTACT_STEPS[next_step]["q"])
    else:
        await state.update_data(answers=answers)
        await state.set_state(Survey.confirm)
        await _show_summary(message, state)


# ── Summary ───────────────────────────────────────────────────────────────────

async def _show_summary(message: Message, state: FSMContext) -> None:
    data    = await state.get_data()
    answers = data.get("answers", {})
    top3    = get_top3(answers)

    await state.update_data(top3=[{k: v for k, v in e.items()} for e in top3])

    partner_text = get_partner_advice(answers)
    top3_text    = format_top3_text(top3, answers)

    text = (
        "📋 *Ваш профиль сформирован!*\n\n"
        + top3_text +
        "\n\n━━━━━━━━━━━━━━━━━\n\n"
        + partner_text +
        "\n\n━━━━━━━━━━━━━━━━━\n\n"
        "📨 Нажмите *«Отправить бриф партнёру»* — структурированный запрос "
        "уйдёт на email со всеми вашими ответами и рекомендациями."
    )
    await message.answer(text, reply_markup=_confirm_kbd())


# ── Send brief ────────────────────────────────────────────────────────────────

@dp.callback_query(Survey.confirm, F.data == "send_brief")
async def cb_send(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer("Отправляем...")
    await cb.message.edit_reply_markup(reply_markup=None)

    data    = await state.get_data()
    answers = data.get("answers", {})
    top3    = data.get("top3") or get_top3(answers)

    processing = await cb.message.answer("⏳ Генерирую AI-анализ и отправляю бриф...")

    try:
        ai_text    = await get_ai_recommendation(answers, top3)
        email_id   = send_brief(answers, top3)
        partner_email = os.environ.get("PARTNER_EMAIL", "")

        await processing.delete()
        await cb.message.answer(
            f"✅ *Бриф отправлен!*\n\n"
            f"📧 На: `{partner_email}`\n"
            f"🆔 ID письма: `{email_id}`\n\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "🤖 *Развёрнутый AI-анализ:*\n\n" + ai_text,
            reply_markup=_back_kbd(),
        )

        # Notify manager
        manager_id = os.environ.get("MANAGER_TELEGRAM_ID")
        if manager_id:
            company  = answers.get("contact_company", "?")
            name     = answers.get("contact_name", "?")
            industry = answers.get("industry", "?")
            top_name = top3[0]["name"] if top3 else "?"
            budgets  = answers.get("budget", [])
            if isinstance(budgets, str): budgets = [budgets]
            try:
                await bot.send_message(
                    int(manager_id),
                    f"🔔 *Новый лид — ERP Yoga Bot*\n\n"
                    f"*Компания:* {company}\n"
                    f"*Контакт:* {name}\n"
                    f"*Отрасль:* {industry}\n"
                    f"*#1 ERP:* {top_name}\n"
                    f"*Бюджет:* {', '.join(budgets)}\n"
                    f"*Email ID:* `{email_id}`",
                )
            except Exception as e:
                log.warning(f"Не удалось уведомить менеджера: {e}")

    except Exception as e:
        log.error(f"Ошибка отправки: {e}")
        await processing.delete()
        await cb.message.answer(
            f"❌ *Ошибка:* `{e}`\n\n"
            "Проверьте RESEND_API_KEY и PARTNER_EMAIL.\n"
            "Для теста: RESEND_FROM_EMAIL=onboarding@resend.dev",
            reply_markup=_back_kbd(),
        )


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
        "Бот задаёт вопросы, рекомендует Top-3 ERP из 12 мировых систем "
        "и отправляет структурированный бриф партнёру по email.\n\n"
        "_Рекомендации основаны на официальных сайтах вендоров и аналитических источниках. "
        "Разработан сертифицированными экспертами._"
    )


# ── Fallback ──────────────────────────────────────────────────────────────────

@dp.message()
async def fallback(message: Message, state: FSMContext) -> None:
    if not await state.get_state():
        await message.answer("🧘 Напишите /start чтобы начать подбор ERP-системы.")


# ── Entry point ───────────────────────────────────────────────────────────────

bot = Bot(
    token=os.environ["TELEGRAM_BOT_TOKEN"],
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
)


async def main() -> None:
    log.info("🧘 ERP Yoga Bot (@SAPyogaBOT) запускается...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
