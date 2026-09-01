#!/usr/bin/env python3
"""One job's result, as the loop needs to read it: score plus per-test outcome."""
import json, pathlib, sys

job = pathlib.Path("jobs") / sys.argv[1]
res = json.loads((job / "result.json").read_text())
out = {"job": sys.argv[1], "rewards": {}, "outcomes": {}, "provenance": {}}
for ev in res["stats"]["evals"].values():
    for m in ev.get("metrics", []):
        if "reward" in m:
            out["rewards"] = m
trial = next((p for p in job.iterdir() if p.is_dir()), None)
if trial and (trial / "verifier" / "report.json").exists():
    rep = json.loads((trial / "verifier" / "report.json").read_text())
    out["outcomes"] = rep.get("outcomes", {})
    out["provenance"] = rep.get("provenance", {})
    out["trial"] = trial.name
print(json.dumps(out, indent=1))
