import json
import os

# this py file will convert all raw data files to the same formating

# newsapi is already title, summary keyed dict

# # reddit

import json

# 1) load your scraped data
with open("reddit.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

# 2) transform
standardized = []
for p in posts:
    title = p.get("title", "").strip()
    body  = p.get("body",  "").strip()
    # combine title + body (only add space if body exists)
    full_title = f"{title} {body}".strip() if body else title

    comments = p.get("comments", [])
    standardized.append({
        "title":   full_title,
        "summary": comments
    })

# 3) write it out
with open("reddit_standardized.json", "w", encoding="utf-8") as f:
    json.dump(standardized, f, ensure_ascii=False, indent=2)

print(f"✅ Transformed {len(standardized)} posts → final_data/reddit_standardized.json")


# wiki

# Load the raw Wikipedia data
# with open("wiki.json", "r", encoding="utf-8") as f:
#     entries = json.load(f)

# # Transform: rename 'theory' to 'title'; keep 'summary'
# transformed = []
# for e in entries:
#     title = e.get("theory", "").strip()
#     summary = e.get("summary", "").strip()
#     transformed.append({"title": title, "summary": summary})

# # Save the transformed JSON
# with open("wiki_standarized.json", "w", encoding="utf-8") as f:
#     json.dump(transformed, f, ensure_ascii=False, indent=2)

# print(f"Transformed {len(transformed)} entries and saved to data/wiki_standarized.json")



# import json

# # Attempt to load from project root
# # with open("reddit.json", "r", encoding="utf-8") as f:
# #     articles = json.load(f)

# print("Number of articles in newsapi.json:", len(posts))
