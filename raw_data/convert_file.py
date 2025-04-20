import json
import os

# this py file will convert all raw data files to the same formating

# newsapi is already title, summary keyed dict

# # reddit

# # Load the raw Reddit data
# with open("raw_data/reddit.json", "r", encoding="utf-8") as f:
#     posts = json.load(f)

# # Transform: combine title and body; rename comments to summary
# transformed = []
# for p in posts:
#     title = p.get("title", "").strip()
#     body = p.get("body", "").strip()
#     # If body exists, append it to title
#     full_title = f"{title} {body}".strip() if body else title
#     summary = p.get("comments", [])
#     transformed.append({"title": full_title, "summary": summary})

# # Save the transformed JSON
# with open("reddit_standardized.json", "w", encoding="utf-8") as f:
#     json.dump(transformed, f, ensure_ascii=False, indent=2)

# print(f"Transformed {len(transformed)} posts and saved to data/reddit_standardized.json")

# wiki

# Load the raw Wikipedia data
with open("wiki.json", "r", encoding="utf-8") as f:
    entries = json.load(f)

# Transform: rename 'theory' to 'title'; keep 'summary'
transformed = []
for e in entries:
    title = e.get("theory", "").strip()
    summary = e.get("summary", "").strip()
    transformed.append({"title": title, "summary": summary})

# Save the transformed JSON
with open("wiki_standarized.json", "w", encoding="utf-8") as f:
    json.dump(transformed, f, ensure_ascii=False, indent=2)

print(f"Transformed {len(transformed)} entries and saved to data/wiki_standarized.json")