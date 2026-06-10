"""
ERP Yoga Bot — AI-сервис
Claude API + web_search для актуальных данных о ERP-системах
"""
from __future__ import annotations
import os
import anthropic


async def get_ai_recommendation(answers: dict, top3: list[dict]) -> str:
    """Генерирует развёрнутое AI-обоснование через Claude с web_search."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    names = [e["name"] for e in top3]
    areas = ", ".join(answers.get("areas", []))
    pains = ", ".join(answers.get("pain", []))
    budgets = answers.get("budget", [])
    if isinstance(budgets, str): budgets = [budgets]
    teams = answers.get("has_team", [])
    if isinstance(teams, str): teams = [teams]

    prompt = f"""Ты — независимый ERP-эксперт. Изучи официальные сайты и community-ресурсы 
рекомендованных систем и дай развёрнутое обоснование для клиента.

ПРОФИЛЬ КЛИЕНТА:
- Отрасль: {answers.get("industry", "—")}
- Размер: {answers.get("size", "—")}
- Масштаб: {answers.get("geo", "—")}
- Текущий IT: {answers.get("current", "—")}
- ЦОД / инфраструктура: {answers.get("datacenter", "—")}
- Функциональные области: {areas}
- Боли: {pains}
- Бюджет: {", ".join(budgets)}
- Сроки: {answers.get("timeline", "—")}
- Приоритет: {answers.get("priority", "—")}
- Команда: {", ".join(teams)}

TOP-3 РЕКОМЕНДОВАННЫХ ERP:
1. {names[0] if len(names) > 0 else "—"} (лучший выбор)
2. {names[1] if len(names) > 1 else "—"} (сильная альтернатива)
3. {names[2] if len(names) > 2 else "—"} (выгодно по TCO)

Напиши ответ в Telegram Markdown:

**1. Почему эти три системы** — 2–3 аргумента под профиль клиента
**2. Ключевые отличия** — сравни Top-3 по: TCO, срокам внедрения, кастомизации
**3. На что обратить внимание** — 2–3 специфических риска для их отрасли/бюджета
**4. Следующий шаг** — конкретное действие

Длина ~250–350 слов. Конкретно, без воды.
В конце: одна строка дисклеймера про независимость рекомендаций."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )

    parts = [b.text for b in response.content if hasattr(b, "type") and b.type == "text"]
    return "\n".join(parts) if parts else "Рекомендация сформирована. Подробности — в брифе партнёру."


def get_partner_advice(answers: dict) -> str:
    """Адаптивный блок продажи команды на основе ответов."""
    team = answers.get("has_team", [])
    if isinstance(team, str): team = [team]
    team_str = " ".join(team)

    knows = answers.get("knows_partner", "")

    if "ERP-архитектор" in team_str or "SAP-сертифицир" in team_str:
        pitch = (
            "✅ *У вас есть ERP-экспертиза* — сильная позиция для проекта.\n\n"
            "Партнёр должен дополнять вашу команду там, где не хватает глубины: "
            "отраслевые best practices и нестандартные кейсы."
        )
    elif "Нет IT" in team_str:
        pitch = (
            "🤝 *Рекомендуем привлечь сертифицированного партнёра.*\n\n"
            "Для первого ERP-проекта это критично. "
            "Выбирайте партнёра с подтверждёнными кейсами в вашей отрасли "
            "и готовностью передавать знания вашей команде."
        )
    else:
        pitch = (
            "⚙️ *Ваша IT-команда — хороший старт.*\n\n"
            "ERP-проекты требуют специфической экспертизы по модулям. "
            "Партнёр, работающий *вместе* с вашей командой и передающий знания, — "
            "оптимальный вариант."
        )

    checklist = (
        "\n\n📋 *На что обратить внимание при выборе партнёра:*\n"
        "• Статус в Partner Program вендора\n"
        "• Сертификаты конкретных консультантов проекта\n"
        "• 2–3 референс-клиента в вашей отрасли\n"
        "• Методология SAP Activate / Agile, а не waterfall\n"
        "• Условия поддержки после Go-Live и SLA"
    )

    return pitch + checklist
