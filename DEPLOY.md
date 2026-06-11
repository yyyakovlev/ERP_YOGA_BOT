# 🧘 ERP Yoga Bot — Полная инструкция по деплою
# @SAPyogaBOT | Keep Calm and Get Advice

---

## Структура проекта

```
ERP_YOGA_BOT/
├── bot.py                 — FSM, хэндлеры, Telegram polling
├── data.py                — анкета, скоринг из KB, форматирование
├── ai_service.py          — Claude API + web_search, поиск партнёров
├── email_service.py       — HTML-бриф + Resend
├── knowledge_base.json    — база 12 ERP-систем (25 отраслевых, 52 интеграции)
├── scraper_products.py    — парсер сайтов вендоров (запускать локально)
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Шаг 1. Подготовка локального репозитория

```bash
# Клонируй репо
git clone https://github.com/yyyakovlev/ERP_YOGA_BOT
cd ERP_YOGA_BOT

# Скопируй все файлы из архива erp_yoga_bot.zip сюда
# bot.py  data.py  ai_service.py  email_service.py
# knowledge_base.json  scraper_products.py
# requirements.txt  Dockerfile  .env.example

# Создай .gitignore если нет
cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
*.pyo
knowledge_base.backup.json
scraper_output/
EOF

# Закоммить всё
git add .
git commit -m "feat: ERP Yoga Bot v1 — KB-driven scoring"
git push origin main
```

---

## Шаг 2. Получение API-ключей

### TELEGRAM_BOT_TOKEN
```
Telegram → @BotFather → /newbot
Имя: ERP Yoga Bot
Username: @SAPyogaBOT
Скопируй токен вида: 7xxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxx
```

### ANTHROPIC_API_KEY
```
https://console.anthropic.com
→ API Keys → Create Key → назови "erp-yoga-bot"
→ Billing → Add Credits → минимум $10 (иначе 429 Rate Limit)
Ключ вида: sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
```

### RESEND_API_KEY
```
https://resend.com
→ API Keys → Create API Key
→ Domains → Add Domain (или используй onboarding@resend.dev для теста)
Ключ вида: re_xxxxxxxxxxxxxxxxxxxx
```

### MANAGER_TELEGRAM_ID
```
Telegram → @userinfobot → он пришлёт твой числовой ID
Вид: 123456789
```

---

## Шаг 3. Деплой на Railway

### 3.1 Создать проект
```
1. Зайди на https://railway.app
2. New Project → Deploy from GitHub repo
3. Выбери yyyakovlev/ERP_YOGA_BOT
4. Railway найдёт Dockerfile и запустит сборку автоматически
```

### 3.2 Добавить переменные окружения
```
Railway → твой проект → Variables → + New Variable

Обязательные:
  TELEGRAM_BOT_TOKEN     = 7xxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxx
  ANTHROPIC_API_KEY      = sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
  RESEND_API_KEY         = re_xxxxxxxxxxxxxxxxxxxx
  RESEND_FROM_EMAIL      = bot@yourdomain.com

Рекомендуемые:
  MANAGER_TELEGRAM_ID    = 123456789

Опциональные:
  MANAGER_EMAIL          = you@yourcompany.com
```

### 3.3 Проверить запуск в логах
```
Railway → Deployments → View Logs

Ожидаемый вывод:
  🧘 ERP Yoga Bot (@SAPyogaBOT) запускается...
  KB loaded: 12 systems, 25 industry solutions, 52 integrations
  Start polling
  Run polling for bot @ERP_YOGA_BOT id=xxxxxxxxxx
```

---

## Шаг 4. Рабочий цикл — обновление кода

### Любое изменение кода → автодеплой
```bash
# Внёс правки в любой файл
git add .
git commit -m "fix: описание что изменил"
git push origin main

# Railway автоматически пересобирает образ (~1-2 мин) и перезапускает бота
```

### Посмотреть логи в реальном времени
```bash
# Вариант 1: Railway UI → Deployments → View Logs

# Вариант 2: Railway CLI
npm install -g @railway/cli
railway login
railway logs --follow
```

### Принудительный рестарт
```bash
# Railway UI → Deployments → Redeploy

