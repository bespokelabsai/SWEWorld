"""g7 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
fakes and readers (`Conversation`, `sym`, `log_lines`, `authors`, `write_log`,
`drop_side_files`, `rows_of`), so a value here is the value the test saw. The
judge holds the assertions those tests made.

Two g7-specific reproduction rules:

  * the probe is not under pytest, so every scenario gets its own
    `tempfile.mkdtemp()` in place of the `tmp_path` fixture, created fresh so a
    resume sees only what the reference's truncate/`drop_side_files` left;
  * for the byte-exact facts the probe records the RAW file text and its size and
    lets the judge assert the exact spelling and count — it never carries 186,
    189, or the sidecar's JSON here. For the desync message, whose expected text
    embeds the run's own temp path, the probe records `str(error)` and the
    error's `.path`; the judge rebuilds the expected string from that path plus
    its own format and compares.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest. g7 uses no provider socket: every fake is
# duck-typed and `an_agent()` builds on the litellm backend, which stays offline.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# probe_support owns the curator imports and the answer-free fakes/inputs; reuse
# them so a probe calls curator exactly as the test does. Importing it runs the
# submission's `import bespokelabs.curator` — this process's whole purpose, and
# why it is disposable. The worker never imports test_open, whose source carries
# the expected answer literals.
import probe_support as S  # noqa: E402


# ---------------------------------------------------------------------------
# Answer-free drivers the probe needs, mirrored from the test_r*-local helpers
# (the probe cannot import test_r1/test_r2 — they hold the answers).
# ---------------------------------------------------------------------------
NEVER = lambda author, content: False  # noqa: E731 - the callback build_ledger takes

THREE_LINES = ((S.SEEDER, "seed message"), (S.PARTNER, "first answer"), (S.SEEDER, "second question"))


def newdir():
    """A fresh empty working directory, standing in for the `tmp_path` fixture."""
    return tempfile.mkdtemp(prefix="g7-")


def load(working_dir, max_responses=9):
    """The ledger a working directory holds, by the ticket's own entry point."""
    load_ledger = S.sym("load_ledger")
    return load_ledger(
        str(working_dir),
        seeder_name=S.SEEDER,
        partner_name=S.PARTNER,
        max_responses=max_responses,
        is_completed=NEVER,
    )


def put_sidecar(working_dir, state):
    path = os.path.join(str(working_dir), S.SIDECAR)
    with open(path, "w") as handle:
        handle.write(json.dumps(state))
    return path


def full_state(**overrides):
    """The current-version sidecar the reference writes as INPUT to verify_sidecar.

    version=2 and responses/last_author matching the log are what make a written
    sidecar `verified` rather than `adopted`; they are construction inputs, not
    answers. The judge holds its own copies for the facts it grades.
    """
    state = {
        "version": 2,
        "responses": 2,
        "turns": 3,
        "last_author": S.SEEDER,
        "next_speaker": S.PARTNER,
        "interleave_faults": 0,
        "completed": False,
        "completion_reason": "open",
    }
    state.update(overrides)
    return state


def an_agent():
    """A stock Agent, built the way the public constructor allows.

    `backend="litellm"` only so that construction stays offline: the openai
    backend probes the provider for rate-limit headers inside its constructor,
    which no grading suite is allowed to let happen.
    """
    from bespokelabs.curator.agent.agent import Agent
    return Agent(name="client", model_name="gpt-4o-mini", backend="litellm",
                 system_prompt="You are a client.")


