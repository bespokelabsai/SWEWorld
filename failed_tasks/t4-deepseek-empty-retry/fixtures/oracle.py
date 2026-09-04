#!/usr/bin/env python3
"""Reference implementation of t4 — retrying DeepSeek's empty completions.

    python3 t4_oracle.py <checkout>

One edit, in one place: the response-handling path of the openai-compatible
backend, immediately after the reply arrives and before it is parsed. That is
where the requirement says the special case belongs, and putting it there means
the existing retry/backoff machinery carries it — `handle_single_request_with_retries`
already re-queues on any exception raised here.

Detection reads `self.url`, which curator resolves from config.base_url, then
OPENAI_BASE_URL, then the default. Nothing is added to the public surface: no
`backend_params` key, no constructor argument.
"""
from __future__ import annotations

import pathlib
import sys

ONLINE_REL = "src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py"

CHECK = '''
        # t4: an empty completion from DeepSeek is a retryable failure, not an
        # answer. DeepSeek intermittently returns nothing under load; the row
        # must go back through the normal retry path rather than reaching
        # parse(), and after max_retries it must fail with an error that says
        # so — a generic timeout leaves the user believing the network is slow
        # when the provider is returning empty strings.
        #
        # Scoped by the RESOLVED url, so no caller has to pass a flag, and
        # deliberately not applied to other openai-compatible endpoints, which
        # may legitimately return an empty string as valid content.
        if "api.deepseek.com" in self.url:
            _choices = (response or {}).get("choices") or []
            _content = ""
            if _choices:
                _content = (_choices[0].get("message") or {}).get("content") or ""
            if not str(_content).strip():
                status_tracker.num_other_errors += 1
                raise Exception(
                    "DeepSeek returned an empty completion. DeepSeek "
                    "intermittently returns empty responses while its API is "
                    "under load; curator re-queues them through its normal "
                    "retry path and fails the row once the max_retries "
                    "empty-response retries are exhausted.")

'''


def main(root: str) -> int:
    path = pathlib.Path(root) / ONLINE_REL
    if not path.exists():
        raise SystemExit(f"no {ONLINE_REL} under {root}")
    body = path.read_text()
    if "DeepSeek returned an empty completion" in body:
        print("  = t4 (already applied)")
        return 0

    anchor = '        if response is None:\n            raise Exception("Response is empty")'
    if anchor not in body:
        raise SystemExit("could not find the response-handling anchor")
    path.write_text(body.replace(anchor, CHECK.lstrip("\n") + anchor, 1))
    print("  + t4.r1/r2: empty DeepSeek completions are retried, by resolved url")
    print("t4 oracle applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
