#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/cost.py b/src/bespokelabs/curator/cost.py
index 3180d9d..8afb71a 100644
--- a/src/bespokelabs/curator/cost.py
+++ b/src/bespokelabs/curator/cost.py
@@ -1,7 +1,9 @@
+import dataclasses
 from collections import defaultdict
 
 import litellm
 
+from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP
 
 litellm.suppress_debug_info = True
@@ -10,8 +12,232 @@ RATE_LIMIT_HEADER = {
     "api.together.xyz": {"request-key": {"key": "x-ratelimit-limit", "type": "rps"}, "token-key": {"key": "x-ratelimit-limit-tokens", "type": "tps"}}
 }
 
+# Batch runs are billed at half the list price by the providers whose prices we read from litellm.
+_BATCH_DISCOUNT_FACTOR: float = 0.5
+
+# Prices are floats derived from divisions; round them so that equal prices compare equal.
+_PER_MILLION_NDIGITS: int = 9
+_PER_TOKEN_NDIGITS: int = 15
+
+# The wildcard completion window, used whenever no window was asked for.
+_DEFAULT_COMPLETION_WINDOW = "*"
+
+# Providers that are not looked up in an external price table.
+_LITELLM_PROVIDERS = (None, "default")
+
+
+class UnpricedModelError(LookupError):
+    """Raised when the price table cannot answer for (model, provider, completion_window)."""
+
+    REASONS: frozenset[str] = frozenset({"unknown_provider", "unknown_model", "unknown_window"})
+
+    def __init__(self, *, model: str, provider: str | None, completion_window: str, reason: str) -> None:
+        """Initialize the error.
+
+        Args:
+            model: The model name that was looked up.
+            provider: The provider key that was looked up, or None for the litellm table.
+            completion_window: The normalized completion window that was looked up.
+            reason: One of `UnpricedModelError.REASONS`.
+
+        Raises:
+            ValueError: If `reason` is not one of `UnpricedModelError.REASONS`.
+        """
+        if reason not in self.REASONS:
+            raise ValueError(f"Unknown reason {reason!r}, expected one of {sorted(self.REASONS)}.")
+        super().__init__(f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}")
+        self.model = model
+        self.provider = provider
+        self.completion_window = completion_window
+        self.reason = reason
+
+
+@dataclasses.dataclass(frozen=True)
+class ModelPrice:
+    """A resolved price for one model, provider and completion window.
+
+    The per-million prices already have the batch multiplier applied, so they are what should be
+    displayed and what `register_price_with_litellm` refuses to write back when `batch` is True.
+    """
+
+    model: str
+    provider: str | None
+    completion_window: str
+    input_cost_per_million: float
+    output_cost_per_million: float
+    source: str
+    batch: bool
+    output_price_inferred: bool
+    max_tokens: int | None
+
+    @property
+    def input_cost_per_token(self) -> float:
+        """The input price per token."""
+        return round(self.input_cost_per_million / 1e6, _PER_TOKEN_NDIGITS)
+
+    @property
+    def output_cost_per_token(self) -> float:
+        """The output price per token."""
+        return round(self.output_cost_per_million / 1e6, _PER_TOKEN_NDIGITS)
+
+
+def _normalize_completion_window(completion_window: str | None) -> str:
+    """Normalize a completion window; both None and "" mean the wildcard window."""
+    return completion_window or _DEFAULT_COMPLETION_WINDOW
+
+
+def _resolve_external_price(model: str, provider: str, completion_window: str) -> tuple[float, float, bool, int | None]:
+    """Read (input, output, output_price_inferred, max_tokens) from an external provider's table."""
+    providers = _DEFAULT_COST_MAP["external"]["providers"]
+    if provider not in providers:
+        raise UnpricedModelError(model=model, provider=provider, completion_window=completion_window, reason="unknown_provider")
+
+    provider_cost = providers[provider]["cost"]
+    if model not in provider_cost:
+        raise UnpricedModelError(model=model, provider=provider, completion_window=completion_window, reason="unknown_model")
+
+    entry = provider_cost[model]
+    input_costs = entry.get("input_cost_per_million") or {}
+    if completion_window not in input_costs:
+        raise UnpricedModelError(model=model, provider=provider, completion_window=completion_window, reason="unknown_window")
+
+    input_cost_per_million = input_costs[completion_window]
+    output_cost_per_million = (entry.get("output_cost_per_million") or {}).get(completion_window)
+    output_price_inferred = output_cost_per_million is None
+    if output_price_inferred:
+        output_cost_per_million = input_cost_per_million
+
+    return input_cost_per_million, output_cost_per_million, output_price_inferred, entry.get("max_tokens")
+
+
+def _resolve_litellm_price(model: str, completion_window: str) -> tuple[float, float, bool, int | None]:
+    """Read (input, output, output_price_inferred, max_tokens) from litellm's cost table."""
+    entry = litellm.model_cost.get(model)
+    if entry is None or entry.get("input_cost_per_token") is None:
+        raise UnpricedModelError(model=model, provider=None, completion_window=completion_window, reason="unknown_model")
+
+    input_cost_per_million = entry["input_cost_per_token"] * 1e6
+    output_cost_per_token = entry.get("output_cost_per_token")
+    output_price_inferred = output_cost_per_token is None
+    output_cost_per_million = input_cost_per_million if output_price_inferred else output_cost_per_token * 1e6
+
+    return input_cost_per_million, output_cost_per_million, output_price_inferred, entry.get("max_tokens")
+
+
+def resolve_model_price(
+    model: str,
+    *,
+    provider: str | None = None,
+    completion_window: str | None = None,
+    batch: bool = False,
+) -> ModelPrice:
+    """Resolve the price of a model.
+
+    A named external provider is authoritative: its table is the only one consulted, and a model
+    missing from it is an error rather than a reason to fall back to litellm. Conversely, no
+    provider (or the "default" provider) means litellm's table and nothing else.
+
+    Args:
+        model: The model name to price, as it is keyed in the chosen table.
+        provider: An external provider key, or None/"default" for litellm's table.
+        completion_window: The batch completion window; None and "" both mean "*".
+        batch: Whether this price is for a batch run. Only litellm-sourced prices are discounted;
+            the external tables already list each provider's batch tiers.
+
+    Returns:
+        ModelPrice: The resolved price, never with a None price.
+
+    Raises:
+        UnpricedModelError: If the tables cannot answer for this model, provider and window.
+    """
+    window = _normalize_completion_window(completion_window)
+
+    if provider in _LITELLM_PROVIDERS:
+        provider_key = None
+        source = "litellm"
+        input_cost_per_million, output_cost_per_million, output_price_inferred, max_tokens = _resolve_litellm_price(model, window)
+        multiplier = _BATCH_DISCOUNT_FACTOR if batch else 1.0
+    else:
+        provider_key = provider
+        source = "external"
+        input_cost_per_million, output_cost_per_million, output_price_inferred, max_tokens = _resolve_external_price(model, provider, window)
+        multiplier = 1.0
+
+    return ModelPrice(
+        model=model,
+        provider=provider_key,
+        completion_window=window,
+        input_cost_per_million=round(input_cost_per_million * multiplier, _PER_MILLION_NDIGITS),
+        output_cost_per_million=round(output_cost_per_million * multiplier, _PER_MILLION_NDIGITS),
+        source=source,
+        batch=batch,
+        output_price_inferred=output_price_inferred,
+        max_tokens=max_tokens,
+    )
+
+
+def register_price_with_litellm(price: ModelPrice) -> dict:
+    """Write `price` into litellm's global cost table.
+
+    Args:
+        price: An undiscounted (list) price to register.
+
+    Returns:
+        dict: The entry that was written into `litellm.model_cost`.
+
+    Raises:
+        ValueError: If `price` was resolved with `batch=True`; the global table only ever holds
+            list prices, so that the batch discount can never be applied twice.
+    """
+    if price.batch:
+        raise ValueError(f"Refusing to register batch-discounted prices for {price.model!r}; resolve with batch=False.")
+
+    entry = {
+        "max_tokens": price.max_tokens if price.max_tokens is not None else 8192,
+        "input_cost_per_token": price.input_cost_per_token,
+        "output_cost_per_token": price.output_cost_per_token,
+        "litellm_provider": price.provider if price.provider is not None else "openai",
+    }
+    litellm.register_model({price.model: entry})
+    return entry
+
+
+def format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]:
+    """Format the per-million prices for display.
+
+    An output price that was inferred from the input price is marked with a trailing "*".
+
+    Args:
+        price: The resolved price, or None when no price is known.
+        rich: Whether the strings are destined for a rich display.
+
+    Returns:
+        tuple[str, str]: The (input, output) cost strings.
+    """
+    if price is None:
+        unavailable = "[dim]N/A[/dim]" if rich else "N/A"
+        return unavailable, unavailable
+
+    input_cost_str = f"${price.input_cost_per_million:.3f}"
+    output_cost_str = f"${price.output_cost_per_million:.3f}"
+    if price.output_price_inferred:
+        output_cost_str += "*"
+    if rich:
+        input_cost_str = f"[red]{input_cost_str}[/red]"
+        output_cost_str = f"[red]{output_cost_str}[/red]"
+    return input_cost_str, output_cost_str
+
+
+def external_model_cost(model, completion_window="*", provider="default"):
+    """Get the per-token cost of the model from the external providers registered."""
+    price = resolve_model_price(model, provider=provider, completion_window=completion_window, batch=False)
+    return {"input_cost_per_token": price.input_cost_per_token, "output_cost_per_token": price.output_cost_per_token}
+
 
 class _LitellmCostProcessor:
