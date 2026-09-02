#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/agent/agent.py b/src/bespokelabs/curator/agent/agent.py
index 150970e..10d1dd1 100644
--- a/src/bespokelabs/curator/agent/agent.py
+++ b/src/bespokelabs/curator/agent/agent.py
@@ -1,5 +1,6 @@
 import os
 import typing as t
+import uuid
 from datetime import datetime
 
 from xxhash import xxh64
@@ -190,9 +191,10 @@ class MultiTurnAgents:
                 os.path.expanduser(_CURATOR_DEFAULT_CACHE_DIR),
             )
         disable_cache = os.getenv("CURATOR_DISABLE_CACHE", "").lower() in ["true", "1"]
-        fingerprint = self.seeder._hash_fingerprint(disable_cache=disable_cache)
+        run_id = None if not disable_cache else (os.environ.get("CURATOR_RUN_ID") or uuid.uuid4().hex)
+        fingerprint = self.seeder._run_identity("", cache_enabled=not disable_cache, run_id=run_id).digest
         fingerprint += xxh64(self.seed_message).hexdigest()
-        fingerprint += self.partner._hash_fingerprint(disable_cache=disable_cache)
+        fingerprint += self.partner._run_identity("", cache_enabled=not disable_cache, run_id=run_id).digest
         working_dir = os.path.join(working_dir, fingerprint)
         os.makedirs(working_dir, exist_ok=True)
         logger.info(f"Running multi turn simulation, find results in {working_dir}")
diff --git a/src/bespokelabs/curator/db.py b/src/bespokelabs/curator/db.py
index fd23c28..a37afe6 100644
--- a/src/bespokelabs/curator/db.py
+++ b/src/bespokelabs/curator/db.py
@@ -3,6 +3,30 @@
 import os
 import sqlite3
 
+from bespokelabs.curator.run_identity import RUN_IDENTITY_VERSION
+
+#: The columns of the `runs` table, in creation order, as (name, sqlite type).
+#: Columns missing from an older database are added by `MetadataDB.validate_schema`.
+RUNS_COLUMNS: tuple[tuple[str, str], ...] = (
+    ("run_hash", "TEXT"),
+    ("session_id", "TEXT"),
+    ("dataset_hash", "TEXT"),
+    ("prompt_func", "TEXT"),
+    ("parse_func", "TEXT"),
+    ("model_name", "TEXT"),
+    ("response_format", "TEXT"),
+    ("batch_mode", "BOOLEAN"),
+    ("created_time", "TEXT"),
+    ("last_edited_time", "TEXT"),
+    ("is_hosted_viewer_synced", "BOOLEAN"),
+    ("identity_version", "INTEGER"),
+    # Cost management columns
+    ("total_cost_milli_dollars", "TEXT"),
+    ("total_requests", "TEXT"),
+    ("total_prompt_tokens", "TEXT"),
+    ("total_completion_tokens", "TEXT"),
+)
+
 
 class MetadataDB:
     """Database class for storing Bella run metadata."""
@@ -28,34 +52,27 @@ class MetadataDB:
             schema_info = cursor.fetchall()
         return schema_info
 
-    def validate_schema(self):
-        """Validate that the current database schema matches the expected schema.
+    def validate_schema(self) -> tuple[str, ...]:
+        """Validate the current database schema, migrating it forward if needed.
+
+        Columns of `RUNS_COLUMNS` that are missing from the table are added in
+        place, leaving existing rows untouched (the new columns are NULL for
+        them). Columns that are in the table but not in `RUNS_COLUMNS` are still
+        fatal, since they can only come from a schema this version cannot read.
+
+        Returns:
+            tuple[str, ...]: The names of the columns that were added, in
+                             `RUNS_COLUMNS` order. Empty if nothing was added.
 
         Raises:
-            RuntimeError: If there is a mismatch between the current schema and expected schema,
+            RuntimeError: If the table has columns that are not expected,
                         with instructions to clear the cache.
         """
-        expected_columns = [
-            "run_hash",
-            "session_id",
-            "dataset_hash",
-            "prompt_func",
-            "model_name",
-            "response_format",
-            "batch_mode",
-            "created_time",
-            "last_edited_time",
-            "is_hosted_viewer_synced",
-            # Cost management columns
-            "total_cost_milli_dollars",
-            "total_requests",
-            "total_prompt_tokens",
-            "total_completion_tokens",
-        ]
+        expected_columns = [name for name, _ in RUNS_COLUMNS]
         current_info = self._get_current_schema()
         current_columns = [col[1] for col in current_info]  # col[1] = column name
 
-        if set(current_columns) != set(expected_columns):
+        if set(current_columns) - set(expected_columns):
             msg = (
                 "Detected a mismatch between the local DB schema and the expected schema. "
                 "Please clear your cache with `rm -rf ~/.cache/curator` or "
@@ -63,7 +80,18 @@ class MetadataDB:
             )
             raise RuntimeError(msg)
 
-    def store_metadata(self, metadata: dict):
+        missing_columns = tuple(name for name, _ in RUNS_COLUMNS if name not in set(current_columns))
+        if missing_columns:
+            types = dict(RUNS_COLUMNS)
+            with sqlite3.connect(self.db_path) as conn:
+                cursor = conn.cursor()
+                for name in missing_columns:
+                    cursor.execute(f'ALTER TABLE runs ADD COLUMN "{name}" {types[name]}')
+                conn.commit()
+
+        return missing_columns
+
+    def store_metadata(self, metadata: dict) -> str:
         """Store metadata about a Bella run in the database.
 
         Args:
