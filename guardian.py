from dotenv import load_dotenv
import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

load_dotenv()
GUARDIAN_API_KEY= os.getenv("GUARDIAN_API_KEY")

# def fetch_guardian_articles(q="conspiracy", max_articles=100):
#     """
#     Pull up to max_articles from The Guardian Content API, printing every 10.
#     """
#     url = "https://content.guardianapis.com/search"
#     end = datetime.utcnow().date()
#     start = end - timedelta(days=365*20)
#     articles = []
#     page = 1
#     page_size = 50

#     while len(articles) < max_articles:
#         params = {
#             "api-key":       GUARDIAN_API_KEY,
#             "q":             q,
#             "from-date":     start.isoformat(),
#             "to-date":       end.isoformat(),
#             "page":          page,
#             "page-size":     page_size,
#             "show-fields":   "trailText,bodyText"
#         }
#         print(f"[Guardian] fetching page {page}…")
#         r = requests.get(url, params=params, timeout=10)
#         r.raise_for_status()
#         results = r.json().get("response", {}).get("results", [])
#         if not results:
#             break

#         for item in results:
#             if len(articles) >= max_articles:
#                 break
#             title   = item.get("webTitle","").strip()
#             fields  = item.get("fields",{})
#             summary = fields.get("trailText") or fields.get("bodyText","")
#             articles.append({"title": title, "summary": summary})
#             if len(articles) % 10 == 0:
#                 print(f"[Guardian] collected {len(articles)} articles so far…")
#         page += 1
#         time.sleep(1)

#     print(f"[Guardian] done: fetched {len(articles)} articles.")
#     return articles


# def fetch_guardian_articles(q="conspiracy", max_articles=250):
#     """
#     Fetch up to max_articles from the Guardian Content API, requesting full body blocks
#     and extracting the first 1–2 paragraphs of text. Prints progress every 10 items.
#     """
#     url = "https://content.guardianapis.com/search"
#     end = datetime.utcnow()
#     start = end - timedelta(days=365*20)
#     page = 1
#     page_size = 50
#     articles = []

#     while len(articles) < max_articles:
#         params = {
#             "api-key":       GUARDIAN_API_KEY,
#             "q":             q,
#             "from-date":     start.strftime("%Y-%m-%d"),
#             "to-date":       end.strftime("%Y-%m-%d"),
#             "page":          page,
#             "page-size":     page_size,
#             "show-blocks":   "body",            # <-- ask for full body blocks
#         }
#         print(f"[Guardian] fetching page {page}…")
#         resp = requests.get(url, params=params, timeout=10)
#         resp.raise_for_status()
#         data = resp.json()["response"]

#         # if no results or we've exhausted pages, break early
#         if not data.get("results"):
#             print("[Guardian] no more results.")
#             break

#         for item in data["results"]:
#             if len(articles) >= max_articles:
#                 break

#             title = item["webTitle"]
#             # blocks.body is a list of dicts, each with bodyHtml and bodyTextSummary
#             blocks = item.get("blocks", {}).get("body", [])
#             paras = []

#             for blk in blocks:
#                 # prefer the cleaned‑up summary
#                 txt = blk.get("bodyTextSummary")
#                 if not txt:
#                     # fallback to stripping out HTML
#                     from bs4 import BeautifulSoup
#                     txt = BeautifulSoup(blk.get("body", ""), "html.parser").get_text()
#                 # split into real paragraphs and take the first two
#                 for p in txt.split("\n"):
#                     p = p.strip()
#                     if p:
#                         paras.append(p)
#                     if len(paras) >= 2:
#                         break
#                 if len(paras) >= 2:
#                     break

#             content = "\n\n".join(paras)
#             articles.append({"title": title, "content": content})

#             if len(articles) % 10 == 0:
#                 print(f"[Guardian] collected {len(articles)} articles so far…")

#         page += 1
#         # avoid hammering the API
#         time.sleep(0.5)

#         # stop if we've reached the last page
#         if page > data.get("pages", 0):
#             break

#     print(f"[Guardian] done: fetched {len(articles)} articles.")
#     return articles


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

def fetch_guardian_by_year(year, top_n=10):
    print(f"[Guardian] → fetching {year}…")
    url = "https://content.guardianapis.com/search"
    params = {
        "api-key":     GUARDIAN_API_KEY,
        "q":           "conspiracy",
        "from-date":   f"{year}-01-01",
        "to-date":     f"{year}-12-31",
        "page-size":   top_n * 2,
        "show-blocks": "body"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    items = r.json()["response"]["results"]

    results = []
    for item in items:
        title = item["webTitle"]
        web_url = item["webUrl"]

        # pull first 2 paras from blocks
        blocks = item.get("blocks", {}).get("body", [])
        paras = []
        for blk in blocks:
            txt = blk.get("bodyTextSummary") or BeautifulSoup(blk.get("body",""), "html.parser").get_text()
            for p in txt.split("\n"):
                p = p.strip()
                if len(p) > 50:
                    paras.append(p)
                if len(paras) >= 2:
                    break
            if len(paras) >= 2:
                break
        content = "\n\n".join(paras).strip()

        if not content:
            print(f"[Guardian] → skipping empty-content article: {title}")
            continue

        results.append({
            "title":  title,
            "content": content
        })
        if len(results) >= top_n:
            break

        if len(results) % 5 == 0:
            print(f"[Guardian]   …collected {len(results)}/{top_n} for {year}")
        time.sleep(0.1)

    print(f"[Guardian] ← {len(results)} articles for {year}")
    return results


# if __name__ == "__main__":
#     guardian = fetch_guardian_by_year()

#     # write out
#     for name, data in [("guardian", guardian)]:
#         path = DATA_DIR / f"{name}.json"
#         with open(path, "w", encoding="utf8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         print(f"Wrote {len(data)} items to {path}")

if __name__ == "__main__":
    now = datetime.utcnow().year
    all_guardian = []

    for y in range(now, now - 20, -1):
        all_guardian.extend(fetch_guardian_by_year(y))

    # write out

    with open(DATA_DIR/"guardian_conspiracy_20yr.json", "w", encoding="utf8") as f:
        json.dump(all_guardian, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(all_guardian)} Guardian articles → data/guardian_conspiracy_20yr.json")
