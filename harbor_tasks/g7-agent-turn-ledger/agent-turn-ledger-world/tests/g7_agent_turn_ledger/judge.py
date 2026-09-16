"""g7 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
actually ran in, and the cloned source text; writes a `junit.xml` whose
`classname`/`name` are the suite's node ids — so `score.py` folds them into the
fact keys and `test.sh`/`score.py` are unchanged. It runs as root; the worker
cannot read it, because `test.sh` keeps /tests root-only for a split suite and
the worker's jail holds only `probe.py`, `probe_support.py`, `fixture_spec.py`
and `harness.py`.

WHY THE ANSWERS HERE ARE NOT ENOUGH ON THEIR OWN. Keeping this file unreadable
stopped the worker copying the expected values out of it. It did not stop the
worker writing them anyway: the old fixture was the same every run, so a capture
of one correct run replayed onto a tree that implemented nothing scored 1.0 on
every hidden fact, and a constant file of booleans passed r2.scope and
r2.failure_behavior. Three things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the agent
    names, where a run dies, how long a log is, what a lying checkpoint claims
    and three shuffled lists of candidate replies, and this file works out what
    the answers must be for THOSE inputs;
  * **the directories are read here.** The checkpoint's bytes, the log's lines,
    whether loading wrote anything: this process opens the scenario directories
    under the artifacts root and compares them against what it expects, rather
    than trusting a flag the worker chose;
  * **the constants that cannot be re-drawn are read out of the source** as well
    as the run: `TURN_LEDGER_FILENAME`, `TURN_LEDGER_VERSION`,
    `COMPLETION_SENTINEL`.

The residual, stated plainly: a submission that implements the requirement inside
a forged hook — computing, from `fixture_spec`, what a correct implementation
would have written — still passes, because it has then done the work. What is
gone is passing by repeating values that were knowable in advance.

`test_r1`/`test_r2` stay the human-readable reference for what each fact means;
their worked example uses the old fixed fixture ("client"/"advisor").
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import stat
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used

# ---- the answers the hidden requirements fix, which cannot be re-drawn ------
SIDECAR = "turn_ledger.json"
LEDGER_VERSION = 2
SENTINEL = "<<END_OF_CONVERSATION>>"
STATUSES = ["adopted", "created", "verified"]
EIGHT_KEYS = sorted({
    "version", "responses", "turns", "last_author", "next_speaker",
    "interleave_faults", "completed", "completion_reason",
})

# ---- fixture inputs the open feature states ---------------------------------
SEED = "I need help with my investment strategy. What should I do?"
LOG = fixture_spec.LOG
CLOCK_ISO = fixture_spec.CLOCK_ISO

# Where `sym` looks for a module-level name, as source files.
SYMBOL_FILES = ("bespokelabs/curator/agent", "bespokelabs/curator/status_tracker/agent_status_tracker.py",
                "bespokelabs/curator/__init__.py")

SPEC: dict = {}
ARTIFACTS = pathlib.Path("/nonexistent")


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


def raised_named(info, name, msg=""):
    ok(isinstance(info, dict) and info.get("raised"), f"{msg}: expected {name}, none raised")
    ok(name in (info.get("mro") or []), f"{msg}: {name} not in {info.get('mro')} ({info.get('str', '')[:200]})")


def value_of(step, msg):
    """The value of a probe step recorded with `attempt`, or the step's failure."""
    ok(isinstance(step, dict), f"{msg}: not measured")
    ok("error" not in step, f"{msg}: {step.get('error')}")
    return step.get("value")


# ---------------------------------------------------------------------------
# the expected run, from the seed
# ---------------------------------------------------------------------------
def seeder():
    return SPEC["seeder"]


def partner():
    return SPEC["partner"]


def author_of_line(i):
    """Line 0 is the seed, by the seeder; the two take turns from there."""
    return seeder() if i % 2 == 0 else partner()


def other(name):
    return partner() if name == seeder() else seeder()


def open_state(responses):
    """A checkpoint mid-run: `responses` generated, nothing finished."""
    last = author_of_line(responses)
    return {"version": LEDGER_VERSION, "responses": responses, "turns": responses + 1,
            "last_author": last, "next_speaker": other(last), "interleave_faults": 0,
            "completed": False, "completion_reason": "open"}


