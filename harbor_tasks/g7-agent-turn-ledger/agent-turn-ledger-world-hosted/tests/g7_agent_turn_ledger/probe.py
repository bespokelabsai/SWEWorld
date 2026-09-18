"""g7 worker: the ONLY process that imports the submission.

Runs as `nobody`, from a root-staged jail that holds this file,
`probe_support.py`, `fixture_spec.py` and `harness.py` and nothing else. For
each graded test it drives curator and writes what happened — never a pass/fail
— to the observations file named on argv. `judge.py`, which never imports the
submission and which this process cannot read (test.sh keeps /tests root-only),
turns those values and the directories the scenarios left behind into the
verdict.

WHAT THE SPLIT ALONE DID NOT BUY. Separating the processes stopped the worker
rewriting the verdict; it did not stop the worker inventing the values the
verdict is computed from. With a fixed fixture those values never changed:
a replayed capture of one correct run scored 1.0 on every hidden fact, and a
constant file of booleans passed r2.scope and r2.failure_behavior on a tree that
implemented nothing. So:

  * **the inputs are re-drawn every run** from the seed root chose
    (`fixture_spec.derive`): agent names of varying width (spelled into the
    checkpoint, so its size moves), where a run dies, how long a log is, what a
    lying checkpoint claims, and shuffled lists of candidate replies;
  * **the scenarios run under the artifacts root**, one directory per scenario,
    and the judge opens those directories itself — the checkpoint's bytes, the
    log's lines, what else is there — instead of asking this process;
  * **no answer is carried here.** The checkpoint's name, version and spelling,
    the completion token, the status words: none of them is in the jail. Where a
    scenario has to USE one of them — plant a checkpoint, write a reply that
    ends the conversation — it is discovered from the submission (see
    `sidecar_name`, `completion_token`), and the judge decides whether what was
    discovered is right. A submission that hardcodes the name or the token and
    exports no constant is still measured on every other fact; only the fact
    that names the constant grades the constant (tasks/lessons.md, 2026-09-14,
    "a probe reaching for an attribute is a dependency between facts").
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import shutil
import sys
import traceback

# Bound BEFORE the submission is imported, and called instead of returning from
# main(): interpreter shutdown runs `atexit` hooks the submission registered at
# import. One door, not the fix — what makes a forged value worthless is that it
# is not knowable in advance.
_EXIT = os._exit

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

import fixture_spec  # noqa: E402 - the run's inputs; stdlib only, no answers

# probe_support owns the curator imports and the answer-free fakes; importing it
# runs the submission's `import bespokelabs.curator` — this process's whole
# purpose, and why it is disposable.
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402

SPEC: dict = {}
ARTIFACTS = "/nonexistent"

NEVER = lambda author, content: False  # noqa: E731 - the callback build_ledger takes

# The ledger's own attribute names. The open feature states these (the open
# fact reads every one off `processor.ledger`); what the checkpoint FILE holds beyond
# them is r1.rule's to grade and is never named here.
LEDGER_FIELDS = ("responses", "turns", "last_author", "next_speaker",
                 "interleave_faults", "completed", "completion_reason")


def scenario_dir(name: str) -> str:
    """A fresh directory for one scenario, where the judge will look for it."""
    path = os.path.join(ARTIFACTS, name)
    os.makedirs(path)
    return path


def seeder():
    return SPEC["seeder"]


def partner():
    return SPEC["partner"]


def rows(contents):
    return fixture_spec.alternating(seeder(), partner(), contents)


def load(working_dir, max_responses=9):
    """The ledger a working directory holds, by the ticket's own entry point."""
    load_ledger = S.sym("load_ledger")
    return load_ledger(
        str(working_dir),
        seeder_name=seeder(),
        partner_name=partner(),
        max_responses=max_responses,
        is_completed=NEVER,
    )


def an_agent():
    """A stock Agent, built the way the public constructor allows.

    `backend="litellm"` only so that construction stays offline: the openai
    backend probes the provider for rate-limit headers inside its constructor,
    which no grading suite is allowed to let happen.
    """
    from bespokelabs.curator.agent.agent import Agent
    return Agent(name=seeder(), model_name="gpt-4o-mini", backend="litellm",
                 system_prompt="You are a conversation partner.")


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
                info[attr] = jsonable(getattr(exc, attr))
        return info
    return {"raised": False, "mro": []}


