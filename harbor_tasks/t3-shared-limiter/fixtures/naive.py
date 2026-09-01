#!/usr/bin/env python3
"""The NAIVE build of t3 — a limiter you can pass, and nothing more.

    python3 t3_naive.py <checkout>

The obvious reading of the ticket: let a block hand its limiter to the next one
so they share a budget. It does NOT do the three things nobody wrote down —
the second block still re-reads its own `backend_params` (the reversed decision
the corpus plants), the budget is never reset between invocations, and there is
no `remaining_budget()` accessor.

Expected: the open feature passes, and every hidden fact fails. Any that passes
anyway is not a hidden requirement.
"""
from __future__ import annotations

import pathlib
import sys

CONFIG_REL = "src/bespokelabs/curator/request_processor/config.py"
ONLINE_REL = "src/bespokelabs/curator/request_processor/online/base_online_request_processor.py"

LIMITER = '''

class RateLimiter:
    """A requests/tokens budget two blocks can share."""

    def __init__(self, max_requests_per_minute=None, max_tokens_per_minute=None):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.available_request_capacity = float(max_requests_per_minute or 0)
        self.available_token_capacity = float(max_tokens_per_minute or 0)


'''


def main(root: str) -> int:
    config = pathlib.Path(root) / CONFIG_REL
    online = pathlib.Path(root) / ONLINE_REL

    body = config.read_text()
    if "class RateLimiter" not in body:
        idx = body.index("class RequestProcessorConfig")
        body = body[:idx] + LIMITER.lstrip("\n") + body[idx:]
    if "rate_limiter:" not in body:
        body = body.replace(
            "    seconds_to_pause_on_rate_limit: int = Field(default=10, gt=0)",
            "    seconds_to_pause_on_rate_limit: int = Field(default=10, gt=0)\n"
            "    rate_limiter: _NaiveAny = Field(default=None)", 1)
    if "_NaiveAny" not in body.split("class RateLimiter")[0]:
        body = "from typing import Any as _NaiveAny\n" + body
    config.write_text(body)

    body = online.read_text()
    if "RateLimiter" not in body.split("class BaseOnlineRequestProcessor")[0]:
        body = body.replace(
            "from bespokelabs.curator.log import logger",
            "from bespokelabs.curator.log import logger\n"
            "from bespokelabs.curator.request_processor.config import RateLimiter", 1)
    if "def rate_limiter" not in body:
        # A block offers its limiter, and takes one if given — but the local
        # numbers still win, which is exactly the draft the team reversed.
        body = body.replace(
            "    @property\n    def max_requests_per_minute(self) -> int:",
            '''    @property
    def rate_limiter(self):
        """The budget this block is working to."""
        if getattr(self, "_naive_limiter", None) is None:
            self._naive_limiter = RateLimiter(self.max_requests_per_minute,
                                              self.max_tokens_per_minute)
        return self._naive_limiter

    @property
    def max_requests_per_minute(self) -> int:''', 1)
    if "_naive_limiter = getattr(config" not in body:
        body = body.replace(
            "        self.manual_max_requests_per_minute = config.max_requests_per_minute",
            '''        self._naive_limiter = getattr(config, "rate_limiter", None)
        if self._naive_limiter is not None and not isinstance(
                self._naive_limiter, (int, float)):
            # Take the shared budget only when this block was given no numbers
            # of its own. This is the naive step: the ticket never says whose
            # numbers win, and deferring to the caller's looks respectful.
            if config.max_requests_per_minute is None:
                self.manual_max_requests_per_minute = \\
                    self._naive_limiter.max_requests_per_minute
            else:
                self.manual_max_requests_per_minute = config.max_requests_per_minute
        else:
            self._naive_limiter = None
            self.manual_max_requests_per_minute = config.max_requests_per_minute''', 1)
    online.write_text(body)
    print("t3 naive build applied: a shareable limiter, local numbers still win")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
