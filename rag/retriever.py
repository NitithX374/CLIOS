import faiss
import pickle
import numpy as np
import sys
import os
from rag.embedder import embed
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



# โหลด index + chunks แค่ครั้งเดียว
index = faiss.read_index(resource_path("faiss.index"))

with open(resource_path("chunks.pkl"), "rb") as f:
    chunks = pickle.load(f)


def retrieve(query, top_k=5):
    query_vec = embed(query)
    query_vec = np.array(query_vec, dtype="float32").reshape(1, -1)

    distances, indices = index.search(query_vec, top_k)

    results = []

    for i, idx in enumerate(indices[0]):
        results.append({
            "score": float(distances[0][i]),
            "text": chunks[idx]
        })

    return results