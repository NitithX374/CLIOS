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

    if tokens[0] == "show" and tokens[1] == "topology":

        output = "\nCurrent Topology\n"
        output += "================\n"

        for r_name, r in network.routers.items():

            output += f"\nRouter {r_name}"

            if r.ospf_enabled:
                output += " (OSPF)"

            output += "\n"

            for i in r.interfaces.values():

                output += f"  {i.name}"

                if i.ip:
                    output += f" {i.ip}"

                if i.link:
                    output += f" -> {i.link}"

                output += "\n"

        return output

    return "Unknown command"