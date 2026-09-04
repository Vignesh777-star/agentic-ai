"""
Day 2 · DEMO — Memory is context engineering
============================================
Models are stateless functions: input context -> output. "Memory" is entirely
what YOU choose to put back into the context window. This is the heart of the
12-Factor "own your context window" principle — context is the new memory.

Three patterns you'll use forever:
  1. Buffer   — keep recent turns verbatim (simple; grows unbounded).
  2. Summary  — compress old turns into a rolling summary (bounded context).
  3. Retrieval— store facts externally, recall only the relevant ones (long-term).

This demo shows all three so you can feel the trade-offs.

Run:  python day2_reflection_memory/memory_solution.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of


class SummaryMemory:
    """Fold old turns into a running summary once past a recent budget."""
    def __init__(self, keep_recent=2):
        self.summary = ""
        self.recent = []
        self.keep = keep_recent

    def add(self, role, content):
        self.recent.append({"role": role, "content": content})
        if len(self.recent) > self.keep * 2:
            old, self.recent = self.recent[:-self.keep*2], self.recent[-self.keep*2:]
            joined = "\n".join(f"{t['role']}: {t['content']}" for t in old)
            self.summary = text_of(call_model([{"role": "user", "content":
                f"Prior summary: {self.summary or '(none)'}\nFold in:\n{joined}\n"
                "Return an updated concise summary."}], max_tokens=200))

    def context(self):
        pre = [{"role": "user", "content": f"[Summary: {self.summary}]"}] if self.summary else []
        return pre + self.recent


class RetrievalMemory:
    """Long-term store. Real systems embed + vector-search; here: keyword overlap."""
    def __init__(self): self.facts = []
    def remember(self, fact): self.facts.append(fact)
    def recall(self, query, k=2):
        qw = set(query.lower().split())
        ranked = sorted(self.facts, key=lambda f: len(qw & set(f.lower().split())), reverse=True)
        return [f for f in ranked if qw & set(f.lower().split())][:k]


if __name__ == "__main__":
    ltm = RetrievalMemory()
    for f in ["Dana prefers email over phone.",
              "Dana's account tier is Enterprise with a 99.9% uptime SLA.",
              "Dana had a billing dispute in March resolved with a credit."]:
        ltm.remember(f)
    q = "What SLA does Dana have?"
    hits = ltm.recall(q)
    print("recalled:", hits)
    print("answer:", text_of(call_model([{"role": "user", "content":
        f"Using only: {hits}\nAnswer: {q}"}], max_tokens=80)))
