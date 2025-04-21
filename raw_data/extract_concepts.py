import json
import glob
from pathlib import Path
import spacy

# version 8
# {
#     "title": "Trump pick to head CDC sparks Maga backlash among conspiracy theorists",
#     "content": "Donald Trump’s appointment of a career health researcher to head the US Centers for Disease Control and Prevention has provoked a serious rightwing backlash for the new administration. Dozens of Maga influencers, along with many rank-and-file Trump supporters, have taken to social media to denounce Susan Monarez to spin false conspiracy theories about her connections to the CIA and the Defense Advanced Research Projects Agency (Darpa). On X, Truth Social, across rightwing “alt-tech” sites and in segments of rightwing media, there was a vociferous response to the announcement this week that Monarez would continue in the position she has been acting in at the CDC, following the withdrawal of Trump’s initial nominee, David Weldon, who unlike Monarez has a history of supporting fringe theories which oppose vaccination. The firestorm among the conspiracy theorists and science deniers of the anti-vaccine set shows the power of that constituency among Trump’s circle as it quickly forced Trump’s Health and Human Services (HHS) secretary, Robert F Kennedy, to defend the hire in a post on X. Kennedy wrote: “X posts that erroneously attribute Biden-era tweets supporting masks, lockdowns, vaccine mandates, etc. to my @CDCgov Director nominee, Susan Monarez, have understandably provoked agita within the MAHA [Make America Healthy Again] movement.” He continued, “I handpicked Susan for this job because she is a longtime champion of MAHA values, and a caring, compassionate and brilliant microbiologist and a tech wizard who will reorient CDC toward public health and gold-standard science.” The opposition to Monarez – an immunologist with decades of government service – has so far been couched entirely in terms of the anti-vaccine beliefs that have consumed a segment of Trump’s base in the years since the Covid-19 pandemic. Kennedy himself is also well known for holding fringe beliefs around vaccines and other health matters and has called his agenda Make America Healthy Again (Maha). On Monday John Sabal, who on social media goes by the Patriot Voice, told his 150,000 X followers that Monarez was “a DARPA stooge” and “quite literally the OPPOSITE of the MAHA agenda”. Sabal – a sometime guest of far-right media personality Alex Jones – folded Monarez’s appointment into a conspiracy narrative which encompassed Elon Musk’s Starlink, mRNA vaccines and the Trump-backed “Project Stargate” AI initiative. He concluded: “We are heading towards AI Governance Technocracy at WARP SPEED.” Like hundreds of other critics on X, Sabal had conflated the Advanced Research Projects Agency for Health (ARPA-H), a HHS agency created in 2022 where Monarez was previously deputy director, with Darpa, an agency of the Department of Defense. On Tuesday, Margo Montez-Lind, who posts on X to over half a million followers as “@ProudArmyBrat”, posted about Monarez: “She worked for Biden & Obama. She supports all of Fauci’s policies, and is a huge proponent of Big Pharma. She pushes the dangerous Mrna covid jab for babies. Loves boosters. Loves masks. This is an absolute nightmare!”\n\nMany other posters interpreted the appointment as a sign of the Trump administration’s hostility to anti-vaxxers, and even as evidence of a broader conspiracy in which Kennedy himself may be a mere pawn. “Trump picked RFK to keep MAHA people quiet,” wrote one. “He had no intention of stopping anything.” The revolt was also visible on Trump’s own Truth Social platform. Users responding to Trump’s announcement of the nomination connected Monarez to the “chemtrails” conspiracy theory and railed against Monarez’s expressions of support for research funded by Bill Gates’s philanthropic foundation. The X posters haranguing Kennedy were amplified across a galaxy of anti-vax outlets, many of them on the newsletter platform Substack. The outrage soon spread to rightwing media. Grant Stinchfield of Real America’s Voice headlined the nomination as a “Maha Betrayal”. Former Infowars broadcaster David Knight said that Monarez was “same as old boss but now with AI genetic injection”. The appointment may indeed reflect Trump’s own historic inconsistencies on vaccines. Over time, Trump has alternated between welcoming the support, donations and votes of anti-vaxxers, and claiming credit for the mRNA vaccines developed in response to the Covid-19 epidemic under the auspices of Operation Warp Speed during his first administration. The Guardian contacted Monarez and the CDC but received no response. Weeks before Monarez’s nomination, the CDC announced plans to study any links between vaccines and autism. The belief that such a link exists is a core commitment for many anti-vaxxers, even though it is founded on discredited pseudoscience and conspiracy theories. Monarez’s nomination comes as Trump and billionaire tech mogul Elon Musk’s assault on federal agencies roils the CDC. The day after Trump’s announcement, five senior officials reportedly left the agency, including the heads of the agency’s Office of Science, the Public Health Infrastructure Center, and the National Center on Birth Defects and Developmental Disabilities. Also out: CDC communications director Kevin Griffis. Kennedy’s attempts to defend Monarez had little impact with outraged Maha figures. Stella Immanuel, a Cameroonian American physician and pastor who came to prominence during the Covid-19 pandemic as an advocate for treating coronavirus with hydroxychloroquine, which has been repeatedly proved to be ineffective, posted in response: “That’s all great Secretary, but it’s time to ban mRNA injections! It’s time to prosecute Anthony Fauci. It’s time to remove vaccine mandates from our schools.”",
#     "concepts_spacy": [
#       "Maga backlash",
#       "CDC",
#       "conspiracy theorists",
#       "pick"
#     ]
#   },

