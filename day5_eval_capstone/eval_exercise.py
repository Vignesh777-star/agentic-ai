"""
Day 5 · EXERCISE — Evaluation-driven development
================================================
The single biggest predictor of whether a team ships good agents is whether they
run a disciplined eval + error-analysis process. Prompt-tweaking without evals
hits a ceiling you can't see.

Two kinds of checks:
  - OBJECTIVE (code-based): exact, cheap, reliable. Prefer these. (Does the
    output contain the right number? Valid JSON? The required fact?)
  - SUBJECTIVE (LLM-as-judge): for quality you can't code — scored against a
    rubric, not a vibe.

Build the eval runner. Compare to solution.py.

Run:  python day5_eval_capstone/eval_exercise.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import run_tool_loop, call_model, text_of
from shared.tools import ALL_SCHEMAS, dispatch


def agent(msg: str) -> str:
    ans, _ = run_tool_loop([{"role": "user", "content": msg}],
        tools=ALL_SCHEMAS, dispatch=dispatch,
        system="You are a precise assistant. Use tools rather than guessing.")
    return ans


# An eval set grows every time you find a bug: each incident becomes a test.
CASES = [
    {"id": "math",   "input": "What is 1200 * 0.15?",        "kind": "objective",
     "check": lambda out: "180" in out},
    {"id": "policy", "input": "What is our refund window?",  "kind": "objective",
     "check": lambda out: "30 days" in out.lower()},
    {"id": "tone",   "input": "Explain our SLA to a non-technical customer.",
     "kind": "judge", "rubric": "Accurate (99.9% uptime, 1-hour P1) AND simple wording."},
]


def llm_judge(question: str, answer: str, rubric: str) -> bool:
    r = call_model([{"role": "user", "content":
        f"Q: {question}\nA: {answer}\nRUBRIC: {rubric}\n"
        "Does A satisfy the rubric? Reply PASS or FAIL then a reason."}], max_tokens=80)
    return text_of(r).upper().startswith("PASS")


def run_evals() -> None:
    print("=" * 41)
    print("          AGENT EVALUATION")
    print("=" * 41)
    print()

    passed = 0
    for c in CASES:
        print(f"Running: {c['id']}...")
        out = agent(c["input"])
        if c["kind"] == "objective":
            ok = c["check"](out)
        else:
            ok = llm_judge(c["input"], out, c["rubric"])
        print(f"[{'PASS' if ok else 'FAIL'}] {c['id']} ({c['kind']})")
        passed += ok

    print()
    print("=" * 41)
    print(f"Score: {passed}/{len(CASES)}")
    print("=" * 41)


if __name__ == "__main__":
    run_evals()
