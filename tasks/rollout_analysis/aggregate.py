"""Aggregate the per-run reader verdicts for one task into rates.

The readers decide found / believed / acted by reading transcripts; this only
counts. Remark metadata (surface, kind, carries, literals) comes from the prepass
parse of the answer key, not from the readers, so a reader that mislabels a kind
cannot move a bucket.
"""
import collections, glob, json, os, re, sys

S = os.path.dirname(os.path.abspath(__file__))

# Reader verdicts I checked by hand and overruled (evidence in readers/corrections.md).
# Applied here, not by editing the reader's JSON, so the original verdict survives.
OVERRIDES = {
    # g7's three overrides (run 4 borderline order, run 10 defect A) belonged to eval 94bf8242,
    # superseded 2026-09-11 by eval 8deffce4 (v5), which reuses the same run numbers; they
    # were removed so they cannot land on the new runs. The old verdicts are archived in
    # readers/_superseded/g7_v4_eval94bf8242/.
    # write_sidecar's argument order is graded but stated nowhere the world serves: the only
    # clause pinning it ("you hand it the work dir and the ledger", g7.r1.say20) exists in the
    # plant's gist and was dropped when phase 4 rendered the exchange (0 hits in the served
    # plant/messages.jsonl, 0 in all 10 v5 transcripts). Run 3's reader already said so.
    # The grader now accepts either order (probe_support.call_write_sidecar, 2026-09-11), so both
    # losses are set aside as a grader artefact since fixed: outside KNOWLEDGE, like dead-run
    # causes. They stay in Horizon's grades, so no reward or pass rate moves.
    ("g7", 3, "g7.r1.rule"): "grader_since_fixed",
    ("g7", 8, "g7.r1.rule"): "grader_since_fixed",
    # reader said implementation_slip, yet also that TURN_LEDGER_FILENAME never appears in the
    # transcript (grep agrees: only runs 2, 3, 4, 8 show it); run 10 repeated the VALUE
    # turn_ledger.json, never the name — the single-home constant was not found
    ("g7", 10, "g7.r1.rule"): "not_found",
    ("g2", 3, "g2.r1.observability"): "not_found",
    # g8 runs 3 and 4 (30c95df4) were overridden to overridden_by_other_corpus_text for fix24's
    # invented closing turn ("auto ... not a detail level its a fallback"). Withdrawn 2026-09-11:
    # the answer is knowable (l14 "three entries, index 0 is what the fallback hands back",
    # dermot's "one of the three", the ticket's detail="auto", Image.detail's default), and
    # neither run had l14 in view. The readers' own verdicts stand (found_misread, not_found).
    # g11's three run-1 overrides (herring_followed, the half-reversed konrad herring) belonged to
    # eval 94bf8242 (v7), superseded 2026-09-11 by the rerun on the G11-H fix, which reuses the
    # same run numbers; they were removed so they cannot land on the new run 1. The old verdicts
    # are archived in readers/_superseded/g11_v7_eval94bf8242/.
    # g11 v11 run 7: reader said not_found, yet its own herring row has konrad's herring seen,
    # rev2 never seen, "believed: herring", code followed — Analysis L3640 "warmup strict
    # `step < warmup_steps` ... confirmed", shipped with no effective_warmup clamp.
    ("g11", 7, "g11.r2.failure_behavior"): "herring_followed",
    # g11 v11 run 6: reader said found_misread for the merge, but l17 reached it only as its
    # opening question (reader: "only ever seen as its opening line — the reply thread was never
    # fetched"); runs 2 and 10, identical, are not_found.
    ("g11", 6, "g11.r1.failure_behavior"): "not_found",
    # g3 v9 run 10 shipped throttle_cooldown_until defaulting to None. Reader said
    # implementation_slip, but its reasoning never states the field's default — the "0.0" it
    # wrote is remaining_cooldown_seconds' return (s1d) — and the ticket never names the field.
    # The one remark that does, s1a ("0.0 on a fresh tracker", a wiki comment), was never
    # surfaced. The None came from h2's unretracted tail "sets it to none" (the reset path).
    ("g3", 10, "g3.r2.rule"): "not_found",
    ("g3", 10, "g3.r2.observability"): "not_found",
}
# A run that never shipped (never committed, or built the module and never wired it in, then
# looped until the budget or the 7200s trial limit) says nothing about which clues were found.
# Readers called these "infra" (g4 run2, g3 v9 run3) or "implementation_slip" (g2 run8); none
# is a harness fault, and none is a knowledge loss. g3 run3 typed no git commit or push at
# all, its patch scripts never landed, and it closed claiming a commit and a green CI.
# g4 run9 and g7 (v5) run5 were read as "infra: stale terminal". Withdrawn 2026-09-11: no pager,
# editor or stuck process was ever opened, no two consecutive screens are identical, and the
# "pushed / merged / CI green" readings they reacted to never appear in any tool turn (g7's
# "HEAD=8e34d2ef3d ... ci/test success" and "PR 737/738" exist only in its own reasoning; g4's one
# commit confirmation is at transcript line 11139, near the end, and it never pushed). The agents
# distrusted real output and failed to ship.
NEVER_SHIPPED = {("g2", 8), ("g4", 2), ("g10", 8), ("g3", 3), ("g4", 9), ("g7", 5)}


