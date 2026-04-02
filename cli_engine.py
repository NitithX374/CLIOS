import graphviz
import os
from network_state import network
from ospf_engine import format_lsdb, format_routing_table

def _draw_topology(net):
    dot = graphviz.Graph(comment='Network Topology', format='png')
    dot.attr(rankdir='LR')

    for r_name, r in net.routers.items():
        # Detect ASBR
        is_asbr = False
        if r.ospf_enabled:
            for intf in r.interfaces.values():
                if intf.link:
                    peer_r, _ = intf.link.split(":")
                    if net.routers[peer_r].external_domain:
                        is_asbr = True
                        break

        label = f"{r_name}"
        fillcolor = 'lightblue'

        if r.external_domain:
            label += f"\n({r.external_domain})"
            fillcolor = 'lightgrey'
        elif is_asbr:
            label += "\n(OSPF ASBR)"
            fillcolor = 'orange'
        elif r.ospf_enabled:
            label += "\n(OSPF)"
            
        dot.node(r_name, label, shape='box', style='filled', fillcolor=fillcolor)

    drawn_links = set()
    for r_name, r in net.routers.items():
        for intf_name, intf in r.interfaces.items():
            if intf.link:
                peer_r, peer_i = intf.link.split(":")
                link_key = tuple(sorted([f"{r_name}:{intf_name}", f"{peer_r}:{peer_i}"]))
                
                if link_key not in drawn_links:
                    edge_label = f"{intf_name} -- {peer_i}"
                    # Add area type to edge label if exists
                    if intf.area in net.area_types:
                        edge_label += f"\n(Area {intf.area} {net.area_types[intf.area]})"
                    dot.edge(r_name, peer_r, label=edge_label)
                    drawn_links.add(link_key)
                    
    try:
        dot.render('topology_output', view=True)
    except Exception as e:
        print(f"\n[Warning] Could not render Graphviz topology: {e}")

