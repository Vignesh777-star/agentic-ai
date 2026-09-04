# Agentic AI — Hands-On Coding Labs

Runnable, exercise-driven companion to the course. Each day has an
`exercise.py` (with `TODO`s for you to complete) and a `solution.py` to check
against. Framework-free on purpose: you see the whole agent as plain code.

The labs distill the field's most-cited sources into working patterns:
- The **agent loop** and **workflow-vs-agent** distinction (Anthropic,
  *Building Effective Agents*).
- The five **workflow patterns**: prompt chaining, routing, parallelization,
  orchestrator-workers, evaluator-optimizer (same source).
- **Production principles**: own your context window, tools are structured
  outputs, small focused agents, humans as first-class steps, eval-driven
  development (HumanLayer, *12-Factor Agents*).

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # add ANTHROPIC_API_KEY
```

## The labs
| Day | Pattern | Do the exercise | Reference |
|----|---------|-----------------|-----------|
| 1 | The agent loop | `day1_agent_loop/exercise.py` | `solution.py` |
| 2 | Reflection + memory | `day2_reflection_memory/reflection_exercise.py` | `reflection_solution.py`, `memory_solution.py` |
| 3 | Tool use / structured outputs | `day3_tool_use/exercise.py` | `solution.py` |
| 4 | Planning + multi-agent | `day4_planning_multiagent/orchestrator_exercise.py` | `orchestrator_solution.py`, `router_solution.py` |
| 5 | Evaluation + capstone | `day5_eval_capstone/eval_exercise.py` | `eval_solution.py`, `research_agent_solution.py` |

## How to work
1. Open the day's `exercise.py`, read the header, fill each `TODO`.
2. Run it. When it works (or you're stuck), diff against `solution.py`.
3. The capstone (`research_agent_solution.py`) composes every pattern; it runs
   offline on a small corpus — swap `search()`/`fetch()` for a real web API to
   go live.

## Shared layer
- `shared/llm.py` — one thin model wrapper + the canonical agent loop. Swap the
  provider here (including a self-hosted/air-gapped model) and every lab still runs.
- `shared/tools.py` — reusable tools + their JSON schemas.