@@ -71,17 +99,23 @@ class MetadataDB:
                 - timestamp: ISO format timestamp
                 - dataset_hash: Unique hash of input dataset
                 - prompt_func: Source code of prompt function
+                - parse_func: Source code of parse function
                 - model_name: Name of model used
                 - response_format: JSON schema of response format
                 - run_hash: Unique hash identifying the run
                 - batch_mode: Boolean indicating batch mode or online mode (True = batch, False = online)
+                - identity_version: Version of the run identity rule that produced the run hash
+
+        Returns:
+            str: "inserted" if a new row was created, "updated" if an existing
+                 row for this run hash was refreshed.
         """
         os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
         with sqlite3.connect(self.db_path) as conn:
             cursor = conn.cursor()
             # IMPORTANT: If you modify the CREATE TABLE schema below,
-            # you must update the expected_columns list in validate_schema()
-            # to match the new schema. Otherwise, schema validation will fail.
+            # you must update RUNS_COLUMNS to match the new schema.
+            # Otherwise, schema validation will fail.
             cursor.execute(
                 """
                 CREATE TABLE IF NOT EXISTS runs (
@@ -89,12 +123,14 @@ class MetadataDB:
                     session_id TEXT,
                     dataset_hash TEXT,
                     prompt_func TEXT,
+                    parse_func TEXT,
                     model_name TEXT,
                     response_format TEXT,
                     batch_mode BOOLEAN,
                     created_time TEXT,
                     last_edited_time TEXT,
                     is_hosted_viewer_synced BOOLEAN,
+                    identity_version INTEGER,
 
                     total_cost_milli_dollars TEXT,
                     total_requests TEXT,
@@ -113,38 +149,55 @@ class MetadataDB:
             existing_run = cursor.fetchone()
 
             if existing_run:
-                # Update last_edited_time for existing entry
-                cursor.execute(
-                    """
-                    UPDATE runs
-                    SET last_edited_time = ?
-                    WHERE run_hash = ?
-                    """,
-                    (metadata["timestamp"], metadata["run_hash"]),
-                )
+                # Update last_edited_time for existing entry, and the session id
+                # if this run has one (a run may be replayed without a session).
+                if metadata.get("session_id") is not None:
+                    cursor.execute(
+                        """
+                        UPDATE runs
+                        SET last_edited_time = ?, session_id = ?
+                        WHERE run_hash = ?
+                        """,
+                        (metadata["timestamp"], metadata["session_id"], metadata["run_hash"]),
+                    )
+                else:
+                    cursor.execute(
+                        """
+                        UPDATE runs
+                        SET last_edited_time = ?
+                        WHERE run_hash = ?
+                        """,
+                        (metadata["timestamp"], metadata["run_hash"]),
+                    )
+                status = "updated"
             else:
                 # Insert new entry
                 cursor.execute(
                     """
                     INSERT INTO runs (
-                        run_hash, session_id, dataset_hash, prompt_func, model_name,
-                        response_format, batch_mode, created_time, last_edited_time, is_hosted_viewer_synced
-                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
+                        run_hash, session_id, dataset_hash, prompt_func, parse_func, model_name,
+                        response_format, batch_mode, created_time, last_edited_time, is_hosted_viewer_synced,
+                        identity_version
+                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                     """,
                     (
                         metadata["run_hash"],
                         metadata["session_id"],
                         metadata["dataset_hash"],
                         metadata["prompt_func"],
+                        metadata.get("parse_func", ""),
                         metadata["model_name"],
                         metadata["response_format"],
                         metadata["batch_mode"],
                         metadata["timestamp"],
                         metadata["timestamp"],  # last_edited_time same as created_time initially
                         metadata["is_hosted_viewer_synced"],
+                        int(metadata.get("identity_version", RUN_IDENTITY_VERSION)),
                     ),
                 )
+                status = "inserted"
             conn.commit()
+        return status
 
     def get_existing_session_id(self, run_hash: str):
         """Get existing session id from previous run."""
diff --git a/src/bespokelabs/curator/llm/llm.py b/src/bespokelabs/curator/llm/llm.py
index 26fe117..045521a 100644
--- a/src/bespokelabs/curator/llm/llm.py
+++ b/src/bespokelabs/curator/llm/llm.py
@@ -2,8 +2,8 @@
 
 import inspect
 import os
+import uuid
 from datetime import datetime
-from io import BytesIO
 from pathlib import Path
 from typing import Any, Dict, Iterable, Optional, Type, TypeVar, Union
 
@@ -19,6 +19,13 @@ from bespokelabs.curator.log import add_file_handler, logger
 from bespokelabs.curator.request_processor._factory import _RequestProcessorFactory
 from bespokelabs.curator.request_processor.config import BackendParamsType
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
+from bespokelabs.curator.run_identity import (
+    RunIdentity,
+    RunIdentityError,
+    _get_function_hash,
+    compute_run_identity,
+    reconcile_run_directory,
+)
 from bespokelabs.curator.types.curator_response import CuratorResponse
 
 T = TypeVar("T")
@@ -130,6 +137,7 @@ class LLM:
             system_prompt=system_prompt,
         )
         self.batch_mode = batch
