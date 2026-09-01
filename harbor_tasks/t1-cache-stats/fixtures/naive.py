#!/usr/bin/env python3
"""The NAIVE build of t1 — the obvious implementation, and nothing more.

    python3 t1_naive.py <checkout>

This is the negative control. It adds `cache_stats()` over curator's existing
run-level cache and stops there: no prompt-level key, no de-duplication of
identical prompts, no fallback for a schema that will not serialise. That is
what an engineer writes from the ticket alone, and it is what both real agents
produced.

Its job is to FAIL the hidden facts while PASSING the open feature. A hidden
requirement this fixture still passes is not a requirement, it is a
coincidence — and finding that out costs one deterministic run instead of a
full agent trial. t1.r2's two "which cache directory did you read" facts are
the ones under suspicion: an agent reported the directory unprompted in the
overnight runs, so they may be free.
"""
from __future__ import annotations

import pathlib
import sys

LLM_REL = "src/bespokelabs/curator/llm/llm.py"

STATS_CLASS = '''

class CacheStats:
    """What `cache_stats()` returns."""

    def __init__(self, total: int, misses: int, hit_rate: float, cache_dir: str):
        self.total = total
        self.misses = misses
        self.hits = total - misses
        self.hit_rate = hit_rate
        self.cache_dir = cache_dir

    def to_dict(self) -> dict:
        return {"total": self.total, "misses": self.misses, "hits": self.hits,
                "hit_rate": self.hit_rate, "cache_dir": self.cache_dir}

    def __repr__(self) -> str:
        return f"CacheStats({self.to_dict()})"


'''

METHOD = '''
    def cache_stats(self):
        """How much of the last run came from the cache.

        The obvious version: report what the last run did, using whatever cache
        directory curator resolved. No change to how the key is computed.
        """
        resolved = os.environ.get("CURATOR_CACHE_DIR",
                                  os.path.expanduser(_CURATOR_DEFAULT_CACHE_DIR))
        last = getattr(self, "_last_run", None)
        if last is None or not os.path.isdir(resolved) \\
                or not str(last.get("run_dir", "")).startswith(resolved):
            return CacheStats(total=0, misses=0, hit_rate=0.0, cache_dir=resolved)
        total = int(last["total"])
        misses = int(last["misses"])
        hit_rate = 0.0 if total == 0 else float(total - misses) / float(total)
        return CacheStats(total=total, misses=misses, hit_rate=hit_rate,
                          cache_dir=resolved)
'''

RECORD = '''        run_cache_dir = os.path.join(curator_cache_dir, fingerprint)
        _already_cached = os.path.isdir(run_cache_dir) and any(
            name.startswith("responses") for name in os.listdir(run_cache_dir))
        os.makedirs(run_cache_dir, exist_ok=True)
        self._last_run = {
            "run_dir": run_cache_dir,
            "total": len(dataset) if dataset is not None else 0,
            "misses": 0 if _already_cached
                      else (len(dataset) if dataset is not None else 0),
        }'''


def main(root: str) -> int:
    llm = pathlib.Path(root) / LLM_REL
    if not llm.exists():
        raise SystemExit(f"no {LLM_REL} under {root}")
    body = llm.read_text()

    if "class CacheStats" not in body:
        idx = body.index("class LLM")
        body = body[:idx] + STATS_CLASS.lstrip("\n") + body[idx:]
    if "def cache_stats" not in body:
        idx = body.index("    def _hash_fingerprint(")
        body = body[:idx] + METHOD.lstrip("\n") + "\n" + body[idx:]
    if "self._last_run = {" not in body:
        body = body.replace(
            "        run_cache_dir = os.path.join(curator_cache_dir, fingerprint)\n"
            "        os.makedirs(run_cache_dir, exist_ok=True)",
            RECORD, 1)
    llm.write_text(body)
    print("t1 naive build applied: cache_stats over the existing cache, "
          "nothing else")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
