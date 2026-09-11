"""g7 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g7 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks this file to
0600 root, so the worker cannot read the numbers below to forge an observation
that matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection. The facts
that live ONLY here are the ones a worker must not see: the 186/189 byte counts,
the exact `turn_ledger.json` spelling, the eight sidecar key/values, the
completion-reason strings, `TURN_LEDGER_VERSION`, the sentinel token
`COMPLETION_SENTINEL` is graded against, and the `TurnLedgerDesyncError` message
format. The known fixture INPUTS (`SEED`, `SEEDER`, `PARTNER`, `SENTINEL`) are
restated here only to build the structures the assertions expect.
"""
from __future__ import annotations

import json
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# Fixture inputs, restated so the judge can build the expected structures.
SEEDER = "client"
PARTNER = "advisor"
SEED = "I need help with my investment strategy. What should I do?"
SENTINEL = "<<END_OF_CONVERSATION>>"
CLOCK_ISO = "2025-01-02T03:04:05"

EIGHT_KEYS = sorted({
    "version", "responses", "turns", "last_author", "next_speaker",
    "interleave_faults", "completed", "completion_reason",
})

# The exact bytes the first checkpoint holds, seed logged and no response yet.
OPENING_TEXT = (
    "{\n"
    '  "completed": false,\n'
    '  "completion_reason": "open",\n'
    '  "interleave_faults": 0,\n'
    '  "last_author": "client",\n'
    '  "next_speaker": "advisor",\n'
    '  "responses": 0,\n'
    '  "turns": 1,\n'
    '  "version": 2\n'
    "}\n"
)

# The sidecar the run leaves when the conversation ends on the agent signal.
DONE_STATE = {
    "version": 2,
    "responses": 3,
    "turns": 4,
    "last_author": PARTNER,
    "next_speaker": None,
    "interleave_faults": 0,
    "completed": True,
    "completion_reason": "agent_signal",
}

# The mid-run checkpoint of the r1-rule failed run: seed + two responses.
RULE_STATE = {
    "version": 2,
    "responses": 2,
    "turns": 3,
    "last_author": SEEDER,
    "next_speaker": PARTNER,
    "interleave_faults": 0,
    "completed": False,
    "completion_reason": "open",
}


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def is_true(got, msg=""):
    if got is not True:
        raise Fail(f"{msg}: {got!r} is not True")


def is_false(got, msg=""):
    if got is not False:
        raise Fail(f"{msg}: {got!r} is not False")


def is_none(got, msg=""):
    if got is not None:
        raise Fail(f"{msg}: {got!r} is not None")