+    # Whether the prices this processor reads are list prices that a batch run halves.
+    _BATCH_DISCOUNT_APPLIES: bool = True
+
     def __init__(self, config, batch=False) -> None:
         self.batch = batch
         self.config = config
@@ -37,48 +263,54 @@ class _LitellmCostProcessor:
                 }
             )
 
+    def batch_multiplier(self) -> float:
+        """The factor a computed cost is multiplied by; the only owner of the batch discount."""
+        if not self.batch:
+            return 1.0
+        if self.config.in_mtok_cost is not None:
+            # A user-supplied price is taken as given.
+            return 1.0
+        if not self._BATCH_DISCOUNT_APPLIES:
+            return 1.0
+        return _BATCH_DISCOUNT_FACTOR
+
+    def price_model(self, **kwargs) -> str:
+        """The model name this request is registered under and looked up by."""
+        completion_response = kwargs.get("completion_response")
+        if completion_response is not None:
+            model = completion_response.get("model") if hasattr(completion_response, "get") else getattr(completion_response, "model", None)
+            if model:
+                return model
+        return kwargs.get("model") or self.config.model
+
     def cost(self, *, completion_window="*", **kwargs):
+        """The cost of one completion, after the batch multiplier."""
+        kwargs["model"] = self.price_model(**kwargs)
         cost_to_complete = 0.0
