from rag.retriever import retrieve
from cli_engine import process_command
from network_state import network
from llm_engine import call_typhoon, call_typhoon_agent

mode = "topology"
DEBUG_RAG = False

def print_banner():

    print("""
   _____ _      _____  ____   _____
  / ____| |    |_   _|/ __ \\ / ____|
 | |    | |      | | | |  | | (___
 | |    | |      | | | |  | |\\___ \\
 | |____| |____ _| |_| |__| |____) |
  \\_____|______|_____|_____/|_____/

C.L.I.O.S. - CLI-based OSPF Simulator
""")

    print("Welcome to C.L.I.O.S. (CLI-based OSPF Simulator)")
    print("-----------------------------------------------------------")
    print("Modes:")
    print("  ask       - Ask AI about OSPF behavior")
    print("  topology  - Build and configure network topology")
    print("  agent     - Build topology using AI based on natural language")
    print("")
    print("Usage:")
    print("  type 'mode topology' to start building a network")
    print("  type 'mode ask' to ask AI questions")
    print("  type 'mode agent' to prompt the AI to build a topology")
    print("")
    print("Tips:")
    print("  In topology mode, type '?' to see available commands")
    print("  type 'q' to exit")
    print("")

def is_question(text):

    text = text.lower().strip()

    question_words = [
        "what", "why", "how", "when", "where",
        "explain", "describe", "does", "do",
        "can", "is", "are" , "if", "tell"
    ]

    if "?" in text:
        return True

    return any(text.startswith(w) for w in question_words)

def is_cli_command(text):
    cli_keywords = ["show", "config", "router", "interface", "?", "ip", "connect", "ospf", "area", "external", "no", "areatype"]
    return any(text.strip().startswith(k) for k in cli_keywords)


def export_topology():

    output = "NETWORK TOPOLOGY\n"
    
    if network.area_types:
        output += "\nArea Configurations:\n"
        for aid, atype in network.area_types.items():
            output += f"- Area {aid}: {atype}\n"

    for r_name, router in network.routers.items():

        if router.external_domain:
            output += f"\nRouter: {r_name}\n"
            output += f"Role: External Domain ({router.external_domain})\n"
        else:
            output += f"\nRouter: {r_name}\n"

            # Detect roles
            areas = set()
            is_asbr = False
            for intf in router.interfaces.values():
                if intf.area:
                    areas.add(intf.area)
                if intf.link:
                    peer_r, _ = intf.link.split(":")
                    if network.routers[peer_r].external_domain:
                        is_asbr = True

            roles = []
            if router.ospf_enabled:
                if len(areas) > 1: roles.append("ABR")
                if is_asbr: roles.append("ASBR")
                if not roles: roles.append("Internal Router")
                output += f"Role: {' & '.join(roles)}\n"
            else:
                output += "Role: OSPF Disabled\n"

        for intf in router.interfaces.values():

            output += f"Interface: {intf.name}\n"

            if intf.ip:
                output += f"IP: {intf.ip}\n"

            if intf.area:
                output += f"Area: {intf.area}\n"

            if intf.link:
                output += f"Link: {intf.link}\n"

        output += "\n"

    return output


if __name__ == "__main__":
    print_banner()
    while True:

        query = input(f"[{mode}]# ")

        if query == "q":
            break

        # =====================
        # SWITCH MODE
        # =====================

        if query == "mode topology":
            mode = "topology"
            print("Entered topology build mode")
            continue

        if query == "mode ask":
            mode = "ask"
            print("Entered LLM query mode")
            continue

        if query == "mode agent":
            mode = "agent"
            print("Entered AI Agent mode")
            continue

        # =====================
        # TOPOLOGY MODE
        # =====================

        if mode == "topology":

            if is_cli_command(query):

                output = process_command(query)
                print(output)

            else:
                print("Invalid topology command")

        # =====================
        # ASK MODE
        # =====================

        elif mode == "ask":
            if not is_question(query):
                print("🙂 You're welcome!")
                continue

            topology = export_topology()

            results = retrieve(query, top_k=3)

            print("\nTopology Context")
            print("================")
            print(topology)

            # print("\nRAG Results")
            # print("================")

            rag_text = ""
            if DEBUG_RAG:
                print(results)
                print("-"*40)
            for r in results:
                if DEBUG_RAG:
                    print(r["text"])
                    print("-"*40)
                rag_text += r["text"] + "\n\n"

            prompt = f"""
Network Topology
================
{topology}

Reference Knowledge
================
{rag_text}

Question
================
{query}

Explain the answer using the topology and the reference knowledge.
"""

            answer = call_typhoon(prompt)

            print("\nLLM Answer")
            print("================")
            print(answer)

        # =====================
        # AGENT MODE
        # =====================

        elif mode == "agent":
            print("Calling AI Agent to generate commands...\n")
            commands_str = call_typhoon_agent(query)
            # Remove any possible markdown artifacts just in case
            commands_str = commands_str.replace("```bash", "").replace("```", "").strip()
            commands = [cmd.strip() for cmd in commands_str.split("\n") if cmd.strip()]
            
            print("Executing commands:")
            for cmd in commands:
                print(f"> {cmd}")
                output = process_command(cmd)
                if output:
                    print(output)
            print("Agent execution complete.\n")