def raised_named(info, name, msg=""):
    ok(info.get("raised"), f"{msg}: expected {name}, none raised")
    ok(name in info.get("mro", []), f"{msg}: {name} not in {info.get('mro')}")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["calls_names"], [PARTNER, SEEDER, PARTNER, SEEDER], "call order")
    eq(o["calls_task_ids"], [0, 1, 2, 3], "task ids")
    eq(o["n_calls"], 4, "call count")
    eq(o["n_lines"], 5, "log lines")
    eq(o["authors"], [SEEDER, PARTNER, SEEDER, PARTNER, SEEDER], "authors")

    s = o["seed"]
    eq(s["name"], SEEDER, "seed name")
    eq(s["response_message"], SEED, "seed message")
    eq(s["finish_reason"], "seed", "seed finish_reason")
    eq(s["response_cost"], 0.0, "seed cost")
    is_true(s["token_usage_is_none"], "seed token_usage")
    is_true(s["raw_response_is_none"], "seed raw_response")
    is_true(s["raw_request_is_none"], "seed raw_request")
    is_true(s["parsed_is_none"], "seed parsed")
    is_true(s["errors_is_none"], "seed errors")
    eq(s["created_iso"], CLOCK_ISO, "seed created_at")
    eq(s["finished_iso"], CLOCK_ISO, "seed finished_at")
    is_true(s["created_eq_finished"], "seed created==finished")
    eq(s["gr_model"], "gpt-4o-mini", "seed request model")
    eq(s["gr_messages"], [{"role": "user", "content": SEED}], "seed request messages")
    eq(s["gr_original_row"], {"prompt": SEED}, "seed original_row")
    eq(s["gr_original_row_idx"], 0, "seed original_row_idx")

    lg = o["ledger"]
    eq(lg["responses"], 4, "ledger responses")
    eq(lg["turns"], 5, "ledger turns")
    eq(lg["last_author"], SEEDER, "ledger last_author")
    is_none(lg["next_speaker"], "ledger next_speaker")
    eq(lg["interleave_faults"], 0, "ledger interleave_faults")
    is_true(lg["completed"], "ledger completed")
    eq(lg["completion_reason"], "budget", "ledger completion_reason")
    is_true(lg["entries_is_tuple"], "ledger entries is tuple")
    is_true(lg["messages_eq_history"], "ledger.messages() == conversation_history")
    eq(o["history0"], {"role": SEEDER, "content": SEED}, "history[0]")

    tr = o["tracker"]
    eq(tr["max_turns"], 4, "max_turns")
    eq(tr["current_turn"], 4, "current_turn")
    eq(tr["num_responses"], 4, "num_responses")
    eq(tr["num_cached"], 0, "num_cached")
    eq(tr["num_errors"], 0, "num_errors")

    eq(o["columns"], ["content", "role", "source", "turn"], "dataset columns")
    eq(o["n_rows"], 5, "row count")
    eq(o["row0"], {"role": SEEDER, "content": SEED, "turn": 0, "source": "seed"}, "row 0")
    eq(o["turns_col"], [0, 1, 2, 3, 4], "turn column")
    eq(o["sources_col"], ["seed"] + ["response"] * 4, "source column")
    eq(o["roles_col"], o["authors_after"], "role column == authors")

    eq(o["resume_calls"], [[PARTNER, 2], [SEEDER, 3]], "resume calls")
    eq(o["resume_n_calls"], 2, "resume call count")
    eq(o["resume_lines"], 5, "resume log lines")
    eq(o["resume_responses"], 4, "resume ledger responses")
    eq(o["resume_n_rows"], 5, "resume rows")
    eq(o["resume_num_cached"], 2, "resume num_cached")
    eq(o["resume_num_responses"], 2, "resume num_responses")
    eq(o["resume_current_turn"], 4, "resume current_turn")

    eq(o["bare_n_calls"], 1, "bare call count")
    eq(o["bare_lines"], 2, "bare log lines")
    eq(o["bare_n_rows"], 2, "bare rows")


# ---------------------------------------------------------------------------
# r1 — the checkpoint beside the log
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["filename"], "turn_ledger.json", "TURN_LEDGER_FILENAME")
    eq(o["version"], 2, "TURN_LEDGER_VERSION")
    raised_named(o["run_raises"], "Boom", "run dies on third call")
    eq(o["authors"], [SEEDER, PARTNER, SEEDER], "authors after failure")
    is_true(o["exists"], "checkpoint written before failure")
    eq(o["state_keys"], EIGHT_KEYS, "sidecar keys")
    eq(o["state"], RULE_STATE, "sidecar state")
    eq(o["sidecar_state"], RULE_STATE, "ledger.sidecar_state()")
    is_true(o["returned_is_abs"], "write_sidecar returns absolute path")
    is_true(o["returned_realpath_eq"], "write_sidecar returns the checkpoint path")
    eq(o["written"], RULE_STATE, "write_sidecar wrote the state")


def judge_r1_scope(o):
    eq(o["statuses"], ["adopted", "created", "verified"], "LEDGER_STATUSES")
    eq(o["adopted_status"], "adopted", "log-only status")
    eq(o["adopted_responses"], 2, "log-only responses")
    is_true(o["listing_unchanged"], "load_ledger wrote nothing")
    v = o["verified"]
    eq(v["status"], "verified", "verified status")
    eq(v["turns"], 3, "log turns beat the lie")
    eq(v["responses"], 2, "log responses")
    eq(v["next_speaker"], PARTNER, "log next_speaker")
    eq(v["interleave_faults"], 0, "log interleave_faults")
    is_false(v["completed"], "log completed")
    eq(v["completion_reason"], "open", "log completion_reason")
    is_true(o["sidecar_untouched"], "sidecar bytes untouched")
    is_true(o["log_untouched"], "log bytes untouched")
    eq(o["authors"], [SEEDER, PARTNER, SEEDER], "authors untouched")
    raised_named(o["fresh_run_raises"], "Boom", "fresh run dies on first call")
    eq(o["fresh_status"], "created", "fresh-run ledger status")


