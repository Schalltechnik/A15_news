"""
A15 News Fetcher – Abteilung 15 Energie, Wohnbau und Technik
Amt der Steiermärkischen Landesregierung
Fetches RSS feeds, summarizes with Gemini, saves to docs/data.json
"""

import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

# ── Configuration ──────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

MAX_ITEMS_FROM_FEED    = 100
MAX_AGE_DAYS           = 7
MAX_ITEMS_PER_CATEGORY = 15
MAX_TITLES_FOR_SUMMARY = 15
GEMINI_PAUSE_SECONDS   = 120
GEMINI_RETRY_ATTEMPTS  = 10
GEMINI_RETRY_WAIT      = 120


def gnews(query: str, lang: str = "de", country: str = "AT") -> str:
    from urllib.parse import quote
    return (
        f"https://news.google.com/rss/search"
        f"?q={quote(query)}&hl={lang}&gl={country}&ceid={country}:{lang}"
    )


CATEGORIES = {
    "energie": {
        "label": "Energie & Energiewende",
        "icon": "⚡",
        "color": "#1a5c38",
        "feeds": [
            gnews("Energie Steiermark"),
            gnews("Energiewende Steiermark"),
            gnews("Erneuerbare Energie Steiermark"),
            gnews("Photovoltaik Steiermark"),
            gnews("Windkraft Steiermark"),
            gnews("Fernwärme Steiermark"),
            gnews("Energieversorgung Steiermark"),
            gnews("Stromversorgung Steiermark"),
            gnews("Energieeffizienz Steiermark"),
            gnews("Abteilung 15 Steiermark Energie"),
        ],
        "summary_prompt": (
            "Du bist Experte für Energiepolitik und Energiewende in der Steiermark. "
            "Fasse die folgenden Nachrichtentitel zu Energie, erneuerbaren Energiequellen, "
            "Energieversorgung und Energieeffizienz in der Steiermark in 3 prägnanten deutschen "
            "Sätzen zusammen. Antworte NUR mit Fließtext, keine Aufzählungen."
        ),
    },
    "wohnbau": {
        "label": "Wohnbau & Wohnförderung",
        "icon": "🏠",
        "color": "#c8102e",
        "feeds": [
            gnews("Wohnbau Steiermark"),
            gnews("Wohnbauförderung Steiermark"),
            gnews("Sozialer Wohnbau Steiermark"),
            gnews("Wohnungsmarkt Steiermark"),
            gnews("Mieten Steiermark"),
            gnews("Wohnförderung Land Steiermark"),
            gnews("Gemeindebau Steiermark"),
            gnews("Sanierung Wohngebäude Steiermark Förderung"),
            gnews("leistbares Wohnen Steiermark"),
            gnews("Wohnkosten Steiermark"),
        ],
        "summary_prompt": (
            "Du bist Experte für Wohnbau und Wohnförderung in der Steiermark. "
            "Fasse die folgenden Nachrichtentitel zu Wohnbau, Wohnbauförderung, "
            "Mietpreisen und sozialem Wohnbau in 3 prägnanten deutschen Sätzen zusammen. "
            "Antworte NUR mit Fließtext, keine Aufzählungen."
        ),
    },
    "technik": {
        "label": "Technik & Normung",
        "icon": "🔧",
        "color": "#003399",
        "feeds": [
            gnews("Bautechnik Steiermark"),
            gnews("Haustechnik Normen Österreich"),
            gnews("OIB Richtlinie Österreich"),
            gnews("Heizung Steiermark Förderung"),
            gnews("Wärmepumpe Steiermark Förderung"),
            gnews("Gebäudetechnik Steiermark"),
            gnews("Raumwärme Österreich Technik"),
            gnews("Heizkesseltausch Österreich Förderung"),
            gnews("Pellets Biomasse Heizung Steiermark"),
            gnews("Abteilung 15 Steiermark Technik"),
        ],
        "summary_prompt": (
            "Du bist Experte für Gebäudetechnik und Normung in der Steiermark und Österreich. "
            "Fasse die folgenden Nachrichtentitel zu Bautechnik, Haustechnik, OIB-Richtlinien "
            "und Heizungssystemen in 3 prägnanten deutschen Sätzen zusammen. "
            "Antworte NUR mit Fließtext, keine Aufzählungen."
        ),
    },
    "klimaschutz": {
        "label": "Klimaschutz & Nachhaltigkeit",
        "icon": "🌿",
        "color": "#1a6b3c",
        "feeds": [
            gnews("Klimaschutz Steiermark"),
            gnews("Klimaneutralität Steiermark"),
            gnews("CO2 Reduktion Steiermark"),
            gnews("Nachhaltigkeit Steiermark Land"),
            gnews("Klimastrategie Steiermark"),
            gnews("Treibhausgase Österreich Steiermark"),
            gnews("Energiearmut Steiermark"),
            gnews("Klimawandel Anpassung Steiermark"),
            gnews("Green Deal Steiermark Österreich"),
            gnews("Dekarbonisierung Steiermark"),
        ],
        "summary_prompt": (
            "Du bist Experte für Klimaschutz und Nachhaltigkeit in der Steiermark. "
            "Fasse die folgenden Nachrichtentitel zu Klimaschutzmaßnahmen, CO2-Reduktion, "
            "Klimastrategie und Nachhaltigkeit in 3 prägnanten deutschen Sätzen zusammen. "
            "Antworte NUR mit Fließtext, keine Aufzählungen."
        ),
    },
    "foerderungen": {
        "label": "Förderungen",
        "icon": "💶",
        "color": "#7b4f12",
        "feeds": [
            gnews("Energieförderung Steiermark Land"),
            gnews("Wohnbauförderung Antrag Steiermark"),
            gnews("Sanierungsförderung Steiermark"),
            gnews("Photovoltaik Förderung Steiermark"),
            gnews("Heizkesseltausch Förderung Österreich"),
            gnews("Klimabonus Österreich"),
            gnews("Raus aus Öl Gas Förderung Österreich"),
            gnews("Förderung Steiermark Energie Wohnen"),
            gnews("Bundesförderung thermische Sanierung"),
            gnews("aws Wohnbau Förderung Steiermark"),
        ],
        "summary_prompt": (
            "Du bist Experte für Förderungen im Bereich Energie und Wohnbau in der Steiermark. "
            "Fasse die folgenden Nachrichtentitel zu Energie- und Wohnbauförderungen, "
            "Sanierungsförderungen und Bundesförderungen in 3 prägnanten deutschen Sätzen zusammen. "
            "Antworte NUR mit Fließtext, keine Aufzählungen."
        ),
    },
}


