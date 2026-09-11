"""Render tasks/g1-g11-lumen-rollout-analysis.md as the shareable audit page.

    python3 build_page.py <out.html>

The page is the report, re-set for reading: a header with the headline figures, two charts
drawn from the report's own tables (so they cannot drift from the text), a contents rail,
then every section of the report in its original order, with "How this was measured" moved
to the end. No markdown library is installed here, so this carries a converter for exactly
the subset the report uses: headings, paragraphs, nested lists, pipe tables, block quotes,
rules, bold, italic and code spans.
"""
import html, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "g1-g11-lumen-rollout-analysis.md")

CAUSE_TOKENS = {  # cause label as the report writes it -> colour token
    "not found": "--c-notfound", "implementation slip": "--c-slip", "found but misread": "--c-misread",
    "herring followed": "--c-herring", "grader over-specifies": "--c-grader",
    "the corpus argues against the grader": "--c-corpus",
}


# ---------------------------------------------------------------- inline
def inline(s):
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False).replace("\\[", "[").replace("\\]", "]")
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + html.escape(codes[int(m.group(1))], quote=False) + "</code>", s)


def cells(line):
    # split a pipe-table row, keeping pipes that sit inside code spans
    out, cur, in_code = [], "", False
    for ch in line.strip().strip("|"):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


# ---------------------------------------------------------------- blocks
LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def slug(text):
    m = re.match(r"(g\d+)\b", text)
    if m:
        return m.group(1)
    for key, sid in (("Findings", "findings"), ("Register", "register"), ("How this was measured", "method")):
        if text.startswith(key):
            return sid
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def heading(level, text):
    sid = slug(text) if level == 2 else re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]
    m = re.match(r"^(.*?)\s+(\((?:v\d+|evals?)[^)]*\).*)$", text) if level == 2 else None
    if m:  # "g7 — agent-turn-ledger (v5, eval 8deffce4)": set the version and eval as data
        body = f'{inline(m.group(1))} <span class="h-meta">{inline(m.group(2))}</span>'
    else:
        body = inline(text)
    return f'<h{level} id="{sid}">{body}</h{level}>'


def render_list(items, i, indent):
    tag = "ol" if items[i][1] else "ul"
    out = [f"<{tag}>"]
    while i < len(items) and items[i][0] == indent:
        text = inline(items[i][2])
        i += 1
        child = ""
        if i < len(items) and items[i][0] > indent:
            child, i = render_list(items, i, items[i][0])
        out.append(f"<li>{text}{child}</li>")
    out.append(f"</{tag}>")
    return "".join(out), i


def convert(md):
    lines, out, para, i = md.split("\n"), [], [], 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(x.strip() for x in para)) + "</p>")
            para.clear()

    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            flush(); i += 1; continue
        if ln.startswith("```"):
            flush(); j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            out.append('<div class="code-wrap"><pre><code>' + html.escape("\n".join(buf)) + "</code></pre></div>")
            i = j + 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            flush(); out.append(heading(len(m.group(1)), m.group(2))); i += 1; continue
        if ln.strip() == "---":
            flush(); out.append("<hr>"); i += 1; continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1]):
            flush(); head = cells(ln); rows = []; j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(cells(lines[j])); j += 1
            t = ['<div class="table-wrap"><table><thead><tr>'] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>")
            i = j; continue
        if ln.startswith(">"):
            flush(); buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip()); i += 1
            out.append("<blockquote><p>" + inline(" ".join(buf)) + "</p></blockquote>"); continue
        if LIST_RE.match(ln) and not ln.startswith(" "):
            flush(); items = []
            while i < len(lines) and lines[i].strip():
                lm = LIST_RE.match(lines[i])
                if lm:
                    items.append([len(lm.group(1)), lm.group(2)[0].isdigit(), lm.group(3)])
                elif lines[i].startswith(" ") and items:
                    items[-1][2] += " " + lines[i].strip()
                else:
                    break
                i += 1
            k = 0
            while k < len(items):
                h, k = render_list(items, k, items[k][0])
                out.append(h)
            continue
        para.append(ln); i += 1
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- data for the charts
def table_after(md, marker):
    at = md.find(marker)
    if at < 0:
        return []
    rows, started = [], False
    for ln in md[at:].split("\n")[1:]:
        if ln.startswith("|"):
            started = True
            if not re.match(r"^\|[\s:|-]+\|?\s*$", ln):
                rows.append(cells(ln))
        elif started:
            break
    return rows[1:]  # drop the header row