+        self._backend_params = dict(backend_params) if backend_params is not None else {}
 
         self._request_processor = _RequestProcessorFactory.create(
             params=backend_params,
@@ -141,32 +149,28 @@ class LLM:
             return_completions_object=self.return_completions_object,
         )
 
-    def _hash_fingerprint(self, dataset_hash: str = "", disable_cache: bool = False):
-        if disable_cache:
-            fingerprint = xxh64(os.urandom(8)).hexdigest()
-        else:
-            # Get the source code of the prompt and parse methods
-            prompt_func_hash = _get_function_hash(self.prompt_formatter.prompt_func)
-
-            fingerprint_str = "_".join(
-                [
-                    str(dataset_hash),
-                    str(prompt_func_hash),
-                    str(self.prompt_formatter.model_name),
-                    str(self.prompt_formatter.response_format.model_json_schema() if self.prompt_formatter.response_format else "text"),
-                    str(self.batch_mode),
-                ]
-            )
+    @property
+    def backend(self) -> str:
+        """The resolved backend name, e.g. "openai" even when it was auto-determined."""
+        return self._request_processor.backend
 
-            if self.prompt_formatter.generation_params:
-                generation_params_str = str(sorted(self.prompt_formatter.generation_params.items()))
-                fingerprint_str += f"_{generation_params_str}"
+    @property
+    def backend_params(self) -> dict:
+        """A copy of the backend parameters this LLM was constructed with."""
+        return dict(self._backend_params)
 
-            fingerprint = xxh64(fingerprint_str.encode("utf-8")).hexdigest()
-            logger.debug(f"Curator Cache Fingerprint String: {fingerprint_str}")
-            logger.debug(f"Curator Cache Fingerprint: {fingerprint}")
+    def _run_identity(self, dataset_hash: str, *, cache_enabled: bool, run_id: Optional[str] = None) -> RunIdentity:
+        """Compute the identity of a run of this LLM.
 
-        return fingerprint
+        Args:
+            dataset_hash: The fingerprint of the input dataset.
+            cache_enabled: Whether this run may reuse (and be reused as) a cache.
+            run_id: The ephemeral id identifying a cache-disabled run.
+
+        Returns:
+            RunIdentity: The components, their digest and the resulting run hash.
+        """
+        return compute_run_identity(self, dataset_hash, cache_enabled=cache_enabled, run_id=run_id)
 
     def _get_cached_response(self, cache_dir: str, dataset: Dataset) -> Optional[CuratorResponse]:
         """Check if a cached response exists and return it if valid.
@@ -177,9 +181,14 @@ class LLM:
 
         Returns:
             Optional[CuratorResponse]: Cached response if it exists and is valid, None otherwise
+
+        Raises:
+            RunIdentityError: If the cache directory does not describe this run.
         """
         try:
             return CuratorResponse.load(cache_dir, dataset)
+        except RunIdentityError:
+            raise
         except Exception as e:
             logger.warning(f"Failed to load curator cached response: {e}")
             return None
@@ -191,6 +200,7 @@ class LLM:
         batch_cancel: bool = False,
         batch_cancel_auto_confirm: bool = False,
         cache_dir: Optional[Union[str, Path]] = None,
+        run_id: Optional[str] = None,
     ) -> CuratorResponse:
         """Apply structured completions in parallel to a dataset using specified model and prompts.
 
@@ -200,9 +210,15 @@ class LLM:
             batch_cancel (bool): Whether to cancel the batch if it is running
             batch_cancel_auto_confirm (bool): Whether we should automatically run batch cancellation without explicit user confirmation (for testing)
             cache_dir: Directory to cache results
+            run_id (str): Identifier of this run, only used when caching is disabled (CURATOR_DISABLE_CACHE),
+                where it is what keeps two runs apart. Defaults to CURATOR_RUN_ID, or a fresh random id.
 
         Returns:
             CuratorResponse: A response object containing the dataset, failed requests, and various statistics
+
+        Raises:
+            RunIdentityError: If the run cache directory belongs to a different run, or if a run_id
+                is given for a run that has caching enabled.
         """
         # We convert from iterable to Dataset because Dataset has random access via row_idx
         if dataset:
@@ -219,10 +235,19 @@ class LLM:
             curator_cache_dir = working_dir
 
         disable_cache = os.getenv("CURATOR_DISABLE_CACHE", "").lower() in ["true", "1"]
