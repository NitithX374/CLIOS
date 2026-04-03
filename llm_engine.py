import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def call_typhoon(prompt):

    client = OpenAI(
        api_key=os.getenv("TYPHOON_API_KEY"),
        base_url="https://api.opentyphoon.ai/v1"
    )

    response = client.chat.completions.create(
        model="typhoon-v2.5-30b-a3b-instruct",
        messages=[
            {
                "role": "system",
                "content": """You are an expert network engineer specializing in all routing protocols and networking standards (including OSPF, TCP, UDP, IP, RIP, EIGRP, ICMP, and ARP).

                You analyze network topologies and explain routing behavior using:
                - The provided network topology
                - Reference knowledge retrieved from RFC documents
                - If there are no topology information, use the RFC knowledge to answer the question DO NOT MAKE UP TOPOLOGY INFORMATION.
                - If the retrieved knowledge have topology in it, say that the topology is from the RFC document and use it to answer the question.

                Rules:
                - Assume any questions regarding the provided network topology are explicitly OSPF-related, unless the user query specifies a different protocol.
                - Always use the given topology when reasoning.
                - Use RFC knowledge when relevant.
                - Do NOT invent routers or links that are not in the topology.
                - If information is missing, say so instead of guessing.
                - Output format: Use ONLY PLAIN TEXT. Do NOT use any Markdown (no bold, no italics, no tables, no lists with * or -) and do NOT use HTML tags. You are permitted and encouraged to use emojis (emotes) to make the text friendly for a CLI.
                
                When evaluating network robustness or single points of failure:
                - Explicitly identify bottlenecks, single links, or routers that could cause network partitioning if they fail.
                - Recommend specific redundant links or topology changes (e.g., connecting specific routers) to improve fault tolerance."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=3000
    )

    return response.choices[0].message.content

def call_typhoon_agent(prompt):

    client = OpenAI(
        api_key=os.getenv("TYPHOON_API_KEY"),
        base_url="https://api.opentyphoon.ai/v1"
    )

    system_prompt = """You are an AI network assistant. Ensure to translate the user's natural language request into a sequence of topology CLI commands.
Available commands:
router <name>
no router <name>
interface <router> <name>
ip address <router> <intf> <ip/subnet>
connect <r1> <i1> <r2> <i2>
ospf enable <router>
area <router> <interface> <area_id>
areatype <id> <stub|totally-stub|nssa|normal>
external <router> <domain>

Rules:
- Give ONE command per line.
- DO NOT use markdown blocks like ``` or ```bash.
- DO NOT provide explanations, ONLY the CLI commands.
- Assume basic IP addressing (e.g., 192.168.1.0/24) if not specified.
- Automatically construct interfaces (e.g., e0, e1) and connect them as requested.
- If OSPF is requested on a router, use 'ospf enable <router>' and assign the correct 'area <router> <intf> <area_id>'.
- For area types, use stub, totally-stub, nssa, or normal.
"""

    response = client.chat.completions.create(
        model="typhoon-v2.5-30b-a3b-instruct",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=2000
    )

    return response.choices[0].message.content