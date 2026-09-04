#!/usr/bin/env python3
"""Reference implementation of t3 — a limiter shared between chained blocks.

    python3 t3_oracle.py <checkout>

Four edits, each next to the fact it satisfies. The seams are clean: the rpm
and tpm a block ends up on come from two properties on
`BaseOnlineRequestProcessor`, and a shared limiter only has to win there.
"""
from __future__ import annotations

import pathlib
import sys

CONFIG_REL = "src/bespokelabs/curator/request_processor/config.py"
ONLINE_REL = "src/bespokelabs/curator/request_processor/online/base_online_request_processor.py"

LIMITER = '''

class SharedRateLimiter:
    """One request/token budget, shared by every block that is handed it.

    r3.r2.observability names `remaining_budget()`, so that is the accessor.
    The budget is per-process and is RESET at the start of each top-level
    invocation rather than carried over: a limiter that arrives exhausted from
    the previous run leaves the next one with nothing, which is the failure the
    requirement describes.
    """

    def __init__(self, max_requests_per_minute: int | None = None,
                 max_tokens_per_minute: int | None = None):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.available_request_capacity = float(max_requests_per_minute or 0)
        self.available_token_capacity = float(max_tokens_per_minute or 0)

    def reset(self) -> None:
        """Start an invocation with the full budget."""
        self.available_request_capacity = float(self.max_requests_per_minute or 0)
        self.available_token_capacity = float(self.max_tokens_per_minute or 0)

    def remaining_budget(self) -> dict:
        return {"requests": self.available_request_capacity,
                "tokens": self.available_token_capacity}


'''


def edit(path: pathlib.Path, old: str, new: str, what: str, marker: str) -> None:
    body = path.read_text()
    if marker in body:
        print(f"  = {what} (already applied)")
        return
    if old not in body:
        raise SystemExit(f"could not apply {what}: anchor not found in {path}")
    path.write_text(body.replace(old, new, 1))
    print(f"  + {what}")


