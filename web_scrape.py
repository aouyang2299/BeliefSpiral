#!/usr/bin/env python3
"""
scraper.py

Web scraper for the Belief Spiral – Conspiracy Recommender Engine project.
Collects text snippets from:
  - Reddit (r/conspiracy)
  - Wikipedia (List of conspiracy theories)
  - Gab (public posts)
  - Satirical sites (e.g., The Onion)

Requirements:
  pip install praw requests beautifulsoup4 python-dotenv

Usage:
  1. Create a .env file with:
       REDDIT_CLIENT_ID=your_client_id
       REDDIT_CLIENT_SECRET=your_client_secret
       REDDIT_USER_AGENT=BeliefSpiralScraper/0.1
  2. Run: python scraper.py
  3. Output: conspiracy_snippets.json
"""

import os
import time
import json
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newsapi import NewsApiClient
from newsapi import NewsApiClient

try:
    import praw
except ImportError:
    raise ImportError("Please install praw: pip install praw")

# Load credentials from .env
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "BeliefSpiralScraper/0.1")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Initialize NewsAPI client
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def scrape_reddit(subreddit_name: str, limit: int = 500):
    """
    Scrape titles, bodies, and comments from a subreddit,
    returning a list of dicts with keys: title, body, comments.
    """
    posts = []
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.hot(limit=limit):
        # Pull all the comments (flattened)
        submission.comments.replace_more(limit=0)
        comments = [comment.body for comment in submission.comments.list()]

        posts.append({
            "title": submission.title,
            "body": submission.selftext or "",
            "comments": comments
        })

        time.sleep(0.5)  # rate‑limit

    return posts

def dedupe_dicts(items):
    seen = set()
    unique = []
    for item in items:
        key = json.dumps(item, sort_keys=True)   # canonical string
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

# this one sorta worked, it got all the names and the hyperlinks in references

