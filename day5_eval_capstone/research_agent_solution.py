"""
Day 5 · CAPSTONE — The deep-research agent
==========================================
This composes everything from the week into the archetypal agentic app:

    plan -> search -> (fetch) -> synthesize & rank -> outline -> edit -> report
                     ^________ loop back if gaps remain ________|

Patterns used:
  - Planning: the agent first drafts research questions (plan-as-data).
  - Tool use: `search` is a tool the agent calls and re-calls with better queries.
  - Reflection: the final edit pass critiques and tightens the draft.
  - Evaluation mindset: a grounding check verifies claims against sources.

The `search` tool here uses a small offline corpus so the capstone runs with no
web key. To go live, replace `search()` with a call to Tavily/Serper/Brave and
`fetch()` with a real HTTP GET — the rest of the agent is unchanged.

Run:  python day5_eval_capstone/research_agent_solution.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of, run_tool_loop

# ---- Swap these two functions for real web tools to go live ----------------
_CORPUS = {
    "d1": "Small language models (SLMs) under ~4B params now rival older large "
          "models on narrow tasks while running on a single GPU or CPU.",
    "d2": "Quantization (e.g. 4-bit) cuts SLM memory ~4x with minor quality loss, "
          "enabling on-device and air-gapped deployment.",
    "d3": "LoRA fine-tuning adapts SLMs cheaply by training small adapter matrices "
          "instead of full weights, often in under an hour on consumer GPUs.",
    "d4": "RAG pairs an SLM with a retriever so it can answer over private data "
          "without baking that data into the weights.",
}

def search(query: str, k: int = 2) -> list[dict]:
    qw = set(query.lower().split())
    scored = sorted(_CORPUS.items(),
                    key=lambda kv: len(qw & set(kv[1].lower().split())), reverse=True)
    return [{"id": i, "text": t} for i, t in scored[:k]
            if qw & set(t.lower().split())]

# ---- Tool schema the research agent calls ----------------------------------
SEARCH_TOOL = {
    "name": "search",
    "description": ("Search the research corpus for passages relevant to a query. "
                    "Returns passages with ids. Call multiple times with refined "
                    "queries to cover all sub-questions before writing."),
    "input_schema": {"type": "object",
                     "properties": {"query": {"type": "string"}}, "required": ["query"]},
}
_seen: list[str] = []

def dispatch(name, tool_input):
    hits = search(tool_input["query"])
    _seen.extend(h["text"] for h in hits)
    return [{"id": h["id"], "text": h["text"]} for h in hits]


RESEARCH_SYSTEM = (
    "You are a research agent. First list 2-3 sub-questions for the topic. "
    "Use the search tool to gather evidence for each (search again with better "
    "queries if results are thin). Then write a concise, well-structured Markdown "
    "brief with a short intro, 2-3 sections, and a closing takeaway. Ground every "
    "claim in retrieved passages and cite ids like [d2]. Do not invent facts.")


def grounding_check(report: str, evidence: list[str]) -> str:
    r = call_model([{"role": "user", "content":
        "EVIDENCE:\n" + "\n".join(f"- {e}" for e in evidence) +
        f"\n\nREPORT:\n{report}\n\nAre all factual claims supported by the evidence? "
        "Reply SUPPORTED or UNSUPPORTED then one sentence."}], max_tokens=120)
    return text_of(r)


def research(topic: str) -> str:
    _seen.clear()
    report, _ = run_tool_loop(
        messages=[{"role": "user", "content": f"Research topic: {topic}"}],
        tools=[SEARCH_TOOL], dispatch=dispatch, system=RESEARCH_SYSTEM,
        max_turns=10,
        on_step=lambda k, p: print(f"  search: {p['input']['query']}")
                              if k == "tool_call" else None,
    )
    return report


if __name__ == "__main__":
    topic = "Why small language models are useful for private, on-device AI"
    print("TOPIC:", topic, "\n")
    report = research(topic)
    print("\n===== REPORT =====\n", report)
    print("\n===== GROUNDING =====\n", grounding_check(report, _seen))
