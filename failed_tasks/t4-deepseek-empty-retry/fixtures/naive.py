#!/usr/bin/env python3
"""The NAIVE build of t4 — retry every empty completion, everywhere.

    python3 t4_naive.py <checkout>

The obvious reading: empty completions are junk, so retry them. It does not
scope the behaviour to DeepSeek, and its error says nothing about which
provider or why — both of which are things nobody wrote down.

Retrying every empty completion looks like a strict improvement, which is
exactly why it is the naive build: an agent has no reason from the code alone
to think other openai-compatible endpoints may return an empty string as valid
content.
"""
from __future__ import annotations

import pathlib
import sys

ONLINE_REL = "src/bespokelabs/curator/request_processor/online/openai_online_request_processor.py"

CHECK = '''
        # Empty completions are junk; retry them.
        _choices = (response or {}).get("choices") or []
        if _choices:
            _content = (_choices[0].get("message") or {}).get("content") or ""
            if not str(_content).strip():
                status_tracker.num_other_errors += 1
                raise Exception("Empty response received; retrying.")

'''


def main(root: str) -> int:
    path = pathlib.Path(root) / ONLINE_REL
    body = path.read_text()
    if "Empty response received" in body:
        print("  = t4 naive (already applied)")
        return 0
    anchor = '        if response is None:\n            raise Exception("Response is empty")'
    path.write_text(body.replace(anchor, CHECK.lstrip("\n") + anchor, 1))
    print("t4 naive build applied: every empty completion retried, no scoping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
