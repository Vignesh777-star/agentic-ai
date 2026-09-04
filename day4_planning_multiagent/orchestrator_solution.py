"""
Day 4 · SOLUTION — Orchestrator-workers + plan-as-JSON
======================================================
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of, run_tool_loop
from shared.tools import CALCULATOR_SCHEMA, SEARCH_KB_SCHEMA, calculator, search_kb


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

WORKERS = {"finance": finance_worker, "policy": policy_worker}


def plan(request: str) -> list[dict]:
    resp = call_model([{"role": "user", "content":
        f"Break this request into subtasks for specialist workers.\n"
        f"Request: {request}\n\n"
        'Return ONLY a JSON array; each item {"worker":"finance"|"policy",'
        '"task":"<self-contained subtask>"}. Order matters (policy before math).'}],
        max_tokens=400)
    raw = text_of(resp).replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def orchestrate(request: str) -> str:
    steps = plan(request)
    print("PLAN:", json.dumps(steps, indent=2))
    results = []
    for step in steps:
        worker = WORKERS[step["worker"]]
        print(f"  → {step['worker']}: {step['task'][:60]}...")
        out = worker(step["task"])
        results.append({"worker": step["worker"], "task": step["task"], "result": out})
    summary = text_of(call_model([{"role": "user", "content":
        f"Original request: {request}\n\nWorker results:\n{json.dumps(results, indent=2)}\n\n"
        "Write a single customer-ready answer."}], max_tokens=400))
    return summary


if __name__ == "__main__":
    req = ("A customer wants a refund on a $2,400 order. Confirm our refund "
           "policy, then compute a 15% restocking fee and the net refund.")
    print("\nFINAL:\n", orchestrate(req))