def plain(s):
    return re.sub(r"[*`]", "", s).strip()


def build(out_path):
    md = open(SRC).read()
    title_intro, rest = md.split("## How this was measured", 1)
    method, rest = rest.split("## Findings at a glance", 1)
    method = "## How this was measured" + method.rstrip().rstrip("-").rstrip()
    body_md = "## Findings at a glance" + rest.rstrip() + "\n\n---\n\n" + method

    status = re.search(r"Status:\s*(.+)", title_intro)
    status_txt = plain(status.group(1)) if status else ""
    n_read = re.search(r"(\d+) rollouts are read", title_intro)

    ranking = []
    for r in table_after(md, "### Difficulty ranking"):
        code, name = plain(r[0]).split(" ", 1)
        ranking.append({"code": code, "name": name, "mean": float(plain(r[1])), "top": plain(r[2]), "hard": plain(r[3])})
    causes = [(plain(r[0]), int(plain(r[1])), plain(r[2])) for r in table_after(md, "### 1.")]
    total = sum(c[1] for c in causes)
    herr = next((r for r in table_after(md, "### 4.") if plain(r[0]).startswith("overall")), None)
    herr_txt = plain(herr[1]).split(" (")[0] if herr else "—"
    notfound = next((c for c in causes if c[0] == "not found"), None)

    # header figures
    stats = [
        (n_read.group(1) if n_read else "—", "transcripts read against their answer keys"),
        (str(total), "hidden-requirement fact-points lost in live runs"),
        (notfound[2] if notfound else "—", "of those: the clue was never found"),
        (herr_txt, "run–herring pairs where the herring was believed"),
    ]
    stat_html = "".join(f'<div class="stat"><span class="stat-n">{html.escape(n)}</span><span class="stat-l">{html.escape(l)}</span></div>' for n, l in stats)

    # chart 1: mean reward per task on a true 0–1 scale
    rows = []
    for t in ranking:
        rows.append(
            f'<div class="bar-row"><span class="bar-label"><a href="#{t["code"]}"><code>{t["code"]}</code></a> {html.escape(t["name"])}</span>'
            f'<span class="track" role="img" aria-label="{t["code"]} mean reward {t["mean"]:.2f}"><span class="fill" style="width:{t["mean"] * 100:.1f}%"></span></span>'
            f'<span class="bar-val">{t["mean"]:.2f}</span><span class="bar-note">{html.escape(t["top"])} at 1.00</span></div>')
    ticks = "".join(f'<span class="tick" style="left:{v * 100:.0f}%">{v:g}</span>' for v in (0, 0.25, 0.5, 0.75, 1))
    chart1 = (f'<figure class="chart"><figcaption>Mean reward on live runs, hardest task first</figcaption>'
              f'<div class="bars">{"".join(rows)}<div class="bar-row axis"><span></span><span class="ticks">{ticks}</span><span></span><span></span></div></div></figure>')

    # chart 2: why the fact-points were lost
    segs = "".join(f'<span class="seg" style="width:{p / total * 100:.2f}%;background:var({CAUSE_TOKENS.get(c, "--muted")})" title="{html.escape(c)}: {p}"></span>' for c, p, _ in causes)
    legend = "".join(f'<li><span class="sw" style="background:var({CAUSE_TOKENS.get(c, "--muted")})"></span><span class="lg-c">{html.escape(c)}</span><span class="lg-n">{p}</span><span class="lg-s">{html.escape(s)}</span></li>' for c, p, s in causes)
    chart2 = (f'<figure class="chart"><figcaption>Why {total} fact-points were lost (live runs)</figcaption>'
              f'<div class="stack" role="img" aria-label="Lost fact-points by cause">{segs}</div><ul class="legend">{legend}</ul></figure>')

    # contents rail
    means = {t["code"]: t["mean"] for t in ranking}
    nav = ['<a href="#findings">Findings at a glance</a>']
    for m in re.finditer(r"^## (g\d+) — ([^\s(]+)", md, re.M):
        mean = f'<span class="nav-n">{means[m.group(1)]:.2f}</span>' if m.group(1) in means else ""
        nav.append(f'<a href="#{m.group(1)}"><code>{m.group(1)}</code> {html.escape(m.group(2))}{mean}</a>')
    nav += ['<a href="#register">Defect register</a>', '<a href="#method">How this was measured</a>']

    page = TEMPLATE.format(
        status=html.escape(status_txt), stats=stat_html, chart1=chart1, chart2=chart2,
        nav="".join(nav), body=convert(body_md))
    open(out_path, "w").write(page)
    print("wrote", out_path, len(page), "bytes;", len(ranking), "tasks,", total, "fact-points")


