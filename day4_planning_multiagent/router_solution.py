"""
Day 4 · DEMO — Routing (Anthropic workflow pattern)
===================================================
Routing = classify the input, then send it to a specialized handler. It's the
cheapest multi-path pattern and often all you need: no loop, no orchestrator,
just "figure out the category, then use the right prompt/tool for it."

When to use it: distinct input types that each deserve different handling
(billing vs. technical vs. sales), where a single do-everything prompt would be
mediocre at all of them.

Run:  python day4_planning_multiagent/router_solution.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of

ROUTES = {
    "billing":   "You are a billing specialist. Be precise about charges and refunds.",
    "technical": "You are a technical support engineer. Give clear step-by-step fixes.",
    "sales":     "You are a friendly sales rep. Focus on fit and next steps.",
}

def classify(message: str) -> str:
    resp = call_model([{"role": "user", "content":
        f"Classify this message into exactly one of {list(ROUTES)}.\n"
        f"Reply with only the label.\n\nMessage: {message}"}], max_tokens=10)
    label = text_of(resp).strip().lower()
    return label if label in ROUTES else "technical"   # safe default

def handle(message: str) -> str:
    route = classify(message)
    print(f"  routed to: {route}")
    return text_of(call_model([{"role": "user", "content": message}],
                              system=ROUTES[route], max_tokens=250))

if __name__ == "__main__":
    for msg in ["I was charged twice this month, can I get a refund?",
                "The app crashes every time I upload a PDF.",
                "Do you offer volume discounts for 50 seats?"]:
        print("\nMESSAGE:", msg)
        print("REPLY:", handle(msg))