-        fingerprint = self._hash_fingerprint(dataset_hash, disable_cache)
-
-        run_cache_dir = os.path.join(curator_cache_dir, fingerprint)
-        os.makedirs(run_cache_dir, exist_ok=True)
+        cache_enabled = not disable_cache
+        if disable_cache and run_id is None:
+            # A cache-disabled run still needs an identity, it just must not be reused.
+            run_id = os.environ.get("CURATOR_RUN_ID") or uuid.uuid4().hex
+
+        now = datetime.now().isoformat()
+        identity = self._run_identity(dataset_hash, cache_enabled=cache_enabled, run_id=run_id)
+        run_hash = identity.run_hash
+
+        run_cache_dir = os.path.join(curator_cache_dir, run_hash)
+        directory_check = reconcile_run_directory(run_cache_dir, identity, now=now)
+        logger.debug(f"Run directory {run_cache_dir} {directory_check.status}")
+        run_identity = directory_check.stamp.to_dict()
         add_file_handler(run_cache_dir)
 
         if batch_cancel and self.batch_mode:
@@ -234,7 +259,7 @@ class LLM:
                     working_dir=run_cache_dir, dataset=dataset, prompt_formatter=self.prompt_formatter, auto_confirm=batch_cancel_auto_confirm
                 )
             )
-            return CuratorResponse(dataset=dataset, batch_mode=self.batch_mode, cache_dir=run_cache_dir)
+            return CuratorResponse(dataset=dataset, batch_mode=self.batch_mode, cache_dir=run_cache_dir, run_identity=run_identity)
 
         elif batch_cancel:
             logger.warning("You set batch_cancel=True but you're not in batch mode. Ignoring batch_cancel.")
@@ -251,14 +276,15 @@ class LLM:
             parse_func_source = ""
 
         metadata_dict = {
-            "timestamp": datetime.now().isoformat(),
+            "timestamp": now,
             "dataset_hash": dataset_hash,
             "prompt_func": prompt_func_source,
             "parse_func": parse_func_source,
             "model_name": self.prompt_formatter.model_name,
             "response_format": (str(self.prompt_formatter.response_format.model_json_schema()) if self.prompt_formatter.response_format else "text"),
-            "run_hash": fingerprint,
+            "run_hash": run_hash,
             "batch_mode": self.batch_mode,
+            "identity_version": identity.identity_version,
         }
 
         existing_session_id = metadata_db.get_existing_session_id(metadata_dict["run_hash"])
@@ -310,6 +336,7 @@ class LLM:
                 else None,
                 model_name=self.prompt_formatter.model_name,
                 metadata=metadata_dict,
+                run_identity=run_identity,
             )
             response.update_tracker_stats(tracker)
         else:
@@ -326,6 +353,7 @@ class LLM:
                     else None,
                     model_name=self.prompt_formatter.model_name,
                     metadata=metadata_dict,
+                    run_identity=run_identity,
                 )
 
         # Save the response if cache directory is specified
@@ -334,40 +362,6 @@ class LLM:
         return response
 
 
-def _get_function_hash(func) -> str:
-    # setting recursion limit to avoid random recursion limit error
-    # todo: understand why this is happening and fix it
-    import sys
-
-    sys.setrecursionlimit(10000)
-
-    """Get a hash of a function's source code."""
-    if func is None:
-        return xxh64("").hexdigest()
-
-    # Remove parameter annotations to avoid dill complaining about pickling
-    # pydantic BaseModel: https://github.com/bespokelabsai/curator/issues/229.
-    # For class/instance methods, get the underlying function
-    if hasattr(func, "__func__"):
-        func = func.__func__
-
-    # Clear annotations if they exist
-    if hasattr(func, "__annotations__"):
-        func.__annotations__ = {}
-
-    file = BytesIO()
-
-    from datasets.utils._dill import Pickler
-
-    try:
-        Pickler(file, recurse=True).dump(func)
-    except TypeError:
-        logger.debug("Failed to recursive pickle function, trying non-recursive")
-        Pickler(file, recurse=False).dump(func)
-
-    return xxh64(file.getvalue()).hexdigest()
-
-
 def _get_function_source(func) -> str:
     """Get the source code of a function.
 
diff --git a/src/bespokelabs/curator/request_processor/base_request_processor.py b/src/bespokelabs/curator/request_processor/base_request_processor.py
index c3828af..47723db 100644
--- a/src/bespokelabs/curator/request_processor/base_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/base_request_processor.py
@@ -121,6 +121,7 @@ class BaseRequestProcessor(ABC):
         Raises:
             ValueError: If model doesn't support structured output but it's requested
         """
+        self._is_cached_dataset = False
         self.prompt_formatter = prompt_formatter
         self.working_dir = working_dir
         self.total_requests = len(dataset) if dataset is not None else 1
