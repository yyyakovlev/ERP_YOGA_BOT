"""
ERP Yoga Bot — Email-сервис
Генерация HTML-брифа и отправка через Resend
"""
from __future__ import annotations
import os
from datetime import datetime
import resend


def _tag(text: str, bg: str, color: str) -> str:
    return (f'<span style="display:inline-block;font-size:11px;padding:2px 8px;'
            f'border-radius:12px;background:{bg};color:{color};margin:2px;">{text}</span>')


def _section(title: str) -> str:
    return (f'<tr><td colspan="2" style="padding:6px 14px;font-size:11px;font-weight:600;'
            f'color:#888;background:#fafafa;letter-spacing:.05em;text-transform:uppercase;'
            f'border-bottom:1px solid #f0f0f0;">{title}</td></tr>')


def _row(key: str, val: str, highlight: bool = False) -> str:
    vs = "padding:8px 14px;font-size:13px;color:#3C3489;font-weight:600;" if highlight \
         else "padding:8px 14px;font-size:13px;color:#1a1a1a;"
    return (f'<tr style="border-bottom:1px solid #f0f0f0;">'
            f'<td style="padding:8px 14px;font-size:12px;color:#888;min-width:180px;'
            f'border-right:1px solid #f0f0f0;vertical-align:top;">{key}</td>'
            f'<td style="{vs}">{val}</td></tr>')


def build_html_email(answers: dict, top3: list[dict]) -> str:
    now = datetime.now().strftime("%d.%m.%Y")

    name    = answers.get("contact_name", "—")
    role    = answers.get("contact_role", "—")
    company = answers.get("contact_company", "—")
    country = answers.get("contact_country", "—")
    email   = answers.get("contact_email", "—")
    phone   = answers.get("contact_phone", "—")
    comment = answers.get("contact_comment", "")

    areas    = answers.get("areas", [])
    pains    = answers.get("pain", [])
    concerns = answers.get("partner_concerns", [])
    budgets  = answers.get("budget", [])
    teams    = answers.get("has_team", [])
    if isinstance(budgets, str): budgets = [budgets]
    if isinstance(teams, str):   teams = [teams]

    areas_html    = "".join(_tag(v, "#EEEDFE", "#3C3489") for v in areas)
    pains_html    = "".join(_tag(v, "#FAEEDA", "#633806") for v in pains)
    concerns_html = "".join(_tag(v, "#E1F5EE", "#0F6E56") for v in concerns)
    budgets_html  = "".join(_tag(v, "#FAEEDA", "#633806") for v in budgets)
    teams_html    = "".join(_tag(v, "#EEEDFE", "#3C3489") for v in teams)

    # Top-3 ERP rows
    medals = ["🥇 Лучший выбор", "🥈 Альтернатива", "🥉 Выгодно по TCO"]
    erp_rows = ""
    for i, erp in enumerate(top3):
        erp_rows += f"""
        <tr style="background:{'#EEEDFE' if i==0 else '#fafafa'};">
          <td style="padding:10px 14px;font-size:12px;font-weight:600;
                     color:#534AB7;border-right:1px solid #e0e0e0;white-space:nowrap;">{medals[i]}</td>
          <td style="padding:10px 14px;">
            <div style="font-size:14px;font-weight:700;color:#3C3489;">{erp['name']}</div>
            <div style="font-size:11px;color:#534AB7;margin-top:3px;">
              {erp['vendor']} · TCO: {erp['tco']} · {erp['deploy_types'][0].upper()}
            </div>
            <div style="margin-top:5px;">
              <a href="{erp['url']}" style="font-size:12px;color:#534AB7;margin-right:12px;">
                🔗 Официальный сайт
              </a>
              <a href="{erp['community']}" style="font-size:12px;color:#534AB7;">
                💬 Community
              </a>
            </div>
          </td>
        </tr>"""

    comment_row = _row("Доп. контекст", f'<em style="color:#666;">{comment}</em>') \
        if comment and comment != "/skip" else ""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f5f5f5;">
<div style="max-width:640px;margin:24px auto;background:white;border-radius:8px;
     overflow:hidden;border:1px solid #e0e0e0;">

  <div style="background:#534AB7;padding:20px 24px;">
    <div style="font-size:18px;font-weight:700;color:white;">
      🧘 ERP Yoga Bot — Запрос на подбор ERP-системы
    </div>
    <div style="font-size:12px;color:#AFA9EC;margin-top:4px;">
      @SAPyogaBOT · Keep Calm and Get Advice · {now}
    </div>
  </div>

  <table style="width:100%;border-collapse:collapse;">
    {_section("Контактное лицо")}
    {_row("Имя / должность", f"{name}, {role}")}
    {_row("Компания", company)}
    {_row("Страна / регион", country)}
    {_row("Email", f'<a href="mailto:{email}" style="color:#534AB7;">{email}</a>')}
    {_row("Телефон / Telegram", phone)}

    {_section("Профиль компании")}
    {_row("Отрасль", answers.get("industry", "—"))}
    {_row("Размер компании", answers.get("size", "—"))}
    {_row("Масштаб операций", answers.get("geo", "—"))}
    {_row("Текущий IT-ландшафт", answers.get("current", "—"))}
    {_row("Инфраструктура / ЦОД", answers.get("datacenter", "—"))}

    {_section("Задачи и требования")}
    {_row("Функциональные области", areas_html)}
    {_row("Ключевые боли", pains_html)}

    {_section("Технические предпочтения")}
    {_row("Бюджет (год 1)", budgets_html)}
    {_row("Желаемые сроки", answers.get("timeline", "—"))}
    {_row("Главный приоритет", answers.get("priority", "—"))}

    {_section("Команда и требования к партнёру")}
    {_row("Внутренняя IT-команда", teams_html)}
    {_row("Приоритеты по партнёру", concerns_html)}

    {comment_row}

    {_section("AI-рекомендация Top-3 ERP")}
    {erp_rows}

  </table>

  <div style="padding:14px 16px;background:#fafafa;border-top:1px solid #f0f0f0;
              font-size:11px;color:#aaa;line-height:1.7;">
    🧘 <strong>ERP Yoga Bot (@SAPyogaBOT)</strong> — независимый ERP-советник.<br>
    Рекомендации основаны на официальных сайтах вендоров, Gartner, G2 и community-ресурсах.<br>
    Разработан сертифицированными экспертами. Итоговый выбор уточняется после детального анализа требований.<br>
    Keep Calm and Get Advice 🧘
  </div>

</div>
</body>
</html>"""


def send_brief(answers: dict, top3: list[dict], to_email: str | None = None) -> str:
    """Отправляет HTML-бриф через Resend. Возвращает ID письма."""
    resend.api_key = os.environ["RESEND_API_KEY"]
    recipient = to_email or os.environ["PARTNER_EMAIL"]
    from_addr = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    company  = answers.get("contact_company", "")
    industry = answers.get("industry", "")
    subject  = f"ERP-бриф: {company} — {industry}" if company else "ERP Yoga Bot — Запрос на подбор ERP"

    params: resend.Emails.SendParams = {
        "from": from_addr,
        "to": [recipient],
        "subject": subject,
        "html": build_html_email(answers, top3),
    }
    response = resend.Emails.send(params)
    return response["id"]
