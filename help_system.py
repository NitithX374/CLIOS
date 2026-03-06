commands = {
    "show": [
        "show topology",
        "show ip interface"
    ],
    "router": [
        "router ospf"
    ],
    "interface": [
        "interface <name>"
    ],
    "ip": [
        "ip address <ip>"
    ],
    "connect": [
        "connect <router1> <intf1> <router2> <intf2>"
    ]
}


def get_help(command=None):

    if command is None:

        output = "Available Commands\n"
        output += "==================\n"

        for cmd in commands:
            output += cmd + "\n"

        return output

    if command in commands:

        output = f"{command} commands\n"
        output += "----------------\n"

        for c in commands[command]:
            output += c + "\n"

        return output

    return "No help available"