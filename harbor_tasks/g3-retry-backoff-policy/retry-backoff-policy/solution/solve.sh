#!/bin/bash
# Reference solution, run by `harbor run -a oracle` and by Horizon's validation
# gate — which is why it has to be real. Horizon refuses to schedule any
# evaluation against a task whose oracle does not score ~1.0:
#
#     409 Conflict: One or more tasks are blocked by the evaluation validation gate.
#
# And a real one here means more than applying a patch. `run_suites.py` clones
# and grades **the pushed `main`**, not the working tree, so an oracle that edits
# files and stops scores exactly zero with every test reporting "does not
# import". Pushing IS the solution in this world.
#
# The patch is embedded rather than read from a file beside this script: on the
# apex arms the sibling file was unreadable from the solution's own directory
# (/tests is root-owned 0700), and a heredoc has no permissions of its own. It is
# generated from fixtures/oracle.patch at build time, so it cannot drift from the
# suite that grades it.
set -uo pipefail

REPO_URL="http://worldadmin:worldadmin@git.world.local/worldadmin/curator.git"
WORK="$(mktemp -d)"

# The healthcheck should already have waited for gitea, but the oracle also runs
# in contexts that do not go through it. Cheap when it is already up.
wait-for-service --quiet gitea 2>/dev/null || true

git clone --quiet "$REPO_URL" "$WORK/curator" || { echo "oracle: clone failed"; exit 1; }
cd "$WORK/curator" || exit 1

cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
index c5e4c90..e26cc30 100644
--- a/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
@@ -1,6 +1,5 @@
 import datetime
 import os
-import time
 from typing import TypeVar
 
 import aiohttp
@@ -278,15 +277,8 @@ class AnthropicOnlineRequestProcessor(BaseOnlineRequestProcessor):
             if response is None:
                 raise Exception("Response is empty")
             elif "error" in response:
-                status_tracker.num_api_errors += 1
                 error = response["error"]
-                error_message = error.get("message", str(error))
-                if "rate limit" in error_message.lower():
-                    status_tracker.time_of_last_rate_limit_error = time.time()
-                    status_tracker.num_rate_limit_errors += 1
-                    status_tracker.num_api_errors -= 1
-                    # because handle_single_request_with_retries will double count otherwise
-                    status_tracker.num_other_errors -= 1
+                # The base class classifies and counts this failure once, from the message.
                 raise Exception(f"API error: {error}")
 
             if response_obj.status != 200:
diff --git a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
index 085c2ec..6df1ae4 100644
--- a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
@@ -8,10 +8,11 @@ import asyncio
 import datetime
 import json
 import os
+import random
 import time
 import typing as t
 from abc import ABC, abstractmethod
-from collections import Counter, deque
+from collections import deque
 from dataclasses import dataclass, field
 
 import aiofiles
@@ -23,6 +24,13 @@ from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP
 from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
+from bespokelabs.curator.request_processor.online.retry_policy import (
+    DEFAULT_THROTTLE_WAIVERS,
+    RetryPolicy,
+    format_attempt_label,
+    format_failure_summary,
+    remaining_cooldown_seconds,
+)
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
@@ -44,6 +52,9 @@ class APIRequest:
         result: List to store results/errors from attempts
         prompt_formatter: Formatter for prompts and responses
         created_at: Timestamp when request was created
+        attempts_made: Number of attempts that have already failed
+        throttle_waivers_left: Number of rate limit failures that are still free of charge
+        failure_log: List of (FailureClass, message) pairs, one per failed attempt
     """
 
     task_id: int
@@ -53,6 +64,9 @@ class APIRequest:
     result: list = field(default_factory=list)
     prompt_formatter: PromptFormatter = field(default=None)
     created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
+    attempts_made: int = 0
+    throttle_waivers_left: int = DEFAULT_THROTTLE_WAIVERS
+    failure_log: list = field(default_factory=list)
 
 
 class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
@@ -87,6 +101,8 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
         self._output_tokens_window = deque(maxlen=_MAX_OUTPUT_MVA_WINDOW)
         self._semaphore = None
 
+        self.retry_policy = RetryPolicy(clock=time.time, jitter=random.random)
+
     @property
     def backend(self) -> str:
         """Backend property."""
@@ -298,15 +314,16 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
     async def cool_down_if_rate_limit_error(self, status_tracker: OnlineStatusTracker) -> None:
         """Pause processing if a rate limit error is detected.
 
