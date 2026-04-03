import traceback
try:
    print("Testing embedder...")
    from rag.embedder import embed
    vec = embed("test sentence")
    print("Embedder OK, dim:", len(vec))
    
    print("Testing classifier...")
    import rag.classifier as classifier
    candidates, conf = classifier.classify_query("how does tcp 3 way handshake work?")
    print("Classifier Result:", candidates, conf)
    
    print("All syntax checks passed!")
except Exception as e:
    print("Error:")
    traceback.print_exc()