DESYNC_ATTRS = ("path", "log_responses", "recorded_responses",
                "log_last_author", "recorded_last_author")


def jsonable(value):
    try:
        return json.loads(json.dumps(value))
    except (TypeError, ValueError):
        return repr(value)


def attempt(fn, *args, **kwargs) -> dict:
    """{"value": ...} or {"error": ...}: one step's evidence, never the node's death."""
    try:
        return {"value": jsonable(fn(*args, **kwargs))}
    except BaseException as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def field(obj, name):
    return read_field(obj, name, default=None)


def mro_of(name):
    cls = S.sym(name, None)
    return [c.__name__ for c in cls.__mro__] if isinstance(cls, type) else None


# ---------------------------------------------------------------------------
# discovery: the names a scenario has to USE, taken from the submission
# ---------------------------------------------------------------------------
_DISCOVERED: dict = {}


def sidecar_name():
    """The file the submission keeps beside the log, or None.

    NOT a default to the name r1.rule grades: that string is an answer and this
    file is in the worker's jail. The exported constant if there is one, else the
    single file a fresh run leaves beside its log. The judge decides whether the
    name is right; the facts that only need to PLANT a checkpoint use whatever
    the implementation itself reads.
    """
    if "name" not in _DISCOVERED:
        _DISCOVERED.update(name=None, source=None, template=None)
        try:
            _discover_sidecar()
        except BaseException as exc:  # noqa: BLE001 - discovery failing is evidence, not a crash
            _DISCOVERED["discovery_error"] = f"{type(exc).__name__}: {exc}"
    return _DISCOVERED["name"]


def _discover_sidecar():
    constant = S.sym("TURN_LEDGER_FILENAME", None)
    if isinstance(constant, str) and constant and os.path.basename(constant) == constant:
        _DISCOVERED.update(name=constant, source="constant")
    work = os.path.join(ARTIFACTS, "discover")
    os.makedirs(work, exist_ok=True)
    conversation = S.Conversation(raise_on=(1,))
    try:
        asyncio.run(conversation.processor(max_length=3).run(work))
    except BaseException:  # noqa: BLE001 - the fake raises by design
        pass
    others = sorted(n for n in os.listdir(work)
                    if n != S.LOG and os.path.isfile(os.path.join(work, n)))
    if _DISCOVERED["name"] is None and len(others) == 1:
        _DISCOVERED.update(name=others[0], source="written")
    name = _DISCOVERED["name"]
    if name is not None and os.path.isfile(os.path.join(work, name)):
        try:
            loaded = json.loads(open(os.path.join(work, name)).read())
            if isinstance(loaded, dict):
                _DISCOVERED["template"] = loaded
        except (OSError, ValueError):
            pass
    if _DISCOVERED["template"] is None:
        try:
            state = S.sym("load_ledger")(work, seeder_name=seeder(), partner_name=partner(),
                                         max_responses=3, is_completed=NEVER).sidecar_state()
            if isinstance(state, dict):
                _DISCOVERED["template"] = dict(state)
        except BaseException:  # noqa: BLE001
            pass


def template():
    sidecar_name()
    return _DISCOVERED["template"]


def planted_state(**fields):
    """A checkpoint in the submission's own shape, with the ledger fields set."""
    state = dict(template() or {})
    state.update(fields)
    return state


def older_state(bump, **fields):
    """The same, with every key the ledger itself does not carry moved by `bump`.

    That is how an older-version checkpoint is made without this file naming the
    version key or its value: whatever integer the build records beside the
    ledger's own fields is shifted, and the judge checks one really was.
    """
    state = planted_state(**fields)
    moved = []
    for key, value in list(state.items()):
        if key not in LEDGER_FIELDS and isinstance(value, int) and not isinstance(value, bool):
            state[key] = value + bump
            moved.append(key)
    return state, moved


def plant(working_dir, text):
    name = sidecar_name()
    if name is None:
        return None
    with open(os.path.join(working_dir, name), "w") as handle:
        handle.write(text)
    return name


