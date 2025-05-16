# scraper/static_scraper.py

import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://www.madewithnestle.ca"

# mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def scrape_page(path: str) -> dict:
    url = BASE_URL + path
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()     # will now succeed if the UA header was the issue
    soup = BeautifulSoup(resp.text, "html.parser")

    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return {
        "url": url,
        "title": (soup.title.string.strip() if soup.title else ""),
        "text": "\n\n".join(paragraphs),
    }

def main():
    paths = ["/", "/recipes", "/about", "/products"]
    results = [scrape_page(p) for p in paths]

    out_path = os.path.abspath(os.path.join(__file__, "..", "..", "content.json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote {len(results)} pages to {out_path}")

if __name__ == "__main__":
    main()