TEMPLATE = """<title>SWEWorld Rollout Audit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<style>
:root {{
  --bg: #F3F5F8; --surface: #FFFFFF; --ink: #18202C; --muted: #586273; --rule: #D6DCE4;
  --accent: #2457A6; --accent-soft: #E3EBF7; --code-bg: #E9EDF3; --track: #E6EAF0;
  --c-notfound: #2457A6; --c-slip: #B8702A; --c-misread: #7456B0; --c-herring: #B23A48;
  --c-grader: #2F8575; --c-corpus: #8A94A6;
  --display: "Bricolage Grotesque", "Segoe UI", system-ui, sans-serif;
  --prose: "Source Serif 4", Georgia, "Times New Roman", serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #10141B; --surface: #171C25; --ink: #E4E8EF; --muted: #9AA4B5; --rule: #2A3240;
    --accent: #7EA6EC; --accent-soft: #1D2940; --code-bg: #1F2632; --track: #222A36;
    --c-notfound: #7EA6EC; --c-slip: #E0A15E; --c-misread: #A993DD; --c-herring: #E07482;
    --c-grader: #6CC0AE; --c-corpus: #7C8699;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #10141B; --surface: #171C25; --ink: #E4E8EF; --muted: #9AA4B5; --rule: #2A3240;
  --accent: #7EA6EC; --accent-soft: #1D2940; --code-bg: #1F2632; --track: #222A36;
  --c-notfound: #7EA6EC; --c-slip: #E0A15E; --c-misread: #A993DD; --c-herring: #E07482;
  --c-grader: #6CC0AE; --c-corpus: #7C8699;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-padding-top: 1.5rem; }}
@media (prefers-reduced-motion: no-preference) {{ html {{ scroll-behavior: smooth; }} }}
body {{ background: var(--bg); color: var(--ink); font-family: var(--prose); font-size: 17px; line-height: 1.6;
  padding-inline: 24px; padding-block: 0 72px; }}
a {{ color: var(--accent); text-underline-offset: 2px; }}
a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }}
code {{ font-family: var(--mono); font-size: 0.84em; background: var(--code-bg); padding: 0.08em 0.32em; border-radius: 3px; }}

.masthead {{ max-width: 1120px; margin-inline: auto; padding-block: 56px 32px; border-bottom: 1px solid var(--rule); }}
.eyebrow {{ font-family: var(--mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 0 0 14px; }}
.masthead h1 {{ font-family: var(--display); font-weight: 700; font-size: clamp(34px, 5vw, 52px); line-height: 1.04;
  letter-spacing: -0.02em; margin: 0 0 16px; text-wrap: balance; max-width: 18ch; }}
.dek {{ font-size: 20px; line-height: 1.5; color: var(--muted); max-width: 60ch; margin: 0 0 28px; }}
.stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px 28px; margin: 0 0 28px; }}
.stat {{ display: flex; flex-direction: column; gap: 4px; padding-top: 12px; border-top: 2px solid var(--ink); }}
.stat-n {{ font-family: var(--display); font-weight: 700; font-size: 32px; line-height: 1; font-variant-numeric: tabular-nums; }}
.stat-l {{ font-family: var(--display); font-size: 14px; line-height: 1.35; color: var(--muted); }}
.status {{ font-family: var(--display); font-size: 14px; color: var(--muted); max-width: 80ch; margin: 0; }}

.charts {{ max-width: 1120px; margin-inline: auto; padding-block: 32px; display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 40px; border-bottom: 1px solid var(--rule); }}
.chart {{ margin: 0; }}
.chart figcaption {{ font-family: var(--display); font-weight: 600; font-size: 15px; margin-bottom: 14px; }}
.bars {{ display: grid; gap: 7px; }}
.bar-row {{ display: grid; grid-template-columns: 13.5rem minmax(0, 1fr) 2.6rem 5.4rem; gap: 10px; align-items: center; font-family: var(--display); font-size: 14px; }}
.bar-label {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bar-label a {{ text-decoration: none; }}
.track {{ position: relative; height: 12px; border-radius: 2px;
  background: linear-gradient(to right, transparent calc(25% - 0.5px), var(--rule) calc(25% - 0.5px), var(--rule) calc(25% + 0.5px), transparent calc(25% + 0.5px),
    transparent calc(50% - 0.5px), var(--rule) calc(50% - 0.5px), var(--rule) calc(50% + 0.5px), transparent calc(50% + 0.5px),
    transparent calc(75% - 0.5px), var(--rule) calc(75% - 0.5px), var(--rule) calc(75% + 0.5px), transparent calc(75% + 0.5px)), var(--track); }}
.fill {{ position: absolute; inset: 0 auto 0 0; background: var(--accent); border-radius: 2px; }}
.bar-val {{ font-family: var(--mono); font-size: 13px; text-align: right; font-variant-numeric: tabular-nums; }}
.bar-note {{ font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.axis {{ margin-top: 2px; }}
.ticks {{ position: relative; height: 16px; }}
.tick {{ position: absolute; top: 0; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; color: var(--muted); }}
.tick:first-child {{ transform: none; }}
.tick:last-child {{ transform: translateX(-100%); }}
.stack {{ display: flex; height: 22px; border-radius: 3px; overflow: hidden; background: var(--track); }}
.seg {{ display: block; height: 100%; }}
.seg + .seg {{ box-shadow: inset 1px 0 0 var(--surface); }}
.legend {{ list-style: none; margin: 14px 0 0; padding: 0; display: grid; gap: 6px; font-family: var(--display); font-size: 14px; }}
.legend li {{ display: grid; grid-template-columns: 12px minmax(0, 1fr) 2.5rem 3rem; gap: 10px; align-items: center; }}
.sw {{ width: 12px; height: 12px; border-radius: 2px; }}
.lg-n, .lg-s {{ font-family: var(--mono); font-size: 13px; text-align: right; font-variant-numeric: tabular-nums; }}
.lg-s {{ color: var(--muted); }}

.layout {{ max-width: 1120px; margin-inline: auto; display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 56px; padding-top: 40px; }}
.rail {{ position: sticky; top: 24px; align-self: start; font-family: var(--display); font-size: 14px; }}
.rail-h {{ font-family: var(--mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }}
.rail nav {{ display: grid; gap: 2px; }}
.rail a {{ display: flex; align-items: baseline; gap: 6px; color: var(--ink); text-decoration: none; padding: 4px 8px; border-radius: 3px; }}
.rail a:hover {{ background: var(--accent-soft); }}
.rail code {{ background: none; padding: 0; color: var(--accent); }}
.nav-n {{ margin-left: auto; font-family: var(--mono); font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }}

.report {{ min-width: 0; max-width: 46rem; }}
.report h2 {{ font-family: var(--display); font-weight: 700; font-size: 30px; line-height: 1.15; letter-spacing: -0.01em;
  margin: 8px 0 18px; text-wrap: balance; }}
.h-meta {{ display: block; margin-top: 6px; font-family: var(--mono); font-weight: 400; font-size: 13px; letter-spacing: 0; color: var(--muted); }}
.h-meta code {{ background: none; padding: 0; font-size: inherit; }}
.report h3 {{ font-family: var(--display); font-weight: 600; font-size: 21px; line-height: 1.25; margin: 36px 0 12px; text-wrap: balance; }}
.report h4 {{ font-family: var(--display); font-weight: 600; font-size: 17px; margin: 24px 0 8px; }}
.report p {{ margin: 0 0 14px; }}
.report ul, .report ol {{ margin: 0 0 16px; padding-left: 1.3em; }}
.report li {{ margin: 0 0 6px; }}
.report li > ul, .report li > ol {{ margin: 6px 0 0; }}
.report hr {{ border: 0; border-top: 1px solid var(--rule); margin: 48px 0 40px; }}
.report blockquote {{ margin: 0 0 16px; padding: 2px 0 2px 18px; border-left: 2px solid var(--rule); color: var(--muted); font-style: italic; }}
.table-wrap, .code-wrap {{ overflow-x: auto; margin: 4px 0 20px; }}
table {{ border-collapse: collapse; font-family: var(--display); font-size: 14px; line-height: 1.45; min-width: 100%; font-variant-numeric: tabular-nums; }}
th {{ text-align: left; font-weight: 600; font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted);
  padding: 8px 12px 8px 0; border-bottom: 1px solid var(--ink); vertical-align: bottom; }}
td {{ padding: 8px 12px 8px 0; border-bottom: 1px solid var(--rule); vertical-align: top; }}
td code {{ font-size: 0.86em; }}
pre {{ margin: 0; padding: 14px 16px; background: var(--code-bg); border-radius: 4px; }}
pre code {{ background: none; padding: 0; font-size: 13px; line-height: 1.5; }}

@media (max-width: 960px) {{
  .charts {{ grid-template-columns: minmax(0, 1fr); }}
  .layout {{ grid-template-columns: minmax(0, 1fr); gap: 24px; }}
  .rail {{ position: static; }}
  .rail nav {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .rail a {{ border: 1px solid var(--rule); }}
  .nav-n {{ margin-left: 4px; }}
  .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 560px) {{
  body {{ padding-inline: 16px; font-size: 16px; }}
  .bar-row {{ grid-template-columns: minmax(0, 1fr) 2.6rem; grid-template-areas: "label val" "track track" "note note"; gap: 4px 10px; }}
  .bar-label {{ grid-area: label; }} .track {{ grid-area: track; }} .bar-val {{ grid-area: val; }} .bar-note {{ grid-area: note; }}
  .axis {{ grid-template-columns: minmax(0, 1fr); grid-template-areas: "ticks"; }}
  .axis > span:not(.ticks) {{ display: none; }}
  .ticks {{ grid-area: ticks; }}
}}
</style>

<header class="masthead">
  <p class="eyebrow">SWEWorld · lumen (Opus 5) · world-hosted blind arm · g1–g11</p>
  <h1>What 100 rollouts reveal about the hidden requirements</h1>
  <p class="dek">Every transcript read against its task's answer key, remark by remark: what made each task hard, which clues go unfound, when a red herring actually works, and what to fix first.</p>
  <div class="stats">{stats}</div>
  <p class="status">{status}</p>
</header>

<section class="charts" aria-label="Headline charts">
  {chart1}
  {chart2}
</section>

<div class="layout">
  <aside class="rail">
    <p class="rail-h">Contents</p>
    <nav aria-label="Report sections">{nav}</nav>
  </aside>
  <article class="report">
{body}
  </article>
</div>
"""

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "rollout-audit.html"))
