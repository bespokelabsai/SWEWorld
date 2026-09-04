"""t23 — hidden requirement r1: persist the job id at submission time.

    rule              the batch job ID must be persisted to the on-disk cache
                      directory immediately after successful submission, before
                      polling begins
    scope             batch job ID persistence, submission-time only
    failure_behavior  if persistence itself fails (disk full, permissions), the
                      submission must still proceed — losing resumability beats
                      blocking the job — but a warning must be logged

`rule` and `scope` are largely TRUE OF BASELINE CURATOR, which already writes
`batch_objects.jsonl` right after `mark_as_submitted`
(`base_batch_request_processor.py:422-425`). They are graded anyway, because a
requirement is graded on what it says; that they do not discriminate is
recorded in the bracket rather than fixed by inventing a stricter reading.

`failure_behavior` is the one baseline gets wrong: an unwritable persistence
path takes the whole submission down with it.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from harness import printed_text

from test_open import batch_llm, rows

pytestmark = pytest.mark.timeout(300)


def run_dirs(root: pathlib.Path) -> list[pathlib.Path]:
    """The per-run directories curator made under the cache root."""
    return [p for p in root.iterdir() if p.is_dir()] if root.exists() else []


def persisted_batch_ids(root: pathlib.Path) -> list[str]:
    """Every provider batch id written anywhere under the cache root.

    Searched by CONTENT rather than by filename: the requirement says the id is
    persisted to the cache directory, not what the file is called, and an
    implementation that renamed it would otherwise fail for spelling.
    """
    found = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            body = path.read_text(errors="replace")
        except OSError:
            continue
        for token in ("batch-", "batch_"):
            if token in body:
                for line in body.splitlines():
                    if token in line:
                        found.append(line.strip()[:200])
                break
    return found


# =============================================================================
# rule — on disk, under the cache directory, once submitted
# =============================================================================
def test_rule__the_batch_id_is_on_disk_after_submission(provider, monkeypatch,
                                                        tmp_path):
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    provider.reset()
    batch_llm(provider)(rows())

    assert provider.batches_created == 1, (
        f"expected one submitted batch, the provider saw "
        f"{provider.batches_created}")
    ids = persisted_batch_ids(root)
    assert ids, (
        f"nothing under the cache directory {root} records the submitted batch "
        f"id, so a crash during polling would lose it. Files present: "
        f"{[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()][:8]}")


# =============================================================================
# scope — submission-time, in the run's own directory
# =============================================================================
def test_scope__persistence_lands_in_the_runs_cache_directory(
        provider, monkeypatch, tmp_path):
    """"...to the on-disk cache directory", not somewhere else on the box.

    Pointing CURATOR_CACHE_DIR at a fresh directory and finding the id under it
    is the whole claim.
    """
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    provider.reset()
    batch_llm(provider)(rows())

    assert run_dirs(root), f"the run wrote no directory under {root}"
    assert persisted_batch_ids(root), (
        "the batch id was not written under the cache directory this run was "
        f"pointed at ({root})")


# =============================================================================
# failure_behavior — persistence may fail; the submission may not
# =============================================================================
def test_failure_behavior__an_unwritable_store_warns_but_does_not_block(
        provider, monkeypatch, tmp_path, capfd, caplog):
    """Losing resumability beats blocking the job.

    Persistence is made to fail WITHOUT patching curator: the run directory is
    emptied and a DIRECTORY is created where the status file belongs, so every
    `open(..., "w")` on that path raises IsADirectoryError. That is an
    environment, not a fake — the same shape as a read-only mount or a full
    disk — and it is reproducible because the run directory is a pure function
    of the dataset, model and params, so the second run lands in the first
    run's directory.

    Baseline curator dies here: `update_batch_objects_file` is awaited straight
    after `mark_as_submitted` and nothing catches it, so the job is lost
    outright rather than merely un-resumable.
    """
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    data = rows(2)

    # Learn the run directory by running once.
    provider.reset()
    batch_llm(provider)(data)
    made = run_dirs(root)
    assert len(made) == 1, f"expected one run directory under {root}, saw {made}"
    run_dir = made[0]

    # Empty it so nothing is resumed, then block the status file by name.
    for path in sorted(run_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    (run_dir / "batch_objects.jsonl").mkdir()

    provider.reset()
    printed_text(capfd, caplog)                   # drop the first run's output
    error = None
    try:
        batch_llm(provider)(data)
    except Exception as exc:                      # noqa: BLE001 - classified below
        error = exc
    text = printed_text(capfd, caplog)

    if error is not None:
        pytest.fail(
            "the batch job was blocked when its status could not be persisted: "
            f"{type(error).__name__}: {error}. The requirement says losing "
            "resumability is preferable to blocking the job outright")
    assert provider.batches_created >= 1, (
        "no batch reached the provider when the status file was unwritable; "
        "the submission must still proceed")
    assert any(w in text.lower() for w in
               ("warn", "persist", "resum", "could not", "unable", "failed to")), (
        "the status file could not be written and nothing said so; the "
        f"requirement asks for a warning. What was printed:\n{text[-800:]}")
