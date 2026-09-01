"""Find the agent's limiter without knowing what they called it.

Nothing in t3's ticket fixes a name. The agent chooses the class, the module and
the `backend_params` key that carries it, and a suite that guessed would fail a
correct implementation for spelling. Two facts make guessing unnecessary:

**The pristine tree is on disk at verify time.** `/opt/world-state/input/curator`
is what the world shipped, root-readable, so any config field that is not in it
is one the agent added. It is read with `ast`, never imported: two copies of
`bespokelabs` in one interpreter is a trap, and `src/bespokelabs/__init__.py` is
a regular package so only one of them can win.

**`RequestProcessorConfig` forbids extras.** `Config.extra = "forbid"` means an
unknown `backend_params` key raises, so a candidate that constructs is a
candidate that exists — the config validates the guess for us.

Only `remaining_budget` is required by name, and only because the requirement
names it.
"""
from __future__ import annotations

import ast
import pathlib

BASELINE = pathlib.Path("/opt/world-state/input/curator")
CONFIG_REL = "src/bespokelabs/curator/request_processor/config.py"

# Names an agent might reasonably pick, tried after the discovered ones. Never
# instead of them: this is a tiebreaker, not the mechanism.
HINTS = ("rate_limiter", "limiter", "shared_limiter", "rate_limit",
         "status_tracker", "shared_rate_limiter")


def _baseline_fields(class_names: tuple[str, ...]) -> set[str]:
    """Field names those classes declare in the tree the world shipped."""
    path = BASELINE / CONFIG_REL
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target,
                                                                  ast.Name):
                    found.add(stmt.target.id)
                elif isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            found.add(target.id)
    return found


def new_config_fields() -> list[str]:
    """Config fields the agent added, most-likely-looking first."""
    from bespokelabs.curator.request_processor.config import (
        OnlineRequestProcessorConfig, RequestProcessorConfig)

    live = set(OnlineRequestProcessorConfig.model_fields)
    baseline = _baseline_fields(("OnlineRequestProcessorConfig",
                                 "RequestProcessorConfig"))
    added = sorted(live - baseline) if baseline else []

    def rank(name: str) -> tuple[int, str]:
        looks_right = any(word in name for word in
                          ("limit", "budget", "tracker", "rate"))
        return (0 if looks_right else 1, name)

    ordered = sorted(added, key=rank)
    # Hints last, and only ones the live config actually accepts.
    ordered += [h for h in HINTS if h in live and h not in ordered]
    return ordered


def find_limiter(*objects, require_budget: bool = True):
    """The limiter object, however the agent named it.

    `remaining_budget` is verbatim in the requirement, so it is fair to search
    on — but ONLY when grading that requirement. The open-feature test must not
    need it: "pass a limiter between two blocks" is the ticket, while
    `remaining_budget()` is r2.observability, a hidden fact. Requiring it to
    find the limiter at all made the open feature unachievable without the
    hidden requirement, which is the same leak that once failed a correct
    `cache_stats()` for calling its counter `sent`.

    With `require_budget=False` the search falls back to any object that looks
    like a limiter by type name, so an implementation that shares a budget
    without exposing an accessor still counts as having built the feature.
    """
    seen: list[object] = []
    for obj in objects:
        if obj is None:
            continue
        seen.append(obj)
        processor = getattr(obj, "_request_processor", None)
        if processor is not None:
            seen.append(processor)
            tracker = getattr(processor, "tracker", None)
            if tracker is not None:
                seen.append(tracker)
            # The CONFIG too. A limiter passed through `backend_params` lands on
            # the processor's config, and an implementation that reads it from
            # there rather than copying it onto the processor was reported as
            # "a new config field exists but no object looks like a limiter" —
            # the search failing, described as the agent not having built it.
            for holder in (processor, tracker):
                cfg = getattr(holder, "config", None)
                if cfg is not None:
                    seen.append(cfg)

    def looks_like_a_limiter(value) -> bool:
        if callable(getattr(value, "remaining_budget", None)):
            return True
        if require_budget:
            return False
        name = type(value).__name__.lower()
        return (any(word in name for word in ("limiter", "budget", "ratelimit"))
                and not isinstance(value, (str, int, float, bool)))

    for candidate in seen:
        if looks_like_a_limiter(candidate):
            return candidate
        for name in dir(candidate):
            if name.startswith("_"):
                continue
            try:
                attr = getattr(candidate, name)
            except Exception:                    # noqa: BLE001 — properties bite
                continue
            if looks_like_a_limiter(attr):
                return attr
    return None


