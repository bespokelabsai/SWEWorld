"""t2 — the openly stated feature: an estimate for THIS job, before submission.

Two things must hold, and the second took three attempts to get right.

**Before submission.** The provider counts batches, so "before any requests are
submitted" is checkable: at the moment the estimate is printed, no batch has
been created.

**An estimate of THIS job.** Untouched curator already prints
`Cost: Current: $0.000 • Projected: $0.000` from its batch status tracker,
before submission, with a dollar sign and the word "cost" in it. That is the
live tracker reporting zero, not a prediction, and it scored this test as
PASSED against the pristine tree. What separates the two is that a real
estimate depends on the dataset: ten times the rows, more money.
"""
from __future__ import annotations

import re

import pytest
from datasets import Dataset

from bespokelabs import curator


pytestmark = pytest.mark.timeout(300)

MODEL = "gpt-4o-mini"
MONEY = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")

# Only lines that are the ESTIMATE. curator's batch tracker prints a model
# pricing line of its own ("Per 1M tokens: Input: $500.0"), and taking the
# largest dollar figure in the output picked that up instead — identical for a
# 3-row and a 60-row job, so a correct estimator read as not depending on the
# dataset at all.
ESTIMATE_LINE = re.compile(r"estimat", re.I)


def money_on_estimate_lines(text: str) -> list[float]:
    return [float(m.replace(",", ""))
            for line in text.splitlines() if ESTIMATE_LINE.search(line)
            for m in MONEY.findall(line)]



class Describer(curator.LLM):
    def prompt(self, input):
        return f"Describe {input['topic']} in one sentence."


def rows(n):
    return Dataset.from_list([{"topic": f"subject {i}"} for i in range(n)])


def batch_llm(provider, **params):
    return Describer(model_name=MODEL, backend="openai", batch=True,
                     backend_params={"base_url": provider.url("api.openai.com"),
                                     "batch_check_interval": 1,
                                     "in_mtok_cost": 1000, "out_mtok_cost": 1000,
                                     **params})


def preflight_money(provider, n, output) -> tuple[list, str]:
    """Every dollar figure printed on an estimate line for an n-row job.

    Returns them ALL rather than the largest. `max()` picked the wrong number:
    an implementation that prints its per-1M-token rate on the same line — a
    discounted 500.0 against the 1000.0 configured here — put a constant above
    the job total, so a correct estimate read as "does not depend on the
    dataset" and failed the open feature.
    """
    output()
    batch_llm(provider)(rows(n))
    text = output()
    return money_on_estimate_lines(text), text


def test_open_feature__an_estimate_for_this_job_is_printed(provider, output):
    small, _ = preflight_money(provider, 3, output)
    provider.reset()
    large, text = preflight_money(provider, 60, output)

    assert large, (
        "no dollar figure reached the terminal for a 60-row batch job. What was "
        f"printed:\n{text[-1200:]}")

    # Figures printed identically for both jobs are CONSTANTS — a per-token
    # rate, a $0.000 projection from curator's own tracker — so they cancel.
    # What is left has to grow with the dataset, which is what makes it an
    # estimate of THIS job rather than a number that is always the same.
    varies_large = set(large) - set(small)
    varies_small = set(small) - set(large)
    assert varies_large and max(varies_large) > max(varies_small | {0.0}), (
        f"a 3-row job printed {sorted(small)} and a 60-row job printed "
        f"{sorted(large)}; nothing grew with the dataset, so what is printed is "
        "not an estimate of this job's cost — curator's batch tracker already "
        "prints a $0.000 projection without anyone adding a pre-flight.")
