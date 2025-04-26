from dotenv import load_dotenv
import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# Optional: for richer extraction from NYT URLs
# pip install newspaper3k lxml_html_clean
try:
    from newspaper import Article as NYTArticle
    from newspaper.article import ArticleException
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

load_dotenv()
NYT_API_KEY = os.getenv("NYT_API_KEY")
if not NYT_API_KEY:
    raise RuntimeError(
        "❌ NYT_API_KEY is not set! Make sure you’ve created an **Article Search** API key in your NYT developer dashboard "
        "and set it in your environment: export NYT_API_KEY=your_article_search_key"
    )

def extract_first_paragraphs_via_bs4(url, n=2):
    """Fetch URL and return the first n non-empty <p> texts."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paras = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50:
            paras.append(text)
        if len(paras) >= n:
            break
    return "\n\n".join(paras)

def fetch_nyt_by_year(year, top_n=10):
    print(f"[NYT] → fetching {year}…")
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "api-key":    NYT_API_KEY,
        "q":          "conspiracy",
        "begin_date": f"{year}0101",
        "end_date":   f"{year}1231",
        "sort":       "relevance",
        "page":       0
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    docs = resp.json()["response"]["docs"][: top_n * 2]  # overfetch

    results = []
    for doc in docs:
        web_url  = doc["web_url"]
        headline = doc["headline"].get("main", "")

        # 1) Try newspaper3k if available
        content = ""
        if NEWSPAPER_AVAILABLE:
            try:
                art = NYTArticle(web_url)
                art.download()
                art.parse()
                content = "\n\n".join(art.text.split("\n")[:2]).strip()
            except ArticleException as e:
                print(f"[NYT]   newspaper failed ({e}), falling back to BS4")
            except Exception as e:
                print(f"[NYT]   unexpected error ({e}), falling back to BS4")

        # 2) If still empty, fallback to BS4
        if not content:
            try:
                content = extract_first_paragraphs_via_bs4(web_url, n=2).strip()
            except Exception as e:
                print(f"[NYT]   BS4 fallback failed ({e}), skipping")

        # 3) Skip if still no good content
        if not content:
            print(f"[NYT]   → skipping empty-content article: {headline}")
            continue

        results.append({
            "title":   headline,
            "content": content
        })
        if len(results) >= top_n:
            break

        if len(results) % 5 == 0:
            print(f"[NYT]   …collected {len(results)}/{top_n} for {year}")
        time.sleep(10)

    print(f"[NYT] ← {len(results)} articles for {year}")
    return results

if __name__ == "__main__":
    now = datetime.utcnow().year
    all_nyt = []

    for y in range(now, now - 20, -1):
        all_nyt.extend(fetch_nyt_by_year(y))

    # write out
    with open(DATA_DIR/"nyt_conspiracy_20yr.json", "w", encoding="utf8") as f:
        json.dump(all_nyt, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(all_nyt)} NYT articles → data/nyt_conspiracy_20yr.json")