def spelled(state):
    return json.dumps(state, indent=2, sort_keys=True) + "\n"


def completes(value):
    return isinstance(value, str) and value.rstrip().endswith(SENTINEL)


# ---------------------------------------------------------------------------
# reading what the scenarios left, as root, without trusting it
# ---------------------------------------------------------------------------
def _safe_path(rel: str) -> pathlib.Path:
    """ARTIFACTS/rel, refusing a symlink anywhere below the artifacts root.

    The worker owns these directories, so any entry can be a symlink by the time
    root reads it — pointing at /opt/world-state or at a file planted before the
    run. `lstat` every component and open with O_NOFOLLOW.
    """
    ok(".." not in pathlib.PurePosixPath(rel).parts and not rel.startswith("/"), f"bad path {rel!r}")
    path = ARTIFACTS
    for part in pathlib.PurePosixPath(rel).parts:
        path = path / part
        try:
            st = os.lstat(path)
        except OSError:
            raise Fail(f"{rel}: does not exist")
        ok(not stat.S_ISLNK(st.st_mode), f"{rel}: is a symlink")
    return path


def read_bytes(rel: str) -> bytes:
    path = _safe_path(rel)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise Fail(f"{rel}: {exc}")
    try:
        st = os.fstat(fd)
        ok(stat.S_ISREG(st.st_mode), f"{rel}: not a regular file")
        ok(st.st_size <= 4 * 1024 * 1024, f"{rel}: too large")
        with os.fdopen(fd, "rb") as fh:
            return fh.read()
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def exists(rel: str) -> bool:
    try:
        read_bytes(rel)
        return True
    except Fail:
        return False


def text_of(rel: str) -> str:
    return read_bytes(rel).decode("utf-8", errors="replace")


def json_of(rel: str):
    try:
        return json.loads(read_bytes(rel))
    except ValueError as exc:
        raise Fail(f"{rel}: not JSON: {exc}")


def listing(dirrel: str) -> list:
    path = _safe_path(dirrel)
    ok(path.is_dir(), f"{dirrel}: not a directory")
    return sorted(os.listdir(path))


def log_rows(dirrel: str) -> list:
    """[(name, response_message)] for every non-blank line of a scenario's log."""
    out = []
    for line in text_of(f"{dirrel}/{LOG}").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            raise Fail(f"{dirrel}/{LOG}: a line is not JSON")
        out.append((record.get("name"), record.get("response_message")))
    return out


def same_file(recorded, rel: str, msg: str):
    ok(isinstance(recorded, str) and recorded, f"{msg}: no path recorded ({recorded!r})")
    eq(os.path.realpath(recorded), os.path.realpath(str(ARTIFACTS / rel)), msg)


def plain_name(name, msg):
    ok(isinstance(name, str) and name and os.path.basename(name) == name
       and name not in (".", "..") and name != LOG,
       f"{msg}: no checkpoint name to plant under ({name!r}) — the submission neither "
       "exports the constant nor leaves a single file beside a fresh run's log")


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
def _symbol_sources():
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in SYMBOL_FILES:
        path = root / rel
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if file.is_file() and not file.is_symlink():
                yield file.read_text(errors="replace")


