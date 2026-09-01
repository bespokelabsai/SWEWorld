#!/usr/bin/env python3
"""The ORACLE build of t23 — the ticket plus both hidden requirements.

    python3 oracle.py <checkout>

Two changes to `base_batch_request_processor.py`:

**r1.failure_behavior** — `update_batch_objects_file` is awaited immediately
after `mark_as_submitted`, and baseline lets an OSError from it take the whole
submission down. Losing resumability is preferable to losing the job, so the
write is guarded and the failure is logged rather than raised.

**r2** — `_attempt_loading_batch_status_tracker` loads a persisted tracker and
then assigns `self.tracker.model = self.prompt_formatter.model_name`, which
overwrites the very field a resume ought to be checking. The oracle compares
first, and on a mismatch starts fresh with a logged reason.
"""
from __future__ import annotations

import pathlib
import sys

REL = "src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py"

GUARD_OLD = """        async with self._batch_objects_file_lock:"""
GUARD_NEW = '''        try:
            await self._write_batch_objects_file()
        except OSError as exc:
            # r1.failure_behavior: a full disk or a read-only mount costs the
            # ability to resume, which is worth strictly less than the job.
            logger.warning(
                f"Could not persist batch status to {self.batch_objects_file}: "
                f"{exc}. The job will run, but a restart will not be able to "
                "resume it.")

    async def _write_batch_objects_file(self):
        async with self._batch_objects_file_lock:'''

VALIDATE = '''        if os.path.exists(self.batch_objects_file):
            _loaded = None
            try:
                with open(self.batch_objects_file, "r") as f:
                    _loaded = BatchStatusTracker.model_validate_json(f.read())
            except (OSError, ValueError) as exc:
                logger.warning(
                    f"Could not read {self.batch_objects_file}: {exc}. "
                    "Submitting a fresh batch.")
            # r2.rule: the persisted job has to belong to THIS run. Baseline
            # assigned the current model over the loaded one a few lines below,
            # which quietly adopted a stale job instead of noticing it.
            _why = None
            if _loaded is not None:
                _want_model = self.prompt_formatter.model_name
                _want_provider = self.compatible_provider
                if _loaded.model and _loaded.model != _want_model:
                    _why = (f"it was submitted for model {_loaded.model!r}, "
                            f"this run is {_want_model!r}")
                elif (getattr(_loaded, "compatible_provider", None)
                      and _loaded.compatible_provider != _want_provider):
                    _why = (f"it was submitted to provider "
                            f"{_loaded.compatible_provider!r}, this run is "
                            f"{_want_provider!r}")
                elif (_loaded.n_total_requests
                      and _loaded.n_total_requests != self.total_requests):
                    _why = (f"it covers {_loaded.n_total_requests} request(s), "
                            f"this run has {self.total_requests}")
            if _loaded is not None and _why is None:
                self.tracker = _loaded
                self.tracker.viewer_client = self._viewer_client
                logger.info(f"Loaded existing tracker from {self.batch_objects_file}")
            else:
                if _why is not None:
                    # r2.failure_behavior: say why, rather than resuming
                    # something incompatible or silently starting over.
                    logger.warning(
                        f"Not resuming the batch job in {self.batch_objects_file}: "
                        f"{_why}. Submitting a fresh batch instead.")
                self.tracker = BatchStatusTracker(
                    unsubmitted_request_files=set(request_files),
                    viewer_client=self._viewer_client,
                    compatible_provider=self.compatible_provider,
                    model=self.prompt_formatter.model_name,
                    n_total_requests=self.total_requests,
                    completion_window=self.config.completion_window,
                )
        else:'''


def main(root: str) -> int:
    path = pathlib.Path(root) / REL
    src = path.read_text()
    if "_write_batch_objects_file" in src:
        print("  = already applied")
        return 0

    if GUARD_OLD not in src:
        print("  ! persistence anchor not found", file=sys.stderr)
        return 1
    src = src.replace(GUARD_OLD, GUARD_NEW, 1)

    old_load = '''        if os.path.exists(self.batch_objects_file):
            with open(self.batch_objects_file, "r") as f:
                self.tracker = BatchStatusTracker.model_validate_json(f.read())
                self.tracker.viewer_client = self._viewer_client  # Note that viewer_client is not serialized
            logger.info(f"Loaded existing tracker from {self.batch_objects_file}")
        else:'''
    if old_load not in src:
        print("  ! resume anchor not found", file=sys.stderr)
        return 1
    src = src.replace(old_load, VALIDATE, 1)

    # Baseline reassigns the model right after loading, which would undo the
    # comparison above on the next run.
    src = src.replace("        self.tracker.model = self.prompt_formatter.model_name\n",
                      "", 1)
    path.write_text(src)
    print("  + t23.r1: persistence failure warns instead of killing the job")
    print("  + t23.r2: a persisted job is validated before it is resumed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