# ── RSS Fetching ───────────────────────────────────────────────────────────────

def parse_pub_date(raw: str):
    if not raw:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw.rstrip("Z") + "+00:00")
    except Exception:
        return None


def fetch_rss(url: str) -> list[dict]:
    items = []
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"})
        with urlopen(req, timeout=30) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        channel = root.find("channel")
        entries = channel.findall("item") if channel is not None else (
            root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall("entry")
        )
        for item in entries[:MAX_ITEMS_FROM_FEED]:
            title = (item.findtext("title") or
                     item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            title = re.sub(r"<[^>]+>", "", title).strip()
            link_el = item.find("link")
            link = (link_el.get("href") or link_el.text or "").strip() if link_el is not None else ""
            pub = (item.findtext("pubDate") or
                   item.findtext("{http://www.w3.org/2005/Atom}published") or "").strip()
            source_el = item.find("source")
            source = source_el.text.strip() if source_el is not None else ""
            if not source:
                try:
                    from urllib.parse import urlparse
                    source = urlparse(url).netloc.replace("www.", "")
                except Exception:
                    pass
            if title:
                items.append({
                    "title": title, "link": link,
                    "date_raw": pub, "date_parsed": parse_pub_date(pub), "source": source,
                })
    except Exception as e:
        print(f"  Warning: could not fetch {url[:70]}: {e}")
    return items


def filter_by_age(items, max_age_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    result, skipped = [], 0
    for item in items:
        dt = item.get("date_parsed")
        if dt is None or dt >= cutoff:
            result.append(item)
        else:
            skipped += 1
    if skipped:
        print(f"  Filtered out {skipped} items older than {max_age_days} days")
    return result


def deduplicate(items):
    seen, result = set(), []
    for item in items:
        key = re.sub(r"\s+", " ", item["title"].lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def format_date(raw):
    if not raw:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw).strftime("%-d. %b %Y")
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw.rstrip("Z") + "+00:00").strftime("%-d. %b %Y")
    except Exception:
        return raw[:16]


# ── Gemini ─────────────────────────────────────────────────────────────────────

def call_gemini(prompt: str, max_tokens: int = 2000) -> str:
    import json as _json
    body = _json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3},
    }).encode()
    for attempt in range(1, GEMINI_RETRY_ATTEMPTS + 1):
        try:
            req = Request(GEMINI_URL, data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read())
            print(f"  Finish reason: {data['candidates'][0].get('finishReason','unknown')}")
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except HTTPError as e:
            if e.code == 429:
                if attempt < GEMINI_RETRY_ATTEMPTS:
                    print(f"  Gemini 429 (attempt {attempt}/{GEMINI_RETRY_ATTEMPTS}) – waiting {GEMINI_RETRY_WAIT}s…")
                    time.sleep(GEMINI_RETRY_WAIT)
                else:
                    return "Zusammenfassung konnte nicht erstellt werden (Rate Limit)."
            else:
                print(f"  Gemini HTTP error {e.code}")
                return "Zusammenfassung konnte nicht erstellt werden."
        except Exception as e:
            print(f"  Gemini error: {e}")
            return "Zusammenfassung konnte nicht erstellt werden."
    return "Zusammenfassung konnte nicht erstellt werden."