+        The pause lasts until the cooldown horizon the retry policy set on the
+        tracker, so a run that has never been throttled never waits.
+
         Args:
             status_tracker: Tracker containing rate limit status
         """
-        seconds_to_pause_on_rate_limit = self.config.seconds_to_pause_on_rate_limit
-        seconds_since_rate_limit_error = time.time() - status_tracker.time_of_last_rate_limit_error
-        remaining_seconds_to_pause = seconds_to_pause_on_rate_limit - seconds_since_rate_limit_error
-        if remaining_seconds_to_pause > 0:
-            logger.warning(f"Pausing for {int(remaining_seconds_to_pause)} seconds")
-            await asyncio.sleep(remaining_seconds_to_pause)
+        remaining = remaining_cooldown_seconds(status_tracker, time.time())
+        if remaining > 0:
+            logger.warning(f"Pausing for {int(remaining)} seconds")
+            await asyncio.sleep(remaining)
             status_tracker.last_update_time = time.time()
 
     def free_capacity(self, tracker, tokens):
@@ -421,10 +438,9 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
                     else:
                         token_estimate = _TokenUsage()  # Empty
 
-                    attempt_number = self.config.max_retries - retry_request.attempts_left
                     logger.debug(
                         f"Retrying request {retry_request.task_id} "
-                        f"(attempt #{attempt_number} of {self.config.max_retries})"
+                        f"({format_attempt_label(retry_request.attempts_made, self.config.max_retries)})"
                         f"Previous errors: {retry_request.result}"
                     )
 
@@ -524,8 +540,18 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
             await self._viewer_client.log_cost_projection(status_tracker)
 
         except Exception as e:
-            status_tracker.num_other_errors += 1
+            verdict = self.retry_policy.decide(
+                e,
+                attempts_made=request.attempts_made,
+                attempts_left=request.attempts_left,
+                throttle_waivers_left=request.throttle_waivers_left,
+            )
+            self.retry_policy.apply_to_tracker(status_tracker, verdict)
             request.result.append(e)
+            request.failure_log.append((verdict.failure_class, str(e)))
+            request.attempts_made = verdict.attempt_index
+            request.attempts_left = verdict.attempts_left_after
+            request.throttle_waivers_left = verdict.throttle_waivers_after
 
             if generic_response and generic_response.token_usage is not None:
                 used_tokens: _TokenUsage = _TokenUsage(input=generic_response.token_usage.input, output=generic_response.token_usage.output)
@@ -533,19 +559,20 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
             else:
                 status_tracker.update_cost_projection(None)
 
-            if request.attempts_left > 0:
-                request.attempts_left -= 1
+            if verdict.should_retry:
                 logger.warning(
-                    f"Encountered '{e.__class__.__name__}: {e}' during attempt "
-                    f"{self.config.max_retries - request.attempts_left} of {self.config.max_retries} "
-                    f"while processing request {request.task_id}"
+                    f"Encountered '{e.__class__.__name__}: {e}' [{verdict.reason_code}] during "
+                    f"{format_attempt_label(verdict.attempt_index - 1, self.config.max_retries)} "
+                    f"while processing request {request.task_id}; "
+                    f"retrying in {verdict.delay_seconds}s"
                 )
+                request.retry_not_before = self.retry_policy._clock() + verdict.delay_seconds
                 retry_queue.put_nowait(request)
             else:
-                error_counts = Counter(str(err) for err in request.result)
-                formatted_errors = [f"{error}(x{count})" for error, count in error_counts.items()]
+                formatted_errors = format_failure_summary(request.failure_log)
                 logger.error(
-                    f"Request {request.task_id} failed permanently after exhausting all {self.config.max_retries} retry attempts. "
+                    f"Request {request.task_id} failed permanently [{verdict.reason_code}] after "
+                    f"{format_attempt_label(verdict.attempt_index - 1, self.config.max_retries)}. "
                     f"Errors: {formatted_errors}"
                 )
 
diff --git a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
index 276755b..6d60776 100644
--- a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
@@ -1,5 +1,4 @@
 import datetime
-import time
 from collections import defaultdict
 
 import aiohttp
@@ -426,10 +425,7 @@ class LiteLLMOnlineRequestProcessor(BaseOnlineRequestProcessor):
                 else:
                     response_message = completion_obj["choices"][0]["message"]["content"]
         except litellm.RateLimitError as e:
-            status_tracker.time_of_last_rate_limit_error = time.time()
-            status_tracker.num_rate_limit_errors += 1
-            # because handle_single_request_with_retries will double count otherwise
-            status_tracker.num_api_errors -= 1
+            # The base class classifies and counts this failure once.
             raise e
 
         # Extract token usage
diff --git a/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
index e46f417..e96bed9 100644
--- a/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
@@ -1,7 +1,6 @@
 import datetime
 import json
 import os
-import time
 
 import aiohttp
 import litellm
@@ -292,15 +291,8 @@ class OpenAIOnlineRequestProcessor(BaseOnlineRequestProcessor, OpenAIRequestMixi
         if response is None:
             raise Exception("Response is empty")
         elif "error" in response:
-            status_tracker.num_api_errors += 1
             error = response["error"]
-            error_message = error if isinstance(error, str) else error.get("message", "")
-            if "rate limit" in error_message.lower():
-                status_tracker.time_of_last_rate_limit_error = time.time()
-                status_tracker.num_rate_limit_errors += 1
-                status_tracker.num_api_errors -= 1
-                # because handle_single_request_with_retries will double count otherwise
-                status_tracker.num_other_errors -= 1
+            # The base class classifies and counts this failure once, from the message.
             raise Exception(f"API error: {error}")
 
         if self.config.return_completions_object:
diff --git a/src/bespokelabs/curator/request_processor/online/retry_policy.py b/src/bespokelabs/curator/request_processor/online/retry_policy.py
new file mode 100644
index 0000000..8fc5cc4
--- /dev/null
+++ b/src/bespokelabs/curator/request_processor/online/retry_policy.py
@@ -0,0 +1,364 @@
+"""Failure classification and retry backoff policy for online request processors.
+
+This module is deliberately pure: it knows nothing about ``aiohttp``, the event
+loop, the wall clock or the random module. The clock and the jitter source are
+injected into :class:`RetryPolicy`, which makes every decision reproducible and
+testable without a network or an event loop.
+"""
+
+from __future__ import annotations
+
+import dataclasses
+import enum
+import typing as t
+
+
+class FailureClass(str, enum.Enum):
+    """The kind of failure an exception represents.
+
+    Attributes:
+        THROTTLE: The provider asked us to slow down (rate limit, overload, quota).
+        TRANSIENT: A failure that is expected to go away on its own.
+        CONTRACT: The response came back but did not satisfy the request's contract.
+        TERMINAL: A failure that retrying cannot fix (auth, permissions, missing model).
+    """
+
+    THROTTLE = "throttle"
+    TRANSIENT = "transient"
+    CONTRACT = "contract"
+    TERMINAL = "terminal"
+
+
+_STATUS_CLASS: dict[int, FailureClass] = {
+    400: FailureClass.CONTRACT,
+    401: FailureClass.TERMINAL,
+    403: FailureClass.TERMINAL,
+    404: FailureClass.TERMINAL,
+    408: FailureClass.TRANSIENT,
+    409: FailureClass.TRANSIENT,
+    413: FailureClass.CONTRACT,
+    422: FailureClass.CONTRACT,
+    425: FailureClass.TRANSIENT,
+    429: FailureClass.THROTTLE,
+    529: FailureClass.THROTTLE,
+}
+
+_TYPE_CLASS: dict[str, FailureClass] = {
+    "TimeoutError": FailureClass.TRANSIENT,
+    "ConnectionError": FailureClass.TRANSIENT,
+    "ClientConnectorError": FailureClass.TRANSIENT,
+    "ValueError": FailureClass.CONTRACT,
+    "ValidationError": FailureClass.CONTRACT,
+    "JSONDecodeError": FailureClass.CONTRACT,
+    "KeyError": FailureClass.CONTRACT,
+    "PermissionError": FailureClass.TERMINAL,
+    "NotImplementedError": FailureClass.TERMINAL,
+}
+
+_MESSAGE_MARKERS: tuple[tuple[str, FailureClass], ...] = (
+    ("rate limit", FailureClass.THROTTLE),
+    ("ratelimit", FailureClass.THROTTLE),
+    ("too many requests", FailureClass.THROTTLE),
+    ("overloaded", FailureClass.THROTTLE),
+    ("quota", FailureClass.THROTTLE),
+    ("timed out", FailureClass.TRANSIENT),
+    ("timeout", FailureClass.TRANSIENT),
+    ("connection reset", FailureClass.TRANSIENT),
+    ("temporarily unavailable", FailureClass.TRANSIENT),
+    ("response is empty", FailureClass.TRANSIENT),
+    ("invalid api key", FailureClass.TERMINAL),
+    ("authentication", FailureClass.TERMINAL),
+    ("permission denied", FailureClass.TERMINAL),
+)
+
+_DEFAULT_CLASS: FailureClass = FailureClass.TRANSIENT
+
+# (base_seconds, factor, cap_seconds)
+_SCHEDULE: dict[FailureClass, tuple[float, float, float]] = {
+    FailureClass.THROTTLE: (8.0, 2.0, 60.0),
+    FailureClass.TRANSIENT: (0.5, 3.0, 20.0),
+    FailureClass.CONTRACT: (0.0, 1.0, 0.0),
+    FailureClass.TERMINAL: (0.0, 1.0, 0.0),
+}
+
+# attempts deducted from APIRequest.attempts_left; None == not retryable
+_ATTEMPT_COST: dict[FailureClass, int | None] = {
+    FailureClass.THROTTLE: 1,  # 0 while a waiver remains, see RetryPolicy.decide
+    FailureClass.TRANSIENT: 1,
+    FailureClass.CONTRACT: 2,
+    FailureClass.TERMINAL: None,
+}
+
+_TRACKER_FIELD: dict[FailureClass, str] = {
+    FailureClass.THROTTLE: "num_rate_limit_errors",
+    FailureClass.TRANSIENT: "num_api_errors",
+    FailureClass.TERMINAL: "num_api_errors",
+    FailureClass.CONTRACT: "num_other_errors",
+}
+
+DEFAULT_THROTTLE_WAIVERS: int = 6
+
+
+def _status_of(exc: BaseException) -> t.Any:
+    """Read the HTTP status an exception carries, if it carries one."""
+    status = getattr(exc, "status_code", None)
+    if status is None:
+        status = getattr(exc, "status", None)
+    return status
+
+
+def _class_from_status(exc: BaseException) -> FailureClass | None:
+    """Classify by HTTP status, or return None when the status is absent or unrecognised."""
+    status = _status_of(exc)
+    if not isinstance(status, int):
+        return None
+    if status in _STATUS_CLASS:
+        return _STATUS_CLASS[status]
+    if 500 <= status <= 599:
+        return FailureClass.TRANSIENT
+    return None
+
+
+def _class_from_type(exc: BaseException) -> FailureClass | None:
+    """Classify by exception type name, walking the MRO so subclasses inherit their base's class."""
+    for klass in type(exc).__mro__:
+        failure_class = _TYPE_CLASS.get(klass.__name__)
+        if failure_class is not None:
+            return failure_class
+    return None
+
+
+def _class_from_message(exc: BaseException) -> FailureClass | None:
+    """Classify by the first matching marker, in marker order rather than message order."""
+    message = str(exc).lower()
+    for marker, failure_class in _MESSAGE_MARKERS:
+        if marker in message:
+            return failure_class
+    return None
+
+
+def classify_failure(exc: BaseException) -> FailureClass:
+    """Map an exception to exactly one failure class.
+
+    Signals are consulted in a fixed order and the first one that yields a class
+    wins: HTTP status, then exception type, then message markers, then the
+    default. This function never raises.
+
+    Args:
+        exc: The exception raised while processing a request.
+
+    Returns:
+        The failure class the exception belongs to.
+    """
+    for signal in (_class_from_status, _class_from_type, _class_from_message):
+        try:
+            failure_class = signal(exc)
+        except Exception:  # classification must never raise
+            failure_class = None
+        if failure_class is not None:
+            return failure_class
+    return _DEFAULT_CLASS
+
+
+@dataclasses.dataclass(frozen=True)
+class RetryVerdict:
+    """The decision taken about a single failed attempt.
+
+    Attributes:
+        should_retry: True when the caller should re-queue the request.
+        failure_class: The class the failure was assigned to.
+        attempt_index: 1-based index of the attempt that just failed.
+        delay_seconds: How long to wait before the retry; 0.0 when not retrying.
+        attempts_left_after: What ``APIRequest.attempts_left`` becomes.
+        throttle_waivers_after: What ``APIRequest.throttle_waivers_left`` becomes.
+        tracker_field: Name of the ``OnlineStatusTracker`` counter to increment.
+        reason_code: ``"<failure class>:<retry|exhausted|abort>"``.
+    """
+
+    should_retry: bool
+    failure_class: FailureClass
+    attempt_index: int
+    delay_seconds: float
+    attempts_left_after: int
+    throttle_waivers_after: int
+    tracker_field: str
+    reason_code: str
+
+
+class RetryPolicy:
+    """Prices failures against a request's retry budget and schedules the backoff.
+
+    Args:
+        clock: Returns the current time in seconds; called only when a throttle
+            verdict is applied to a tracker.
+        jitter: Returns a value in ``[0.0, 1.0]``; called once per positive delay.
+    """
+
+    def __init__(
+        self,
+        clock: t.Callable[[], float],
+        jitter: t.Callable[[], float],
+    ) -> None:
+        """Initialize the RetryPolicy with an injected clock and jitter source."""
+        self._clock = clock
+        self._jitter = jitter
+
+    def delay_for(self, failure_class: FailureClass, attempt_index: int) -> float:
+        """Compute the backoff delay for an attempt.
+
+        The cap is applied before jitter, so the result never exceeds the class's
+        cap. The jitter source is consumed only when the delay is positive.
+
+        Args:
+            failure_class: The class of the failure being retried.
+            attempt_index: 1-based index of the attempt that just failed.
+
+        Returns:
+            The delay in seconds, rounded to three decimals.
+
+        Raises:
+            ValueError: If attempt_index is less than 1.
+        """
+        if attempt_index < 1:
+            raise ValueError(f"attempt_index must be >= 1, got {attempt_index}")
+        base, factor, cap = _SCHEDULE[failure_class]
+        raw = min(cap, base * factor ** (attempt_index - 1))
+        if raw <= 0:
+            return 0.0
+        jitter = min(1.0, max(0.0, self._jitter()))
+        return round(raw * (0.5 + 0.5 * jitter), 3)
+
+    def decide(
+        self,
+        exc: BaseException,
+        *,
+        attempts_made: int,
+        attempts_left: int,
+        throttle_waivers_left: int,
+    ) -> RetryVerdict:
+        """Decide what to do about a failed attempt.
+
+        Args:
+            exc: The exception raised by the attempt.
+            attempts_made: How many attempts have already failed for this request.
+            attempts_left: The request's remaining retry budget.
+            throttle_waivers_left: How many throttles the request may absorb for free.
+
+        Returns:
+            The verdict for this attempt.
+        """
+        failure_class = classify_failure(exc)
+        attempt_index = attempts_made + 1
+        tracker_field = _TRACKER_FIELD[failure_class]
+        cost = _ATTEMPT_COST[failure_class]
+
+        if cost is None:
+            return RetryVerdict(
+                should_retry=False,
+                failure_class=failure_class,
+                attempt_index=attempt_index,
+                delay_seconds=0.0,
+                attempts_left_after=0,
+                throttle_waivers_after=throttle_waivers_left,
+                tracker_field=tracker_field,
+                reason_code=f"{failure_class.value}:abort",
+            )
+
+        throttle_waivers_after = throttle_waivers_left
+        if failure_class is FailureClass.THROTTLE:
+            if throttle_waivers_left > 0:
+                cost = 0
+                throttle_waivers_after = throttle_waivers_left - 1
+            else:
+                cost = 1
+                throttle_waivers_after = 0
+
+        if attempts_left - cost < 0:
+            return RetryVerdict(
+                should_retry=False,
+                failure_class=failure_class,
+                attempt_index=attempt_index,
+                delay_seconds=0.0,
+                attempts_left_after=0,
+                throttle_waivers_after=throttle_waivers_after,
+                tracker_field=tracker_field,
+                reason_code=f"{failure_class.value}:exhausted",
+            )
+
+        return RetryVerdict(
+            should_retry=True,
+            failure_class=failure_class,
+            attempt_index=attempt_index,
+            delay_seconds=self.delay_for(failure_class, attempt_index),
+            attempts_left_after=attempts_left - cost,
+            throttle_waivers_after=throttle_waivers_after,
+            tracker_field=tracker_field,
+            reason_code=f"{failure_class.value}:retry",
+        )
+
+    def apply_to_tracker(self, tracker: t.Any, verdict: RetryVerdict) -> None:
+        """Record a verdict on a status tracker.
+
+        Exactly one error counter is incremented. A throttle additionally stamps
+        the tracker's cooldown horizon, which only ever moves forward.
+
+        Args:
+            tracker: The ``OnlineStatusTracker`` to update.
+            verdict: The verdict to record.
+        """
+        setattr(tracker, verdict.tracker_field, getattr(tracker, verdict.tracker_field) + 1)
+        if verdict.failure_class is FailureClass.THROTTLE:
+            now = self._clock()
+            tracker.time_of_last_rate_limit_error = now
+            tracker.throttle_cooldown_until = max(tracker.throttle_cooldown_until, now + verdict.delay_seconds)
+
+
+def remaining_cooldown_seconds(tracker: t.Any, now: float) -> float:
+    """Return how much of the tracker's throttle cooldown is still ahead of ``now``.
+
+    Args:
+        tracker: The ``OnlineStatusTracker`` holding the cooldown horizon.
+        now: The current time in seconds.
+
+    Returns:
+        The remaining cooldown in seconds, never negative.
+    """
+    return max(0.0, round(tracker.throttle_cooldown_until - now, 3))
+
+
+def format_failure_summary(
+    failure_log: t.Sequence[tuple[FailureClass, str]],
+) -> list[str]:
+    """Summarize a request's failure log, most frequent failure first.
+
+    Args:
+        failure_log: The ``(failure class, message)`` pairs recorded for a request.
+
+    Returns:
+        One ``"[class] message (xN)"`` line per distinct pair, sorted by count
+        descending and, for ties, by first occurrence.
+    """
+    counts: dict[tuple[FailureClass, str], int] = {}
+    first_seen: dict[tuple[FailureClass, str], int] = {}
+    for index, entry in enumerate(failure_log):
+        key = (entry[0], entry[1])
+        if key not in counts:
+            counts[key] = 0
+            first_seen[key] = index
+        counts[key] += 1
+
+    ordered = sorted(counts.items(), key=lambda item: (-item[1], first_seen[item[0]]))
+    return [f"[{failure_class.value}] {message} (x{count})" for (failure_class, message), count in ordered]
+
+
+def format_attempt_label(attempts_made: int, max_retries: int) -> str:
+    """Label the attempt that follows ``attempts_made`` failures.
+
+    Args:
+        attempts_made: How many attempts have already failed.
+        max_retries: The configured retry budget; total attempts is one more.
+
+    Returns:
+        A label such as ``"attempt #1 of 11"``.
+    """
+    return f"attempt #{attempts_made + 1} of {max_retries + 1}"
diff --git a/src/bespokelabs/curator/status_tracker/online_status_tracker.py b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
index 7603945..62c0532 100644
--- a/src/bespokelabs/curator/status_tracker/online_status_tracker.py
+++ b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
@@ -65,6 +65,7 @@ class OnlineStatusTracker:
     pbar: Optional[tqdm.tqdm] = field(default=None, repr=False, compare=False)
     response_cost: float = 0
     time_of_last_rate_limit_error: float = field(default=0.0)
