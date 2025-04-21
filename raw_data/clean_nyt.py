import json
from pathlib import Path

# Load the JSON file
file_path = Path("nyt_conspiracy_20yr.json")
with open(file_path, encoding="utf-8") as f:
    data = json.load(f)

# Remove 'year' and 'url' from each dictionary in the list
for entry in data:
    entry.pop("year", None)
    entry.pop("url", None)

# Save the cleaned data to a new file
cleaned_path = Path("nyt_200.json")
with open(cleaned_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
