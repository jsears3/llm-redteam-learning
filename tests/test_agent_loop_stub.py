"""Tests the agent loop with a fake model that replays scripted responses.
Run from the repo root: python tests/test_agent_loop_stub.py
"""
import importlib.util
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location("agent", "src/minimal_agent_loop.py")
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


def tool_use(id_, name, **inp):
    return NS(type="tool_use", id=id_, name=name, input=inp)


def text(t):
    return NS(type="text", text=t)


class FakeClient:
    """Mimics client.messages.create, returning scripted responses in order."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.messages = self  # so client.messages.create works

    def create(self, **kw):
        # snapshot the message count to confirm history grows each step
        self.calls.append(len(kw["messages"]))
        return self.script.pop(0)


def resp(stop, *blocks):
    return NS(stop_reason=stop, content=list(blocks))


# --- Test 1: multi-step run with parallel calls, then a final answer
fake = FakeClient([
    resp("tool_use", tool_use("t1", "list_solvents")),
    resp("tool_use",
         tool_use("t2", "boiling_point", compound="methanol", pressure_mmHg=500),
         tool_use("t3", "boiling_point", compound="acetone", pressure_mmHg=500)),
    resp("end_turn", text("Acetone boils lowest.")),
])
out = agent.run_agent("goal", fake)
assert out == "Acetone boils lowest.", out
assert fake.calls == [1, 3, 5], fake.calls  # history: 1 -> +2 -> +2
print("\nTEST 1 PASS: dispatch, parallel calls, history growth, clean finish")

# --- Test 2: bad tool name and bad compound come back as errors, not crashes
assert "no such tool" in agent.run_tool("nope", {})
assert "unknown compound" in agent.run_tool("boiling_point", {"compound": "xenon", "pressure_mmHg": 760})
assert "error" in agent.run_tool("boiling_point", {"compound": "water"})  # missing arg
print("TEST 2 PASS: errors returned to the model instead of raising")

# --- Test 3: step cap stops a model that never finishes
endless = FakeClient([resp("tool_use", tool_use(f"t{i}", "list_solvents")) for i in range(50)])
out = agent.run_agent("goal", endless, max_steps=4)
assert out.startswith("[stopped"), out
assert len(endless.calls) == 4, endless.calls
print("TEST 3 PASS: step cap halts a runaway loop at 4 calls")

# --- Test 4: Antoine values vs. known normal boiling points at 760 mmHg
known = {"methanol": 64.7, "ethanol": 78.4, "isopropanol": 82.3,
         "acetone": 56.1, "toluene": 110.6, "water": 100.0}
for name, ref in known.items():
    got = agent.boiling_point(name, 760)["boiling_point_C"]
    assert abs(got - ref) < 0.6, (name, got, ref)
    print(f"  {name:12s} calc {got:6.1f}  ref {ref:6.1f}")
print("TEST 4 PASS: tool numbers match literature normal boiling points")
