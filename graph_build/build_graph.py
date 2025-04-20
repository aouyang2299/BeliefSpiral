import json
import pathlib
from itertools import combinations

import networkx as nx
from node2vec import Node2Vec
from tqdm import tqdm

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
RAW_SENT_PATH = pathlib.Path("../raw_data/parsed_sentences.jsonl")
#GRAPH_PATH = RAW_SENT_PATH.parent / "belief_graph.gpickle"
EMB_PATH = RAW_SENT_PATH.parent / "belief_embeddings.txt"

# node2vec hyper‑params — tweak later
DIM = 64
WALK_LEN = 30
NUM_WALKS = 200
WINDOW = 10

# -----------------------------------------------------------------------------
# 1) BUILD CO‑OCCURRENCE GRAPH
# -----------------------------------------------------------------------------
print("\n⏳  Building co‑occurrence graph …")
G = nx.Graph()
with RAW_SENT_PATH.open() as f:
    for line in tqdm(f, total=sum(1 for _ in open(RAW_SENT_PATH))):
        sent = json.loads(line)
        # keep nouns + proper nouns that are NOT stop words
        concepts = {t["lemma"].lower() for t in sent["tokens"]
                    if t["pos"] in ("NOUN", "PROPN") and not t["is_stop"]}
        # add edges for every unordered pair in this sentence
        for a, b in combinations(concepts, 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)
print(f"✔️  graph done  —  {G.number_of_nodes()} nodes  /  {G.number_of_edges()} edges")

#nx.write_gpickle(G, GRAPH_PATH)
#print(f"📦  saved graph → {GRAPH_PATH}\n")

# -----------------------------------------------------------------------------
# 2) TRAIN NODE2VEC EMBEDDING
# -----------------------------------------------------------------------------
print("⏳  training node2vec … (this can take a minute)")
node2vec = Node2Vec(G, dimensions=DIM, walk_length=WALK_LEN,
                    num_walks=NUM_WALKS, workers=4)
model = node2vec.fit(window=WINDOW, min_count=1, batch_words=4)
model.wv.save_word2vec_format(EMB_PATH)
print(f"✅  embeddings saved → {EMB_PATH}\n")

# -----------------------------------------------------------------------------
# 3) QUICK TEST
# -----------------------------------------------------------------------------
try:
    query = "vaccines"
    if query in model.wv:
        print(f"Top neighbours for '{query}':")
        for word, score in model.wv.most_similar(query, topn=10):
            print(f"  {word:20}  {score:.3f}")
    else:
        print(f"'{query}' not in vocab — try another word")
except Exception as e:
    print("⚠️  quick‑test failed:", e)
