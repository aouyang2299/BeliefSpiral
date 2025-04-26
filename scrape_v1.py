import os
import json
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import feedparser
import praw
import nltk
from nltk.tokenize import sent_tokenize
import wikipediaapi

# Ensure NLTK punkt tokenizer is available
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Directory to save data
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

from newspaper import Article
USE_NEWSPAPER = True

# ----------------------------------------------------------------------------
# 1) Wikipedia scraping
# ----------------------------------------------------------------------------

def scrape_wikipedia_api(page: str = "List_of_conspiracy_theories") -> list[dict]:
    """
    Uses MediaWiki API to extract each level-2 section (theory title + first paragraph).
    """
    S = requests.Session()
    API = "https://en.wikipedia.org/w/api.php"

    # Fetch all sections
    sec_params = {"action": "parse", "page": page, "prop": "sections", "format": "json"}
    sec_resp = S.get(API, params=sec_params); sec_resp.raise_for_status()
    sections = sec_resp.json()["parse"]["sections"]

    results = []
    for sec in sections:
        if sec["toclevel"] != 2:
            continue
        title = sec["line"].strip()
        if title.lower() in {"see also","references","notes","further reading","external links","bibliography"}:
            continue
        text_params = {"action": "parse", "page": page, "section": sec["index"], "prop": "text", "format": "json"}
        txt = S.get(API, params=text_params); txt.raise_for_status()
        html = txt.json()["parse"]["text"]["*"]
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")
        summary = p.get_text(" ", strip=True) if p else ""
        results.append({"title": title, "summary": summary})
    return results

WIKI_US_CATEGORY = "Category:Conspiracy_theories_in_the_United_States"
wiki = wikipediaapi.Wikipedia(language='en', user_agent='BeliefSpiral/0.1')


def fetch_wikipedia_snippets():
    items, seen = [], set()
    list_items = scrape_wikipedia_api()
    for e in list_items:
        if e['title'] not in seen and e['summary']:
            seen.add(e['title']); items.append(e)
    cat = wiki.page(WIKI_US_CATEGORY)
    for title, member in cat.categorymembers.items():
        if member.ns == wikipediaapi.Namespace.MAIN and title not in seen:
            page = wiki.page(title)
            if page.exists() and page.summary:
                seen.add(title)
                items.append({"title": page.title, "summary": page.summary.strip()})
    print(f"Fetched {len(items)} Wikipedia snippets.")
    return items

# ----------------------------------------------------------------------------
# 2) News scraping via Google News RSS (historic)
# ----------------------------------------------------------------------------

def fetch_google_news(query: str = "conspiracy", years: int = 20):
    articles = []
    current_year = time.localtime().tm_year
    session = requests.Session()

    for year in range(current_year - years, current_year + 1):
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        rss_url = (
            "https://news.google.com/rss/search?" +
            f"q={query}%20when%3A{start}..{end}&hl=en-US&gl=US&ceid=US:en"
        )
        print(f"Fetching Google News RSS for {start}..{end}")
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.get('title','').strip()
            link = entry.get('link','').strip()
            raw = entry.get('summary','') or entry.get('description','')
            summary = None
            # try newspaper3k
            if USE_NEWSPAPER and link:
                try:
                    art = Article(link)
                    art.download()
                    art.parse()
                    art.nlp()
                    summary = art.summary
                except Exception:
                    summary = None
            # fallback to first 3 sentences
            if not summary:
                text = BeautifulSoup(raw, 'html.parser').get_text()
                sents = sent_tokenize(text)
                summary = ' '.join(sents[:3])
            # filter only conspiracy-related
            combined = (title + " " + summary).lower()
            if "conspir" not in combined:
                continue
            articles.append({"title": title, "summary": summary})
        time.sleep(1)
    print(f"Collected {len(articles)} conspiracy-related news items from Google News RSS.")
    return articles

# ----------------------------------------------------------------------------
# 3) Reddit scraping r/conspiracy
# ----------------------------------------------------------------------------

REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT","BeliefSpiral/0.1")
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_CLIENT_SECRET,
                     user_agent=REDDIT_USER_AGENT)

def is_valid_comment(text):
    low = text.lower()
    return not any(k in low for k in ["i am a bot","contact the moderators","rule ","meta"])


def fetch_reddit_posts(subreddit='conspiracy', limit=500):
    """
    Fetch top `limit` posts from r/conspiracy (all-time) and up to 20 relevant comments each.
    """
    posts, seen = [], set()
    for sub in reddit.subreddit(subreddit).top(time_filter='all', limit=limit):
        full_title = f"{sub.title.strip()} -- {sub.selftext.strip()}"
        if full_title in seen:
            continue
        seen.add(full_title)
        sub.comments.replace_more(limit=0)
        comments = []
        for c in sub.comments.list():
            if c.body and is_valid_comment(c.body):
                comments.append(c.body)
            if len(comments) >= 20:
                break
        posts.append({"title": full_title, "summary": comments})
    print(f"Fetched {len(posts)} Reddit posts.")
    return posts

# ----------------------------------------------------------------------------
# Run pipeline
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    wiki_data   = fetch_wikipedia_snippets()
    news_data   = fetch_google_news(years=20)
    reddit_data = fetch_reddit_posts(limit=100)
    for name, ds in [('wiki2',wiki_data),('news2',news_data),('reddit2',reddit_data)]:
        p = DATA_DIR/f"{name}.json"
        with open(p,'w',encoding='utf-8') as f:
            json.dump(ds,f,ensure_ascii=False,indent=2)
        print(f"Saved {len(ds)} items to {p}")
