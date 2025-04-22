# reddit 010  - get rid of cursing
# get rid of links

# can you prevent links from showing up as one of the concepts and filter out any cursing? thanks


import json
import re
import string
from pathlib import Path
import spacy

# ─── Load spaCy model ─────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm")

# filters and scoring
_NUMERIC = re.compile(r'\d')               # any digit
_WH_TAGS = {"WDT", "WP", "WP$", "WRB"}
_URL = re.compile(r'https?://\S+|www\.\S+')  # URLs to filter out
_PROFANITY = re.compile(r'\b(?:fuck|shit|bitch|damn|asshole|cunt)\b', re.IGNORECASE)

def is_valid(st: str) -> bool:
    """Filter out anything with digits, URLs, profanity, too short, pronouns or wh‑words."""
    # drop anything containing a URL
    if _URL.search(st):
        return False
    # drop profanity
    if _PROFANITY.search(st):
        return False
    # drop numeric spans
    if _NUMERIC.search(st):
        return False
    # drop very short or common filler
    if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
        return False
    doc = nlp(st)
    # drop pronouns
    if any(tok.pos_ == "PRON" for tok in doc):
        return False
    # drop wh‑words
    if any(tok.tag_ in _WH_TAGS for tok in doc):
        return False
    return True


def score_span(st: str, context: str) -> int:
    """+2 if any PROPN, +1 if it appears in the combined title+summary."""
    score = 0
    doc = nlp(st)
    if any(tok.pos_ == "PROPN" for tok in doc):
        score += 2
    if st.lower() in context.lower():
        score += 1
    return score


def extract_spacy_concepts(title: str,
                           summary: str,
                           top_n: int = 6) -> list[str]:
    text = f"{title} {summary}"
    doc = nlp(text)
    seen = set()
    candidates: list[tuple[int,int,str]] = []
    order = 0

    def consider(st: str, ord_idx: int):
        st = st.strip()
        if st in seen or not is_valid(st):
            return
        seen.add(st)
        sc = score_span(st, text)
        candidates.append((ord_idx, sc, st))

    # 1) Named entities
    for ent in doc.ents:
        consider(ent.text, order)
        order += 1

    # 2) Noun chunks (skip those starting with punctuation)
    for chunk in doc.noun_chunks:
        txt = chunk.text.strip()
        if txt and txt[0] in string.punctuation:
            continue
        consider(txt, order)
        order += 1

    # 3) Sort by: score desc, then span‑length desc, then original order asc
    candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

    # 4) Build final, skipping substrings of already kept spans
    final: list[str] = []
    for _,_,st in candidates:
        if any(st.lower() in kept.lower() for kept in final):
            continue
        final.append(st)
        if len(final) >= top_n:
            break

    return final


