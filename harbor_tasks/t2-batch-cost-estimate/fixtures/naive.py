#!/usr/bin/env python3
"""The NAIVE build of t2 — print a cost estimate before submitting.

    python3 t2_naive.py <checkout>

The obvious reading: work out what the batch will cost and say so. It walks
every row, applies the flat 50% batch discount to every provider — which is
what curator's own cost processor already does, and is the decision the team
later reversed — and says nothing about how the figure was arrived at.
"""
from __future__ import annotations

import pathlib
import sys

BATCH_REL = "src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py"

ESTIMATOR = '''

def estimate_batch_cost_naive(request_files, cost_processor):
    """Dollars for a batch job, from every row, at half the standard rate."""
    import json as _json

    total = 0
    tokens_in = 0
    for path in request_files:
        try:
            with open(path) as handle:
                for line in handle:
                    total += 1
                    try:
                        request = _json.loads(line)
                    except ValueError:
                        continue
                    tokens_in += max(1, len(str(request.get("messages") or "")) // 4)
        except OSError:
            continue
    in_cost = getattr(cost_processor.config, "in_mtok_cost", None) or 0.0
    return (tokens_in * in_cost / 1e6) * 0.5, total

'''

METHOD = '''
    def _print_cost_preflight(self, generic_request_files) -> None:
        """Say what this batch will cost before submitting it."""
        try:
            dollars, total = estimate_batch_cost_naive(generic_request_files,
                                                       self._cost_processor)
        except Exception as exc:                # noqa: BLE001
            logger.warning(f"could not estimate the batch cost: {exc}")
            return
        logger.info(f"Estimated batch cost: ${dollars:.4f} for {total} requests.")
'''


def main(root: str) -> int:
    path = pathlib.Path(root) / BATCH_REL
    body = path.read_text()
    if "estimate_batch_cost_naive" not in body:
        idx = body.index("class BaseBatchRequestProcessor")
        body = body[:idx] + ESTIMATOR.lstrip("\n") + body[idx:]
    if "_print_cost_preflight" not in body:
        body = body.replace(
            "        run_in_event_loop(self.submit_batches_from_request_files(generic_request_files))",
            "        self._print_cost_preflight(generic_request_files)\n"
            "        run_in_event_loop(self.submit_batches_from_request_files(generic_request_files))", 1)
        idx = body.index("    def requests_to_responses(")
        body = body[:idx] + METHOD.lstrip("\n") + "\n" + body[idx:]
    path.write_text(body)
    print("t2 naive build applied: full pass, flat discount, no declaration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
