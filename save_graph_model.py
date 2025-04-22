import json
from collections import Counter
import networkx as nx
from node2vec import Node2Vec
from gensim.models import Word2Vec
from pathlib import Path

# 1) Manually list your files ──────────────────────────────────────────────
input_files = [
    "raw_data/final_data/newsapi_100_with_spacy_concepts010_full.json",
    "raw_data/final_data/reddit_600_with_spacy_concepts010__filtered_full.json",
    "raw_data/final_data/wiki_180_with_spacy_concepts011_full.json",
    "raw_data/final_data/nyt_200_with_spacy_concepts011_full.json", 
    "raw_data/final_data/guardian_200_with_spacy_concepts011_full.json"
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
output_fp = Path("raw_data/final_data") / "all_spacy_concepts_final.json"
output_fp.parent.mkdir(exist_ok=True)
with output_fp.open("w", encoding="utf8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)

print(f"✅ Merged {len(all_records)} records into {output_fp}")

# file_path = Path("raw_data/final_data/all_spacy_concepts_final.json")

# # Read and parse the JSON
# with file_path.open(encoding="utf8") as f:
#     all_records = json.load(f)

# # Summary information
# print(f"✅ Loaded {len(all_records)} records from {file_path}")

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
    
model.save("belief_node2vec.model")