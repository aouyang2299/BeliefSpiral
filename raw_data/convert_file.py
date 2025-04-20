import json
import os

# this py file will convert all raw data files to the same formating

# newsapi is already title, summary keyed dict

# # reddit

\

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
