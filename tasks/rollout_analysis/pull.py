"""Pull the rollouts one analysis covers, and write the manifest every later stage reads.

For each task in targets.json: `horizon rollouts pull` the task version into rollouts/<g>/,
then fetch every rollout of the named eval(s) by the target's model in full from the API into full/<g>/.
The full record matters: `rollouts pull` truncates grade_result at 2048 bytes, which cuts off
the pytest trace that names the failing assertion.

    ~/horizon_env/bin/python pull.py            # every task in targets.json
    ~/horizon_env/bin/python pull.py g7 g9      # just these

It must run under ~/horizon_env's python: the `horizon` client package is installed only in
that venv's site-packages. The key comes from the repo's .env.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
HORIZON = os.path.expanduser("~/horizon_env/bin/horizon")


def load_env():
    for line in open(os.path.join(REPO, ".env")):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main(tasks):
    load_env()
    from horizon import HorizonClient  # only importable under ~/horizon_env/bin/python

    T = json.load(open(f"{HERE}/targets.json"))
    man_path = f"{HERE}/manifest.json"
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    c = HorizonClient()
    for g in tasks or list(T):
        x = T[g]
        r = subprocess.run([HORIZON, "rollouts", "pull", x["tid"], "--version", str(x["v"]),
                            "--output-dir", f"{HERE}/rollouts/{g}"], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"{g}: rollouts pull failed:\n{r.stderr}")
        os.makedirs(f"{HERE}/full/{g}", exist_ok=True)
        # task_version_number, not version, and extracted_score, not score: the first pass
        # grouped on the wrong fields and every rollout came back version None
        # the model is per-target: the same task version has been run under several
        # (lumen, meridian, vesper), and pooling them would average two different agents
        model = x.get("model", "lumen")
        rs = [r for r in c.tasks.rollouts(x["tid"]).rollouts
              if r.model == model and r.task_version_number == x["v"]
              and any(r.evaluation_id.startswith(e) for e in x["evals"])]
        man[g] = []
        for ro in sorted(rs, key=lambda ro: (ro.evaluation_id, ro.run_number)):
            raw = c._transport.request("GET", f"/api/v1/rollouts/{ro.id}")
            json.dump(raw, open(f"{HERE}/full/{g}/{ro.id}.json", "w"))
            man[g].append({"id": ro.id, "eval": ro.evaluation_id[:8], "run": ro.run_number,
                           "score": ro.extracted_score, "errored": ro.is_errored,
                           "turns": ro.turn_count, "cost": ro.total_cost, "stop": ro.stop_reason})
        scored = sum(m["score"] is not None for m in man[g])
        print(f"{g}: {len(man[g])} {model} rollouts, {scored} scored")
    json.dump(man, open(man_path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
