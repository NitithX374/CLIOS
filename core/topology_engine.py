import networkx as nx

def build_graph(data):
    G = nx.Graph()
    for node, neighbors in data.items():
        for n in neighbors:
            G.add_edge(node, n, cost=1)
    return G