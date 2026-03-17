"""
datasets/collect_wikipedia.py
Scrapes Chinese ancient architecture articles from Wikipedia (EN + ZH)
and saves them as plain-text files ready for the RAG document processor.

Usage:
    python datasets/collect_wikipedia.py --out-dir datasets/raw/wikipedia
"""

import argparse
import re
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Target articles ── extend this list as needed
# ---------------------------------------------------------------------------
ARTICLES = {
    "en": [
        "Forbidden City",
        "Temple of Heaven",
        "Giant Wild Goose Pagoda",
        "Summer Palace",
        "Zhaozhou Bridge",
        "Hakka architecture",
        "Chinese architecture",
        "Chengde Mountain Resort",
        "Ming tombs",
        "Yellow Crane Tower",
        "Longmen Grottoes",
        "Dunhuang",
        "Pingyao Ancient City",
        "Lijiang Old Town",
    ],
    "zh": [
        "故宫",
        "天坛",
        "大雁塔",
        "颐和园",
        "赵州桥",
        "土楼",
        "中国建筑",
        "避暑山庄",
        "明十三陵",
        "黄鹤楼",
    ],
}

WIKIPEDIA_API = "https://{lang}.wikipedia.org/w/api.php"


def fetch_article(title: str, lang: str = "en") -> str | None:
    """Return plain-text content of a Wikipedia article, or None on failure."""
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "redirects": 1,
    }
    url = WIKIPEDIA_API.format(lang=lang)
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        if "missing" in page:
            print(f"  [!] Not found: {title} ({lang})")
            return None
        return page.get("extract", "")
    except requests.RequestException as e:
        print(f"  [!] Error fetching {title}: {e}")
        return None


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def collect(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0

    for lang, titles in ARTICLES.items():
        lang_dir = out_dir / lang
        lang_dir.mkdir(exist_ok=True)

        for title in titles:
            print(f"Fetching [{lang}] {title} …")
            content = fetch_article(title, lang)
            if content:
                path = lang_dir / f"{sanitize_filename(title)}.txt"
                path.write_text(content, encoding="utf-8")
                total += 1
                print(f"  -> saved {path} ({len(content):,} chars)")
            time.sleep(0.5)          # polite crawl rate

    print(f"\nDone. {total} articles saved to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="datasets/raw/wikipedia")
    args = parser.parse_args()
    collect(Path(args.out_dir))
