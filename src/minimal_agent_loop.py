"""
Minimal agent loop with chemistry toy tools.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=...   (Mac/Linux)   or   $env:ANTHROPIC_API_KEY="..."  (PowerShell)

Run (from the repo root):
    python src/minimal_agent_loop.py
    python src/minimal_agent_loop.py "Your own goal here"

The key is read from the environment by the SDK; it never appears in this file.
"""

import json
import math
import sys

MODEL = "claude-sonnet-5-5"   # swap for any model string you have access to
MAX_STEPS = 10                # safety cap: the loop can never run forever

# ---------------------------------------------------------------------------
# 1. TOOLS: plain Python functions the model can ask us to run
# ---------------------------------------------------------------------------
# Antoine equation: log10(P_mmHg) = A - B / (C + T_celsius)
# Constants are standard textbook values, good for rough comparisons only.
ANTOINE = {
    "methanol":    (8.08097, 1582.271, 239.726),
    "ethanol":     (8.20417, 1642.890, 230.300),
    "isopropanol": (8.11778, 1580.920, 219.610),
    "acetone":     (7.11714, 1210.595, 229.664),
    "toluene":     (6.95464, 1344.800, 219.482),
    "water":       (8.07131, 1730.630, 233.426),
}


def list_solvents():
    """Return the names of solvents we have data for."""
    return {"solvents": sorted(ANTOINE)}


def boiling_point(compound, pressure_mmHg):
    """Invert Antoine: T = B / (A - log10(P)) - C."""
    key = compound.strip().lower()
    if key not in ANTOINE:
        return {"error": f"unknown compound '{compound}'", "known": sorted(ANTOINE)}
    if pressure_mmHg <= 0:
        return {"error": "pressure must be positive"}
    a, b, c = ANTOINE[key]
    t_c = b / (a - math.log10(pressure_mmHg)) - c
    return {"compound": key, "pressure_mmHg": pressure_mmHg, "boiling_point_C": round(t_c, 1)}


# Dispatch table: tool name -> Python function
TOOL_FUNCTIONS = {"list_solvents": list_solvents, "boiling_point": boiling_point}

# What the model sees: name, description, and a JSON schema for the inputs
TOOL_DEFS = [
    {
        "name": "list_solvents",
        "description": "List the solvents available in the boiling point database.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "boiling_point",
        "description": "Estimate a solvent's boiling point (deg C) at a given pressure (mmHg) using the Antoine equation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "compound": {"type": "string", "description": "Solvent name, e.g. 'methanol'"},
                "pressure_mmHg": {"type": "number", "description": "Absolute pressure in mmHg"},
            },
            "required": ["compound", "pressure_mmHg"],
        },
    },
]


def run_tool(name, tool_input):
    """Execute one tool request and return the result as a string."""
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"error": f"no such tool '{name}'"})
    try:
        return json.dumps(func(**tool_input))
    except Exception as exc:  # report failures to the model so it can adapt
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


# ---------------------------------------------------------------------------
# 2. THE AGENT LOOP
# ---------------------------------------------------------------------------
def run_agent(goal, client, model=MODEL, max_steps=MAX_STEPS):
    # The conversation so far. This list IS the agent's state.
    messages = [{"role": "user", "content": goal}]

    for step in range(1, max_steps + 1):
        print(f"\n--- step {step} ---")

        # STEP A: send the conversation and tool definitions to the model
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=TOOL_DEFS,
            messages=messages,
        )

        # STEP B: check why the model stopped. If it did not ask for a tool,
        # it considers the goal done, so we return its text answer.
        if response.stop_reason != "tool_use":
            answer = "".join(b.text for b in response.content if b.type == "text")
            print("model finished.")
            return answer

        # STEP C: record the model's turn (including its tool requests)
        messages.append({"role": "assistant", "content": response.content})

        # STEP D: execute every tool the model requested, and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"model calls {block.name}({json.dumps(block.input)})")
                result = run_tool(block.name, block.input)
                print(f"  -> {result}")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )

        # STEP E: feed results back as a user turn, then loop to Step A
        messages.append({"role": "user", "content": tool_results})

    # Reached the cap without a final answer: stop rather than run forever
    return f"[stopped: hit the {max_steps}-step cap without a final answer]"


# ---------------------------------------------------------------------------
# 3. ENTRY POINT
# ---------------------------------------------------------------------------
def main():
    import anthropic  # imported here so the loop can be tested without the package

    goal = " ".join(sys.argv[1:]) or (
        "Which of methanol, ethanol, isopropanol and acetone boils lowest at "
        "500 mmHg, and by how many degrees C does it beat the second lowest?"
    )
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    print(f"goal: {goal}")
    print("\nFINAL ANSWER:\n" + run_agent(goal, client))


if __name__ == "__main__":
    main()
