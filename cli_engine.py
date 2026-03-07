from network_state import network

def process_command(cmd):

    tokens = cmd.split()

    if not tokens:
        return ""

    if tokens[0] == "?":
        return """
Available commands:

router <name>
interface <router> <name>
ip address <router> <intf> <ip/subnet>
connect <r1> <i1> <r2> <i2>
ospf enable <router>
area <router> <interface> <area_id>
show topology
"""

    if tokens[0] == "router":

        name = tokens[1]
        network.add_router(name)
        return f"Router {name} created"

    if tokens[0] == "interface":

        router = tokens[1]
        intf = tokens[2]

        network.add_interface(router, intf)

        return f"Interface {intf} created on {router}"

    if tokens[0] == "ip" and tokens[1] == "address":

        router = tokens[2]
        intf = tokens[3]
        ip = tokens[4]

        network.set_ip(router, intf, ip)

        return f"{router} {intf} IP set to {ip}"

    if tokens[0] == "connect":

        r1 = tokens[1]
        i1 = tokens[2]
        r2 = tokens[3]
        i2 = tokens[4]

        network.connect(r1, i1, r2, i2)

        return f"{r1}:{i1} connected to {r2}:{i2}"

    if tokens[0] == "ospf" and tokens[1] == "enable":

        router = tokens[2]

        network.enable_ospf(router)

        return f"OSPF enabled on {router}"

    # =========================
    # AREA CONFIG
    # =========================

    if tokens[0] == "area":

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

            if peer_interface.area and peer_interface.area != area:

                warning = (
                    "\nWARNING: OSPF Area Mismatch Detected\n"
                    f"{router} {intf} = Area {area}\n"
                    f"{peer_router} {peer_intf} = Area {peer_interface.area}\n"
                )

        return f"Area {area} configured on {router} {intf}" + warning

    # =========================
    # SHOW TOPOLOGY
    # =========================

    if tokens[0] == "show" and tokens[1] == "topology":

        output = "\nCurrent Topology\n"
        output += "================\n"

        for r_name, r in network.routers.items():
            area = set()
            for i in r.interfaces.values():
                if i.area:
                    area.add(i.area)

            output += f"\nRouter {r_name}"
            if r.ospf_enabled and len(area) > 1:
                output += " (OSPF ABR)"
            elif r.ospf_enabled:
                output += " (OSPF)"

            output += "\n"

            for i in r.interfaces.values():

                output += f"  {i.name}"

                if i.ip:
                    output += f" {i.ip}"

                if i.area:
                    output += f" (Area {i.area})"

                if i.link:
                    output += f" -> {i.link}"

                output += "\n"

        return output

    return "Unknown command"