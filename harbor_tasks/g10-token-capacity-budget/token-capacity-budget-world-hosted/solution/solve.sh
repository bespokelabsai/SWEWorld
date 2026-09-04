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
index c5e4c90..6368b81 100644
--- a/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
@@ -12,6 +12,7 @@ from litellm.litellm_core_utils.core_helpers import map_finish_reason
 from bespokelabs.curator.cost import cost_processor_factory
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor
+from bespokelabs.curator.status_tracker.capacity_budget import read_rate_limit_headers
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse, _TokenUsage
@@ -127,28 +128,22 @@ class AnthropicOnlineRequestProcessor(BaseOnlineRequestProcessor):
             }
             return content
 
-    def get_header_based_rate_limits(self) -> tuple[int, _TokenUsage]:
+    def get_header_based_rate_limits(self) -> tuple[int | None, _TokenUsage | int | None]:
         """Get rate limits from Anthropic API headers.
 
         Returns:
-            tuple[int, _TokenUsage]: Contains 'max_requests_per_minute' and 'max_tokens_per_minute'
-                with separate input and output token limits
+            tuple[int | None, _TokenUsage | int | None]: Contains 'max_requests_per_minute' and
+                'max_tokens_per_minute', None for whatever the headers did not report
 
         Note:
             - Makes a dummy request to get actual rate limits from headers
+            - Limits the headers do not report are left to the status tracker to default
         """
         if not self.api_key:
             raise ValueError("Missing Anthropic API Key - Please set ANTHROPIC_API_KEY in your environment vars")
 
-        # Default to these values when header-based limits can't be determined
-        # Based on Anthropic's documented default rate limits
-        # These defaults are true for tier 4 Claude 3.7
-        # More information: https://docs.anthropic.com/en/api/rate-limits#rate-limits
-        headers = self.test_call()
-        rpm = headers.get("anthropic-ratelimit-requests-limit", 4000)
-        input_tpm = headers.get("anthropic-ratelimit-output-tokens-limit", 80000)
-        output_tpm = headers.get("anthropic-ratelimit-input-tokens-limit", 400000)
-        return int(rpm), _TokenUsage(input=int(input_tpm), output=int(output_tpm))
+        reading = read_rate_limit_headers(self.test_call())
+        return reading.max_requests_per_minute, reading.max_tokens_per_minute
 
     def estimate_output_tokens(self) -> int:
         """Estimate number of tokens in the response.
diff --git a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
index 085c2ec..4875759 100644
--- a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
@@ -23,6 +23,7 @@ from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP
 from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
+from bespokelabs.curator.status_tracker.capacity_budget import RateLimitReading
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
@@ -218,6 +219,26 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
             )
             return self.default_max_tokens_per_minute
 
+    def apply_rate_limit_reading(self, reading: RateLimitReading) -> None:
+        """Adopt the rate limits a provider reported in its response headers.
+
+        The reading also decides the token limit strategy, so the default token
+        limits are re-read for the strategy that is now in effect.
+
+        Args:
+            reading: The limits read from the provider's response headers
+        """
+        self.header_based_max_requests_per_minute = reading.max_requests_per_minute
+        self.header_based_max_tokens_per_minute = reading.max_tokens_per_minute
+        self.token_limit_strategy = reading.token_limit_strategy
+
+        defaults = _DEFAULT_COST_MAP["online"]["default"]["ratelimit"]["max_tokens_per_minute"]
+        default_tokens_per_minute = defaults[self.token_limit_strategy.value]
+        if self.token_limit_strategy == TokenLimitStrategy.combined:
+            self.default_max_tokens_per_minute = default_tokens_per_minute
+        else:
+            self.default_max_tokens_per_minute = _TokenUsage(**default_tokens_per_minute)
+
     @abstractmethod
     def estimate_total_tokens(self, messages: list) -> _TokenUsage:
         """Estimate total tokens for a request.
@@ -309,9 +330,6 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
             await asyncio.sleep(remaining_seconds_to_pause)
             status_tracker.last_update_time = time.time()
 
-    def free_capacity(self, tracker, tokens):
-        """Free blocked capacity."""
-
     def aiohttp_connector(self, tcp_limit: int) -> aiohttp.ClientSession:
         """Create an aiohttp connector with rate limiting."""
         connector = aiohttp.TCPConnector(limit=10 * tcp_limit)
@@ -375,20 +393,13 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
                         prompt_formatter=self.prompt_formatter,
                     )
 
-                    if status_tracker.max_tokens_per_minute is not None:
-                        token_estimate = self.estimate_total_tokens(request.generic_request.messages)
-                    else:
-                        token_estimate = _TokenUsage()  # Empty
-
-                    # Wait for capacity if needed
-                    while not status_tracker.has_capacity(token_estimate):
+                    # Wait for capacity if needed, reserving it as soon as it is available
+                    while (token_estimate := self._reserve_capacity(status_tracker, request.generic_request.messages)) is None:
                         await asyncio.sleep(0.1)
 
                     # Wait for rate limits cool down if needed
                     await self.cool_down_if_rate_limit_error(status_tracker)
 
