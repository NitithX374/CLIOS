from rag.retriever import retrieve
import json

def test_query(question):
    print(f"\n======================================")
    print(f"QUESTION: '{question}'")
    print(f"======================================")
    
    # Retrieve top 5 chunks
    results = retrieve(question, top_k=5)
    
    print(f"Found {len(results)} chunks.\n")
    for i, r in enumerate(results):
        meta = r.get("metadata", {})
        proto = meta.get("protocol", "Unknown")
        rfc = meta.get("rfc", "Unknown")
        section = meta.get("section", "")
        title = meta.get("title", "Unknown Title")
        score = r.get("score", 0.0)
        
        print(f"--- Result {i+1} [Score: {score:.3f}] ---")
        print(f"Source: {proto} (RFC {rfc}) | Section: {section} - {title}")
        print(f"Text Preview: {r['text'][:400]}...")
        print()

if __name__ == "__main__":
    test_query("what method that RIP use to prevent routing loop")
