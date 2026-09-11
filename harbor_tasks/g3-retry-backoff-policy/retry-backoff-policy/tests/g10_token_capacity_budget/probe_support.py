"""g10 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, scenario factories and tolerant
readers the probe needs to drive curator; it contains NO expected-output value
(no `-250.0`, no `0.25`, no refund numbers). That is load-bearing: `run_split`
copies this file into the worker's jail, so it is inside the process that runs
agent code. If any reward-bearing expected value ever appears here, the worker
can read it and forge a passing `observations.json`. The answers live only in
`judge.py` (and, for humans, in `test_open.py`), which the worker cannot read.

`test_open.py` imports these names so there is a single definition of each helper
— the probe cannot drift from the reference.
"""
from __future__ import annotations

import asyncio
import datetime

import pytest
from harness import read_field

_IMPORT_ERROR = None
try:
    from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        APIRequest,
        BaseOnlineRequestProcessor,
    )
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
    from bespokelabs.curator.types.generic_request import GenericRequest
    from bespokelabs.curator.types.generic_response import GenericResponse
    from bespokelabs.curator.types.token_usage import _TokenUsage
except Exception as exc:  # pragma: no cover - reported per test by importable()
    _IMPORT_ERROR = exc
    OnlineRequestProcessorConfig = APIRequest = BaseOnlineRequestProcessor = None
    OnlineStatusTracker = GenericRequest = GenericResponse = _TokenUsage = None

_BUDGET_ERROR = None
try:
    from bespokelabs.curator.status_tracker import capacity_budget as budget
except Exception as exc:  # pragma: no cover - reported per test by budget_module()
    _BUDGET_ERROR = exc
    budget = None


# ---------------------------------------------------------------------------
# Guards and tolerant readers, shared with test_r1 / test_r2
# ---------------------------------------------------------------------------
def importable():
    """Curator itself must import; anything else is an environment fault, not a grade."""
    if _IMPORT_ERROR is not None:
        pytest.fail(f"curator did not import: {_IMPORT_ERROR!r}")


def budget_module():
    """The capacity-budget module, named by the ticket, or a clear failure."""
    importable()
    if budget is None:
        pytest.fail(
            "bespokelabs.curator.status_tracker.capacity_budget did not import: "
            f"{_BUDGET_ERROR!r}"
        )
    return budget


_MISSING = object()


def find_const(name, *aliases, default=_MISSING):
    """A module-level constant, looked up in the module the ticket names.

    Also looked for in `online_status_tracker`, which the ticket says re-exports the
    same names for existing importers, so an implementation that put the canonical
    definition on either side is read the same way. Returns `default` when nothing
    answers to any of the names.
    """
    import sys

    homes = [budget_module()]
    tracker_mod = sys.modules.get(getattr(OnlineStatusTracker, "__module__", ""), None)
    if tracker_mod is not None:
        homes.append(tracker_mod)
    for candidate in (name, *aliases):
        for home in homes:
            if hasattr(home, candidate):
                return getattr(home, candidate)
    return default


def const(name, *aliases):
    """`find_const`, but a missing constant is a failed requirement rather than a None."""
    value = find_const(name, *aliases)
    if value is _MISSING:
        pytest.fail(f"no constant named {name!r} on the capacity budget module")
    return value


class Clock:
    """A callable clock whose `now` a test sets. No sleeping, no wall clock."""

    def __init__(self, now: float = 1000.0):
        self.now = float(now)

    def __call__(self) -> float:
        return self.now


def T(**kw):
    """`_TokenUsage(input=..., output=...)`, shorter."""
    return _TokenUsage(**kw)


def tracker(**kw):
    """An `OnlineStatusTracker` on an injected clock, with a model that is priced."""
    kw.setdefault("model", "gpt-4o-mini")
    kw.setdefault("capacity_clock", Clock(1000.0))
    return OnlineStatusTracker(**kw)


def token_axes(capacity):
    """`(input, output, total)` of a token capacity, whatever shape it is in.

    Under `combined` a single number is the total and the axes are unknown; under
    `seperate` the three come off the `_TokenUsage`. `None` means unlimited.
    """
    if capacity is None:
        return (None, None, None)
    if isinstance(capacity, (int, float)):
        return (None, None, capacity)
    return (
        read_field(capacity, "input"),
        read_field(capacity, "output"),
        read_field(capacity, "total"),
    )


def reading_fields(reading):
    """The four fields of a `RateLimitReading`, by the names the ticket fixes."""
    return (
        read_field(reading, "max_requests_per_minute"),
        read_field(reading, "max_tokens_per_minute"),
        read_field(reading, "token_limit_strategy"),
        tuple(read_field(reading, "source_headers")),
    )


class NullFormatter:
    """`prompt_formatter.response_to_response_format` is called on the success path."""

    def response_to_response_format(self, message):
        return None


class NullViewer:
    """`_viewer_client.log_cost_projection` is awaited on the success path."""

    async def log_cost_projection(self, status_tracker, force_log=False):
        return None


class StubProcessor(BaseOnlineRequestProcessor if BaseOnlineRequestProcessor else object):
    """The five abstract methods, a counted estimator and a queue of canned responses.

    No sockets: `call_single_request` hands back whatever the test put in `responses`,
    and `append_generic_response` writes nothing.
    """

    def __init__(self, estimate):
        super().__init__(OnlineRequestProcessorConfig(model="gpt-4o-mini"))
        self._estimate = estimate
        self.estimate_calls = 0
        self.responses = []
        self.appended = []
        self.prompt_formatter = NullFormatter()
        self._viewer_client = NullViewer()

    # --- the five abstract methods -----------------------------------------
    def file_upload_limit_check(self, base64_image: str) -> None:
        return None

    def estimate_total_tokens(self, messages: list):
        self.estimate_calls += 1
        return T(input=self._estimate.input, output=self._estimate.output)

    def estimate_output_tokens(self) -> int:
        return self._estimate.output

    def create_api_specific_request_online(self, generic_request):
        return {}

    async def call_single_request(self, request, session, status_tracker):
        return self.responses.pop(0)

    # --- no I/O ------------------------------------------------------------
    async def append_generic_response(self, status_tracker, data, filename) -> None:
        self.appended.append(data)


def make_request(attempts_left: int = 0):
    generic = GenericRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        original_row={},
        original_row_idx=0,
    )
    return APIRequest(
        task_id=0,
        generic_request=generic,
        api_specific_request={},
        attempts_left=attempts_left,
    )


def make_response(finish_reason: str, usage):
    generic = GenericRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        original_row={},
        original_row_idx=0,
    )
    now = datetime.datetime.now()
    return GenericResponse(
        response_message={"answer": "ok"},
        response_errors=None,
        raw_request={},
        raw_response={},
        generic_request=generic,
        created_at=now,
        finished_at=now,
        token_usage=usage,
        response_cost=0.0,
        finish_reason=finish_reason,
    )


def run_attempt(proc, status_tracker, blocked, *, attempts_left: int, response):
    """One trip through `handle_single_request_with_retries`, no real waiting.

    `asyncio.run` rather than pytest-asyncio: the coroutine awaits nothing but the
    stubs, so a plain event loop per call keeps the suite free of an asyncio_mode
    setting it does not control.
    """

    async def drive():
        proc.responses.append(response)
        request = make_request(attempts_left=attempts_left)
        await proc.handle_single_request_with_retries(
            request=request,
            session=None,
            retry_queue=asyncio.Queue(),
            response_file="unused",
            status_tracker=status_tracker,
            blocked_capacity=blocked,
        )
        return request

    return asyncio.run(drive())