def raises(fn, *args, attrs=(), **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, its str, and the
    named attributes an exception carries (path, response/author counts)."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in attrs:
            if hasattr(exc, attr):
                info[attr] = getattr(exc, attr)
        return info
    return {"raised": False, "mro": []}


def realpath_eq(a, b) -> bool:
    return os.path.realpath(str(a)) == os.path.realpath(str(b))


def seed_fields(seed) -> dict:
    """The `AgentResponse` parsed from log line 0, as JSON-safe observations."""
    gr = seed.generic_request
    return {
        "name": seed.name,
        "response_message": seed.response_message,
        "finish_reason": seed.finish_reason,
        "response_cost": seed.response_cost,
        "token_usage_is_none": seed.token_usage is None,
        "raw_response_is_none": seed.raw_response is None,
        "raw_request_is_none": seed.raw_request is None,
        "parsed_is_none": seed.parsed_response_message is None,
        "errors_is_none": seed.response_errors is None,
        "created_iso": seed.created_at.isoformat(),
        "finished_iso": seed.finished_at.isoformat(),
        "created_eq_finished": seed.created_at == seed.finished_at,
        "gr_model": gr.model,
        "gr_messages": gr.messages,
        "gr_original_row": gr.original_row,
        "gr_original_row_idx": gr.original_row_idx,
    }


# ===========================================================================
# open feature — the seed line and the response budget (one fact)
# ===========================================================================
def probe_open() -> dict:
    from harness import read_field
    o: dict = {}

    # ---- a fresh run -------------------------------------------------------
    work = newdir()
    conversation = S.Conversation()
    processor = conversation.processor(max_length=4)
    dataset = asyncio.run(processor.run(str(work)))

    o["calls_names"] = [name for name, _ in conversation.calls]
    o["calls_task_ids"] = [task_id for _, task_id in conversation.calls]
    o["n_calls"] = len(conversation.calls)

    lines = S.log_lines(work)
    o["n_lines"] = len(lines)
    o["authors"] = S.authors(work)
    o["seed"] = seed_fields(S.AgentResponse.model_validate_json(lines[0]))

    ledger = processor.ledger
    o["ledger"] = {
        "responses": read_field(ledger, "responses"),
        "turns": read_field(ledger, "turns"),
        "last_author": read_field(ledger, "last_author"),
        "next_speaker": read_field(ledger, "next_speaker"),
        "interleave_faults": read_field(ledger, "interleave_faults"),
        "completed": read_field(ledger, "completed"),
        "completion_reason": read_field(ledger, "completion_reason"),
        "entries_is_tuple": isinstance(read_field(ledger, "entries"), tuple),
        "messages_eq_history": ledger.messages() == processor.conversation_history,
    }
    o["history0"] = processor.conversation_history[0]

    tracker = processor.status_tracker
    o["tracker"] = {
        "max_turns": read_field(tracker, "max_turns"),
        "current_turn": read_field(tracker, "current_turn"),
        "num_responses": read_field(tracker, "num_responses"),
        "num_cached": read_field(tracker, "num_cached"),
        "num_errors": read_field(tracker, "num_errors"),
    }

    rows = S.rows_of(dataset)
    o["columns"] = sorted(dataset.column_names)
    o["n_rows"] = len(rows)
    o["row0"] = rows[0]
    o["turns_col"] = [row["turn"] for row in rows]
    o["sources_col"] = [row["source"] for row in rows]
    o["roles_col"] = [row["role"] for row in rows]
    o["authors_after"] = S.authors(work)

    # ---- and a resume of the same directory --------------------------------
    log_path = os.path.join(str(work), S.LOG)
    keep = open(log_path).read().splitlines(keepends=True)[:3]
    open(log_path, "w").write("".join(keep))
    S.drop_side_files(work)

    resumed = S.Conversation()
    second = resumed.processor(max_length=4)
    dataset2 = asyncio.run(second.run(str(work)))

    o["resume_calls"] = [[name, task_id] for name, task_id in resumed.calls]
    o["resume_n_calls"] = len(resumed.calls)
    o["resume_lines"] = len(S.log_lines(work))
    o["resume_responses"] = read_field(second.ledger, "responses")
    o["resume_n_rows"] = len(S.rows_of(dataset2))
    o["resume_num_cached"] = read_field(second.status_tracker, "num_cached")
    o["resume_num_responses"] = read_field(second.status_tracker, "num_responses")
    o["resume_current_turn"] = read_field(second.status_tracker, "current_turn")

    # ---- an agent built without a system prompt still converses -------------
    bare_dir = newdir()
    bare = S.Conversation(system_prompt=False)
    third = bare.processor(max_length=1)
    dataset3 = asyncio.run(third.run(str(bare_dir)))
    o["bare_n_calls"] = len(bare.calls)
    o["bare_lines"] = len(S.log_lines(bare_dir))
    o["bare_n_rows"] = len(S.rows_of(dataset3))
    return o


# ===========================================================================
# r1 — the checkpoint beside the log
# ===========================================================================
def probe_r1_rule() -> dict:
    o: dict = {}
    o["filename"] = S.sym("TURN_LEDGER_FILENAME")
    o["version"] = S.sym("TURN_LEDGER_VERSION")

    read_sidecar = S.sym("read_sidecar")
    write_sidecar = S.sym("write_sidecar")
    S.sym("verify_sidecar")  # the third of the three functions the requirement names

    # A run that dies on its third call has appended the seed and two responses.
    work = newdir()
    conversation = S.Conversation(raise_on=(3,))
    processor = conversation.processor(max_length=4)
    o["run_raises"] = raises(lambda: asyncio.run(processor.run(str(work))))
    o["authors"] = S.authors(work)

    path = os.path.join(str(work), "turn_ledger.json")
    o["exists"] = os.path.exists(path)

    state = read_sidecar(str(work))
    o["state_keys"] = sorted(state)
    o["state"] = state

    ledger = load(work, max_responses=4)
    o["sidecar_state"] = ledger.sidecar_state()
    returned = S.call_write_sidecar(write_sidecar, str(work), ledger)
    o["returned_is_abs"] = os.path.isabs(returned)
    o["returned_realpath_eq"] = realpath_eq(returned, path)
    o["written"] = json.loads(open(path).read())
    return o


def probe_r1_scope() -> dict:
    from harness import read_field
    o: dict = {}
    o["statuses"] = sorted(S.sym("LEDGER_STATUSES"))

    work = newdir()
    S.write_log(work, THREE_LINES)
    before = os.path.join(str(work), "responses_0.jsonl")
    log_bytes = open(before, "rb").read()

    listing = sorted(os.listdir(str(work)))
    adopted = load(work)
    o["adopted_status"] = read_field(adopted, "status")
    o["adopted_responses"] = read_field(adopted, "responses")
    o["listing_unchanged"] = sorted(os.listdir(str(work))) == listing

    path = put_sidecar(
        work,
        full_state(
            turns=99,
            next_speaker="nobody",
            interleave_faults=7,
            completed=True,
            completion_reason="budget",
        ),
    )
    recorded = open(path, "rb").read()
    ledger = load(work)
    o["verified"] = {
        "status": read_field(ledger, "status"),
        "turns": read_field(ledger, "turns"),
        "responses": read_field(ledger, "responses"),
        "next_speaker": read_field(ledger, "next_speaker"),
        "interleave_faults": read_field(ledger, "interleave_faults"),
        "completed": read_field(ledger, "completed"),
        "completion_reason": read_field(ledger, "completion_reason"),
    }
    o["sidecar_untouched"] = open(path, "rb").read() == recorded
    o["log_untouched"] = open(before, "rb").read() == log_bytes
    o["authors"] = S.authors(work)

    fresh = newdir()
    conversation = S.Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=4)
    o["fresh_run_raises"] = raises(lambda: asyncio.run(processor.run(str(fresh))))
    o["fresh_status"] = read_field(processor.ledger, "status")
    return o


