"""t23 — hidden requirement r2: check the job belongs to this run before resuming.

    rule              on restart, before resuming an existing batch job ID,
                      verify the persisted job's provider, model name and
                      request payload hash still match the current run's
                      configuration; a mismatch must cause a fresh submission
                      rather than resuming a stale/incompatible job
    scope             resume-time validation
    failure_behavior  mismatch causes a fresh submission with a logged reason,
                      not a silent resume of incompatible results

This is the half baseline curator gets wrong, and it is worth being precise
about how. `_attempt_loading_batch_status_tracker` loads the persisted tracker
and then does:

    self.tracker.model = self.prompt_formatter.model_name

It OVERWRITES the model with the current run's, so a stale job is adopted and
made to look like it belongs. Nothing is compared.

The stale state is manufactured by editing the persisted file, which is the
only way to reach it: curator's run directory is keyed on model and dataset, so
a genuinely different configuration would land in a different directory and
never see this job. Editing the file is what a crashed run from an earlier
version of the script leaves behind.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from harness import printed_text, unmeasured

from test_open import batch_llm, rows
from test_r1 import run_dirs

pytestmark = pytest.mark.timeout(300)


def status_file(run_dir: pathlib.Path) -> pathlib.Path | None:
    """The persisted tracker, whatever the implementation called it."""
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            body = path.read_text(errors="replace")
        except OSError:
            continue
        if "batch-" in body or "batch_id" in body:
            return path
    return None


def leave_a_pending_job(run_dir: pathlib.Path, model: str | None = None) -> bool:
    """Turn a finished run's directory into what a CRASH would have left.

    This is the whole difficulty of testing t23. The requirement is about a job
    "still pending on the provider's side", and the verifier's provider
    completes batches immediately so the poller returns straight away — a
    normal run therefore leaves a DOWNLOADED batch and a full set of responses,
    with nothing left to resume. A second run then submits nothing whatever the
    implementation does, and every test here passes vacuously.

    So the finished state is walked back to the crashed one: the batch is moved
    out of `downloaded_batches` into `submitted_batches`, the response file it
    produced is removed, and the counters that say the work is done are reset.
    Optionally the recorded model is changed, which is the mismatch r2 is about.
    """
    store = status_file(run_dir)
    if store is None:
        return False
    try:
        state = json.loads(store.read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(state, dict):
        return False

    pending = {}
    for bucket in ("downloaded_batches", "finished_batches"):
        for bid, batch in (state.get(bucket) or {}).items():
            if isinstance(batch, dict):
                batch["status"] = "submitted"
                # SET to null, never remove: `finished_at` is Optional but
                # REQUIRED on GenericBatch, so popping it makes the tracker
                # fail pydantic validation. The run then died on a corrupt
                # file, and an implementation that falls back to a fresh
                # submission when it cannot read the tracker passed `rule`
                # without ever comparing the model — the right answer for the
                # wrong reason, which is worse than a failure.
                batch["finished_at"] = None
            pending[bid] = batch
        state[bucket] = {}
    if not pending:
        return False
    state["submitted_batches"] = {**(state.get("submitted_batches") or {}),
                                  **pending}
    for zeroed in ("n_final_success_requests", "n_final_failed_requests",
                   "num_parsed_responses", "n_succeeded_requests",
                   "n_finished_requests"):
        if zeroed in state:
            state[zeroed] = 0
    if model is not None:
        # Replace the recorded model EVERYWHERE, not just at the top level.
        # An implementation may record identity per batch rather than per
        # tracker — one real submission validated each batch's own model and
        # payload hash, which is the more precise design — and poisoning only
        # `state["model"]` left every batch still matching. The oracle happened
        # to read the top-level field, so it passed while the better
        # implementation failed.
        was = state.get("model")
        blob = json.dumps(state)
        if was:
            blob = blob.replace(json.dumps(was)[1:-1], model)
        state = json.loads(blob)
        state["model"] = model
    store.write_text(json.dumps(state))

    # The responses are what make the batch processor think it is finished —
    # and the .arrow dataset is what makes `run()` return before the batch
    # processor is reached at all. Both have to go, or the second run is served
    # entirely from the run-level cache and submits nothing whatever the
    # implementation does, which passed every test here vacuously.
    for pattern in ("responses*.jsonl", "response.json", "*.arrow"):
        for path in run_dir.rglob(pattern):
            path.unlink()
    return True


def stale_run(provider, monkeypatch, tmp_path, model=None, field=None,
              value=None):
    """Run, walk the run back to a crash, run again. Returns batches submitted."""
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    data = rows(2)

    provider.reset()
    batch_llm(provider)(data)
    made = run_dirs(root)
    assert made, "the first run created no run directory"
    if not leave_a_pending_job(made[0], model):
        pytest.skip("the run directory records no batch that can be put back "
                    "into a pending state, so a crashed run cannot be staged")
    if field is not None:
        store = status_file(made[0])
        state = json.loads(store.read_text())
        if field not in state:
            pytest.skip(f"the persisted job records no {field!r}, so a "
                        "mismatch on it cannot be presented")
        state[field] = value
        store.write_text(json.dumps(state))

    provider.reset()
    batch_llm(provider)(data)
    return provider.batches_created


# =============================================================================
# rule — a job from another model is not this run's job
# =============================================================================
def test_rule__a_persisted_job_for_another_model_is_not_resumed(
        provider, monkeypatch, tmp_path):
    made = stale_run(provider, monkeypatch, tmp_path, model="gpt-4o-not-this")
    assert made >= 1, (
        "a persisted batch recorded against a different MODEL was resumed "
        "rather than resubmitted; the requirement says a mismatch must cause a "
        "fresh submission")

    # The sentence names three identity fields — provider, model, payload hash
    # — and testing only the model graded a third of it. The provider is the
    # other one this harness can present; the payload hash has no field of its
    # own in the persisted job, so it is left to the model check that stands in
    # for it.
    made = stale_run(provider, monkeypatch, tmp_path,
                     field="compatible_provider", value="not-this-provider")
    assert made >= 1, (
        "a persisted batch recorded against a different PROVIDER was resumed "
        "rather than resubmitted")


# =============================================================================
# scope — resume time, and only there
# =============================================================================
def test_scope__a_matching_job_is_still_resumed(provider, monkeypatch, tmp_path):
    """"Resume-time validation" — so validation must not become "never resume".

    The cheapest way to pass `rule` is to resubmit every time, which throws
    away the feature the ticket asked for. A crashed run whose configuration
    still MATCHES must be picked up.

    This was recorded unmeasurable once, wrongly: the staging used to drop
    `finished_at` when moving a batch back to pending, which left a tracker
    that failed pydantic validation, so nothing could resume and both trees
    resubmitted. That measured the corrupt file, not the implementation.
    """
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    data = rows(2)

    provider.reset()
    batch_llm(provider)(data)
    made = run_dirs(root)
    assert made, "the first run created no run directory"
    if not leave_a_pending_job(made[0]):          # crashed, but NOT mismatched
        pytest.skip("no batch could be put back into a pending state")

    provider.reset()
    batch_llm(provider)(data)

    assert provider.batches_created == 0, (
        "a persisted job matching this run's configuration was resubmitted "
        f"anyway ({provider.batches_created} batch(es)); validation is "
        "rejecting jobs it should accept")


# =============================================================================
# failure_behavior — say why the old job was dropped
# =============================================================================
def test_failure_behavior__the_reason_for_not_resuming_is_logged(
        provider, monkeypatch, tmp_path, capfd, caplog):
    """"...with a logged reason for why the old job was not resumed, not a
    silent resume of incompatible results."

    A fresh submission is graded by `rule`; what is graded here is that the
    user is told, because a silent resubmission looks identical to a lost job.
    """
    printed_text(capfd, caplog)
    made = stale_run(provider, monkeypatch, tmp_path, model="gpt-4o-not-this")
    text = printed_text(capfd, caplog)

    assert made >= 1, "the stale job was resumed, so there is no reason to log"
    assert any(w in text.lower() for w in
               ("mismatch", "model", "resum", "stale", "differ", "new batch",
                "not match")), (
        "the persisted job was discarded and nothing said why. What was "
        f"printed:\n{text[-900:]}")
