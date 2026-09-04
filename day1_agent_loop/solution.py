"""
Day 1 · SOLUTION — the agent loop
=================================
The whole of "agentic" fits in ~15 lines. Everything else in this course is
elaboration on this loop. Read it until it feels obvious.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of
from shared.tools import ALL_SCHEMAS, dispatch

SYSTEM = ("You are a precise assistant. Use tools rather than guessing. "
          "Look up policy before applying it, and calculate rather than estimate.")


def agent_loop(user_message: str, max_turns: int = 8) -> str:
    messages = [{"role": "user", "content": user_message}]

    for turn in range(max_turns):
        resp = call_model(messages, system=SYSTEM, tools=ALL_SCHEMAS)   # TODO 1

        if resp.stop_reason != "tool_use":                             # TODO 2
            return text_of(resp)

        messages.append({"role": "assistant", "content": resp.content})

        tool_results = []                                              # TODO 3
        for block in resp.content:
            if block.type == "tool_use":
                print(f"  → {block.name}({block.input})")
                result = dispatch(block.name, block.input)
                print(f"  ← {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

        messages.append({"role": "user", "content": tool_results})     # TODO 4

    return "Stopped: reached max_turns."


if __name__ == "__main__":
    task = ("A customer bought a $1,200 item. Check our refund policy, then if "
            "refunds are allowed compute a 15% restocking fee on $1,200 and give "
            "me the final refund amount.")
    print("TASK:", task, "\n")
    print("\nANSWER:", agent_loop(task))
