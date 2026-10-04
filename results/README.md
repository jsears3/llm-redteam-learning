# Results

The raw per-run JSON output from the original test batches (every model answer and tool call) was not retained — it was generated in a temporary session and never saved to persistent storage, so it no longer exists. The summarized, hand-corrected results in the main [README](../README.md) (after fixing the scoring-heuristic bug described there) are the authoritative record of that run.

To regenerate comparable data, run the harness locally with your own `ANTHROPIC_API_KEY`:

```bash
python src/injection_harness.py --reps 20   # more reps than the original 5, per the roadmap
```

This saves a dated JSON file into this folder automatically (an existing file is never overwritten). Commit and push it here once you have one, and the README's results table can be updated to cite it directly.
