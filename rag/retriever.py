import faiss
import pickle
import numpy as np
import sys
import os

from rag.embedder import embed
import rag.classifier as classifier

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

_loaded_metadata = {}
_loaded_sec_indexes = {}

def get_protocol_data(proto):
    global _loaded_metadata
    global _loaded_sec_indexes
    if proto not in _loaded_metadata:
        meta_path = resource_path(f"rag/metadata_{proto}.pkl")
        sec_idx_path = resource_path(f"rag/faiss_{proto}_sections.index")
        
        if not os.path.exists(meta_path) or not os.path.exists(sec_idx_path):
            return None, None
            
        with open(meta_path, "rb") as f:
            _loaded_metadata[proto] = pickle.load(f)
        _loaded_sec_indexes[proto] = faiss.read_index(sec_idx_path)
        
    return _loaded_metadata[proto], _loaded_sec_indexes[proto]

def get_available_protocols():
    protos = []
    rag_dir = resource_path("rag")
    if not os.path.exists(rag_dir): return protos
    for f in os.listdir(rag_dir):
        if f.startswith("metadata_") and f.endswith(".pkl"):
            protos.append(f.replace("metadata_", "").replace(".pkl", ""))
    return protos

def retrieve_from_protocol(proto, query_vec, top_k_sec=3, top_k_chunk=5):
    meta, sec_index = get_protocol_data(proto)
    if not meta or not sec_index:
        return []
        
    # Stage 1: Retrieve top-k relevant sections
    distances, indices = sec_index.search(query_vec, top_k_sec)
    
    candidate_chunks = []
    
    for i, idx in enumerate(indices[0]):
        if idx == -1: continue # FAISS returning -1 means not enough results
        
        sec_obj = meta["sections"][idx]
        
        # Stage 2: Retrieve chunks within those sections
        for chunk in sec_obj["chunk_records"]:
            candidate_chunks.append(chunk)
            
    if not candidate_chunks:
        return []
        
    # Re-rank chunks using cosine similarity against query
    q_vec_1d = query_vec[0]
    
    scored_chunks = []
    for chunk in candidate_chunks:
        chunk_vec = np.array(chunk["embedding"], dtype="float32")
        
        # calculate cosine similarity
        v1_norm = np.linalg.norm(q_vec_1d)
        v2_norm = np.linalg.norm(chunk_vec)
        if v1_norm == 0 or v2_norm == 0:
            sim = 0
        else:
            sim = np.dot(q_vec_1d, chunk_vec) / (v1_norm * v2_norm)
        
        scored_chunks.append({
            "score": float(sim),
            "text": chunk["text"],
            "metadata": {
                "protocol": chunk.get("protocol", proto),
                "rfc": chunk.get("rfc_version", "unknown"),
                "section": chunk.get("section", ""),
                "title": chunk.get("title", "")
            }
        })
        
    # Sort and return top-n chunks
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k_chunk]


def retrieve(query, top_k=5):
    candidates, confidence = classifier.classify_query(query)
    
    query_vec = np.array(embed(query), dtype="float32").reshape(1, -1)
    
    results = []
    
    # Threshold for fallback is 0.4. If keyword matched, confidence is 1.0.
    if confidence >= 0.4 and candidates:
        # High confidence -> Query only the specific protocol(s)
        for proto in candidates:
            proto_results = retrieve_from_protocol(proto, query_vec, top_k_sec=3, top_k_chunk=top_k)
            results.extend(proto_results)
    else:
        # Low confidence -> Fallback strategy: query all and merge
        all_protos = get_available_protocols()
        for proto in all_protos:
            proto_results = retrieve_from_protocol(proto, query_vec, top_k_sec=1, top_k_chunk=2)
            results.extend(proto_results)
            
    # Final global rerank/sort across protocols if necessary
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]