import random
import networkx as nx
from core.routing_engine import generate_routing_table, compare_tables
from core.failure_engine import simulate_link_failure
from intelligence.llm_reasoner import analyze



def run_manual_mode(G, get_failure_input):
    failed_link, detecting_router = get_failure_input(G)
    return failed_link, detecting_router


def run_random_mode(G):
    edge = random.choice(list(G.edges()))
    detecting_router = random.choice(edge)

    print(f"\nRandom failure selected: {edge}")
    print(f"Detected by: {detecting_router}")

    return list(edge), detecting_router


def run_batch_mode(G):

    print("\nRunning Batch Resilience Test...\n")

    edges = list(G.edges())
    results = []

    total_changes = 0
    connected_count = 0

    for edge in edges:

        G_test = G.copy()

        old_table = generate_routing_table(G_test, "R1")

        simulate_link_failure(G_test, edge[0], edge[1], edge[0])

        new_table = generate_routing_table(G_test, "R1")

        changes = compare_tables(old_table, new_table)

        still_connected = nx.is_connected(G_test)

        total_changes += len(changes)
        if still_connected:
            connected_count += 1

        results.append({
            "failed_link": edge,
            "connected": still_connected,
            "change_count": len(changes)
        })

    # =========================
    # 🔎 1️⃣ Bridge Detection
    # =========================
    bridges = list(nx.bridges(G))

    # =========================
    # 📊 2️⃣ Metrics
    # =========================
    connectivity_ratio = connected_count / len(edges)
    avg_changes = total_changes / len(edges)

    # Normalize stability score (less changes = better)
    stability_score = max(0, 1 - (avg_changes / 10))  # adjust divisor if needed

    # Final Resilience Score
    resilience_score = (
        connectivity_ratio * 50 +
        stability_score * 30 +
        (1 - len(bridges)/len(edges)) * 20
    )

    print("===== Batch Summary =====")
    print(f"Connectivity survival rate: {connectivity_ratio*100:.2f}%")
    print(f"Average routing changes: {avg_changes:.2f}")
    print(f"Critical links (bridges): {bridges}")
    print(f"Resilience Score: {resilience_score:.2f} / 100")

    # =========================
    # 🧠 3️⃣ Send to LLM
    # =========================
    batch_summary = {
        "connectivity_survival_rate": connectivity_ratio,
        "average_routing_changes": avg_changes,
        "critical_links": bridges,
        "resilience_score": resilience_score,
        "total_links_tested": len(edges)
    }

    print("\n===== LLM NETWORK REVIEW =====\n")

    analysis = analyze({
        "mode": "batch_resilience_analysis",
        "summary": batch_summary
    })

    print(analysis)

    return None, None