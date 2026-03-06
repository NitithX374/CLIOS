from models import Network

network = Network()

current_router = None
current_interface = None


# ==============================
# OSPF ENGINE
# ==============================

def same_subnet(ip1, ip2):
    net1 = ip1.split("/")[0].rsplit(".", 1)[0]
    net2 = ip2.split("/")[0].rsplit(".", 1)[0]
    return net1 == net2


def detect_ospf_neighbors():

    for r1_name, r1 in network.routers.items():

        if not r1.ospf_enabled:
            continue

        for if_name, iface in r1.interfaces.items():

            if not iface.ip or not iface.connected_to:
                continue

            peer_name, peer_if_name = iface.connected_to
            peer_router = network.routers[peer_name]
            peer_iface = peer_router.interfaces[peer_if_name]

            if not peer_router.ospf_enabled:
                continue

            if not peer_iface.ip:
                continue

            if same_subnet(iface.ip, peer_iface.ip):

                r1.ospf_neighbors[peer_name] = {
                    "state": "FULL",
                    "interface": if_name
                }


def show_ospf_neighbors():

    if not current_router.ospf_neighbors:
        return "No OSPF neighbors"

    output = "Neighbor ID     State     Interface\n"

    for nbr, data in current_router.ospf_neighbors.items():
        output += f"{nbr}        {data['state']}     {data['interface']}\n"

    return output


# ==============================
# TOPOLOGY VIEW
# ==============================

def show_topology():

    output = "\n===== Network Topology =====\n"

    for r_name, router in network.routers.items():
        output += f"\nRouter {r_name}\n"

        if not router.interfaces:
            output += "  No interfaces configured\n"
            continue

        for if_name, iface in router.interfaces.items():

            ip = iface.ip if iface.ip else "No IP"

            if iface.connected_to:
                peer_router, peer_if = iface.connected_to
                link = f"{peer_router}:{peer_if}"
            else:
                link = "Not connected"

            output += f"  {if_name} | IP: {ip} | Connected to: {link}\n"

    output += "\n============================\n"

    return output


# ==============================
# CLI ENGINE
# ==============================

def process_command(cmd):

    global current_router, current_interface

    tokens = cmd.split()

    if not tokens:
        return ""

    # ---- SHOW ----
    if cmd.strip() == "show topology":
        return show_topology()

    if cmd.strip() == "show ip ospf neighbor" and current_router:
        return show_ospf_neighbors()

    # ---- ENABLE OSPF ----
    if cmd.strip() == "enable ospf" and current_router:
        current_router.ospf_enabled = True
        detect_ospf_neighbors()
        return f"OSPF enabled on {current_router.name}"

    # ---- CREATE ROUTER ----
    if tokens[0] == "create" and tokens[1] == "router":
        network.add_router(tokens[2])
        return f"Router {tokens[2]} created."

    # ---- CONNECT ----
    if tokens[0] == "connect":
        r1, i1, r2, i2 = tokens[1], tokens[2], tokens[3], tokens[4]
        network.connect(r1, i1, r2, i2)
        return f"{r1}:{i1} connected to {r2}:{i2}"

    # ---- USE ROUTER ----
    if tokens[0] == "use":
        current_router = network.routers.get(tokens[1])
        return f"Entering {tokens[1]}"

    # ---- INTERFACE ----
    if tokens[0] == "interface" and current_router:
        current_router.add_interface(tokens[1])
        current_interface = current_router.interfaces[tokens[1]]
        return f"Interface {tokens[1]} selected"

    # ---- IP ADDRESS ----
    if tokens[0] == "ip" and tokens[1] == "address":
        if current_interface is None:
            return "No interface selected"
        current_interface.ip = tokens[2]
        return f"IP {tokens[2]} assigned"

    return "Unknown command"