# see how trump is mentioned but not included in the concepts? make sure that there are no repeats in the concepts for each dictionary but allow there to be repeats across dictionaries

# also do not include conspiracy theorists or conspiracy theory as one of the concepts
# 011

import json
import re
import string
from pathlib import Path
import spacy

# ─── Load spaCy model ─────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm")

_NUMERIC      = re.compile(r'\d')  # any digit
_WH_TAGS      = {"WDT", "WP", "WP$", "WRB"}
_PROFANITY    = re.compile(r"\b(fuck|fucking|shit|damn|crap|bitch|bastard|asshole)\b",
                           re.IGNORECASE)
_EXCLUDE_PHRASES = {
    "conspiracy theorist", "conspiracy theorists",
    "conspiracy theory",    "conspiracy theories"
}
URL_PATTERN = re.compile(r'https?://|www\.')

def is_valid(st: str) -> bool:
    """Filter out digits, URLs, profanity, too-short, pronouns or wh‑words."""
    if _NUMERIC.search(st):
        return False
    if URL_PATTERN.search(st):
        return False
    if _PROFANITY.search(st):
        return False
    low = st.lower()
    if len(st) <= 2 or low in {"the", "this", "that"}:
        return False
    doc = nlp(st)
    if any(tok.pos_ == "PRON"    for tok in doc):  # no pronouns
        return False
    if any(tok.tag_ in _WH_TAGS for tok in doc):  # no "which", "who", etc.
        return False
    return True

def score_span(st: str, context: str) -> int:
    """+2 if any PROPN, +1 if the span occurs verbatim in the context."""
    score = 0
    doc = nlp(st)
    if any(tok.pos_ == "PROPN" for tok in doc):
        score += 2
    if st.lower() in context.lower():
        score += 1
    return score