def judge_r1_failure_behavior(o):
    ok("TurnLedgerError" in o["desync_mro"], "TurnLedgerDesyncError subclasses TurnLedgerError")
    ok("RuntimeError" in o["base_mro"], "TurnLedgerError subclasses RuntimeError")
    is_true(o["desync_sub_base"], "desync subclasses base")
    is_true(o["base_sub_runtime"], "base subclasses RuntimeError")

    eq(o["absent_status"], "adopted", "absent -> adopted")
    eq(o["unreadable_status"], "adopted", "unreadable -> adopted")
    eq(o["oldversion_status"], "adopted", "old version -> adopted")
    eq(o["agree_status"], "verified", "agree -> verified")

    dr = o["desync_responses"]
    raised_named(dr, "TurnLedgerDesyncError", "response mismatch")
    eq(dr["log_responses"], 2, "log_responses")
    eq(dr["recorded_responses"], 1, "recorded_responses")
    eq(dr["log_last_author"], SEEDER, "log_last_author")
    eq(dr["recorded_last_author"], SEEDER, "recorded_last_author")
    is_true(dr["path_realpath_eq"], "error.path is the checkpoint")
    expected_str = (
        f"{dr['path']} records 1 response(s) last authored by {SEEDER!r}, "
        f"the log holds 2 last authored by {SEEDER!r}"
    )
    eq(dr["str"], expected_str, "desync message")

    da = o["desync_author"]
    raised_named(da, "TurnLedgerDesyncError", "author mismatch")
    eq(da["log_last_author"], SEEDER, "author mismatch log_last_author")
    eq(da["recorded_last_author"], PARTNER, "author mismatch recorded_last_author")
    eq(da["log_responses"], 2, "author mismatch log_responses")
    eq(da["recorded_responses"], 2, "author mismatch recorded_responses")

    raised_named(o["run_raises"], "TurnLedgerDesyncError", "desync raised on the load path")
    eq(o["run_calls"], [], "nothing asked")
    eq(o["run_lines"], 3, "nothing appended")


def judge_r1_observability(o):
    raised_named(o["opening_run_raises"], "Boom", "opening run dies on first call")
    is_true(o["opening_exists"], "seed checkpointed before first request")
    eq(o["opening_text"], OPENING_TEXT, "opening checkpoint spelling")
    eq(o["opening_size"], 186, "opening checkpoint is 186 bytes")

    eq(o["done_lines"], 4, "done log lines")
    eq(o["done_size"], 189, "done checkpoint is 189 bytes")
    eq(o["done_state"], DONE_STATE, "done checkpoint state")

    sr = o["stale_raises"]
    raised_named(sr, "TurnLedgerDesyncError", "stale log desync")
    is_true(sr["path_realpath_eq"], "stale error.path is the checkpoint")
    eq(sr["log_responses"], 2, "stale log_responses")
    eq(sr["recorded_responses"], 3, "stale recorded_responses")
    eq(sr["log_last_author"], SEEDER, "stale log_last_author")
    eq(sr["recorded_last_author"], PARTNER, "stale recorded_last_author")
    eq(o["stale_calls"], [], "stale asks nothing")
    eq(o["stale_lines"], 3, "stale appends nothing")

    eq(o["nockpt_status"], "adopted", "no checkpoint -> adopted")
    eq(o["nockpt_calls"], [[PARTNER, 2]], "resume asks one")
    eq(o["nockpt_lines"], 4, "resume completes the log")

    eq(o["older_status"], "adopted", "old-version checkpoint -> adopted")