def _string_literals(root):
    found = set()
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            try:
                tree = ast.parse(open(os.path.join(dirpath, fname), errors="replace").read())
            except (OSError, SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and 1 < len(node.value) <= 200 and "\n" not in node.value:
                    found.add(node.value)
    return sorted(found)


def completion_token():
    """The token `Agent.is_completed` ends a conversation on, or None.

    The exported constant if there is one. Otherwise the submission's own source
    is searched: every short string literal the stock agent says completes a
    conversation, trimmed from the front while it still does, shortest first. A
    submission that wrote the literal straight into `is_completed` is then
    measured on scope, failure behaviour and observability like any other; the
    judge checks the token against the one the requirement names.
    """
    if "token" in _DISCOVERED:
        return _DISCOVERED["token"]
    token, source = None, None
    constant = S.sym("COMPLETION_SENTINEL", None)
    if isinstance(constant, str) and constant:
        token, source = constant, "constant"
    else:
        try:
            import bespokelabs.curator as curator
            agent = an_agent()

            def completes(value):
                try:
                    return agent.is_completed(value) is True
                except BaseException:  # noqa: BLE001
                    return False

            if not completes("") and not completes("plain words"):
                hits = set()
                for literal in _string_literals(os.path.dirname(curator.__file__)):
                    if completes(literal):
                        while len(literal) > 1 and completes(literal[1:]):
                            literal = literal[1:]
                        hits.add(literal)
                if hits:
                    token, source = sorted(hits, key=lambda s: (len(s), s))[0], "source"
        except BaseException:  # noqa: BLE001
            token = None
    _DISCOVERED.update(token=token, token_source=source)
    return token


def outcomes(recipes, token):
    """What `Agent.is_completed` answered for each rendered recipe, in order."""
    if token is None:
        return None
    agent = an_agent()
    out = []
    for recipe in recipes:
        try:
            value = agent.is_completed(fixture_spec.render(recipe, token))
        except BaseException as exc:  # noqa: BLE001
            out.append({"raised": type(exc).__name__})
            continue
        out.append(value if isinstance(value, bool) else {"returned": type(value).__name__})
    return out


# ===========================================================================
# open feature — the seed line and the response budget (one fact)
# ===========================================================================
def probe_open() -> dict:
    o: dict = {}

    # ---- a fresh run -------------------------------------------------------
    work = scenario_dir("open_run")
    conversation = S.Conversation()
    processor = conversation.processor(max_length=4)
    dataset = asyncio.run(processor.run(str(work)))

    o["calls_names"] = [name for name, _ in conversation.calls]
    o["calls_task_ids"] = [task_id for _, task_id in conversation.calls]
    o["n_calls"] = len(conversation.calls)

    lines = S.log_lines(work)
    o["n_lines"] = len(lines)
    o["authors"] = S.authors(work)
    seed = S.AgentResponse.model_validate_json(lines[0])
    gr = seed.generic_request
    o["seed"] = {
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

    ledger = processor.ledger
    o["ledger"] = {name: read_field(ledger, name) for name in LEDGER_FIELDS}
    o["ledger"]["entries_is_tuple"] = isinstance(read_field(ledger, "entries"), tuple)
    o["ledger"]["messages_eq_history"] = ledger.messages() == processor.conversation_history
    o["history0"] = processor.conversation_history[0]

    tracker = processor.status_tracker
    o["tracker"] = {name: read_field(tracker, name) for name in
                    ("max_turns", "current_turn", "num_responses", "num_cached", "num_errors")}

    rows_ = S.rows_of(dataset)
    o["columns"] = sorted(dataset.column_names)
    o["n_rows"] = len(rows_)
    o["row0"] = rows_[0]
    o["turns_col"] = [row["turn"] for row in rows_]
    o["sources_col"] = [row["source"] for row in rows_]
    o["roles_col"] = [row["role"] for row in rows_]
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
    bare_dir = scenario_dir("open_bare")
    bare = S.Conversation(system_prompt=False)
    third = bare.processor(max_length=1)
    dataset3 = asyncio.run(third.run(str(bare_dir)))
    o["bare_n_calls"] = len(bare.calls)
    o["bare_lines"] = len(S.log_lines(bare_dir))
    o["bare_n_rows"] = len(S.rows_of(dataset3))

    # ---- a formatter that answers with more than one system message --------
    # instruction.md:44 names this case outright. Nothing is expected here: the
    # messages the formatter produced, the messages each call was then given and
    # the log's own authors and contents all go over, and the judge builds the
    # transformation it should have seen out of the three.
    multi_dir = scenario_dir("open_multi_system")
    multi = S.Conversation(extra_system=2)
    fourth = multi.processor(max_length=2)
    asyncio.run(fourth.run(str(multi_dir)))
    o["multi_requests"] = jsonable(multi.requests)
    o["multi_formatter_out"] = jsonable(multi.formatter_out)
    o["multi_authors"] = S.authors(multi_dir)
    o["multi_contents"] = [json.loads(line)["response_message"] for line in S.log_lines(multi_dir)]
    return o


# ===========================================================================
# r1 — the checkpoint beside the log
# ===========================================================================
def probe_r1_rule() -> dict:
    o: dict = {}
    o["filename"] = jsonable(S.sym("TURN_LEDGER_FILENAME", None))
    o["version"] = jsonable(S.sym("TURN_LEDGER_VERSION", None))
    o["functions"] = {name: callable(S.sym(name, None))
                      for name in ("read_sidecar", "write_sidecar", "verify_sidecar")}

    # A run that dies on call `die_on` has appended the seed and die_on - 1
    # responses. The judge reads the checkpoint it left from the directory.
    work = scenario_dir("r1_rule_run")
    conversation = S.Conversation(raise_on=(SPEC["rule_die_on"],))
    processor = conversation.processor(max_length=SPEC["rule_max_length"])
    o["run_raises"] = raises(lambda: asyncio.run(processor.run(work)))

    read_sidecar = S.sym("read_sidecar", None)
    o["read_sidecar"] = attempt(read_sidecar, work) if callable(read_sidecar) else None

    try:
        ledger = load(work, max_responses=SPEC["rule_max_length"])
        o["sidecar_state"] = attempt(ledger.sidecar_state)
    except BaseException as exc:  # noqa: BLE001
        ledger = None
        o["sidecar_state"] = {"error": f"{type(exc).__name__}: {exc}"}

    # write_sidecar into an empty directory, so the file there is its alone.
    write_sidecar = S.sym("write_sidecar", None)
    target = scenario_dir("r1_rule_write")
    if callable(write_sidecar) and ledger is not None:
        o["write_returned"] = attempt(S.call_write_sidecar, write_sidecar, target, ledger)
    else:
        o["write_returned"] = None
    return o


def probe_r1_scope() -> dict:
    o: dict = {}
    statuses = S.sym("LEDGER_STATUSES", None)
    o["statuses"] = sorted(statuses) if isinstance(statuses, (list, tuple, set, frozenset)) else None

    contents = SPEC["scope_contents"]
    log_rows = rows(contents)
    last = log_rows[-1][0]
    other = partner() if last == seeder() else seeder()

    # No checkpoint yet: the ledger comes from the log alone. The judge reads
    # the directory afterwards to see that loading wrote nothing.
    adopted_dir = scenario_dir("r1_scope_adopted")
    S.write_log(adopted_dir, log_rows)
    adopted = load(adopted_dir)
    o["adopted_status"] = field(adopted, "status")
    o["adopted_responses"] = field(adopted, "responses")

    # A checkpoint that agrees on the only two keys compared and lies about the
    # rest. The judge compares the file on disk against these planted bytes.
    verified_dir = scenario_dir("r1_scope_verified")
    S.write_log(verified_dir, log_rows)
    lies = dict(SPEC["scope_lies"])
    text = json.dumps(planted_state(responses=len(contents) - 1, last_author=last, **lies))
    o["planted_name"] = plant(verified_dir, text)
    o["planted_text"] = text
    o["other"] = other
    try:
        ledger = load(verified_dir)
        o["agreeing"] = {"status": field(ledger, "status"),
                         **{name: field(ledger, name) for name in LEDGER_FIELDS}}
    except BaseException as exc:  # noqa: BLE001
        o["agreeing"] = {"error": f"{type(exc).__name__}: {exc}"}

    fresh = scenario_dir("r1_scope_fresh")
    conversation = S.Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=SPEC["scope_fresh_max_length"])
    o["fresh_run_raises"] = raises(lambda: asyncio.run(processor.run(fresh)))
    o["fresh_status"] = field(processor.ledger, "status") if getattr(processor, "ledger", None) is not None else None
    return o


def probe_r1_failure_behavior() -> dict:
    o: dict = {}
    o["desync_mro"] = mro_of("TurnLedgerDesyncError")
    o["base_mro"] = mro_of("TurnLedgerError")

    contents = SPEC["fail_contents"]
    log_rows = rows(contents)
    last = log_rows[-1][0]
    other = partner() if last == seeder() else seeder()
    responses = len(contents) - 1

    work = scenario_dir("r1_fail")
    S.write_log(work, log_rows)

    def status():
        try:
            return field(load(work), "status")
        except BaseException as exc:  # noqa: BLE001
            return {"error": f"{type(exc).__name__}: {exc}"}

    # (a) absent, unreadable, or a version this build does not speak.
    o["absent_status"] = status()
    o["planted_name"] = plant(work, SPEC["fail_garbage"])
    o["unreadable_status"] = status()
    old, moved = older_state(SPEC["fail_old_bump"], responses=responses, last_author=last)
    o["old_moved"] = moved
    plant(work, json.dumps(old))
    o["oldversion_status"] = status()

    # (b) the version matches and both compared keys agree.
    plant(work, json.dumps(planted_state(responses=responses, last_author=last)))
    o["agree_status"] = status()

    # (c) the version matches and the response count differs.
    plant(work, json.dumps(planted_state(responses=SPEC["fail_recorded_responses"], last_author=last)))
    o["desync_responses"] = raises(lambda: load(work), attrs=DESYNC_ATTRS)

    # (c) the version matches and the last author differs.
    plant(work, json.dumps(planted_state(responses=responses, last_author=other)))
    o["desync_author"] = raises(lambda: load(work), attrs=DESYNC_ATTRS)

    # The raise happens on the load path: nothing is asked, nothing is appended
    # (the judge counts the log's lines itself).
    conversation = S.Conversation()
    processor = conversation.processor(max_length=SPEC["fail_run_max_length"])
    o["run_raises"] = raises(lambda: asyncio.run(processor.run(work)))
    o["run_calls"] = [list(call) for call in conversation.calls]
    return o


def probe_r1_observability() -> dict:
    o: dict = {}
    read_sidecar = S.sym("read_sidecar", None)
    marker = SPEC["obs_marker"]
    stops = lambda response: isinstance(response, str) and response.endswith(marker)  # noqa: E731

    # ---- the first write, before a single response exists ------------------
    opening = scenario_dir("r1_obs_opening")
    conversation = S.Conversation(raise_on=(1,))
    processor = conversation.processor(max_length=SPEC["obs_opening_max_length"])
    o["opening_run_raises"] = raises(lambda: asyncio.run(processor.run(opening)))

    # ---- and the last write, when the conversation ends --------------------
    done = scenario_dir("r1_obs_done")
    finished = S.Conversation(replies=SPEC["obs_done_replies"], is_completed=stops)
    runner = finished.processor(max_length=SPEC["obs_done_max_length"])
    o["done_run"] = raises(lambda: asyncio.run(runner.run(done)))
    o["done_read_sidecar"] = attempt(read_sidecar, done) if callable(read_sidecar) else None

    # ---- a log truncated behind the checkpoint's back ----------------------
    stale_dir = os.path.join(ARTIFACTS, "r1_obs_stale")
    shutil.copytree(done, stale_dir)
    log_path = os.path.join(stale_dir, S.LOG)
    lines = open(log_path).read().splitlines(keepends=True)
    open(log_path, "w").write("".join(lines[:SPEC["obs_truncate_to"]]))
    stale = S.Conversation(replies=[SPEC["obs_resume_reply"]], is_completed=stops)
    aborted = stale.processor(max_length=SPEC["obs_done_max_length"])
    o["stale_raises"] = raises(lambda: asyncio.run(aborted.run(stale_dir)), attrs=DESYNC_ATTRS)
    o["stale_calls"] = [list(call) for call in stale.calls]

    # ---- the same log with no checkpoint at all ----------------------------
    # Everything but the log goes, so this does not need to know the file's name.
    resume_dir = scenario_dir("r1_obs_resume")
    shutil.copy(log_path, os.path.join(resume_dir, S.LOG))
    resumed = S.Conversation(replies=[SPEC["obs_resume_reply"]], is_completed=stops)
    second = resumed.processor(max_length=SPEC["obs_done_max_length"])
    o["resume_run"] = raises(lambda: asyncio.run(second.run(resume_dir)))
    o["resume_status"] = field(second.ledger, "status") if getattr(second, "ledger", None) is not None else None
    o["resume_calls"] = [list(call) for call in resumed.calls]

    # ---- and with one written by a version this build does not speak -------
    older = scenario_dir("r1_obs_older")
    older_rows = rows(SPEC["obs_older_contents"])
    S.write_log(older, older_rows)
    state, moved = older_state(SPEC["obs_older_bump"],
                               responses=len(older_rows) - 1, last_author=older_rows[-1][0])
    o["older_moved"] = moved
    o["older_planted_name"] = plant(older, json.dumps(state))
    try:
        o["older_status"] = field(load(older), "status")
    except BaseException as exc:  # noqa: BLE001
        o["older_status"] = {"error": f"{type(exc).__name__}: {exc}"}
    return o


# ===========================================================================
# r2 — the default completion signal
# ===========================================================================
def probe_r2_rule() -> dict:
    token = completion_token()
    return {"completion_sentinel": jsonable(S.sym("COMPLETION_SENTINEL", None)),
            "token": token, "outcomes": outcomes(SPEC["r2_rule"], token)}


def probe_r2_scope() -> dict:
    token = completion_token()
    return {"token": token, "outcomes": outcomes(SPEC["r2_scope"], token)}


def probe_r2_failure_behavior() -> dict:
    token = completion_token()
    return {"token": token, "outcomes": outcomes(SPEC["r2_fail"], token)}


def probe_r2_observability() -> dict:
    o: dict = {}
    token = completion_token()
    o["token"] = token
    if token is None:
        return o
    judge_of = an_agent()
    last = f"{SPEC['r2_obs_last_text']} {token}"
    work = scenario_dir("r2_obs")
    conversation = S.Conversation(replies=SPEC["r2_obs_replies"] + [last],
                                  is_completed=judge_of.is_completed)
    processor = conversation.processor(max_length=SPEC["r2_obs_max_length"])
    dataset = asyncio.run(processor.run(work))

    o["n_calls"] = len(conversation.calls)
    o["num_responses"] = read_field(processor.status_tracker, "num_responses")
    o["ledger_responses"] = read_field(processor.ledger, "responses")
    o["completion_reason"] = read_field(processor.ledger, "completion_reason")
    o["completed"] = read_field(processor.ledger, "completed")

    rows_ = [dict(row) for row in dataset]
    o["n_rows"] = len(rows_)
    o["last_content"] = rows_[-1]["content"]
    o["last_role"] = rows_[-1]["role"]
    return o


PROBES = {
    "test_open::test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses": probe_open,
    "test_r1::test_rule__checkpoint_contract": probe_r1_rule,
    "test_r1::test_scope__loading_and_authority": probe_r1_scope,
    "test_r1::test_failure_behavior__verification_arms": probe_r1_failure_behavior,
    "test_r1::test_observability__checkpoint_on_disk": probe_r1_observability,
    "test_r2::test_rule__completion_signal": probe_r2_rule,
    "test_r2::test_scope__matching_discipline": probe_r2_scope,
    "test_r2::test_failure_behavior__non_text_replies": probe_r2_failure_behavior,
    "test_r2::test_observability__final_turn_accounting": probe_r2_observability,
}


def main(out_path: str, seed: str, artifacts: str) -> int:
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = artifacts
    S.set_names(SPEC["seeder"], SPEC["partner"])

    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    results["discovery"] = {"ok": True, "obs": {
        "sidecar_name": _DISCOVERED.get("name"), "sidecar_source": _DISCOVERED.get("source"),
        "token_source": _DISCOVERED.get("token_source")}}
    with open(out_path, "w") as fh:
        json.dump(results, fh, default=repr)
    return 0


if __name__ == "__main__":
    code = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.stdout.flush()
    sys.stderr.flush()
    _EXIT(code)
