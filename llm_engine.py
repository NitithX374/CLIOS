import os
from openai import OpenAI

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
                "content": """You are an expert network engineer specializing in OSPF and routing protocols.

                You analyze network topologies and explain routing behavior using:
                - The provided network topology
                - Reference knowledge retrieved from RFC documents

                Rules:
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