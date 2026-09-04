"""t23 — the openly stated feature: a restart resumes rather than resubmits.

Baseline curator already does this — `_attempt_loading_batch_status_tracker`
reads `batch_objects.jsonl` from the run directory — so the pristine tree passes
this test on purpose. It separates "built nothing" from "built it and missed
the hidden facts". What baseline does NOT do is validate that the job it found
belongs to this run, which is r2.

Everything here is measured at the provider: `batches_created` is the count of
batch submissions that actually reached the backend, so "resumed" and
"resubmitted" are a number rather than an inference about internals.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

pytestmark = pytest.mark.timeout(300)

MODEL = "gpt-4o-mini"
PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}


class Asker(curator.LLM):
    def prompt(self, input):
        return f"Answer about {input['topic']}."


def rows(n=2):
    return Dataset.from_list([{"topic": f"s{i}"} for i in range(n)])


def batch_llm(provider, model=MODEL, **params):
    return Asker(model_name=model, backend="openai", batch=True,
                 backend_params={"base_url": provider.url("api.openai.com"),
                                 "batch_check_interval": 1, **PRICES, **params})


def test_open_feature__a_second_run_resumes_instead_of_resubmitting(provider):
    provider.reset()
    batch_llm(provider)(rows())
    assert provider.batches_created == 1, (
        f"a cold batch run submitted {provider.batches_created} batch(es), want 1")

    provider.reset()
    batch_llm(provider)(rows())
    assert provider.batches_created == 0, (
        "re-running the same job submitted a second batch; the ticket asks for "
        "the pending job to be resumed rather than duplicated")