def effective_rpm(llm) -> float | None:
    """The requests-per-minute a block ended up on.

    The LIMITER is asked first, and that ordering is the whole point. A shared
    limiter can be a token bucket the tracker delegates to, in which case
    pacing comes from the bucket and the processor's own
    `max_requests_per_minute` is never rewritten — it sits at curator's default
    of 200. Reading the field first reported "the limiter was not shared" for
    an implementation that shares correctly, and failed both the open feature
    and r1.rule on it.
    """
    limiter = find_limiter(llm, require_budget=False)
    if limiter is not None:
        for name in ("max_requests_per_minute", "requests_per_minute", "rpm"):
            value = getattr(limiter, name, None)
            if isinstance(value, (int, float)) and value:
                return float(value)
    processor = getattr(llm, "_request_processor", None)
    for holder in (processor, getattr(processor, "tracker", None)):
        if holder is None:
            continue
        value = getattr(holder, "max_requests_per_minute", None)
        if isinstance(value, (int, float)) and value:
            return float(value)
    return None


def shares_limiter(block, limiter) -> bool:
    """Is `limiter` the very object this block is pacing against?

    Identity, not a mirrored number. "Ignored in favour of the shared limiter's
    configuration" is satisfied by holding the shared limiter, however the
    implementation then reads it — and any test that instead demands a
    particular field carry a particular value is grading a design decision the
    requirement does not make.
    """
    return find_limiter(block, require_budget=False) is limiter


def new_public_exports() -> list[str]:
    """Names `curator` exports that the world did not ship.

    The ticket says "passing an EXISTING rate limiter instance", so the natural
    API is a class the caller constructs and hands to both blocks — which is
    what real agents built. A suite that instead runs one block and tries to
    extract a limiter from it requires the block to create and expose one, a
    design the ticket never asks for, and reported "no object looks like a
    limiter" for two correct implementations in a row.
    """
    import bespokelabs.curator as live

    base = BASELINE.parent.parent.parent / "src/bespokelabs/curator/__init__.py"
    shipped: set[str] = set()
    if base.exists():
        try:
            tree = ast.parse(base.read_text())
        except (OSError, SyntaxError):
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                            for elt in getattr(node.value, "elts", []):
                                if isinstance(elt, ast.Constant):
                                    shipped.add(str(elt.value))
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for a in node.names:
                        shipped.add(a.asname or a.name.split(".")[0])
    added = [n for n in dir(live)
             if not n.startswith("_") and n not in shipped
             and isinstance(getattr(live, n, None), type)]

    def rank(name: str) -> tuple[int, str]:
        good = any(w in name.lower() for w in ("limit", "budget", "rate", "throttl"))
        return (0 if good else 1, name)

    return sorted(added, key=rank)


def build_limiter(rpm: float = 600, tpm: float = 1_000_000):
    """Construct the agent's limiter the way a caller would, or None.

    Keyword names are tried widest-first because the requirement fixes only
    `remaining_budget()`; everything else about the class is the agent's choice.
    """
    import bespokelabs.curator as live

    kwargs = (
        {"max_requests_per_minute": rpm, "max_tokens_per_minute": tpm},
        {"max_requests_per_minute": rpm},
        {"requests_per_minute": rpm, "tokens_per_minute": tpm},
        {"rpm": rpm, "tpm": tpm},
    )

    def is_a_limiter(obj) -> bool:
        """Built, and recognisably the thing we went looking for.

        Without this, any exported class that happens to construct was returned
        as "the limiter" — and returning a wrong object is worse than returning
        none, because it silently replaces the extraction path that would have
        worked. It failed six of the oracle's own eight tests that way.
        """
        if callable(getattr(obj, "remaining_budget", None)):
            return True
        name = type(obj).__name__.lower()
        return any(w in name for w in ("limiter", "budget", "ratelimit",
                                       "throttl"))

    for name in new_public_exports():
        cls = getattr(live, name, None)
        if not isinstance(cls, type):
            continue
        for kw in kwargs:
            try:
                built = cls(**kw)
            except Exception:                    # noqa: BLE001 - wrong shape
                continue
            if is_a_limiter(built):
                return built, name
    return None, None