def defined(name: str, expected):
    """The module-level assignment of `name` somewhere `sym` looks, checked
    against `expected` when it is a literal.

    A non-literal assignment is accepted here and left to the runtime value the
    probe reported; what fails is a tree that REPORTS the constant without
    defining it at all, or defines it as a different literal.
    """
    seen = False
    for src in _symbol_sources():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                seen = True
                try:
                    literal = ast.literal_eval(value)
                except ValueError:
                    continue
                eq(literal, expected, f"{name} as written in the source")
    ok(seen, f"no module of bespokelabs.curator.agent assigns {name}")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    S_, P_ = seeder(), partner()
    eq(o["calls_names"], [P_, S_, P_, S_], "call order")
    eq(o["calls_task_ids"], [0, 1, 2, 3], "task ids")
    eq(o["n_calls"], 4, "call count")
    eq(o["n_lines"], 5, "log lines")
    eq(o["authors"], [S_, P_, S_, P_, S_], "authors")

    s = o["seed"]
    eq(s["name"], S_, "seed name")
    eq(s["response_message"], SEED, "seed message")
    eq(s["finish_reason"], "seed", "seed finish_reason")
    eq(s["response_cost"], 0.0, "seed cost")
    for key in ("token_usage_is_none", "raw_response_is_none", "raw_request_is_none",
                "parsed_is_none", "errors_is_none", "created_eq_finished"):
        is_true(s[key], f"seed {key}")
    eq(s["created_iso"], CLOCK_ISO, "seed created_at")
    eq(s["finished_iso"], CLOCK_ISO, "seed finished_at")
    eq(s["gr_model"], "gpt-4o-mini", "seed request model")
    eq(s["gr_messages"], [{"role": "user", "content": SEED}], "seed request messages")
    eq(s["gr_original_row"], {"prompt": SEED}, "seed original_row")
    eq(s["gr_original_row_idx"], 0, "seed original_row_idx")

    lg = o["ledger"]
    eq(lg["responses"], 4, "ledger responses")
    eq(lg["turns"], 5, "ledger turns")
    eq(lg["last_author"], S_, "ledger last_author")
    eq(lg["next_speaker"], None, "ledger next_speaker")
    eq(lg["interleave_faults"], 0, "ledger interleave_faults")
    is_true(lg["completed"], "ledger completed")
    eq(lg["completion_reason"], "budget", "ledger completion_reason")
    is_true(lg["entries_is_tuple"], "ledger entries is tuple")
    is_true(lg["messages_eq_history"], "ledger.messages() == conversation_history")
    eq(o["history0"], {"role": S_, "content": SEED}, "history[0]")

    tr = o["tracker"]
    eq(tr["max_turns"], 4, "max_turns")
    eq(tr["current_turn"], 4, "current_turn")
    eq(tr["num_responses"], 4, "num_responses")
    eq(tr["num_cached"], 0, "num_cached")
    eq(tr["num_errors"], 0, "num_errors")

    eq(o["columns"], ["content", "role", "source", "turn"], "dataset columns")
    eq(o["n_rows"], 5, "row count")
    eq(o["row0"], {"role": S_, "content": SEED, "turn": 0, "source": "seed"}, "row 0")
    eq(o["turns_col"], [0, 1, 2, 3, 4], "turn column")
    eq(o["sources_col"], ["seed"] + ["response"] * 4, "source column")
    eq(o["roles_col"], o["authors_after"], "role column == authors")

    eq(o["resume_calls"], [[P_, 2], [S_, 3]], "resume calls")
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
    eq(o["filename"], SIDECAR, "TURN_LEDGER_FILENAME")
    defined("TURN_LEDGER_FILENAME", SIDECAR)
    eq(o["version"], LEDGER_VERSION, "TURN_LEDGER_VERSION")
    defined("TURN_LEDGER_VERSION", LEDGER_VERSION)
    for name in ("read_sidecar", "write_sidecar", "verify_sidecar"):
        is_true(o["functions"].get(name), f"{name} is exported")

    die_on = SPEC["rule_die_on"]
    raised_named(o["run_raises"], "Boom", f"the run dies on call {die_on}")
    responses = die_on - 1
    expected = open_state(responses)
    eq([name for name, _ in log_rows("r1_rule_run")],
       [author_of_line(i) for i in range(die_on)], "authors in the log when the run died")

    # Written before the failure, so written after a response and not at the end.
    ok(exists(f"r1_rule_run/{SIDECAR}"),
       f"no {SIDECAR} beside the log when the run died after {responses} response(s); "
       f"the directory held {listing('r1_rule_run')}")
    on_disk = json_of(f"r1_rule_run/{SIDECAR}")
    ok(isinstance(on_disk, dict), "the checkpoint is not a JSON object")
    eq(sorted(on_disk), EIGHT_KEYS, "checkpoint keys")
    eq(on_disk, expected, "the checkpoint the failed run left")
    eq(value_of(o["read_sidecar"], "read_sidecar"), expected, "read_sidecar(working_dir)")
    eq(value_of(o["sidecar_state"], "ledger.sidecar_state()"), expected, "ledger.sidecar_state()")

    returned = value_of(o["write_returned"], "write_sidecar")
    ok(isinstance(returned, str) and os.path.isabs(returned),
       f"write_sidecar returns an absolute path: {returned!r}")
    same_file(returned, f"r1_rule_write/{SIDECAR}", "write_sidecar returns the checkpoint's path")
    eq(json_of(f"r1_rule_write/{SIDECAR}"), expected, "what write_sidecar put on disk")


