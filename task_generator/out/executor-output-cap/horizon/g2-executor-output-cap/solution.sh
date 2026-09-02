#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py b/src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py
index 2750905..b225f4f 100644
--- a/src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py
+++ b/src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py
@@ -8,10 +8,18 @@ from concurrent.futures import ThreadPoolExecutor
 from functools import partial
 
 from bespokelabs.curator.code_executor.code_execution_backend.base_backend import BaseCodeExecutionBackend
+from bespokelabs.curator.code_executor.output_cap import (
+    DEFAULT_MAX_OUTPUT_BYTES,
+    MIN_MAX_OUTPUT_BYTES,
+    TRUNCATION_LOG_TEMPLATE,
+    cap_execution_streams,
+    cap_stream,
+)
 from bespokelabs.curator.code_executor.types import CodeAPIRequest, CodeExecutionOutput
 from bespokelabs.curator.log import logger
 
 WORKSPACE_DIR = "/workspace"
+MAX_OUTPUT_BYTES_ENV_VAR = "CURATOR_MAX_OUTPUT_BYTES"
 
 
 class SandboxCodeExecutionBackend(BaseCodeExecutionBackend):
@@ -28,6 +36,7 @@ class SandboxCodeExecutionBackend(BaseCodeExecutionBackend):
         self.config = config
         self.backend_name = backend_name
         self.thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count())
+        self.max_output_bytes: int = _resolve_max_output_bytes(config.max_output_bytes)
 
         # Build sandbox constructor kwargs from config
         self.sandbox_kwargs = {}
@@ -57,6 +66,7 @@ class SandboxCodeExecutionBackend(BaseCodeExecutionBackend):
                 timeout=request.execution_request.execution_params.timeout if request.execution_request.execution_params else 10,
                 backend_name=self.backend_name,
                 sandbox_kwargs=self.sandbox_kwargs,
+                max_output_bytes=self.max_output_bytes,
             ),
         )
 
