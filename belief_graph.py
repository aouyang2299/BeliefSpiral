import json
from collections import Counter
import networkx as nx
from node2vec import Node2Vec
from gensim.models import Word2Vec
from pathlib import Path

# load the model

model = Word2Vec.load("belief_node2vec.model")


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

    print(f"↳ Mapping '{query}' → node «{node}»")

    # 1) record this central node so we never suggest it again
    _seen_queries.add(query)
    _seen_queries.add(node)

    # 2) fetch a few extra neighbors to allow filtering
    raw = model.wv.most_similar(node, topn=topn + len(_seen_queries))

    # 3) drop anything we've already queried
    fresh = [c for c, _ in raw if c not in _seen_queries]

    # 4) warn if we can't fill all slots
    if len(fresh) < topn:
        print(f"⚠️ Only {len(fresh)} new nodes available for '{query}' (wanted {topn}).")

    return fresh[:topn]

# Examples
for q in ["trump", "the New York City mayor", "vaccines", "moon", "right-wing"]:
    print(f"\nQuery: {q!r}")
    print(" Related:", similar_to(q))



    