diff --git a/src/bespokelabs/curator/run_identity.py b/src/bespokelabs/curator/run_identity.py
new file mode 100644
index 0000000..4715b8d
--- /dev/null
+++ b/src/bespokelabs/curator/run_identity.py
@@ -0,0 +1,433 @@
+"""Run identity: what makes two curator runs the same run.
+
+A run identity is the versioned answer to "have I run this before?". It is
+computed from a fixed set of components (:data:`IDENTITY_COMPONENT_KEYS`),
+canonicalised into a stable payload, hashed, and written next to the run's
+files as ``run_identity.json`` so a later run can tell whether the directory
+it is about to reuse really belongs to it.
+
+This module is deliberately free of ambient state: it never reads the clock,
+the environment or a source of randomness. Every timestamp and every
+ephemeral run id is passed in by the caller.
+"""
+
+import json
+import os
+from dataclasses import dataclass
+from io import BytesIO
+from pathlib import Path
+from typing import Any, Mapping, Optional, Union
+
+from xxhash import xxh64
+
+from bespokelabs.curator.log import logger
+
+RUN_IDENTITY_VERSION: int = 3
+RUN_IDENTITY_FILENAME: str = "run_identity.json"
+PAYLOAD_PREFIX: str = "curator-run-identity/v3\n"
+
+#: Backend parameters that change *what* comes back and therefore fork the cache.
+#: Everything else (retries, timeouts, rate limits, ...) only changes how the work
+#: is done. ``api_key`` is deliberately excluded: the components are written to
+#: disk in cleartext.
+IDENTITY_BACKEND_PARAM_KEYS: frozenset[str] = frozenset({"azure_deployment", "base_url", "batch_size", "completion_window"})
+
+IDENTITY_COMPONENT_KEYS: tuple[str, ...] = (
+    "backend",
+    "backend_params",
+    "batch_mode",
+    "dataset_hash",
+    "generation_params",
+    "model_name",
+    "parse_func_hash",
+    "prompt_func_hash",
+    "response_format",
+    "return_completions_object",
+    "run_id",
+    "system_prompt",
+)
+
+
+class RunIdentityError(RuntimeError):
+    """Base class for every run-identity failure."""
+
+
+class RunIdentityMismatch(RunIdentityError):  # noqa: N818
+    """Raised when a run directory was written under a different identity."""
+
+    def __init__(self, path: str, expected_run_hash: str, found_run_hash: Optional[str], mismatched_components: tuple[str, ...]) -> None:
+        """Initialize the mismatch.
+
+        Args:
+            path: The run directory that disagrees with this run.
+            expected_run_hash: The run hash of the run that wants the directory.
+            found_run_hash: The run hash recorded in the directory, if any.
+            mismatched_components: Names of the components that differ.
+        """
+        self.path: str = path
+        self.expected_run_hash: str = expected_run_hash
+        self.found_run_hash: Optional[str] = found_run_hash
+        self.mismatched_components: tuple[str, ...] = mismatched_components
+        super().__init__(
+            f"{path} was written under run identity {found_run_hash!r}, expected {expected_run_hash!r} "
+            f"(differing: {', '.join(mismatched_components) or 'unknown'})"
+        )
+
+
+class CachedResponseMismatch(RunIdentityError):  # noqa: N818
+    """Raised when a cached response.json does not describe the dataset it is loaded with."""
+
+    def __init__(self, cache_dir: str, field: str, expected: Any, found: Any) -> None:
+        """Initialize the mismatch.
+
+        Args:
+            cache_dir: The cache directory the response was loaded from.
+            field: The dataset field that differs ("fingerprint", "size" or "columns").
+            expected: The value recorded in the cached response.
+            found: The value of the dataset that was handed to ``load``.
+        """
+        self.cache_dir: str = cache_dir
+        self.field: str = field
+        self.expected: Any = expected
+        self.found: Any = found
+        super().__init__(f"cached response in {cache_dir} has {field}={expected!r}, dataset has {found!r}")
+
+
+@dataclass(frozen=True)
+class RunIdentity:
+    """The identity of a single curator run.
+
+    Attributes:
+        run_hash: The directory name for the run, e.g. ``v3-2917e0582eb73e61``.
+        digest: The bare 16 character xxh64 digest of the canonical payload.
+        identity_version: The version of the identity rule that produced it.
+        cache_enabled: Whether this run may reuse (and be reused as) a cache.
+        components: The components the digest was computed from.
+    """
+
+    run_hash: str
+    digest: str
+    identity_version: int
+    cache_enabled: bool
+    components: dict[str, Any]
+
+
+@dataclass(frozen=True)
+class RunStamp:
+    """The contents of a run directory's ``run_identity.json``.
+
+    Attributes:
+        identity_version: The identity version the directory was stamped with.
+        run_hash: The run hash of the run that owns the directory.
+        digest: The bare digest of the run.
+        components: The components the digest was computed from.
+        created_at: When the directory was first stamped.
+        updated_at: When the directory was last used.
+    """
+
+    identity_version: int
+    run_hash: str
+    digest: str
+    components: dict[str, Any]
+    created_at: str
+    updated_at: str
+
+    def to_dict(self) -> dict[str, Any]:
+        """Return the stamp as a JSON serialisable dictionary."""
+        return {
+            "identity_version": self.identity_version,
+            "run_hash": self.run_hash,
+            "digest": self.digest,
+            "components": dict(self.components),
+            "created_at": self.created_at,
+            "updated_at": self.updated_at,
+        }
+
+    @classmethod
+    def from_dict(cls, data: Mapping[str, Any]) -> "RunStamp":
+        """Build a stamp from its dictionary form.
+
+        Args:
+            data: A mapping carrying the six stamp keys.
+
+        Returns:
+            RunStamp: The parsed stamp.
+        """
+        return cls(
+            identity_version=int(data["identity_version"]),
+            run_hash=data["run_hash"],
+            digest=data["digest"],
+            components=dict(data["components"]),
+            created_at=data["created_at"],
+            updated_at=data["updated_at"],
+        )
+
+
+@dataclass(frozen=True)
+class RunDirectoryCheck:
+    """The outcome of reconciling a run directory with a run identity.
+
+    Attributes:
+        status: One of ``"created"``, ``"adopted"``, ``"upgraded"`` or ``"matched"``.
+        stamp: The stamp now on disk.
+        previous_version: The identity version found on disk, if there was one.
+    """
+
+    status: str
+    stamp: RunStamp
+    previous_version: Optional[int]
+
+
+def _get_function_hash(func) -> str:
+    # setting recursion limit to avoid random recursion limit error
+    # todo: understand why this is happening and fix it
+    import sys
+
+    sys.setrecursionlimit(10000)
+
+    """Get a hash of a function's source code."""
+    if func is None:
+        return xxh64("").hexdigest()
+
+    # Remove parameter annotations to avoid dill complaining about pickling
+    # pydantic BaseModel: https://github.com/bespokelabsai/curator/issues/229.
+    # For class/instance methods, get the underlying function
+    if hasattr(func, "__func__"):
+        func = func.__func__
+
+    # Clear annotations if they exist
+    if hasattr(func, "__annotations__"):
+        func.__annotations__ = {}
+
+    file = BytesIO()
+
+    from datasets.utils._dill import Pickler
+
+    try:
+        Pickler(file, recurse=True).dump(func)
+    except TypeError:
+        logger.debug("Failed to recursive pickle function, trying non-recursive")
+        Pickler(file, recurse=False).dump(func)
+
+    return xxh64(file.getvalue()).hexdigest()
+
+
+def _validate_run_id(cache_enabled: bool, run_id: Optional[str]) -> None:
+    """Check that the run id agrees with whether caching is enabled.
+
+    Args:
+        cache_enabled: Whether the run may reuse a cache.
+        run_id: The ephemeral id identifying a cache-disabled run.
+
+    Raises:
+        RunIdentityError: If a cache-disabled run has no run id, or a cached run has one.
+    """
+    if cache_enabled:
+        if run_id is not None:
+            raise RunIdentityError(f"run_id is only meaningful when caching is disabled, got run_id={run_id!r} with cache_enabled=True")
+    elif not run_id:
+        raise RunIdentityError("caching is disabled, which requires a non-empty run_id (curator never mints one implicitly)")
+
+
+def build_components(llm, dataset_hash: str, *, cache_enabled: bool = True, run_id: Optional[str] = None) -> dict[str, Any]:
+    """Collect the components a run is identified by.
+
+    Args:
+        llm: Any object exposing ``prompt_formatter``, ``batch_mode``, ``backend``,
+            ``backend_params`` and ``return_completions_object``.
+        dataset_hash: The fingerprint of the input dataset.
+        cache_enabled: Whether the run may reuse a cache.
+        run_id: The ephemeral id of a cache-disabled run.
+
+    Returns:
+        dict[str, Any]: Exactly the keys of :data:`IDENTITY_COMPONENT_KEYS`.
+
+    Raises:
+        RunIdentityError: If the run id does not agree with ``cache_enabled``.
+    """
+    _validate_run_id(cache_enabled, run_id)
+
+    formatter = llm.prompt_formatter
+    response_format = formatter.response_format
+    backend_params = dict(llm.backend_params or {})
+
+    return {
+        "backend": str(llm.backend),
+        "backend_params": {key: value for key, value in backend_params.items() if key in IDENTITY_BACKEND_PARAM_KEYS},
+        "batch_mode": bool(llm.batch_mode),
+        "dataset_hash": str(dataset_hash),
+        "generation_params": dict(formatter.generation_params or {}),
+        "model_name": str(formatter.model_name),
+        "parse_func_hash": _get_function_hash(formatter.parse_func),
+        "prompt_func_hash": _get_function_hash(formatter.prompt_func),
+        "response_format": (json.dumps(response_format.model_json_schema(), sort_keys=True, separators=(",", ":")) if response_format else "text"),
+        "return_completions_object": bool(llm.return_completions_object),
+        "run_id": None if cache_enabled else run_id,
+        "system_prompt": formatter.system_prompt,
+    }
+
+
+def canonical_payload(components: Mapping[str, Any]) -> str:
+    """Render components as the exact string that gets hashed.
+
+    Args:
+        components: The components of a run identity.
+
+    Returns:
+        str: The versioned prefix followed by one line of compact, sorted JSON.
+
+    Raises:
+        RunIdentityError: If a component value is not JSON serialisable.
+    """
+    try:
+        body = json.dumps(dict(components), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
+    except (TypeError, ValueError) as e:
+        raise RunIdentityError(f"run identity components are not JSON serializable: {e}") from e
+    return PAYLOAD_PREFIX + body
+
+
+def hash_components(components: Mapping[str, Any]) -> str:
+    """Return the bare 16 character digest of the components.
+
+    Args:
+        components: The components of a run identity.
+
+    Returns:
+        str: The lowercase xxh64 hexdigest of the canonical payload.
+    """
+    return xxh64(canonical_payload(components).encode("utf-8")).hexdigest()
+
+
+def format_run_hash(digest: str, *, cache_enabled: bool) -> str:
+    """Turn a digest into the run hash used as the cache directory name.
+
+    Args:
+        digest: The bare digest of the components.
+        cache_enabled: Whether the run may reuse a cache.
+
+    Returns:
+        str: ``v3-<digest>``, or ``v3-nocache-<digest>`` for cache-disabled runs.
+    """
+    if cache_enabled:
+        return f"v{RUN_IDENTITY_VERSION}-{digest}"
+    return f"v{RUN_IDENTITY_VERSION}-nocache-{digest}"
+
+
+def compute_run_identity(llm, dataset_hash: str, *, cache_enabled: bool = True, run_id: Optional[str] = None) -> RunIdentity:
+    """Compute the identity of a run.
+
+    Args:
+        llm: The object the components are read off (see :func:`build_components`).
+        dataset_hash: The fingerprint of the input dataset.
+        cache_enabled: Whether the run may reuse a cache.
+        run_id: The ephemeral id of a cache-disabled run.
+
+    Returns:
+        RunIdentity: The components, their digest and the resulting run hash.
+    """
+    components = build_components(llm, dataset_hash, cache_enabled=cache_enabled, run_id=run_id)
+    digest = hash_components(components)
+    run_hash = format_run_hash(digest, cache_enabled=cache_enabled)
+    logger.debug(f"Curator run identity payload: {canonical_payload(components)}")
+    logger.debug(f"Curator run identity: {run_hash}")
+    return RunIdentity(run_hash=run_hash, digest=digest, identity_version=RUN_IDENTITY_VERSION, cache_enabled=cache_enabled, components=components)
+
+
+def write_run_stamp(run_cache_dir: Union[str, Path], identity: RunIdentity, *, now: str, created_at: Optional[str] = None) -> RunStamp:
+    """Write ``run_identity.json`` into a run directory.
+
+    Args:
+        run_cache_dir: The run directory, created if it does not exist.
+        identity: The identity to stamp the directory with.
+        now: The timestamp of this run.
+        created_at: The timestamp to preserve as the creation time, if any.
+
+    Returns:
+        RunStamp: The stamp that was written.
+    """
+    run_cache_dir = Path(run_cache_dir)
+    run_cache_dir.mkdir(parents=True, exist_ok=True)
+    stamp = RunStamp(
+        identity_version=identity.identity_version,
+        run_hash=identity.run_hash,
+        digest=identity.digest,
+        components=dict(identity.components),
+        created_at=created_at if created_at is not None else now,
+        updated_at=now,
+    )
+    with open(run_cache_dir / RUN_IDENTITY_FILENAME, "w") as f:
+        f.write(json.dumps(stamp.to_dict(), indent=2, sort_keys=True) + "\n")
+    return stamp
+
+
+def read_run_stamp(run_cache_dir: Union[str, Path]) -> Optional[RunStamp]:
+    """Read ``run_identity.json`` from a run directory.
+
+    Args:
+        run_cache_dir: The run directory to read.
+
+    Returns:
+        Optional[RunStamp]: The stamp, or None if it is absent or unusable.
+    """
+    path = Path(run_cache_dir) / RUN_IDENTITY_FILENAME
+    try:
+        with open(path, "r") as f:
+            data = json.load(f)
+        return RunStamp.from_dict(data)
+    except Exception as e:
+        logger.debug(f"Could not read run identity stamp at {path}: {e}")
+        return None
+
+
+def _mismatched_components(stamp: RunStamp, identity: RunIdentity) -> tuple[str, ...]:
+    """Return the sorted names of the components a stamp and an identity disagree on."""
+    if not stamp.components:
+        return ("run_hash",)
+    missing = object()
+    keys = set(stamp.components) | set(identity.components)
+    differing = tuple(sorted(key for key in keys if stamp.components.get(key, missing) != identity.components.get(key, missing)))
+    return differing or ("run_hash",)
+
+
+def reconcile_run_directory(run_cache_dir: Union[str, Path], identity: RunIdentity, *, now: str) -> RunDirectoryCheck:
+    """Decide what a run may do with the directory it is about to use.
+
+    A missing or empty directory is created, a directory with no stamp (a cache
+    from before run identities existed) is adopted as-is, a stamp from an older
+    identity version is upgraded in place, and a matching stamp only has its
+    ``updated_at`` refreshed. Nothing is ever deleted.
+
+    Args:
+        run_cache_dir: The run directory.
+        identity: The identity of the run that wants the directory.
+        now: The timestamp of this run.
+
+    Returns:
+        RunDirectoryCheck: What happened, the stamp now on disk, and the version it replaced.
+
+    Raises:
+        RunIdentityMismatch: If the directory belongs to a different run, or was
+            written by a newer version of curator.
+    """
+    path = Path(run_cache_dir)
+    entries = os.listdir(path) if path.is_dir() else []
+
+    if not entries:
+        return RunDirectoryCheck(status="created", stamp=write_run_stamp(path, identity, now=now), previous_version=None)
+
+    stamp = read_run_stamp(path)
+    if stamp is None:
+        return RunDirectoryCheck(status="adopted", stamp=write_run_stamp(path, identity, now=now), previous_version=None)
+
+    if stamp.identity_version < RUN_IDENTITY_VERSION:
+        new_stamp = write_run_stamp(path, identity, now=now, created_at=stamp.created_at)
+        return RunDirectoryCheck(status="upgraded", stamp=new_stamp, previous_version=stamp.identity_version)
+
+    if stamp.identity_version > RUN_IDENTITY_VERSION:
+        raise RunIdentityMismatch(str(path), identity.run_hash, stamp.run_hash, ("identity_version",))
+
+    if stamp.run_hash != identity.run_hash or stamp.components != identity.components:
+        raise RunIdentityMismatch(str(path), identity.run_hash, stamp.run_hash, _mismatched_components(stamp, identity))
+
+    new_stamp = write_run_stamp(path, identity, now=now, created_at=stamp.created_at)
+    return RunDirectoryCheck(status="matched", stamp=new_stamp, previous_version=stamp.identity_version)
diff --git a/src/bespokelabs/curator/types/curator_response.py b/src/bespokelabs/curator/types/curator_response.py
index 2d219ae..5b33511 100644
--- a/src/bespokelabs/curator/types/curator_response.py
+++ b/src/bespokelabs/curator/types/curator_response.py
@@ -9,6 +9,7 @@ from datasets import Dataset
 from pydantic import BaseModel
 
 from bespokelabs.curator.log import logger
+from bespokelabs.curator.run_identity import CachedResponseMismatch
 from bespokelabs.curator.status_tracker.offline_status_tracker import OfflineStatusTracker
 
 
@@ -144,6 +145,9 @@ class CuratorResponse:
     # Additional metadata
     metadata: Dict[str, Any] = field(default_factory=dict)
 
+    # Identity of the run that produced this response, as written to run_identity.json
+    run_identity: Optional[Dict[str, Any]] = None
+
     def __post_init__(self):
         """Post-initialization hook."""
         if self.metadata is None:
@@ -292,6 +296,7 @@ class CuratorResponse:
                 "max_concurrent_requests": self.performance_stats.max_concurrent_requests,
             },
             "metadata": self.metadata,
