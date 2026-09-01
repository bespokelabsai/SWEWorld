#!/usr/bin/env python3
"""The ORACLE build of t12 — the ticket plus both hidden requirements.

    python3 oracle.py <checkout>

Moves the structured-output compatibility check from `run()` to `LLM.__init__`,
and reaches the SAME list curator already maintains rather than a copy:
`OnlineRequestProcessorConfig` + `_factory` already know how to answer "does
this model support structured output", and litellm's `supports_response_schema`
is what answers it when no base_url is set. Consulting that import at call time
— not at module import — is what lets a test flip the verdict and see the check
follow, which is r2's whole point.
"""
from __future__ import annotations

import pathlib
import sys

LLM_REL = "src/bespokelabs/curator/llm/llm.py"

CHECK = '''
    def _validate_response_format_support(self) -> None:
        """Refuse an incompatible model + response_format at construction.

        Curator already refuses this, but only once `run()` is under way
        (`base_request_processor.py`), which is after the caller has handed
        over a dataset and, for a batch job, after money can already have been
        spent. The requirement moves it forward to __init__.

        The verdict comes from litellm's `supports_response_schema` — the list
        curator's own `check_structured_output_support` consults, and the one
        that gets updated when a model like o3 lands. Imported HERE rather than
        at module scope so the lookup is late-bound: a second, private copy of
        the list would drift the first time that list changed.
        """
        if getattr(self, "response_format", None) is None:
            return
        name = str(getattr(self, "model_name", "") or "").lower()
        if not name:
            return
        # A base_url means a private or proxied endpoint, which curator probes
        # at request time instead; there is no list to consult for it.
        params = getattr(self, "_backend_params", None) or {}
        if params.get("base_url"):
            return
        try:
            from litellm import supports_response_schema
        except Exception:                          # noqa: BLE001
            return
        try:
            ok = supports_response_schema(model=name)
        except Exception:                          # noqa: BLE001 - unknown model
            return
        if not ok:
            raise ValueError(
                f"Model {name} does not support structured output, but a "
                f"response_format was given ({getattr(self, 'response_format', None)}). "
                "Checked at construction so this fails before any API spend.")
'''


def main(root: str) -> int:
    path = pathlib.Path(root) / LLM_REL
    src = path.read_text()
    if "_validate_response_format_support" in src:
        print("  = already applied")
        return 0

    # Remember backend_params so the check can tell a proxied endpoint apart.
    anchor = "        self.prompt_formatter = PromptFormatter("
    if anchor not in src:
        print(f"  ! anchor not found in {LLM_REL}", file=sys.stderr)
        return 1
    src = src.replace(anchor,
                      "        self._backend_params = backend_params or {}\n"
                      + anchor, 1)

    # Call it at the very end of __init__, after everything it reads is set.
    # `_hash_fingerprint` is the first method after __init__ in this file —
    # __call__ comes much later, and anchoring there would have put the call
    # inside another method's body.
    tail = "\n    def _hash_fingerprint("
    if tail not in src:
        print("  ! could not find the end of __init__", file=sys.stderr)
        return 1
    src = src.replace(tail, "\n        self._validate_response_format_support()\n"
                      + CHECK + tail, 1)
    path.write_text(src)
    print("  + t12.r1: compatibility refused at __init__ with ValueError")
    print("  + t12.r2: verdict read from litellm's maintained list, late-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