-        if self.config.model in litellm.model_cost:
-            if "model" not in kwargs:
-                kwargs["model"] = self.config.model
+        if kwargs["model"] in litellm.model_cost:
             cost_to_complete = litellm.completion_cost(**kwargs)
-        if self.batch:
-            cost_to_complete *= 0.5
-        return cost_to_complete
-
-
-def _get_litellm_cost_map(model, completion_window="*", provider="default"):
-    cost = external_model_cost(model, completion_window=completion_window, provider=provider)
-    litellm_cost_map = {
-        model: {
-            "max_tokens": 8192,
-            "input_cost_per_token": cost["input_cost_per_token"],
-            "output_cost_per_token": cost["output_cost_per_token"],
-            "litellm_provider": "openai",
-        }
-    }
+        return cost_to_complete * self.batch_multiplier()
 
-    return litellm_cost_map
-
-
-def external_model_cost(model, completion_window="*", provider="default"):
-    """Get the cost of the model from the external providers registered."""
-    if provider not in _DEFAULT_COST_MAP["external"]["providers"]:
-        return {"input_cost_per_token": None, "output_cost_per_token": None}
-    provider_cost = _DEFAULT_COST_MAP["external"]["providers"][provider]["cost"]
-    if model not in provider_cost:
-        raise KeyError(f"Model {model} is not supported by {provider}.")
 
