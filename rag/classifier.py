import re
import numpy as np
from rag.embedder import embed

PROTOCOL_KEYWORDS = {
    "TCP": ["tcp", "transmission control", "handshake", "retransmission", "syn", "ack", "fin", "window size", "sequence number"],
    "OSPF": ["ospf", "link state", "lsa", "spf", "area 0", "asbr", "hello packet", "dijkstra", "router id"],
    "RIP": ["rip", "routing information protocol", "distance vector", "hop count", "bellman-ford"],
    "UDP": ["udp", "user datagram", "datagram", "connectionless", "port"],
    "IP": ["ip", "internet protocol", "type of service", "fragmentation", "ttl", "tos", "header checksum"],
    "EIGRP": ["eigrp", "enhanced interior", "dual", "feasible successor", "successor", "hello interval", "diffusing"],
    "ICMP": ["icmp", "internet control message", "ping", "echo request", "echo reply", "destination unreachable", "time exceeded"],
    "ARP": ["arp", "address resolution protocol", "mac address", "hardware address", "arp request", "arp reply"],
    "ROUTER": ["router", "routing requirements", "forwarding", "gateway", "ip router", "fragmentation", "packet forwarding"]
}

PROTOCOL_DESCRIPTIONS = {
    "TCP": "Transmission Control Protocol. Connection-oriented, reliable delivery, 3-way handshake, retransmission, windowing.",
    "OSPF": "Open Shortest Path First. Interior Gateway Protocol, Link-state routing, Dijkstra's SPF algorithm, areas, LSA.",
    "RIP": "Routing Information Protocol. Distance vector routing, hop count metric, bellman-ford.",
    "UDP": "User Datagram Protocol. Connectionless, unreliable transmission, minimal overhead, fast.",
    "IP": "Internet Protocol. Addressing, fragmentation, Type of Service (ToS), Time to Live (TTL), IPv4.",
    "EIGRP": "Enhanced Interior Gateway Routing Protocol. Advanced distance vector, DUAL algorithm, successors.",
    "ICMP": "Internet Control Message Protocol. Error reporting, echo queries, ping, routing diagnostics.",
    "ARP": "Address Resolution Protocol. Resolving IP networking addresses to local hardware/MAC addresses.",
    "ROUTER": "IPv4 Router Requirements. General forwarding rules, datagram parsing, gateway behavior."
}

_embedded_descriptions = None

def get_embedded_descriptions():
    global _embedded_descriptions
    if _embedded_descriptions is None:
        _embedded_descriptions = {}
        for proto, desc in PROTOCOL_DESCRIPTIONS.items():
            _embedded_descriptions[proto] = np.array(embed(desc), dtype="float32")
    return _embedded_descriptions

def cosine_similarity(v1, v2):
    v1_norm = np.linalg.norm(v1)
    v2_norm = np.linalg.norm(v2)
    if v1_norm == 0 or v2_norm == 0:
        return 0.0
    return np.dot(v1, v2) / (v1_norm * v2_norm)

def classify_query(query):
    query_lower = query.lower()
    
    # 1. Keyword matching (Fast Path)
    scores = {p: 0 for p in PROTOCOL_KEYWORDS}
    for proto, keywords in PROTOCOL_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{kw}\b", query_lower):
                scores[proto] += 1
                
    max_kw_score = max(scores.values())
    
    candidates = []
    if max_kw_score > 0:
        candidates = [p for p, score in scores.items() if score == max_kw_score]
        # Return top 2 candidates if multiple have same score, else just top 1
        return candidates[:2], 1.0  # (candidates, confidence)
        
    # 2. Embedding similarity (Fallback)
    query_vec = np.array(embed(query), dtype="float32")
    emb_desc = get_embedded_descriptions()
    
    sim_scores = []
    for proto, desc_vec in emb_desc.items():
        sim = cosine_similarity(query_vec, desc_vec)
        sim_scores.append((proto, sim))
        
    sim_scores.sort(key=lambda x: x[1], reverse=True)
    
    top_sim = sim_scores[0][1]
    confidence = top_sim
    candidates = [sim_scores[0][0]]
    if len(sim_scores) > 1 and (top_sim - sim_scores[1][1] < 0.05):
        candidates.append(sim_scores[1][0])
        
    return candidates, confidence
