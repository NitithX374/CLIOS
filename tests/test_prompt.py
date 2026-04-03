from rag.retriever import retrieve
from chat import export_topology

query = "How does TCP 3-way handshake work?"
topology = export_topology()
results = retrieve(query, top_k=3)

rag_text = ""
for r in results:
    meta = r.get("metadata", {})
    proto = meta.get("protocol", "Unknown")
    section = meta.get("section", "")
    title = meta.get("title", "")
    
    rag_text += f"[Source: {proto} RFC, Section: {section} - {title}]\n"
    rag_text += r["text"] + "\n\n"

prompt = f"""
Network Topology
================
{topology}

Reference Knowledge
================
{rag_text}

Question
================
{query}

Explain the answer using the topology and the reference knowledge.
"""

print("\n[DEBUG] THIS IS THE EXACT FINAL PROMPT PAYLOAD THAT GETS SENT TO THE LLM API:\n")
print("=" * 80)
print(prompt)
print("=" * 80)
