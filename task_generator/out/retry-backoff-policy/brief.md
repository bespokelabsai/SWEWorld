Retry policy for online requests: what a failed request costs before it is tried
again, and how a caller can tell which failures were which.

The area, concretely:
- `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` —
  the `APIRequest` dataclass (line 43, `attempts_left`), seeded from
  `config.max_retries` at line 374; `handle_single_request_with_retries()`
  (line 474) whose `except Exception as e:` block (lines 526-563) increments
  `num_other_errors` (line 527) for every failure alike, decrements
  `attempts_left` (line 537) and re-queues with `retry_queue.put_nowait(request)`
  (line 543) — immediately, with no delay of any kind; and the permanent-failure
  path (lines 545-563), which collapses the accumulated errors with `Counter`
  into `f"{error}(x{count})"`.
- `cool_down_if_rate_limit_error()` (line 298) — a flat, global
  `seconds_to_pause_on_rate_limit` sleep computed off
  `status_tracker.time_of_last_rate_limit_error`, awaited before every request
  in both the main loop (line 388) and the retry loop (line 436).
- The three places a rate-limit error is actually recognised, all of them in
  provider subclasses and none in the base:
  `openai_online_request_processor.py` lines 299-300,
  `anthropic_online_request_processor.py` lines 285-286,
  `litellm_online_request_processor.py` lines 429-430 — each stamping
  `time_of_last_rate_limit_error` and `num_rate_limit_errors` on the tracker.
- `status_tracker/online_status_tracker.py` — `num_rate_limit_errors` (line 56),
  `num_api_errors`, `num_other_errors`, `time_of_last_rate_limit_error`
  (line 67), and the error line those three feed (lines 148-150).
- `request_processor/config.py` — `max_retries` (line 28, default 10, `ge=0`)
  and `seconds_to_pause_on_rate_limit` (line 111, default 10, `gt=0`), the only
  two retry knobs that exist.

Three mechanisms disagree about what a retry costs, and the disagreement is
reachable. The retry queue says zero: every exception is re-queued at once. The
cooldown says a flat global pause, applied to requests that were never rate
limited. The config says one number for all error kinds. Classification lives in
three provider subclasses, so the base class cannot tell a 429 from a schema
violation and charges them the same. The attempt number is computed from the
same expression at two moments — line 424 before the attempt, line 540 after the
decrement — and both are printed. Read all of it and design the fix as one fully
specified retry policy: a classifier, a delay schedule, and one decision object
the queue, the log and the tracker all read.

Constraints: pure and deterministic, no network, no sleeping, no threads. Both
the clock and the source of jitter are injected, never read from `time` or the
`random` module inside the policy. The design must be testable by calling the
classifier and the schedule directly on exception instances and attempt numbers,
and by driving the retry decision with a fake tracker — no aiohttp session, no
event loop, no provider.
