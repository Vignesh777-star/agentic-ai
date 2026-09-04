"""
Day 2 · SOLUTION — Reflection / evaluator-optimizer
===================================================
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of

RUBRIC = [
    "Has a clear hook in the first sentence",
    "States exactly one concrete benefit",
    "Is under 60 words",
    "Ends with a call to action",
]


def generate(task: str, feedback: str | None = None) -> str:
    prompt = f"Write a short product announcement for: {task}."
    if feedback:
        prompt += f"\n\nRevise to fix these problems:\n{feedback}"
    return text_of(call_model([{"role": "user", "content": prompt}], max_tokens=300))


def critique(draft: str) -> tuple[bool, str]:
    checklist = "\n".join(f"- {c}" for c in RUBRIC)
    resp = call_model([{"role": "user", "content":
        f"DRAFT:\n{draft}\n\nCheck each criterion yes/no and list only the ones "
        f"it FAILS (empty if none):\n{checklist}"}], max_tokens=200)
    feedback = text_of(resp)
    # Heuristic: if the model lists no failing bullet, treat as pass.
    passes = ("- " not in feedback) or ("none" in feedback.lower()[:30])
    return passes, feedback


def reflect(task: str, max_rounds: int = 3) -> str:
    draft = generate(task)
    for r in range(max_rounds):
        ok, feedback = critique(draft)
        print(f"round {r+1}: {'PASS' if ok else 'revise'} — {feedback[:80]}")
        if ok:
            return draft
        draft = generate(task, feedback)
    return draft


if __name__ == "__main__":
    print("\nFINAL:\n", reflect("a smart water bottle that tracks hydration"))
