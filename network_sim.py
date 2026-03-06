from topology_cli import process_command

while True:
    cmd = input("> ")

    if cmd == "q":
        break

    print(process_command(cmd))