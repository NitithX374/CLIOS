import networkx as nx

LSA_DELAY = 0.1
SPF_DELAY = 0.2
FLOOD_PER_HOP = 0.1

def simulate_link_failure(G, node1, node2, detecting_router):

    events = []
    t = 0.0

    if G.has_edge(node1, node2):
        G.remove_edge(node1, node2)
        events.append((t, f"Link {node1}-{node2} DOWN detected by {detecting_router}"))
    else:
        return [("0.0", "Link not found")]

    t += LSA_DELAY
    events.append((t, f"{detecting_router} generates LSA"))

    lengths = nx.single_source_shortest_path_length(G, detecting_router)

    for router, hop in lengths.items():
        if router != detecting_router:
            flood_time = t + (hop * FLOOD_PER_HOP)
            events.append((flood_time, f"{router} receives LSA (hop={hop})"))

    t += SPF_DELAY
    events.append((t, "All routers run SPF"))

    t += 0.2
    events.append((t, "Routing tables updated"))

    return sorted(events)