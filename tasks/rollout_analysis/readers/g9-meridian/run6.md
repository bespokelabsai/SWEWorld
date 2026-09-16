# g9-meridian run 6 (49bfd4e7) — reward 0.8571

Six of seven weighted facts landed. The agent ran a competent, if noisy, search of chat, mail
and a handful of wiki pages, correctly rebuilt the tail-preserving windowing rule (r1), the
Fireworks byte-budget rule, the 16-token retained-prompt floor and its herring/reversal, the
`EncodingReport` dataclass shape, and the "only the batch entry points write `self.last_report`"
scope rule. It shipped, tests passed locally (120/120), and it pushed to CI.

The one miss, `g9.r2.failure_behavior`, is a real implementation bug, not a search failure that
happened to also be a coincidence of bad luck — although the underlying cause **is** a search
failure. `format_batch`'s shipped body (transcript lines 2719 and again 3369–3386, identical both
times) opens with an unconditional `self.last_report = EncodingReport()`, *before* the loop over
examples runs, and only reassigns the real value once at the very end. Only `ExampleTooLongError`
is caught inside the loop; `InvalidRoleSequenceError` and `TokenizerCapabilityError` correctly
propagate out of `format_batch` uncaught (the agent got that half right — see below). But because
the attribute was already zeroed at the top of the call, an abort leaves `self.last_report` reading
`EncodingReport()` (`[0,0,0,[],0]`) instead of whatever a prior successful batch had left behind
(`[1,1,1,[1],9]`) — exactly the failing assertion. The oracle instead accumulates into local
variables through the loop and assigns the attribute in one statement *after* the loop finishes, so
a mid-loop exception never touches it at all.

**Did the agent ever reason about this?** No. An exhaustive grep of every Analysis/Plan line for
"abort", "half updated", "632", "review note", "last good run", "previous report" returns nothing.
The agent's own reasoning about `self.last_report` covers only two things, both of which it got
right: that single-example `to_tinker_datum` calls must never touch it (line 2096, "Single-example
calls must not update last_report") and that both `format_batch` and `to_jsonl_lines` must reassign
it (line 2970, "Both batch methods now update last_report as required by mail"). It never
considered what an aborted batch should leave behind, because nothing it read ever raised the
question.

That gap traces to a genuine miss, not a red herring or overridden text. `g9.r2.l19` — the mail
thread "Re: Weekly update: week of Apr 7", where Dermot's review note on PR 632 states the rule
almost verbatim ("when the batch aborted halfway, self.last_report had already been half updated —
it should still read whatever the last good run left") — never surfaces in the transcript beyond
its bare subject line appearing three times in a `grep '^SUBJECT'` header dump (line 826–828). The
agent's two `sed` reads of `/tmp/mail.txt` covered only lines 131–197 of 231; this thread's body
sits outside that range. A later targeted IMAP re-fetch searched only for the literal terms
"Fireworks" or "EncodingReport", which this thread's language doesn't contain. Its two wiki-comment
carriers, `g9.r2.say24` and `g9.r2.l17`, fare no better: neither page's title matched either of the
two BookStack searches the agent ran ("encoding", "finetuning"), so neither was ever fetched, and
BookStack comments aren't indexed by search regardless. All three carriers of this half of the fact
were simply never seen.

Two related carriers, `g9.r2.l18` and `g9.r2.l16`, *were* found (or partly found) and did teach the
agent the adjacent, correctly-implemented half of the fact — that a bad role sequence or an unusable
tokenizer must abort the pass rather than being silently binned as a drop. `g9.r2.l16` is worth a
flag on its own: the text actually served in this world ("pulled the eval file this morning and the
tool role example isnt in it. dropped or never generated", line 2397) is markedly weaker than what
the answer key quotes for it, and never states that the row was wrongly counted as a drop — a likely
case of the corpus having drifted since this eval was captured.

No herring was followed. `g9.r1.h1` never appears as an independent hit; the agent only ever saw it
pre-debunked, embedded in its own reversal's chat dump. The other three herring/reversal pairs were
both seen together in the same channel dumps and resolved correctly. Wiki page 154 (carrier of
`g9.r1.l-fw-2`) is a clean "found but never opened" case — it was one of only two hits on the very
first wiki search, and the agent fetched the other hit but not this one — though it cost nothing
here since a sibling remark carried the same information.

Search strategy: Mattermost via targeted `/api/v4/posts/search` calls followed by full 200-post
channel dumps and broad OR-pattern greps over them (effective, but produces false-positive line
matches); BookStack via two title searches yielding six pages actually fetched out of roughly
fifteen comment-bearing pages that exist, since BookStack never indexes comments and several
relevant pages' titles didn't match either search term; mail via one large dump read only
two-thirds through, plus one narrowly-worded IMAP re-fetch. No crashes or truncated tooling — every
miss here is recall, not infrastructure.
