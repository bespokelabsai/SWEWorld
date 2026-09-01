#!/usr/bin/env python3
"""Reference implementation of t1, applied to a curator checkout.

Written as a patch script rather than a diff so it can be run against any
checkout an agent might have pushed, and so each edit sits next to the fact it
satisfies.

    python3 t1_oracle.py <checkout>

This is the ORACLE half of the bracket: if the grading suite cannot be passed by
a correct implementation, the suite is wrong and no agent result from it means
anything. That gap is exactly how a run reporting "the agent recovered 2 of 9
hidden facts" turned out to include five tests no implementation could pass.
"""
from __future__ import annotations

import pathlib
import sys

LLM_REL = "src/bespokelabs/curator/llm/llm.py"


def patch(path: pathlib.Path, old: str, new: str, what: str,
          marker: str | None = None) -> None:
    """Apply one edit, idempotently.

    `marker` is a string unique to the NEW text. Defaulting to its first line
    is wrong whenever an edit keeps its anchor: the `_last_run` patch begins
    with a line that is already in the file, so it reported "already applied"
    and silently did nothing, and cache_stats() then had no record to read.
    """
    body = path.read_text()
    if (marker or new.strip().split("\n")[0]) in body:
        print(f"  = {what} (already applied)")
        return
    if old not in body:
        raise SystemExit(f"could not apply {what}: anchor not found in {path}")
    path.write_text(body.replace(old, new, 1))
    print(f"  + {what}")


