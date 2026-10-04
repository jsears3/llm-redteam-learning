# Results

The raw per-run JSON output from the original test batches — every model answer and every tool call, for all 7 variants against both models — is included here:

- [`2026-10-02-injection-harness-results.json`](2026-10-02-injection-harness-results.json) — Sonnet, variants `control` / `blunt_command` / `policy_wording` / `policy_action` / `buried_action`, 5 reps each
- [`2026-10-02-injection-harness-results-2.json`](2026-10-02-injection-harness-results-2.json) — Haiku, same 5 variants, 5 reps each
- [`2026-10-02-injection-harness-results-3.json`](2026-10-02-injection-harness-results-3.json) — Haiku, variants `chemical_wording` / `chemical_action`, 5 reps each
- [`2026-10-02-injection-harness-results-4.json`](2026-10-02-injection-harness-results-4.json) — Sonnet, same 2 chemical variants, 5 reps each

Together these four files cover all 7 attack variants against both models, 5 reps per cell (70 runs total). The results table in the main [README](../README.md) is computed directly from this data (see the query in that section) — not hand-read or hand-corrected.

To regenerate or extend this data, run the harness locally with your own `ANTHROPIC_API_KEY`:

```bash
python src/injection_harness.py --reps 20   # more reps than the original 5, per the roadmap
```

This saves a dated JSON file into this folder automatically (an existing file is never overwritten).
