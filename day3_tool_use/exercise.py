"""
Day 3 · EXERCISE — Tool use & "tools are structured outputs"
===========================================================
The core lesson (12-Factor Agents, factor 4): a "tool" is nothing magic. It's a
schema the model fills in — structured JSON output — that your code then runs.
The model DECIDES; your code EXECUTES. That separation is where safety lives.

Two parts:
  A) Define a NEW tool (schema + function) and register it.
  B) Force structured extraction by making the model call a tool.

Fill the TODOs. Compare to solution.py.

Run:  python day3_tool_use/exercise.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, client
from shared.tools import REGISTRY, ALL_SCHEMAS

# ---- Part A: add a currency-conversion tool -------------------------------
def convert_currency(amount: float, rate: float) -> float:
    return round(amount * rate, 2)

# TODO 1: write the schema for convert_currency. The description is the model's
#         ENTIRE manual for the tool — be precise about what it does and its args.
CONVERT_SCHEMA = {
    "name": "convert_currency",
    "description": ...,
    "input_schema": {
        "type": "object",
        "properties": {
            "amount": {"type": "number"},
            "rate": {"type": "number"},
        },
        "required": ["amount", "rate"],
    },
}

# TODO 2: register the function and add its schema so the agent can pick it.
REGISTRY["convert_currency"] = ...
TOOLS = ALL_SCHEMAS + [...]


# ---- Part B: structured extraction via forced tool call -------------------
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
    # TODO 3: call the model with tool_choice forcing "record_lead", then return
    #         the tool_use block's .input (the structured data).
    ...


if __name__ == "__main__":
    email = ("Hi, I'm Priya from Acme Retail. We're exploring a rollout and have "
             "roughly $40k earmarked for this year.")
    print(json.dumps(extract(email), indent=2))