def judge_r1_scope(o):
    eq(o["statuses"], STATUSES, "LEDGER_STATUSES")
    contents = SPEC["scope_contents"]
    rows = fixture_spec.alternating(seeder(), partner(), contents)
    log_bytes = fixture_spec.log_text(rows).encode()
    responses = len(contents) - 1
    last = author_of_line(responses)

    # No checkpoint: the log alone, and reading it wrote nothing.
    eq(o["adopted_status"], "adopted", "log-only status")
    eq(o["adopted_responses"], responses, "log-only responses")
    eq(listing("r1_scope_adopted"), [LOG], "load_ledger wrote to the directory")
    eq(read_bytes(f"r1_scope_adopted/{LOG}"), log_bytes, "the log after a log-only load")

    # A checkpoint that agrees on the two compared keys and lies about the rest.
    name = o["planted_name"]
    plain_name(name, "r1.scope")
    lies = SPEC["scope_lies"]
    planted = json.loads(o["planted_text"])
    eq([planted.get("responses"), planted.get("last_author")], [responses, last],
       "the planted checkpoint agrees on responses and last_author")
    eq({k: planted.get(k) for k in lies}, lies, "the planted checkpoint carries this run's lies")

    v = o["agreeing"]
    ok("error" not in v, f"loading beside an agreeing checkpoint: {v.get('error')}")
    eq(v["status"], "verified", "status beside an agreeing checkpoint")
    eq(v["turns"], len(contents), "turns come from the log, not the checkpoint")
    eq(v["responses"], responses, "responses from the log")
    eq(v["last_author"], last, "last_author from the log")
    eq(v["next_speaker"], other(last), "next_speaker from the log, not the checkpoint")
    eq(v["interleave_faults"], 0, "interleave_faults from the log")
    is_false(v["completed"], "completed from the log")
    eq(v["completion_reason"], "open", "completion_reason from the log")

    eq(listing("r1_scope_verified"), sorted([LOG, name]), "load_ledger wrote to the directory")
    eq(text_of(f"r1_scope_verified/{name}"), o["planted_text"], "the checkpoint was rewritten on load")
    eq(read_bytes(f"r1_scope_verified/{LOG}"), log_bytes, "the log was rewritten to agree with the checkpoint")

    raised_named(o["fresh_run_raises"], "Boom", "fresh run dies on its first call")
    eq(o["fresh_status"], "created", "a fresh run's ledger status")


