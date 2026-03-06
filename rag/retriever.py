import faiss
import pickle
import numpy as np
from rag.embedder import embed


# โหลด index + chunks แค่ครั้งเดียว
index = faiss.read_index("faiss.index")

with open("chunks.pkl", "rb") as f:
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