import json
from collections import Counter
import networkx as nx
from node2vec import Node2Vec
from gensim.models import Word2Vec
from pathlib import Path

# load the model

model = Word2Vec.load("belief_node2vec.model")

from difflib import SequenceMatcher

# def _find_best_node(query):
#     q = query.lower()
#     nodes = model.wv.index_to_key

#     # 1) Try substring match on both the raw query and its singular form
#     singular = q.rstrip('s')
#     substr = [
#         n for n in nodes
#         if q in n.lower() or (singular != q and singular in n.lower())
#     ]
#     print(substr)
#     if substr:
#         # Pick the shortest match (most specific)
#         return min(substr, key=lambda n: len(n))

#     # 2) Fallback: fuzzy‐ratio, but only if it’s very strong
#     best, score = None, 0.0
#     for n in nodes:
#         print(nodes)
#         r = SequenceMatcher(None, q, n.lower()).ratio()
#         if r > score:
#             best, score = n, r
            

#     # require a high threshold for fuzzy matching
#     return best if score >= 0.75 else None

# changing above code to find best 5 matches instead


def _find_best_nodes(query: str, topk: int = 5) -> list[str]:
    """
    Return up to `topk` nodes whose names best match `query`:
      1) Any node containing the raw query (or its singular form) as a substring,
         shortest names first.
      2) Otherwise, fuzzy‑match all nodes and return those with ratio ≥ 0.75,
         sorted by descending similarity.
    """
    q = query.lower()
    nodes = model.wv.index_to_key
    singular = q.rstrip('s')

    # 1) substring matches
    substr = [
        n for n in nodes
        if q in n.lower() or (singular != q and singular in n.lower())
    ]
    if substr:
        # sort by length (most specific first) and return topk
        substr_sorted = sorted(substr, key=lambda n: len(n))
        return substr_sorted[:topk]

    # 2) fuzzy fallback
    scores = [(n, SequenceMatcher(None, q, n.lower()).ratio()) for n in nodes]
    # keep only strong matches
    filtered = [ (n, r) for n, r in scores if r >= 0.75 ]
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _ in filtered[:topk]]

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

    # store only the first node
    # but use all nodes found to generate neighbors
    # select top 2 neighbors from each node
    # select top 5 from the 10 based on score

# … keep your imports, global `_seen_queries`, and _find_best_nodes as before …

def similar_to(query: str, topn: int = 5) -> list[str]:
    # 1) find up to five matching central candidates
    candidates = _find_best_nodes(query, topk=5)
    if not candidates:
        print(f"✗ No node match for '{query}'.")
        return []

    # choose the first one as our true "central" node
    central = candidates[0]
    print(f"↳ Mapping '{query}' → node «{central}» (candidates: {candidates})")

    # 2) mark query and central so we never re‑suggest them
    _seen_queries.add(query)
    _seen_queries.add(central)

    # 3) for each candidate, pull top‑2 neighbors
    all_neighbors: list[tuple[str,float]] = []
    for cand in candidates:
        for neigh, score in model.wv.most_similar(cand, topn=2):
            if neigh not in _seen_queries:
                all_neighbors.append((neigh, score))

    # 4) sort ALL collected neighbors by score desc
    all_neighbors.sort(key=lambda x: x[1], reverse=True)

    # 5) take the top‑`topn` unique neighbor names
    seen_nei = set()
    final: list[str] = []
    for neigh, score in all_neighbors:
        if neigh in seen_nei:
            continue
        seen_nei.add(neigh)
        final.append(neigh)
        if len(final) >= topn:
            break

    # warn if we couldn’t fill all slots
    if len(final) < topn:
        print(f"⚠️ Only {len(final)} new nodes available for '{query}' (wanted {topn}).")

    return final


# def similar_to(query, topn=5):
#     node = _find_best_nodes(query) # gets top 5 nodes now

#     if not node:
#         print(f"✗ No node match for '{query}' (tried singular='{query.rstrip('s')}').")
#         return []

#     print(f"↳ Mapping '{query}' → node «{node}»")

#     # 1) record this central node so we never suggest it again
#     _seen_queries.add(query)
#     _seen_queries.add(node)

#     # 2) fetch a few extra neighbors to allow filtering
#     raw = model.wv.most_similar(node, topn=topn + len(_seen_queries))

#     # 3) drop anything we've already queried
#     fresh = [c for c, _ in raw if c not in _seen_queries]

#     # 4) warn if we can't fill all slots
#     if len(fresh) < topn:
#         print(f"⚠️ Only {len(fresh)} new nodes available for '{query}' (wanted {topn}).")

#     return fresh[:topn]

# Examples
for q in ["trump"]: # ["trump", "the New York City mayor", "vaccines", "moon", "right-wing"]:
    print(f"\nQuery: {q!r}")
    print(" Related:", similar_to(q))



    
