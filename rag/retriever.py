import faiss
import pickle
import numpy as np
import sys
import os
from rank_bm25 import BM25Okapi

from rag.embedder import embed, cross_score
import rag.classifier as classifier

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

_loaded_metadata = {}
_loaded_chunk_indexes = {}
_loaded_bm25 = {}

def get_protocol_data(proto):
    global _loaded_metadata
    global _loaded_chunk_indexes
    global _loaded_bm25
    
    if proto not in _loaded_metadata:
        meta_path = resource_path(f"rag/metadata_{proto}.pkl")
        chunk_idx_path = resource_path(f"rag/faiss_{proto}_chunks.index")
        
        if not os.path.exists(meta_path) or not os.path.exists(chunk_idx_path):
            return None, None, None
            
        with open(meta_path, "rb") as f:
            _loaded_metadata[proto] = pickle.load(f)
            
        _loaded_chunk_indexes[proto] = faiss.read_index(chunk_idx_path)
        
        # Initialize BM25 dynamically into RAM
        corpus = [chunk["text"] for chunk in _loaded_metadata[proto]["chunks"]]
        tokenized_corpus = [doc.lower().split() for doc in corpus]
        _loaded_bm25[proto] = BM25Okapi(tokenized_corpus)
        
    return _loaded_metadata[proto], _loaded_chunk_indexes[proto], _loaded_bm25[proto]


def get_available_protocols():
    protos = []
    rag_dir = resource_path("rag")
    if not os.path.exists(rag_dir): return protos
    for f in os.listdir(rag_dir):
        if f.startswith("metadata_") and f.endswith(".pkl"):
            protos.append(f.replace("metadata_", "").replace(".pkl", ""))
    return protos


def retrieve_from_protocol(proto, query, query_vec, top_k_candidates=15):
    meta, chunk_index, bm25 = get_protocol_data(proto)
    if not meta or not chunk_index or not bm25:
        return []
        
    chunks = meta["chunks"]
    if not chunks:
        return []

    # 1. Dense Semantic Retrieval (FAISS)
    k_search = min(20, len(chunks))
    distances, indices = chunk_index.search(query_vec, k_search)
    faiss_ranks = {idx: rank for rank, idx in enumerate(indices[0]) if idx != -1}
    
    # 2. Sparse Keyword Retrieval (BM25)
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_indices = np.argsort(bm25_scores)[::-1][:k_search]
    bm25_ranks = {idx: rank for rank, idx in enumerate(bm25_indices) if bm25_scores[idx] > 0}
    
    # 3. Mathematical Reciprocal Rank Fusion (RRF)
    all_indices = set(faiss_ranks.keys()).union(set(bm25_ranks.keys()))
    rrf_scores = []
    for idx in all_indices:
        f_rank = faiss_ranks.get(idx, 1000)
        b_rank = bm25_ranks.get(idx, 1000)
        rrf_score = (1.0 / (f_rank + 60)) + (1.0 / (b_rank + 60))
        rrf_scores.append((rrf_score, idx))
        
    rrf_scores.sort(key=lambda x: x[0], reverse=True)
    top_candidates_idx = [x[1] for x in rrf_scores[:top_k_candidates]]
    
    candidates = [chunks[idx] for idx in top_candidates_idx]
    if not candidates:
        return []
        
    # 4. Deep Neural Reranking via Cross-Encoder
    candidate_texts = [c["text"] for c in candidates]
    ce_scores = cross_score(query, candidate_texts)
    
    results = []
    for chunk, ce_score in zip(candidates, ce_scores):
        results.append({
            "score": float(ce_score),
            "text": chunk["text"],
            "metadata": {
                "protocol": chunk.get("protocol", proto),
                "rfc": chunk.get("rfc_version", "unknown"),
                "section": chunk.get("section", ""),
                "title": chunk.get("title", "")
            }
        })
        
    # Sort by true semantic relevance cross-score (logits)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def retrieve(query, top_k=8):
    candidates, confidence = classifier.classify_query(query)
    
    query_vec = np.array(embed(query), dtype="float32").reshape(1, -1)
    
    results = []
    
    if confidence >= 0.4 and candidates:
        for proto in candidates:
            # Over-retrieve candidates per active protocol, then we rerank across them
            proto_results = retrieve_from_protocol(proto, query, query_vec, top_k_candidates=12)
            results.extend(proto_results)
    else:
        all_protos = get_available_protocols()
        for proto in all_protos:
            # Panic fallback mode, slim context retrieval
            proto_results = retrieve_from_protocol(proto, query, query_vec, top_k_candidates=3)
            results.extend(proto_results)
            
    # Final global rerank combining all protocol logits
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]