def probe_r1_failure_behavior() -> dict:
    from harness import read_field
    o: dict = {}
    desync = S.sym("TurnLedgerDesyncError")
    base = S.sym("TurnLedgerError")
    o["desync_mro"] = [c.__name__ for c in desync.__mro__]
    o["base_mro"] = [c.__name__ for c in base.__mro__]
    o["desync_sub_base"] = issubclass(desync, base)
    o["base_sub_runtime"] = issubclass(base, RuntimeError)

    work = newdir()
    S.write_log(work, THREE_LINES)
    path = os.path.join(str(work), "turn_ledger.json")

    # (a) absent, unreadable, or a version this build does not speak.
    o["absent_status"] = read_field(load(work), "status")
    with open(path, "w") as handle:
        handle.write("{not json at all")
    o["unreadable_status"] = read_field(load(work), "status")
    put_sidecar(work, {"version": 1, "responses": 2, "last_author": S.SEEDER})
    o["oldversion_status"] = read_field(load(work), "status")

    # (b) the version matches and both compared keys agree.
    put_sidecar(work, full_state())
    o["agree_status"] = read_field(load(work), "status")

    # (c) the version matches and the response count differs.
    put_sidecar(work, full_state(responses=1))
    o["desync_responses"] = raises(
        lambda: load(work),
        attrs=("path", "log_responses", "recorded_responses",
               "log_last_author", "recorded_last_author"),
    )
    o["desync_responses"]["path_realpath_eq"] = (
        realpath_eq(o["desync_responses"].get("path", ""), path)
        if o["desync_responses"].get("raised") else False)

    # (c) the version matches and the last author differs.
    put_sidecar(work, full_state(last_author=S.PARTNER))
    o["desync_author"] = raises(
        lambda: load(work),
        attrs=("path", "log_responses", "recorded_responses",
               "log_last_author", "recorded_last_author"),
    )

    # The raise happens on the load path: nothing is asked, nothing is appended.
    conversation = S.Conversation()
    processor = conversation.processor(max_length=6)
    o["run_raises"] = raises(lambda: asyncio.run(processor.run(str(work))))
    o["run_calls"] = conversation.calls
    o["run_lines"] = len(S.log_lines(work))
    return o