-    if completion_window not in provider_cost[model]["input_cost_per_million"]:
-        raise KeyError(f"Completion window {completion_window} is not supported for {model} by {provider}.")
-
-    cost = provider_cost[model]["input_cost_per_million"][completion_window]
-    return {"input_cost_per_token": cost / 1e6, "output_cost_per_token": cost / 1e6}
+def _register_external_price(processor_cls, model: str, completion_window: str) -> None:
+    """Register a model's external list price with litellm, memoised per (model, window)."""
+    key = processor_cls._wrap(model, completion_window)
+    if key in processor_cls._registered_models:
+        return
+    try:
+        register_price_with_litellm(resolve_model_price(model, provider=processor_cls._PROVIDER, completion_window=completion_window))
+    except UnpricedModelError as e:
+        logger.debug(f"Could not determine model costs: {e}")
+        return
+    processor_cls._registered_models.add(key)
 
 
 # source: https://www.kluster.ai/#pricing
 class _KlusterAICostProcessor(_LitellmCostProcessor):
+    # The per-window prices in the external table are already kluster.ai's batch tiers.
+    _BATCH_DISCOUNT_APPLIES: bool = False
+    _PROVIDER: str = "klusterai"
+
     _registered_models = set()
 
     def __init__(self, config, batch=False) -> None:
@@ -90,17 +322,18 @@ class _KlusterAICostProcessor(_LitellmCostProcessor):
         return model + "." + completion_window
 
     def cost(self, *, completion_window="*", **kwargs):
-        times = 2 if self.batch else 1
-        if _KlusterAICostProcessor._wrap(self.config.model, completion_window) in _KlusterAICostProcessor._registered_models:
-            return super().cost(completion_window=completion_window, **kwargs) * times
-
-        litellm.register_model(_get_litellm_cost_map(self.config.model, provider="klusterai", completion_window=completion_window))
-        _KlusterAICostProcessor._registered_models.add(_KlusterAICostProcessor._wrap(self.config.model, completion_window))
-        return super().cost(completion_window=completion_window, **kwargs) * times
+        """The cost of one completion, pricing the model from kluster.ai's table."""
+        window = _normalize_completion_window(completion_window)
+        _register_external_price(_KlusterAICostProcessor, self.price_model(**kwargs), window)
+        return super().cost(completion_window=window, **kwargs)
 
 
 # source: https://docs.inference.net/resources/pricing
 class _InferenceNetCostProcessor(_LitellmCostProcessor):
+    # The per-window prices in the external table are already inference.net's batch tiers.
+    _BATCH_DISCOUNT_APPLIES: bool = False
+    _PROVIDER: str = "inference.net"
+
     _registered_models = set()
 
     def __init__(self, config, batch=False) -> None:
@@ -112,17 +345,10 @@ class _InferenceNetCostProcessor(_LitellmCostProcessor):
         return model + "." + completion_window
 
     def cost(self, *, completion_window="*", **kwargs):
-        if "completion_response" in kwargs:
-            model = kwargs["completion_response"]["model"]
-        else:
-            model = kwargs.get("model", None)
-        times = 2 if self.batch else 1
-        if _InferenceNetCostProcessor._wrap(model, completion_window) in _InferenceNetCostProcessor._registered_models:
-            return super().cost(completion_window=completion_window, **kwargs) * times
-
-        litellm.register_model(_get_litellm_cost_map(model, provider="inference.net", completion_window=completion_window))
-        _InferenceNetCostProcessor._registered_models.add(_InferenceNetCostProcessor._wrap(model, completion_window))
-        return super().cost(completion_window=completion_window, **kwargs) * times
+        """The cost of one completion, pricing the model from inference.net's table."""
+        window = _normalize_completion_window(completion_window)
+        _register_external_price(_InferenceNetCostProcessor, self.price_model(**kwargs), window)
+        return super().cost(completion_window=window, **kwargs)
 
 
 class _AzureCostProcessor(_LitellmCostProcessor):
