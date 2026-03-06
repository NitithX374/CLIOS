from rag.retriever import retrieve
from cli_engine import process_command
from network_state import network
from llm_engine import call_typhoon

mode = "topology"
DEBUG_RAG = False

def is_cli_command(text):
    cli_keywords = ["show", "config", "router", "interface", "?", "ip", "connect", "ospf"]
    return any(text.strip().startswith(k) for k in cli_keywords)


def export_topology():

    output = "NETWORK TOPOLOGY\n"

    for r_name, router in network.routers.items():

        output += f"\nRouter: {r_name}\n"

        if router.ospf_enabled:
            output += "OSPF: enabled\n"
        else:
            output += "OSPF: disabled\n"

        for intf in router.interfaces.values():

            output += f"Interface: {intf.name}\n"

            if intf.ip:
                output += f"IP: {intf.ip}\n"

            if intf.link:
                output += f"Link: {intf.link}\n"

        output += "\n"

    return output


if __name__ == "__main__":

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