def yes(v):
    # readers write "yes", "yes (line 3047)", true, "partial", "no", false, null
    if isinstance(v, bool):
        return v
    return isinstance(v, str) and v.strip().lower().startswith(("yes", "true"))


def norm_found(v):
    s = str(v).strip().lower()
    return "yes" if s.startswith("yes") else "partial" if s.startswith("partial") else "no"


def pct(n, d):
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "—"


def main(g):
    pre = json.load(open(f"{S}/prepass/{g}.json"))
    meta = {r["id"]: r for r in pre["remarks"]}
    runs = []
    fact_fixes = []
    for f in sorted(glob.glob(f"{S}/readers/{g}/run*.json"), key=lambda p: int(re.search(r"run(\d+)", p).group(1))):
        d = json.load(open(f))
        # Horizon's grade is the truth for what passed; a reader's copy of it drifted
        # once already (g7 counted r1.failure_behavior 3/10 against 6 recorded losses)
        rid_full = next(k for k in pre["runs"] if k.startswith(str(d["rollout_id"])[:8]))
        graded = {k: v for k, v in pre["runs"][rid_full]["grade"]["subscores"].items() if re.match(rf"{g}\.r\d\.", k)}
        fact_fixes += [(d["run"], k, d["facts"].get(k), v) for k, v in graded.items() if d["facts"].get(k) != v]
        d["facts"] = graded
        for l in d.get("lost_facts", []):
            o = OVERRIDES.get((g, d["run"], l["fact"]))
            if o:
                l["reader_cause"], l["cause"] = l["cause"], o
        shipped_nothing = (g, d["run"]) in NEVER_SHIPPED
        if shipped_nothing:
            for l in d.get("lost_facts", []):
                l.setdefault("reader_cause", l["cause"])
                l["cause"] = "never_shipped"
        causes = [l["cause"] for l in d.get("lost_facts", [])]
        # a run lost wholly to the harness, or that never shipped, says nothing about findability
        d["_infra"] = shipped_nothing or (bool(causes) and all(c == "infra" for c in causes) and not d.get("passed_facts"))
        runs.append(d)
    live = [d for d in runs if not d["_infra"]]
    L = [f"# {g}: {len(runs)} runs read ({len(live)} counted for findability; infra-only runs excluded: "
         f"{[d['run'] for d in runs if d['_infra']]})", ""]

    # facts
    facts = sorted({k for d in runs for k in d["facts"] if re.match(rf"{g}\.r\d\.", k)})
    L += ["## per-fact pass rate (all runs)", "", "| fact | passed | lost causes |", "|---|---|---|"]
    for k in facts:
        p = sum(d["facts"].get(k) == 1 for d in runs)
        c = collections.Counter(l["cause"] for d in runs for l in d.get("lost_facts", []) if l["fact"] == k)
        L.append(f"| {k} | {pct(p, len(runs))} | {dict(c)} |")
    allc = collections.Counter(l["cause"] for d in runs for l in d.get("lost_facts", []))
    L += ["", f"**lost fact-points by cause:** {dict(allc)}",
          f"**graded losses:** {sum(v == 0 for d in runs for v in d['facts'].values())}; "
          f"reader-recorded losses: {sum(len(d.get('lost_facts', [])) for d in runs)}",
          f"**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** {fact_fixes or 'none'}", ""]

    # remarks
    rows = collections.defaultdict(list)
    for d in live:
        for r in d["remarks"]:
            rows[r["id"]].append(r)
    L += ["## per remark (live runs)", "",
          "| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |",
          "|---|---|---|---|---|---|---|---|"]
    bucket = collections.defaultdict(lambda: [0, 0])
    for rid, m in meta.items():
        rs = rows.get(rid, [])
        fy = [r for r in rs if norm_found(r.get("found")) == "yes"]
        fp = [r for r in rs if norm_found(r.get("found")) == "partial"]
        seen = fy + fp
        reg = sum(str(r.get("registered", "")).startswith("requirement") for r in seen)
        act = sum(str(r.get("acted", "")).startswith("followed") for r in seen)
        L.append(f"| {rid} | {m['kind']} | {m.get('surface','')} | {','.join(c.split('.')[-1] for c in m['carries']) or '—'} | "
                 f"{pct(len(fy), len(rs))} | {len(fp)} | {pct(reg, len(seen))} | {pct(act, len(seen))} |")
        for key in (f"surface={m.get('surface')}", f"kind={m['kind']}", f"literal={'yes' if m.get('literal') else 'no'}"):
            bucket[key][0] += len(seen)
            bucket[key][1] += len(rs)
    L += ["", "## found rate by remark quality (live runs; found = yes or partial)", "", "| bucket | found |", "|---|---|"]
    L += [f"| {k} | {pct(v[0], v[1])} |" for k, v in sorted(bucket.items())]

    # herrings
    L += ["", "## herrings (live runs)", "", "| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |", "|---|---|---|---|---|"]
    hs = collections.defaultdict(list)
    # readers append a description to the id ("g7.r1.x (dermot #pipeline ...)"), which
    # split one herring across several rows
    hid = lambda s: (re.search(rf"{g}\.r\d\.[\w-]+", str(s)) or re.search(r"\S+", str(s))).group(0)
    for d in live:
        for h in d.get("herrings", []):
            hs[(hid(h.get("herring")), hid(h.get("reversal")))].append(h)
    for (h, rv), xs in sorted(hs.items(), key=lambda x: str(x[0])):
        L.append(f"| {h} → {rv} | {pct(sum(yes(x.get('saw_herring')) for x in xs), len(xs))} | "
                 f"{pct(sum(yes(x.get('saw_reversal')) for x in xs), len(xs))} | "
                 f"{pct(sum(str(x.get('believed','')).lower().startswith('herring') for x in xs), len(xs))} | "
                 f"{pct(sum(x.get('code_followed_herring') is True for x in xs), len(xs))} |")

    # reader vs prepass agreement, as a check on both
    agree = tot = 0
    disagree = []
    for d in live:
        rid_full = next((k for k in pre["runs"] if k.startswith(str(d["rollout_id"])[:8])), None)
        if not rid_full:
            continue
        hits = pre["runs"][rid_full]["hits"]
        for r in d["remarks"]:
            a = norm_found(r.get("found")) != "no"
            b = any(h["in"] == "tool" for h in hits.get(r["id"], []))
            tot += 1
            agree += a == b
            if a != b:
                disagree.append((d["run"], r["id"], "reader" if a else "prepass"))
    L += ["", f"## reader vs prepass agreement: {pct(agree, tot)}; only-one-says-found: "
          f"{collections.Counter(x[2] for x in disagree)}", ""]
    L += [f"- run{x[0]} {x[1]}: found only by {x[2]}" for x in disagree[:40]]

    out = f"{S}/readers/{g}/summary.md"
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1])