@@ -72,6 +82,8 @@ def _execute_in_sandbox(
     timeout: int,
     backend_name: str,
     sandbox_kwargs: dict,
+    *,
+    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
 ) -> CodeExecutionOutput:
     """Execute code in a bespokelabs-sandbox.
 
@@ -102,8 +114,11 @@ def _execute_in_sandbox(
                 args=["-c", f'cd "${{SANDBOX_ROOT:-}}{WORKSPACE_DIR}" && timeout {timeout} python3 program.py < input.txt'],
             )
             files = _collect_sandbox_files(sb)
-            stdout = result.stdout
-            stderr = result.stderr
+            report = cap_execution_streams(result.stdout, result.stderr, max_output_bytes)
+            stdout = report.stdout
+            stderr = report.stderr
+            if report.truncated_streams:
+                logger.warning(TRUNCATION_LOG_TEMPLATE.format(streams=", ".join(report.truncated_streams), budget=max_output_bytes))
 
             if result.exit_code == 0:
                 return CodeExecutionOutput(
@@ -111,6 +126,7 @@ def _execute_in_sandbox(
                     stdout=stdout,
                     stderr=stderr,
                     files=files,
+                    truncated_streams=report.truncated_streams,
                 )
 
             if result.exit_code == 124:
@@ -120,6 +136,7 @@ def _execute_in_sandbox(
                     stdout=stdout,
                     stderr=stderr,
                     files=files,
+                    truncated_streams=report.truncated_streams,
                 )
 
             return CodeExecutionOutput(
@@ -128,21 +145,54 @@ def _execute_in_sandbox(
                 stdout=stdout,
                 stderr=stderr,
                 files=files,
+                truncated_streams=report.truncated_streams,
             )
 
     except Exception as e:
         if sb is not None and not files:
             files = _collect_sandbox_files(sb)
 
+        # Salvage whatever the half-built result carries, under the same budget.
+        salvaged = cap_execution_streams(getattr(result, "stdout", None), getattr(result, "stderr", None), max_output_bytes)
+        capped_error = cap_stream(str(e), max_output_bytes)
+
         return CodeExecutionOutput(
             message="error",
-            error=str(e),
-            stdout=getattr(result, "stdout", None),
-            stderr=getattr(result, "stderr", None),
+            error=capped_error.text,
+            stdout=salvaged.stdout,
+            stderr=salvaged.stderr,
             files=files,
+            truncated_streams=salvaged.truncated_streams,
+            error_truncated=capped_error.truncated,
         )
 
 
+def _resolve_max_output_bytes(configured: int) -> int:
+    """Resolve the effective output budget, letting the environment override the config.
+
+    A malformed or sub-floor ``CURATOR_MAX_OUTPUT_BYTES`` is ignored rather than
+    raised: a typo in an env var must not take the process down.
+
+    Args:
+        configured: The budget from the backend configuration.
+
+    Returns:
+        The budget to cap sandbox streams with.
+    """
+    raw = os.environ.get(MAX_OUTPUT_BYTES_ENV_VAR)
+    if raw is None:
+        return configured
+
+    try:
+        override = int(raw.strip())
+    except ValueError:
+        return configured
+
+    if override != 0 and override < MIN_MAX_OUTPUT_BYTES:
+        return configured
+    return override
+
+
 def _format_exit_code_error(exit_code: int | None, stderr: str | None) -> str:
     """Format a descriptive error message for non-zero exits."""
     status = "unknown" if exit_code is None else str(exit_code)
diff --git a/src/bespokelabs/curator/code_executor/output_cap.py b/src/bespokelabs/curator/code_executor/output_cap.py
new file mode 100644
index 0000000..01f762d
--- /dev/null
+++ b/src/bespokelabs/curator/code_executor/output_cap.py
@@ -0,0 +1,153 @@
+"""Byte-budget capping for sandboxed stdout/stderr."""
+
+from dataclasses import dataclass
+
+DEFAULT_MAX_OUTPUT_BYTES: int = 65536
+MIN_MAX_OUTPUT_BYTES: int = 16
+ELISION_MARKER_TEMPLATE: str = "\n[[curator:elided {dropped} bytes]]\n"
+TRUNCATION_LOG_TEMPLATE: str = "sandbox output capped: {streams} exceeded the {budget}-byte budget"
+
+# Longest UTF-8 sequence is four bytes, so a split codepoint is always repaired
+# by moving the cut by at most three bytes.
+_MAX_BOUNDARY_SHIFT: int = 3
+
+
+class OutputCapError(ValueError):
+    """Raised when a stream cap is too small to split head from tail."""
+
+    def __init__(self, max_bytes: int) -> None:
+        """Record the offending budget and build the message.
+
+        Args:
+            max_bytes: The rejected budget.
+        """
+        self.max_bytes: int = max_bytes
+        super().__init__(f"max_bytes must be 0 or at least {MIN_MAX_OUTPUT_BYTES}, got {max_bytes}")
+
+
+@dataclass(frozen=True)
+class CappedStream:
+    """A single stream after capping.
+
+    Attributes:
+        text: The capped stream, elision marker included. ``None`` only when the input was ``None``.
+        truncated: Whether the elision marker was inserted.
+        original_bytes: UTF-8 byte length of the input.
+        kept_bytes: UTF-8 byte length of head plus tail, marker excluded.
+    """
+
+    text: str | None
+    truncated: bool
+    original_bytes: int
+    kept_bytes: int
+
+
+@dataclass(frozen=True)
+class StreamCapReport:
+    """Both execution streams after capping.
+
+    Attributes:
+        stdout: The capped stdout.
+        stderr: The capped stderr.
+        truncated_streams: Alphabetically sorted names of the streams that were truncated.
+    """
+
+    stdout: str | None
+    stderr: str | None
+    truncated_streams: list[str]
+
+
+def cap_stream(data: str | bytes | None, max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> CappedStream:
+    """Cap a stream to a byte budget, keeping its head and its tail.
+
+    Beyond the budget the first ``(max_bytes * 3) // 4`` bytes and the last
+    ``max_bytes - (max_bytes * 3) // 4`` bytes are kept, joined by an elision
+    marker that is itself outside the budget. Both slices are moved to codepoint
+    boundaries, so a clean multi-byte stream never gains a replacement character.
+
+    Args:
+        data: The stream to cap. ``None`` is preserved as ``None``.
+        max_bytes: The budget in bytes. ``0`` disables capping.
+
+    Returns:
+        The capped stream and its accounting.
+
+    Raises:
+        OutputCapError: If ``max_bytes`` is negative or below ``MIN_MAX_OUTPUT_BYTES``.
+    """
+    if max_bytes != 0 and max_bytes < MIN_MAX_OUTPUT_BYTES:
+        raise OutputCapError(max_bytes)
+
+    if data is None:
+        return CappedStream(text=None, truncated=False, original_bytes=0, kept_bytes=0)
+
+    raw = data.encode("utf-8") if isinstance(data, str) else data
+    original_bytes = len(raw)
+
+    if max_bytes == 0 or original_bytes <= max_bytes:
+        return CappedStream(text=_decode(raw), truncated=False, original_bytes=original_bytes, kept_bytes=original_bytes)
+
+    head_budget = (max_bytes * 3) // 4
+    head, head_bytes = _decode_head(raw[:head_budget])
+    tail, tail_bytes = _decode_tail(raw[original_bytes - (max_bytes - head_budget) :])
+
+    kept_bytes = head_bytes + tail_bytes
+    marker = ELISION_MARKER_TEMPLATE.format(dropped=original_bytes - kept_bytes)
+    return CappedStream(text=f"{head}{marker}{tail}", truncated=True, original_bytes=original_bytes, kept_bytes=kept_bytes)
+
+
+def cap_execution_streams(
+    stdout: str | bytes | None,
+    stderr: str | bytes | None,
+    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
+) -> StreamCapReport:
+    """Cap both execution streams with the same budget.
+
+    Args:
+        stdout: The stdout stream.
+        stderr: The stderr stream.
+        max_bytes: The budget in bytes. ``0`` disables capping.
+
+    Returns:
+        The capped streams and the sorted names of those that were truncated.
+
+    Raises:
+        OutputCapError: If ``max_bytes`` is negative or below ``MIN_MAX_OUTPUT_BYTES``.
+    """
+    capped_stdout = cap_stream(stdout, max_bytes)
+    capped_stderr = cap_stream(stderr, max_bytes)
+
+    truncated_streams = []
+    if capped_stderr.truncated:
+        truncated_streams.append("stderr")
+    if capped_stdout.truncated:
+        truncated_streams.append("stdout")
+
+    return StreamCapReport(stdout=capped_stdout.text, stderr=capped_stderr.text, truncated_streams=truncated_streams)
+
+
+def _decode(raw: bytes) -> str:
+    """Decode bytes, replacing anything that is not valid UTF-8."""
+    return raw.decode("utf-8", errors="replace")
+
+
+def _decode_head(chunk: bytes) -> tuple[str, int]:
+    """Decode a head slice, dropping up to three trailing bytes to land on a boundary."""
+    for cut in range(_MAX_BOUNDARY_SHIFT + 1):
+        candidate = chunk[: len(chunk) - cut]
+        try:
+            return candidate.decode("utf-8"), len(candidate)
+        except UnicodeDecodeError:
+            continue
+    return _decode(chunk), len(chunk)
+
+
+def _decode_tail(chunk: bytes) -> tuple[str, int]:
+    """Decode a tail slice, dropping up to three leading bytes to land on a boundary."""
+    for drop in range(_MAX_BOUNDARY_SHIFT + 1):
+        candidate = chunk[drop:]
+        try:
+            return candidate.decode("utf-8"), len(candidate)
+        except UnicodeDecodeError:
+            continue
+    return _decode(chunk), len(chunk)
diff --git a/src/bespokelabs/curator/code_executor/types.py b/src/bespokelabs/curator/code_executor/types.py
index 2843516..7729abb 100644
--- a/src/bespokelabs/curator/code_executor/types.py
+++ b/src/bespokelabs/curator/code_executor/types.py
@@ -2,7 +2,9 @@ import datetime
 from dataclasses import field
 from typing import Any, Dict, Optional
 
-from pydantic import BaseModel
+from pydantic import BaseModel, Field, field_validator
+
+from bespokelabs.curator.code_executor.output_cap import DEFAULT_MAX_OUTPUT_BYTES, MIN_MAX_OUTPUT_BYTES, OutputCapError
 
 
 class CodeExecutionResult(BaseModel):
@@ -11,6 +13,7 @@ class CodeExecutionResult(BaseModel):
     stdout: str
     stderr: str
     exit_code: int
+    truncated_streams: list[str] = []
 
 
 class CodeExecutionRequestParams(BaseModel):
@@ -50,6 +53,8 @@ class CodeExecutionOutput(BaseModel):
     stdout: Optional[str] = None
     stderr: Optional[str] = None
     files: Optional[str] = None
+    truncated_streams: list[str] = []
+    error_truncated: bool = False
 
 
 class CodeExecutionResponse(BaseModel):
@@ -69,6 +74,16 @@ class CodeExecutionBackendConfig(BaseModel):
     max_retries: int = 3
     seconds_to_pause_on_rate_limit: int = 10
     image: Optional[str] = None
+    # Byte budget for captured stdout/stderr; 0 disables capping
+    max_output_bytes: int = Field(default=DEFAULT_MAX_OUTPUT_BYTES, ge=0)
     # Legacy aliases — mapped to sandbox params at runtime
     docker_image: Optional[str] = None
     base_url: Optional[str] = None
+
+    @field_validator("max_output_bytes")
+    @classmethod
+    def _check_output_cap_floor(cls, value: int) -> int:
+        """Reject a budget the capping layer would refuse on every request."""
+        if value != 0 and value < MIN_MAX_OUTPUT_BYTES:
+            raise OutputCapError(value)
+        return value
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
