from rag.loader import load_vector_store
from rag.retriever import retrieve

stored = load_vector_store()  

results = retrieve("Explain Router-LSA in OSPF", stored, k=3)

print("\n=== TOP RESULTS ===\n")

for i, r in enumerate(results):
    print(f"\n--- Result {i+1} ---\n")
    print(r[:500])