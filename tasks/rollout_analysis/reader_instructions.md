# Reader instructions — one rollout against its answer key

You are auditing ONE agent rollout (an AI coding agent solving a task inside a simulated company
"world") against the task's answer key. Read-only analysis: do NOT edit anything under
/home/nidhi_bespokelabs_ai/SWEWorld. Write only your two output files. Your prompt gives you the
task id, the fact list and every path.

## Background
The agent got a ticket (the transcript's first [user] message) stating a feature openly. The
task's HIDDEN requirements (`<task>.r1`, `<task>.r2`) are written down nowhere; they were planted
as ~35-60 scattered "remarks" across Mattermost chat, BookStack wiki (pages and page *comments* —
BookStack search does not index comments), and mail. Some remarks are **herrings** (a decision
later reversed) with a later **reversal**. The grader tests each hidden requirement as separate
facts — some of rule / scope / exclusions_or_crossover / failure_behavior / observability; your
prompt lists exactly which facts this task declares. `reward` = mean of those facts.

Transcript format: `## [assistant]` turns contain `Analysis:` and `Plan:` — that is the agent's
REASONING; `## [tool]` turns contain terminal output (the commands it typed appear after `$ `).
If a file the agent wrote is only visible as a heredoc, the full rollout JSON (path in your
prompt) holds the raw tool calls.

## Files (paths are in your prompt)
- Transcript — THE thing to read.
- Pointer sheet — graded facts, full failing-test traces, and a mechanical table of where each
  remark's exact text surfaces (first step, transcript line, the command that surfaced it). A
  POINTER ONLY: it can miss re-wrapped text and cannot tell whether the agent understood anything.
- Answer key — hidden requirements, herrings, and "Where every remark is": every remark with its
  location, kind, facts it carries, identifiers that must be typed literally, and the exchange
  quoted exactly as it appears. IGNORE its "measured" column (fabricated). **The key in the repo
  can be newer than the world this rollout ran against** (corpus fixes are sometimes made locally
  after an eval). If the key's quote of a remark differs from what the transcript shows the world
  served, judge the agent against what it actually saw, and record the difference in `notable`.
- Grader (test_r1.py / test_r2.py) and reference solution (oracle.patch).
- Plant record (per remark `settles`, `forbidden_terms`, `carrier`).

## What to do
Read the transcript for real — especially every Analysis/Plan — against the answer key. Use the
pointer sheet to jump to locations, and for every remark the sheet marks as not surfaced, grep
the transcript yourself for its distinctive phrases and literal identifiers before concluding
"no". Determine what code the agent finally shipped (file writes / diffs / final cat of files) to
judge whether it acted on each remark.

Before you claim something is or is not in the ticket, grep the ticket text for it. Before you
claim a remark is the only carrier of something, check the plant record.

For EVERY remark in the answer key produce a row:
- found: "yes" | "partial" (only a fragment was in view, e.g. cut by `| head`, or a search snippet) | "no"
- step and transcript line where first seen; how: the exact search query / channel dump / page
  fetch / mail read that surfaced it, or "stumbled" if incidental
- near_miss (if not found): e.g. a search returned the page but it was never opened, comments
  never fetched, output truncated, wrong date window, keyword list lacked the remark's wording
- registered: "requirement" | "noted" | "dismissed" | "missed_point" (saw it, drew the wrong or
  no inference) | "n/a"
- agent_quote: verbatim Analysis/Plan text where the agent reasons about this remark (≤300
  chars), with its transcript line
- acted: "followed" | "contradicted" | "partly" | "n/a" — judged against the shipped code

For EVERY herring: saw_herring, saw_reversal (yes/no + line), believed ("herring" | "reversal" |
"neither" | "unclear"), quote of the reasoning, shipped code followed herring (true/false/null).
Use the bare remark ids for `herring` and `reversal` (e.g. "g3.r1.h1"), no descriptions.

For EVERY fact that scored 0: the failing assertion (from the pointer sheet trace), and ONE cause:
- "not_found"
- "found_misread"
- "herring_followed"
- "overridden_by_other_corpus_text" — the agent found the right remark but other text in the
  world (often the invented conversation around a planted remark, or another remark) argued the
  graded question the other way and it went with that; quote both. This is a TASK DEFECT.
- "grader_overspecifies" — the world never pins what the test asserts (verify by grepping)
- "implementation_slip" — its own reasoning states the rule and the code does otherwise
- "infra" — ONLY a harness/model/environment failure (empty model replies, trial did not
  complete, nothing pushed because the run died). A corpus contradiction is never infra.
Give evidence (transcript lines, remark ids, quotes).
For EVERY fact that scored 1: which remark(s) the agent actually relied on (quote), or "ticket" /
"guess" if it got it without any remark.

If the whole run scored 0 or has no fact grades, first establish why from its final turns and the
pointer sheet (nothing pushed? CI red? provenance failed? run died?) and say so in `end_reason`.

Also characterise its search strategy (how it searched chat / wiki / mail; did it enumerate pages
whole, fetch comments, read mail; did truncation or a crashed helper script hurt).

## Output (write both; exact paths are in your prompt)
1. JSON:
{"task":"gN","run":N,"eval":"xxxxxxxx","rollout_id":"xxxxxxxx","reward":..., "facts":{"gN.r1.rule":0|1, ...},
 "remarks":[{"id","kind","carries","found","step","line","how","near_miss","registered","agent_quote","quote_line","acted","note"}],
 "herrings":[{"herring","reversal","saw_herring","saw_reversal","believed","quote","code_followed_herring"}],
 "lost_facts":[{"fact","assertion","cause","evidence","remarks"}],
 "passed_facts":[{"fact","relied_on","quote"}],
 "search_strategy":"...", "end_reason":"...", "notable":["short findings worth reporting, each with a line ref"]}
   Use the fact names exactly as the task declares them (e.g. "g3.r1.rule").
2. Markdown: a half-page narrative — what this run found, what it missed and why, what it
   believed and why, why each lost fact was lost.

Be precise and evidence-based; every claim cites a transcript line. Final reply: 5 lines max
summarising lost facts and causes.
