# scraper/dynamic_static_scraper.py

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json, os

BASE_URL = "https://www.madewithnestle.ca"
PATHS = ["/", "/recipes", "/about", "/products"]

def scrape_page(path: str) -> dict:
    url = BASE_URL + path
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            )
        )
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return {
        "url": url,
        "title": (soup.title.string.strip() if soup.title else ""),
        "text": "\n\n".join(paragraphs),
    }

def main():
    results = [scrape_page(p) for p in PATHS]
    out_path = os.path.abspath(
        os.path.join(__file__, "..", "..", "content.json")
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {len(results)} pages to {out_path}")

if __name__ == "__main__":
    main()