def main(root: str) -> int:
    config = pathlib.Path(root) / CONFIG_REL
    online = pathlib.Path(root) / ONLINE_REL
    for path in (config, online):
        if not path.exists():
            raise SystemExit(f"missing {path}")

    # -- the limiter, and the slot that carries it --------------------------
    body = config.read_text()
    if "class SharedRateLimiter" not in body:
        idx = body.index("class RequestProcessorConfig")
        config.write_text(body[:idx] + LIMITER.lstrip("\n") + body[idx:])
        print("  + SharedRateLimiter")

    # `Any`, because a pydantic model cannot carry an arbitrary class without
    # it — and `extra = "forbid"` means the field has to be declared to be
    # passable at all, which is what makes "did the agent add a knob?" a
    # question the config answers.
    edit(config,
         "    seconds_to_pause_on_rate_limit: int = Field(default=10, gt=0)",
         "    seconds_to_pause_on_rate_limit: int = Field(default=10, gt=0)\n"
         "    rate_limiter: _AnyType = Field(default=None)",
         "t3: the rate_limiter slot", "rate_limiter: _AnyType")
    # An unambiguous alias. config.py already says `import typing as t`, so a
    # substring check for "import typing" is satisfied and `typing.Any` is
    # never bound — the suite then dies at collection with NameError, which
    # reads as a broken test rather than a broken patch.
    body = config.read_text()
    if "_AnyType" not in body.split("class SharedRateLimiter")[0]:
        config.write_text("from typing import Any as _AnyType\n" + body)
        print("  + _AnyType alias")

    # -- r1.rule: the shared limiter wins over the block's own numbers ------
    edit(online,
         "        self.manual_max_requests_per_minute = config.max_requests_per_minute",
         '''        # r1.rule: when a limiter OBJECT is shared, the second block must NOT
        # re-initialise its budgets from its own backend_params. Reading the
        # shared configuration here is what makes the sharing real; the first
        # draft let the local numbers win, which silently defeated the point.
        self._shared_limiter = getattr(config, "rate_limiter", None)
        if self._shared_limiter is not None and not isinstance(
                self._shared_limiter, (int, float)):
            self.manual_max_requests_per_minute = \\
                self._shared_limiter.max_requests_per_minute
            self.manual_max_tokens_per_minute = \\
                self._shared_limiter.max_tokens_per_minute
        else:
            self._shared_limiter = None
            self.manual_max_requests_per_minute = config.max_requests_per_minute''',
         "t3.r1.rule: the shared limiter's budgets win",
         "self._shared_limiter = getattr(config")

    # The tpm assignment sits a line below and must not overwrite the shared
    # value, so it is made conditional in place.
    body = online.read_text()
    if "if self._shared_limiter is None:\n            self.manual_max_tokens_per_minute" not in body:
        body = body.replace(
            "        self.manual_max_tokens_per_minute = config.max_tokens_per_minute",
            "        if self._shared_limiter is None:\n"
            "            self.manual_max_tokens_per_minute = config.max_tokens_per_minute",
            1)
        online.write_text(body)
        print("  + t3.r1.rule: tpm too")

    # -- the limiter a block OFFERS ----------------------------------------
    # The ticket says "passing an EXISTING rate limiter instance" between
    # blocks, so a block has to have one to hand over. Built lazily, because
    # the effective rpm is resolved by a property that may consult response
    # headers, and is not known at __init__ time.
    edit(online,
         "    @property\n    def max_requests_per_minute(self) -> int:",
         '''    @property
    def rate_limiter(self):
        """The budget this block is working to, shareable with another block."""
        if getattr(self, "_shared_limiter", None) is None:
            self._shared_limiter = SharedRateLimiter(
                self.max_requests_per_minute, self.max_tokens_per_minute)
        return self._shared_limiter

    @property
    def max_requests_per_minute(self) -> int:''',
         "t3: a block offers its limiter", "def rate_limiter(self):")

    body = online.read_text()
    if "SharedRateLimiter" not in body.split("class BaseOnlineRequestProcessor")[0]:
        body = body.replace(
            "from bespokelabs.curator.log import logger",
            "from bespokelabs.curator.log import logger\n"
            "from bespokelabs.curator.request_processor.config import SharedRateLimiter",
            1)
        online.write_text(body)
        print("  + SharedRateLimiter import")

    # -- r2.rule / r2.scope: reset at the start of each invocation ----------
    edit(online,
         "    def requests_to_responses(",
         '''    def _reset_shared_limiter(self):
        """r2.rule: a shared limiter is RESET between top-level invocations.

        Per-process budgets that carry over leave the second run of the day
        with whatever the first left behind, which is exactly what the
        requirement forbids.
        """
        if getattr(self, "_shared_limiter", None) is not None:
            self._shared_limiter.reset()

    def requests_to_responses(''',
         "t3.r2.rule: reset between invocations", "_reset_shared_limiter")

    # Anchored on the first statement of requests_to_responses, not on "the
    # first colon after the def" — that heuristic put both calls inside
    # `cool_down_if_rate_limit_error`, above its docstring, where they run only
    # on a rate-limit error. The suite then reported "the limiter was reused
    # rather than reset" and a 45-second stall, both of which looked like the
    # implementation being wrong rather than the patch being misplaced.
    edit(online,
         """        max_requests_per_minute = self.max_requests_per_minute
        max_tokens_per_minute = self.max_tokens_per_minute""",
         """        self._reset_shared_limiter()
        max_requests_per_minute = self.max_requests_per_minute
        max_tokens_per_minute = self.max_tokens_per_minute
        self._assert_budget_is_satisfiable(64)""",
         "t3.r2: reset and budget check at the start of an invocation",
         "self._reset_shared_limiter()\n        max_requests_per_minute")

    # -- r2.failure_behavior: an unsatisfiable budget raises ----------------
    edit(online,
         "    @property\n    def max_requests_per_minute(self) -> int:",
         '''    def _assert_budget_is_satisfiable(self, needed_tokens: int = 1) -> None:
        """r2.failure_behavior: raise rather than stall.

        curator otherwise spins in `while not status_tracker.has_capacity(...)`
        with no exit when the budget can never satisfy one request, and a run
        that hangs is indistinguishable from a slow one.
        """
        budget = self.max_tokens_per_minute
        if budget is not None and 0 < budget < needed_tokens:
            raise ValueError(
                f"the token budget of {budget}/minute is smaller than a single "
                f"request needs ({needed_tokens}); it can never be satisfied, "
                "so the run would wait forever. Raise max_tokens_per_minute or "
                "reset the shared limiter.")

    @property
    def max_requests_per_minute(self) -> int:''',
         "t3.r2.failure_behavior: refuse an unsatisfiable budget",
         # The DEFINITION, not any call to it: the reset edit above inserts a
         # call, and a marker matching both makes this edit skip itself.
         "def _assert_budget_is_satisfiable")

    print("t3 oracle applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
