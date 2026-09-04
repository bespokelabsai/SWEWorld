#!/usr/bin/env python3
"""Reference implementation of t2 — the batch cost pre-flight.

    python2 t2_oracle.py <checkout>

The estimate is printed at the top of `requests_to_responses`, before
`submit_batches_from_request_files` uploads anything, which is what "before any
requests are submitted to the provider" means. It is computed from the request
files curator has already built, sampled above a threshold, and it declares
which of the two it did.

The discount is provider-specific and lives in the ESTIMATOR. It deliberately
does not touch `cost_processor_factory`, the post-hoc billing seam — the
requirement's own scope says this "does not change actual billing", and a
grader that checked the billing seam instead once failed an implementation
whose code contained `assert batch_discount("litellm") == 1.0`.
"""
from __future__ import annotations

import pathlib
import sys

BATCH_REL = "src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py"

ESTIMATOR = '''

# How many rows the estimate reads before it stops and extrapolates. Above this
# the pre-flight is a sample; at or below it, every row is used.
_ESTIMATE_SAMPLE_SIZE = 500


def batch_discount(backend: str) -> float:
    """The batch discount for a provider, as a multiplier on standard pricing.

    OpenAI and Anthropic bill batch work at half the per-token rate. Anything
    routed through litellm does not get a distinct batch tier in this codebase,
    so it is estimated at the standard rate — quoting it at half would tell a
    user a batch run is cheaper than it will actually be.
    """
    return 0.5 if str(backend).lower() in ("openai", "anthropic") else 1.0


def estimate_batch_cost(request_files, cost_processor, backend, model):
    """(dollars, rows counted, rows in total, sampled?) for a batch job.

    Reads the request files curator has already written rather than walking the
    dataset again, and stops after _ESTIMATE_SAMPLE_SIZE rows: iterating a
    multi-million row dataset to print an estimate makes the pre-flight its own
    run, which is the thing it exists to avoid.
    """
    import json as _json

    total = 0
    counted = 0
    tokens_in = 0
    for path in request_files:
        try:
            with open(path) as handle:
                for line in handle:
                    total += 1
                    if counted >= _ESTIMATE_SAMPLE_SIZE:
                        continue
                    try:
                        request = _json.loads(line)
                    except ValueError:
                        # A row that will not parse is skipped, never fatal:
                        # the estimate is advisory and must not be able to
                        # break a run that would otherwise have worked.
                        continue
                    messages = request.get("messages") or []
                    tokens_in += max(1, len(str(messages)) // 4)
                    counted += 1
        except OSError:
            continue

    if counted == 0:
        return 0.0, 0, total, False
    per_row = tokens_in / counted
    in_cost = getattr(cost_processor.config, "in_mtok_cost", None) or 0.0
    dollars = (per_row * total * in_cost / 1e6) * batch_discount(backend)
    return dollars, counted, total, counted < total

'''

PREFLIGHT = '''        self._print_cost_preflight(generic_request_files)
        run_in_event_loop(self.submit_batches_from_request_files(generic_request_files))'''

METHOD = '''
    def _print_cost_preflight(self, generic_request_files) -> None:
        """Print what this batch job will cost, before anything is submitted."""
        try:
            dollars, counted, total, sampled = estimate_batch_cost(
                generic_request_files, self._cost_processor,
                getattr(self.config, "backend", None) or self.backend,
                self.config.model)
        except Exception as exc:                # noqa: BLE001
            logger.warning(f"could not estimate the batch cost: {exc}")
            return
        how = (f"sampled the first {counted} of {total} rows" if sampled
               else f"computed from a full pass over all {total} rows")
        logger.info(f"Estimated batch cost: ${dollars:.4f} for {total} "
                    f"requests ({how}; "
                    f"{int(batch_discount(getattr(self.config, 'backend', None) or self.backend) * 100)}% "
                    "of standard per-token pricing applied).")
'''


def main(root: str) -> int:
    path = pathlib.Path(root) / BATCH_REL
    if not path.exists():
        raise SystemExit(f"no {BATCH_REL} under {root}")
    body = path.read_text()

    if "def estimate_batch_cost" not in body:
        idx = body.index("class BaseBatchRequestProcessor")
        body = body[:idx] + ESTIMATOR.lstrip("\n") + body[idx:]
        print("  + estimator and batch_discount")

    if "_print_cost_preflight" not in body:
        body = body.replace(
            "        run_in_event_loop(self.submit_batches_from_request_files(generic_request_files))",
            PREFLIGHT, 1)
        idx = body.index("    def requests_to_responses(")
        body = body[:idx] + METHOD.lstrip("\n") + "\n" + body[idx:]
        print("  + the pre-flight, before submission")

    path.write_text(body)
    print("t2 oracle applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
