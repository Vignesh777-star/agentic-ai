"""
Day 1 · EXERCISE — Build the agent loop yourself
================================================
An agent is a workflow's more autonomous cousin: an LLM that chooses actions
in a LOOP based on the results it gets back, instead of following a fixed code
path. Your job: implement that loop.

Two ideas from the field you're putting into practice:
  - "Agents are just LLMs using tools in a loop based on environmental feedback."
    (Anthropic, Building Effective Agents)
  - "Own your control flow." The loop is ordinary code you control — prompt,
    switch, context, repeat — not framework magic. (12-Factor Agents)

Fill in the four TODOs. Run it; compare with solution.py when done.

Run:  python day1_agent_loop/exercise.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import call_model, text_of          # thin model wrapper
from shared.tools import ALL_SCHEMAS, dispatch        # calculator, today, search_kb

SYSTEM = ("You are a precise assistant. Use tools rather than guessing. "
          "Look up policy before applying it, and calculate rather than estimate.")


def agent_loop(user_message: str, max_turns: int = 8) -> str:
    messages = [{"role": "user", "content": user_message}]

    for turn in range(max_turns):
        # TODO 1: call the model with `messages`, `system=SYSTEM`, and
        #         `tools=ALL_SCHEMAS`. Store the response in `resp`.
        resp = call_model(messages, system=SYSTEM, tools=ALL_SCHEMAS)

        # TODO 2: if resp.stop_reason is NOT "tool_use", the agent is finished.
        #         Return the final text (hint: text_of(resp)).
        if resp.stop_reason != "tool_use":                             # TODO 2
                    return text_of(resp)
        
        messages.append({"role": "assistant", "content": resp.content})
        

        # The model asked for one or more tools. Record its turn verbatim.
        messages.append({"role": "assistant", "content": resp.content})

        # TODO 3: for each content block whose .type == "tool_use", run it with
        #         dispatch(block.name, block.input) and collect a tool_result dict:
        #         {"type": "tool_result", "tool_use_id": block.id, "content": <json str>}
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
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

        # TODO 4: append the tool results back to `messages` as a user turn,
        #         then let the loop continue.
        messages.append({"role": "user", "content": tool_results})

    return "Stopped: reached max_turns."


if __name__ == "__main__":
    task = ("A customer bought a $1,200 item. Check our refund policy, then if "
            "refunds are allowed compute a 15% restocking fee on $1,200 and give "
            "me the final refund amount.")
    print("TASK:", task, "\n")
    print("ANSWER:", agent_loop(task))
