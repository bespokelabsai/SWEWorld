"""t1 — hidden requirement r2: which cache `cache_stats()` is talking about.

Each field is graded on ITS OWN fact. The previous version opened with an
assertion about counting semantics — a cold run must report one miss — which is
r1's business, and an agent whose directory resolution was completely correct
(`cache_dir` and `run_dir` both under the directory it was pointed at) scored
zero on all four r2 fields because its counter was wrong. One defect, billed
four times, against facts it had nothing to do with.

Anything that is a precondition rather than the fact under test now goes
through `require_feature`, which says so instead of failing the field.
"""
from __future__ import annotations

import hashlib
import os
import pathlib

import pytest
from datasets import Dataset

from bespokelabs import curator

from harness import cache_stats_of, read_field, require_feature, surface

pytestmark = pytest.mark.timeout(180)

MODEL = "gpt-4o-mini"
# The requirement fixes that the directory is REPORTED, never what the field is
# called, so any plausible name counts.
PATH_NAMES = ("cache_dir", "cache_directory", "directory", "path", "dir",
              "cache_path", "resolved_cache_dir", "run_dir")


class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def llm_for(provider):
    return Describer(model_name=MODEL, backend="openai",
                     backend_params={"base_url": provider.url("api.openai.com"),
                                     "in_mtok_cost": 1000, "out_mtok_cost": 1000})


def one_row():
    return Dataset.from_list([{"topic": "cats"}])


def reported_dir(stats):
    value = read_field(stats, *PATH_NAMES, default=None)
    if value is None:
        pytest.fail(
            "cache_stats() does not report which cache directory it read; the "
            "requirement asks for it so a user can verify which cache was "
            f"inspected. Fields present: {surface(stats)}")
    return os.path.realpath(str(value))


def under(path: str, root: pathlib.Path) -> bool:
    """The root itself or anything inside it.

    `LLM.__call__` builds `<cache>/<fingerprint>` per run, so both the root and
    the run directory are defensible answers. An earlier version demanded exact
    equality with the root in one test while accepting either in two others, so
    an agent reporting the run directory passed two fields and failed one for
    nothing.
    """
    return os.path.realpath(path).startswith(os.path.realpath(str(root)))


def tree(root: pathlib.Path) -> dict:
    """Every file under `root` by size and hash.

    curator's own logging is excluded: `log.add_file_handler` attaches a
    RotatingFileHandler inside the run directory and never detaches it, so any
    later log line rewrites that file through no fault of the agent.
    """
    out = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("curator.log") \
                or path.name.endswith("-journal"):
            continue
        body = path.read_bytes()
        out[str(path.relative_to(root))] = (len(body),
                                            hashlib.sha256(body).hexdigest())
    return out


# =============================================================================
# rule — honours CURATOR_CACHE_DIR at call time, and never writes to it
# =============================================================================
def test_rule__cache_stats_reads_the_configured_dir_and_does_not_mutate_it(
        provider, monkeypatch, tmp_path):
    """The sentence makes two claims, and this grades both.

    (1) `cache_stats()` reads the directory the rest of `curator.LLM` used,
    honouring `CURATOR_CACHE_DIR`. (2) It never writes to or mutates it.

    What is NOT graded: whether the environment variable is re-read on every
    call. An earlier version repointed `CURATOR_CACHE_DIR` at an empty
    directory after the run and demanded the next call describe THAT one. But
    "the same on-disk cache directory the rest of `curator.LLM` uses" is the
    directory the run used, and reporting it is at least as faithful as
    re-resolving. The words "at call time" appear in `scope`, and are
    themselves ambiguous between the `LLM` call and the `cache_stats()` call.
    A real agent lost this field to that ambiguity.
    """
    root = tmp_path / "cache-a"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    llm = llm_for(provider)
    llm(one_row())

    before = tree(root)
    stats = cache_stats_of(llm)
    after = tree(root)
    changed = [name for name in set(before) | set(after)
               if before.get(name) != after.get(name)]
    assert not changed, (
        f"cache_stats() changed {len(changed)} file(s) under the cache "
        f"directory it was only supposed to read: {changed[:5]}")
    assert under(reported_dir(stats), root), (
        f"the run used {root}, honouring CURATOR_CACHE_DIR, but cache_stats() "
        f"reports {reported_dir(stats)}")


# =============================================================================
# scope — the directory the run actually used
# =============================================================================
def test_scope__cache_stats_reads_the_directory_the_run_used(
        provider, monkeypatch, tmp_path):
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    llm = llm_for(provider)
    response = llm(one_row())

    run_dir = getattr(response, "cache_dir", None)
    require_feature(bool(run_dir), "a run directory on the response to compare against")
    assert under(reported_dir(cache_stats_of(llm)), root), (
        f"the run wrote to {run_dir} under {root}, but cache_stats() reports "
        f"{reported_dir(cache_stats_of(llm))}")


# =============================================================================
# failure_behavior
# =============================================================================
def test_failure_behavior__a_missing_cache_dir_returns_zeroed_stats(
        provider, monkeypatch, tmp_path):
    """No prior run at all: zeros, not an exception."""
    missing = tmp_path / "never-created"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(missing))
    llm = llm_for(provider)

    try:
        stats = cache_stats_of(llm)
    except Exception as exc:                      # noqa: BLE001 - the point
        pytest.fail("a cache directory that does not exist yet raised "
                    f"{type(exc).__name__}: {exc}, instead of returning zeroed "
                    "stats")

    # The claim graded here is "rather than raising a file-not-found error" —
    # reaching this line at all is most of it.
    #
    # NOT asserted: that the miss count is zero. "Zeroed stats" is ambiguous
    # between all-zeros and zero-HITS, and the planted clue for this very fact
    # endorses the second reading in so many words: "For a machine with no
    # history ... all hits at zero and everything counted as going to the
    # provider." An agent who read the corpus and reported the rows as misses
    # was following the clue, and this test failed it for that.
    #
    # hit_rate is asserted because both readings agree on it: with no prior run
    # nothing was served from the cache either way.
    rate = read_field(stats, "hit_rate", default=0.0)
    assert rate in (0.0, 0), (
        f"no prior run, so nothing came from the cache and hit_rate should be "
        f"zero; reported {stats!r}")


# =============================================================================
# observability
# =============================================================================
def test_observability__the_resolved_cache_dir_is_reported(
        provider, monkeypatch, tmp_path):
    root = tmp_path / "cache"
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(root))
    llm = llm_for(provider)
    llm(one_row())

    assert under(reported_dir(cache_stats_of(llm)), root), (
        "the directory cache_stats() reports is not the one it was pointed at")