def extract_spacy_concepts(title: str, summary: str, top_n: int = 6) -> list[str]:
    text = f"{title} {summary}"
    doc = nlp(text)
    seen = set()
    candidates = []
    order = 0

    def consider(raw: str, idx: int):
        # strip, normalize trailing ’s or 's, skip excluded
        st = re.sub(r"(?:’s|'s)$", "", raw.strip())
        if not st or st.lower() in _EXCLUDE_PHRASES:
            return
        if st in seen or not is_valid(st):
            return
        seen.add(st)
        sc = score_span(st, text)
        candidates.append((idx, sc, st))

    # 1) Named entities
    for ent in doc.ents:
        consider(ent.text, order)
        order += 1

    # 2) Noun chunks
    for chunk in doc.noun_chunks:
        txt = chunk.text.strip()
        if txt and txt[0] not in string.punctuation:
            consider(txt, order)
            order += 1

    # 3) Sort: by score desc, then length desc, then original order asc
    candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

    # 4) Build final list, skipping substrings of items we’ve already kept
    final = []
    for _, _, st in candidates:
        if any(st.lower() in kept.lower() for kept in final):
            continue
        final.append(st)
        if len(final) >= top_n:
            break

    return final

if __name__ == "__main__":
    # manually list whichever JSON files you need
    input_paths = [
        "nyt_200.json",
        # add more here...
    ]
    out_dir = Path("final_data")
    out_dir.mkdir(exist_ok=True)

    for path in input_paths:
        items = json.load(open(path, encoding="utf8"))
        for entry in items:  
            title   = entry.get("title", "") or ""
            # pull from "summary" or else from "content"
            summary = entry.get("summary")
            if summary is None:
                summary = entry.get("content", "")
            if isinstance(summary, list):
                summary = " ".join(summary)

            entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

        out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts011_full.json"
        with open(out_path, "w", encoding="utf8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote {out_path} ({len(items)} records)")

# **What this fixes**  
# - Now `summary` defaults to your `"content"` field if `"summary"` is missing.  
# - Possessives like `Trump’s` or `Biden’s` normalize to `Trump`/`Biden`, so “Trump” will show up.  
# - We explicitly slice to the first 25 items for Reddit.  
# - Links, profanity, “conspiracy theory(ies)”, and pronouns/WH‑words are filtered out.  

# Give it a run and you should see “Trump” in your concepts for that CDC‐pick article, plus no internal duplicates.


# not working 011
# import json
# import re
# import string
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# _NUMERIC = re.compile(r'\d')               # any digit
# _WH_TAGS = {"WDT", "WP", "WP$", "WRB"}
# _PROFANITY = re.compile(r"\b(fuck|fucking|shit|damn|crap|bitch|bastard|asshole)\b", re.IGNORECASE)

# # phrases to exclude
# _EXCLUDE_PHRASES = {
#     "conspiracy theorist", "conspiracy theorists",
#     "conspiracy theory", "conspiracy theories"
# }

# URL_PATTERN = re.compile(r'https?://|www\.')

# def is_valid(st: str) -> bool:
#     """Filter out digits, URLs, profanity, too short, pronouns or wh‑words."""
#     if _NUMERIC.search(st):
#         return False
#     if URL_PATTERN.search(st):
#         return False
#     if _PROFANITY.search(st):
#         return False
#     if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
#         return False
#     doc = nlp(st)
#     # drop if any token is a pronoun
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     # drop if any token is a wh‑word
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False
#     return True


# def score_span(st: str, context: str) -> int:
#     """+2 if any PROPN, +1 if in the combined title+summary."""
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

#     def consider(span_text: str, ord_idx: int):
#         st = span_text.strip()
#         # normalize possessives
#         st = re.sub(r"(?:’s|'s)$", "", st)
#         # skip excluded phrases
#         if st.lower() in _EXCLUDE_PHRASES:
#             return
#         # skip URLs
#         if URL_PATTERN.search(st):
#             return
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
#         if not txt or txt[0] in string.punctuation:
#             continue
#         consider(txt, order)
#         order += 1

#     # 3) Sort by: score desc, length desc, order asc
#     candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

#     # 4) Build final, skipping substrings
#     final: list[str] = []
#     for _,_,st in candidates:
#         if any(st.lower() in kept.lower() for kept in final):
#             continue
#         final.append(st)
#         if len(final) >= top_n:
#             break

#     return final


