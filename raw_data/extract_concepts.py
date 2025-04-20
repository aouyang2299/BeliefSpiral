import json
import glob
from pathlib import Path
import spacy

# ─── Load spaCy model ─────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm")

def extract_spacy_concepts(text):
    """
    Run spaCy on the text and return a deduped list of:
      • Named Entities (PERSON, ORG, GPE, etc.)
      • Noun chunks (multi-word noun phrases)
    """
    doc = nlp(text)
    seen = set()
    concepts = []

    # 1) Named entities (highest priority)
    for ent in doc.ents:
        label = ent.text.strip()
        if len(label) > 2 and label not in seen:
            seen.add(label)
            concepts.append(label)

    # 2) Noun chunks (e.g. “neural implants”, “secret AI startup”)
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        # filter out very short/common ones
        if len(phrase) > 2 and phrase.lower() not in {"the", "this", "that"}:
            if phrase not in seen:
                seen.add(phrase)
                concepts.append(phrase)

    return concepts

# ─── Process each JSON in data/ or CWD ────────────────────────────────────────
input_paths = ["newsapi.json"]

for path in input_paths:
    items = json.load(open(path, encoding="utf8"))
    for entry in items:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        # flatten list→str if necessary
        if isinstance(summary, list):
            text = title + " " + " ".join(summary)
        else:
            text = title + " " + str(summary)

        entry["concepts_spacy"] = extract_spacy_concepts(text)

    final_dir = Path("final_data")
    final_dir.mkdir(parents=True, exist_ok=True)

    # 2) Build the output filename inside that directory
    out_path = final_dir / f"{Path(path).stem}_with_spacy_concepts.json"

    # 3) Write your JSON
    with open(out_path, "w", encoding="utf8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote {out_path} ({len(items)} records)")

# python3 extract_concepts.py