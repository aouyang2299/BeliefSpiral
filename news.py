import os
import json
import time
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
import requests

# Ensure NLTK punkt tokenizer is available
nltk.download('punkt', quiet=True)

# Directory to save data
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# 1) News scraping via NewsAPI
# ----------------------------------------------------------------------------
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_URL = "https://newsapi.org/v2/everything"
EARLIEST_ALLOWED = datetime.date(2025, 3, 21)

def fetch_newsapi(query: str = "conspiracy", years: int = 20, per_year: int = 100) -> list[dict]:
    articles = []
    current_year = datetime.date.today().year
    headers = {"Authorization": NEWSAPI_KEY}
    print("Starting NewsAPI fetch (clamped to earliest allowed date {})...".format(EARLIEST_ALLOWED))
    for year in range(current_year - years + 1, current_year + 1):
        year_start = datetime.date(year, 1, 1)
        year_end   = datetime.date(year, 12, 31)
        if year_end < EARLIEST_ALLOWED:
            print(f"Year {year}: skipped (ends before earliest allowed)")
            continue
        from_date = max(year_start, EARLIEST_ALLOWED).isoformat()
        to_date   = year_end.isoformat()
        params = {
            "q": query,
            "language": "en",
            "from": from_date,
            "to": to_date,
            "sortBy": "popularity",
            "pageSize": per_year
        }
        print(f"Year {year}: querying NewsAPI with from={from_date}, to={to_date}")
        resp = requests.get(NEWSAPI_URL, headers=headers, params=params, timeout=10)
        print(f"  HTTP status {resp.status_code}")
        if resp.status_code != 200:
            print(f"  → Error {resp.status_code}: {resp.text}")
            continue
        data = resp.json()
        print(f"  retrieved {len(data.get('articles', []))} articles")
        for art in data.get('articles', [])[:per_year]:
            title = art.get('title', '').strip()
            description = art.get('description') or ''
            content_field = art.get('content') or ''
            # start with description + API content
            combined = description
            if content_field:
                combined += "\n\n" + content_field
            # attempt to fetch full article paragraphs
            url = art.get('url')
            if url:
                try:
                    page_html = requests.get(url, timeout=5).text
                    soup = BeautifulSoup(page_html, 'html.parser')
                    paras = [p.get_text(' ', strip=True) for p in soup.find_all('p')]
                    if len(paras) >= 2:
                        combined = description + "\n\n" + paras[0] + "\n\n" + paras[1]
                except Exception:
                    pass
            summary = combined.strip()
            if title and summary:
                articles.append({"title": title, "summary": summary})
        time.sleep(1)
    print(f"Collected {len(articles)} conspiracy-related news items.")
    return articles

# ----------------------------------------------------------------------------
# Run pipeline
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    news_data   = fetch_newsapi()

    for name, dataset in [('news3', news_data)]:
        path = DATA_DIR / f"{name}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(dataset)} items to {path}")
