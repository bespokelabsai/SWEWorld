"""Pointer pre-pass for the rollout readers. Decides nothing; it aims the reading.

For each task: parse the answer key's "Where every remark is" section into a remark
table, parse each transcript into numbered turns, and list where each remark's exact
rendered text surfaces (turn, transcript line, the command that surfaced it).
Also writes each run's graded outcome: fact subscores plus the full failing ctrf traces.
"""
import codecs, json, os, re, sys

S = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/nidhi_bespokelabs_ai/SWEWorld"
T = json.load(open(f"{S}/targets.json"))
MAN = json.load(open(f"{S}/manifest.json"))


def norm(s):
    # Mattermost/BookStack/IMAP output arrives JSON-escaped, quoted-printable or
    # re-wrapped, so compare on letters and digits only.
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def unescape(s):
    s = s.replace("\\n", " ").replace('\\"', '"').replace("\\/", "/")
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def parse_key(path):
    text = open(path).read()
    start = text.index("## Where every remark is")
    body = text[start:]
    table = {}
    for row in re.finditer(r"^\| (\S+) \| ([^|]+) \| (.+?) \| (\S+) \| \[`([^`]+)`\].*?\| \d+ \| (.+?) \| (.+?) \|$", body, re.M):
        table[row.group(5)] = {"date": row.group(1), "surface": row.group(2).strip(), "where": row.group(3).strip(),
                               "holder": row.group(4), "kind_cell": row.group(6).strip(), "carries_cell": row.group(7).strip()}
    remarks = []
    for m in re.finditer(r"^#### `([^`]+)`(.*?)$(.*?)(?=^#### `|\Z)", body, re.M | re.S):
        rid, head, block = m.group(1), m.group(2), m.group(3)
        kind = "herring" if "herring" in head else "reversal" if "reversal" in head else "clue"
        r = {"id": rid, "kind": kind, **table.get(rid, {})}
        first = re.search(r"^- \*\*(.+?)\*\* · (.+?) · \*\*(\w+)\*\* · ([\d-]+ [\d:]+)", block, re.M)
        if first:
            r.update(surface=first.group(1), where=first.group(2).strip("“”"), holder=first.group(3), when=first.group(4))
        c = re.search(r"^- carries (.+)$", block, re.M)
        r["carries"] = re.findall(r"`([^`]+)`", c.group(1)) if c else []
        tb = re.search(r"^- takes back `([^`]+)`", block, re.M)
        r["reverses"] = tb.group(1) if tb else ""
        lit = re.search(r"^- must be typed literally: (.+)$", block, re.M)
        r["literal"] = re.findall(r"`([^`]+)`", lit.group(1)) if lit else []
        gist = re.search(r"leave a reader with:\s*\n\s*\n((?:> .*\n?)+)", block)
        if gist:
            r["gist"] = " ".join(l[2:] for l in gist.group(1).splitlines())
        else:
            # wiki comments and page bodies quote the remark straight under the
            # bullets, with no "leave a reader with" header; without this they get
            # no probe at all and read as never found (4 of g7's 51)
            r["gist"] = " ".join(l[2:] for l in block.splitlines() if l.startswith("> "))
        rendered = re.search(r"As it appears.*?```\n(.*?)```", block, re.S)
        if rendered:
            lines = []
            for l in rendered.group(1).splitlines():
                cm = re.match(r"^\d\d:\d\d\s+\S+\s+(.*)$", l)
                if cm:
                    lines.append(cm.group(1))
                elif l.strip() and not re.match(r"^(From|Sent|To|Subject):|^-{10,}", l):
                    lines.append(l)
            r["rendered"] = lines
        else:
            r["rendered"] = [r["gist"]]
        remarks.append(r)
    return remarks


def fragments(r):
    # Exact corpus text, cut into probes long enough not to collide with the ticket
    # or with ordinary prose; sentences for mail/wiki, whole messages for chat.
    out = []
    for line in r["rendered"]:
        for sent in re.split(r"(?<=[.!?])\s+", line):
            n = norm(sent)
            if len(n) >= 28:
                out.append(n[:60])
    return out


def parse_transcript(path):
    lines = open(path).read().splitlines()
    turns, cur = [], None
    for i, l in enumerate(lines, 1):
        h = re.match(r"^## \[(user|assistant|tool)\]", l)
        if h:
            cur = {"role": h.group(1), "start": i, "lines": []}
            turns.append(cur)
        elif cur is not None:
            cur["lines"].append((i, l))
    return turns