def summarize_with_gemini(titles, prompt):
    if not titles:
        return "Keine aktuellen Meldungen der letzten 7 Tage gefunden."
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    return call_gemini(prompt + "\n\nNachrichtentitel:\n" + numbered, max_tokens=2000)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    output = {
        "generated": datetime.now(timezone.utc).strftime("%d. %B %Y, %H:%M UTC"),
        "categories": {},
    }

    for cat_id, cat in CATEGORIES.items():
        print(f"\n── {cat['label']} ──")
        all_items = []
        for feed_url in cat["feeds"]:
            print(f"  Fetching: {feed_url[:80]}…")
            all_items.extend(fetch_rss(feed_url))

        print(f"  {len(all_items)} total items before filtering")
        all_items = filter_by_age(all_items, MAX_AGE_DAYS)
        items = deduplicate(all_items)[:MAX_ITEMS_PER_CATEGORY]
        print(f"  {len(items)} unique items after filter")

        for item in items:
            item["date"] = format_date(item.pop("date_raw", ""))
            item.pop("date_parsed", None)

        print("  Calling Gemini…")
        summary = summarize_with_gemini(
            [i["title"] for i in items[:MAX_TITLES_FOR_SUMMARY]], cat["summary_prompt"]
        )
        print(f"  Summary: {summary[:80]}…")
        print(f"  Waiting {GEMINI_PAUSE_SECONDS}s…")
        time.sleep(GEMINI_PAUSE_SECONDS)

        output["categories"][cat_id] = {
            "label":   cat["label"],
            "icon":    cat["icon"],
            "color":   cat["color"],
            "summary": summary,
            "items":   items,
        }

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("\n✅ docs/data.json written successfully.")


if __name__ == "__main__":
    main()
