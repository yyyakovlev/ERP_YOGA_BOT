# 🧘 ERP Yoga Bot

> **Keep Calm and Get Advice** · [@SAPyogaBOT](https://t.me/SAPyogaBOT)

Независимый Telegram-бот для подбора ERP-системы из **Top-12 мировых решений** с автоматической отправкой структурированного брифа партнёру.

---

## 🎯 Что делает бот

1. **Анкета** — 12 умных вопросов (профиль компании, инфраструктура, команда, партнёр)
2. **AI-рекомендация** — Claude API + web_search → Top-3 ERP с обоснованием
3. **Бриф партнёру** — HTML-письмо через Resend с полным профилем клиента

## 🗃️ ERP-системы в базе

| # | Система | Вендор | Деплой |
|---|---------|--------|--------|
| 1 | SAP S/4HANA Public | SAP | Cloud |
| 2 | SAP S/4HANA Private / On-Prem | SAP | Private / On-Prem |
| 3 | SAP Business One | SAP | Cloud / On-Prem |
| 4 | Oracle Fusion Cloud | Oracle | Cloud / On-Prem |
| 5 | Oracle NetSuite | Oracle | Cloud |
| 6 | Microsoft Dynamics 365 | Microsoft | Cloud / Hybrid |
| 7 | Infor CloudSuite | Infor | Cloud / On-Prem |
| 8 | Epicor Kinetic | Epicor | Cloud / On-Prem |
| 9 | Acumatica Cloud ERP | Acumatica | Cloud / On-Prem |
| 10 | Odoo | Odoo | Cloud / On-Prem / Open |
| 11 | ERPNext / Frappe | Frappe | Cloud / On-Prem / Open |
| 12 | IFS Cloud | IFS | Cloud / On-Prem |

## 🚀 Быстрый старт

```bash
git clone https://github.com/yyyakovlev/ERP_YOGA_BOT
cd ERP_YOGA_BOT
pip install -r requirements.txt
cp .env.example .env   # заполни переменные
python bot.py
```

## ⚙️ Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `ANTHROPIC_API_KEY` | Claude API — console.anthropic.com |
| `RESEND_API_KEY` | resend.com/api-keys |
| `RESEND_FROM_EMAIL` | Email отправителя (верифицировать домен в Resend) |
| `PARTNER_EMAIL` | Email партнёра для брифов |
| `MANAGER_TELEGRAM_ID` | (опц.) Ваш Telegram ID для уведомлений о лидах |

> **Тест без домена:** `RESEND_FROM_EMAIL=onboarding@resend.dev`

## 🏗️ Структура проекта

```
ERP_YOGA_BOT/
├── bot.py           # хэндлеры, FSM, роутинг
├── data.py          # вопросы, база ERP, скоринг, Top-3
├── ai_service.py    # Claude API + web_search
├── email_service.py # HTML-бриф + Resend
├── Dockerfile       # для Railway / Docker
├── requirements.txt
├── .env.example
└── README.md
```

## 🚂 Деплой на Railway

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Выбери `yyyakovlev/ERP_YOGA_BOT`
3. Variables → добавь все 6 переменных из `.env.example`
4. Deploy → готово. Каждый `git push` = автодеплой ✅

## 📋 Поток пользователя

```
/start
  └─► Анкета (12 вопросов, inline-кнопки)
        └─► Контактные данные (6 полей)
              └─► Top-3 ERP + партнёрский блок
                    ├─► [Отправить бриф]
                    │     ├─► Claude: AI-анализ + web_search
                    │     ├─► Resend: HTML-бриф партнёру
                    │     └─► Уведомление менеджеру в Telegram
                    └─► [Пройти заново]
```

## 🧘 Дисклеймер

Рекомендации основаны на официальных сайтах вендоров, Gartner Magic Quadrant, G2 и community-ресурсах.
Разработан сертифицированными экспертами в области ERP-решений.
Окончательный выбор уточняется после детального анализа требований проекта.