def judge_r1_failure_behavior(o):
    ok(o["desync_mro"] is not None, "TurnLedgerDesyncError is not exported")
    ok(o["base_mro"] is not None, "TurnLedgerError is not exported")
    ok("TurnLedgerError" in o["desync_mro"], "TurnLedgerDesyncError subclasses TurnLedgerError")
    ok("RuntimeError" in o["base_mro"], "TurnLedgerError subclasses RuntimeError")

    contents = SPEC["fail_contents"]
    responses = len(contents) - 1
    last = author_of_line(responses)
    name = o["planted_name"]
    plain_name(name, "r1.failure_behavior")

    eq(o["absent_status"], "adopted", "absent checkpoint")
    eq(o["unreadable_status"], "adopted", "unreadable checkpoint")
    ok(o["old_moved"], "could not plant an older-version checkpoint: the build records no "
                       "integer beside the ledger's own fields")
    eq(o["oldversion_status"], "adopted", "older-version checkpoint")
    eq(o["agree_status"], "verified", "agreeing checkpoint")

    recorded = SPEC["fail_recorded_responses"]
    dr = o["desync_responses"]
    raised_named(dr, "TurnLedgerDesyncError", "response-count mismatch")
    eq(dr.get("log_responses"), responses, "log_responses")
    eq(dr.get("recorded_responses"), recorded, "recorded_responses")
    eq(dr.get("log_last_author"), last, "log_last_author")
    eq(dr.get("recorded_last_author"), last, "recorded_last_author")
    same_file(dr.get("path"), f"r1_fail/{name}", "error.path is the checkpoint")
    eq(dr.get("str"),
       f"{dr.get('path')} records {recorded} response(s) last authored by {last!r}, "
       f"the log holds {responses} last authored by {last!r}", "desync message")

    da = o["desync_author"]
    raised_named(da, "TurnLedgerDesyncError", "last-author mismatch")
    eq(da.get("log_last_author"), last, "author mismatch log_last_author")
    eq(da.get("recorded_last_author"), other(last), "author mismatch recorded_last_author")
    eq(da.get("log_responses"), responses, "author mismatch log_responses")
    eq(da.get("recorded_responses"), responses, "author mismatch recorded_responses")

    raised_named(o["run_raises"], "TurnLedgerDesyncError", "desync raised on the load path")
    eq(o["run_calls"], [], "a request was issued before the desync was raised")
    eq(len(log_rows("r1_fail")), len(contents), "a line was appended before the desync was raised")


def judge_r1_observability(o):
    # ---- the first write --------------------------------------------------
    raised_named(o["opening_run_raises"], "Boom", "opening run dies on its first call")
    ok(exists(f"r1_obs_opening/{SIDECAR}"),
       f"the seed line was not checkpointed before the first request: the directory "
       f"held {listing('r1_obs_opening')}")
    opening = spelled(open_state(0))
    raw = read_bytes(f"r1_obs_opening/{SIDECAR}")
    eq(raw.decode("utf-8", errors="replace"), opening, "the first checkpoint's spelling")
    eq(len(raw), len(opening.encode()), "the first checkpoint's size in bytes")

    # ---- the last write ---------------------------------------------------
    k = len(SPEC["obs_done_replies"])
    last = author_of_line(k)
    done_state = {"version": LEDGER_VERSION, "responses": k, "turns": k + 1, "last_author": last,
                  "next_speaker": None, "interleave_faults": 0, "completed": True,
                  "completion_reason": "agent_signal"}
    eq(o["done_run"].get("raised"), False, f"the finished run raised: {o['done_run'].get('str', '')[:200]}")
    eq(len(log_rows("r1_obs_done")), k + 1, "lines in the finished log")
    raw = read_bytes(f"r1_obs_done/{SIDECAR}")
    eq(raw.decode("utf-8", errors="replace"), spelled(done_state), "the last checkpoint's spelling")
    eq(len(raw), len(spelled(done_state).encode()), "the last checkpoint's size in bytes")
    eq(value_of(o["done_read_sidecar"], "read_sidecar"), done_state, "read_sidecar after the run")

    # ---- a log truncated behind the checkpoint's back ---------------------
    m = SPEC["obs_truncate_to"]
    sr = o["stale_raises"]
    raised_named(sr, "TurnLedgerDesyncError", "a truncated log beside a stale checkpoint")
    same_file(sr.get("path"), f"r1_obs_stale/{SIDECAR}", "stale error.path")
    eq(sr.get("log_responses"), m - 1, "stale log_responses")
    eq(sr.get("recorded_responses"), k, "stale recorded_responses")
    eq(sr.get("log_last_author"), author_of_line(m - 1), "stale log_last_author")
    eq(sr.get("recorded_last_author"), last, "stale recorded_last_author")
    eq(o["stale_calls"], [], "a stale checkpoint issued a request")
    eq(len(log_rows("r1_obs_stale")), m, "a stale checkpoint appended to the log")

    # ---- the same log with no checkpoint ----------------------------------
    eq(o["resume_run"].get("raised"), False, f"the resume raised: {o['resume_run'].get('str', '')[:200]}")
    eq(o["resume_status"], "adopted", "no checkpoint -> adopted")
    eq(o["resume_calls"], [[author_of_line(m), m - 1]], "the resume asks exactly one")
    eq(len(log_rows("r1_obs_resume")), m + 1, "the resume completes the log")

    # ---- an older-version checkpoint --------------------------------------
    plain_name(o["older_planted_name"], "r1.observability")
    ok(o["older_moved"], "could not plant an older-version checkpoint: the build records no "
                         "integer beside the ledger's own fields")
    eq(o["older_status"], "adopted", "older-version checkpoint -> adopted")


