"""
Day 4 · EXERCISE — Orchestrator-workers (multi-agent) + plan-as-JSON
===================================================================
Two field-standard ideas combined:
  - PLANNING: have the model emit a structured plan (JSON), then execute it
    step by step. Structured plans are inspectable and adaptable.
  - ORCHESTRATOR-WORKERS (Anthropic): a central LLM breaks a task into subtasks,
    delegates each to a focused worker, and synthesizes the results. Small,
    focused agents beat one monolith (12-Factor Agents, factor 10).

The trick that makes composition work: a worker agent is exposed to the
orchestrator AS A TOOL. Routing is just tool selection, one level up.

Implement the plan step and wire the workers as tools. Compare to solution.py.

Run:  python day4_planning_multiagent/orchestrator_exercise.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of, run_tool_loop
from shared.tools import CALCULATOR_SCHEMA, SEARCH_KB_SCHEMA, calculator, search_kb


# --- Workers: two focused specialist agents --------------------------------
def finance_worker(task: str) -> str:
    ans, _ = run_tool_loop([{"role": "user", "content": task}],
        tools=[CALCULATOR_SCHEMA], dispatch=lambda n, i: calculator(**i),
        system="You are a finance specialist. Use the calculator for all math.")
    return ans

def policy_worker(task: str) -> str:
    ans, _ = run_tool_loop([{"role": "user", "content": task}],
        tools=[SEARCH_KB_SCHEMA], dispatch=lambda n, i: search_kb(**i),
        system="You are a policy specialist. Answer only from the knowledge base.")
    return ans


def plan(request: str) -> list[dict]:
    """Ask the model for a JSON plan: a list of {worker, task} steps."""
    # TODO 1: prompt the model to return ONLY a JSON array where each item is
    #         {"worker": "finance"|"policy", "task": "<self-contained subtask>"}.
    #         Parse and return it. (Strip ```json fences before json.loads.)
    ...


WORKERS = {"finance": finance_worker, "policy": policy_worker}

def orchestrate(request: str) -> str:
    steps = plan(request)
    print("PLAN:", json.dumps(steps, indent=2))
    results = []
    # TODO 2: run each step by calling the right worker with step["task"];
    #         collect (worker, task, result) into `results`.
    ...
    # Synthesize a final answer from the collected results.
    summary = text_of(call_model([{"role": "user", "content":
        f"Original request: {request}\n\nWorker results:\n{results}\n\n"
        "Write a single customer-ready answer."}], max_tokens=400))
    return summary


if __name__ == "__main__":
    req = ("A customer wants a refund on a $2,400 order. Confirm our refund "
           "policy, then compute a 15% restocking fee and the net refund.")
    print("\nFINAL:\n", orchestrate(req))
