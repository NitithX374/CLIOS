from core.topology_engine import build_graph
from core.routing_engine import generate_routing_table, compare_tables
from core.failure_engine import simulate_link_failure
from visualization.diagram_generator import generate_diagram, open_file
from modes.simulation_modes import (
    run_manual_mode,
    run_random_mode,
    run_batch_mode
)

from rag.retriever import retrieve
import copy
import json
import pickle


# -----------------------------
# Load topology
# -----------------------------
def load_topology_from_file(path):
    with open(path, "r") as f:
        return json.load(f)


# -----------------------------
# Load RAG vector store
# -----------------------------
def load_vector_store():
    with open("vector_store.pkl", "rb") as f:
        return pickle.load(f)


# -----------------------------
# Ask LLM with RAG
# -----------------------------
import requests

def analyze_with_rag(data_package, stored_chunks):

    question = f"""
Topology failure occurred.
Failed link: {data_package['failure']['link']}
Detected by: {data_package['failure']['detected_by']}

Routing changes:
{data_package['changes']}

Explain what OSPF mechanism is responsible for convergence.
"""

    # 🔎 Retrieve RFC context
    top_chunks = retrieve(question, stored_chunks)
    context = "\n\n".join([chunk for _, chunk in top_chunks])

    prompt = f"""
You are a CCNP-level OSPF expert.

Answer ONLY using the RFC 2328 context below.
If not found in context, say "Not specified in RFC 2328".

RFC Context:
{context}

Question:
{question}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


# -----------------------------
# Failure input
# -----------------------------
def get_failure_input(G):

    print("\nAvailable links:")
    for edge in G.edges():
        print(f"- {edge[0]} -- {edge[1]}")

    while True:
        node1 = input("\nEnter first router of failed link: ").strip()
        node2 = input("Enter second router of failed link: ").strip()

        if G.has_edge(node1, node2):
            break
        else:
            print("Invalid link. Try again.")

    while True:
        detecting = input("Enter detecting router: ").strip()
        if detecting in [node1, node2]:
            break
        else:
            print("Detecting router must be one of the failed link routers.")

    return [node1, node2], detecting


# =============================
# MAIN
# =============================
if __name__ == "__main__":

    topology = load_topology_from_file("topology.json")
    G = build_graph(topology)
    G_visual = copy.deepcopy(G)

    print("\nSelect Mode:")
    print("1) Manual failure")
    print("2) Random failure")
    print("3) Batch resilience test")

    mode = input("Enter choice: ").strip()

    if mode == "1":
        failed_link, detecting_router = run_manual_mode(G, get_failure_input)

    elif mode == "2":
        failed_link, detecting_router = run_random_mode(G)

    elif mode == "3":
        run_batch_mode(G)
        exit()

    else:
        print("Invalid mode")
        exit()

    # BEFORE
    old_table = generate_routing_table(G, "R1")

    # FAILURE
    events = simulate_link_failure(
        G,
        failed_link[0],
        failed_link[1],
        detecting_router
    )

    # AFTER
    new_table = generate_routing_table(G, "R1")
    changes = compare_tables(old_table, new_table)

    data_package = {
        "topology": topology,
        "failure": {
            "link": failed_link,
            "detected_by": detecting_router
        },
        "timeline": events,
        "changes": changes
    }

    # 🔥 Load RFC vector store
    stored_chunks = load_vector_store()

    # 🔥 RAG Analysis
    analysis = analyze_with_rag(data_package, stored_chunks)

    print("\n===== RAG OSPF ANALYSIS =====\n")
    print(analysis)

    # Visualization
    visual_data = {
        "nodes": list(G_visual.nodes()),
        "edges": list(G_visual.edges()),
        "failed_link": failed_link,
        "detected_by": detecting_router
    }

    generate_diagram(visual_data)
    open_file("network_diagram.png")