@@ -134,14 +360,14 @@ class _AzureCostProcessor(_LitellmCostProcessor):
     OpenAI entry) when available, falling back to the default OpenAI-style lookup otherwise.
     """
 
+    _BATCH_DISCOUNT_APPLIES: bool = True
+
     def cost(self, *, completion_window="*", **kwargs):
+        """The cost of one completion, preferring litellm's `azure/`-prefixed pricing."""
         azure_model = f"azure/{self.config.model}"
         if azure_model in litellm.model_cost:
             kwargs["model"] = azure_model
-            cost_to_complete = litellm.completion_cost(**kwargs)
-            if self.batch:
-                cost_to_complete *= 0.5
-            return cost_to_complete
+            return litellm.completion_cost(**kwargs) * self.batch_multiplier()
         return super().cost(completion_window=completion_window, **kwargs)
 
 
diff --git a/src/bespokelabs/curator/request_processor/batch/azure_batch_request_processor.py b/src/bespokelabs/curator/request_processor/batch/azure_batch_request_processor.py
index 0396ab5..28f9bc3 100644
--- a/src/bespokelabs/curator/request_processor/batch/azure_batch_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/batch/azure_batch_request_processor.py
@@ -1,5 +1,3 @@
-from litellm import model_cost
-
 from bespokelabs.curator.request_processor.batch.openai_batch_request_processor import OpenAIBatchRequestProcessor
 from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
 from bespokelabs.curator.types.generic_request import GenericRequest
@@ -44,10 +42,8 @@ class AzureBatchRequestProcessor(OpenAIBatchRequestProcessor):
 
     def set_model_cost(self):
         """Set tracker cost information, preferring litellm's `azure/`-prefixed pricing table."""
-        azure_model = f"azure/{self.prompt_formatter.model_name}"
-        if azure_model in model_cost:
-            self.tracker.input_cost_per_million = (model_cost[azure_model]["input_cost_per_token"] * 1_000_000) * 0.5
-            self.tracker.output_cost_per_million = (model_cost[azure_model]["output_cost_per_token"] * 1_000_000) * 0.5
-            self.tracker.start_tracker(self._tracker_console)
-        else:
-            super().set_model_cost()
+        if self.tracker.refresh_model_price(price_model=f"azure/{self.prompt_formatter.model_name}") is not None:
+            self.tracker.refresh_model_price()
+
+        # Start the tracker with the console from constructor
+        self.tracker.start_tracker(self._tracker_console)
diff --git a/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py b/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
index e3ccf10..2663cac 100644
--- a/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
@@ -6,7 +6,6 @@ from collections import Counter
 from typing import Optional
 
 import aiofiles
-from litellm import model_cost
 
 from bespokelabs.curator.cost import cost_processor_factory
 from bespokelabs.curator.log import logger
@@ -319,25 +318,8 @@ class BaseBatchRequestProcessor(BaseRequestProcessor):
 
     def set_model_cost(self):
         """Set cost information for the current model."""
-        # Set cost information if available
-        if self.prompt_formatter.model_name in model_cost:
-            # Batch requests are 50% cheaper
-            self.tracker.input_cost_per_million = (model_cost[self.prompt_formatter.model_name]["input_cost_per_token"] * 1_000_000) * 0.5
-            self.tracker.output_cost_per_million = (model_cost[self.prompt_formatter.model_name]["output_cost_per_token"] * 1_000_000) * 0.5
-        else:
-            from bespokelabs.curator.cost import external_model_cost
-
-            cost_info = external_model_cost(
-                self.prompt_formatter.model_name,
-                provider=self.compatible_provider,
-                completion_window=self.config.completion_window,
-            )
-            input_cost = cost_info["input_cost_per_token"]
-            output_cost = cost_info["output_cost_per_token"]
-            if input_cost is not None:
-                self.tracker.input_cost_per_million = input_cost * 1_000_000
-            if output_cost is not None:
-                self.tracker.output_cost_per_million = output_cost * 1_000_000
+        # The tracker owns the price lookup, so both entry points hold the same numbers.
+        self.tracker.refresh_model_price()
 
         # Start the tracker with the console from constructor
         self.tracker.start_tracker(self._tracker_console)