if __name__ == "__main__":
    # Only process first 25 entries
    input_file = "reddit_600.json"
    items = json.load(open(input_file, encoding="utf8"))
    subset = items # items[:25]

    out_dir = Path("final_data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "reddit_600_with_spacy_concepts010__filtered_full.json"

    for entry in subset:
        title   = entry.get("title", "") or ""
        summary = entry.get("summary", "")
        if isinstance(summary, list):
            summary = " ".join(summary)
        entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

    # Write only processed subset
    with open(out_path, "w", encoding="utf8") as f:
        json.dump(subset, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote {out_path} ({len(subset)} records)")









# reddit 09
# use the newsapi json as an example of what we want
# good for reddit_500 with top comments only


# import json
# import re
# import string
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# # filters and scoring
# _NUMERIC = re.compile(r'\d')               # any digit
# _WH_TAGS = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(st: str) -> bool:
#     """Filter out anything with digits, too short, pronouns or wh‑words."""
#     if _NUMERIC.search(st):
#         return False
#     if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
#         return False
#     doc = nlp(st)
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False
#     return True


# def score_span(st: str, context: str) -> int:
#     """+2 if any PROPN, +1 if it appears in the combined title+summary."""
#     score = 0
#     doc = nlp(st)
#     if any(tok.pos_ == "PROPN" for tok in doc):
#         score += 2
#     if st.lower() in context.lower():
#         score += 1
#     return score


# def extract_spacy_concepts(title: str,
#                            summary: str,
#                            top_n: int = 6) -> list[str]:
#     text = f"{title} {summary}"
#     doc = nlp(text)
#     seen = set()
#     candidates: list[tuple[int,int,str]] = []
#     order = 0

#     def consider(st: str, ord_idx: int):
#         st = st.strip()
#         if st in seen or not is_valid(st):
#             return
#         seen.add(st)
#         sc = score_span(st, text)
#         candidates.append((ord_idx, sc, st))

#     # 1) Named entities
#     for ent in doc.ents:
#         consider(ent.text, order)
#         order += 1

#     # 2) Noun chunks (skip those starting with punctuation)
#     for chunk in doc.noun_chunks:
#         txt = chunk.text.strip()
#         if txt and txt[0] in string.punctuation:
#             continue
#         consider(txt, order)
#         order += 1

#     # 3) Sort by: score desc, then span‑length desc, then original order asc
#     candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

#     # 4) Build final, skipping substrings of already kept spans
#     final: list[str] = []
#     for _,_,st in candidates:
#         if any(st.lower() in kept.lower() for kept in final):
#             continue
#         final.append(st)
#         if len(final) >= top_n:
#             break

#     return final


# if __name__ == "__main__":
#     # Only process first 25 entries
#     input_file = "reddit_500.json"
#     items = json.load(open(input_file, encoding="utf8"))
#     subset = items[:25]

#     out_dir = Path("final_data")
#     out_dir.mkdir(exist_ok=True)
#     out_path = out_dir / f"reddit_500_with_spacy_concepts09.json"

#     for entry in subset:
#         title   = entry.get("title", "") or ""
#         summary = entry.get("summary", "")
#         if isinstance(summary, list):
#             summary = " ".join(summary)
#         entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#     # Write only processed subset
#     with open(out_path, "w", encoding="utf8") as f:
#         json.dump(subset, f, ensure_ascii=False, indent=2)
#     print(f"✅ Wrote {out_path} ({len(subset)} records)")


# reddit version (08)

# can u change it to the most commonly appearing concepts and with nouns
# testing on first 25 reddit json entries

# import json
# import re
# import string
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# _NUMERIC = re.compile(r'\d')               # any digit
# _WH_TAGS = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(st: str) -> bool:
#     if _NUMERIC.search(st):
#         return False
#     if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
#         return False
#     doc = nlp(st)
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False
#     return True

# def contains_noun(st: str) -> bool:
#     doc = nlp(st)
#     return any(tok.pos_ in {"NOUN", "PROPN"} for tok in doc)

# def score_span(st: str, context: str) -> int:
#     score = 0
#     doc = nlp(st)
#     if any(tok.pos_ == "PROPN" for tok in doc):
#         score += 2
#     if st.lower() in context.lower():
#         score += 1
#     freq = context.lower().count(st.lower())
#     if freq > 1:
#         score += freq
#     return score

# def extract_spacy_concepts(title: str,
#                            summary: str,
#                            top_n: int = 6) -> list[str]:
#     text = f"{title} {summary}"
#     doc = nlp(text)
#     seen = set()
#     candidates: list[tuple[int,int,str]] = []
#     order = 0

#     def consider(span: str, idx: int):
#         st = span.strip()
#         if st in seen or not is_valid(st) or not contains_noun(st):
#             return
#         seen.add(st)
#         sc = score_span(st, text)
#         candidates.append((idx, sc, st))

#     # Named entities
#     for ent in doc.ents:
#         consider(ent.text, order)
#         order += 1

#     # Noun chunks (skip leading punctuation)
#     for chunk in doc.noun_chunks:
#         txt = chunk.text.strip()
#         if txt and txt[0] in string.punctuation:
#             continue
#         consider(txt, order)
#         order += 1

#     # Sort by score ↓, length ↓, order ↑
#     candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

#     # Take top_n, avoiding substrings
#     final = []
#     for _,_,st in candidates:
#         if any(st.lower() in kept.lower() for kept in final):
#             continue
#         final.append(st)
#         if len(final) >= top_n:
#             break

#     return final

# if __name__ == "__main__":
#     input_paths = ["reddit_standardized.json"]
#     out_dir = Path("final_data")
#     out_dir.mkdir(exist_ok=True)

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         # only process first 25 entries:
#         items = items[:25]

#         for entry in items:
#             title   = entry.get("title", "") or ""
#             summary = entry.get("summary", "")
#             if isinstance(summary, list):
#                 summary = " ".join(summary)

#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts08.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, ensure_ascii=False, indent=2)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")