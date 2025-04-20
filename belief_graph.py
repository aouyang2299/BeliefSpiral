import json
from collections import Counter
import networkx as nx
from node2vec import Node2Vec

# ── 1) Load your JSON of snippets with spaCy concepts ─────────────────────────
DATA_PATH = "raw_data/final_data/newsapi_with_spacy_concepts.json"
with open(DATA_PATH, encoding="utf8") as f:
    records = json.load(f)

# ── 2) Count concept co‑occurrences per snippet ───────────────────────────────
edge_counts = Counter()
for rec in records:
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

def similar_to(query, topn=5):
    node = _find_best_node(query)
    if not node:
        print(f"✗ No node match for '{query}' (tried singular='{query.rstrip('s')}').")
        return []
    print(f"↳ Mapping '{query}' → node «{node}»")
    sims = model.wv.most_similar(node, topn=topn)
    return [c for c, _ in sims]

# Examples
for q in ["trump", "vaccines", "moon", "right-wing"]:
    print(f"\nQuery: {q!r}")
    print(" Related:", similar_to(q))

    
# graph works as intended

# # 1) Load and rebuild G exactly as before
# with open("raw_data/final_data/newsapi_with_spacy_concepts.json", encoding="utf8") as f:
#     records = json.load(f)

# edge_counts = {}
# for rec in records:
#     cs = rec.get("concepts_spacy", [])
#     for i in range(len(cs)):
#         for j in range(i+1, len(cs)):
#             pair = tuple(cs[k] for k in (i,j))
#             edge_counts[pair] = edge_counts.get(pair, 0) + 1

# G = nx.Graph()
# for (a, b), w in edge_counts.items():
#     G.add_edge(a, b, weight=w)

# # 2) Print total nodes & edges
# print("Nodes:", G.number_of_nodes(), "Edges:", G.number_of_edges())

# # 3) List the first 20 nodes (alphabetically)
# print("Sample nodes:", sorted(list(G.nodes()))[:20])

# # 4) Search for any node containing “trump” (case‐insensitive)
# print("Nodes matching 'trump':",
#       [n for n in G.nodes() if "trump" in n.lower()])

# # 5) Print top 10 highest‐degree nodes
# deg = sorted(G.degree(), key=lambda x: x[1], reverse=True)
# print("Top 10 by degree:", deg[:10])

# # 6) (Re)run your embedding query with the exact node name:
# from pprint import pprint
# model = Node2Vec(G, dimensions=64, walk_length=30, num_walks=200, workers=4, weight_key="weight").fit(window=10, min_count=1)
# for query in ["Trump", "Laura Loomer", "NSA"]:
#     print(f"\nMost similar to {query!r}:")
#     try:
#         pprint([c for c, _ in model.wv.most_similar(query, topn=5)])
#     except KeyError:
#         print("x not found in graph nodes")


# ── Example query ──────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     query = "trump"
#     print(f"Top related beliefs to '{query}': {similar_to_fuzzy(query)}")