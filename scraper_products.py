"""
ERP Yoga Bot — scraper_products.py
Парсит официальные страницы вендоров и обновляет knowledge_base.json

РЕЖИМЫ ЗАПУСКА:
  python scraper_products.py                     # все системы, прямой HTTP
  python scraper_products.py --dry-run           # показать без записи
  python scraper_products.py --id sap_s4_public  # одна система
  python scraper_products.py --via-archive       # через web.archive.org (обход блокировок)

ПРИМЕЧАНИЕ:
  Некоторые вендорские сайты блокируют серверные запросы (403).
  В этом случае используйте --via-archive или запускайте локально с реального IP.
  Данные в knowledge_base.json заполнены вручную экспертами и служат основой.
  Парсер обновляет только поля *_scraped, не затрагивая ручные данные.

GitHub Actions: запускать раз в квартал через cron
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

KB_PATH  = Path(__file__).parent / "knowledge_base.json"
RAW_DIR  = Path(__file__).parent / "scraper_output"
RAW_DIR.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ── Источники ─────────────────────────────────────────────────────────────────

SOURCES: dict[str, dict] = {
    "sap_s4_public": {
        "urls": [
            "https://www.sap.com/products/erp/s4hana-cloud.html",
            "https://www.sap.com/products/erp/grow.html",
        ],
        "desc_selectors":    ["div.content-text p", "div.text-component p", "p.content-body"],
        "feature_selectors": ["ul.content-list li", "div.feature-item h3"],
    },
    "sap_s4_private": {
        "urls": [
            "https://www.sap.com/products/erp/s4hana-private-cloud.html",
        ],
        "desc_selectors":    ["div.content-text p", "div.text-component p"],
        "feature_selectors": ["ul.content-list li"],
    },
    "sap_b1": {
        "urls": [
            "https://www.sap.com/products/erp/business-one.html",
        ],
        "desc_selectors":    ["div.content-text p", "div.text-component p"],
        "feature_selectors": ["ul.content-list li"],
    },
    "oracle_fusion": {
        "urls": [
            "https://www.oracle.com/erp/",
            "https://www.oracle.com/erp/what-is-erp/",
        ],
        "desc_selectors":    ["div.cc01-blurb-content p", "div.card-body p", "section.u20 p"],
        "feature_selectors": ["div.rc24 h3", "ul.obr-lc5-list li"],
    },
    "netsuite": {
        "urls": [
            "https://www.netsuite.com/portal/products/erp.shtml",
        ],
        "desc_selectors":    ["div.NS-body-content p", "section.hero p", "div.ns-content p"],
        "feature_selectors": ["div.feature-desc p", "ul.ns-list li"],
    },
    "dynamics": {
        "urls": [
            "https://dynamics.microsoft.com/en-us/erp/what-is-erp/",
            "https://dynamics.microsoft.com/en-us/finance/overview/",
        ],
        "desc_selectors":    ["div.m-content-placement p", "p.c-paragraph-3", "div[data-m]>p"],
        "feature_selectors": ["ul.c-list li", "h3.c-heading-4"],
    },
    "infor": {
        "urls": [
            "https://www.infor.com/products/cloudsuite-industrial-enterprise",
            "https://www.infor.com/erp",
        ],
        "desc_selectors":    ["div.hero__description p", "div.rte p", "div.content-block p"],
        "feature_selectors": ["ul.feature-list li", "div.card__body p"],
    },
    "ifs": {
        "urls": [
            "https://www.ifs.com/products/ifs-cloud/",
            "https://www.ifs.com/products/enterprise-resource-planning/",
        ],
        "desc_selectors":    ["div.hero__text p", "div.rich-text p", "section.intro p"],
        "feature_selectors": ["div.card__title", "ul.list--check li"],
    },
    "epicor": {
        "urls": [
            "https://www.epicor.com/en/products/erp/kinetic/",
        ],
        "desc_selectors":    ["div.hero__content p", "div.rte-content p", "p.lead"],
        "feature_selectors": ["div.card-body p", "ul.check-list li"],
    },
    "acumatica": {
        "urls": [
            "https://www.acumatica.com/cloud-erp-software/",
            "https://www.acumatica.com/why-acumatica/",
        ],
        "desc_selectors":    ["div.hero__content p", "section.intro p", "div.content-area p"],
        "feature_selectors": ["ul.benefits li", "div.feature-item__title"],
    },
    "odoo": {
        "urls": [
            "https://www.odoo.com/page/erp",
            "https://www.odoo.com/",
        ],
        "desc_selectors":    ["section.o_hero p", "div#wrap .container p", "p.lead"],
        "feature_selectors": ["div.card-body p", "div.o_field_widget p"],
    },
    "erpnext": {
        "urls": [
            "https://erpnext.com/",
        ],
        "desc_selectors":    ["section.hero p", "div.section-body p", "div.intro p"],
        "feature_selectors": ["div.feature__title", "ul.features-list li"],
    },
}

# ── Заголовки запросов ────────────────────────────────────────────────────────

HEADERS_CHROME = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def archive_url(url: str) -> str:
    """Возвращает URL через web.archive.org (Wayback Machine)."""
    return f"https://web.archive.org/web/2024/{url}"


def fetch_url(url: str, via_archive: bool = False, timeout: int = 25) -> Optional[str]:
    """Загружает страницу. При via_archive использует Wayback Machine."""
    target = archive_url(url) if via_archive else url
    try:
        with httpx.Client(
            headers=HEADERS_CHROME,
            follow_redirects=True,
            timeout=timeout,
            verify=True,
        ) as client:
            resp = client.get(target)
            if resp.status_code == 403:
                log.warning(f"  403 Forbidden: {url}")
                if not via_archive:
                    log.info(f"  Retrying via web.archive.org...")
                    return fetch_url(url, via_archive=True, timeout=timeout)
                return None
            resp.raise_for_status()
            log.info(f"  GET {url} → {resp.status_code} ({len(resp.text):,} chars)")
            return resp.text
    except httpx.TimeoutException:
        log.warning(f"  TIMEOUT: {url}")
    except httpx.HTTPStatusError as e:
        log.warning(f"  HTTP {e.response.status_code}: {url}")
    except Exception as e:
        log.warning(f"  ERROR {url}: {type(e).__name__}: {e}")
    return None


# ── Парсинг ───────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s.,;:!?()\-/&\'\"]+', '', text)
    return text


def extract_description(soup: BeautifulSoup, selectors: list[str], max_len: int = 800) -> str:
    for sel in selectors:
        elements = soup.select(sel)
        texts = [clean(el.get_text()) for el in elements if len(clean(el.get_text())) > 60]
        if texts:
            combined = ' '.join(texts)
            return (combined[:max_len].rsplit(' ', 1)[0] + '…') if len(combined) > max_len else combined
    # Fallback: любые <p> достаточной длины
    paras = [clean(p.get_text()) for p in soup.find_all('p') if len(clean(p.get_text())) > 80]
    combined = ' '.join(paras[:4])
    return combined[:max_len] if combined else ""


def extract_features(soup: BeautifulSoup, selectors: list[str], max_n: int = 8) -> list[str]:
    for sel in selectors:
        items = [clean(el.get_text()) for el in soup.select(sel)]
        items = [t for t in items if 15 < len(t) < 150]
        if len(items) >= 3:
            seen, unique = set(), []
            for t in items:
                k = t.lower()[:40]
                if k not in seen:
                    seen.add(k); unique.append(t)
            return unique[:max_n]
    return []


def scrape_one(erp_id: str, config: dict, via_archive: bool = False) -> dict:
    log.info(f"\nScraping [{erp_id}]...")
    result = {
        "id": erp_id,
        "scraped_at": NOW,
        "descriptions": [],
        "features": [],
        "urls_ok": [],
        "urls_failed": [],
    }

    for i, url in enumerate(config["urls"]):
        html = fetch_url(url, via_archive=via_archive)
        if not html:
            result["urls_failed"].append(url)
            continue

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        desc  = extract_description(soup, config.get("desc_selectors", []))
        feats = extract_features(soup, config.get("feature_selectors", []))

        if desc:  result["descriptions"].append(desc)
        result["features"].extend(feats)
        result["urls_ok"].append(url)

        if i < len(config["urls"]) - 1:
            time.sleep(2)

    # Дедупликация фич
    seen, dedup = set(), []
    for f in result["features"]:
        k = f.lower()[:45]
        if k not in seen:
            seen.add(k); dedup.append(f)
    result["features"] = dedup[:8]

    status = "✅" if result["urls_ok"] else "❌"
    log.info(f"  {status} {erp_id}: {len(result['descriptions'])} desc, {len(result['features'])} features, {len(result['urls_failed'])} blocked")
    return result


# ── Merge ────────────────────────────────────────────────────────────────────

def merge(scraped: dict, kb: dict) -> dict:
    erp_id = scraped["id"]
    system = next((s for s in kb["erp_systems"] if s["id"] == erp_id), None)
    if not system:
        log.warning(f"  {erp_id} not found in knowledge_base")
        return kb

    if scraped["descriptions"]:
        best = max(scraped["descriptions"], key=len)
        if len(best) > 100:
            system["description_scraped"] = best

    if scraped["features"]:
        system["key_features_scraped"] = scraped["features"]

    if scraped["urls_ok"]:
        system["url_official"] = scraped["urls_ok"][0]

    system["scraped_at"] = scraped["scraped_at"]
    return kb


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="ERP Yoga Bot — product scraper")
    ap.add_argument("--dry-run",      action="store_true", help="Показать без записи в файл")
    ap.add_argument("--via-archive",  action="store_true", help="Использовать web.archive.org")
    ap.add_argument("--id",           type=str,  default=None, help="Парсить только одну систему")
    ap.add_argument("--delay",        type=float, default=3.0,  help="Задержка между вендорами (сек)")
    args = ap.parse_args()

    if not KB_PATH.exists():
        log.error(f"knowledge_base.json not found: {KB_PATH}")
        return

    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)

    log.info(f"Loaded KB: {len(kb['erp_systems'])} systems")
    log.info(f"Mode: dry_run={args.dry_run} | via_archive={args.via_archive} | id={args.id or 'ALL'}")

    targets = {args.id: SOURCES[args.id]} if args.id and args.id in SOURCES else SOURCES

    if args.id and args.id not in SOURCES:
        log.error(f"Unknown id: {args.id}. Valid: {list(SOURCES)}")
        return

    results: dict[str, dict] = {}
    for i, (eid, cfg) in enumerate(targets.items()):
        try:
            scraped = scrape_one(eid, cfg, via_archive=args.via_archive)
            # Сохраняем сырые данные всегда
            raw_path = RAW_DIR / f"{eid}_raw.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(scraped, f, ensure_ascii=False, indent=2)
            results[eid] = scraped
            if not args.dry_run:
                kb = merge(scraped, kb)
        except Exception as e:
            log.error(f"  FAILED {eid}: {e}")
            results[eid] = {"id": eid, "urls_ok": [], "urls_failed": ["exception"], "descriptions": [], "features": []}

        if i < len(targets) - 1:
            time.sleep(args.delay)

    if not args.dry_run:
        backup = KB_PATH.with_suffix(".backup.json")
        import shutil; shutil.copy(KB_PATH, backup)
        kb["meta"]["scraped_at"] = NOW
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        log.info(f"\n✅ Saved. Backup: {backup.name}")
    else:
        log.info("\n[DRY RUN] Nothing written.")

    # Отчёт
    ok      = [k for k, v in results.items() if v["urls_ok"]]
    blocked = [k for k, v in results.items() if not v["urls_ok"]]
    print(f"\n{'─'*55}")
    print(f"  SCRAPING REPORT  {NOW}")
    print(f"{'─'*55}")
    print(f"  Success:  {len(ok)}/{len(targets)}")
    print(f"  Blocked:  {len(blocked)}/{len(targets)}")
    if ok:
        for eid in ok:
            r = results[eid]
            print(f"  ✅  {eid:<22} desc={len(r['descriptions'])}  feat={len(r['features'])}")
    if blocked:
        print()
        for eid in blocked:
            print(f"  ❌  {eid:<22} (403 / timeout)")
    if blocked:
        print(f"\n  Hint: retry with --via-archive to use web.archive.org")
    print(f"  Raw files: {RAW_DIR}/")
    print(f"{'─'*55}")


if __name__ == "__main__":
    main()