def probe_r1_observability() -> dict:
    from harness import read_field
    o: dict = {}
    read_sidecar = S.sym("read_sidecar")

    # ---- the first write, before a single response exists ------------------
    opening = newdir()
    conversation = S.Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=4)
    o["opening_run_raises"] = raises(lambda: asyncio.run(processor.run(str(opening))))
    opening_path = os.path.join(str(opening), "turn_ledger.json")
    o["opening_exists"] = os.path.exists(opening_path)
    o["opening_text"] = open(opening_path).read() if o["opening_exists"] else None
    o["opening_size"] = os.stat(opening_path).st_size if o["opening_exists"] else None

    # ---- and the last write, when the conversation ends --------------------
    done = newdir()
    stops = lambda response: isinstance(response, str) and response.endswith("STOP")  # noqa: E731
    finished = S.Conversation(replies=["a", "b", "c STOP"], is_completed=stops)
    runner = finished.processor(max_length=6)
    asyncio.run(runner.run(str(done)))
    o["done_lines"] = len(S.log_lines(done))
    sidecar = os.path.join(str(done), "turn_ledger.json")
    o["done_size"] = os.stat(sidecar).st_size
    o["done_state"] = read_sidecar(str(done))

    # ---- a log truncated behind the checkpoint's back ----------------------
    log_path = os.path.join(str(done), "responses_0.jsonl")
    lines = open(log_path).read().splitlines(keepends=True)
    open(log_path, "w").write("".join(lines[:3]))
    stale = S.Conversation(replies=["c STOP"], is_completed=stops)
    aborted = stale.processor(max_length=6)
    o["stale_raises"] = raises(
        lambda: asyncio.run(aborted.run(str(done))),
        attrs=("path", "log_responses", "recorded_responses",
               "log_last_author", "recorded_last_author"),
    )
    o["stale_raises"]["path_realpath_eq"] = (
        realpath_eq(o["stale_raises"].get("path", ""), sidecar)
        if o["stale_raises"].get("raised") else False)
    o["stale_calls"] = stale.calls
    o["stale_lines"] = len(S.log_lines(done))

    # ---- the same log with no checkpoint at all ----------------------------
    os.unlink(sidecar)
    resumed = S.Conversation(replies=["c STOP"], is_completed=stops)
    second = resumed.processor(max_length=6)
    asyncio.run(second.run(str(done)))
    o["nockpt_status"] = read_field(second.ledger, "status")
    o["nockpt_calls"] = [[n, t] for n, t in resumed.calls]
    o["nockpt_lines"] = len(S.log_lines(done))

    # ---- and with one written by a version this build does not speak -------
    older = newdir()
    S.write_log(older, THREE_LINES)
    put_sidecar(older, {"version": 1, "responses": 2, "last_author": S.SEEDER})
    o["older_status"] = read_field(load(older), "status")
    return o


