import json
import pathlib
from typing import Dict, Iterable, Generator

import spacy
from spacy.tokens import Doc

# --- CONFIG -----------------------------------------------------------------
DATA_DIR = pathlib.Path("../raw_data")  # adjust if your data lives elsewhere
INPUT_FILES = [
    DATA_DIR / "reddit.json",
    DATA_DIR / "wiki.json",
    # DATA_DIR / "conspiracy_snippets.json",
]

# Output is emitted as a JSON Lines file: one parsed sentence per line
OUT_PATH = DATA_DIR / "parsed_sentences.jsonl"

# Which spaCy model?  en_core_web_sm ships with POS + dep; swap for _md/_lg if available
SPACY_MODEL = "en_core_web_sm"

# ---------------------------------------------------------------------------

def iter_documents() -> Generator[Dict[str, str], None, None]:
    """Yield unified {text, source} dicts from the heterogeneous input files."""
    for fp in INPUT_FILES:
        if not fp.exists():
            print(f"⚠️  File {fp} missing – skipping")
            continue

        with fp.open() as f:
            data = json.load(f)

        if fp.name == "reddit.json":
            for post in data:
                blob = " ".join([
                    post.get("title", ""),
                    post.get("body", ""),
                    *post.get("comments", []),
                ])
                yield {"text": blob, "source": "reddit"}

        elif fp.name == "wiki.json":
            for row in data:
                blob = f"{row.get('theory', '')}. {row.get('summary', '')}"
                yield {"text": blob, "source": "wikipedia"}

        # elif fp.name == "conspiracy_snippets.json":
        #     for snippet in data:
        #         yield {"text": snippet, "source": "snippet"}

        # else:
        #     print(f"Unknown schema for {fp}, skipping…")


def parse_sentence(doc: Doc, sent_idx: int, source: str) -> Dict:
    """Return a serialisable dict with POS / dependency info for one sentence."""
    return {
        "source": source,
        "sentence_index": sent_idx,
        "text": doc.text,
        "tokens": [
            {
                "text": tok.text,
                "lemma": tok.lemma_,
                "pos": tok.pos_,
                "tag": tok.tag_,
                "dep": tok.dep_,
                "head": tok.head.i,
                "is_stop": tok.is_stop,
            }
            for tok in doc
        ],
        # optional sentiment (requires spaCyTextBlob or similar pipeline component)
        "sentiment": getattr(doc._, "polarity", None),
    }


def main():
    nlp = spacy.load(SPACY_MODEL, disable=["ner"])  # NER not needed here (yet)

    with OUT_PATH.open("w") as fout:
        for doc_idx, record in enumerate(iter_documents()):
            for sent_idx, sent in enumerate(nlp(record["text"]).sents):
                parsed = parse_sentence(sent, sent_idx, record["source"])
                fout.write(json.dumps(parsed, ensure_ascii=False) + "\n")

            if doc_idx % 100 == 0:
                print(f"Processed {doc_idx} docs…")

    print(f"✅ Parsing complete → {OUT_PATH}")


if __name__ == "__main__":
    main()