# if __name__ == "__main__":
#     input_paths = ["guardian_200.json"]  # adjust as needed
#     out_dir = Path("final_data")
#     out_dir.mkdir(exist_ok=True)

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:  
#             title   = entry.get("title", "") or ""
#             summary = entry.get("summary", "")
#             if isinstance(summary, list):
#                 summary = " ".join(summary)

#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts011.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, ensure_ascii=False, indent=2)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")


# version 7 - get rid of numbers, fix apostrophe case, avoid repeats (use the longest phrase if see repeat)
# last version using newsapi only

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

#     # 3) Sort by: score desc, then span‐length desc, then original order asc
#     candidates.sort(key=lambda x: (-x[1], -len(x[2]), x[0]))

#     # 4) Build final, skipping anything that’s a substring of an already kept span
#     final: list[str] = []
#     for _,_,st in candidates:
#         if any(st.lower() in kept.lower() for kept in final):
#             continue
#         final.append(st)
#         if len(final) >= top_n:
#             break

#     return final

# if __name__ == "__main__":
#     input_paths = ["guardian_200.json"]  # adjust as needed
#     out_dir = Path("final_data")
#     out_dir.mkdir(exist_ok=True)

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:
#             title   = entry.get("title", "") or ""
#             summary = entry.get("summary", "")
#             if isinstance(summary, list):
#                 summary = " ".join(summary)

#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts07.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, ensure_ascii=False, indent=2)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")

# idk what this is 
# import json
# import re
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# _NUMERIC_ONLY = re.compile(r'^[\d\W]+$')
# _WH_TAGS      = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(span_text: str) -> bool:
#     st = span_text.strip()
#     # drop pure numbers / punctuation or any digit
#     if _NUMERIC_ONLY.match(st) or re.search(r'\d', st):
#         return False
#     # too short or trivial
#     if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
#         return False
#     doc = nlp(st)
#     # no pronouns or wh‑words
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False
#     return True

# def score_span(span_text: str, context: str) -> int:
#     score = 0
#     doc = nlp(span_text)
#     # proper‑noun bonus
#     if any(tok.pos_ == "PROPN" for tok in doc):
#         score += 2
#     # presence bonus
#     if span_text.lower() in context.lower():
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

#     def consider(span_text: str, ord_idx: int):
#         st = span_text.strip()
#         if st in seen or not is_valid(st):
#             return
#         seen.add(st)
#         sc = score_span(st, text)
#         candidates.append((ord_idx, sc, st))

#     # 1) Named entities
#     for ent in doc.ents:
#         consider(ent.text, order)
#         order += 1

#     # 2) Noun chunks
#     for chunk in doc.noun_chunks:
#         consider(chunk.text, order)
#         order += 1

#     # 3) Sort by score desc, then by original order asc
#     candidates.sort(key=lambda x: (-x[1], x[0]))

#     # 4) Build final list, dropping any that are substrings of a longer already‑chosen phrase
#     final: list[str] = []
#     for _,_,st in candidates:
#         # skip if it’s contained in one we’ve already kept
#         if any(st.lower() in kept.lower() for kept in final):
#             continue
#         final.append(st)
#         if len(final) >= top_n:
#             break

#     return final

# if __name__ == "__main__":
#     input_paths = ["newsapi.json"]
#     out_dir = Path("final_data")
#     out_dir.mkdir(exist_ok=True)

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:
#             title = entry.get("title","") or ""
#             summary = entry.get("summary","") or ""
#             if isinstance(summary, list):
#                 summary = " ".join(summary)

#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts07.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, ensure_ascii=False, indent=2)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")


# VERSION 6 - actually keep punctuation

# import json
# import re
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# # ─── Filters ──────────────────────────────────────────────────────────────────
# _NUMERIC_ONLY = re.compile(r'^[\d\W]+$')
# _WH_TAGS      = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(span_text: str) -> bool:
#     st = span_text.strip()
#     # drop pure numbers / punctuation
#     if _NUMERIC_ONLY.match(st):
#         return False
#     # too short or trivial
#     if len(st) <= 2 or st.lower() in {"the", "this", "that"}:
#         return False
#     # no pronouns or wh‑words
#     doc = nlp(st)
#     if any(tok.pos_ == "PRON" for tok in doc): return False
#     if any(tok.tag_ in _WH_TAGS for tok in doc): return False
#     return True