diff --git a/src/bespokelabs/curator/request_processor/batch/mistral_batch_request_processor.py b/src/bespokelabs/curator/request_processor/batch/mistral_batch_request_processor.py
index 77b2891..d77130b 100644
--- a/src/bespokelabs/curator/request_processor/batch/mistral_batch_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/batch/mistral_batch_request_processor.py
@@ -4,7 +4,6 @@ import uuid
 import httpx
 import instructor
 import litellm
-from litellm import model_cost
 from litellm.litellm_core_utils.core_helpers import map_finish_reason
 from mistralai import Mistral
 from mistralai.models import BatchJobOut, UploadFileOutTypedDict
@@ -76,12 +75,8 @@ class MistralBatchRequestProcessor(BaseBatchRequestProcessor):
 
     def set_model_cost(self):
         """Set input and output tracker cost information for the Mistral model."""
-        if f"mistral/{self.prompt_formatter.model_name}" in model_cost:
-            self.tracker.input_cost_per_million = (model_cost["mistral/" + self.prompt_formatter.model_name]["input_cost_per_token"] * 1_000_000) * 0.5
-            self.tracker.output_cost_per_million = (model_cost["mistral/" + self.prompt_formatter.model_name]["output_cost_per_token"] * 1_000_000) * 0.5
-
-        else:
-            super().set_model_cost()
+        if self.tracker.refresh_model_price(price_model=f"mistral/{self.prompt_formatter.model_name}") is not None:
+            self.tracker.refresh_model_price()
 
         # Start the tracker with the console from constructor
         self.tracker.start_tracker(self._tracker_console)
diff --git a/src/bespokelabs/curator/status_tracker/batch_status_tracker.py b/src/bespokelabs/curator/status_tracker/batch_status_tracker.py
index 3583667..5529ac4 100644
--- a/src/bespokelabs/curator/status_tracker/batch_status_tracker.py
+++ b/src/bespokelabs/curator/status_tracker/batch_status_tracker.py
@@ -5,7 +5,6 @@ import time
 from typing import Optional
 
 import tqdm
-from litellm import model_cost
 from pydantic import BaseModel, Field
 from rich import box
 from rich.console import Console, Group
@@ -17,6 +16,7 @@ from rich.table import Table
 from bespokelabs.curator import _CONSOLE
 from bespokelabs.curator.client import Client
 from bespokelabs.curator.constants import PUBLIC_CURATOR_VIEWER_HOME_URL
+from bespokelabs.curator.cost import ModelPrice, UnpricedModelError, format_cost_strings, resolve_model_price
 from bespokelabs.curator.log import USE_RICH_DISPLAY, logger
 from bespokelabs.curator.status_tracker.tqdm_constants.colors import COST, END, ERROR, HEADER, METRIC, MODEL, SUCCESS, WARNING
 from bespokelabs.curator.telemetry.client import TelemetryEvent, telemetry_client
@@ -81,6 +81,8 @@ class BatchStatusTracker(BaseModel):
     output_cost_per_million: Optional[float] = Field(default=None)
     input_cost_str: Optional[str] = Field(default=None)
     output_cost_str: Optional[str] = Field(default=None)
+    price_unavailable_reason: Optional[str] = Field(default=None)
+    output_price_inferred: bool = Field(default=False)
 
     # Track start time
     start_time: float = Field(default_factory=time.time)
@@ -105,44 +107,61 @@ class BatchStatusTracker(BaseModel):
     def model_post_init(self, __context__) -> None:
         """Post init processing after model initialization."""
         super().model_post_init(__context__)
+        self.refresh_model_price()
 
-        # Initialize cost strings with appropriate formatting based on display mode
+    def refresh_model_price(self, *, price_model: Optional[str] = None) -> Optional[str]:
+        """Re-resolve this tracker's per-million prices and cost strings.
+
+        Batches are always resolved with `batch=True`, so every entry point holds the same numbers.
+
+        Args:
+            price_model: The model name to price, defaulting to `self.model`.
+
+        Returns:
+            Optional[str]: None on success, or the `UnpricedModelError` reason on failure.
+        """
         try:
