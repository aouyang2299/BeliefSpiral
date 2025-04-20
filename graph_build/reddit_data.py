import json
from collections import defaultdict
from itertools import combinations
import spacy
import networkx as nx
from node2vec import Node2Vec

def flatten_post(post): #flattens a single dict entry 
    parts = [post.get('title', ''), post.get('body', '')] + post.get('comments', [])
    return " ".join(parts)  

#load data 
with open('../raw_data/reddit.json', 'r') as f:
    reddit_data = json.load(f)

for post in reddit_data:
    texts = [post.get('title', ''), post.get('body', '')] + post.get('comments', [])
    combined_text = " ".join(texts)


