import faiss
import pickle

def load_vector_store():
    index = faiss.read_index("faiss.index")

    with open("chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    return index, chunks