-            if self.model in model_cost:
-                self.input_cost_per_million = model_cost[self.model]["input_cost_per_token"] * 1_000_000
-                self.output_cost_per_million = model_cost[self.model]["output_cost_per_token"] * 1_000_000
-            elif self.compatible_provider:
-                from bespokelabs.curator.cost import external_model_cost
-
-                costs = external_model_cost(
-                    self.model,
-                    provider=self.compatible_provider,
-                    completion_window=self.completion_window,
-                )
-                self.input_cost_per_million = costs["input_cost_per_token"] * 1_000_000
-                self.output_cost_per_million = costs["output_cost_per_token"] * 1_000_000
-        except Exception as e:
+            price = resolve_model_price(
+                price_model or self.model,
+                provider=self.compatible_provider,
+                completion_window=self.completion_window,
+                batch=True,
+            )
+        except UnpricedModelError as e:
             logger.warning(f"Could not determine model costs: {e}")
             self.input_cost_per_million = None
             self.output_cost_per_million = None
+            self.output_price_inferred = False
+            self.price_unavailable_reason = e.reason
+            self._format_cost_str()
+            return e.reason
+
+        self.input_cost_per_million = price.input_cost_per_million
+        self.output_cost_per_million = price.output_cost_per_million
+        self.output_price_inferred = price.output_price_inferred
+        self.price_unavailable_reason = None
+        self._format_cost_str()
+        return None
+
+    def _current_price(self) -> Optional[ModelPrice]:
+        """The resolved price this tracker currently holds, or None if it has none."""
+        if self.input_cost_per_million is None or self.output_cost_per_million is None:
+            return None
+        return ModelPrice(
+            model=self.model,
+            provider=self.compatible_provider,
+            completion_window=self.completion_window or "*",
+            input_cost_per_million=self.input_cost_per_million,
+            output_cost_per_million=self.output_cost_per_million,
+            source="external" if self.compatible_provider else "litellm",
+            batch=True,
+            output_price_inferred=self.output_price_inferred,
+            max_tokens=None,
+        )
 
     def _format_cost_str(self):
         # Format the cost strings based on the values we got
-        if self.input_cost_per_million is not None:
-            if USE_RICH_DISPLAY:
-                self.input_cost_str = f"[red]${self.input_cost_per_million:.3f}[/red]"
-            else:
-                self.input_cost_str = f"${self.input_cost_per_million:.3f}"
-        else:
-            self.input_cost_str = "[dim]N/A[/dim]" if USE_RICH_DISPLAY else "N/A"
-
-        if self.output_cost_per_million is not None:
-            if USE_RICH_DISPLAY:
-                self.output_cost_str = f"[red]${self.output_cost_per_million:.3f}[/red]"
-            else:
-                self.output_cost_str = f"${self.output_cost_per_million:.3f}"
-        else:
-            self.output_cost_str = "[dim]N/A[/dim]" if USE_RICH_DISPLAY else "N/A"
+        self.input_cost_str, self.output_cost_str = format_cost_strings(self._current_price(), rich=USE_RICH_DISPLAY)
 
     def start_tracker(self, console: Optional[Console] = None):
         """Start the progress tracker."""
diff --git a/src/bespokelabs/curator/status_tracker/online_status_tracker.py b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
index 7603945..6055c5a 100644
--- a/src/bespokelabs/curator/status_tracker/online_status_tracker.py
+++ b/src/bespokelabs/curator/status_tracker/online_status_tracker.py
@@ -5,7 +5,7 @@ from enum import Enum
 from typing import Optional
 
 import tqdm
-from litellm import model_cost
+from litellm import model_cost  # noqa: F401  # kept: legacy patch target
 from rich import box
 from rich.console import Console, Group
 from rich.live import Live
@@ -16,7 +16,7 @@ from rich.table import Table
 from bespokelabs.curator import _CONSOLE
 from bespokelabs.curator.client import Client
 from bespokelabs.curator.constants import PUBLIC_CURATOR_VIEWER_HOME_URL