-                    # Consume capacity before making request
-                    status_tracker.consume_capacity(token_estimate)
                     task = asyncio.create_task(
                         self.handle_single_request_with_retries(
                             request=request,
@@ -416,11 +427,6 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
 
                 if not queue_of_requests_to_retry.empty():
                     retry_request = await queue_of_requests_to_retry.get()
-                    if status_tracker.max_tokens_per_minute is not None:
-                        token_estimate = self.estimate_total_tokens(retry_request.generic_request.messages)
-                    else:
-                        token_estimate = _TokenUsage()  # Empty
-
                     attempt_number = self.config.max_retries - retry_request.attempts_left
                     logger.debug(
                         f"Retrying request {retry_request.task_id} "
@@ -428,16 +434,13 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
                         f"Previous errors: {retry_request.result}"
                     )
 
-                    # Wait for capacity if needed
-                    while not status_tracker.has_capacity(token_estimate):
+                    # Wait for capacity if needed, reserving it as soon as it is available
+                    while (token_estimate := self._reserve_capacity(status_tracker, retry_request.generic_request.messages)) is None:
                         await asyncio.sleep(0.1)
 
                     # Wait for rate limits cool down if needed
                     await self.cool_down_if_rate_limit_error(status_tracker)
 
-                    # Consume capacity before making request
-                    status_tracker.consume_capacity(token_estimate)
-
                     task = asyncio.create_task(
                         self.handle_single_request_with_retries(
                             request=retry_request,
@@ -467,10 +470,33 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
         if status_tracker.num_tasks_failed > 0:
             logger.warning(f"{status_tracker.num_tasks_failed} / {status_tracker.num_tasks_started} requests failed. Errors logged to {response_file}.")
 
+    def _reserve_capacity(self, status_tracker: OnlineStatusTracker, messages: list) -> _TokenUsage | None:
+        """Estimate a request's capacity and reserve it, all or nothing.
+
+        Args:
+            status_tracker: Tracker holding the capacity budget
+            messages: The messages of the request to be made
+
+        Returns:
+            The reserved token estimate, or None when there is not enough capacity yet
+
+        Raises:
+            CapacityExceedsLimitError: If the request can never fit inside the per-minute limit.
+        """
+        token_estimate = self.estimate_total_tokens(messages)
+        if not status_tracker.has_capacity(token_estimate):
+            return None
+        status_tracker.consume_capacity(token_estimate)
+        return token_estimate
+
     def _free_capacity(self, status_tracker: OnlineStatusTracker, used_capacity: "_TokenUsage", blocked_capacity: "_TokenUsage"):
         if status_tracker.max_tokens_per_minute is not None:
             status_tracker.free_capacity(used_capacity, blocked_capacity)
 
+    def _refund_capacity(self, status_tracker: OnlineStatusTracker, blocked_capacity: "_TokenUsage"):
+        """Give a failed attempt's whole reservation back, request slot included."""
+        status_tracker.refund_capacity(blocked_capacity)
+
     async def handle_single_request_with_retries(
         self,
         request: APIRequest,
@@ -561,6 +587,9 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
                 await self.append_generic_response(status_tracker, generic_response, response_file)
                 status_tracker.num_tasks_in_progress -= 1
                 status_tracker.num_tasks_failed += 1
+
+            # The attempt failed, refund the whole reservation it blocked.
+            self._refund_capacity(status_tracker, blocked_capacity)
             return
         else:
             self._add_output_token_moving_window(generic_response.token_usage.output)
diff --git a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
index 276755b..14c638f 100644
--- a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
@@ -11,6 +11,7 @@ from bespokelabs.curator.file_utilities import get_base64_size
 from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor
+from bespokelabs.curator.status_tracker.capacity_budget import read_rate_limit_headers
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
@@ -296,35 +297,24 @@ class LiteLLMOnlineRequestProcessor(BaseOnlineRequestProcessor):
         logger.info(f"Test call headers: {headers}")
         return headers
 
-    def get_header_based_rate_limits(self) -> tuple[int, _TokenUsage | int]:
+    def get_header_based_rate_limits(self) -> tuple[int | None, _TokenUsage | int | None]:
         """Retrieve rate limits from the LLM provider via LiteLLM.
 
         Returns:
-            tuple[int, _TokenUsage | int]: Contains 'max_requests_per_minute' and
-                                           'max_tokens_per_minute' info.
+            tuple[int | None, _TokenUsage | int | None]: Contains 'max_requests_per_minute' and
+                                                         'max_tokens_per_minute' info, None for
+                                                         whatever the headers did not report.
 
         Note:
             - Makes a test request to get rate limit information from response headers.
             - Some providers (e.g., Claude) require non-empty messages
+            - The headers also decide the token limit strategy.
         """
         logger.info(f"Getting rate limits for model: {self.config.model}")
 
-        headers = self.test_call()
-        provider = self.config.model.split("/")[0]
-        output_token_key = f"llm_provider-{provider}-ratelimit-output-tokens-remaining"
-        rpm = int(headers.get("x-ratelimit-limit-requests", 0))
-        if output_token_key in headers:
-            self.token_limit_strategy = TokenLimitStrategy.seperate
-            output_tpm = int(headers.get(output_token_key, 0))
-
-            input_token_key = f"llm_provider-{provider}-ratelimit-input-tokens-remaining"
-            input_tpm = int(headers.get(input_token_key, 0))
-            tpm = _TokenUsage(input=input_tpm, output=output_tpm)
-
-        else:
-            tpm = int(headers.get("x-ratelimit-limit-tokens", 0))
-
-        return rpm, tpm
+        reading = read_rate_limit_headers(self.test_call())
+        self.apply_rate_limit_reading(reading)
+        return reading.max_requests_per_minute, reading.max_tokens_per_minute
 
     def create_api_specific_request_online(self, generic_request: GenericRequest) -> dict:
         """Convert a generic request into a LiteLLM-compatible format.
diff --git a/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
index e46f417..57c49e3 100644
--- a/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py
@@ -17,6 +17,7 @@ from bespokelabs.curator.request_processor import openai_request_mixin
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor
 from bespokelabs.curator.request_processor.openai_request_mixin import OpenAIRequestMixin
+from bespokelabs.curator.status_tracker.capacity_budget import read_rate_limit_headers
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse, _TokenUsage
@@ -123,11 +124,12 @@ class OpenAIOnlineRequestProcessor(BaseOnlineRequestProcessor, OpenAIRequestMixi
         else:
             return super().aiohttp_connector(tcp_limit)
 
-    def get_header_based_rate_limits(self) -> tuple[int, int]:
+    def get_header_based_rate_limits(self) -> tuple[int | None, int | None]:
         """Get rate limits from OpenAI API headers.
 
         Returns:
-            tuple[int, int]: Contains 'max_requests_per_minute' and 'max_tokens_per_minute'
+            tuple[int | None, int | None]: Contains 'max_requests_per_minute' and 'max_tokens_per_minute',
+                None for whatever the headers did not report
 
         Note:
             - Makes a dummy request to get actual rate limits
@@ -155,10 +157,8 @@ class OpenAIOnlineRequestProcessor(BaseOnlineRequestProcessor, OpenAIRequestMixi
                     tpm = tpm * 60
                 return int(rpm), int(tpm)
 
-        rpm = int(response.headers.get("x-ratelimit-limit-requests", 0))
-        tpm = int(response.headers.get("x-ratelimit-limit-tokens", 0))
-
-        return rpm, tpm
+        reading = read_rate_limit_headers(response.headers)
+        return reading.max_requests_per_minute, reading.max_tokens_per_minute
 
     def estimate_output_tokens(self) -> int:
         """Estimate number of tokens in the response.
diff --git a/src/bespokelabs/curator/status_tracker/capacity_budget.py b/src/bespokelabs/curator/status_tracker/capacity_budget.py
new file mode 100644
index 0000000..4906c02
--- /dev/null
+++ b/src/bespokelabs/curator/status_tracker/capacity_budget.py
@@ -0,0 +1,167 @@
+"""Capacity budgeting for online request processors.
+
+This module owns the vocabulary shared by the online status tracker and the
+online request processors: the per-minute limit defaults, the token limit
+strategy, and the reading of provider rate limit headers.
+"""
+
+import math
+import re
+import typing as t
+from dataclasses import dataclass
+from enum import Enum
+
+from bespokelabs.curator.types.token_usage import _TokenUsage
+
+# Per-minute limits used when nobody told us what the real limits are.
+DEFAULT_MAX_REQUESTS_PER_MINUTE: int = 200
+DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED: int = 100_000
+DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE: int = 100_000
+DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE: int = 40_000
+
+# An underestimated request may push an axis negative, but never below
+# -CAPACITY_DEBT_FLOOR_FRACTION * limit.
+CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25
+
+# Where a per-minute limit came from.
+LIMIT_ORIGIN_CONFIGURED: str = "configured"
+LIMIT_ORIGIN_DEFAULTED: str = "defaulted"
+LIMIT_ORIGIN_UNLIMITED: str = "unlimited"
+
+# Header names carrying a *limit* (never a remaining counter), in priority order.
+REQUEST_LIMIT_HEADERS: tuple[str, ...] = (
+    "x-ratelimit-limit-requests",
+    "anthropic-ratelimit-requests-limit",
+)
+INPUT_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
+    "x-ratelimit-limit-input-tokens",
+    "anthropic-ratelimit-input-tokens-limit",
+)
+OUTPUT_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
+    "x-ratelimit-limit-output-tokens",
+    "anthropic-ratelimit-output-tokens-limit",
+)
+TOTAL_TOKEN_LIMIT_HEADERS: tuple[str, ...] = (
+    "x-ratelimit-limit-tokens",
+    "anthropic-ratelimit-tokens-limit",
+)
+
+_LIMIT_VALUE_RE = re.compile(r"^(\d+(?:\.\d+)?)([kKmM]?)$")
+_LIMIT_VALUE_MULTIPLIERS = {"": 1, "k": 1_000, "m": 1_000_000}
+
+
+class TokenLimitStrategy(str, Enum):
+    """Token limit Strategy enum."""
+
+    combined = "combined"
+    seperate = "seperate"
+    default = "combined"
+
+
+class CapacityExceedsLimitError(ValueError):
+    """A single request can never fit inside the configured per-minute budget.
+
+    Attributes:
+        axis: The capacity axis that cannot fit the request ("total", "input" or "output")
+        requested: The amount of capacity the request needs on that axis
+        limit: The per-minute limit of that axis
+    """
+
+    def __init__(self, axis: str, requested: int, limit: float) -> None:
+        """Initialize the CapacityExceedsLimitError."""
+        self.axis: str = axis
+        self.requested: int = requested
+        self.limit: float = limit
+        super().__init__(f"request needs {requested} {axis} capacity but the per-minute limit is {int(limit)}")
+
+
+@dataclass(frozen=True)
+class RateLimitReading:
+    """The rate limits a provider reported through its response headers.
+
+    Attributes:
+        max_requests_per_minute: Positive RPM, or None when no usable header was present
+        max_tokens_per_minute: int under `combined`, _TokenUsage under `seperate`, None when nothing usable
+        token_limit_strategy: `seperate` iff both an input and an output limit were read, else `combined`
+        source_headers: The header names actually consumed, request axis first
+    """
+
+    max_requests_per_minute: int | None
+    max_tokens_per_minute: int | _TokenUsage | None
+    token_limit_strategy: TokenLimitStrategy
+    source_headers: tuple[str, ...]
+
+
+def parse_limit_value(raw: object) -> int | None:
+    """Decode a single rate limit value reported by a provider.
+
+    Accepts positive integers and strings of digits with an optional `k`/`m`
+    suffix (e.g. "1.5k" -> 1500). Anything else - a malformed string, a float,
+    a bool, a zero or a negative number - is treated as "not reported".
+
+    Args:
+        raw: The raw header value
+
+    Returns:
+        The positive limit, or None when the value carries no usable limit
+    """
+    if isinstance(raw, bool):
+        return None
+    if isinstance(raw, int):
+        return raw if raw > 0 else None
+    if not isinstance(raw, str):
+        return None
+
+    match = _LIMIT_VALUE_RE.match(raw.strip())
+    if match is None:
+        return None
+    value = math.floor(float(match.group(1)) * _LIMIT_VALUE_MULTIPLIERS[match.group(2).lower()])
+    return value if value > 0 else None
+
+
+def _first_limit(headers: t.Mapping[str, object], names: tuple[str, ...]) -> tuple[int | None, str | None]:
+    """Return the first present-and-parseable limit among `names`, with its header name."""
+    for name in names:
+        if name not in headers:
+            continue
+        value = parse_limit_value(headers[name])
+        if value is not None:
+            return value, name
+    return None, None
+
+
+def read_rate_limit_headers(headers: t.Mapping[str, object]) -> RateLimitReading:
+    """Read the per-minute limits a provider advertises in its response headers.
+
+    Only `*-limit` headers are consulted; remaining counters and reset timers are
+    ignored. A complete input/output pair wins over the total token limit and
+    selects the `seperate` strategy; half a pair is discarded.
+
+    Args:
+        headers: The response headers, matched case-insensitively
+
+    Returns:
+        RateLimitReading: The limits read, with the header names they came from
+    """
+    normalized = {str(key).lower(): value for key, value in headers.items()}
+
+    rpm, rpm_header = _first_limit(normalized, REQUEST_LIMIT_HEADERS)
+    input_tpm, input_header = _first_limit(normalized, INPUT_TOKEN_LIMIT_HEADERS)
+    output_tpm, output_header = _first_limit(normalized, OUTPUT_TOKEN_LIMIT_HEADERS)
+
+    if input_tpm is not None and output_tpm is not None:
+        tpm: int | _TokenUsage | None = _TokenUsage(input=input_tpm, output=output_tpm)
+        strategy = TokenLimitStrategy.seperate
+        token_headers = (input_header, output_header)
+    else:
+        tpm, total_header = _first_limit(normalized, TOTAL_TOKEN_LIMIT_HEADERS)
+        strategy = TokenLimitStrategy.combined
+        token_headers = () if total_header is None else (total_header,)
+
+    source_headers = (() if rpm_header is None else (rpm_header,)) + token_headers
+    return RateLimitReading(
+        max_requests_per_minute=rpm,
+        max_tokens_per_minute=tpm,
+        token_limit_strategy=strategy,
+        source_headers=source_headers,
+    )
diff --git a/src/bespokelabs/curator/status_tracker/online_status_tracker.py b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
index 7603945..a3bdf38 100644
--- a/src/bespokelabs/curator/status_tracker/online_status_tracker.py
+++ b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
@@ -1,7 +1,7 @@
+import math
 import time
 import typing as t
 from dataclasses import asdict, dataclass, field
-from enum import Enum
 from typing import Optional
 
 import tqdm
@@ -18,6 +18,18 @@ from bespokelabs.curator.client import Client
 from bespokelabs.curator.constants import PUBLIC_CURATOR_VIEWER_HOME_URL
 from bespokelabs.curator.cost import external_model_cost
 from bespokelabs.curator.log import USE_RICH_DISPLAY, logger
+from bespokelabs.curator.status_tracker.capacity_budget import (  # noqa: F401  (re-exported for existing importers)
+    CAPACITY_DEBT_FLOOR_FRACTION,
+    DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE,
+    DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE,
+    DEFAULT_MAX_REQUESTS_PER_MINUTE,
+    DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED,
+    LIMIT_ORIGIN_CONFIGURED,
+    LIMIT_ORIGIN_DEFAULTED,
+    LIMIT_ORIGIN_UNLIMITED,
+    CapacityExceedsLimitError,
+    TokenLimitStrategy,
+)
 from bespokelabs.curator.status_tracker.tqdm_constants.colors import COST, DIM, END, ERROR, HEADER, METRIC, MODEL, SUCCESS, WARNING
 from bespokelabs.curator.telemetry.client import TelemetryEvent, telemetry_client
 from bespokelabs.curator.types.generic_response import _TokenUsage
@@ -34,14 +46,6 @@ _SUCCESS_WEIGHT_FACTOR = 5
 _STATUS_UPDATE_INTERVAL = 5
 
 
-class TokenLimitStrategy(str, Enum):
-    """Token limit Strategy enum."""
-
-    combined = "combined"
-    seperate = "seperate"
-    default = "combined"
-
-
 @dataclass
 class OnlineStatusTracker:
     """Tracks the status of all requests."""
@@ -55,13 +59,12 @@ class OnlineStatusTracker:
     num_other_errors: int = 0
     num_rate_limit_errors: int = 0
     num_parsed_responses: int = 0
-    available_request_capacity: float = 1.0
-    available_token_capacity: float | _TokenUsage = 0
+    available_request_capacity: float | None = 1.0
+    available_token_capacity: float | _TokenUsage | None = 0
     last_update_time: float = field(default_factory=time.time)
-    max_requests_per_minute: int = 0
-    max_tokens_per_minute: int | _TokenUsage = 0
+    max_requests_per_minute: int | None = 0
+    max_tokens_per_minute: int | _TokenUsage | None = 0
     max_concurrent_requests: int | None = None
-    max_tokens_per_minute: int = 0
     pbar: Optional[tqdm.tqdm] = field(default=None, repr=False, compare=False)
     response_cost: float = 0
     time_of_last_rate_limit_error: float = field(default=0.0)
@@ -93,15 +96,19 @@ class OnlineStatusTracker:
     estimated_cost_average: float = 0.0
     num_estimates: int = 0
 
+    # Capacity budgeting
+    capacity_clock: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)
+    token_limit_origin: str = field(default=LIMIT_ORIGIN_CONFIGURED, init=False)
+    request_limit_origin: str = field(default=LIMIT_ORIGIN_CONFIGURED, init=False)
+    num_capacity_settlements: int = 0
+    num_capacity_refunds: int = 0
+    num_capacity_debt_clamps: int = 0
+
     def __post_init__(self):
         """Post init."""
-        if self.token_limit_strategy == TokenLimitStrategy.combined:
-            self.available_token_capacity = t.cast(float, self.available_token_capacity)
-        else:
-            self.available_token_capacity = t.cast(_TokenUsage, self.available_token_capacity)
-            self.available_token_capacity = _TokenUsage()
-            if not self.max_tokens_per_minute:
-                self.max_tokens_per_minute = _TokenUsage()
+        self.last_update_time = self.capacity_clock()
+        self._normalize_request_limit()
+        self._normalize_token_limit()
 
         # Initialize cost strings
         if self.model in model_cost:
@@ -591,42 +598,113 @@ class OnlineStatusTracker:
         ]
         logger.info("\n".join(stats))
 
+    def _normalize_request_limit(self):
+        """Normalize the request limit and seed the request bucket full.
+
+        `None` means unlimited, `0` means nobody told us and gets the default.
+        """
+        if self.max_requests_per_minute is None:
+            self.request_limit_origin = LIMIT_ORIGIN_UNLIMITED
+            self.available_request_capacity = None
+            return
+
+        if not self.max_requests_per_minute:
+            self.max_requests_per_minute = DEFAULT_MAX_REQUESTS_PER_MINUTE
+            self.request_limit_origin = LIMIT_ORIGIN_DEFAULTED
+        else:
+            self.request_limit_origin = LIMIT_ORIGIN_CONFIGURED
+        self.available_request_capacity = float(self.max_requests_per_minute)
+
+    def _normalize_token_limit(self):
+        """Coerce the token limit to the shape of the strategy and seed the token bucket full.
+
+        `None` means unlimited, `0` (per axis under `seperate`) means nobody told
+        us and gets the default.
+        """
+        if self.token_limit_strategy == TokenLimitStrategy.combined:
+            if isinstance(self.max_tokens_per_minute, _TokenUsage):
+                self.max_tokens_per_minute = self.max_tokens_per_minute.total
+
+            if self.max_tokens_per_minute is None:
+                self.token_limit_origin = LIMIT_ORIGIN_UNLIMITED
+                self.available_token_capacity = None
+                return
+
+            if not self.max_tokens_per_minute:
+                self.max_tokens_per_minute = DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED
+                self.token_limit_origin = LIMIT_ORIGIN_DEFAULTED
+            else:
+                self.token_limit_origin = LIMIT_ORIGIN_CONFIGURED
+            self.available_token_capacity = float(self.max_tokens_per_minute)
+            return
+
+        if self.max_tokens_per_minute is None:
+            limit = _TokenUsage(input=None, output=None)
+        elif isinstance(self.max_tokens_per_minute, _TokenUsage):
+            limit = self.max_tokens_per_minute
+        else:
+            limit = _TokenUsage(input=self.max_tokens_per_minute, output=self.max_tokens_per_minute)
+
+        input_limit, input_defaulted = self._normalize_axis_limit(limit.input, DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE)
+        output_limit, output_defaulted = self._normalize_axis_limit(limit.output, DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE)
+
+        if input_defaulted or output_defaulted:
+            self.token_limit_origin = LIMIT_ORIGIN_DEFAULTED
+        elif input_limit is None and output_limit is None:
+            self.token_limit_origin = LIMIT_ORIGIN_UNLIMITED
+        else:
+            self.token_limit_origin = LIMIT_ORIGIN_CONFIGURED
+
+        self.max_tokens_per_minute = _TokenUsage(input=input_limit, output=output_limit)
+        self.available_token_capacity = _TokenUsage(input=input_limit, output=output_limit)
+
+    @staticmethod
+    def _normalize_axis_limit(limit: int | None, default: int) -> tuple[int | None, bool]:
+        """Return the limit of a single token axis and whether the default was substituted."""
+        if limit is None:
+            return None, False
+        if not limit:
+            return default, True
+        return limit, False
+
     def update_capacity(self):
         """Update available capacity based on time elapsed."""
-        current_time = time.time()
-        seconds_since_update = current_time - self.last_update_time
-        if self.max_requests_per_minute is not None:
+        current_time = self.capacity_clock()
+        seconds_since_update = max(0.0, current_time - self.last_update_time)
+        if self.available_request_capacity is not None:
             self.available_request_capacity = min(
                 self.available_request_capacity + self.max_requests_per_minute * seconds_since_update / 60.0,
-                self.max_requests_per_minute,
+                float(self.max_requests_per_minute),
             )
 
         if self.token_limit_strategy == TokenLimitStrategy.combined:
-            if self.max_tokens_per_minute is not None:
-                self.available_token_capacity = t.cast(int, self.available_token_capacity)
+            if self.available_token_capacity is not None:
+                self.available_token_capacity = t.cast(float, self.available_token_capacity)
                 self.max_tokens_per_minute = t.cast(int, self.max_tokens_per_minute)
                 self.available_token_capacity = min(
                     self.available_token_capacity + self.max_tokens_per_minute * seconds_since_update / 60.0,
-                    self.max_tokens_per_minute,
+                    float(self.max_tokens_per_minute),
                 )
         else:
-            self.available_token_capacity = t.cast(_TokenUsage, self.available_token_capacity)
-            self.max_tokens_per_minute = t.cast(_TokenUsage, self.max_tokens_per_minute)
-            if self.max_tokens_per_minute.input is not None:
-                self.available_token_capacity.input = min(
-                    self.available_token_capacity.input + self.max_tokens_per_minute.input * seconds_since_update / 60.0,
-                    self.max_tokens_per_minute.input,
-                )
-            if self.max_tokens_per_minute.output is not None:
-                self.available_token_capacity.output = min(
-                    self.available_token_capacity.output + self.max_tokens_per_minute.output * seconds_since_update / 60.0,
-                    self.max_tokens_per_minute.output,
-                )
+            available = t.cast(_TokenUsage, self.available_token_capacity)
+            limit = t.cast(_TokenUsage, self.max_tokens_per_minute)
+            input_capacity = available.input
+            output_capacity = available.output
+            if limit.input is not None:
+                input_capacity = min(input_capacity + math.floor(limit.input * seconds_since_update / 60.0), limit.input)
+            if limit.output is not None:
+                output_capacity = min(output_capacity + math.floor(limit.output * seconds_since_update / 60.0), limit.output)
+            self.available_token_capacity = _TokenUsage(input=input_capacity, output=output_capacity)
 
         self.last_update_time = current_time
 
     def has_capacity(self, token_estimate: _TokenUsage) -> bool:
-        """Check if there's enough capacity for a request."""
+        """Check if there's enough capacity for a request.
+
+        Raises:
+            CapacityExceedsLimitError: If the request can never fit inside the per-minute limit.
+        """
+        self._check_fits_limit(token_estimate)
         self.update_capacity()
         if self.token_limit_strategy == TokenLimitStrategy.combined:
             has_capacity = self._check_combined_capacity(token_estimate)
@@ -642,56 +720,123 @@ class OnlineStatusTracker:
         #     )
         return has_capacity
 
-    def _check_combined_capacity(self, token_estimate: _TokenUsage):
-        self.available_token_capacity = t.cast(int, self.available_token_capacity)
-        if self.max_requests_per_minute is None and self.max_tokens_per_minute is None:
-            return True
+    def _check_fits_limit(self, token_estimate: _TokenUsage):
+        """Raise if the estimate could never be satisfied, whatever the bucket holds."""
+        if self.token_limit_strategy == TokenLimitStrategy.combined:
+            axes = (("total", token_estimate.total, self.max_tokens_per_minute),)
+        else:
+            limit = t.cast(_TokenUsage, self.max_tokens_per_minute)
+            axes = (("input", token_estimate.input, limit.input), ("output", token_estimate.output, limit.output))
 
-        token_estimate = token_estimate.total
-        has_capacity = self.available_request_capacity >= 1 and self.available_token_capacity >= token_estimate
-        return has_capacity
+        for axis, requested, limit_value in axes:
+            if limit_value is None or requested is None:
+                continue
+            if requested > limit_value:
+                raise CapacityExceedsLimitError(axis, requested, limit_value)
 
-    def _check_seperate_capacity(self, token_estimate: _TokenUsage):
-        self.available_token_capacity = t.cast(_TokenUsage, self.available_token_capacity)
-        if self.max_tokens_per_minute.total is None and self.max_requests_per_minute is None:
+    def _check_combined_capacity(self, token_estimate: _TokenUsage):
+        if self.available_request_capacity is not None and self.available_request_capacity < 1:
+            return False
+        if self.available_token_capacity is None:
             return True
+        self.available_token_capacity = t.cast(float, self.available_token_capacity)
+        return self.available_token_capacity >= token_estimate.total
 
-        has_capacity = (
-            self.available_request_capacity >= 1
-            and self.available_token_capacity.input >= token_estimate.input
-            and self.available_token_capacity.output >= token_estimate.output
-        )
-        return has_capacity
+    def _check_seperate_capacity(self, token_estimate: _TokenUsage):
+        if self.available_request_capacity is not None and self.available_request_capacity < 1:
+            return False
+        available = t.cast(_TokenUsage, self.available_token_capacity)
+        if available.input is not None and available.input < token_estimate.input:
+            return False
+        if available.output is not None and available.output < token_estimate.output:
+            return False
+        return True
 
     def consume_capacity(self, token_estimate: _TokenUsage):
         """Consume capacity for a request."""
-        if self.max_requests_per_minute is not None:
+        if self.available_request_capacity is not None:
             self.available_request_capacity -= 1
-        if self.token_limit_strategy == TokenLimitStrategy.combined:
-            if self.max_tokens_per_minute is not None:
-                self.available_token_capacity = t.cast(float, self.available_token_capacity)
-                self.available_token_capacity -= token_estimate.total
-        else:
-            self.available_token_capacity = t.cast(_TokenUsage, self.available_token_capacity)
-
-            if self.max_tokens_per_minute is not None:
-                self.available_token_capacity.input -= token_estimate.input
-                self.available_token_capacity.output -= token_estimate.output
+        self._move_token_capacity(-token_estimate.total, -token_estimate.input, -token_estimate.output)
+        self._clamp_token_debt()
 
     def free_capacity(self, used: _TokenUsage, blocked: _TokenUsage):
-        """Free extra consumed capacity.
+        """Settle a finished request: give back what was blocked but not used.
 
         Note: This can be a negative number
         incase of under estimation of consumed capacity.
+        The request slot is not returned, the request really was made.
         """
-        if self.token_limit_strategy == TokenLimitStrategy.seperate:
-            input_free = blocked.input - used.input
-            output_free = blocked.output - used.output
-            self.available_token_capacity.input += input_free
-            self.available_token_capacity.output += output_free
-        else:
-            free = blocked.total - used.total
-            self.available_token_capacity += free
+        self._move_token_capacity(
+            blocked.total - used.total,
+            blocked.input - used.input,
+            blocked.output - used.output,
+            cap_at_limit=True,
+        )
+        self.num_capacity_settlements += 1
+        self._clamp_token_debt()
+
+    def refund_capacity(self, blocked: _TokenUsage):
+        """Refund a failed attempt in full, request slot included."""
+        if self.available_request_capacity is not None:
+            self.available_request_capacity = min(self.available_request_capacity + 1.0, float(self.max_requests_per_minute))
+        self._move_token_capacity(blocked.total, blocked.input, blocked.output, cap_at_limit=True)
+        self.num_capacity_refunds += 1
+        self._clamp_token_debt()
+
+    def _move_token_capacity(self, combined_delta: int, input_delta: int, output_delta: int, cap_at_limit: bool = False):
+        """Add the given deltas to the token buckets, leaving unlimited axes untouched."""
+        if self.token_limit_strategy == TokenLimitStrategy.combined:
+            if self.available_token_capacity is None:
+                return
+            available = t.cast(float, self.available_token_capacity) + (combined_delta or 0)
+            if cap_at_limit:
+                available = min(available, float(t.cast(int, self.max_tokens_per_minute)))
+            self.available_token_capacity = available
+            return
+
+        available = t.cast(_TokenUsage, self.available_token_capacity)
+        limit = t.cast(_TokenUsage, self.max_tokens_per_minute)
+        input_capacity = available.input
+        output_capacity = available.output
+        if input_capacity is not None:
+            input_capacity += input_delta or 0
+            if cap_at_limit:
+                input_capacity = min(input_capacity, limit.input)
+        if output_capacity is not None:
+            output_capacity += output_delta or 0
+            if cap_at_limit:
+                output_capacity = min(output_capacity, limit.output)
+        self.available_token_capacity = _TokenUsage(input=input_capacity, output=output_capacity)
+
+    def _clamp_token_debt(self):
+        """Clamp any token axis that fell below its debt floor, counting one clamp per call."""
+        if self.token_limit_strategy == TokenLimitStrategy.combined:
+            if self.available_token_capacity is None:
+                return
+            floor = -t.cast(int, self.max_tokens_per_minute) * CAPACITY_DEBT_FLOOR_FRACTION
+            if self.available_token_capacity < floor:
+                self.available_token_capacity = floor
+                self.num_capacity_debt_clamps += 1
+            return
+
+        available = t.cast(_TokenUsage, self.available_token_capacity)
+        limit = t.cast(_TokenUsage, self.max_tokens_per_minute)
+        input_capacity = available.input
+        output_capacity = available.output
+        clamped = False
+        if input_capacity is not None:
+            floor = math.ceil(-limit.input * CAPACITY_DEBT_FLOOR_FRACTION)
+            if input_capacity < floor:
+                input_capacity = floor
+                clamped = True
+        if output_capacity is not None:
+            floor = math.ceil(-limit.output * CAPACITY_DEBT_FLOOR_FRACTION)
+            if output_capacity < floor:
+                output_capacity = floor
+                clamped = True
+        if clamped:
+            self.available_token_capacity = _TokenUsage(input=input_capacity, output=output_capacity)
+            self.num_capacity_debt_clamps += 1
 
     def __del__(self):
         """Ensure live display is stopped on deletion."""
CURATOR_ORACLE_PATCH_EOF

git apply --whitespace=nowarn /tmp/oracle.patch || { echo "oracle: patch did not apply"; exit 1; }
rm -f /tmp/oracle.patch

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "Online token-capacity budget: reservation, refund and reported limits" || { echo "oracle: nothing to commit"; exit 1; }

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world — but the first is one round trip and
# the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/token-capacity-budget"
  git push --quiet --force origin "HEAD:$BRANCH" || { echo "oracle: push failed"; exit 1; }
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \
        -H 'Content-Type: application/json' "$API/pulls" \
        -d "{\"head\":\"$BRANCH\",\"base\":\"main\",\"title\":\"oracle: token-capacity-budget\"}" \
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