# def score_span(span_text: str, context: str) -> int:
#     """+2 if any PROPN, +1 if appears in the title+summary."""
#     score = 0
#     doc = nlp(span_text)
#     if any(tok.pos_ == "PROPN" for tok in doc):
#         score += 2
#     if span_text.lower() in context.lower():
#         score += 1
#     return score

# def extract_spacy_concepts(title: str,
#                            summary: str,
#                            top_n: int = 6) -> list[str]:
#     """
#     1) regex for hyphen‑words
#     2) spaCy ents + noun‑chunks
#     3) filter + score + de‑dup + hyphen‑subpart drop
#     4) return top_n
#     """
#     text = f"{title} {summary}"
#     seen = set()
#     candidates: list[tuple[int,int,str]] = []
#     order = 0

#     def consider(span_text: str, ord_idx: int):
#         st = span_text.strip()
#         if st in seen or not is_valid(st):
#             return
#         seen.add(st)
#         sc = score_span(st, text)
#         candidates.append((ord_idx, sc, st))

#     # ─── 0) Hyphenated terms ────────────────────────────────────────────────
#     for m in re.findall(r"\b[^\s-]+(?:-[^\s-]+)+\b", text):
#         consider(m, order)
#         order += 1

#     # ─── 1) Named entities ─────────────────────────────────────────────────
#     doc = nlp(text)
#     for ent in doc.ents:
#         consider(ent.text, order)
#         order += 1

#     # ─── 2) Noun chunks ────────────────────────────────────────────────────
#     for chunk in doc.noun_chunks:
#         consider(chunk.text, order)
#         order += 1

#     # ─── 3) Drop standalone parts of any hyphenated candidate ─────────────
#     hyphens = [st for (_,_,st) in candidates if "-" in st]
#     parts_to_drop = set()
#     for h in hyphens:
#         for part in h.split("-"):
#             parts_to_drop.add(part)
#     candidates = [
#         (ord_idx, sc, st)
#         for (ord_idx, sc, st) in candidates
#         if ("-" in st) or (st not in parts_to_drop)
#     ]

#     # ─── 4) Sort & take top_n ─────────────────────────────────────────────
#     candidates.sort(key=lambda x: (-x[1], x[0]))
#     return [st for (_,_,st) in candidates[:top_n]]

# # ─── Main ───────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     input_paths = [
#         "newsapi.json",
#         # add more if needed
#     ]
#     out_dir = Path("final_data")
#     out_dir.mkdir(parents=True, exist_ok=True)

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:
#             title   = entry.get("title","") or ""
#             summary = entry.get("summary","") or ""
#             if isinstance(summary, list):
#                 summary = " ".join(summary)
#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts06.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, indent=2, ensure_ascii=False)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")


# VERSION 5 - give the top 6 concepts and prioritize proper nouns and key words that are in the title and summary

# import json
# import re
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# _NUMERIC_ONLY = re.compile(r'^[\d\W]+$')
# _WH_TAGS      = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(span_text: str) -> bool:
#     """Filter out numeric‐only, too short, pronouns or wh‑words."""
#     if _NUMERIC_ONLY.match(span_text):
#         return False
#     if len(span_text) <= 2 or span_text.lower() in {"the", "this", "that"}:
#         return False

#     doc = nlp(span_text)
#     # drop if any token is a pronoun
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     # drop if any token is a wh‑word
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False

#     return True

# def score_span(span_text: str, context: str) -> int:
#     """Higher if contains PROPN, also if appears in context (title+summary)."""
#     score = 0
#     doc = nlp(span_text)
#     # proper‑noun bonus
#     if any(tok.pos_ == "PROPN" for tok in doc):
#         score += 2
#     # presence bonus
#     if span_text.lower() in context.lower():
#         score += 1
#     return score