-from bespokelabs.curator.cost import external_model_cost
+from bespokelabs.curator.cost import UnpricedModelError, external_model_cost, format_cost_strings, resolve_model_price  # noqa: F401
 from bespokelabs.curator.log import USE_RICH_DISPLAY, logger
 from bespokelabs.curator.status_tracker.tqdm_constants.colors import COST, DIM, END, ERROR, HEADER, METRIC, MODEL, SUCCESS, WARNING
 from bespokelabs.curator.telemetry.client import TelemetryEvent, telemetry_client
@@ -77,6 +77,8 @@ class OnlineStatusTracker:
     input_cost_per_million: Optional[float] = None
     output_cost_per_million: Optional[float] = None
     compatible_provider: Optional[str] = None
+    price_unavailable_reason: Optional[str] = None
+    output_price_inferred: bool = False
 
     start_time: float = field(default_factory=time.time, init=False)
 
@@ -104,37 +106,41 @@ class OnlineStatusTracker:
                 self.max_tokens_per_minute = _TokenUsage()
 
         # Initialize cost strings
-        if self.model in model_cost:
-            model_pricing = model_cost[self.model]
-            if model_pricing.get("input_cost_per_token") is not None:
-                self.input_cost_per_million = model_pricing.get("input_cost_per_token", 0) * 1_000_000
-            else:
-                self.input_cost_per_million = None
-            if model_pricing.get("output_cost_per_token") is not None:
-                self.output_cost_per_million = model_pricing.get("output_cost_per_token", 0) * 1_000_000
-            else:
-                self.output_cost_per_million = None
-        else:
-            try:
-                external_pricing = external_model_cost(self.model, provider=self.compatible_provider)
-                self.input_cost_per_million = (
-                    external_pricing.get("input_cost_per_token", 0) * 1_000_000 if external_pricing.get("input_cost_per_token") is not None else None
-                )
-                self.output_cost_per_million = (
-                    external_pricing.get("output_cost_per_token", 0) * 1_000_000 if external_pricing.get("output_cost_per_token") is not None else None
-                )
-            except (KeyError, TypeError):
-                self.input_cost_per_million = None
-                self.output_cost_per_million = None
+        self.refresh_model_price()
 
-        # Handle None values for cost per million tokens
-        self.input_cost_str = f"[red]${self.input_cost_per_million:.3f}[/red]" if self.input_cost_per_million is not None else "[dim]N/A[/dim]"
-        if not USE_RICH_DISPLAY:
-            self.input_cost_str = f"${self.input_cost_per_million:.3f}" if self.input_cost_per_million is not None else "N/A"
+    def refresh_model_price(self, *, price_model: Optional[str] = None) -> Optional[str]:
+        """Re-resolve this tracker's per-million prices and cost strings.
 
-        self.output_cost_str = f"[red]${self.output_cost_per_million:.3f}[/red]" if self.output_cost_per_million is not None else "[dim]N/A[/dim]"
-        if not USE_RICH_DISPLAY:
-            self.output_cost_str = f"${self.output_cost_per_million:.3f}" if self.output_cost_per_million is not None else "N/A"
+        Online runs pay list price, so prices are always resolved with `batch=False`.
+
+        Args:
+            price_model: The model name to price, defaulting to `self.model`.
+
+        Returns:
+            Optional[str]: None on success, or the `UnpricedModelError` reason on failure.
+        """
+        try:
+            price = resolve_model_price(
+                price_model or self.model,
+                provider=self.compatible_provider,
+                completion_window="*",
+                batch=False,
+            )
+        except UnpricedModelError as e:
+            logger.debug(f"Could not determine model costs: {e}")
+            self.input_cost_per_million = None
+            self.output_cost_per_million = None
+            self.output_price_inferred = False
+            self.price_unavailable_reason = e.reason
+            self.input_cost_str, self.output_cost_str = format_cost_strings(None, rich=USE_RICH_DISPLAY)
+            return e.reason
+
+        self.input_cost_per_million = price.input_cost_per_million
+        self.output_cost_per_million = price.output_cost_per_million
+        self.output_price_inferred = price.output_price_inferred
+        self.price_unavailable_reason = None
+        self.input_cost_str, self.output_cost_str = format_cost_strings(price, rich=USE_RICH_DISPLAY)
+        return None
 
     def __str__(self):
         """String representation of the token limit strategy."""
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
