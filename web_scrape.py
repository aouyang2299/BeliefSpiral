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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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
def dedupe_dicts(items):
    seen = set()
    unique = []
    for item in items:
        key = json.dumps(item, sort_keys=True)   # canonical string
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

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

# def scrape_gab_api(keyword: str = "conspiracy", page_limit: int = 5, per_page: int = 50):
#     """
#     Fetch public Gab posts containing `keyword` via Gab's JSON search endpoint.
#     Returns a flat list of post texts.
#     """
#     snippets = []
#     base_url = "https://gab.com/api/v3/search"
#     for page in range(1, page_limit + 1):
#         params = {
#             "type": "status",
#             "onlyVerified": "false",
#             "q": keyword,
#             "resolve": "true",
#             "page": page
#         }
#         resp = requests.get(base_url, params=params)
#         resp.raise_for_status()
#         data = resp.json()

#         statuses = data.get("statuses", [])
#         if not statuses:
#             break

#         # Extract the rendered HTML content, stripping tags if you like
#         for status in statuses:
#             html = status.get("content", "")
#             # Optionally strip HTML tags:
#             text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
#             snippets.append(text)

#     return snippets


import json
from garc.client import Garc

# from garc.garc import Gab

GAB_USER = os.getenv("GAB_USERNAME")
GAB_PASS = os.getenv("GAB_PASSWORD")

# def scrape_gab_conspiracies(username: str,
#                             password: str,
#                             keyword: str = "conspiracy",
#                             number_gabs: int = 200):
#     """
#     Authenticates to Gab, searches for 'keyword', and returns up to
#     `number_gabs` posts containing that term.
#     """
 
#     gab = Garc(user_account=os.getenv("GAB_ACCOUNT"), 
#                        user_password=os.getenv("GAB_PASSWORD"))

#     print("Scraping Gab…")
#     posts = list(gab.search("conspiracy", gabs=200))
#     snippets = [p["body"] for p in posts]  # or p["content"]
#     return snippets


# def scrape_gab_conspiracies(
#     keyword: str = "conspiracy",
#     number_gabs: int = 200
# ):
#     """
#     Logs in (automatically via env vars), searches for `keyword`, and
#     returns up to `number_gabs` post bodies as plain text.
#     """
#     # load GAB_ACCOUNT & GAB_PASSWORD from .env
#     load_dotenv()
#     # Garc will pick up GAB_ACCOUNT / GAB_PASSWORD from the environment
#     gab = Garc()

#     snippets = []
#     print(f"Scraping Gab for '{keyword}'…")
#     for post in gab.search(keyword, gabs=number_gabs):
#         # each `post` is a dict; the cleaned text lives in `body`
#         snippets.append(post.get("body", ""))

#     return snippets

# def scrape_gab_conspiracies(
#     username: str,
#     password: str,
#     keyword: str = "conspiracy",
#     number_gabs: int = 200
# ):
#     """
#     Authenticates to Gab with the given credentials, searches for `keyword`,
#     and returns up to `number_gabs` posts' bodies.
#     """
#     # Pass the creds you received as args here:
#     gab = Garc(user_account=username, user_password=password)

#     snippets = []
#     print(f"Scraping Gab for '{keyword}'…")
#     for post in gab.search(keyword, gabs=number_gabs):
#         snippets.append(post.get("body", ""))

#     return snippets

# def scrape_gab_selenium(limit=100, headless=True):
#     """
#     Uses Selenium to scrape the public Explore page on Gab without logging in.
#     Returns up to `limit` post texts.
#     """
#     # 1) Configure headless Chrome
#     chrome_opts = Options()
#     if headless:
#         chrome_opts.add_argument("--headless")
#     chrome_opts.add_argument("--disable-gpu")
#     chrome_opts.add_argument("--window-size=1920,1080")

#     # 2) Launch the browser
#     driver = webdriver.Chrome(options=chrome_opts)
#     driver.get("https://gab.com/explore")

#     # 3) Scroll to load more posts until we have enough
#     SCROLL_PAUSE = 1.5
#     posts = []
#     while len(posts) < limit:
#         # grab whatever posts are currently loaded
#         elems = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='post']")
#         posts = elems  # override to the latest list
#         if len(posts) >= limit:
#             break

