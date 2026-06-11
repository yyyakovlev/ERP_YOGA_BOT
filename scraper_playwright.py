"""
ERP Yoga Bot — scraper_playwright.py
Парсит сайты вендоров через реальный браузер Chromium.
Обходит Cloudflare, JavaScript-рендеринг и bot-detection.

УСТАНОВКА:
    pip install playwright
    playwright install chromium

ЗАПУСК:
    python scraper_playwright.py                    # все системы
    python scraper_playwright.py --id sap_s4_public # одна система
    python scraper_playwright.py --dry-run          # без записи в KB
    python scraper_playwright.py --headed           # с видимым браузером (отладка)

ПРИМЕЧАНИЕ:
    Запускать локально — серверные IP блокируются даже с браузером.
    Скрипт обновляет только поля *_scraped, не трогая ручные данные в KB.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

KB_PATH = Path(__file__).parent / "knowledge_base.json"
RAW_DIR = Path(__file__).parent / "scraper_output"
RAW_DIR.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ── Источники ─────────────────────────────────────────────────────────────────

SOURCES: dict[str, dict] = {
    "sap_s4_public": {
        "urls": ["https://www.sap.com/products/erp/s4hana-cloud.html"],
        "wait_for": "div.content-text, div.text-component, main",
        "desc_selectors": ["div.content-text p", "div.text-component p", "main p"],
        "feat_selectors": ["ul.content-list li", "div.feature-item h3", "div.feature-title"],
    },
    "sap_s4_private": {
        "urls": ["https://www.sap.com/products/erp/s4hana-private-cloud.html"],
        "wait_for": "main",
        "desc_selectors": ["div.content-text p", "div.text-component p", "main p"],
        "feat_selectors": ["ul.content-list li"],
    },
    "sap_b1": {
        "urls": ["https://www.sap.com/products/erp/business-one.html"],
        "wait_for": "main",
        "desc_selectors": ["div.content-text p", "div.text-component p", "main p"],
        "feat_selectors": ["ul.content-list li"],
    },
    "oracle_fusion": {
        "urls": [
            "https://www.oracle.com/erp/",
            "https://www.oracle.com/erp/what-is-erp/",
        ],
        "wait_for": "main, #main",
        "desc_selectors": ["div.cc01-blurb-content p", "section p", "div.card-body p"],
        "feat_selectors": ["div.rc24 h3", "ul li", "h3.u20icon"],
    },
    "dynamics": {
        "urls": [
            "https://www.microsoft.com/en-us/dynamics-365/solutions/erp",
            "https://www.microsoft.com/ru-ru/dynamics-365/",
        ],
        "wait_for": "main, .m-content-placement",
        "desc_selectors": [
            "div.m-content-placement p",
            "section.ocr p",
            "div[class*='content'] p",
            "main p",
        ],
        "feat_selectors": [
            "h2[class*='heading']",
            "h3[class*='heading']",
            "ul[class*='list'] li",
        ],
    },
    "ifs": {
        "urls": [
            "https://www.ifs.com/en/ifs-cloud",
            "https://www.ifs.com/en/products/erp",
        ],
        "wait_for": "main, .hero, section",
        "desc_selectors": [
            "div.hero__text p",
            "div.rich-text p",
            "section[class*='content'] p",
            "div[class*='block'] p",
            "main p",
        ],
        "feat_selectors": [
            "div.card__title",
            "ul[class*='check'] li",
            "h2", "h3",
        ],
    },
    "epicor": {
        "urls": [
            "https://www.epicor.com/en-us/products/enterprise-resource-planning-erp/kinetic/",
            "https://www.epicor.com/en-us/products/enterprise-resource-planning-erp/kinetic/cloud-business-platform/",
        ],
        "wait_for": "main, .hero, section",
        "desc_selectors": [
            "div[class*='hero'] p",
            "div[class*='content'] p",
            "section[class*='intro'] p",
            "main p",
        ],
        "feat_selectors": [
            "h2[class*='heading']",
            "h3",
            "ul[class*='list'] li",
            "div[class*='card'] p",
        ],
    },
    "odoo": {
        "urls": [
            "https://www.odoo.com/page/erp",
            "https://www.odoo.com/",
        ],
        "wait_for": "main, #wrap",
        "desc_selectors": ["section.o_hero p", "div.o_section p", "main p"],
        "feat_selectors": ["div.card-body p", "h3", "ul li"],
    },
    "erpnext": {
        "urls": ["https://erpnext.com/"],
        "wait_for": "main, body",
        "desc_selectors": ["section.hero p", "div.section-body p", "main p"],
        "feat_selectors": ["div.feature__title", "ul li", "h3"],
    },
}

# ── Утилиты ──────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_useful(text: str, min_len: int = 60) -> bool:
    """Отбрасывает навигацию, кнопки, мусор."""
    if len(text) < min_len:
        return False
    noise = [
        "cookie", "accept", "privacy", "terms of", "sign in", "log in",
        "subscribe", "newsletter", "©", "all rights reserved",
        "capture a web page", "archive team", "wayback machine",
        "javascript", "enable cookies", "please wait",
    ]
    t = text.lower()
    return not any(n in t for n in noise)


def extract_description(page: Page, selectors: list[str], max_len: int = 900) -> str:
    """Извлекает описание из загруженной страницы."""
    for sel in selectors:
        try:
            elements = page.query_selector_all(sel)
            texts = []
            for el in elements:
                t = clean(el.inner_text())
                if is_useful(t):
                    texts.append(t)
                if sum(len(x) for x in texts) > max_len:
                    break
            if texts:
                combined = " ".join(texts)
                return combined[:max_len]
        except Exception:
            continue

    # Fallback: все <p> на странице
    try:
        paras = page.query_selector_all("p")
        texts = [clean(p.inner_text()) for p in paras if is_useful(clean(p.inner_text()))]
        if texts:
            return " ".join(texts[:4])[:max_len]
    except Exception:
        pass

    return ""


def extract_features(page: Page, selectors: list[str], max_n: int = 8) -> list[str]:
    """Извлекает список ключевых возможностей."""
    for sel in selectors:
        try:
            elements = page.query_selector_all(sel)
            items = []
            for el in elements:
                t = clean(el.inner_text())
                if 15 < len(t) < 150 and is_useful(t, min_len=15):
                    items.append(t)
            if len(items) >= 3:
                seen, unique = set(), []
                for t in items:
                    k = t.lower()[:40]
                    if k not in seen:
                        seen.add(k)
                        unique.append(t)
                return unique[:max_n]
        except Exception:
            continue
    return []


# ── Браузерный парсер ────────────────────────────────────────────────────────

def scrape_one(
    browser: Browser,
    erp_id: str,
    config: dict,
    headed: bool = False,
) -> dict:
    log.info(f"\n[{erp_id}] Scraping...")

    result = {
        "id": erp_id,
        "scraped_at": NOW,
        "descriptions": [],
        "features": [],
        "urls_ok": [],
        "urls_failed": [],
    }

    # Контекст с реалистичными настройками браузера
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        # Скрываем что это автоматизированный браузер
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        },
    )

    # Скрипт для обхода bot-detection
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        window.chrome = { runtime: {} };
    """)

    for i, url in enumerate(config["urls"]):
        page = context.new_page()
        try:
            log.info(f"  GET {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Ждём появления контента
            wait_sel = config.get("wait_for", "main")
            try:
                page.wait_for_selector(wait_sel, timeout=8_000)
            except PWTimeout:
                log.info(f"  wait_for '{wait_sel}' timed out — continuing anyway")

            # Пауза для JS-рендеринга
            page.wait_for_timeout(2_000)

            # Закрываем cookie-баннеры
            for btn_text in ["Accept", "Accept All", "Accept Cookies", "I agree", "Got it"]:
                try:
                    btn = page.get_by_role("button", name=re.compile(btn_text, re.I))
                    if btn.count() > 0:
                        btn.first.click(timeout=2_000)
                        page.wait_for_timeout(500)
                except Exception:
                    pass

            desc  = extract_description(page, config.get("desc_selectors", []))
            feats = extract_features(page, config.get("feat_selectors", []))

            if desc:
                result["descriptions"].append(desc)
                log.info(f"  ✅ description: {desc[:80]}...")
            else:
                log.warning(f"  ⚠️  no description extracted")

            if feats:
                result["features"].extend(feats)
                log.info(f"  ✅ features: {len(feats)} items")

            result["urls_ok"].append(url)

        except PWTimeout:
            log.warning(f"  ❌ Timeout: {url}")
            result["urls_failed"].append(url)
        except Exception as e:
            log.warning(f"  ❌ Error {url}: {type(e).__name__}: {e}")
            result["urls_failed"].append(url)
        finally:
            page.close()
            if i < len(config["urls"]) - 1:
                time.sleep(3)

    context.close()

    # Дедупликация фич
    seen, dedup = set(), []
    for f in result["features"]:
        k = f.lower()[:40]
        if k not in seen:
            seen.add(k)
            dedup.append(f)
    result["features"] = dedup[:8]

    status = "✅" if result["urls_ok"] else "❌"
    log.info(
        f"  {status} {erp_id}: {len(result['descriptions'])} desc, "
        f"{len(result['features'])} features, "
        f"{len(result['urls_failed'])} failed"
    )
    return result


# ── Merge ────────────────────────────────────────────────────────────────────

def merge_into_kb(scraped: dict, kb: dict) -> tuple[dict, bool]:
    """Возвращает (обновлённый kb, был_ли_изменён)."""
    erp_id = scraped["id"]
    system = next((s for s in kb["erp_systems"] if s["id"] == erp_id), None)
    if not system:
        log.warning(f"  {erp_id} not found in knowledge_base")
        return kb, False

    changed = False

    if scraped["descriptions"]:
        best = max(scraped["descriptions"], key=len)
        if len(best) > 100:
            system["description_scraped"] = best
            changed = True

    if scraped["features"]:
        system["key_features_scraped"] = scraped["features"]
        changed = True

    if scraped["urls_ok"]:
        system["url_official"] = scraped["urls_ok"][0]

    system["scraped_at"] = scraped["scraped_at"]
    return kb, changed


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="ERP Yoga Bot — Playwright scraper")
    ap.add_argument("--id",       type=str,   default=None,  help="Парсить одну систему")
    ap.add_argument("--dry-run",  action="store_true",        help="Без записи в KB")
    ap.add_argument("--headed",   action="store_true",        help="Видимый браузер (отладка)")
    ap.add_argument("--delay",    type=float, default=4.0,    help="Пауза между вендорами (сек)")
    ap.add_argument("--timeout",  type=int,   default=30,     help="Таймаут страницы (сек)")
    args = ap.parse_args()

    if not KB_PATH.exists():
        log.error(f"knowledge_base.json not found: {KB_PATH}")
        return

    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)

    log.info(f"KB: {len(kb['erp_systems'])} systems | mode: dry_run={args.dry_run} headed={args.headed}")

    # Выбираем что парсить
    if args.id:
        if args.id not in SOURCES:
            log.error(f"Unknown id '{args.id}'. Available: {list(SOURCES)}")
            return
        targets = {args.id: SOURCES[args.id]}
    else:
        targets = SOURCES

    results: dict[str, dict] = {}
    changed_ids: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not args.headed,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
            ],
        )
        log.info(f"Browser: Chromium {browser.version}")

        for i, (eid, cfg) in enumerate(targets.items()):
            try:
                scraped = scrape_one(browser, eid, cfg, headed=args.headed)

                # Сохраняем сырые данные
                raw_path = RAW_DIR / f"{eid}_pw_raw.json"
                with open(raw_path, "w", encoding="utf-8") as f:
                    json.dump(scraped, f, ensure_ascii=False, indent=2)

                results[eid] = scraped

                if not args.dry_run:
                    kb, changed = merge_into_kb(scraped, kb)
                    if changed:
                        changed_ids.append(eid)

            except Exception as e:
                log.error(f"FAILED {eid}: {e}")
                results[eid] = {
                    "id": eid, "urls_ok": [], "urls_failed": ["exception"],
                    "descriptions": [], "features": [],
                }

            if i < len(targets) - 1:
                log.info(f"Waiting {args.delay}s...")
                time.sleep(args.delay)

        browser.close()

    # Сохраняем KB
    if not args.dry_run and changed_ids:
        backup = KB_PATH.with_suffix(".backup.json")
        shutil.copy(KB_PATH, backup)
        kb["meta"]["scraped_at"] = NOW
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        log.info(f"\n✅ KB updated: {changed_ids}")
        log.info(f"Backup: {backup.name}")
    elif args.dry_run:
        log.info("\n[DRY RUN] Nothing written.")
    else:
        log.info("\nNo changes to write.")

    # Отчёт
    ok      = [k for k, v in results.items() if v["urls_ok"]]
    blocked = [k for k, v in results.items() if not v["urls_ok"]]
    partial = [k for k, v in results.items() if v["urls_ok"] and v["urls_failed"]]

    print(f"\n{'─'*60}")
    print(f"  PLAYWRIGHT SCRAPING REPORT  {NOW}")
    print(f"{'─'*60}")
    print(f"  Total:    {len(targets)}")
    print(f"  Success:  {len(ok)}")
    print(f"  Partial:  {len(partial)}")
    print(f"  Blocked:  {len(blocked)}")
    if ok:
        print()
        for eid in ok:
            r = results[eid]
            has_desc = "✅" if r["descriptions"] else "⚠️ "
            print(f"  {has_desc} {eid:<22} desc={len(r['descriptions'])}  feat={len(r['features'])}")
    if blocked:
        print()
        for eid in blocked:
            print(f"  ❌  {eid}")
    if not args.dry_run and changed_ids:
        print(f"\n  KB updated: {', '.join(changed_ids)}")
    print(f"  Raw files: {RAW_DIR}/")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