# def extract_spacy_concepts(title: str, summary: str, top_n: int = 6) -> list[str]:
#     """
#     Extract entities + noun‑chunks, filter, score & return top_n concepts.
#     """
#     text = f"{title} {summary}"
#     doc = nlp(text)
#     seen = set()
#     candidates = []

#     # Helper to add a span once
#     def consider(span_text: str, order: int):
#         st = span_text.strip()
#         if st in seen or not is_valid(st):
#             return
#         seen.add(st)
#         sc = score_span(st, text)
#         candidates.append((order, sc, st))

#     order = 0
#     # 1) Named entities
#     for ent in doc.ents:
#         consider(ent.text, order)
#         order += 1
#     # 2) Noun chunks
#     for chunk in doc.noun_chunks:
#         consider(chunk.text, order)
#         order += 1

#     # sort by score desc, then by original order asc
#     candidates.sort(key=lambda x: (-x[1], x[0]))

#     # return only the text of top_n
#     return [c[2] for c in candidates[:top_n]]

# if __name__ == "__main__":
#     input_paths = [
#       "newsapi.json"
#     ]  # adjust to your real paths

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:
#             title   = entry.get("title", "")
#             summary = entry.get("summary", "")
#             # flatten if summary is list
#             if isinstance(summary, list):
#                 summary = " ".join(summary)
#             # overwrite concepts_spacy with top‑6
#             entry["concepts_spacy"] = extract_spacy_concepts(title, summary, top_n=6)

#         out_dir = Path("final_data")
#         out_dir.mkdir(exist_ok=True)
#         out_path = out_dir / f"{Path(path).stem}_with_spacy_concepts05.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, ensure_ascii=False, indent=2)
#         print(f"✅ Wrote {out_path} ({len(items)} records)")


# VERSION 4 - get rid of part of speech like pronouns and what

# import json
# import re
# from pathlib import Path
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# # regex to detect “only digits/punct”
# _NUMERIC_ONLY = re.compile(r'^[\d\W]+$')

# # POS tags for wh‑words (what, who, when, etc.)
# _WH_TAGS = {"WDT", "WP", "WP$", "WRB"}

# def is_valid(span_text: str) -> bool:
#     # drop pure numbers/punct
#     if _NUMERIC_ONLY.match(span_text):
#         return False

#     # drop too short or generic
#     if len(span_text) <= 2 or span_text.lower() in {"the", "this", "that"}:
#         return False

#     doc = nlp(span_text)
#     # drop if any token is a pronoun
#     if any(tok.pos_ == "PRON" for tok in doc):
#         return False
#     # drop if any token is a wh‑word
#     if any(tok.tag_ in _WH_TAGS for tok in doc):
#         return False

#     return True

# def extract_spacy_concepts(text: str) -> list[str]:
#     """
#     Returns a deduped list of:
#       • Named Entities (PERSON, ORG, GPE, etc.)
#       • Noun chunks (multi-word noun phrases)
#     Filtering out pure numbers/punct, pronouns, wh‑words, and very short/common fillers.
#     """
#     doc = nlp(text)
#     seen = set()
#     concepts = []

#     # 1) Named entities (highest priority)
#     for ent in doc.ents:
#         label = ent.text.strip()
#         if is_valid(label) and label not in seen:
#             seen.add(label)
#             concepts.append(label)

#     # 2) Noun chunks
#     for chunk in doc.noun_chunks:
#         phrase = chunk.text.strip()
#         if is_valid(phrase) and phrase not in seen:
#             seen.add(phrase)
#             concepts.append(phrase)

#     return concepts

# if __name__ == "__main__":
#     input_paths = ["newsapi.json"]  # adjust as needed