def locate(turns, remarks):
    hits = {r["id"]: [] for r in remarks}
    probes = {r["id"]: fragments(r) for r in remarks}
    step = 0
    for t in turns:
        if t["role"] == "assistant":
            step += 1
        if t["role"] == "user":
            continue  # the ticket; a hit there is not a find
        cmd = ""
        # a remark can straddle wrapped terminal lines: probe a sliding 3-line window
        buf = [(i, norm(unescape(l)), l) for i, l in t["lines"]]
        for k, (i, n, raw) in enumerate(buf):
            if t["role"] == "tool" and re.search(r"\$ \S", raw):
                cmd = raw.split("$ ", 1)[1][:200]
            window = "".join(x[1] for x in buf[k:k + 3])
            for rid, ps in probes.items():
                got = [p for p in ps if p in window and p in (n + "".join(x[1] for x in buf[k + 1:k + 3]))]
                if got and not any(h["line"] in range(i - 2, i + 1) for h in hits[rid]):
                    hits[rid].append({"step": step, "line": i, "in": t["role"], "cmd": cmd if t["role"] == "tool" else "",
                                      "probes_hit": len(set(got)), "probes_total": len(set(ps))})
    return hits


def grade(g, rid):
    d = json.load(open(f"{S}/full/{g}/{rid}.json"))
    gr = d.get("grade_result") or {}
    ss = gr.get("subscores") or {}
    out = {"subscores": ss, "failed_tests": []}
    fb = (gr.get("metadata") or {}).get("feedback") or {}
    if not isinstance(fb, dict):
        # an execution failure (g2 7be2f425) carries a plain string, no ctrf at all
        out["failed_tests"].append({"name": "execution", "trace": str(fb)[:6000]})
        return out
    ct = fb.get("ctrf.json")
    ct = json.loads(ct) if isinstance(ct, str) else ct
    if ct:
        for t in ct["results"]["tests"]:
            if t["status"] != "passed":
                out["failed_tests"].append({k: v for k, v in t.items() if k not in ("duration", "start", "stop", "retries")})
    return out


def main(tasks):
    os.makedirs(f"{S}/prepass", exist_ok=True)
    for g in tasks:
        x = T[g]
        remarks = parse_key(f"{REPO}/{x['arm']}/solution/hidden_requirements.md")
        vdir = f"{S}/rollouts/{g}/v{x['v']}"
        runs = {}
        for m in MAN[g]:
            tf = next(f for f in os.listdir(vdir) if m["id"][:8] in f and f.endswith("_transcript.md"))
            turns = parse_transcript(f"{vdir}/{tf}")
            runs[m["id"]] = {**m, "transcript": f"{vdir}/{tf}", "steps": sum(t["role"] == "assistant" for t in turns),
                             "hits": locate(turns, remarks), "grade": grade(g, m["id"])}
        json.dump({"task": g, "remarks": remarks, "runs": runs}, open(f"{S}/prepass/{g}.json", "w"), indent=1)
        # a reader-facing pointer sheet per run
        os.makedirs(f"{S}/prepass/{g}", exist_ok=True)
        for rid, run in runs.items():
            L = [f"# {g} run {run['run']} ({rid}) eval {run['eval']} — reward {run['grade']['subscores'].get('reward')}",
                 f"transcript: {run['transcript']}  ({run['steps']} agent steps)", "",
                 "## graded facts", ""]
            L += [f"- {k}: {v}" for k, v in run["grade"]["subscores"].items()]
            L += ["", "## failing tests (full ctrf trace)", ""]
            for t in run["grade"]["failed_tests"]:
                L += [f"### {t.get('name')}", "```", str(t.get("trace") or t.get("message") or t)[:6000], "```"]
            L += ["", "## where each answer-key remark's exact text surfaces (pointer only — verify by reading)", "",
                  "| remark | kind | surface | carries | first step | first line | lines hit | cmd that surfaced it |",
                  "|---|---|---|---|---|---|---|---|"]
            for r in remarks:
                h = run["hits"][r["id"]]
                tool = [x for x in h if x["in"] == "tool"]
                f = (tool or h or [None])[0]
                L.append(f"| {r['id']} | {r['kind']}{' of ' + r['reverses'] if r['reverses'] else ''} | {r.get('surface','')} · {r.get('where','')[:60]} | {','.join(c.split('.')[-1] for c in r['carries'])} | "
                         + (f"{f['step']} | {f['line']} | {len(h)} ({len(tool)} tool) | `{f['cmd'][:90]}` |" if f else "— | — | 0 | |"))
            open(f"{S}/prepass/{g}/run{run['run']}_{run['eval']}_{rid[:8]}.md", "w").write("\n".join(L) + "\n")
        found = sum(1 for run in runs.values() for r in remarks if any(h["in"] == "tool" for h in run["hits"][r["id"]]))
        print(g, "remarks", len(remarks), "kinds", {k: sum(r["kind"] == k for r in remarks) for k in ("clue", "herring", "reversal")},
              "runs", len(runs), "remark-surfacings", found, "of", len(runs) * len(remarks))


if __name__ == "__main__":
    main(sys.argv[1:] or list(T))