#         # scroll down and wait
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(SCROLL_PAUSE)

#     # 4) Extract text from the first `limit` posts
#     snippets = []
#     for post in posts[:limit]:
#         try:
#             content = post.find_element(By.CSS_SELECTOR, "div[data-testid='post-content']")
#             snippets.append(content.text)
#         except Exception:
#             continue

#     driver.quit()
#     return snippets

# def scrape_gab(keyword="conspiracy", limit=100, headless=True):
    
#     """
#     Drives a headless Chrome to grab up to `limit` Gab posts matching `keyword`.
#     """
#     # 1) Configure Chrome
#     opts = Options()
#     if headless:
#         opts.add_argument("--headless")
#     opts.add_argument("--disable-gpu")
#     opts.add_argument("--window-size=1920,1080")

#     driver = webdriver.Chrome(options=opts)
#     # 2) Go directly to the search results page
#     driver.get(f"https://gab.com/top?q={keyword}")
#     time.sleep(3)  # let initial posts load

#     # 3) Scroll until we have `limit` posts
#     SCROLL_PAUSE = 1.5
#     posts = []
#     search = 0
#     while len(posts) < limit:
#         elems = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='post']")
#         posts = elems
#         if len(posts) >= limit:
#             break
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(SCROLL_PAUSE)
#         search += 1
#         print(len(posts), search)

#     # 4) Extract text
#     snippets = []
#     for post in posts[:limit]:
#         try:
#             content = post.find_element(By.CSS_SELECTOR, "div[data-testid='post-content']")
#             snippets.append(content.text)
#         except:
#             continue

#     driver.quit()
#     return snippets

    # chrome_opts = Options()
    # if headless:
    #     chrome_opts.add_argument("--headless")
    # chrome_opts.add_argument("--disable-gpu")
    # chrome_opts.add_argument("--window-size=1920,1080")

    # driver = webdriver.Chrome(options=chrome_opts)
    # # 1) Load the Gab homepage so the search box is available
    # driver.get("https://gab.com/")
    # time.sleep(2)

    # # 2) Find the search input, type your keyword, and submit
    # search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
    # search_box.send_keys(keyword)
    # search_box.send_keys(Keys.RETURN)
    # time.sleep(3)  # wait for search results to load

    # # 3) Scroll until you’ve loaded at least `limit` posts
    # SCROLL_PAUSE = 1.5
    # posts = []
    # while len(posts) < limit:
    #     elems = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='post']")
    #     posts = elems
    #     if len(posts) >= limit:
    #         break
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(SCROLL_PAUSE)
    #     print(len(posts))

    # # 4) Extract text from the first `limit` results
    # snippets = []
    # for post in posts[:limit]:
    #     try:
    #         content = post.find_element(By.CSS_SELECTOR, "div[data-testid='post-content']")
    #         snippets.append(content.text)
    #     except:
    #         continue

    # driver.quit()
    # return snippets


def login_gab(driver, user, pw):
    driver.get("https://gab.com/login")
    time.sleep(2)
    # these name attrs may change—adjust if needed
    driver.find_element(By.NAME, "user[username]").send_keys(user)
    driver.find_element(By.NAME, "user[password]").send_keys(pw + Keys.RETURN)
    time.sleep(5)  # wait for login to complete

def scrape_gab_hashtag(keyword="conspiracy", limit=50, headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=opts)
    # 1) Log in
    login_gab(driver, os.getenv("GAB_USER"), os.getenv("GAB_PASS"))

    print("logged in")
    # 2) Visit the hashtag page (must be logged in)
    driver.get(f"https://gab.com/top?q={keyword}")
    time.sleep(3)

    # 3) Infinite‑scroll until we load enough <div data-testid="post">
    SCROLL_PAUSE = 1.5
    search = 0
    while True:
        posts = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='post']")
        if len(posts) >= limit:
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        search += 1
        print(search, len(posts))

    # 4) Extract the text content
    snippets = []
    for post in posts[:limit]:
        try:
            snippets.append(
                post.find_element(By.CSS_SELECTOR,
                    "div[data-testid='post-content']").text
            )
        except:
            continue

    driver.quit()
    return list(dict.fromkeys(snippets))  # dedupe

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

