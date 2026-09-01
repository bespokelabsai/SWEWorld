#!/usr/bin/env python3
"""The NAIVE build of t12 — the ticket implemented the obvious way.

    python3 naive.py <checkout>

Validates the response_format at construction, as the ticket asks, and stops
there: the verdict comes from a hand-written set of model families, which is
what an engineer writes when nobody has told them a maintained list already
exists. That is the negative control for r2 — a private copy agrees with
litellm today and drifts the first time a model is added.

It should PASS the open feature and r1.failure_behavior (it does raise
ValueError at construction) and FAIL r1.rule and r2.rule, which flip the
maintained list and watch whether the verdict follows.
"""
from __future__ import annotations

import pathlib
import sys

LLM_REL = "src/bespokelabs/curator/llm/llm.py"

CHECK = '''
    # Models known to accept a json schema. Written out here because it is the
    # obvious thing to do; the point of the control is that it cannot follow
    # the list curator already maintains.
    _STRUCTURED_OK = ("gpt-4o", "gpt-4.1", "gpt-5", "o1", "o3", "o4",
                      "claude-3", "claude-4", "gemini-1.5", "gemini-2")

    def _validate_response_format_support(self) -> None:
        if getattr(self, "response_format", None) is None:
            return
        name = str(getattr(self, "model_name", "") or "").lower()
        if not name:
            return
        params = getattr(self, "_backend_params", None) or {}
        if params.get("base_url"):
            return
        if not any(name.startswith(p) for p in self._STRUCTURED_OK):
            raise ValueError(
                f"Model {name} does not support structured output, but a "
                "response_format was given.")
'''


def main(root: str) -> int:
    path = pathlib.Path(root) / LLM_REL
    src = path.read_text()
    if "_validate_response_format_support" in src:
        print("  = already applied")
        return 0
    anchor = "        self.prompt_formatter = PromptFormatter("
    if anchor not in src:
        print(f"  ! anchor not found in {LLM_REL}", file=sys.stderr)
        return 1
    src = src.replace(anchor,
                      "        self._backend_params = backend_params or {}\n"
                      + anchor, 1)
    tail = "\n    def _hash_fingerprint("
    src = src.replace(tail, "\n        self._validate_response_format_support()\n"
                      + CHECK + tail, 1)
    path.write_text(src)
    print("  + t12 naive: construction-time check against a hand-written list")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
