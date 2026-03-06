import networkx as nx

def generate_routing_table(G, source):
    distances, paths = nx.single_source_dijkstra(G, source)
    table = {}

    for dest in paths:
        if dest == source:
            continue

        path = paths[dest]
        next_hop = path[1] if len(path) > 1 else dest

        table[dest] = {
            "cost": distances[dest],
            "next_hop": next_hop
        }

    return table


def compare_tables(old, new):
    changes = []
    all_dest = set(old.keys()).union(set(new.keys()))

    for dest in all_dest:
        if dest not in old:
            changes.append({"type": "NEW", "dest": dest, "data": new[dest]})
        elif dest not in new:
            changes.append({"type": "REMOVED", "dest": dest})
        elif old[dest] != new[dest]:
            changes.append({
                "type": "CHANGED",
                "dest": dest,
                "old": old[dest],
                "new": new[dest]
            })

    return changes