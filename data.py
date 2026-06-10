"""
ERP Yoga Bot — база вопросов, ERP-решений и логика рекомендаций
@SAPyogaBOT | Keep Calm and Get Advice
"""
from __future__ import annotations

STEPS = [
    # ── Блок 1: Профиль проекта ──────────────────────────────────────────
    {
        "id": "industry", "block": "main",
        "q": "🏭 В какой отрасли работает компания?",
        "sub": "Выберите наиболее подходящую",
        "type": "single",
        "opts": [
            "Производство дискретное (машиностроение, электроника)",
            "Производство процессное (химия, фармацевтика, FMCG)",
            "Нефть и газ / Горнодобывающая промышленность",
            "Энергетика и коммунальные услуги",
            "Розничная торговля (Retail)",
            "Оптовая торговля / Дистрибуция",
            "Логистика и транспорт",
            "Строительство и недвижимость",
            "Банки и финансовые услуги / Страхование",
            "Телекоммуникации",
            "Здравоохранение / Фармацевтика",
            "Государственный сектор",
            "Агробизнес / Пищевая промышленность",
            "IT и профессиональные услуги",
            "Аэрокосмос / Оборонная промышленность",
        ],
    },
    {
        "id": "size", "block": "main",
        "q": "👥 Размер компании",
        "sub": "По количеству сотрудников",
        "type": "single",
        "opts": [
            "Стартап / Малый бизнес (до 50)",
            "Малый-средний (50–200)",
            "Средний (200–1000)",
            "Крупный (1000–10 000)",
            "Корпорация / холдинг (10 000+)",
        ],
    },
    {
        "id": "geo", "block": "main",
        "q": "🌍 Масштаб операций",
        "type": "single",
        "opts": [
            "Локальный — одна страна",
            "Региональный — несколько стран",
            "Глобальный — мультинациональный",
        ],
    },
    {
        "id": "areas", "block": "main",
        "q": "⚙️ Какие функциональные области нужно автоматизировать?",
        "sub": "Можно выбрать несколько. Нажмите «Готово» когда закончите.",
        "type": "multi",
        "opts": [
            "Финансы и контроллинг",
            "Закупки и снабжение",
            "Управление цепочкой поставок (SCM)",
            "Производство / MES",
            "Продажи и дистрибуция",
            "Управление складом",
            "HR и управление персоналом",
            "Техническое обслуживание активов (EAM)",
            "Проекты и сервис",
            "CRM и управление клиентами",
            "Аналитика и отчётность",
            "Охрана окружающей среды / ESG",
        ],
    },
    {
        "id": "pain", "block": "main",
        "q": "🎯 Главные боли / приоритеты проекта",
        "sub": "Можно выбрать несколько. Нажмите «Готово» когда закончите.",
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
        "q": "💻 Текущий IT-ландшафт",
        "type": "single",
        "opts": [
            "Нет ERP — работаем в Excel / 1С / самописном",
            "SAP ECC / R3 — планируем миграцию",
            "Другой ERP — планируем замену",
            "Microsoft стек (D365 / AX / NAV)",
            "Oracle (EBS / JDE / NetSuite)",
            "Гибридная среда",
        ],
    },

    # ── Блок 2: Инфраструктура ────────────────────────────────────────────
    {
        "id": "datacenter", "block": "infra",
        "q": "🏢 Готовы ли вы инвестировать в собственный ЦОД?",
        "sub": "Это определяет возможность On-Premise решений",
        "type": "single",
        "opts": [
            "Да — у нас уже есть собственный ЦОД и IT-команда",
            "Да — готовы построить / арендовать ЦОД",
            "Нет — предпочитаем облако, не хотим заниматься инфраструктурой",
            "Нет — но хотим Private Cloud у вендора (изолированная среда)",
            "Частично — гибридная модель (часть on-prem, часть в облаке)",
        ],
    },
    {
        "id": "deploy_reason", "block": "infra",
        "q": "🔒 Основная причина выбора On-Premise / Private Cloud?",
        "sub": "Поможет точнее подобрать решение",
        "type": "single",
        # Показывается только если выбран on-prem/hybrid/private сценарий
        "conditional": lambda ans: any(k in (ans.get("datacenter") or "")
            for k in ["есть собственный", "построить", "Private Cloud", "гибридная"]),
        "opts": [
            "Требования к суверенитету данных / регуляторика",
            "Сложная кастомизация — стандартное облако не подойдёт",
            "Уже вложены в инфраструктуру, хотим использовать",
            "Соображения безопасности / изоляции",
            "Нет стабильного интернет-соединения на площадках",
            "Корпоративная политика — только on-premise",
        ],
    },

    # ── Блок 1 (продолжение) ──────────────────────────────────────────────
    {
        "id": "budget", "block": "main",
        "q": "💰 Индикативный бюджет на ERP (первый год)",
        "sub": "Лицензия + внедрение + инфраструктура. Можно выбрать несколько диапазонов.",
        "type": "multi",   # ★ MULTI
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
        "q": "📅 Желаемые сроки внедрения",
        "type": "single",
        "opts": [
            "До 3 месяцев — быстрый старт",
            "3–6 месяцев — стандартный SaaS",
            "6–12 месяцев — сложный проект",
            "Свыше 12 месяцев / поэтапный rollout",
        ],
    },
    {
        "id": "priority", "block": "main",
        "q": "⭐️ Что важнее при выборе ERP?",
        "sub": "Выберите главный приоритет",
        "type": "single",
        "opts": [
            "Глубина отраслевой функциональности",
            "Простота внедрения и скорость старта",
            "Минимальная стоимость владения (TCO)",
            "Гибкость и возможность кастомизации",
            "Экосистема партнёров и поддержка",
            "Открытый исходный код / независимость от вендора",
        ],
    },

    # ── Блок 3: Партнёр ───────────────────────────────────────────────────
    {
        "id": "has_team", "block": "partner",
        "q": "👨‍💼 Есть ли внутренняя IT-команда для поддержки ERP?",
        "sub": "Можно выбрать несколько — отметьте всё что есть",
        "type": "multi",   # ★ MULTI
        "opts": [
            "Опытные ERP-архитекторы / консультанты",
            "IT-команда общего профиля (без ERP-специализации)",
            "Финансовые аналитики / ключевые пользователи",
            "SAP-сертифицированные специалисты",
            "Разработчики (для кастомизации)",
            "Нет IT-команды — полностью на партнёре",
            "Планируем нанять после выбора системы",
        ],
    },
    {
        "id": "partner_concerns", "block": "partner",
        "q": "🤝 Что важно при выборе партнёра по внедрению?",
        "sub": "Можно выбрать несколько. Нажмите «Готово» когда закончите.",
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
    {"id": "contact_name",    "q": "👤 Ваше имя и фамилия?"},
    {"id": "contact_role",    "q": "💼 Ваша должность?"},
    {"id": "contact_company", "q": "🏢 Название компании?"},
    {"id": "contact_country", "q": "🌐 Страна / регион?"},
    {"id": "contact_email",   "q": "📧 Ваш email?"},
    {"id": "contact_phone",   "q": "📱 Телефон или Telegram (@username)?"},
    {
        "id": "contact_comment",
        "q": "💬 Дополнительный контекст (необязательно)\n\n"
             "Специфика процессов, интеграции с внешними системами, "
             "особые требования. Или /skip чтобы пропустить."
    },
]

ERP_DB: dict[str, dict] = {
    "sap_s4_public": {
        "name": "SAP S/4HANA Cloud, Public Edition",
        "vendor": "SAP",
        "deploy_types": ["cloud"],
        "tco": "$$$$",
        "url": "https://www.sap.com/products/erp/s4hana-cloud.html",
        "community": "https://community.sap.com/t5/sap-s-4hana-cloud/ct-p/S4HANAcloud",
        "strengths": ["Стандарт mid-market → enterprise", "Быстрый старт 3–6 мес (SAP Activate)", "Широкая экосистема партнёров", "Регулярные облачные обновления"],
        "weaknesses": ["Ограниченная кастомизация", "Выше цена vs альтернативы", "Только Public Cloud"],
        "industries": ["Нефть", "Производство", "Фарма", "Банки", "Дистрибуция", "Оптовая", "Энергет"],
    },
    "sap_s4_private": {
        "name": "SAP S/4HANA Private / On-Premise",
        "vendor": "SAP",
        "deploy_types": ["onprem", "private"],
        "tco": "$$$$$",
        "url": "https://www.sap.com/products/erp/s4hana-private-cloud.html",
        "community": "https://community.sap.com/t5/sap-s-4hana/ct-p/S4HANA",
        "strengths": ["Максимальная кастомизация", "Полный контроль данных", "Отраслевые расширения IS-Oil/Mining", "Госсектор и оборонка"],
        "weaknesses": ["Самый высокий TCO", "Внедрение 9–18 мес", "Требует большой IT-команды"],
        "industries": ["Нефть", "Горнодоб", "Аэрокосмос", "Государств", "Производство процессное"],
    },
    "sap_b1": {
        "name": "SAP Business One",
        "vendor": "SAP",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$",
        "url": "https://www.sap.com/products/erp/business-one.html",
        "community": "https://community.sap.com/t5/sap-business-one/ct-p/businessone",
        "strengths": ["Быстрый старт 1–3 мес", "Доступная цена", "Облако и on-prem"],
        "weaknesses": ["Только малый бизнес", "Нет масштабирования до enterprise"],
        "industries": ["Оптовая", "Дистрибуция", "Производство дискретное", "Ритейл"],
    },
    "oracle_fusion": {
        "name": "Oracle Fusion Cloud ERP",
        "vendor": "Oracle",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$$$$",
        "url": "https://www.oracle.com/erp/",
        "community": "https://community.oracle.com",
        "strengths": ["Сильная финансовая функциональность", "AI встроен нативно", "Мультиюрисдикция"],
        "weaknesses": ["Высокая стоимость", "Долгое внедрение", "Меньше партнёров чем у SAP"],
        "industries": ["Банки", "Страхование", "Государств", "Телеком", "Энергет"],
    },
    "netsuite": {
        "name": "Oracle NetSuite",
        "vendor": "Oracle",
        "deploy_types": ["cloud"],
        "tco": "$$$",
        "url": "https://www.netsuite.com",
        "community": "https://community.netsuite.com",
        "strengths": ["Нативный SaaS с 1998 г.", "Быстрый старт", "Мультивалюта / мультиентити", "Цена / функционал"],
        "weaknesses": ["Слабее для производства", "Кастомизация через SuiteScript"],
        "industries": ["Оптовая", "Дистрибуция", "Ритейл", "IT", "Стартапы"],
    },
    "dynamics": {
        "name": "Microsoft Dynamics 365",
        "vendor": "Microsoft",
        "deploy_types": ["cloud", "hybrid"],
        "tco": "$$$",
        "url": "https://dynamics.microsoft.com",
        "community": "https://community.dynamics.com",
        "strengths": ["Интеграция M365 / Azure / Copilot AI", "Гибкая модульность", "Знакомый UI", "Hybrid возможен"],
        "weaknesses": ["Запутанное лицензирование", "Производство слабее SAP"],
        "industries": ["Производство дискретное", "Ритейл", "IT", "Дистрибуция", "Банки"],
    },
    "infor": {
        "name": "Infor CloudSuite",
        "vendor": "Infor",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$$$",
        "url": "https://www.infor.com",
        "community": "https://inforum.infor.com",
        "strengths": ["Глубокая отраслевая специализация", "Лидер в здравоохранении и дистрибуции", "Аналитика Birst"],
        "weaknesses": ["Меньше партнёров", "Менее известен в СНГ"],
        "industries": ["Здравоохр", "Фарма", "Производство", "Дистрибуция", "Аэрокосмос"],
    },
    "epicor": {
        "name": "Epicor Kinetic",
        "vendor": "Epicor",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$$",
        "url": "https://www.epicor.com/en/products/erp/kinetic/",
        "community": "https://epicor.com/community",
        "strengths": ["Специализация на производстве", "Гибкое развёртывание", "Отраслевые best practices"],
        "weaknesses": ["Слабее вне производства", "Меньше глобальной сети"],
        "industries": ["Производство дискретное", "Производство процессное", "Аэрокосмос"],
    },
    "acumatica": {
        "name": "Acumatica Cloud ERP",
        "vendor": "Acumatica",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$",
        "url": "https://www.acumatica.com",
        "community": "https://community.acumatica.com",
        "strengths": ["Безлимитные пользователи — оплата за ресурсы", "Быстрое внедрение", "Современный UI"],
        "weaknesses": ["Не для крупного enterprise", "Меньше отраслевых решений"],
        "industries": ["Ритейл", "Дистрибуция", "Строительство", "IT"],
    },
    "odoo": {
        "name": "Odoo (Community / Enterprise)",
        "vendor": "Odoo",
        "deploy_types": ["cloud", "onprem", "open"],
        "tco": "$",
        "url": "https://www.odoo.com",
        "community": "https://www.odoo.com/forum",
        "strengths": ["Open Source Community версия", "Самый низкий TCO", "Модульность — берёте только нужное"],
        "weaknesses": ["Сложен для крупного бизнеса", "Требует разработчика для кастомизации"],
        "industries": ["Стартапы", "IT", "Ритейл", "Дистрибуция", "Оптовая"],
    },
    "erpnext": {
        "name": "ERPNext / Frappe",
        "vendor": "Frappe",
        "deploy_types": ["cloud", "onprem", "open"],
        "tco": "$",
        "url": "https://erpnext.com",
        "community": "https://discuss.frappe.io",
        "strengths": ["100% Open Source", "Нулевые лицензии", "Активное сообщество"],
        "weaknesses": ["Требует Python-разработчика", "Слабее для сложного производства"],
        "industries": ["Стартапы", "IT", "Дистрибуция", "Агробизнес"],
    },
    "ifs": {
        "name": "IFS Cloud",
        "vendor": "IFS",
        "deploy_types": ["cloud", "onprem"],
        "tco": "$$$$",
        "url": "https://www.ifs.com",
        "community": "https://community.ifs.com",
        "strengths": ["Лидер для asset-intensive отраслей", "Сильный FSM (Field Service)", "Аэрокосмос и оборона"],
        "weaknesses": ["Нишевый продукт", "Дорогой вне ключевых отраслей"],
        "industries": ["Аэрокосмос", "Энергет", "Логистика", "Производство"],
    },
}

TCO_LABELS = {
    "$": "Низкий TCO",
    "$$": "Ниже среднего",
    "$$$": "Средний",
    "$$$$": "Выше среднего",
    "$$$$$": "Высокий",
}

BUDGET_SCORE_MAP = {
    "До $30K":       {"sap_b1": 10, "odoo": 20, "erpnext": 20, "acumatica": 15},
    "$30K – $150K":  {"sap_b1": 18, "odoo": 15, "netsuite": 12, "dynamics": 10, "acumatica": 15, "epicor": 10},
    "$150K – $500K": {"netsuite": 15, "dynamics": 15, "sap_b1": 12, "epicor": 12, "infor": 10, "sap_s4_public": 10},
    "$500K – $1M":   {"sap_s4_public": 18, "dynamics": 15, "netsuite": 15, "infor": 12, "epicor": 12},
    "$1M – $2M":     {"sap_s4_private": 18, "sap_s4_public": 15, "oracle_fusion": 15, "infor": 15, "ifs": 15},
    "Свыше $2M":     {"sap_s4_private": 18, "oracle_fusion": 18, "ifs": 15},
}


def _get_deploy_filter(ans: dict) -> str:
    dc = ans.get("datacenter", "")
    if "Нет — предпочитаем облако" in dc:  return "cloud_only"
    if "Private Cloud у вендора" in dc:    return "private_ok"
    if "есть собственный" in dc or "построить" in dc: return "onprem_ok"
    if "гибридная" in dc:                  return "hybrid_ok"
    return "any"


def _deploy_allowed(erp_key: str, deploy_filter: str) -> bool:
    dt = ERP_DB[erp_key]["deploy_types"]
    if deploy_filter == "cloud_only":  return "cloud" in dt
    if deploy_filter == "private_ok":  return "cloud" in dt or "private" in dt
    if deploy_filter == "onprem_ok":   return True
    if deploy_filter == "hybrid_ok":   return any(x in dt for x in ["cloud", "hybrid", "onprem"])
    return True


def _budget_score(erp_key: str, budgets: list[str]) -> int:
    max_s = 0
    for b in budgets:
        s = BUDGET_SCORE_MAP.get(b, {}).get(erp_key, 0)
        if s > max_s:
            max_s = s
    return max_s


def _team_score(erp_key: str, teams: list[str]) -> int:
    teams_str = " ".join(teams)
    has_experts = any(k in teams_str for k in ["ERP-архитектор", "SAP-сертифицир", "Разработчик"])
    has_none = "Нет IT" in teams_str
    heavy = ["sap_s4_private", "oracle_fusion", "ifs"]
    light = ["sap_s4_public", "netsuite", "dynamics", "acumatica"]
    if has_experts and erp_key in heavy:   return 12
    if has_none and erp_key in heavy:      return -10
    if has_none and erp_key in ["odoo", "erpnext"]: return -8
    if has_none and erp_key in light:      return 8
    return 0


def _score(erp_key: str, ans: dict) -> int:
    s = 0
    e = ERP_DB[erp_key]
    industry = ans.get("industry", "")
    size     = ans.get("size", "")
    dc       = ans.get("datacenter", "")
    priority = ans.get("priority", "")
    areas    = ans.get("areas", [])
    current  = ans.get("current", "")
    timeline = ans.get("timeline", "")
    budgets  = ans.get("budget", [])
    teams    = ans.get("has_team", [])
    if isinstance(budgets, str): budgets = [budgets]
    if isinstance(teams, str):   teams = [teams]

    # Industry
    for ind in e["industries"]:
        if ind in industry:
            s += 30
            break

    # Size
    is_small = "до 50" in size or "50–200" in size
    is_mid   = "200–1000" in size
    is_large = "1000" in size or "10 000+" in size
    if is_small and erp_key in ["sap_b1", "odoo", "erpnext", "acumatica", "netsuite"]:  s += 22
    if is_mid   and erp_key in ["netsuite", "dynamics", "acumatica", "sap_s4_public", "epicor", "infor"]: s += 22
    if is_large and erp_key in ["sap_s4_public", "sap_s4_private", "oracle_fusion", "dynamics", "infor", "ifs"]: s += 22

    # Budget
    s += _budget_score(erp_key, budgets)

    # Datacenter / deploy
    if "есть собственный" in dc or "построить" in dc:
        if erp_key in ["sap_s4_private", "oracle_fusion", "ifs", "infor"]: s += 25
    if "Private Cloud у вендора" in dc:
        if erp_key in ["sap_s4_private", "oracle_fusion", "dynamics", "infor"]: s += 22
    if "Нет — предпочитаем облако" in dc:
        if erp_key in ["sap_s4_public", "netsuite", "dynamics", "acumatica", "odoo"]: s += 22
        if erp_key == "sap_s4_private": s -= 20
    if "гибридная" in dc:
        if erp_key in ["dynamics", "sap_s4_private", "epicor", "ifs"]: s += 15

    # Timeline
    if "До 3" in timeline   and erp_key in ["odoo", "sap_b1", "acumatica", "erpnext"]: s += 15
    if "3–6" in timeline    and erp_key in ["sap_s4_public", "netsuite", "dynamics", "acumatica"]: s += 15
    if "6–12" in timeline   and erp_key in ["sap_s4_private", "oracle_fusion", "infor", "ifs", "epicor"]: s += 15
    if "12 мес" in timeline and erp_key in ["sap_s4_private", "oracle_fusion", "ifs"]: s += 15

    # Priority
    if "отраслевой" in priority and erp_key in ["sap_s4_public", "sap_s4_private", "infor", "ifs", "epicor"]: s += 15
    if "Простота"   in priority and erp_key in ["odoo", "netsuite", "acumatica", "sap_b1"]: s += 15
    if "TCO"        in priority and erp_key in ["odoo", "erpnext", "acumatica", "sap_b1"]: s += 20
    if "Гибкость"   in priority and erp_key in ["odoo", "dynamics", "acumatica", "erpnext"]: s += 15
    if "Экосистема" in priority and erp_key in ["sap_s4_public", "dynamics", "netsuite"]: s += 15
    if "открытый"   in priority and erp_key in ["odoo", "erpnext"]: s += 30

    # Current system migration bonus
    if "SAP ECC" in current   and erp_key in ["sap_s4_public", "sap_s4_private"]: s += 25
    if "Microsoft" in current and erp_key == "dynamics":  s += 20
    if "Oracle" in current    and erp_key in ["oracle_fusion", "netsuite"]: s += 15

    # Functional areas
    if "Производство / MES" in areas      and erp_key in ["sap_s4_public", "sap_s4_private", "epicor", "infor"]: s += 10
    if "ESG" in " ".join(areas)           and erp_key in ["sap_s4_public", "sap_s4_private"]: s += 15
    if "EAM" in " ".join(areas)           and erp_key in ["sap_s4_private", "ifs", "infor"]: s += 12

    # Team
    s += _team_score(erp_key, teams)

    return s


def get_top3(ans: dict) -> list[dict]:
    """Возвращает Top-3 ERP с учётом фильтра деплоя и скоринга."""
    deploy_filter = _get_deploy_filter(ans)
    candidates = [k for k in ERP_DB if _deploy_allowed(k, deploy_filter)]
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
    """Возвращает только те шаги, которые должны показываться клиенту."""
    return [s for s in STEPS if not s.get("conditional") or s["conditional"](ans)]


def format_top3_text(top3: list[dict], ans: dict) -> str:
    """Форматирует Top-3 для отображения в Telegram."""
    deploy_filter = _get_deploy_filter(ans)
    filter_labels = {
        "cloud_only": "☁️ Только облачные решения",
        "private_ok": "🔒 Облако + Private Cloud",
        "onprem_ok":  "🏢 Cloud + On-Premise доступны",
        "hybrid_ok":  "🔀 Гибридная модель",
        "any":        "Все варианты деплоя",
    }

    budgets = ans.get("budget", [])
    if isinstance(budgets, str): budgets = [budgets]
    budget_str = ", ".join(b for b in budgets if b != "Не готовы раскрывать") or "не указан"

    lines = [
        f"🎯 *Фильтр деплоя:* {filter_labels[deploy_filter]}",
        f"💰 *Бюджет:* {budget_str}",
        "",
    ]
    medals = ["🥇", "🥈", "🥉"]
    labels = ["Лучший выбор", "Сильная альтернатива", "Выгодно по TCO"]

    for i, erp in enumerate(top3):
        tco_label = TCO_LABELS.get(erp["tco"], erp["tco"])
        pros = " · ".join(erp["strengths"][:2])
        lines += [
            f"{medals[i]} *{labels[i]}*",
            f"*{erp['name']}* ({erp['vendor']})",
            f"TCO: {tco_label} ({erp['tco']}) | {erp['deploy_types'][0].upper()}",
            f"✅ {pros}",
            f"🔗 [sap.com / официальный сайт]({erp['url']})",
            "",
        ]

    lines.append(
        "_🧘 ERP Yoga Bot (@SAPyogaBOT) — независимый советник. "
        "Рекомендации основаны на официальных сайтах вендоров и аналитических источниках. "
        "Разработан сертифицированными экспертами. "
        "Окончательный выбор уточняется после детального анализа требований._"
    )
    return "\n".join(lines)