#     for path in input_paths:
#         items = json.load(open(path, encoding="utf8"))
#         for entry in items:
#             title = entry.get("title", "")
#             summary = entry.get("summary", "") or ""
#             # flatten list→str if necessary
#             if isinstance(summary, list):
#                 text = f"{title} " + " ".join(summary)
#             else:
#                 text = f"{title} {summary}"

#             entry["concepts_spacy"] = extract_spacy_concepts(text)

#         final_dir = Path("final_data")
#         final_dir.mkdir(parents=True, exist_ok=True)

#         out_path = final_dir / f"{Path(path).stem}_with_spacy_concepts04.json"
#         with open(out_path, "w", encoding="utf8") as f:
#             json.dump(items, f, indent=2, ensure_ascii=False)

#         print(f"✅ Wrote {out_path} ({len(items)} records)")



# VERSION 3  - get rid of standalone dates

# import json
# import glob
# from pathlib import Path
# import re
# import spacy

# # ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")
# # regex to detect strings made up solely of digits or punctuation
# num_re = re.compile(r"^[\d\W]+$")

# def extract_spacy_concepts(text):
#     """
#     Run spaCy on the text and return a deduped list of:
#       • Named Entities (PERSON, ORG, GPE, etc.)
#       • Noun chunks (multi-word noun phrases)
#     Filters out any concept that is purely numeric/punctuation.
#     """
#     doc = nlp(text)
#     seen = set()
#     concepts = []

#     # 1) Named entities (highest priority)
#     for ent in doc.ents:
#         label = ent.text.strip()
#         # skip very short, numeric-only, or already seen
#         if len(label) > 2 and not num_re.match(label) and label not in seen:
#             seen.add(label)
#             concepts.append(label)

#     # 2) Noun chunks (multi-word noun phrases)
#     for chunk in doc.noun_chunks:
#         phrase = chunk.text.strip()
#         # require length>2, contain at least one alpha char, and not numeric-only
#         if (len(phrase) > 2 and not num_re.match(phrase)
#             and any(tok.is_alpha for tok in chunk)
#             and phrase.lower() not in {"the", "this", "that"}
#             and phrase not in seen):
#             seen.add(phrase)
#             concepts.append(phrase)

#     return concepts

# # ─── Process each JSON in raw_data/ ──────────────────────────────────────────
# input_paths = glob.glob("newsapi.json")
# # glob.glob(str(Path("raw_data") / "*_standardized.json"))

# for path in input_paths:
#     items = json.load(open(path, encoding="utf8"))
#     for entry in items:
#         title = entry.get("title", "")
#         summary = entry.get("summary", "")
#         # flatten list→str if necessary
#         if isinstance(summary, list):
#             text = title + " " + " ".join(summary)
#         else:
#             text = title + " " + str(summary)

#         entry["concepts_spacy"] = extract_spacy_concepts(text)

#     final_dir = Path("final_data")
#     final_dir.mkdir(parents=True, exist_ok=True)

#     out_path = final_dir / f"{Path(path).stem}_with_spacy_concepts03.json"
#     with open(out_path, "w", encoding="utf8") as f:
#         json.dump(items, f, indent=2, ensure_ascii=False)

#     print(f"✅ Wrote {out_path} ({len(items)} records)")


# VERSION 2 
# updated the script to

    # Filter named entities to only common “meaty” types (people, orgs, places, events, products, works of art, laws, etc.)

    # Deduplicate entries via a seen set

    # Restrict noun‑chunks to multi‑word phrases that include at least one non‑stopword token

    # Glob over all JSONs in raw_data/ and write enhanced files to final_data/

# ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# # Allowed entity labels to keep
# ALLOW_ENT = {"PERSON", "ORG", "GPE", "NORP", "EVENT", "PRODUCT", "WORK_OF_ART", "LAW"}

# def extract_spacy_concepts(text: str) -> list[str]:
#     """
#     Run spaCy on the text and return a deduped list of:
#       • Named Entities (filtered by type)
#       • Noun chunks (multi-word noun phrases)
#     """
#     doc = nlp(text)
#     seen = set()
#     concepts = []

