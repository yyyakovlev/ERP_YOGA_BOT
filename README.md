# 🧘 ERP Yoga Bot

> **Keep Calm and Get Advice** · [@SAPyogaBOT](https://t.me/SAPyogaBOT)

Независимый Telegram-бот для подбора ERP-системы из **12 мировых решений**. Анкета из 17 вопросов → скоринговый алгоритм → Top-3 рекомендации с отраслевыми тегами, локализацией и compliance-оценкой → бриф для партнёра.

---

## Что делает бот

1. **Анкета 17 вопросов** — вендор, отрасль, размер, пользователи, аудит, страна, функции, интеграции, инфраструктура, бюджет и др.
2. **KB-скоринг** — 14 факторов с весами, чтение из `knowledge_base.json`
3. **Top-3 рекомендации** — с отраслевым решением вендора, compliance-бейджем, тегами интеграций и локализацией по стране
4. **Бриф** — текст для копирования и отправки партнёру / вендору
5. **Поиск партнёров** — Claude + web_search по региону, на русском

---

## 12 ERP-систем в базе

| Система | Вендор | Деплой | TCO |
|---|---|---|---|
| SAP S/4HANA Cloud, Public Edition | SAP | Cloud | $$$$ |
| SAP S/4HANA Cloud, Private Edition / On-Prem | SAP | Cloud / On-Prem | $$$$$ |
| SAP Business One | SAP | Cloud / On-Prem | $$ |
| Oracle Fusion Cloud ERP | Oracle | Cloud / On-Prem | $$$$$ |
| Oracle NetSuite | Oracle | Cloud | $$$ |
| Microsoft Dynamics 365 | Microsoft | Cloud / Hybrid | $$$ |
| Infor CloudSuite | Infor | Cloud / On-Prem | $$$$ |
| Epicor Kinetic | Epicor | Cloud / On-Prem | $$$ |
| Acumatica Cloud ERP | Acumatica | Cloud | $$ |
| Odoo | Odoo | Cloud / On-Prem / Open | $ |
| ERPNext / Frappe | Frappe | Cloud / On-Prem / Open | $ |
| IFS Cloud | IFS | Cloud / On-Prem | $$$$ |

---

## Алгоритм скоринга — 14 факторов

1. Предпочтение вендора (фильтр кандидатов)
2. Базовый отраслевой скор
3. Отраслевой бонус из KB (94 решения)
4. Размер компании
5. Количество пользователей (Acumatica: pay-per-resource бонус)
6. Бюджет первого года
7. Инфраструктура / ЦОД + причина On-Prem
8. Сроки внедрения
9. Приоритет выбора
10. Compliance / IPO / SOX (штраф −30 для open source при IPO)
11. Миграция с текущей системы
12. Интеграции из KB (native +20, certified +12, ipaas +6, custom +2)
13. Команда
14. Локализация по стране (native +15, certified +8, limited −10)

---

## Анкета — 17 вопросов

| # | Вопрос | Тип |
|---|---|---|
| 1 | Вендорское предпочтение | multi + mutex |
| 2 | Отрасль (15 вариантов) | single |
| 3 | Размер компании | single |
| 4 | Количество пользователей ERP | single |
| 5 | Требования к аудиту / IPO | single |
| 6 | Масштаб операций | single |
| 7 | Основная страна операций | single |
| 8 | Функциональные области | multi |
| 9 | Требования к интеграциям | multi + mutex |
| 10 | Главные боли | multi |
| 11 | Текущий IT-ландшафт | single |
| 12 | Готовность к ЦОД | single |
| 13 | Причина On-Prem / Private | single, conditional |
| 14 | Бюджет первого года | single |
| 15 | Сроки внедрения | single |
| 16 | Главный приоритет | single |
| 17 | Внутренняя IT-команда | single |
| 18 | Требования к партнёру | multi |

---

## Дисклеймер

Рекомендации основаны на официальных сайтах вендоров, Gartner, G2 и аналитических источниках.
Разработан сертифицированными экспертами в области ERP-решений.
Окончательный выбор уточняется после детального анализа требований проекта.

🧘 *Keep Calm and Get Advice*