def main(root: str) -> int:
    llm = pathlib.Path(root) / LLM_REL
    if not llm.exists():
        raise SystemExit(f"no {LLM_REL} under {root}")
    print(f"patching {llm}")

    # -- r1.failure_behavior ------------------------------------------------
    # An unhashable response_format is a guaranteed MISS, never a raise. A
    # schema carrying an arbitrary type has no JSON representation at all, so
    # model_json_schema() throws; falling back to fresh randomness makes the
    # fingerprint unique per run, which is what "guaranteed miss" means.
    patch(llm,
          '                    str(self.prompt_formatter.response_format.model_json_schema() if self.prompt_formatter.response_format else "text"),',
          '                    str(_schema_key(self.prompt_formatter.response_format)),',
          "r1.failure_behavior: unhashable response_format degrades to a miss")

    # The same schema serialisation happens again when the run's metadata is
    # built (llm.py:259) and once more in the prompt formatter. Patching only
    # the fingerprint left the raise in place two call sites later, which is
    # what the oracle caught: "guaranteed miss" has to hold everywhere the
    # schema is touched, not just where the key is computed.
    patch(llm,
          '            "response_format": (str(self.prompt_formatter.response_format.model_json_schema()) if self.prompt_formatter.response_format else "text"),',
          '            "response_format": str(_schema_key(self.prompt_formatter.response_format)),',
          "r1.failure_behavior: the metadata call site too")

    # -- r1.rule ------------------------------------------------------------
    # The key comes from the RENDERED PROMPTS, not the dataset fingerprint.
    # Two rows that render identically are one entry; a column prompt() never
    # reads cannot change the key.
    patch(llm,
          "        dataset_hash = dataset._fingerprint if dataset is not None else xxh64(\"\").hexdigest()",
          "        dataset_hash = self._prompt_level_hash(dataset)",
          "r1.rule: key derived from rendered prompts")

    # -- the helpers, and cache_stats --------------------------------------
    helpers = '''

def _schema_key(response_format):
    """A stable key for a response_format, or fresh randomness if it has none.

    r1.failure_behavior: a dynamically built model whose schema cannot be
    serialised must be treated as a guaranteed cache miss rather than raising.
    """
    if response_format is None:
        return "text"
    try:
        return response_format.model_json_schema()
    except Exception:                       # noqa: BLE001 - any schema failure
        return "unhashable-" + os.urandom(8).hex()


'''
    body = llm.read_text()
    if "_schema_key" not in body.split("class LLM")[0]:
        marker = "class LLM"
        idx = body.index(marker)
        llm.write_text(body[:idx] + helpers.lstrip("\n") + body[idx:])
        print("  + _schema_key helper")

    methods = '''
    def _prompt_level_hash(self, dataset) -> str:
        """Hash the rendered prompts, not the rows that produced them.

        r1.rule and r1.exclusions. Two rows that render to the same prompt
        contribute one entry, so a dataset differing only in a column prompt()
        never reads resolves to the same key — and within one dataset the pair
        counts once.
        """
        if dataset is None:
            return xxh64("").hexdigest()
        rendered = []
        for idx, row in enumerate(dataset):
            try:
                request = self.prompt_formatter.create_generic_request(row, idx)
                rendered.append(str(request.messages))
            except Exception:               # noqa: BLE001 - unrenderable row
                rendered.append(f"<unrenderable-{idx}>")
        unique = sorted(set(rendered))
        self._prompt_count = len(rendered)
        self._unique_prompt_count = len(unique)
        return xxh64("|".join(unique).encode("utf-8")).hexdigest()

    def cache_stats(self):
        """How much of the last run came from the cache.

        r1.observability and all of r2. Resolves CURATOR_CACHE_DIR at CALL
        time, reads only, and reports zeros when the directory does not exist
        rather than raising.
        """
        resolved = os.environ.get("CURATOR_CACHE_DIR",
                                  os.path.expanduser(_CURATOR_DEFAULT_CACHE_DIR))
        last = getattr(self, "_last_run", None)
        if last is None or not os.path.isdir(resolved) \\
                or not str(last.get("run_dir", "")).startswith(resolved):
            return CacheStats(total=0, misses=0, hit_rate=0.0,
                              cache_dir=resolved)
        total = int(last["total"])
        misses = int(last["misses"])
        hit_rate = 0.0 if total == 0 else float(total - misses) / float(total)
        return CacheStats(total=total, misses=misses, hit_rate=hit_rate,
                          cache_dir=resolved)
'''
    body = llm.read_text()
    if "def cache_stats" not in body:
        anchor = "    def _hash_fingerprint("
        idx = body.index(anchor)
        llm.write_text(body[:idx] + methods.lstrip("\n") + "\n" + body[idx:])
        print("  + _prompt_level_hash and cache_stats")

    # -- the record cache_stats reads --------------------------------------
    patch(llm,
          "        run_cache_dir = os.path.join(curator_cache_dir, fingerprint)\n        os.makedirs(run_cache_dir, exist_ok=True)",
          '''        run_cache_dir = os.path.join(curator_cache_dir, fingerprint)
        _already_cached = os.path.isdir(run_cache_dir) and any(
            name.startswith("responses") for name in os.listdir(run_cache_dir))
        os.makedirs(run_cache_dir, exist_ok=True)
        # What cache_stats() reports. `misses` is the number of DISTINCT
        # rendered prompts this run had to send; a run served entirely from the
        # cache sends none.
        self._last_run = {
            "run_dir": run_cache_dir,
            "total": getattr(self, "_prompt_count", 0),
            "misses": 0 if _already_cached
                      else getattr(self, "_unique_prompt_count", 0),
        }''',
          "r1.observability / r2: record what the run did",
          marker="self._last_run = {")

    # -- r1.exclusions ------------------------------------------------------
    # Two rows rendering to one prompt are ONE request. Collapse the dataset to
    # its distinct prompts before the processor sees it, then fan the answers
    # back out so the caller still gets a row per input row — de-duplicating
    # the request must not drop the output.
    patch(llm,
          """        parse_func_hash = _get_function_hash(self.prompt_formatter.parse_func)
        dataset = self._request_processor.run(""",
          """        parse_func_hash = _get_function_hash(self.prompt_formatter.parse_func)
        _dedup_map = self._collapse_duplicate_prompts(dataset)
        if _dedup_map is not None:
            _kept = sorted(set(_dedup_map))
            dataset = dataset.select(_kept)
        dataset = self._request_processor.run(""",
          "r1.exclusions: collapse duplicate prompts before sending",
          marker="_dedup_map = self._collapse_duplicate_prompts")

    # ...and fan the answers back out, so de-duplicating the request does not
    # drop the caller's rows.
    patch(llm,
          "        viewer_url = self._request_processor.viewer_client.curator_viewer_url",
          """        if _dedup_map is not None and dataset is not None:
            _slot = {original: position
                     for position, original in enumerate(_kept)}
            dataset = dataset.select([_slot[first] for first in _dedup_map])
        viewer_url = self._request_processor.viewer_client.curator_viewer_url""",
          "r1.exclusions: expand the answers back to one row per input row",
          marker="_slot = {original: position")

    collapse = '''
    def _collapse_duplicate_prompts(self, dataset):
        """Row index -> the index of the first row rendering the same prompt.

        None when every prompt is distinct, so the ordinary path is untouched.
        """
        if dataset is None:
            return None
        first_for: dict = {}
        mapping = []
        for idx, row in enumerate(dataset):
            try:
                key = str(self.prompt_formatter.create_generic_request(row, idx).messages)
            except Exception:               # noqa: BLE001
                key = f"<unrenderable-{idx}>"
            mapping.append(first_for.setdefault(key, idx))
        return None if len(set(mapping)) == len(mapping) else mapping

'''
    body = llm.read_text()
    if "_collapse_duplicate_prompts" not in body.split("def _prompt_level_hash")[0]:
        idx = body.index("    def _prompt_level_hash")
        llm.write_text(body[:idx] + collapse.lstrip("\n") + body[idx:])
        print("  + _collapse_duplicate_prompts")

    # -- the returned object ------------------------------------------------
    stats_class = '''

class CacheStats:
    """What `cache_stats()` returns.

    A small object rather than a dict so `hit_rate` and `misses` are attributes
    as well as keys; the requirement names both but fixes no container.
    """

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
    body = llm.read_text()
    if "class CacheStats" not in body:
        idx = body.index("class LLM")
        llm.write_text(body[:idx] + stats_class.lstrip("\n") + body[idx:])
        print("  + CacheStats")

    # The third and last schema call site, inside create_generic_request.
    # Three sites for one fact: the fingerprint, the run metadata, and the
    # request builder. An implementation that patches fewer still raises, which
    # is precisely what the oracle surfaced twice in a row here.
    fmt = pathlib.Path(root) / "src/bespokelabs/curator/llm/prompt_formatter.py"
    if fmt.exists():
        body = fmt.read_text()
        if "_safe_schema" not in body:
            body = body.replace(
                "            response_format=(self.response_format.model_json_schema() if self.response_format else None),",
                "            response_format=_safe_schema(self.response_format),")
            body = body.replace(
                "import json",
                "import json\n\n\ndef _safe_schema(response_format):\n"
                '    """The schema, or None when it cannot be built.\n\n'
                "    A response_format whose schema raises must degrade to a\n"
                "    request without one — a guaranteed miss — rather than taking\n"
                '    the run down."""\n'
                "    if response_format is None:\n"
                "        return None\n"
                "    try:\n"
                "        return response_format.model_json_schema()\n"
                "    except Exception:  # noqa: BLE001\n"
                "        return None\n", 1)
            fmt.write_text(body)
            print("  + r1.failure_behavior: the request-builder call site")

    # r1.failure_behavior, properly. Nulling the schema only in the request
    # leaves the parser validating against the model, so the row fails
    # permanently — the request and the parse have to agree. Dropping the
    # response_format wholesale serves the row as plain text; remembering that
    # it was dropped keeps the KEY unique, because a forgotten schema makes the
    # fingerprint stable again and the second run becomes a cache HIT, which is
    # the opposite of the guaranteed miss the requirement asks for.
    if fmt.exists():
        body = fmt.read_text()
        if "_drop_if_unserialisable" not in body:
            body = body.replace(
                "def _safe_schema(response_format):",
                "def _drop_if_unserialisable(formatter):\n"
                '    """Forget a response_format whose schema cannot be built."""\n'
                "    fmt = getattr(formatter, \"response_format\", None)\n"
                "    if fmt is None:\n"
                "        return\n"
                "    try:\n"
                "        fmt.model_json_schema()\n"
                "    except Exception:  # noqa: BLE001\n"
                "        formatter.response_format = None\n"
                "        formatter._schema_unserialisable = True\n"
                "\n\n"
                "def _safe_schema(response_format):", 1)
            fmt.write_text(body)
            print("  + r1.failure_behavior: drop the schema for the whole run")

    body = llm.read_text()
    if "_drop_if_unserialisable(self.prompt_formatter)" not in body:
        body = body.replace(
            "        dataset_hash = self._prompt_level_hash(dataset)",
            "        from bespokelabs.curator.llm.prompt_formatter import "
            "_drop_if_unserialisable\n"
            "        _drop_if_unserialisable(self.prompt_formatter)\n"
            "        dataset_hash = self._prompt_level_hash(dataset)", 1)
        body = body.replace(
            "                    str(_schema_key(self.prompt_formatter.response_format)),",
            "                    str(\"unhashable-\" + os.urandom(8).hex()\n"
            "                        if getattr(self.prompt_formatter, "
            "\"_schema_unserialisable\", False)\n"
            "                        else _schema_key(self.prompt_formatter.response_format)),", 1)
        llm.write_text(body)
        print("  + r1.failure_behavior: keep the key unique")

    print("t1 oracle applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
