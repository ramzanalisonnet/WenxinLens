"""
datasets/collect_museum_data.py
Downloads and processes open-access museum/heritage records that include
Chinese ancient architecture metadata.

Sources (all open-data or CC-licensed):
  1. UNESCO World Heritage List  →  https://whc.unesco.org/en/list/?
  2. China Heritage Quarterly     →  static text snapshots
  3. Wikimedia Commons image URLs for labelled architecture photos

Output layout:
    datasets/raw/museum/
        heritage_sites.json        ← UNESCO site metadata
        architecture_images.csv    ← Wikimedia image URL list (for labelling)
"""

import csv
import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# UNESCO World Heritage open data (SPARQL endpoint, public domain)
# ---------------------------------------------------------------------------
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

CHINESE_HERITAGE_QUERY = """
SELECT DISTINCT ?site ?siteLabel ?coords ?inception ?image ?articleEN ?articleZH WHERE {
  ?site wdt:P31/wdt:P279* wd:Q9259 .           # instance of: World Heritage Site
  ?site wdt:P17 wd:Q29520 .                     # country: China
  OPTIONAL { ?site wdt:P625 ?coords }
  OPTIONAL { ?site wdt:P571 ?inception }
  OPTIONAL { ?site wdt:P18  ?image }
  OPTIONAL {
    ?articleEN schema:about ?site ;
               schema:isPartOf <https://en.wikipedia.org/> ;
               schema:name ?articleEN .
  }
  OPTIONAL {
    ?articleZH schema:about ?site ;
               schema:isPartOf <https://zh.wikipedia.org/> ;
               schema:name ?articleZH .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,zh". }
}
ORDER BY ?siteLabel
LIMIT 100
"""

# Wikimedia Commons architecture category (CC-BY-SA images)
COMMONS_ARCHITECTURE_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?image WHERE {
  ?item wdt:P31/wdt:P279* wd:Q811979 ;           # architectural structure
        wdt:P17 wd:Q29520 ;                       # China
        wdt:P18 ?image .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""


def sparql_query(query: str) -> list[dict]:
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "WenxinLens-DataCollector/1.0 (educational research)",
    }
    resp = requests.get(WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=60)
    resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    return [{k: v["value"] for k, v in row.items()} for row in bindings]


def collect_heritage_sites(out_dir: Path) -> None:
    print("Querying Wikidata for Chinese World Heritage Sites …")
    try:
        rows = sparql_query(CHINESE_HERITAGE_QUERY)
    except Exception as e:
        print(f"  [!] SPARQL query failed: {e}")
        rows = []

    sites = []
    for r in rows:
        site = {
            "id":          r.get("site", "").split("/")[-1],
            "name_en":     r.get("siteLabel", ""),
            "article_en":  r.get("articleEN", ""),
            "article_zh":  r.get("articleZH", ""),
            "coordinates": r.get("coords", ""),
            "inception":   r.get("inception", ""),
            "image_url":   r.get("image", ""),
        }
        sites.append(site)
        print(f"  + {site['name_en']}")

    out_path = out_dir / "heritage_sites.json"
    out_path.write_text(json.dumps(sites, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> saved {len(sites)} sites to {out_path}")


def collect_architecture_images(out_dir: Path) -> None:
    print("Querying Wikimedia Commons for architecture images …")
    time.sleep(1)
    try:
        rows = sparql_query(COMMONS_ARCHITECTURE_QUERY)
    except Exception as e:
        print(f"  [!] Image query failed: {e}")
        rows = []

    csv_path = out_dir / "architecture_images.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["wikidata_id", "name_en", "image_url"])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "wikidata_id": r.get("item", "").split("/")[-1],
                "name_en":     r.get("itemLabel", ""),
                "image_url":   r.get("image", ""),
            })
    print(f"  -> saved {len(rows)} image URLs to {csv_path}")


if __name__ == "__main__":
    out_dir = Path("datasets/raw/museum")
    out_dir.mkdir(parents=True, exist_ok=True)
    collect_heritage_sites(out_dir)
    collect_architecture_images(out_dir)
    print("\nMuseum data collection complete.")
