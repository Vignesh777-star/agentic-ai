"""
shared/llm.py  —  OPENROUTER backend (drop-in replacement)
==========================================================
Same public interface the labs use (call_model, text_of, run_tool_loop,
client) but it routes through OpenRouter, a single OpenAI-compatible gateway to
hundreds of models (many free). Every exercise and solution keeps working
UNCHANGED: this module translates the Anthropic-style messages/tools the labs
produce into the OpenAI Chat Completions format OpenRouter speaks, and back.

SETUP
-----
    pip install -U openai python-dotenv
    set  OPENROUTER_API_KEY   (from https://openrouter.ai/keys)

MODEL
-----
Defaults to "openrouter/free" — OpenRouter's auto-router that picks a FREE model
matching your request's needs (including tool calling), so the labs keep working
even as individual free models rotate out. To pin a specific model instead:

    set OPENROUTER_MODEL=meta-llama/llama-4-maverick:free      # a specific free model
    set OPENROUTER_MODEL=openai/gpt-4o-mini                    # a cheap paid model

If the tool-using labs (Day 3+) misbehave on free models, pin a model that
lists "Tools" support on https://openrouter.ai/models (a cheap paid one is the
most reliable). List what your key can call:

    python -c "from openai import OpenAI; import os; \
    c=OpenAI(api_key=os.environ['OPENROUTER_API_KEY'], base_url='https://openrouter.ai/api/v1'); \
    print([m.id for m in c.models.list().data][:40])"

NOTE: the free tier is rate-limited (~20 requests/min, ~200/day). A single lab
run makes only a handful of calls; if you hit a 429, wait a moment and rerun.
"""

from __future__ import annotations
import os, json, uuid
from typing import Any, Callable

# Optional .env loading.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
ESCALATION_MODEL = os.environ.get("OPENROUTER_ESCALATION_MODEL", "openai/gpt-4o-mini")

# Optional OpenRouter ranking headers (harmless; identify your app).
_HEADERS = {
    "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost"),
    "X-Title": os.environ.get("OPENROUTER_TITLE", "agentic-ai-labs"),
}

_client_obj = None
def _or_client():
    global _client_obj
    if OpenAI is None:
        raise RuntimeError("Run: pip install -U openai")
    if _client_obj is None:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("Set OPENROUTER_API_KEY (get one at https://openrouter.ai/keys)")
        _client_obj = OpenAI(api_key=key, base_url=BASE_URL, default_headers=_HEADERS)
    return _client_obj


# --- Anthropic-shaped response objects the labs already know how to read ------
class _Block:
    def __init__(self, **kw): self.__dict__.update(kw)

class _Response:
    def __init__(self, content, stop_reason):
        self.content = content            # list of _Block
        self.stop_reason = stop_reason    # "tool_use" or "end_turn"

def _bget(b, key):
    return b[key] if isinstance(b, dict) else getattr(b, key, None)


# --- tool translation: Anthropic -> OpenAI (OpenRouter accepts JSON schema) ---
def _tools_to_openai(tools: list[dict]):
    return [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
        },
    } for t in tools]


# --- message translation: Anthropic messages -> OpenAI messages --------------
def _messages_to_openai(messages: list[dict], system: str | None):
    out = []
    if system:
        out.append({"role": "system", "content": system})
    for m in messages:
        role, c = m["role"], m["content"]
        if isinstance(c, str):
            out.append({"role": role, "content": c})
            continue
        if role == "assistant":
            texts, tool_calls = [], []
            for b in c:
                bt = _bget(b, "type")
                if bt == "text":
                    texts.append(_bget(b, "text"))
                elif bt == "tool_use":
                    tool_calls.append({
                        "id": _bget(b, "id"),
                        "type": "function",
                        "function": {"name": _bget(b, "name"),
                                     "arguments": json.dumps(_bget(b, "input") or {})},
                    })
            msg = {"role": "assistant", "content": ("".join(texts) or None)}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
        else:  # user turn: tool_result blocks become OpenAI "tool" messages
            for b in c:
                bt = _bget(b, "type")
                if bt == "tool_result":
                    val = _bget(b, "content")
                    out.append({"role": "tool", "tool_call_id": _bget(b, "tool_use_id"),
                                "content": val if isinstance(val, str) else json.dumps(val)})
                elif bt == "text":
                    out.append({"role": "user", "content": _bget(b, "text")})
    return out


def _to_anthropic_response(resp) -> _Response:
    msg = resp.choices[0].message
    blocks, stop = [], "end_turn"
    if msg.content:
        blocks.append(_Block(type="text", text=msg.content))
    for tc in (getattr(msg, "tool_calls", None) or []):
        try:
            args = json.loads(tc.function.arguments or "{}")
        except Exception:
            args = {}
        blocks.append(_Block(type="tool_use", id=tc.id or ("call_" + uuid.uuid4().hex[:12]),
                             name=tc.function.name, input=args))
        stop = "tool_use"
    if not blocks:
        blocks.append(_Block(type="text", text=""))
    return _Response(blocks, stop)


# --- Anthropic-compatible client shim the labs call --------------------------
class _Messages:
    def create(self, model=None, max_tokens=1024, temperature=0.0, messages=None,
               system=None, tools=None, tool_choice=None, **_ignored):
        kwargs = dict(
            model=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),  # ignore Anthropic model strings
            messages=_messages_to_openai(messages or [], system),
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if tools:
            kwargs["tools"] = _tools_to_openai(tools)
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "tool":
                kwargs["tool_choice"] = {"type": "function",
                                         "function": {"name": tool_choice["name"]}}
        resp = _or_client().chat.completions.create(**kwargs)
        return _to_anthropic_response(resp)

class _Client:
    def __init__(self): self.messages = _Messages()

_compat = None
def client():
    global _compat
    if _compat is None:
        _compat = _Client()
    return _compat


# --- public helpers (identical signatures to the Anthropic version) ----------
def call_model(messages, system=None, tools=None, model=None,
               max_tokens=1024, temperature=0.0):
    kwargs = {"model": model or DEFAULT_MODEL, "max_tokens": max_tokens,
              "temperature": temperature, "messages": messages}
    if system: kwargs["system"] = system
    if tools:  kwargs["tools"] = tools
    return client().messages.create(**kwargs)


def text_of(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


def run_tool_loop(messages, tools, dispatch, system=None, model=None,
                  max_turns=8, on_step=None):
    for _turn in range(max_turns):
        resp = call_model(messages, system=system, tools=tools, model=model)
        if on_step: on_step("model_response", resp)
        if resp.stop_reason != "tool_use":
            return text_of(resp), messages
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            if on_step: on_step("tool_call", {"name": block.name, "input": block.input})
            try:
                result = dispatch(block.name, block.input); is_error = False
            except Exception as e:
                result = f"Tool error: {e}"; is_error = True
            if on_step: on_step("tool_result", {"name": block.name, "result": result})
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": json.dumps(result) if not isinstance(result, str) else result,
                "is_error": is_error})
        messages.append({"role": "user", "content": tool_results})
    return "Stopped: reached max_turns without a final answer.", messages