#!/bin/bash
# Reference solution, run by `harbor run -a oracle` and by Horizon's validation
# gate.
#
# This USED to be a no-op that printed a line and exited 0. That was defensible
# locally -- Harbor never gates on the oracle, and the `-spec` control is what
# proves the suite is satisfiable -- but Horizon refuses to schedule any
# evaluation against a task whose oracle does not score ~1.0:
#
#     409 Conflict: One or more tasks are blocked by the evaluation validation gate.
#
# So the world arm needs a real one, and a real one here means more than
# applying a patch. `run_suites.py` clones and grades **the pushed `main`**, not
# the working tree -- an oracle that edits files and stops scores exactly zero,
# with all eleven tests reporting "batch_payload_planner does not import".
# Pushing IS the solution on this arm.
#
# The patch is embedded rather than read from a file beside this script: on the
# apex arms the sibling file was unreadable from the solution's own directory,
# and a heredoc has no permissions of its own. It is generated, not hand-written,
# so it cannot drift from the suite.
set -uo pipefail

REPO_URL="http://worldadmin:worldadmin@git.world.local/worldadmin/curator.git"
WORK="$(mktemp -d)"

# The healthcheck should already have waited for gitea, but the oracle also runs
# in contexts that do not go through it. Cheap when it is already up.
wait-for-service --quiet gitea 2>/dev/null || true

git clone --quiet "$REPO_URL" "$WORK/curator" || { echo "oracle: clone failed"; exit 1; }
cd "$WORK/curator" || exit 1

cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/request_processor/base_request_processor.py b/src/bespokelabs/curator/request_processor/base_request_processor.py
index c3828af..c8cd537 100644
--- a/src/bespokelabs/curator/request_processor/base_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/base_request_processor.py
@@ -22,6 +22,7 @@ from bespokelabs.curator.file_utilities import count_lines
 from bespokelabs.curator.hf_card_template import HUGGINGFACE_CARD_TEMPLATE
 from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
 from bespokelabs.curator.log import logger
+from bespokelabs.curator.request_processor.batch_payload_planner import PLAN_FILE_NAME, plan_document
 from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig, RequestProcessorConfig
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
 from bespokelabs.curator.types.generic_response import GenericResponse
@@ -260,38 +261,32 @@ class BaseRequestProcessor(ABC):
         if isinstance(self.config, BatchRequestProcessorConfig):
             batch_size = self.config.batch_size
 
-            def _get_optimal_batch_size(start_idx: int) -> int:
-                batch_size = self.max_requests_per_batch
-                end_idx = min(start_idx + batch_size, len(dataset))
-                current_dataset = dataset.select(range(start_idx, end_idx))
-                batch_size_bytes = 0
-                for idx, dataset_row in enumerate(current_dataset):
-                    dataset_row_idx = idx + start_idx
-                    request = self.prompt_formatter.create_generic_request(dataset_row, dataset_row_idx, False)
-                    request_size = len(json.dumps(request.model_dump(), default=str).encode())
-                    if batch_size_bytes + request_size >= self.max_bytes_per_batch:
-                        batch_size = idx
-                        break
-                    else:
-                        batch_size_bytes += request_size
-
-                return batch_size
-
             if batch_size == "auto":