# ---------------------------------------------------------------------------
# r2 — the default completion signal
# ---------------------------------------------------------------------------
def require_token(o):
    """The old `require_feature`: the stock agent completes on THE token.

    The worker found its token in the submission (the constant, or a literal
    `is_completed` completes on); the candidate lists were rendered with it, so
    they only mean something if it is the token the requirement names.
    """
    ok(o.get("token") is not None,
       "Agent.is_completed's default sentinel match is not implemented: no token it completes on")
    eq(o["token"], SENTINEL, "the token Agent.is_completed completes on")


def outcomes_match(recipes, got, msg):
    ok(isinstance(got, list), f"{msg}: no outcomes recorded")
    eq(len(got), len(recipes), f"{msg}: outcome count")
    wrong = []
    for i, (recipe, answer) in enumerate(zip(recipes, got)):
        value = fixture_spec.render(recipe, SENTINEL)
        want = completes(value)
        if answer is not want:
            wrong.append(f"#{i} {recipe[0]} {value!r}: got {answer!r}, want {want}")
    ok(not wrong, f"{msg}: {len(wrong)} of {len(recipes)} wrong — " + "; ".join(wrong[:6]))


def judge_r2_rule(o):
    eq(o["completion_sentinel"], SENTINEL, "COMPLETION_SENTINEL")
    defined("COMPLETION_SENTINEL", SENTINEL)
    require_token(o)
    outcomes_match(SPEC["r2_rule"], o["outcomes"], "a reply that ends with the token completes")


def judge_r2_scope(o):
    require_token(o)
    outcomes_match(SPEC["r2_scope"], o["outcomes"],
                   "case-sensitive, suffix-only, blind to trailing whitespace")


def judge_r2_failure_behavior(o):
    require_token(o)
    outcomes_match(SPEC["r2_fail"], o["outcomes"], "a non-str reply answers False")


def judge_r2_observability(o):
    require_token(o)
    k = len(SPEC["r2_obs_replies"]) + 1
    last = f"{SPEC['r2_obs_last_text']} {SENTINEL}"
    eq(o["n_calls"], k, "calls before the token ended the conversation")
    rows = log_rows("r2_obs")
    eq(len(rows), k + 1, "log lines")
    eq(rows[-1], (author_of_line(k), last), "the log's last line is the token-bearing reply")
    eq(o["num_responses"], k, "num_responses")
    eq(o["ledger_responses"], k, "ledger responses")
    eq(o["completion_reason"], "agent_signal", "completion_reason")
    is_true(o["completed"], "ledger completed")
    eq(o["n_rows"], k + 1, "dataset rows")
    eq(o["last_content"], last, "the dataset's last row")
    eq(o["last_role"], author_of_line(k), "the dataset's last role")


JUDGES = {
    "test_open::test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses": judge_open,
    "test_r1::test_rule__checkpoint_contract": judge_r1_rule,
    "test_r1::test_scope__loading_and_authority": judge_r1_scope,
    "test_r1::test_failure_behavior__verification_arms": judge_r1_failure_behavior,
    "test_r1::test_observability__checkpoint_on_disk": judge_r1_observability,
    "test_r2::test_rule__completion_signal": judge_r2_rule,
    "test_r2::test_scope__matching_discipline": judge_r2_scope,
    "test_r2::test_failure_behavior__non_text_replies": judge_r2_failure_behavior,
    "test_r2::test_observability__final_turn_accounting": judge_r2_observability,
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


def main(obs_path: str, out_path: str, seed: str, artifacts: str) -> int:
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = pathlib.Path(artifacts)

    try:
        observations = json.loads(pathlib.Path(obs_path).read_text())
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)
    if not isinstance(observations, dict):
        observations = {}

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if not isinstance(probe, dict):
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
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