# def fetch_conspiracy_articles(
#     keyword: str = "conspiracy",
#     page_size: int = 100,
#     max_pages: int = 3,
#     from_date: str = "2025-01-01",
#     to_date: str = "2025-04-19"
# ):
#     """
#     Fetch NewsAPI articles matching a single keyword ("conspiracy"),
#     paginating up to `max_pages` pages of size `page_size`.
#     """
#     all_articles = []
#     for page in range(1, max_pages + 1):
#         resp = newsapi.get_everything(
#             q=f'"{keyword}"',
#             language="en",
#             from_param=from_date,
#             to=to_date,
#             page=page,
#             page_size=page_size,
#             sort_by="relevancy"
#         )
#         articles = resp.get("articles", [])
#         if not articles:
#             break  # no more results
#         all_articles.extend(articles)

#     # Dedupe by URL
#     seen, unique = set(), []
#     for art in all_articles:
#         url = art.get("url")
#         if url and url not in seen:
#             seen.add(url)
#             unique.append(art)

#     return unique


def fetch_newsapi(
    page_size: int = 100,
    max_pages: int = 3
) -> list[dict]:
    """
    Fetch NewsAPI articles matching "conspiracy", paginating through
    up to `max_pages` pages of size `page_size`, and return a list of
    {"title": ..., "summary": ...} dictionaries.
    """
    seen = set()
    results = []

    for page in range(1, max_pages + 1):
        response = newsapi.get_everything(
            q='"conspiracy"',
            language="en",
            page=page,
            page_size=page_size,
            sort_by="relevancy"
        )
        articles = response.get("articles", [])
        if not articles:
            break

        for art in articles:
            url = art.get("url")
            if url and url not in seen:
                seen.add(url)
                results.append({
                    "title":  art.get("title", "").strip(),
                    "summary": (art.get("description") or "").strip()
                })

    return results

def old(keywords, page_size=100, max_pages=3): # based on wiki keywords
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
    
    print("Scraping Reddit...")
    reddit_snips = scrape_reddit("conspiracy", limit=200)
    unique_posts = dedupe_dicts(reddit_snips)
    with open("reddit.json", "w", encoding="utf-8") as f:
        json.dump(unique_posts, f, ensure_ascii=False, indent=2)
    print("!! Saved to reddit.json")

    # print("Scraping Wikipedia...")
    # wiki_data = scrape_wikipedia_api()
    # print(f"Found {len(wiki_data)} theories.")  # should be >0
    # with open("raw_data/wiki.json", "w", encoding="utf-8") as f:
    #     json.dump(wiki_data, f, ensure_ascii=False, indent=2)
    # print("Saved to wiki.json")


    # gabs = scrape_gab_hashtag("conspiracy", limit=50, headless=True)
    # print(f"Fetched {len(gabs)} posts.")
    # os.makedirs("data", exist_ok=True)
    # with open("raw_data/gab.json", "w", encoding="utf-8") as f:
    #     json.dump(gabs, f, ensure_ascii=False, indent=2)
    # print("Saved to raw_data/gab.json")

    # 2) Fetch articles via NewsAPI
    # print("Querying NewsAPI for matching articles…")
    # articles_list = fetch_newsapi(page_size=200, max_pages=3)
    # `articles_list` is now a list of dicts, e.g.:
    # [
    #   {"title": "Conspiracy Theory A", "summary": "Brief description…"},
    #   {"title": "Conspiracy Theory B", "summary": "Another summary…"},
    #   …
    # ]

    # Example: print the first 3 entries
    # for idx, art in enumerate(articles_list[:3], start=1):
    #     print(f"{idx}. {art['title']}\n   {art['summary']}\n")
    # print(f"Found {len(articles_list)} unique articles about conspiracy.")

    # with open("newsapi.json", "w", encoding="utf-8") as f:
    #     json.dump(articles_list, f, ensure_ascii=False, indent=2)
    # print("!! Saved to newsapi.json")

    # combined = set(reddit_snips + wiki_snips + gab_snips + articles)
    # print(f"Total unique snippets: {len(combined)}")

    # with open("conspiracy_snippets.json", "w", encoding="utf-8") as f:
    #     json.dump(list(combined), f, ensure_ascii=False, indent=2)
    # print("!! Saved to conspiracy_snippets.json")

if __name__ == "__main__":
    main()