#     # 1) Named entities
#     for ent in doc.ents:
#         label = ent.text.strip()
#         if ent.label_ in ALLOW_ENT and len(label) > 2 and label not in seen:
#             seen.add(label)
#             concepts.append(label)

#     # 2) Noun chunks (filter out very short or stopword-only chunks)
#     for chunk in doc.noun_chunks:
#         phrase = chunk.text.strip()
#         tokens = [tok for tok in chunk if not tok.is_stop and not tok.is_punct]
#         # keep if multi-word and has at least one non-stopword token
#         if len(phrase.split()) > 1 and tokens:
#             if phrase not in seen:
#                 seen.add(phrase)
#                 concepts.append(phrase)

#     return concepts

# # ─── Process each JSON in a folder and output under final_data/ ─────────────────
# input_paths = glob.glob("newsapi.json")  # or specify files explicitly

# final_dir = Path("final_data")
# final_dir.mkdir(parents=True, exist_ok=True)

# for path in input_paths:
#     items = json.load(open(path, encoding="utf8"))
#     for entry in items:
#         title = entry.get("title", "")
#         summary = entry.get("summary", "")
#         # flatten list → str if necessary
#         if isinstance(summary, list):
#             text = title + " " + " ".join(summary)
#         else:
#             text = title + " " + str(summary)

#         entry["concepts_spacy"] = extract_spacy_concepts(text)

#     # Build the output filename inside final_data
#     out_path = final_dir / f"{Path(path).stem}_with_spacy_concepts02.json"

#     # Write the transformed JSON
#     with open(out_path, "w", encoding="utf8") as f:
#         json.dump(items, f, indent=2, ensure_ascii=False)

#     print(f"✅ Wrote {out_path} ({len(items)} records)")


# VERSION 1
# ─── Load spaCy model ─────────────────────────────────────────────────────────
# nlp = spacy.load("en_core_web_sm")

# def extract_spacy_concepts(text):
#     """
#     Run spaCy on the text and return a deduped list of:
#       • Named Entities (PERSON, ORG, GPE, etc.)
#       • Noun chunks (multi-word noun phrases)
#     """
#     doc = nlp(text)
#     seen = set()
#     concepts = []

#     # 1) Named entities (highest priority)
#     for ent in doc.ents:
#         label = ent.text.strip()
#         if len(label) > 2 and label not in seen:
#             seen.add(label)
#             concepts.append(label)

#     # 2) Noun chunks (e.g. “neural implants”, “secret AI startup”)
#     for chunk in doc.noun_chunks:
#         phrase = chunk.text.strip()
#         # filter out very short/common ones
#         if len(phrase) > 2 and phrase.lower() not in {"the", "this", "that"}:
#             if phrase not in seen:
#                 seen.add(phrase)
#                 concepts.append(phrase)

#     return concepts

# # ─── Process each JSON in data/ or CWD ────────────────────────────────────────
# input_paths = ["reddit_standardized.json"]

# for path in input_paths:
#     items = json.load(open(path, encoding="utf8"))
#     for entry in items:
#         title = entry.get("title", "")
#         summary = entry.get("summary", "")
#         # flatten list→str if necessary
#         if isinstance(summary, list):
#             text = title + " " + " ".join(summary)
#         else:
#             text = title + " " + str(summary)

#         entry["concepts_spacy"] = extract_spacy_concepts(text)

#     final_dir = Path("final_data")
#     final_dir.mkdir(parents=True, exist_ok=True)

#     # 2) Build the output filename inside that directory
#     out_path = final_dir / f"{Path(path).stem}_with_spacy_concepts.json"

#     # 3) Write your JSON
#     with open(out_path, "w", encoding="utf8") as f:
#         json.dump(items, f, indent=2, ensure_ascii=False)

#     print(f"✅ Wrote {out_path} ({len(items)} records)")

# # python3 extract_concepts.py