+    throttle_cooldown_until: float = field(default=0.0)
 
     # Stats tracking
     total_requests: int = 0
CURATOR_ORACLE_PATCH_EOF

git apply --whitespace=nowarn /tmp/oracle.patch || { echo "oracle: patch did not apply"; exit 1; }
rm -f /tmp/oracle.patch

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "Failure-class retry policy for online request processors" || { echo "oracle: nothing to commit"; exit 1; }

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world — but the first is one round trip and
# the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/retry-backoff-policy"
  git push --quiet --force origin "HEAD:$BRANCH" || { echo "oracle: push failed"; exit 1; }
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \
        -H 'Content-Type: application/json' "$API/pulls" \
        -d "{\"head\":\"$BRANCH\",\"base\":\"main\",\"title\":\"oracle: retry-backoff-policy\"}" \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number",""))' 2>/dev/null)
  [ -n "$NUM" ] || { echo "oracle: could not open a PR"; exit 1; }
  curl -sS -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
    "$API/pulls/$NUM/merge" -d '{"Do":"merge"}' >/dev/null \
    || { echo "oracle: merge failed"; exit 1; }
  echo "oracle: merged PR #$NUM into main"
fi

# Not required by the score — `score.py` sets reward = hidden_mean and leaves
# provenance unweighted — but the deploy takes about half a minute here, and
# letting it land means the oracle run also demonstrates ci_green and deployed
# rather than leaving two checks reading zero for no reason.
sleep 45
echo "oracle: done"
exit 0
