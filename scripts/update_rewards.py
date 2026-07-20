"""Aggiorna i link Coin Master dagli aggregatori e conserva gli ultimi 3 giorni."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "outputs" / "rewards-data.js"
LOLVVV = "https://www.lolvvv.com/blog/coin-master-free-spins-coins-daily-links"
LEVVVEL = "https://levvvel.com/coin-master/free-spins/"
CANONICAL = "https://static.moonactive.net/static/coinmaster/reward/reward2.html?c={}"


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; GhostMasterItalia/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def campaign(url: str) -> str | None:
    value = parse_qs(urlparse(html.unescape(url)).query).get("c", [None])[0]
    return value if value and re.fullmatch(r"pe_[A-Za-z0-9]+_20\d{6}", value) else None


def campaign_date(code: str) -> str:
    raw = code.rsplit("_", 1)[-1]
    return datetime.strptime(raw, "%Y%m%d").date().isoformat()


def existing_rewards() -> dict[str, dict[str, str]]:
    if not DATA_FILE.exists():
        return {}
    match = re.search(r"window\.REWARDS\s*=\s*(\[.*\])\s*;", DATA_FILE.read_text("utf-8"), re.S)
    if not match:
        return {}
    return {campaign(item["url"]): item for item in json.loads(match.group(1)) if campaign(item["url"])}


def from_lolvvv(page: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    # La data e il link sono contenuti nella stessa riga della tabella.
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", page, re.I | re.S):
        date_match = re.search(r"20\d{2}-\d{2}-\d{2}", row)
        link_match = re.search(r"https://static\.moonactive\.net/[^\"'<>\s]+", row)
        if date_match and link_match:
            code = campaign(link_match.group(0))
            if code:
                found.append((code, date_match.group(0)))
    return found


def from_levvvel(page: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    # LEVVVEL raggruppa i premi di ciascun giorno in una lista. Alcune volte
    # Moon Active riutilizza un vecchio codice in un gruppo nuovo: in quel caso
    # la data scritta nel codice non rappresenta il giorno di pubblicazione.
    # Usiamo quindi la data piu recente della lista per tutti i premi del gruppo.
    lists = re.findall(
        r'<ol\b[^>]*class=["\'][^"\']*coin-master-rewards-list[^"\']*["\'][^>]*>(.*?)</ol>',
        page,
        re.I | re.S,
    )
    for reward_list in lists:
        codes = re.findall(
            r'data-href=["\']/cm/(pe_[A-Za-z0-9]+_20\d{6})["\']', reward_list, re.I
        )
        if not codes:
            continue
        group_date = max(campaign_date(code) for code in codes)
        found.extend((code, group_date) for code in codes)
    return found


def main() -> int:
    saved = existing_rewards()
    discovered: dict[str, str] = {}
    errors: list[str] = []

    for name, url, parser in (("LOLVVV", LOLVVV, from_lolvvv), ("LEVVVEL", LEVVVEL, from_levvvel)):
        try:
            for code, published_date in parser(fetch(url)):
                discovered[code] = max(published_date, discovered.get(code, published_date))
        except Exception as exc:  # Mantiene i dati validi se una fonte non risponde.
            errors.append(f"{name}: {exc}")

    if not discovered:
        print("Nessun link recuperato; il file esistente non viene modificato.", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    newest = max(date.fromisoformat(value) for value in discovered.values())
    cutoff = newest - timedelta(days=2)
    merged: list[dict[str, str]] = []

    for code, published_date in discovered.items():
        if date.fromisoformat(published_date) < cutoff:
            continue
        old = saved.get(code, {})
        merged.append(
            {
                "date": published_date,
                "title": old.get("title", "Premio giornaliero"),
                "url": CANONICAL.format(code),
            }
        )

    merged.sort(key=lambda item: (item["date"], item["url"]), reverse=True)
    counters: dict[str, int] = {}
    for item in merged:
        counters[item["date"]] = counters.get(item["date"], 0) + 1
        if item["title"] == "Premio giornaliero":
            item["title"] = f"Premio giornaliero #{counters[item['date']]}"

    output = "// Questo file viene aggiornato automaticamente da GitHub Actions.\n"
    output += "window.REWARDS = " + json.dumps(merged, ensure_ascii=False, separators=(",", ":")) + ";\n"
    DATA_FILE.write_text(output, encoding="utf-8", newline="\n")
    print(f"Salvati {len(merged)} premi dal {cutoff.isoformat()} al {newest.isoformat()}.")
    for error in errors:
        print(f"Avviso: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
