from cli_engine import process_command

cmds = [
    "router R1",
    "router R2",
    "router R3",
    "interface R1 eth0",
    "interface R2 eth0",
    "interface R1 eth1",
    "interface R3 eth0",
    "interface R2 eth1",
    "interface R3 eth1",
    "ip address R1 eth0 10.0.12.1",
    "ip address R2 eth0 10.0.12.2",
    "ip address R1 eth1 10.0.13.1",
    "ip address R3 eth0 10.0.13.3",
    "ip address R2 eth1 10.0.23.2",
    "ip address R3 eth1 10.0.23.3",
    "connect R1 eth0 R2 eth0",
    "connect R1 eth1 R3 eth0",
    "connect R2 eth1 R3 eth1",
    "ospf enable R1",
    "ospf enable R2",
    "ospf enable R3",
    "area R1 eth0 0",
    "area R2 eth0 0",
    "area R1 eth1 0",
    "area R3 eth0 0",
    "area R2 eth1 0",
    "area R3 eth1 0",
    "show ip ospf database",
    "show ip route R1",
    "cost R1 eth1 100",
    "show ip route R1"
]

for c in cmds:
    out = process_command(c)
    if out and len(out) > 50:
        print("====== COMMAND:", c)
        print(out)
