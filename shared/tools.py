"""
shared/tools.py
===============
A small library of *real* tools the agents in this course can call, plus their
Anthropic-format schemas. Keeping tools here (not inline) teaches an important
production habit: tools are a versioned, testable, reusable surface — not
throwaway lambdas.

A "tool" is two things bolted together:
  1. A JSON *schema* the model reads to decide when/how to call it.
  2. A plain Python *function* your harness runs when the model asks.

The model never runs your code. It only emits a request; YOUR loop executes it.
That gap is where all of your safety and permissioning lives.
"""

from __future__ import annotations
import math
import datetime as dt


# --- 1. The implementations (ordinary, unit-testable Python) ---------------

def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression. Safe-ish eval with no builtins."""
    allowed = {k: getattr(math, k) for k in ("sqrt", "log", "exp", "pow")}
    return eval(expression, {"__builtins__": {}}, allowed)  # noqa: S307 (demo)


def today(_: str = "") -> str:
    """Return today's date in ISO format."""
    return dt.date.today().isoformat()


# A stand-in "knowledge base" so the course runs fully offline. In real life
# this is a vector store / SQL DB / API. The interface is what matters.
_FAKE_KB = {
    "refund policy": "Refunds are issued within 30 days of purchase with a receipt.",
    "sla": "Enterprise SLA guarantees 99.9% uptime and 1-hour P1 response.",
    "data retention": "Customer data is retained for 7 years per regulatory requirement.",
}


def search_kb(query: str) -> str:
    """Naive keyword lookup against a tiny internal knowledge base."""
    q = query.lower()
    hits = [v for k, v in _FAKE_KB.items() if any(w in k for w in q.split())]
    return " ".join(hits) if hits else "No matching policy found."


# --- 2. The schemas (what the model sees) ----------------------------------
# input_schema is standard JSON Schema. Be *precise* in descriptions: the
# description is the model's entire user manual for the tool. Vague descriptions
# are the #1 cause of wrong tool calls.

CALCULATOR_SCHEMA = {
    "name": "calculator",
    "description": (
        "Evaluate a single arithmetic expression and return the number. "
        "Use for any math you would otherwise do in your head — do NOT guess. "
        "Supports + - * / ** and sqrt(), log(), exp(), pow()."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "e.g. '(1200 * 0.045) / 12'"}
        },
        "required": ["expression"],
    },
}

TODAY_SCHEMA = {
    "name": "today",
    "description": "Get today's date in ISO (YYYY-MM-DD). Use when you need the current date.",
    "input_schema": {"type": "object", "properties": {}},
}

SEARCH_KB_SCHEMA = {
    "name": "search_kb",
    "description": (
        "Search the internal company knowledge base for policy information "
        "(refunds, SLA, data retention). Returns the relevant policy text or "
        "a not-found message. Prefer this over answering policy questions from memory."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to look up"}},
        "required": ["query"],
    },
}


# --- 3. A registry so a harness can dispatch by name -----------------------

REGISTRY = {
    "calculator": calculator,
    "today": today,
    "search_kb": search_kb,
}

ALL_SCHEMAS = [CALCULATOR_SCHEMA, TODAY_SCHEMA, SEARCH_KB_SCHEMA]


def dispatch(name: str, tool_input: dict):
    """Look up a tool by name and call it with keyword args from the model."""
    if name not in REGISTRY:
        raise KeyError(f"Unknown tool: {name}")
    return REGISTRY[name](**tool_input)
