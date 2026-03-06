import json
from LLM import call_typhoon

def build_prompt(data_package):

    return f"""
You are a Network Failure Intelligence Engine.

STRICT RULES:
- Do NOT recompute shortest paths.
- Use ONLY the provided data.
- Do NOT invent topology.

Your task:
Explain what happened during convergence.

Structure:

1) Failure Detection
2) LSA Generation
3) Flooding Impact
4) SPF Result
5) Routing Changes
6) Network Stability Assessment

DATA:
{json.dumps(data_package, indent=2)}
"""

def analyze(data_package):
    prompt = build_prompt(data_package)
    return call_typhoon(prompt)