# Или через CLI:
railway redeploy
```

### Откатиться к предыдущей версии
```bash
# Railway UI → Deployments → выбери нужный → Rollback
```

---

## Шаг 5. Обновление knowledge_base.json (раз в квартал)

⚠️ Парсер запускать ЛОКАЛЬНО — серверные IP блокируются вендорами.

```bash
# На локальной машине:
cd ERP_YOGA_BOT

# Установить зависимости парсера
pip install httpx beautifulsoup4

# Посмотреть что будет обновлено (без записи)
python scraper_products.py --dry-run

# Запустить все вендоры
python scraper_products.py

# Если блокирует — через web.archive.org
python scraper_products.py --via-archive

# Обновить одну систему
python scraper_products.py --id sap_s4_public
python scraper_products.py --id dynamics

# Проверить что изменилось в базе
git diff knowledge_base.json

# Если всё корректно — закоммитить
git add knowledge_base.json
git commit -m "chore: quarterly KB update $(date +%Y-%m)"
git push origin main
# Railway автоматически перезапустит бота с новой базой
```

### Автоматизация через GitHub Actions
```yaml
# .github/workflows/scraper.yml
name: Quarterly KB Update

on:
  schedule:
    - cron: '0 6 1 */3 *'   # 1-е число каждого 3-го месяца в 6:00 UTC
  workflow_dispatch:          # или запустить вручную кнопкой в GitHub

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: pip install httpx beautifulsoup4
      - name: Run scraper
        run: python scraper_products.py --via-archive
      - name: Commit if changed
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: quarterly KB update"
          file_pattern: knowledge_base.json
```

---

## Шаг 6. @BotFather — настройки бота

```
@BotFather → /mybots → @SAPyogaBOT

/setname       → ERP Yoga Bot
/setdescription →
  Независимый советник по выбору ERP-системы.
  Анкета 12 вопросов → Top-3 рекомендации из мировых систем
  (SAP, Microsoft, Oracle, Odoo и др.) → бриф для партнёра.
  Keep Calm and Get Advice 🧘

/setabouttext  →
  Помогу выбрать ERP за 2 минуты. Бесплатно и независимо.

/setcommands   →
  start - Начать подбор ERP
  help - Справка

/setuserpic    → загрузи аватар бота
```

---

## Переменные окружения — шпаргалка

| Переменная           | Где взять                                      | Статус        |
|----------------------|------------------------------------------------|---------------|
| TELEGRAM_BOT_TOKEN   | @BotFather → /newbot                           | обязательно   |
| ANTHROPIC_API_KEY    | console.anthropic.com → API Keys               | обязательно   |
| RESEND_API_KEY       | resend.com → API Keys                          | обязательно   |
| RESEND_FROM_EMAIL    | верифицированный домен в Resend                | обязательно   |
| MANAGER_TELEGRAM_ID  | @userinfobot в Telegram                        | рекомендуется |
| MANAGER_EMAIL        | твой email для BCC-копии брифов                | опционально   |

---

## Диагностика типичных ошибок

```
BUTTON_DATA_INVALID
→ Устаревшие кнопки после обновления бота. Пользователь должен нажать /start.
→ В коде: callback_data по числовым индексам, макс 8 байт ✅

TelegramConflictError
→ Два инстанса бота одновременно. Railway сам разрешает при редеплое.
→ В коде: delete_webhook(drop_pending_updates=True) при старте ✅

anthropic 404 / model not found
→ Устаревшее название модели. Текущее: claude-sonnet-4-5 ✅

429 Too Many Requests
→ Rate limit Anthropic. Retry логика встроена (3 попытки × 15/30 сек) ✅
→ Долгосрочно: пополнить баланс на $10+ для повышения лимита

KB loaded: 0 systems
→ knowledge_base.json не попал в Docker-образ.
→ Проверь что файл закоммичен в репо и не в .gitignore
```

---

## Дисклеймер

Рекомендации основаны на официальных сайтах вендоров и аналитических источниках.
Разработан сертифицированными экспертами в области ERP-решений.
Окончательный выбор уточняется после детального анализа требований проекта.
