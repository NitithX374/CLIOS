import heapq

def generate_lsdb(network):
    lsdb = {}
    for r_name, r in network.routers.items():
        if not r.ospf_enabled:
            continue
            
        links = []
        for intf_name, intf in r.interfaces.items():
            if intf.area is None: continue
            
            link_info = {
                "interface": intf_name,
                "ip": intf.ip,
                "area": intf.area,
                "cost": intf.cost,
            }
            if intf.link:
                peer_r, peer_i = intf.link.split(":")
                peer_router = network.routers.get(peer_r)
                if peer_router and peer_router.ospf_enabled:
                    # connected to another OSPF router (Point-to-Point)
                    link_info["type"] = "Transit"
                    link_info["peer_router"] = peer_r
                    link_info["peer_ip"] = peer_router.interfaces[peer_i].ip
                else:
                    # connected but peer is not OSPF
                    link_info["type"] = "Stub"
            else:
                link_info["type"] = "Stub"
                
            links.append(link_info)
            
        lsdb[r_name] = {
            "router_id": r_name,
            "external_domain": r.external_domain,
            "links": links
        }
    return lsdb

def calculate_spf(network, source_router):
    lsdb = generate_lsdb(network)
    
    if source_router not in lsdb:
        return []
        
    distances = {r: float('infinity') for r in lsdb}
    distances[source_router] = 0
    
    # Store shortest path tree: {destination_router: (next_hop_router, out_interface)}
    spt = {r: None for r in lsdb} 
    
    pq = [(0, source_router)]
    
    while pq:
        current_cost, current_node = heapq.heappop(pq)
        
        if current_cost > distances[current_node]:
            continue
            
        for link in lsdb[current_node]["links"]:
            if link["type"] == "Transit":
                neighbor = link["peer_router"]
                distance = current_cost + link["cost"]
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    
                    if current_node == source_router:
                        spt[neighbor] = (neighbor, link["interface"])
                    else:
                        spt[neighbor] = spt[current_node]
                        
                    heapq.heappush(pq, (distance, neighbor))
                    
    routing_table = []
    
    for r_name, data in lsdb.items():
        if distances[r_name] == float('infinity'):
            continue
            
        # Add stub networks attached to r_name
        for link in data["links"]:
            if link["ip"]:
                network_str = link["ip"]
                
                if r_name == source_router:
                    rt_entry = {
                        "destination": network_str,
                        "type": "intra-area",
                        "cost": link["cost"],
                        "next_hop": "Connected",
                        "interface": link["interface"]
                    }
                else:
                    next_hop_data = spt[r_name]
                    if next_hop_data is None:
                        continue # should not happen if distance < infinity
                    next_hop_r, out_intf = next_hop_data
                    
                    # To be perfectly accurate with OSPF metric:
                    # total cost to stub network = distance to router + cost of stub link
                    # total cost to transit network = distance to neighbor
                    
                    rt_entry = {
                        "destination": network_str,
                        "type": "intra-area",
                        "cost": distances[r_name] + link["cost"],
                        "next_hop": next_hop_r,
                        "interface": out_intf
                    }
                    
                existing = next((rt for rt in routing_table if rt["destination"] == network_str), None)
                if not existing or existing["cost"] > rt_entry["cost"]:
                    if existing:
                        routing_table.remove(existing)
                    routing_table.append(rt_entry)
                    
    routing_table.sort(key=lambda x: x["destination"])
    return routing_table

def format_lsdb(network):
    lsdb = generate_lsdb(network)
    if not lsdb:
        return "OSPF Database is empty."
        
    out = "OSPF Router with ID (Context)\n\n"
    for r_name, data in lsdb.items():
        out += f"  Router LSA for Area\n"
        out += f"    Link State ID: {r_name}\n"
        for link in data["links"]:
            out += f"      Link attached to: {link['type']} Network\n"
            if link["type"] == "Transit":
                out += f"        (Link ID) Neighboring Router ID: {link['peer_router']}\n"
            elif link["type"] == "Stub":
                out += f"        (Link ID) Network/subnet IP: {link['ip']}\n"
            out += f"        (Link Data) Interface IP: {link['ip']}\n"
            out += f"        Metric: {link['cost']}\n\n"
    return out

def format_routing_table(network, router_name):
    rt = calculate_spf(network, router_name)
    if not rt:
        return f"Routing table empty or router '{router_name}' not OSPF enabled."
        
    out = f"Routing Table for {router_name}\n"
    out += f"{'Destination':<18} {'Next Hop':<15} {'Interface':<12} {'Cost':<6}\n"
    out += "-" * 55 + "\n"
    for entry in rt:
        out += f"{entry['destination']:<18} {entry['next_hop']:<15} {entry['interface']:<12} {entry['cost']:<6}\n"
        
    return out
