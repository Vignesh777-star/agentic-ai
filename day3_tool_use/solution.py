"""
Day 3 · SOLUTION — Tool use & structured outputs
================================================
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, client, run_tool_loop
from shared.tools import REGISTRY, ALL_SCHEMAS, dispatch

# ---- Part A ----------------------------------------------------------------
def convert_currency(amount: float, rate: float) -> float:
    return round(amount * rate, 2)

CONVERT_SCHEMA = {
    "name": "convert_currency",
    "description": ("Convert an amount from one currency to another given the "
                    "exchange rate (amount * rate). Use for any currency math; "
                    "do not estimate. Get the rate from a search tool first."),
    "input_schema": {
        "type": "object",
        "properties": {"amount": {"type": "number"}, "rate": {"type": "number"}},
        "required": ["amount", "rate"],
    },
}
REGISTRY["convert_currency"] = convert_currency
TOOLS = ALL_SCHEMAS + [CONVERT_SCHEMA]

# ---- Part B ----------------------------------------------------------------
EXTRACT_SCHEMA = {
    "name": "record_lead",
    "description": "Record structured fields extracted from a sales inquiry.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "company": {"type": "string"},
            "budget_usd": {"type": "number"},
            "missing_fields": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "missing_fields"],
    },
}

def extract(text: str) -> dict:
    resp = client().messages.create(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-5"),
        max_tokens=400,
        tools=[EXTRACT_SCHEMA],
        tool_choice={"type": "tool", "name": "record_lead"},   # force the call
        messages=[{"role": "user", "content": f"Extract fields:\n\n{text}"}],
    )
    return next(b.input for b in resp.content if b.type == "tool_use")


if __name__ == "__main__":
    # Part A: watch the agent choose tools in order.
    print("=== agent with a custom tool ===")
    ans, _ = run_tool_loop(
        messages=[{"role": "user", "content":
            "If the EUR/USD rate is 1.08, what is 4000 euros in dollars? Also what is 15% of that?"}],
        tools=TOOLS, dispatch=lambda n, i: REGISTRY[n](**i),
        system="Use tools; never estimate.",
    )
    print("ANSWER:", ans)

    # Part B: structured extraction.
    print("\n=== structured extraction (forced tool call) ===")
    email = ("Hi, I'm Priya from Acme Retail. We're exploring a rollout and have "
             "roughly $40k earmarked for this year.")
    print(json.dumps(extract(email), indent=2))
