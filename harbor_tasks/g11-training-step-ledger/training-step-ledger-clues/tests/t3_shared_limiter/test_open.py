"""t3 — the openly stated feature: two blocks, one budget.

Ported to the real provider. The limiter and the `backend_params` key that
carries it are both discovered rather than guessed — the ticket fixes neither
name, and only `remaining_budget()` is named by the requirement.
"""
from __future__ import annotations

import pytest
from datasets import Dataset

from bespokelabs import curator

from discovery import (build_limiter, find_limiter, new_config_fields,
                       shares_limiter)

pytestmark = pytest.mark.timeout(300)

PRICES = {"in_mtok_cost": 1000, "out_mtok_cost": 1000}


class Block(curator.LLM):
    def prompt(self, input):
        return f"Say something about {input['seed']}."


def seeds(n=2):
    return Dataset.from_list([{"seed": f"s{i}"} for i in range(n)])


def _base(provider):
    return {"base_url": provider.url("api.openai.com"), **PRICES}


def block(provider, **params):
    return Block(model_name="gpt-4o-mini", backend="openai",
                 backend_params={"base_url": provider.url("api.openai.com"),
                                 **PRICES, **params})


def test_open_feature__one_limiter_instance_serves_two_blocks(provider):
    """The ticket: "passing an existing rate limiter instance between two
    blocks ... so they share the same requests-per-minute budget".

    Two paths are accepted, because the ticket picks neither. Either the caller
    CONSTRUCTS the limiter and hands it to both blocks — what real agents built,
    and the plainest reading of "an existing instance" — or block one exposes
    one that can be passed on. An earlier version only tried the second and
    reported "no object looks like a limiter" for two correct implementations.
    """
    slots = new_config_fields()
    limiter, cls_name = build_limiter()
    how = f"constructed curator.{cls_name}"

    if limiter is None:
        first = block(provider, max_requests_per_minute=600)
        first(seeds())
        # require_budget=False: remaining_budget() is r2.observability, a
        # hidden fact, and the open feature must be reachable without it.
        limiter = find_limiter(first, require_budget=False)
        how = "taken off a block that had run"

    if limiter is None:
        pytest.fail(
            "no shared limiter could be reached: curator exports no new class "
            "that constructs as a limiter, and nothing on a block that has run "
            f"looks like one. New config fields seen: {slots[:3] or 'none'}")

    second = third = None
    tried = []
    for slot in slots:                           # inside backend_params
        tried.append(f"backend_params[{slot}]")
        try:
            second = block(provider, **{slot: limiter})
            second(seeds())
            third = block(provider, **{slot: limiter})
            third(seeds())
            break
        except Exception:                        # noqa: BLE001 - wrong slot
            second = third = None
    if second is None:
        # As a direct LLM argument. The TICKET says only "passing an existing
        # rate limiter instance between two blocks" and names no channel;
        # `backend_params` is named in r1.scope, a HIDDEN fact. Requiring it
        # here failed a blind agent that had built curator.RateLimiter and
        # threaded it through the LLM constructor — the open feature, done.
        for kw in ("rate_limiter", "limiter", "shared_limiter", "rate_limit"):
            tried.append(f"LLM({kw}=)")
            try:
                second = Block(model_name="gpt-4o-mini", backend="openai",
                               backend_params=_base(provider), **{kw: limiter})
                second(seeds())
                third = Block(model_name="gpt-4o-mini", backend="openai",
                              backend_params=_base(provider), **{kw: limiter})
                third(seeds())
                break
            except Exception:                    # noqa: BLE001 - wrong name
                second = third = None
    assert second is not None and third is not None, (
        f"a limiter exists ({how}) but nothing accepted it. Tried: {tried[:8]}")

    assert shares_limiter(second, limiter) and shares_limiter(third, limiter), (
        f"two blocks were built with one limiter ({how}, passed in a config "
        "field) but they are not pacing against that same object, so the "
        "budget is not shared")
