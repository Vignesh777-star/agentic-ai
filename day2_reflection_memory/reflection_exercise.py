"""
Day 2 · EXERCISE — Reflection (the evaluator-optimizer loop)
===========================================================
Reflection = generate -> critique -> revise, repeated until good enough. In the
literature this is Anthropic's "evaluator-optimizer" workflow: one LLM produces
output, another evaluates it against criteria, and feedback drives revision.

Key lesson from the field: a critic that scores SPECIFIC yes/no criteria beats a
vague "rate this 1-10" judge. So your rubric matters more than your model.

Implement generate(), critique(), and the loop in reflect(). Compare to solution.py.

Run:  python day2_reflection_memory/reflection_exercise.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of

RUBRIC = [
    "Has a clear hook in the first sentence",
    "States exactly one concrete benefit",
    "Is under 60 words",
    "Ends with a call to action",
]


def generate(task: str, feedback: str | None = None) -> str:
    """Produce a draft. If feedback is given, use it to improve."""
    # TODO 1: build a prompt that asks for a product announcement for `task`.
    #         If `feedback` is not None, include it and ask for a revision.
    prompt = ...
    return text_of(call_model([{"role": "user", "content": prompt}], max_tokens=300))


def critique(draft: str) -> tuple[bool, str]:
    """Score the draft against RUBRIC. Return (passes_all, feedback_text)."""
    # TODO 2: ask the model to check EACH rubric item yes/no and list failures.
    #         Return (True, "") if all pass; else (False, <the failures>).
    ...


def reflect(task: str, max_rounds: int = 3) -> str:
    draft = generate(task)
    for r in range(max_rounds):
        ok, feedback = critique(draft)
        print(f"round {r+1}: {'PASS' if ok else 'revise'} — {feedback[:80]}")
        # TODO 3: if ok, stop and return the draft. Otherwise regenerate using feedback.
        ...
    return draft


if __name__ == "__main__":
    print("\nFINAL:\n", reflect("a smart water bottle that tracks hydration"))
