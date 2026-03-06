import faiss
import pickle
import numpy as np
import time
from rag.chunker import chunk_text
from rag.embedder import embed


def build_vector_store(file_path):
    start_time = time.time()

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    total_chunks = len(chunks)
    print("Total chunks:", total_chunks)
    print("Starting embedding process...\n")

    embeddings = []

    for i, chunk in enumerate(chunks):
        vec = embed(chunk)
        vec = np.array(vec, dtype="float32")
        embeddings.append(vec)
        if (i + 1) % 10 == 0 or (i + 1) == total_chunks:
            percent = ((i + 1) / total_chunks) * 100
            print(f"Processed {i+1}/{total_chunks} chunks ({percent:.2f}%)")

    embeddings = np.vstack(embeddings)

    print("\nEmbeddings shape:", embeddings.shape)
    print("Embedding dimension:", embeddings.shape[1])

    dimension = embeddings.shape[1]

    print("\nBuilding FAISS index...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, "faiss.index")

    with open("chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    end_time = time.time()
    print("\nFAISS index and chunks saved!")
    print(f"Total time: {end_time - start_time:.2f} seconds")