+                plan = self.plan_request_batches(dataset)
+
+                # A previous "auto" run may have left a longer numbering behind, which a later
+                # glob would pick up, so the stale request files are cleared once the plan is in hand.
+                for stale_file in glob.glob(os.path.join(self.working_dir, "requests_*.jsonl")) + glob.glob(os.path.join(self.working_dir, "metadata_*.json")):
+                    os.remove(stale_file)
+
+                plan_file = os.path.join(self.working_dir, PLAN_FILE_NAME)
+                with open(plan_file, "w") as f:
+                    f.write(json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n")
+
+                request_files = [os.path.join(self.working_dir, f"requests_{planned.index}.jsonl") for planned in plan]
+                metadata_files = [os.path.join(self.working_dir, f"metadata_{planned.index}.json") for planned in plan]
 
                 async def create_all_request_files():
-                    tasks = []
-                    start_idx = 0
-                    idx = 0
-                    while True:
-                        batch_size = _get_optimal_batch_size(start_idx)
-                        request_file = os.path.join(self.working_dir, f"requests_{idx}.jsonl")
-                        metadata_file = os.path.join(self.working_dir, f"metadata_{idx}.json")
-                        tasks.append(self.acreate_request_file(dataset, request_file, metadata_file, start_idx=start_idx, batch_size=batch_size))
-                        start_idx += batch_size
-                        idx += 1
-                        if start_idx >= len(dataset):
-                            break
+                    tasks = [
+                        self.acreate_request_file(
+                            dataset,
+                            request_files[planned.index],
+                            metadata_files[planned.index],
+                            start_idx=planned.start_idx,
+                            batch_size=planned.num_requests,
+                        )
+                        for planned in plan
+                    ]
                     await asyncio.gather(*tasks)
 
             else:
diff --git a/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py b/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
index e3ccf10..de7dd8b 100644
--- a/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py
@@ -3,7 +3,7 @@ import json
 import os
 from abc import abstractmethod
 from collections import Counter
-from typing import Optional
+from typing import TYPE_CHECKING, Optional
 
 import aiofiles
 from litellm import model_cost
@@ -11,6 +11,14 @@ from litellm import model_cost
 from bespokelabs.curator.cost import cost_processor_factory
 from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor.base_request_processor import BaseRequestProcessor
+from bespokelabs.curator.request_processor.batch_payload_planner import (
+    BatchLimits,
+    BatchPayloadTooLargeError,
+    PlannedBatch,
+    payload_bytes,
+    payload_size_bytes,
+    plan_batches,
+)
 from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
 from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker
@@ -19,6 +27,9 @@ from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
 from bespokelabs.curator.types.token_usage import _TokenUsage
 
+if TYPE_CHECKING:
+    from datasets import Dataset
+
 _STREAM_CHUNK_SIZE = 1000
 
 
@@ -353,7 +364,62 @@ class BaseBatchRequestProcessor(BaseRequestProcessor):
             with open(self.batch_objects_file, "w") as f:
                 f.write(self.tracker.model_dump_json())
 
-    def create_batch_file(self, api_specific_requests: list[dict]) -> str:
+    @property
+    def batch_limits(self) -> BatchLimits:
+        """Limits any plan for this processor is built against."""
+        return BatchLimits(max_requests_per_batch=self.max_requests_per_batch, max_bytes_per_batch=self.max_bytes_per_batch)
+
+    def measure_request_payload(self, generic_request: GenericRequest) -> int:
+        """Measure the payload one request contributes to a batch file.
+
+        Args:
+            generic_request: Standardized request object.
+
+        Returns:
+            int: Byte size of the API-specific request that will be submitted.
+        """
+        return payload_size_bytes(self.create_api_specific_request_batch(generic_request))
+
+    def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]:
+        """Plan how a dataset is split into batches that the API will accept.
+
+        Measures every row once, in dataset order, against the payload that
+        `create_batch_file` will build, then packs the rows greedily.
+
+        Args:
+            dataset: Dataset to plan batches for.
+
+        Returns:
+            list[PlannedBatch]: Contiguous, ordered and exhaustive batches.
+
+        Raises:
+            SingleRequestTooLargeError: If one request exceeds the byte limit on its own.
+            BatchPlanTooFragmentedError: If the plan needs more batches than allowed.
+
+        Side Effects:
+            - Logs a single summary line describing the plan
+        """
+        generation_params_per_row = "generation_params" in dataset.column_names
+        sizes = [
+            self.measure_request_payload(self.prompt_formatter.create_generic_request(row, idx, generation_params_per_row)) for idx, row in enumerate(dataset)
+        ]
+
+        limits = self.batch_limits
+        plan = plan_batches(sizes, limits)
+        if not plan:
+            logger.warning("Batch plan is empty: dataset has 0 rows; no batches will be submitted.")
+            return plan
+
+        num_requests = sum(planned.num_requests for planned in plan)
+        num_bytes = sum(planned.num_bytes for planned in plan)
+        largest = max(plan, key=lambda planned: planned.num_bytes)
+        logger.info(
+            f"Planned {len(plan)} batch(es) for {num_requests} request(s): {num_bytes:,} bytes total, "
+            f"largest batch {largest.num_bytes:,} bytes in {largest.num_requests} request(s)."
+        )
+        return plan
+
+    def create_batch_file(self, api_specific_requests: list[dict]) -> bytes:
         """Create a batch file from API-specific requests.
 
         Validates request count and file size against API limits before creating
@@ -363,10 +429,11 @@ class BaseBatchRequestProcessor(BaseRequestProcessor):
             api_specific_requests: List of API-specific request dictionaries.
 
         Returns:
-            str: Encoded file content ready for API upload.
+            bytes: Encoded file content ready for API upload.
 
         Raises:
-            ValueError: If batch exceeds request count or size limits.
+            ValueError: If batch exceeds request count limits.
+            BatchPayloadTooLargeError: If batch exceeds the byte limit.
 
         Side Effects:
             - Logs debug information about batch file size
@@ -381,14 +448,10 @@ class BaseBatchRequestProcessor(BaseRequestProcessor):
 
         # Join requests with newlines and encode to bytes for upload
         file_content = "\n".join(json.dumps(r) for r in api_specific_requests).encode()
-        file_content_size = len(file_content)
+        file_content_size = payload_bytes([payload_size_bytes(r) for r in api_specific_requests])
         logger.debug(f"Batch file content size: {file_content_size / (1024 * 1024):.2f} MB ({file_content_size:,} bytes)")
         if file_content_size > self.max_bytes_per_batch:
-            raise ValueError(
-                f"Batch file content size {file_content_size:,} bytes "
-                f"is greater than the maximum of {self.max_bytes_per_batch:,} bytes per batch that {self.__class__.__name__} supports. "
-                f"Please reduce your batch size or request content size (via prompt_func and response_format)."
-            )
+            raise BatchPayloadTooLargeError(num_requests=n_requests, size_bytes=file_content_size, limit_bytes=self.max_bytes_per_batch)
         return file_content
 
     async def submit_batch_from_request_file(
diff --git a/src/bespokelabs/curator/request_processor/batch_payload_planner.py b/src/bespokelabs/curator/request_processor/batch_payload_planner.py
new file mode 100644
index 0000000..bd5153b
--- /dev/null
+++ b/src/bespokelabs/curator/request_processor/batch_payload_planner.py
@@ -0,0 +1,237 @@
+"""Pure planning helpers for splitting a dataset into provider batches.
+
+The planner measures the payload that is actually submitted to the provider -- the
+API-specific request dictionaries joined with newlines by
+:meth:`BaseBatchRequestProcessor.create_batch_file` -- so that a plan can never
+produce a batch that the submission path refuses.
+"""
+
+import dataclasses
+import hashlib
+import json
+from dataclasses import dataclass
+from typing import Sequence
+
+PLAN_FILE_NAME = "batch_plan.json"
+PLAN_FORMAT_VERSION = 1
+
+_MAX_BATCHES_PER_PLAN = 512
+
+
+@dataclass(frozen=True)
+class BatchLimits:
+    """Limits a single plan is built against.
+
+    Attributes:
+        max_requests_per_batch: Maximum number of requests in one provider batch.
+        max_bytes_per_batch: Maximum byte size of one batch file.
+        max_batches_per_plan: Maximum number of batches a single plan may contain.
+    """
+
+    max_requests_per_batch: int
+    max_bytes_per_batch: int
+    max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN
+
+
+@dataclass(frozen=True)
+class PlannedBatch:
+    """One contiguous span of the dataset that becomes one provider batch.
+
+    Attributes:
+        index: 0-based position of this batch in the plan.
+        start_idx: Inclusive dataset index of the first request.
+        end_idx: Exclusive dataset index one past the last request.
+        num_requests: Number of requests in the batch, always at least 1.
+        num_bytes: Exact byte length of the batch file that will be submitted.
+    """
+
+    index: int
+    start_idx: int
+    end_idx: int
+    num_requests: int
+    num_bytes: int
+
+
+class BatchPayloadTooLargeError(ValueError):
+    """Raised when a batch payload exceeds the provider byte limit."""
+
+    def __init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None:
+        """Initialize the error.
+
+        Args:
+            num_requests: Number of requests in the offending payload.
+            size_bytes: Byte size of the offending payload.
+            limit_bytes: Maximum byte size allowed per batch.
+        """
+        self.num_requests = num_requests
+        self.size_bytes = size_bytes
+        self.limit_bytes = limit_bytes
+        super().__init__(self._message())
+
+    def _message(self) -> str:
+        return (
+            f"Batch payload of {self.num_requests:,} request(s) is {self.size_bytes:,} bytes, "
+            f"which is greater than the maximum of {self.limit_bytes:,} bytes per batch. "
+            f"Please reduce your batch size or request content size (via prompt_func and response_format)."
+        )
+
+
+class SingleRequestTooLargeError(BatchPayloadTooLargeError):
+    """Raised when a single request exceeds the provider byte limit on its own."""
+
+    def __init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None:
+        """Initialize the error.
+
+        Args:
+            row_idx: Dataset index of the offending request.
+            size_bytes: Byte size of the offending request.
+            limit_bytes: Maximum byte size allowed per batch.
+        """
+        self.row_idx = row_idx
+        super().__init__(num_requests=1, size_bytes=size_bytes, limit_bytes=limit_bytes)
+
+    def _message(self) -> str:
+        return (
+            f"Request at row {self.row_idx} is {self.size_bytes:,} bytes on its own, "
+            f"which is greater than the maximum of {self.limit_bytes:,} bytes per batch. "
+            f"No batch can contain it. Please reduce the request content size (via prompt_func and response_format)."
+        )
+
+
+class BatchPlanTooFragmentedError(ValueError):
+    """Raised when a plan would need more batches than are allowed."""
+
+    def __init__(self, *, num_batches: int, limit: int) -> None:
+        """Initialize the error.
+
+        Args:
+            num_batches: Number of batches the plan would have needed.
+            limit: Maximum number of batches allowed per plan.
+        """
+        super().__init__(
+            f"Batch plan would contain {num_batches:,} batches, "
+            f"which is more than the maximum of {limit:,} batches per plan. "
+            f"Please check your batch limits, every batch becomes a provider batch job that is polled."
+        )
+        self.num_batches = num_batches
+        self.limit = limit
+
+
+def payload_size_bytes(api_specific_request: dict) -> int:
+    """Measure one API-specific request the way ``create_batch_file`` serializes it.
+
+    Args:
+        api_specific_request: API-specific request dictionary.
+
+    Returns:
+        int: Byte length of the serialized request.
+
+    Raises:
+        TypeError: If the request contains a value that is not JSON serializable.
+    """
+    return len(json.dumps(api_specific_request).encode())
+
+
+def payload_bytes(sizes: Sequence[int]) -> int:
+    """Compute the byte size of the batch file built from requests of these sizes.
+
+    The requests are joined with newlines, so the file carries ``n - 1`` separators
+    and no trailing newline.
+
+    Args:
+        sizes: Byte sizes of the individual requests.
+
+    Returns:
+        int: Byte size of the batch file, 0 for an empty sequence.
+    """
+    if not sizes:
+        return 0
+    return sum(sizes) + len(sizes) - 1
+
+
+def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]:
+    """Split request sizes into contiguous batches that fit within the limits.
+
+    Walks the sizes once in index order, adding each request to the current batch
+    while it still fits and starting a new batch otherwise. Both limits are
+    inclusive, matching the checks in ``create_batch_file``.
+
+    Args:
+        sizes: Byte sizes of the requests, in dataset order.
+        limits: Limits the plan is built against.
+
+    Returns:
+        list[PlannedBatch]: Contiguous, ordered and exhaustive batches.
+
+    Raises:
+        SingleRequestTooLargeError: If one request exceeds the byte limit on its own.
+        BatchPlanTooFragmentedError: If the plan needs more batches than allowed.
+    """
+    for row_idx, size in enumerate(sizes):
+        if size > limits.max_bytes_per_batch:
+            raise SingleRequestTooLargeError(row_idx=row_idx, size_bytes=size, limit_bytes=limits.max_bytes_per_batch)
+
+    plan: list[PlannedBatch] = []
+    start_idx = 0
+    current_sizes: list[int] = []
+
+    def _close(end_idx: int) -> None:
+        plan.append(
+            PlannedBatch(
+                index=len(plan),
+                start_idx=start_idx,
+                end_idx=end_idx,
+                num_requests=len(current_sizes),
+                num_bytes=payload_bytes(current_sizes),
+            )
+        )
+
+    for idx, size in enumerate(sizes):
+        fits = len(current_sizes) + 1 <= limits.max_requests_per_batch and payload_bytes(current_sizes + [size]) <= limits.max_bytes_per_batch
+        if current_sizes and not fits:
+            _close(idx)
+            start_idx = idx
+            current_sizes = []
+        current_sizes.append(size)
+
+    if current_sizes:
+        _close(len(sizes))
+
+    if len(plan) > limits.max_batches_per_plan:
+        raise BatchPlanTooFragmentedError(num_batches=len(plan), limit=limits.max_batches_per_plan)
+
+    return plan
+
+
+def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str:
+    """Fingerprint a plan by where its cuts fall and how big each batch is.
+
+    Args:
+        plan: Planned batches to fingerprint.
+
+    Returns:
+        str: First 12 characters of the sha256 hexdigest of the canonical string.
+    """
+    canonical = ";".join(f"{planned.start_idx}-{planned.end_idx}:{planned.num_bytes}" for planned in plan)
+    return hashlib.sha256(canonical.encode()).hexdigest()[:12]
+
+
+def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict:
+    """Build the sidecar document recording a plan.
+
+    Args:
+        plan: Planned batches.
+        limits: Limits the plan was built against.
+
+    Returns:
+        dict: Serializable description of the plan.
+    """
+    return {
+        "plan_format_version": PLAN_FORMAT_VERSION,
+        "plan_id": plan_fingerprint(plan),
+        "limits": dataclasses.asdict(limits),
+        "num_batches": len(plan),
+        "num_requests": sum(planned.num_requests for planned in plan),
+        "num_bytes": sum(planned.num_bytes for planned in plan),
+        "batches": [dataclasses.asdict(planned) for planned in plan],
+    }
CURATOR_ORACLE_PATCH_EOF

git apply --whitespace=nowarn /tmp/oracle.patch || { echo "oracle: patch did not apply"; exit 1; }
rm -f /tmp/oracle.patch

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "feat: batch payload planner for batch_size=\"auto\"" \
  || { echo "oracle: nothing to commit"; exit 1; }

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world -- but the first is one round trip
# and the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/batch-payload-planner"
  git push --quiet --force origin "HEAD:$BRANCH" || { echo "oracle: push failed"; exit 1; }
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \
        -H 'Content-Type: application/json' "$API/pulls" \
        -d "{\"head\":\"$BRANCH\",\"base\":\"main\",\"title\":\"oracle: batch payload planner\"}" \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number",""))' 2>/dev/null)
  [ -n "$NUM" ] || { echo "oracle: could not open a PR"; exit 1; }
  curl -sS -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
    "$API/pulls/$NUM/merge" -d '{"Do":"merge"}' >/dev/null \
    || { echo "oracle: merge failed"; exit 1; }
  echo "oracle: merged PR #$NUM into main"
fi

# Not required by the score -- `score.py` sets reward = hidden_mean and leaves
# provenance unweighted -- but the deploy takes about half a minute here, and
# letting it land means the oracle run also demonstrates ci_green and deployed
# rather than leaving two checks reading zero for no reason.
sleep 45
echo "oracle: done"
exit 0