# ===========================================================================
# r2 — the default completion signal
# ===========================================================================
def probe_r2_rule() -> dict:
    o: dict = {}
    o["completion_sentinel"] = S.sym("COMPLETION_SENTINEL")
    agent = an_agent()
    o["ends_with"] = agent.is_completed(f"all set {S.SENTINEL}")
    o["exact"] = agent.is_completed(S.SENTINEL)
    o["plain"] = agent.is_completed("all set")
    return o


def probe_r2_scope() -> dict:
    o: dict = {}
    agent = an_agent()
    o["feature"] = agent.is_completed(f"all set {S.SENTINEL}") is True
    o["trailing_space_newline"] = agent.is_completed(f"all set {S.SENTINEL}  \n")
    o["trailing_tab"] = agent.is_completed(f"all set {S.SENTINEL}\t")
    o["prefix_then_more"] = agent.is_completed(f"{S.SENTINEL} but wait")
    o["lowercased"] = agent.is_completed("all set <<end_of_conversation>>")
    o["plain"] = agent.is_completed("all set")
    return o


def probe_r2_failure_behavior() -> dict:
    o: dict = {}
    agent = an_agent()
    o["feature"] = agent.is_completed(f"all set {S.SENTINEL}") is True
    o["dict"] = agent.is_completed({"text": S.SENTINEL})
    o["none"] = agent.is_completed(None)
    o["list"] = agent.is_completed([S.SENTINEL])
    o["int"] = agent.is_completed(42)
    return o


def probe_r2_observability() -> dict:
    from harness import read_field
    o: dict = {}
    probe = an_agent()
    o["feature"] = probe.is_completed(f"all set {S.SENTINEL}") is True

    last = f"Then index funds. {S.SENTINEL}"
    work = newdir()
    conversation = S.Conversation(
        replies=["Start with your goals.", "My goal is retirement in 20 years.", last],
        is_completed=probe.is_completed,
    )
    processor = conversation.processor(max_length=6)
    dataset = asyncio.run(processor.run(str(work)))

    o["n_calls"] = len(conversation.calls)
    o["n_lines"] = len(S.log_lines(work))
    o["num_responses"] = read_field(processor.status_tracker, "num_responses")
    o["ledger_responses"] = read_field(processor.ledger, "responses")
    o["completion_reason"] = read_field(processor.ledger, "completion_reason")
    o["completed"] = read_field(processor.ledger, "completed")

    rows = [dict(row) for row in dataset]
    o["n_rows"] = len(rows)
    o["last_content"] = rows[-1]["content"]
    o["last_content_is_sentinel_msg"] = rows[-1]["content"] == last
    o["last_role"] = rows[-1]["role"]
    return o


PROBES = {
    "test_open::test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses": probe_open,
    "test_r1::test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response": probe_r1_rule,
    "test_r1::test_scope__load_ledger_writes_nothing_and_the_log_outranks_the_checkpoint": probe_r1_scope,
    "test_r1::test_failure_behavior__absent_or_old_is_adopted_and_a_disagreeing_one_aborts": probe_r1_failure_behavior,
    "test_r1::test_observability__the_checkpoint_reads_186_bytes_mid_run_and_189_at_the_end": probe_r1_observability,
    "test_r2::test_rule__the_sentinel_is_the_end_of_conversation_token": probe_r2_rule,
    "test_r2::test_scope__matching_is_case_sensitive_suffix_only_and_ignores_trailing_space": probe_r2_scope,
    "test_r2::test_failure_behavior__a_structured_or_missing_reply_answers_false": probe_r2_failure_behavior,
    "test_r2::test_observability__the_message_that_ends_the_talk_is_still_a_turn": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