# ---------------------------------------------------------------------------
# r2 — the default completion signal
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    eq(o["completion_sentinel"], SENTINEL, "COMPLETION_SENTINEL")
    is_true(o["ends_with"], "reply ending with the sentinel completes")
    is_true(o["exact"], "the bare sentinel completes")
    is_false(o["plain"], "a plain reply does not complete")


def judge_r2_scope(o):
    is_true(o["feature"], "Agent.is_completed's default sentinel match is not implemented")
    is_true(o["trailing_space_newline"], "trailing space/newline ignored")
    is_true(o["trailing_tab"], "trailing tab ignored")
    is_false(o["prefix_then_more"], "sentinel must be a suffix")
    is_false(o["lowercased"], "match is case-sensitive")
    is_false(o["plain"], "a plain reply does not complete")


def judge_r2_failure_behavior(o):
    is_true(o["feature"], "Agent.is_completed's default sentinel match is not implemented")
    is_false(o["dict"], "a structured reply answers False")
    is_false(o["none"], "None answers False")
    is_false(o["list"], "a list answers False")
    is_false(o["int"], "an int answers False")


def judge_r2_observability(o):
    is_true(o["feature"], "Agent.is_completed's default sentinel match is not implemented")
    eq(o["n_calls"], 3, "three calls")
    eq(o["n_lines"], 4, "four log lines")
    eq(o["num_responses"], 3, "num_responses")
    eq(o["ledger_responses"], 3, "ledger responses")
    eq(o["completion_reason"], "agent_signal", "completion_reason")
    is_true(o["completed"], "ledger completed")
    eq(o["n_rows"], 4, "dataset rows")
    eq(o["last_content"], f"Then index funds. {SENTINEL}", "last message content")
    is_true(o["last_content_is_sentinel_msg"], "last message is the sentinel-bearing reply")
    eq(o["last_role"], PARTNER, "last message role")


JUDGES = {
    "test_open::test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses": judge_open,
    "test_r1::test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response": judge_r1_rule,
    "test_r1::test_scope__load_ledger_writes_nothing_and_the_log_outranks_the_checkpoint": judge_r1_scope,
    "test_r1::test_failure_behavior__absent_or_old_is_adopted_and_a_disagreeing_one_aborts": judge_r1_failure_behavior,
    "test_r1::test_observability__the_checkpoint_reads_186_bytes_mid_run_and_189_at_the_end": judge_r1_observability,
    "test_r2::test_rule__the_sentinel_is_the_end_of_conversation_token": judge_r2_rule,
    "test_r2::test_scope__matching_is_case_sensitive_suffix_only_and_ignores_trailing_space": judge_r2_scope,
    "test_r2::test_failure_behavior__a_structured_or_missing_reply_answers_false": judge_r2_failure_behavior,
    "test_r2::test_observability__the_message_that_ends_the_talk_is_still_a_turn": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g7_agent_turn_ledger" '
             f'tests="{len(results)}" failures="{fails}" errors="0">']
    for classname, name, failure in results:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)}>'
        if failure:
            lines.append(head + f'<failure message={quoteattr(failure[:200])}>'
                         + escape(failure[:4000]) + '</failure></testcase>')
        else:
            lines.append(head + '</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def main(obs_path: str, out_path: str) -> int:
    try:
        observations = json.loads(pathlib.Path(obs_path).read_text())
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if probe is None:
            results.append((classname, name, "no observation from probe"))
            continue
        if not probe.get("ok"):
            results.append((classname, name, f"probe error: {probe.get('error', 'unknown')}"))
            continue
        try:
            judge(probe["obs"])
            results.append((classname, name, ""))
        except Fail as exc:
            results.append((classname, name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - a malformed observation is a failed fact, not a crash
            results.append((classname, name, f"judge error: {type(exc).__name__}: {exc}"))

    pathlib.Path(out_path).write_text(junit(results))
    for classname, name, failure in results:
        print(f"{'FAIL' if failure else 'pass'} {classname}::{name}"
              + (f"  {failure[:160]}" if failure else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