def scrape_wikipedia(url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"):
    """  
    Scrape Wikipedia’s ‘List of conspiracy theories’ page for theory names.
    Returns a list of strings and prints debug info.
    """
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # catch every <li> under the main content container
    items = soup.select(".mw-parser-output ul li")
    print(f"[DEBUG] Found total <li> tags: {len(items)}")

    snippets = []
    for li in items:
        text = li.get_text(" ", strip=True)
        # keep anything that *looks* like a theory name
        if len(text) >= 20 and not text.lower().startswith(("see also", "retrieved from")):
            snippets.append(text)

    print(f"[DEBUG] Returning {len(snippets)} theory names")
    return snippets

# def scrape_wikipedia(url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"):
#     """  
#     Scrape Wikipedia’s ‘List of conspiracy theories’ page for theory names.
#     Returns a list of strings and prints debug info.
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()

#     soup = BeautifulSoup(resp.text, "html.parser")
#     # catch every <li> under the main content container
#     items = soup.select(".mw-parser-output ul li")
#     print(f"[DEBUG] Found total <li> tags: {len(items)}")

#     snippets = []
#     for li in items:
#         text = li.get_text(" ", strip=True)
#         # keep anything that *looks* like a theory name
#         if len(text) >= 20 and not text.lower().startswith(("see also", "retrieved from")):
#             snippets.append(text)

#     print(f"[DEBUG] Returning {len(snippets)} theory names")
#     return snippets

# def scrape_wikipedia(url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"):
#     """
#     Scrape Wikipedia’s ‘List of conspiracy theories’ and return a list of
#     { theory: <name>, summary: <short text> } dicts.
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")

#     items = soup.select(".mw-parser-output > ul > li")
#     results = []

#     for li in items:
#         # 1) find the first internal link
#         a = li.find("a", href=True)
#         if not a or not a["href"].startswith("/wiki/"):
#             continue

#         # 2) get the theory name
#         theory = a.get_text(strip=True)

#         # 3) get the full text of the li, remove citation markers
#         text = li.get_text(" ", strip=True)
#         text = re.sub(r"\[\d+\]", "", text)           # remove [1], [2], etc.
#         text = re.sub(r"\[note \d+\]", "", text)      # remove [note 1], etc.

#         # 4) strip off the theory name from the front, plus any leading punctuation
#         summary = re.sub(rf"^{re.escape(theory)}\s*[–:—]\s*", "", text).strip()
#         if not summary:
#             continue

#         results.append({
#             "theory": theory,
#             "summary": summary
#         })

#     return results

# def scrape_wikipedia(
#     url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"
# ):
#     """
#     Returns a list of { theory: <name>, summary: <first paragraph> } for each
#     conspiracy theory on the page.
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")

#     results = []
#     # Select all level‑3 headings under the main content
#     for h3 in soup.select("#mw-content-text .mw-parser-output h3"):
#         # Find the headline span (the theory name)
#         span = h3.find("span", class_="mw-headline")
#         if not span:
#             continue
#         title = span.get_text(strip=True)
#         # Skip non‑theory sections
#         if title.lower() in {"see also", "references", "bibliography"}:
#             continue

#         # The summary is typically the next <p> sibling
#         p = h3.find_next_sibling()
#         while p and p.name != "p":
#             p = p.find_next_sibling()
#         if not p:
#             continue

#         summary = p.get_text(" ", strip=True)
#         results.append({"theory": title, "summary": summary})

#     return results

# def scrape_wikipedia_theories(
#     url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"
# ):
#     """
#     Fetches all leaf <li> items in the 'List of conspiracy theories' page
#     up until the 'See also' heading, and returns a deduped list of theory names.
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     content = soup.select_one(".mw-parser-output")

#     theories = []
#     for el in content.descendants:
#         # stop when we reach the "See also" section
#         if getattr(el, "name", None) == "h2":
#             span = el.find("span", class_="mw-headline")
#             if span and span.get("id") == "See_also":
#                 break

#         # only look at <li> tags
#         if getattr(el, "name", None) != "li":
#             continue

#         # skip any <li> that contains a nested <ul> (i.e. region or grouping headers)
#         if el.find("ul"):
#             continue

#         # find the first valid wiki link
#         a = el.find("a", href=True)
#         if not a:
#             continue
#         href = a["href"]
#         # must be a standard wiki article (no colons)
#         if not href.startswith("/wiki/") or ":" in href:
#             continue

#         name = a.get_text(strip=True)
#         theories.append(name)

#     # dedupe while preserving order
#     return list(dict.fromkeys(theories))

# def scrape_wikipedia_theories(
#     url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"
# ):
#     """
#     Crawl the page’s <h3> headings (one per theory) and grab the first
#     descriptive paragraph that follows each heading. Stops at the “See also” section.
#     Returns: List[{"theory": str, "summary": str}]
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")

#     content = soup.select_one(".mw-parser-output")
#     results = []

#     for elem in content.children:
#         # 1) Stop once we hit “See also”
#         if getattr(elem, "name", None) == "h2":
#             span = elem.find("span", class_="mw-headline")
#             if span and span.get_text(strip=True).lower() == "see also":
#                 break

#         # 2) On each <h3>, grab the theory name and its next real paragraph
#         if getattr(elem, "name", None) == "h3":
#             title = elem.get_text(strip=True)

#             # find the next <p>
#             p = elem.find_next_sibling()
#             while p and p.name != "p":
#                 p = p.find_next_sibling()

#             # if that paragraph just says “Main article…”, skip to the following <p>
#             if p and p.get_text().startswith("Main article"):
#                 p = p.find_next_sibling()
#                 while p and p.name != "p":
#                     p = p.find_next_sibling()

#             summary = p.get_text(" ", strip=True) if p else ""
#             results.append({"theory": title, "summary": summary})

#     return results

# def scrape_wikipedia_theories(
#     url: str = "https://en.wikipedia.org/wiki/List_of_conspiracy_theories"
# ):
#     """
#     Returns a list of { theory: <heading>, summary: <first real paragraph> }
#     for each <h3> section on the page, skipping non‑theory sections.
#     """
#     resp = requests.get(url)
#     resp.raise_for_status()

#     soup = BeautifulSoup(resp.text, "html.parser")
#     content = soup.find("div", class_="mw-parser-output")

#     results = []
#     for h3 in content.find_all("h3"):
#         # Extract the heading text inside <span class="mw-headline">
#         span = h3.find("span", class_="mw-headline")
#         if not span:
#             continue
#         title = span.get_text(strip=True)

#         # Stop if we’ve hit the “See also” (or other end) section
#         if title.lower() in {
#             "see also", "references", "notes", "further reading", "external links"
#         }:
#             break

#         # Find the very next <p> sibling
#         p = h3.find_next_sibling()
#         while p and p.name != "p":
#             p = p.find_next_sibling()

#         # Skip the “Main article:” paragraph if it appears first
#         if p and p.get_text().startswith("Main article"):
#             p = p.find_next_sibling()
#             while p and p.name != "p":
#                 p = p.find_next_sibling()

#         if not p:
#             continue

#         summary = p.get_text(" ", strip=True)
#         results.append({"theory": title, "summary": summary})

#     # Dedupe by title (preserve first occurrence)
#     seen = set()
#     unique = []
#     for item in results:
#         if item["theory"] not in seen:
#             seen.add(item["theory"])
#             unique.append(item)

#     return unique

def scrape_wikipedia_api(
    page: str = "List_of_conspiracy_theories"
) -> list[dict]:
    """
    Uses the MediaWiki JSON API to:
      1) List all level‑2 sections (each theory has its own section).
      2) Skip over non‑theory sections (e.g. See also, References).
      3) Fetch each section’s HTML and extract the first <p> as summary.
    Returns a list of {"theory": <section title>, "summary": <text>} dicts.
    """
    S = requests.Session()
    API = "https://en.wikipedia.org/w/api.php"

    # 1) Fetch all sections
    sec_params = {
        "action":   "parse",
        "page":     page,
        "prop":     "sections",
        "format":   "json"
    }
    sec_resp = S.get(API, params=sec_params)
    sec_resp.raise_for_status()
    sections = sec_resp.json()["parse"]["sections"]

    results = []
    for sec in sections:
        # We want only toclevel 2 (each theory is its own h3)
        if sec["toclevel"] != 2:
            continue
        title = sec["line"]
        # Skip end‑of‑content sections
        if title.lower() in {
            "see also", "references", "notes",
            "further reading", "external links", "bibliography"
        }:
            continue

        # 2) Fetch that one section’s HTML
        text_params = {
            "action":   "parse",
            "page":     page,
            "section":  sec["index"],
            "prop":     "text",
            "format":   "json"
        }
        txt_resp = S.get(API, params=text_params)
        txt_resp.raise_for_status()
        html = txt_resp.json()["parse"]["text"]["*"]

        # 3) Parse out the first <p>
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")
        summary = p.get_text(" ", strip=True) if p else ""
        results.append({"theory": title, "summary": summary})

    return results

# def scrape_gab(topic_url: str = "https://gab.com/explore", limit: int = 300):
#     """Scrape public posts from a Gab topic page."""
#     snippets = []
#     headers = {"User-Agent": "Mozilla/5.0"}
#     resp = requests.get(topic_url, headers=headers)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     posts = soup.select("p.post__content")
#     for p in posts[:limit]:
#         txt = p.get_text(" ", strip=True)
#         if txt:
#             snippets.append(txt)
#     return snippets

# Requires: pip install requests_html
from requests_html import HTMLSession

# def scrape_gab(topic_url: str = "https://gab.com/explore", limit: int = 300):
#     """
#     Scrape public posts from Gab by rendering JavaScript.
#     Uses requests_html to load dynamic content.
#     """
#     session = HTMLSession()
#     response = session.get(topic_url)
#     # Render the page to execute JS and populate dynamic content
#     response.html.render(timeout=20, sleep=2)
    
#     # Find post elements and extract text
#     posts = response.html.find("p.post__content")
#     snippets = [post.text for post in posts[:limit]]
    
#     session.close()
#     return snippets

# # Example usage:
# # gab_snips = scrape_gab_render(limit=200)
# # print(f"Fetched {len(gab_snips)} Gab posts.")

def scrape_gab_api(keyword: str = "conspiracy", page_limit: int = 5, per_page: int = 50):
    """
    Fetch public Gab posts containing `keyword` via Gab's JSON search endpoint.
    Returns a flat list of post texts.
    """
    snippets = []
    base_url = "https://gab.com/api/v3/search"
    for page in range(1, page_limit + 1):
        params = {
            "type": "status",
            "onlyVerified": "false",
            "q": keyword,
            "resolve": "true",
            "page": page
        }
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()

        statuses = data.get("statuses", [])
        if not statuses:
            break

        # Extract the rendered HTML content, stripping tags if you like
        for status in statuses:
            html = status.get("content", "")
            # Optionally strip HTML tags:
            text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
            snippets.append(text)

    return snippets

# DOES NOT WORK, ONION HAS NO TAGS ANYMORE
# def scrape_satire(source_url: str = "https://www.theonion.com/tag/conspiracy", limit: int = 100):
#     """Scrape satirical paragraphs to balance tone."""
#     snippets = []
#     resp = requests.get(source_url)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     paras = soup.select("div.js_post-content p")
#     for p in paras[:limit]:
#         text = p.get_text(" ", strip=True)
#         if text:
#             snippets.append(text)
#     return snippets

def fetch_newsapi_articles(keywords, page_size=100, max_pages=3):
    """
    Fetch NewsAPI articles by batching per keyword and paginating results.
    """
    all_articles = []
    for kw in keywords:
        if not kw:  # skip empty keywords
            continue
        for page in range(1, max_pages + 1):
            # Exact‑phrase match, date‑bound, and paged request
            response = newsapi.get_everything(
                q=f'"{kw}"',
                language='en',
                from_param="2025-01-01",
                to="2025-04-19",
                page=page,
                page_size=page_size
            )
            articles = response.get('articles', [])
            if not articles:
                break  # no further pages for this keyword
            all_articles.extend(articles)

    # Deduplicate by URL
    seen, unique = set(), []
    for article in all_articles:
        url = article.get('url')
        if url and url not in seen:
            seen.add(url)
            unique.append(article)

    return unique

def test_newsapi_connection():
    # try a very common conspiracy term
    resp = newsapi.get_everything(
        q="5G",
        language="en",
        page_size=5,
        from_param="2025-01-01",
        to="2025-04-19",
        sort_by="relevancy"
    )
    print("Status:", resp["status"])
    print("Total results:", resp["totalResults"])
    for art in resp["articles"]:
        print("-", art["title"], "\n  ", art["url"])

def main():
    
    # print("Scraping Reddit...")
    # reddit_snips = scrape_reddit("conspiracy", limit=5)

    # unique_posts = dedupe_dicts(reddit_snips)

    # with open("reddit.json", "w", encoding="utf-8") as f:
    #     json.dump(unique_posts, f, ensure_ascii=False, indent=2)

    # print("!! Saved to reddit.json")

    # print("Scraping Wikipedia...")
    wiki_data = scrape_wikipedia_api()
    print(f"Found {len(wiki_data)} theories.")  # should be >0
    with open("wiki.json", "w", encoding="utf-8") as f:
        json.dump(wiki_data, f, ensure_ascii=False, indent=2)
    print("Saved to wiki.json")
    
    # print("Scraping Gab...")
    # # gab_snips = scrape_gab(limit=5)
    # gab_snips = scrape_gab_api(keyword="conspiracy", page_limit=5)
    # with open("gab.json", "w", encoding="utf-8") as f:
    #     json.dump(list(set(gab_snips)), f, ensure_ascii=False, indent=2)
    # print("!! Saved to gab.json")

    # # 2) Fetch articles via NewsAPI
    # print("Querying NewsAPI for matching articles…")
    # articles = fetch_newsapi_articles(wiki_snips, page_size=5)
    # print(f"Retrieved {len(articles)} articles.")

    # with open("newsapi.json", "w", encoding="utf-8") as f:
    #     json.dump(list(set(articles)), f, ensure_ascii=False, indent=2)
    # print("!! Saved to newsapi.json")

    # combined = set(reddit_snips + wiki_snips + gab_snips + articles)
    # print(f"Total unique snippets: {len(combined)}")

    # with open("conspiracy_snippets.json", "w", encoding="utf-8") as f:
    #     json.dump(list(combined), f, ensure_ascii=False, indent=2)
    # print("!! Saved to conspiracy_snippets.json")

if __name__ == "__main__":
    main()

