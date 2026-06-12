"""
ERP Yoga Bot — data.py
Вопросы анкеты, загрузка knowledge_base.json, скоринг, форматирование
@SAPyogaBOT | Keep Calm and Get Advice
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from functools import lru_cache

log = logging.getLogger(__name__)

# ── Knowledge Base ────────────────────────────────────────────────────────────

KB_PATH = Path(__file__).parent / "knowledge_base.json"


@lru_cache(maxsize=1)
def _load_kb() -> dict:
    """Загружает knowledge_base.json один раз при старте."""
    if not KB_PATH.exists():
        log.warning(f"knowledge_base.json not found at {KB_PATH} — using empty KB")
        return {"erp_systems": [], "industry_solutions": [], "integrations": [], "compliance": []}
    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)
    log.info(
        f"KB loaded: {len(kb['erp_systems'])} systems, "
        f"{len(kb['industry_solutions'])} industry solutions, "
        f"{len(kb['integrations'])} integrations"
    )
    return kb


def _kb_system(erp_id: str) -> dict:
    """Возвращает запись системы из KB или пустой dict."""
    return next((s for s in _load_kb()["erp_systems"] if s["id"] == erp_id), {})


def _kb_compliance(erp_id: str) -> dict:
    """Возвращает compliance-запись из KB."""
    return next((c for c in _load_kb()["compliance"] if c["erp_id"] == erp_id), {})


def _kb_industry_solutions(erp_id: str, industry_key: str) -> list[dict]:
    """Возвращает отраслевые решения для системы и отрасли."""
    return [
        x for x in _load_kb()["industry_solutions"]
        if x["erp_id"] == erp_id and x["industry_key"] == industry_key
    ]


def _kb_integrations(erp_id: str) -> list[dict]:
    """Возвращает все интеграционные записи для системы."""
    return [x for x in _load_kb()["integrations"] if x["erp_id"] == erp_id]


# ── Маппинг: текст анкеты → ключи KB ─────────────────────────────────────────

# Маппинг вариантов ответа на отрасль → industry_key в KB
INDUSTRY_KEY_MAP: dict[str, str] = {
    "Производство дискретное":       "manufacturing_discrete",
    "Производство процессное":        "manufacturing_process",
    "Нефть, газ / Горнодобыча":      "oil_gas",
    "Нефть":                          "oil_gas",
    "Горнодоб":                       "mining",
    "Энергетика и ЖКХ":              "energy",
    "Розничная торговля":             "retail",
    "Оптовая торговля / Дистрибуция":"wholesale",
    "Дистрибуция":                    "distribution",
    "Логистика и транспорт":          "logistics",
    "Строительство и недвижимость":   "construction",
    "Банки и финансовые услуги":      "banking",
    "Банки":                          "banking",
    "Телекоммуникации":               "telecom",
    "Здравоохранение / Фарма":       "healthcare",
    "Здравоохр":                      "healthcare",
    "Фарма":                          "pharma",
    "Государственный сектор":         "public_sector",
    "Агробизнес / Пищепром":         "food_beverage",
    "IT и профессиональные услуги":   "it_services",
    "Аэрокосмос и оборонка":          "aerospace",
    "Аэрокосмос":                     "aerospace",
}

# Маппинг integration_key для вопроса об интеграциях
INTEGRATION_KEY_MAP: dict[str, str] = {
    "Государственные порталы и сервисы":                     "gov_portals",
    "BI и аналитика (Power BI, Tableau)":      "bi_analytics",
    "MES / WMS / TMS":         "mes_wms_tms",
    "Банковские системы и эквайринг":                        "banking",
    "CRM-системы (Salesforce, HubSpot)":                     "crm",
    "Электронный документооборот (EDI, ЮЗЭДО)":              "edo",
    "Маркетплейсы и e-commerce":"ecommerce",
    "HR-системы (SAP SuccessFactors, 1С:ЗУП)":               "hr_systems",
    "IoT / SCADA / OPC-UA":        "iot_scada",
}


# ── База локализаций по странам ──────────────────────────────────────────────
# Уровни: "native" — встроено, "certified" — через партнёра, "limited" — частично, None — нет
LOCALIZATION: dict[str, dict[str, str]] = {
    "sap_s4_public": {
        "Россия": "native",
        "Казахстан": "native",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "certified",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "native",
    },
    "sap_s4_private": {
        "Россия": "native",
        "Казахстан": "native",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "certified",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "native",
    },
    "sap_b1": {
        "Россия": "native",
        "Казахстан": "native",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
    "oracle_fusion": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
    "netsuite": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "certified",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
    "dynamics": {
        "Россия": "native",
        "Казахстан": "native",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "certified",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "native",
    },
    "infor": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "certified",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
    "epicor": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "limited",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "certified",
        "Другая страна / Несколько регионов": "certified",
    },
    "acumatica": {
        "Россия": "native",
        "Казахстан": "certified",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "certified",
        "Германия / DACH": "certified",
        "США / Канада": "native",
        "Великобритания": "certified",
        "Другая страна ЕС": "certified",
        "Другая страна / Несколько регионов": "certified",
    },
    "odoo": {
        "Россия": "certified",
        "Казахстан": "certified",
        "Беларусь": "certified",
        "Украина": "certified",
        "Узбекистан / Центральная Азия": "certified",
        "ОАЭ / Ближний Восток": "certified",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
    "erpnext": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "certified",
        "Германия / DACH": "certified",
        "США / Канада": "native",
        "Великобритания": "certified",
        "Другая страна ЕС": "certified",
        "Другая страна / Несколько регионов": "limited",
    },
    "ifs": {
        "Россия": "limited",
        "Казахстан": "limited",
        "Беларусь": "limited",
        "Украина": "limited",
        "Узбекистан / Центральная Азия": "limited",
        "ОАЭ / Ближний Восток": "native",
        "Германия / DACH": "native",
        "США / Канада": "native",
        "Великобритания": "native",
        "Другая страна ЕС": "native",
        "Другая страна / Несколько регионов": "certified",
    },
}

LOCALIZATION_LABELS = {
    "native":     "✅ Нативная локализация",
    "certified":  "⚡ Через сертифицированного партнёра",
    "limited":    "⚠️ Ограниченная локализация",
    None:         "❌ Локализация отсутствует",
}

LOCALIZATION_SCORE = {
    "native":    15,
    "certified":  8,
    "limited":   -10,
    None:        -20,
}


def get_localization(erp_key: str, country: str) -> tuple[str | None, str]:
    """Возвращает (уровень, текст-метка) для страны и ERP."""
    level = LOCALIZATION.get(erp_key, {}).get(country)
    label = LOCALIZATION_LABELS.get(level, "⚠️ Данные не найдены")
    return level, label


def _industry_key(industry_text: str) -> str:
    """Конвертирует текст отрасли из анкеты в industry_key."""
    for fragment, key in INDUSTRY_KEY_MAP.items():
        if fragment in industry_text:
            return key
    return ""


# ── Вопросы анкеты ────────────────────────────────────────────────────────────

STEPS = [
    {
        "id": "vendor_pref", "block": "main",
        "q": "🏢 Хотите рассматривать решения конкретного вендора?",
        "sub": "Можно выбрать несколько или оставить открытым подбор",
        "type": "multi",
        "opts": [
            "Рассмотреть все — выбор открыт",
            "SAP",
            "Microsoft",
            "Oracle",
            "Infor",
            "IFS",
            "Epicor",
            "Acumatica",
            "Odoo",
            "ERPNext / Frappe",
        ],
    },
    {
        "id": "industry", "block": "main",
        "q": "В какой отрасли работает компания?",
        "sub": "Выберите наиболее подходящую",
        "type": "single",
        "opts": [
            "Производство дискретное",
            "Производство процессное",
            "Нефть, газ / Горнодобыча",
            "Энергетика и ЖКХ",
            "Розничная торговля",
            "Оптовая торговля / Дистрибуция",
            "Логистика и транспорт",
            "Строительство и недвижимость",
            "Банки и финансовые услуги",
            "Телекоммуникации",
            "Здравоохранение / Фарма",
            "Государственный сектор",
            "Агробизнес / Пищепром",
            "IT и профессиональные услуги",
            "Аэрокосмос и оборонка",
        ],
    },
    {
        "id": "size", "block": "main",
        "q": "Размер компании",
        "sub": "По количеству сотрудников",
        "type": "single",
        "opts": [
            "До 50 сотрудников",
            "50–200 сотрудников",
            "200–1000 сотрудников",
            "1000–10 000 сотрудников",
            "Свыше 10 000 сотрудников",
        ],
    },
    {
        "id": "users", "block": "main",
        "q": "👥 Планируемое количество пользователей ERP",
        "sub": "Напрямую влияет на стоимость лицензий",
        "type": "single",
        "opts": [
            "До 10 пользователей",
            "10–50 пользователей",
            "50–200 пользователей",
            "200–500 пользователей",
            "500–1000 пользователей",
            "Свыше 1000 пользователей",
            "Не определено",
        ],
    },
    {
        "id": "audit", "block": "main",
        "q": "Требования к прозрачности учёта",
        "sub": "Определяет круг допустимых систем",
        "type": "single",
        "opts": [
            "Нет особых требований",
            "Внешний аудит (Big4 / независимый)",
            "Подготовка к IPO или листингу на бирже",
            "Публичная компания — SOX / IFRS / МСФО",
            "Регуляторные требования",
        ],
    },
    {
        "id": "geo", "block": "main",
        "q": "Масштаб операций",
        "type": "single",
        "opts": [
            "Одна страна",
            "Несколько стран",
            "Глобально — мультинациональный",
        ],
    },
    {
        "id": "country", "block": "main",
        "q": "🌐 Основная страна операций",
        "sub": "Определяет локализацию и регуляторные требования",
        "type": "single",
        "opts": [
            "Россия",
            "Казахстан",
            "Беларусь",
            "Украина",
            "Узбекистан / Центральная Азия",
            "ОАЭ / Ближний Восток",
            "Германия / DACH",
            "США / Канада",
            "Великобритания",
            "Другая страна ЕС",
            "Другая страна / Несколько регионов",
        ],
    },
    {
        "id": "areas", "block": "main",
        "q": "Функциональные области для автоматизации",
        "sub": "Можно выбрать несколько",
        "type": "multi",
        "opts": [
            "Финансы и контроллинг",
            "Закупки и снабжение",
            "Цепочка поставок (SCM)",
            "Производство / MES",
            "Продажи и дистрибуция",
            "Управление складом",
            "HR и управление персоналом",
            "Техобслуживание активов (EAM)",
            "Проекты и сервис",
            "CRM и управление клиентами",
            "Аналитика и отчётность",
            "Экология / ESG",
        ],
    },
    {
        "id": "integrations", "block": "main",
        "q": "Требования к интеграциям",
        "sub": "С какими системами должен работать ERP? Можно выбрать несколько",
        "type": "multi",
        "opts": [
            "Нет требований к интеграции",
            "Государственные порталы и сервисы",
            "BI и аналитика (Power BI, Tableau)",
            "MES / WMS / TMS",
            "Банковские системы и эквайринг",
            "CRM-системы (Salesforce, HubSpot)",
            "Электронный документооборот (EDI, ЮЗЭДО)",
            "Маркетплейсы и e-commerce",
            "HR-системы (SAP SuccessFactors, 1С:ЗУП)",
            "IoT / SCADA / OPC-UA",
        ],
    },
    {
        "id": "pain", "block": "main",
        "q": "Главные боли и приоритеты",
        "sub": "Можно выбрать несколько",
        "type": "multi",
        "opts": [
            "Нет единой системы, данные разрозненны",
            "Медленная отчётность / закрытие периода",
            "Нет прозрачности цепочки поставок",
            "Высокие затраты на IT-поддержку",
            "Рост и масштабирование бизнеса",
            "Регуляторные требования / комплаенс",
            "Замена устаревшей системы (legacy)",
            "Контроль затрат и TCO",
            "ESG / экологические платежи",
        ],
    },
    {
        "id": "current", "block": "main",
        "q": "Текущий IT-ландшафт",
        "type": "single",
        "opts": [
            "Нет ERP — работаем в Excel / 1С",
            "SAP ECC / R3 — планируем миграцию",
            "Другой ERP — планируем замену",
            "Microsoft стек (D365 / AX / NAV)",
            "Oracle (EBS / JDE / NetSuite)",
            "Гибридная среда",
        ],
    },
    {
        "id": "datacenter", "block": "infra",
        "q": "Готовы инвестировать в собственный ЦОД?",
        "sub": "Определяет возможность On-Premise решений",
        "type": "single",
        "opts": [
            "Да — есть ЦОД и IT-команда",
            "Да — готовы построить или арендовать",
            "Нет — только облако",
            "Нет — хотим Private Cloud у вендора",
            "Частично — гибридная модель",
        ],
    },
    {
        "id": "deploy_reason", "block": "infra",
        "q": "Основная причина выбора On-Premise / Private Cloud?",
        "sub": "Поможет точнее подобрать решение",
        "type": "single",
        "conditional": lambda ans: any(
            k in (ans.get("datacenter") or "")
            for k in ["ЦОД и IT", "построить", "Private Cloud", "гибридная"]
        ),
        "opts": [
            "Суверенитет данных / регуляторика",
            "Нужна сложная кастомизация",
            "Уже есть своя инфраструктура",
            "Безопасность / изоляция среды",
            "Нет стабильного интернета",
            "Корпоративная политика",
        ],
    },
    {
        "id": "budget", "block": "main",
        "q": "Индикативный бюджет на первый год",
        "sub": "Лицензии + внедрение + инфраструктура",
        "type": "single",
        "opts": [
            "До $30K",
            "$30K – $150K",
            "$150K – $500K",
            "$500K – $1M",
            "$1M – $2M",
            "Свыше $2M",
            "Не готовы раскрывать",
        ],
    },
    {
        "id": "timeline", "block": "main",
        "q": "Желаемые сроки внедрения",
        "type": "single",
        "opts": [
            "До 3 месяцев",
            "3–6 месяцев",
            "6–12 месяцев",
            "Свыше 12 месяцев / поэтапно",
        ],
    },
    {
        "id": "priority", "block": "main",
        "q": "Что важнее при выборе ERP?",
        "sub": "Выберите один главный приоритет",
        "type": "single",
        "opts": [
            "Глубина отраслевой функциональности",
            "Простота внедрения и скорость старта",
            "Минимальная стоимость владения (TCO)",
            "Гибкость и возможность кастомизации",
            "Экосистема партнёров и поддержка",
            "Открытый исходный код / независимость",
        ],
    },
    {
        "id": "has_team", "block": "partner",
        "q": "Внутренняя IT-команда для поддержки ERP?",
        "sub": "Выберите наиболее подходящий вариант",
        "type": "single",
        "opts": [
            "Есть ERP-архитекторы / консультанты",
            "Есть IT-команда общего профиля",
            "Есть финансовые аналитики / Key Users",
            "Есть SAP-сертифицированные специалисты",
            "Есть разработчики для кастомизации",
            "Нет команды — полностью на партнёре",
            "Планируем нанять после выбора системы",
        ],
    },
    {
        "id": "partner_concerns", "block": "partner",
        "q": "Что важно при выборе партнёра?",
        "sub": "Можно выбрать несколько",
        "type": "multi",
        "opts": [
            "Сертификаты и статус партнёра вендора",
            "Отраслевые кейсы и референсы",
            "Локальная команда и язык поддержки",
            "Фиксированная стоимость (Fixed Price)",
            "Agile / итерационный подход",
            "Поддержка после Go-Live",
            "Обучение пользователей",
            "Прозрачность хода проекта (PMO)",
        ],
    },
]

CONTACT_STEPS = [
    {"id": "contact_name",    "q": "Ваше имя и фамилия?"},
    {"id": "contact_role",    "q": "Ваша должность?"},
    {"id": "contact_company", "q": "Название компании?"},
    {"id": "contact_country", "q": "Страна / регион?"},
    {"id": "contact_email",   "q": "Ваш email?"},
    {"id": "contact_phone",   "q": "Телефон или Telegram (@username)?"},
    {
        "id": "send_to_email",
        "q": "На какой email отправить бриф?\n\n"
             "Введите свой email или email партнёра. "
             "Можно несколько через запятую.\n"
             "Или /skip — бриф придёт только вам.",
    },
    {
        "id": "contact_comment",
        "q": "Дополнительный контекст (необязательно)\n\n"
             "Специфика процессов, интеграции, особые требования. "
             "Или /skip чтобы пропустить.",
    },
]

# ── Статичная база ERP (fallback если KB не загружен) ────────────────────────

ERP_DB: dict[str, dict] = {
    "sap_s4_public":  {"name": "SAP S/4HANA Cloud, Public Edition",   "vendor": "SAP",       "deploy_types": ["cloud"],               "tco": "$$$$",  "url": "https://www.sap.com/products/erp/s4hana-cloud.html",         "community": "https://community.sap.com/t5/sap-s-4hana-cloud/ct-p/S4HANAcloud", "strengths": ["Стандарт mid-market → enterprise", "Быстрый старт 3–6 мес"], "weaknesses": ["Ограниченная кастомизация", "Выше цена vs альтернативы"], "industries": ["Нефть", "Производство", "Фарма", "Банки", "Дистрибуция", "Оптовая", "Энергет"]},
    "sap_s4_private": {"name": "SAP S/4HANA Private / On-Premise",    "vendor": "SAP",       "deploy_types": ["cloud", "onprem", "private"],   "tco": "$$$$$", "url": "https://www.sap.com/products/erp/s4hana-private-cloud.html",  "community": "https://community.sap.com/t5/sap-s-4hana/ct-p/S4HANA",           "strengths": ["Максимальная кастомизация", "Полный контроль данных"],        "weaknesses": ["Самый высокий TCO", "Внедрение 9–18 мес"],                  "industries": []},
    "sap_b1":         {"name": "SAP Business One",                     "vendor": "SAP",       "deploy_types": ["cloud", "onprem"],     "tco": "$$",    "url": "https://www.sap.com/products/erp/business-one.html",         "community": "https://community.sap.com/t5/sap-business-one/ct-p/businessone","strengths": ["Быстрый старт 1–3 мес", "Доступная цена"],                   "weaknesses": ["Только малый бизнес"],                                       "industries": ["Оптовая", "Дистрибуция", "Производство дискретное", "Ритейл"]},
    "oracle_fusion":  {"name": "Oracle Fusion Cloud ERP",              "vendor": "Oracle",    "deploy_types": ["cloud", "onprem"],     "tco": "$$$$$", "url": "https://www.oracle.com/erp/",                                "community": "https://community.oracle.com",                                     "strengths": ["Сильная финансовая функциональность", "AI встроен нативно"],  "weaknesses": ["Высокая стоимость", "Долгое внедрение"],                    "industries": ["Банки", "Страхование", "Государств", "Телеком", "Энергет"]},
    "netsuite":       {"name": "Oracle NetSuite",                      "vendor": "Oracle",    "deploy_types": ["cloud"],               "tco": "$$$",   "url": "https://www.netsuite.com",                                   "community": "https://community.netsuite.com",                                   "strengths": ["Нативный SaaS", "Мультивалюта / мультиентити"],               "weaknesses": ["Слабее для производства", "Кастомизация через SuiteScript"], "industries": ["Оптовая", "Дистрибуция", "Ритейл", "IT", "Стартапы"]},
    "dynamics":       {"name": "Microsoft Dynamics 365",               "vendor": "Microsoft", "deploy_types": ["cloud", "hybrid"],     "tco": "$$$",   "url": "https://dynamics.microsoft.com",                             "community": "https://community.dynamics.com",                                   "strengths": ["Интеграция M365 / Azure / Copilot AI", "Гибкая модульность"], "weaknesses": ["Запутанное лицензирование", "Производство слабее SAP"],     "industries": ["Производство дискретное", "Ритейл", "IT", "Дистрибуция", "Банки"]},
    "infor":          {"name": "Infor CloudSuite",                     "vendor": "Infor",     "deploy_types": ["cloud", "onprem"],     "tco": "$$$$",  "url": "https://www.infor.com",                                      "community": "https://inforum.infor.com",                                        "strengths": ["Глубокая отраслевая специализация", "Лидер в здравоохранении"],"weaknesses": ["Меньше партнёров", "Менее известен в СНГ"],                 "industries": ["Здравоохр", "Фарма", "Производство", "Дистрибуция", "Аэрокосмос"]},
    "epicor":         {"name": "Epicor Kinetic",                       "vendor": "Epicor",    "deploy_types": ["cloud", "onprem"],     "tco": "$$$",   "url": "https://www.epicor.com/en/products/erp/kinetic/",             "community": "https://epicor.com/community",                                     "strengths": ["Специализация на производстве", "Гибкое развёртывание"],     "weaknesses": ["Слабее вне производства"],                                   "industries": ["Производство дискретное", "Производство процессное", "Аэрокосмос"]},
    "acumatica":      {"name": "Acumatica Cloud ERP",                  "vendor": "Acumatica", "deploy_types": ["cloud", "onprem"],     "tco": "$$",    "url": "https://www.acumatica.com",                                  "community": "https://community.acumatica.com",                                  "strengths": ["Безлимитные пользователи", "Современный UI"],                 "weaknesses": ["Не для крупного enterprise"],                                "industries": ["Ритейл", "Дистрибуция", "Строительство", "IT"]},
    "odoo":           {"name": "Odoo (Community / Enterprise)",        "vendor": "Odoo",      "deploy_types": ["cloud", "onprem", "open"], "tco": "$",  "url": "https://www.odoo.com",                                       "community": "https://www.odoo.com/forum",                                       "strengths": ["Open Source Community версия", "Самый низкий TCO"],           "weaknesses": ["Сложен для крупного бизнеса", "Требует разработчика"],      "industries": ["Стартапы", "IT", "Ритейл", "Дистрибуция", "Оптовая"]},
    "erpnext":        {"name": "ERPNext / Frappe",                     "vendor": "Frappe",    "deploy_types": ["cloud", "onprem", "open"], "tco": "$",  "url": "https://erpnext.com",                                        "community": "https://discuss.frappe.io",                                        "strengths": ["100% Open Source", "Нулевые лицензии"],                       "weaknesses": ["Требует Python-разработчика"],                               "industries": ["Стартапы", "IT", "Дистрибуция", "Агробизнес"]},
    "ifs":            {"name": "IFS Cloud",                            "vendor": "IFS",       "deploy_types": ["cloud", "onprem"],     "tco": "$$$$",  "url": "https://www.ifs.com",                                        "community": "https://community.ifs.com",                                        "strengths": ["Лидер для asset-intensive отраслей", "Аэрокосмос и оборона"], "weaknesses": ["Нишевый продукт", "Дорогой вне ключевых отраслей"],         "industries": ["Аэрокосмос", "Энергет", "Логистика", "Производство"]},
}

TCO_LABELS = {
    "$": "Низкий TCO", "$$": "Ниже среднего", "$$$": "Средний",
    "$$$$": "Выше среднего", "$$$$$": "Высокий",
}

BUDGET_SCORE_MAP = {
    "До $30K":       {"sap_b1": 10, "odoo": 20, "erpnext": 20, "acumatica": 15},
    "$30K – $150K":  {"sap_b1": 18, "odoo": 15, "netsuite": 12, "dynamics": 10, "acumatica": 15, "epicor": 10},
    "$150K – $500K": {"netsuite": 15, "dynamics": 15, "sap_b1": 12, "epicor": 12, "infor": 10, "sap_s4_public": 10},
    "$500K – $1M":   {"sap_s4_public": 18, "dynamics": 15, "netsuite": 15, "infor": 12, "epicor": 12},
    "$1M – $2M":     {"sap_s4_private": 18, "sap_s4_public": 15, "oracle_fusion": 15, "infor": 15, "ifs": 15},
    "Свыше $2M":     {"sap_s4_private": 18, "oracle_fusion": 18, "ifs": 15},
}

# ── Deploy filter ─────────────────────────────────────────────────────────────

def _get_deploy_filter(ans: dict) -> str:
    dc = ans.get("datacenter", "")
    if "только облако" in dc:    return "cloud_only"
    if "Private Cloud" in dc:    return "private_ok"
    if "ЦОД и IT" in dc or "построить" in dc: return "onprem_ok"
    if "гибридная" in dc:        return "hybrid_ok"
    return "any"


def _deploy_allowed(erp_key: str, deploy_filter: str) -> bool:
    dt = ERP_DB[erp_key]["deploy_types"]
    if deploy_filter == "cloud_only":  return "cloud" in dt
    if deploy_filter == "private_ok":  return "cloud" in dt or "private" in dt
    if deploy_filter == "onprem_ok":   return True
    if deploy_filter == "hybrid_ok":   return any(x in dt for x in ["cloud", "hybrid", "onprem"])
    return True

# ── Скоринг ───────────────────────────────────────────────────────────────────

def _integration_score(erp_key: str, selected_integrations: list[str]) -> int:
    """Скор интеграций из KB. Уровень native=20, certified=12, ipaas=6, custom=2."""
    level_bonus = {"native": 20, "certified": 12, "ipaas": 6, "custom": 2}
    kb_integrations = _kb_integrations(erp_key)
    score = 0
    for intg_text in selected_integrations:
        if intg_text == "Нет требований к интеграции":
            continue
        intg_key = INTEGRATION_KEY_MAP.get(intg_text)
        if not intg_key:
            continue
        # Ищем запись в KB
        kb_rec = next((x for x in kb_integrations if x["integration_key"] == intg_key), None)
        if kb_rec:
            score += kb_rec.get("score_bonus") or level_bonus.get(kb_rec.get("level", ""), 0)
    return score


def _industry_score_from_kb(erp_key: str, industry_text: str) -> int:
    """Бонус от отраслевых решений KB."""
    ind_key = _industry_key(industry_text)
    if not ind_key:
        return 0
    solutions = _kb_industry_solutions(erp_key, ind_key)
    if solutions:
        return max(s.get("score_bonus", 0) for s in solutions)
    return 0


def _compliance_score(erp_key: str, audit: str) -> int:
    """Compliance скор из KB."""
    comp = _kb_compliance(erp_key)
    if not comp:
        # Fallback к статичной логике
        ipo_systems = ["sap_s4_public", "sap_s4_private", "oracle_fusion", "dynamics", "netsuite", "infor", "ifs"]
        open_src    = ["odoo", "erpnext"]
        s = 0
        if "IPO" in audit or "SOX" in audit or "Публичная" in audit:
            if erp_key in ipo_systems: s += 25
            if erp_key in open_src:    s -= 30
        if "Big4" in audit or "аудит" in audit:
            if erp_key in ipo_systems: s += 15
            if erp_key in open_src:    s -= 15
        if "Регуляторные" in audit:
            if erp_key in ["sap_s4_public", "sap_s4_private", "oracle_fusion", "dynamics"]: s += 20
        return s

    s = 0
    need_ipo    = any(k in audit for k in ["IPO", "SOX", "Публичная"])
    need_audit  = any(k in audit for k in ["Big4", "аудит"])
    need_regul  = "Регуляторные" in audit

    if need_ipo:
        if comp.get("ipo_ready") and comp.get("big4_approved"): s += 25
        if comp.get("open_source_risk"):                         s -= 30
    if need_audit:
        if comp.get("big4_approved"):       s += 15
        if comp.get("open_source_risk"):    s -= 15
    if need_regul:
        if comp.get("sox_compliant"):       s += 20
    return s


def _score(erp_key: str, ans: dict) -> int:
    s = 0
    e        = ERP_DB[erp_key]
    industry = ans.get("industry", "")
    size     = ans.get("size", "")
    dc       = ans.get("datacenter", "")
    priority = ans.get("priority", "")
    areas    = ans.get("areas", [])
    current  = ans.get("current", "")
    timeline = ans.get("timeline", "")
    audit    = ans.get("audit", "")
    budgets  = ans.get("budget", [])
    teams    = ans.get("has_team", [])
    integrations = ans.get("integrations", [])
    if isinstance(budgets, str):     budgets = [budgets]
    if isinstance(teams, str):       teams = [teams]
    if isinstance(integrations, str): integrations = [integrations]

    # 1. Базовый отраслевой скор (из ERP_DB)
    for ind in e["industries"]:
        if ind in industry:
            s += 30
            break

    # 2. Отраслевой бонус из KB (отраслевые решения)
    s += _industry_score_from_kb(erp_key, industry)

    # 3. Размер компании
    is_small = "до 50" in size or "50–200" in size
    is_mid   = "200–1000" in size
    is_large = "1000" in size or "10 000" in size or "Свыше 10 000" in size
    if is_small and erp_key in ["sap_b1", "odoo", "erpnext", "acumatica", "netsuite"]:  s += 22
    if is_mid   and erp_key in ["netsuite", "dynamics", "acumatica", "sap_s4_public", "epicor", "infor"]: s += 22
    if is_large and erp_key in ["sap_s4_public", "oracle_fusion", "dynamics", "infor", "ifs"]: s += 22
    # sap_s4_private: крупная компания даёт бонус только при наличии инфраструктурного обоснования
    if is_large and erp_key == "sap_s4_private":
        dc = ans.get("datacenter", "")
        dr = ans.get("deploy_reason", "")
        if any(k in dc for k in ["ЦОД и IT", "построить", "Private Cloud", "гибридная"]):
            s += 22
        elif dr:  # есть причина On-Prem — умеренный бонус
            s += 12

    # 4. Бюджет
    for b in budgets:
        s += BUDGET_SCORE_MAP.get(b, {}).get(erp_key, 0)

    # 5. Инфраструктура / ЦОД
    if "ЦОД и IT" in dc or "построить" in dc:
        if erp_key in ["sap_s4_private", "oracle_fusion", "ifs", "infor"]: s += 25
    if "Private Cloud" in dc:
        if erp_key in ["sap_s4_private", "oracle_fusion", "dynamics", "infor"]: s += 22
    if "только облако" in dc:
        if erp_key in ["sap_s4_public", "netsuite", "dynamics", "acumatica", "odoo"]: s += 22
        if erp_key == "sap_s4_private": s -= 15  # без ЦОД предпочтительнее Public Edition
    if "гибридная" in dc:
        if erp_key in ["dynamics", "sap_s4_private", "epicor", "ifs"]: s += 15

    # 5b. Причина On-Prem/Private — ключевые обоснования для SAP Private
    deploy_reason = ans.get("deploy_reason", "")
    if erp_key == "sap_s4_private" and deploy_reason:
        if "кастомизация" in deploy_reason:   s += 20
        if "суверенитет"  in deploy_reason:   s += 18
        if "безопасност"  in deploy_reason:   s += 15
        if "инфраструктур" in deploy_reason:  s += 12
        if "политика"     in deploy_reason:   s += 15
        if "интернет"     in deploy_reason:   s += 10

    # 6. Сроки
    if "До 3" in timeline   and erp_key in ["odoo", "sap_b1", "acumatica", "erpnext"]: s += 15
    if "3–6" in timeline    and erp_key in ["sap_s4_public", "netsuite", "dynamics", "acumatica"]: s += 15
    if "6–12" in timeline   and erp_key in ["sap_s4_private", "oracle_fusion", "infor", "ifs", "epicor"]: s += 15
    if "12" in timeline     and erp_key in ["sap_s4_private", "oracle_fusion", "ifs"]: s += 15

    # 7. Приоритет
    if "отраслевой" in priority and erp_key in ["sap_s4_public", "sap_s4_private", "infor", "ifs", "epicor"]: s += 15
    if "Простота"   in priority and erp_key in ["odoo", "netsuite", "acumatica", "sap_b1"]: s += 15
    if "TCO"        in priority and erp_key in ["odoo", "erpnext", "acumatica", "sap_b1"]: s += 20
    if "Гибкость"   in priority and erp_key in ["odoo", "dynamics", "acumatica", "erpnext"]: s += 15
    if "Экосистема" in priority and erp_key in ["sap_s4_public", "dynamics", "netsuite"]: s += 15
    if "открытый"   in priority and erp_key in ["odoo", "erpnext"]: s += 30

    # 8. Compliance из KB
    s += _compliance_score(erp_key, audit)

    # 9. Миграция с текущей системы
    if "SAP ECC" in current   and erp_key in ["sap_s4_public", "sap_s4_private"]: s += 25
    if "Microsoft" in current and erp_key == "dynamics":                           s += 20
    if "Oracle" in current    and erp_key in ["oracle_fusion", "netsuite"]:        s += 15

    # 10. Функциональные области
    if "Производство / MES" in areas      and erp_key in ["sap_s4_public", "sap_s4_private", "epicor", "infor"]: s += 10
    if "ESG" in " ".join(areas)            and erp_key in ["sap_s4_public", "sap_s4_private"]:                    s += 15
    if "EAM" in " ".join(areas)            and erp_key in ["sap_s4_private", "ifs", "infor"]:                     s += 12

    # 11. Интеграции из KB
    s += _integration_score(erp_key, integrations)

    # 12. Команда
    teams_str = " ".join(teams)
    has_experts = any(k in teams_str for k in ["ERP-архитектор", "SAP-сертифицир", "Разработчик"])
    has_none    = "Нет команды" in teams_str
    if has_experts and erp_key in ["sap_s4_private", "oracle_fusion", "ifs"]: s += 12
    if has_none    and erp_key in ["sap_s4_private", "oracle_fusion", "ifs"]: s -= 10
    if has_none    and erp_key in ["odoo", "erpnext"]:                        s -= 8
    if has_none    and erp_key in ["sap_s4_public", "netsuite", "dynamics", "acumatica"]: s += 8

    # 13. Количество пользователей — влияет на TCO-модель
    users = ans.get("users", "")
    # Acumatica — безлимитные пользователи, выигрывает при большом числе
    if "500–1000" in users or "Свыше 1000" in users:
        if erp_key == "acumatica": s += 18   # per-resource, not per-user
        if erp_key in ["sap_s4_public", "sap_s4_private", "oracle_fusion"]: s += 8  # масштаб в пользу enterprise
        if erp_key in ["sap_b1", "odoo", "erpnext"]: s -= 10  # не для такого масштаба
    if "200–500" in users:
        if erp_key == "acumatica": s += 12
        if erp_key in ["sap_s4_public", "dynamics", "netsuite"]: s += 8
        if erp_key in ["sap_b1"]: s -= 8
    if "50–200" in users:
        if erp_key in ["dynamics", "netsuite", "acumatica", "sap_s4_public"]: s += 8
        if erp_key == "sap_b1": s += 5
    if "10–50" in users or "До 10" in users:
        if erp_key in ["sap_b1", "odoo", "erpnext", "acumatica"]: s += 12
        if erp_key in ["sap_s4_private", "oracle_fusion", "ifs"]: s -= 10  # избыточно для малого числа

    # 14. Локализация по стране
    country = ans.get("country", "")
    if country:
        loc_level, _ = get_localization(erp_key, country)
        s += LOCALIZATION_SCORE.get(loc_level, 0)

    return s


# ── Top-3 ─────────────────────────────────────────────────────────────────────

def get_top3(ans: dict) -> list[dict]:
    deploy_filter = _get_deploy_filter(ans)
    candidates    = [k for k in ERP_DB if _deploy_allowed(k, deploy_filter)]

    # Фильтр по вендору если выбран конкретный
    vendor_pref = ans.get("vendor_pref", [])
    if isinstance(vendor_pref, str): vendor_pref = [vendor_pref]
    selected_vendors = [v for v in vendor_pref if v != "Рассмотреть все — выбор открыт"]
    if selected_vendors:
        vendor_map = {
            "SAP": "SAP", "Microsoft": "Microsoft", "Oracle": "Oracle",
            "Infor": "Infor", "IFS": "IFS", "Epicor": "Epicor",
            "Acumatica": "Acumatica", "Odoo": "Odoo", "ERPNext / Frappe": "Frappe",
        }
        allowed = {vendor_map[v] for v in selected_vendors if v in vendor_map}
        if allowed:
            candidates = [k for k in candidates if ERP_DB[k]["vendor"] in allowed]

    scored = sorted(candidates, key=lambda k: _score(k, ans), reverse=True)

    result: list[str] = []
    used_vendors: set[str] = set()
    for key in scored:
        if len(result) >= 3: break
        vendor = ERP_DB[key]["vendor"]
        if len(result) < 2 or vendor not in used_vendors:
            result.append(key)
            used_vendors.add(vendor)
    for key in scored:
        if len(result) >= 3: break
        if key not in result:
            result.append(key)

    return [ERP_DB[k] | {"key": k} for k in result[:3]]


def get_visible_steps(ans: dict) -> list[dict]:
    return [s for s in STEPS if not s.get("conditional") or s["conditional"](ans)]


# ── Форматирование вывода ─────────────────────────────────────────────────────

def _get_industry_solution_tag(erp_key: str, industry_text: str) -> str | None:
    """Возвращает строку с отраслевым решением если есть нативное."""
    ind_key   = _industry_key(industry_text)
    solutions = [x for x in _kb_industry_solutions(erp_key, ind_key) if x.get("is_native")]
    if solutions:
        sol = solutions[0]
        return f"🏭 Отраслевое решение: [{sol['solution_name']}]({sol['solution_url']})"
    return None


def _get_integration_tags(erp_key: str, selected_integrations: list[str]) -> list[str]:
    """Возвращает теги интеграций для карточки ERP."""
    kb_ints = _kb_integrations(erp_key)
    tags = []
    level_icons = {"native": "✅", "certified": "🔗", "ipaas": "🔀", "custom": "⚙️"}
    for intg_text in selected_integrations:
        if intg_text == "Нет требований к интеграции":
            continue
        intg_key = INTEGRATION_KEY_MAP.get(intg_text)
        if not intg_key:
            continue
        kb_rec = next((x for x in kb_ints if x["integration_key"] == intg_key), None)
        if kb_rec:
            icon  = level_icons.get(kb_rec.get("level", ""), "🔗")
            short = intg_text.split(" (")[0]
            tags.append(f"{icon} {short}")
    return tags


def format_top3_text(top3: list[dict], ans: dict) -> str:
    deploy_filter = _get_deploy_filter(ans)
    filter_labels = {
        "cloud_only": "Только облачные решения",
        "private_ok": "Облако + Private Cloud",
        "onprem_ok":  "Cloud + On-Premise доступны",
        "hybrid_ok":  "Гибридная модель",
        "any":        "Все варианты деплоя",
    }
    budgets = ans.get("budget", [])
    if isinstance(budgets, str): budgets = [budgets]
    budget_str = ", ".join(b for b in budgets if b != "Не готовы раскрывать") or "не указан"
    industry   = ans.get("industry", "")
    audit      = ans.get("audit", "")
    integrations = ans.get("integrations", [])
    if isinstance(integrations, str): integrations = [integrations]
    need_ipo   = any(k in audit for k in ["IPO", "SOX", "Публичная", "Big4"])

    lines = [
        f"*Деплой:* {filter_labels[deploy_filter]}  |  *Бюджет:* {budget_str}"
        + ("  |  *Польз.:* " + ans.get("users","") if ans.get("users") and ans.get("users") != "Не определено" else ""),
        "",
    ]

    medals = ["🥇", "🥈", "🥉"]
    labels = ["Лучший выбор", "Сильная альтернатива", "Выгодно по TCO"]

    for i, erp in enumerate(top3):
        erp_key   = erp.get("key", "")
        tco_label = TCO_LABELS.get(erp["tco"], erp["tco"])
        pros      = " · ".join(erp["strengths"][:2])

        entry = [
            f"{medals[i]} *{labels[i]}*",
            f"*{erp['name']}* ({erp['vendor']})",
            f"TCO: {tco_label} ({erp['tco']}) | {erp['deploy_types'][0].upper()}",
            f"✅ {pros}",
        ]

        # Отраслевое решение из KB
        ind_tag = _get_industry_solution_tag(erp_key, industry)
        if ind_tag:
            entry.append(ind_tag)

        # Compliance badge из KB
        if need_ipo:
            comp = _kb_compliance(erp_key)
            if comp:
                if comp.get("open_source_risk"):
                    entry.append("⚠️ _Не рекомендуется для IPO — open source риск_")
                elif comp.get("ipo_ready") and comp.get("big4_approved"):
                    entry.append("✅ _Подходит для IPO и аудита Big4_")
            else:
                is_open = erp_key in ["odoo", "erpnext"]
                entry.append(
                    "⚠️ _Не рекомендуется для IPO (open source)_" if is_open
                    else "✅ _Подходит для внешнего аудита и IPO_"
                )

        # Теги интеграций из KB
        int_tags = _get_integration_tags(erp_key, integrations)
        if int_tags:
            entry.append("_Интеграции: " + " · ".join(int_tags) + "_")

        # Локализация по стране
        country = ans.get("country", "")
        if country:
            loc_level, loc_label = get_localization(erp_key, country)
            if loc_level == "native":
                entry.append(f"✅ Локализация для {country} — нативная")
            elif loc_level == "certified":
                entry.append(f"⚡ Локализация для {country} — через партнёра")
            elif loc_level == "limited":
                entry.append(f"⚠️ Локализация для {country} — ограниченная")

        entry += [f"🔗 [{erp['vendor']} / официальный сайт]({erp['url']})", ""]
        lines += entry

    lines += [
        "━━━━━━━━━━━━━━━━━",
        "💡 *Структура затрат на внедрение ERP:*",
        "📄 Лицензии и подписки — стоимость ПО и пользователей",
        "🖥 Железо и инфраструктура — серверы, ЦОД, сеть (для on-prem)",
        "🤝 Услуги партнёра — внедрение, настройка, миграция, обучение",
        "_Типичное соотношение: ~30% лицензии · ~20% железо · ~50% услуги_",
        "",
        "_🧘 ERP Yoga Bot (@SAPyogaBOT) — независимый советник. "
        "Рекомендации основаны на официальных сайтах вендоров и аналитических источниках. "
        "Разработан сертифицированными экспертами. "
        "Окончательный выбор уточняется после детального анализа требований._",
    ]
    return "\n".join(lines)


def build_plain_brief(ans: dict, top3: list[dict]) -> str:
    budgets = ans.get("budget", [])
    if isinstance(budgets, str): budgets = [budgets]
    areas  = ans.get("areas", [])
    pains  = ans.get("pain", [])
    teams  = ans.get("has_team", [])
    integrations = ans.get("integrations", [])
    if isinstance(teams, str):        teams = [teams]
    if isinstance(integrations, str): integrations = [integrations]
    concerns = ans.get("partner_concerns", "")
    if isinstance(concerns, list): concerns = ", ".join(concerns)

    intg_list = [x for x in integrations if x != "Нет требований к интеграции"]

    erp_lines = []
    for i, e in enumerate(top3):
        erp_key = e.get("key", "")
        label   = ["#1 Лучший выбор", "#2 Альтернатива", "#3 Выгодно по TCO"][i]
        line    = label + ": " + e["name"] + " (" + e["vendor"] + ") | TCO: " + e["tco"]
        # Добавляем отраслевое решение если есть
        ind_tag = _get_industry_solution_tag(erp_key, ans.get("industry", ""))
        if ind_tag:
            sol_name = ind_tag.split(": [")[1].split("]")[0] if ": [" in ind_tag else ""
            if sol_name: line += "\n    Отраслевое решение: " + sol_name
        line += "\n    Сайт: " + e["url"]
        erp_lines.append(line)

    sep = "\n"
    parts = [
        "=== ERP YOGA BOT — ЗАПРОС НА ПОДБОР ERP ===",
        "",
        "Отрасль:          " + ans.get("industry", "—"),
        "Размер компании:  " + ans.get("size", "—"),
        "Масштаб:          " + ans.get("geo", "—"),
        "Текущий IT:       " + ans.get("current", "—"),
        "ЦОД / инфра:      " + ans.get("datacenter", "—"),
        "",
        "Функц. области:",
        (sep.join("  - " + a for a in areas)) if areas else "  —",
        "",
        "Требования к интеграции:",
        (sep.join("  - " + x for x in intg_list)) if intg_list else "  Нет особых требований",
        "",
        "Ключевые боли:",
        (sep.join("  - " + p for p in pains)) if pains else "  —",
        "",
        "Аудит / Compliance: " + ans.get("audit", "—"),
        "Бюджет (год 1):     " + (", ".join(budgets) if budgets else "—"),
        "Сроки:              " + ans.get("timeline", "—"),
        "Приоритет:          " + ans.get("priority", "—"),
        "",
        "IT-команда:              " + (", ".join(teams) if teams else "—"),
        "Требования к партнёру:   " + (concerns or "—"),
        "",
    ] + erp_lines + [
        "",
        "СТРУКТУРА ЗАТРАТ НА ВНЕДРЕНИЕ ERP:",
        "  1. Лицензии и подписки     — стоимость ПО, зависит от числа пользователей и модулей",
        "  2. Железо и инфраструктура — серверы, ЦОД, сеть, резервное копирование (для on-prem)",
        "  3. Услуги партнёра          — внедрение, настройка, миграция данных, обучение, поддержка",
        "  Типичное соотношение: ~30% лицензии / ~20% железо / ~50% услуги партнёра",
        "",
        "Рекомендации: ERP Yoga Bot @SAPyogaBOT",
        "Источники: Официальные сайты вендоров.",
        "Разработан сертифицированными экспертами.",
        "Окончательное решение по выбору произведите после детального анализа требований.",
    ]
    return "\n".join(parts)
