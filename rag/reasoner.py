import requests
from rag.retriever import retrieve

def ask_llm(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

def rag_answer(question, stored):
    # 1. Retrieve relevant chunks
    results = retrieve(question, stored, k=3)

    # 2. Combine context
    context = "\n\n".join(results)

    # 3. Build RAG prompt
    prompt = f"""
You are a networking expert.
Answer ONLY using the context below.

Context:
{context}

Question:
{question}
"""

    # 4. Ask LLM
    return ask_llm(prompt)