+            "run_identity": self.run_identity,
         }
 
     def save(self, cache_dir: Union[str, Path]) -> None:
@@ -311,19 +316,24 @@ class CuratorResponse:
             json.dump(self.to_dict(), f, indent=2)
 
     @classmethod
-    def load(cls, cache_dir: Union[str, Path], dataset: Dataset) -> "CuratorResponse":
+    def load(cls, cache_dir: Union[str, Path], dataset: Dataset, *, verify: bool = True) -> "CuratorResponse":
         """Load a response from a cache directory.
 
         This class method creates a new CuratorResponse instance from saved
         data in the cache directory. It requires a dataset to be provided
-        as the dataset itself is not cached.
+        as the dataset itself is not cached, and by default checks that the
+        dataset it is given is the one the cached statistics describe.
 
         Args:
             cache_dir (Union[str, Path]): Directory containing the cached response data.
             dataset (Dataset): The dataset to use for the response.
+            verify (bool): Whether to check the dataset against the recorded one.
 
         Returns:
             CuratorResponse: A new CuratorResponse instance loaded from cache.
+
+        Raises:
+            CachedResponseMismatch: If the cached response describes a different dataset.
         """
         cache_dir = Path(cache_dir)
 
@@ -331,6 +341,18 @@ class CuratorResponse:
         with open(cache_dir / "response.json", "r") as f:
             data = json.load(f)
 
+        # Responses written before run identities have no dataset record to check against.
+        if verify and data.get("dataset") is not None:
+            recorded = data["dataset"]
+            found = {
+                "fingerprint": dataset._fingerprint,
+                "size": len(dataset),
+                "columns": list(dataset.column_names),
+            }
+            for name in ("fingerprint", "size", "columns"):
+                if recorded.get(name) != found[name]:
+                    raise CachedResponseMismatch(str(cache_dir), name, recorded.get(name), found[name])
+
         # Create response object
         response = cls(
             dataset=dataset,
@@ -343,6 +365,7 @@ class CuratorResponse:
             request_stats=RequestStats(**data["request_stats"]),
             performance_stats=PerformanceStats(**data["performance_stats"]),
             metadata=data["metadata"],
+            run_identity=data.get("run_identity"),
         )
 
         return response
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
