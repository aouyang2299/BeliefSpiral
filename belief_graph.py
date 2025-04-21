import json
from collections import Counter
import networkx as nx
from node2vec import Node2Vec

# ── 1) Load your JSON of snippets with spaCy concepts ─────────────────────────
import json
from pathlib import Path

# 1) Manually list your files ──────────────────────────────────────────────
input_files = [
    "raw_data/final_data/newsapi_100_with_spacy_concepts010_full.json",
    "raw_data/final_data/reddit_500_with_spacy_concepts010.json",
    "raw_data/final_data/wiki_180_with_spacy_concepts010_full.json"
]

# 2) Load & concatenate ────────────────────────────────────────────────────
all_records = []
for path_str in input_files:
    fp = Path(path_str)
    if not fp.exists():
        print(f"⚠️ File not found: {fp}")
        continue
    with fp.open(encoding="utf8") as f:
        data = json.load(f)
        all_records.extend(data)

# 3) Write out merged file ─────────────────────────────────────────────────
output_fp = Path("raw_data/final_data") / "all_spacy_concepts_combined.json"
output_fp.parent.mkdir(exist_ok=True)
with output_fp.open("w", encoding="utf8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)

print(f"✅ Merged {len(all_records)} records into {output_fp}")


# ── 2) Count concept co‑occurrences per snippet ───────────────────────────────
edge_counts = Counter()
for rec in all_records:
    concepts = rec.get("concepts_spacy", [])
    # all unordered pairs within this snippet
    for i in range(len(concepts)):
        for j in range(i+1, len(concepts)):
            a, b = concepts[i], concepts[j]
            # you could sort((a, b)) to force a consistent order
            edge_counts[(a, b)] += 1

# ── 3) Build a weighted, undirected graph ─────────────────────────────────────
G = nx.Graph()
for (a, b), weight in edge_counts.items():
    G.add_edge(a, b, weight=weight)

print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ── 4) Train Node2Vec embeddings ───────────────────────────────────────────────
#    (treats weighted edges as transition biases)
node2vec = Node2Vec(
    G,
    dimensions=64,      # size of embedding vectors
    walk_length=30,     # how long each random walk is
    num_walks=200,      # how many walks per node
    workers=4,          # parallelism
    weight_key="weight"
)
model = node2vec.fit(
    window=10,       # context size for Skip‑gram
    min_count=1,     # include all nodes, even leaf nodes
    batch_words=4
)
    
from difflib import SequenceMatcher

def _find_best_node(query):
    q = query.lower()
    nodes = model.wv.index_to_key

    # 1) Try substring match on both the raw query and its singular form
    singular = q.rstrip('s')
    substr = [
        n for n in nodes
        if q in n.lower() or (singular != q and singular in n.lower())
    ]
    if substr:
        # Pick the shortest match (most specific)
        return min(substr, key=lambda n: len(n))

    # 2) Fallback: fuzzy‐ratio, but only if it’s very strong
    best, score = None, 0.0
    for n in nodes:
        r = SequenceMatcher(None, q, n.lower()).ratio()
        if r > score:
            best, score = n, r

    # require a high threshold for fuzzy matching
    return best if score >= 0.75 else None

# def similar_to(query, topn=5):
#     node = _find_best_node(query)
#     if not node:
#         print(f"✗ No node match for '{query}' (tried singular='{query.rstrip('s')}').")
#         return []
#     print(f"↳ Mapping '{query}' → node «{node}»")
#     sims = model.wv.most_similar(node, topn=topn)
#     return [c for c, _ in sims]

# curr problem - nodes that already appeared will appear again in later searches 
# ex. trump ==> eric adams ==> trump 

# new function similar_to()

# 👇 Added at the top (after imports)
_seen_queries = set()


def similar_to(query, topn=5):
    node = _find_best_node(query)
    if not node:
        print(f"✗ No node match for '{query}' (tried singular='{query.rstrip('s')}').")
        return []

    # 👇 Skip nodes we've already shown before
    if node in _seen_queries:
        print(f"✓ Skipping node '{node}' (already seen)")
        return []

    _seen_queries.add(node)  # 👈 Mark this node as seen
    print(f"↳ Mapping '{query}' → node «{node}»")

    sims = model.wv.most_similar(node, topn=topn)
    return [c for c, _ in sims if c not in _seen_queries]



# Examples
for q in ["trump", "the New York City mayor", "vaccines", "moon", "right-wing"]:
    print(f"\nQuery: {q!r}")
    print(" Related:", similar_to(q))



    