def process_command(cmd):

    tokens = cmd.split()

    if not tokens:
        return ""

    if tokens[0] == "?":
        return """
Available commands:

router <name>
no router <name>
interface <router> <name>
ip address <router> <intf> <ip/subnet>
cost <router> <intf> <value>
connect <r1> <i1> <r2> <i2>
ospf enable <router>
area <router> <interface> <area_id>
areatype <id> <stub|totally-stub|nssa|normal>
external <router> <domain>
show topology
show ip route <router>
show ip ospf database
"""

    if tokens[0] == "router":
        if len(tokens) < 2: return "Usage: router <name>"
        name = tokens[1]
        network.add_router(name)
        return f"Router {name} created"

    if tokens[0] == "no" and len(tokens) >= 3 and tokens[1] == "router":
        name = tokens[2]
        if name in network.routers:
            # Clean up links on other routers pointing to this one
            for r in network.routers.values():
                for intf in r.interfaces.values():
                    if intf.link and intf.link.startswith(f"{name}:"):
                        intf.link = None
            del network.routers[name]
            return f"Router {name} deleted"
        return "Router not found"

    if tokens[0] == "interface":
        if len(tokens) < 3: return "Usage: interface <router> <name>"
        router = tokens[1]
        intf = tokens[2]
        network.add_interface(router, intf)
        return f"Interface {intf} created on {router}"

    if tokens[0] == "ip" and tokens[1] == "address":
        if len(tokens) < 5: return "Usage: ip address <router> <intf> <ip/subnet>"
        router = tokens[2]
        intf = tokens[3]
        ip = tokens[4]
        network.set_ip(router, intf, ip)
        return f"{router} {intf} IP set to {ip}"

    if tokens[0] == "cost":
        if len(tokens) < 4: return "Usage: cost <router> <intf> <value>"
        router = tokens[1]
        intf = tokens[2]
        value = tokens[3]
        error = network.set_cost(router, intf, value)
        if error:
            return error
        return f"{router} {intf} OSPF cost set to {value}"

    if tokens[0] == "connect":
        if len(tokens) < 5: return "Usage: connect <r1> <i1> <r2> <i2>"
        r1 = tokens[1]
        i1 = tokens[2]
        r2 = tokens[3]
        i2 = tokens[4]
        network.connect(r1, i1, r2, i2)
        return f"{r1}:{i1} connected to {r2}:{i2}"

    if tokens[0] == "ospf" and tokens[1] == "enable":
        if len(tokens) < 3: return "Usage: ospf enable <router>"
        router = tokens[2]
        network.enable_ospf(router)
        return f"OSPF enabled on {router}"

    if tokens[0] == "external":
        if len(tokens) < 3: return "Usage: external <router> <domain>"
        router = tokens[1]
        domain = tokens[2]
        if router not in network.routers:
            return "Router not found"
        network.routers[router].external_domain = domain
        return f"Router {router} marked as external domain: {domain}"

    if tokens[0] == "areatype":
        if len(tokens) < 3: return "Usage: areatype <id> <type>"
        area_id = tokens[1]
        area_type = tokens[2]
        
        warning = ""
        # Check if changing type causes mismatches for existing members
        for r_name, r in network.routers.items():
            for i_name, i in r.interfaces.items():
                if i.area == area_id and i.link:
                    peer_r, peer_i = i.link.split(":")
                    peer_area = network.routers[peer_r].interfaces[peer_i].area
                    if peer_area == area_id:
                        warning = f"\nWARNING: Changing Area {area_id} type to {area_type} may break existing adjacencies."
        
        network.area_types[area_id] = area_type
        return f"Area {area_id} type set to: {area_type}" + warning

    # =========================
    # AREA CONFIG
    # =========================

    if tokens[0] == "area":
        if len(tokens) < 4: return "Usage: area <router> <interface> <area_id>"
        
        router = tokens[1]
        intf = tokens[2]
        area = tokens[3]

        if router not in network.routers:
            return "Router not found"

        if intf not in network.routers[router].interfaces:
            return "Interface not found"

        interface = network.routers[router].interfaces[intf]

        interface.area = area

        warning = ""

        # check area mismatch
        if interface.link:

            peer_router, peer_intf = interface.link.split(":")
            peer_interface = network.routers[peer_router].interfaces[peer_intf]

            # 1. Check Area ID mismatch
            if peer_interface.area and peer_interface.area != area:
                warning += (
                    "\nWARNING: OSPF Area ID Mismatch\n"
                    f"{router} {intf} = Area {area}\n"
                    f"{peer_router} {peer_intf} = Area {peer_interface.area}\n"
                )
            
            # 2. Check Area Type mismatch
            my_type = network.area_types.get(area, "normal")
            peer_type = network.area_types.get(peer_interface.area, "normal")
            if peer_interface.area == area and my_type != peer_type:
                warning += (
                    "\nWARNING: OSPF Area Type Mismatch (Adjacency will fail)\n"
                    f"Local (Area {area}): {my_type}\n"
                    f"Peer  (Area {area}): {peer_type}\n"
                )

        return f"Area {area} configured on {router} {intf}" + warning

    # =========================
    # SHOW COMMANDS
    # =========================

    if tokens[0] == "show" and tokens[1] == "ip" and len(tokens) >= 3:
        if tokens[2] == "route" and len(tokens) == 4:
            router = tokens[3]
            return format_routing_table(network, router)
            
        if tokens[2] == "ospf" and len(tokens) >= 4 and tokens[3] == "database":
            return format_lsdb(network)

    if tokens[0] == "show" and tokens[1] == "topology":

        output = "\nCurrent Topology\n"
        output += "================\n"

        for r_name, r in network.routers.items():
            if r.external_domain:
                output += f"\nRouter {r_name} (External: {r.external_domain})\n"
                continue

            areas = set()
            is_asbr = False
            for i in r.interfaces.values():
                if i.area:
                    areas.add(i.area)
                if i.link:
                    peer_r, _ = i.link.split(":")
                    if network.routers[peer_r].external_domain:
                        is_asbr = True

            output += f"\nRouter {r_name}"
            roles = []
            if r.ospf_enabled:
                if len(areas) > 1: roles.append("ABR")
                if is_asbr: roles.append("ASBR")
                if not roles: roles.append("Internal")
                output += f" (OSPF {'/'.join(roles)})"

            output += "\n"

            for i in r.interfaces.values():

                output += f"  {i.name}"

                if i.ip:
                    output += f" {i.ip}"

                if i.area:
                    a_type = network.area_types.get(i.area, "normal")
                    output += f" (Area {i.area} [{a_type}])"

                if i.link:
                    output += f" -> {i.link}"

                output += "\n"

        _draw_topology(network)
        return output

    return "Unknown command"