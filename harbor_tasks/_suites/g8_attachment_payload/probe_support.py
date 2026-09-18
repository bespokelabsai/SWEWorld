"""g8 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, the harness contract the ticket
fixes (`StubOnline`, `FakeEncoder`, the warning recorder) and the answer-free
inputs the probe drives curator with (`PDF_BYTES`, its base64 derivation
`PDF_B64`, `REMOTE_JPEG`). It contains NO expected-output value: no fingerprint
string, no token count, no capped filename, no MIME literal, no size ceiling.
That is load-bearing: `run_suites.run_split` copies this file into the worker's
jail, so it sits inside the process that runs agent code. If any reward-bearing
expected value ever appeared here, the worker could read it and forge a passing
`observations.json`. The answers live only in `judge.py` (and, for humans, in
`test_open.py` / `test_r1.py` / `test_r2.py`), which the worker cannot read.

`test_open.py` imports these names so there is a single definition of each
helper and the probe cannot drift from the reference.
"""
from __future__ import annotations

import base64
import logging
import pathlib
import tempfile

import pytest
from harness import read_field  # re-exported; the probe records values with it

# Imported defensively and re-raised per probe: a missing attachment module is
# one fact failing per requirement, not three probes that die at import.
IMPORT_ERROR = None
try:
    from bespokelabs.curator.file_utilities import get_base64_size
    from bespokelabs.curator.request_processor.online.base_online_request_processor import (
        BaseOnlineRequestProcessor,
    )
    from bespokelabs.curator.types.prompt import BaseType, File, Image, _MultiModalPrompt
except Exception as _exc:  # pragma: no cover - the shape of an unimplemented tree
    IMPORT_ERROR = _exc
    BaseOnlineRequestProcessor = BaseType = File = Image = _MultiModalPrompt = None
    get_base64_size = None

ATTACHMENT_IMPORT_ERROR = None
try:
    from bespokelabs.curator.types import attachment as attachment_module
except Exception as _exc:  # pragma: no cover
    ATTACHMENT_IMPORT_ERROR = _exc
    attachment_module = None


def importable() -> None:
    """Fail one test, not the whole module, when curator itself will not import."""
    if IMPORT_ERROR is not None:
        pytest.fail(f"curator's prompt/request-processor modules could not be imported: {IMPORT_ERROR!r}")


# ---------------------------------------------------------------------------
# Locating the new symbols
#
# The ticket names `types/attachment.py`, but which module a name is *written*
# in is not what is being graded: an implementation that defined the block model
# next to the processor and re-exported it has satisfied the requirement just as
# well. Every lookup below therefore sweeps the modules that could plausibly
# hold it and takes the first hit.
# ---------------------------------------------------------------------------
def _candidate_modules():
    import importlib

    names = (
        "bespokelabs.curator.types.attachment",
        "bespokelabs.curator.types.prompt",
        "bespokelabs.curator.types",
        "bespokelabs.curator.request_processor.online.base_online_request_processor",
    )
    out = []
    for name in names:
        try:
            out.append(importlib.import_module(name))
        except Exception:
            continue
    return out


def attachment_symbol(*names, required: bool = True):
    """One of `names`, from wherever in curator it was defined."""
    for module in _candidate_modules():
        for name in names:
            if hasattr(module, name):
                return getattr(module, name)
    if not required:
        return None
    pytest.fail(
        f"none of {names} is exported by curator's attachment/prompt/processor modules "
        f"(attachment module import: {ATTACHMENT_IMPORT_ERROR!r})"
    )


# ---------------------------------------------------------------------------
# The harness contract the specification fixes
# ---------------------------------------------------------------------------
class StubOnline(BaseOnlineRequestProcessor if BaseOnlineRequestProcessor is not None else object):
    """A base processor with no config, no client and no I/O.

    `BaseRequestProcessor.__init__` builds a cost processor and a working
    directory; none of the behaviour under test needs either, so the constructor
    is bypassed entirely and only `file_upload_limit_check` does anything.
    """

    backend = "base"
    compatible_provider = "base"

    def __init__(self, hook=None):
        self.calls: list[str] = []
        self._hook = hook

    def validate_config(self):
        return None

    def requests_to_responses(self, generic_request_files):
        return None

    def estimate_total_tokens(self, messages):
        return 0

    def estimate_output_tokens(self):
        return 0

    def create_api_specific_request_online(self, generic_request):
        return {}

    async def call_single_request(self, request, session, status_tracker):  # pragma: no cover
        raise NotImplementedError

    def file_upload_limit_check(self, base64_image: str) -> None:
        self.calls.append(base64_image)
        if self._hook is not None:
            self._hook(base64_image)


def raising_stub(message: str = "provider"):
    """A stub whose provider hook refuses everything it is shown."""

    def hook(payload):
        raise RuntimeError(message)

    return StubOnline(hook=hook)


class FakeEncoder:
    """One token per character, so every count below is a literal length."""

    def encode(self, text, disallowed_special=()):
        return list(text)


PDF_BYTES = b"%PDF-1.4\n"
PDF_B64 = base64.b64encode(PDF_BYTES).decode()  # a base64 of the input, not an answer
PNG_BYTES = b"1234"
REMOTE_JPEG = "https://cdn.example.com/photos/cat.jpeg?size=large"


def apply_seed(spec: dict) -> None:
    """Re-draw the attached bytes from the run's seed (see `fixture_spec`).

    `probe.main` calls this before any probe runs, and the values above are the
    stand-in the offline `test_*.py` read. A probe that never applied the seed
    therefore does not pass blind: the judge derives its expectations from the
    seed root drew, and last run's bytes do not match this run's.
    """
    global PDF_BYTES, PDF_B64, PNG_BYTES
    PDF_BYTES = spec["pdf_bytes"]
    PDF_B64 = base64.b64encode(PDF_BYTES).decode()
    PNG_BYTES = spec["png_bytes"]


def make_tmp_dir() -> pathlib.Path:
    """A throwaway directory the probe writes payloads into.

    The reference tests get one from pytest's `tmp_path` fixture; the worker runs
    outside pytest, so it makes its own. Returned as a `pathlib.Path` so `write()`
    below spells `dir / name` the same way for both callers.
    """
    return pathlib.Path(tempfile.mkdtemp(prefix="g8-attachment-"))


def write(tmp_path, name: str, body: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(body)
    return str(path)


def block_of(stub, data):
    """The canonical block for one attachment, however the seam is spelled."""
    build = getattr(stub, "_canonical_attachment_block", None)
    if build is None:
        pytest.fail(
            "BaseOnlineRequestProcessor has no _canonical_attachment_block(); the "
            "canonical attachment layer is the whole ticket."
        )
    return build(data)


# ---------------------------------------------------------------------------
# The warning-capture plumbing (r2's `failure_behavior`)
#
# Which module logs the downgrade is not the requirement; that it is logged once
# is. So the handler hangs on both the root logger and curator's own, and dedupes
# records by identity — "exactly one" still means one in total however the
# implementation routes the warning. Answer-free: it counts warnings, it does not
# know what a right count is.
# ---------------------------------------------------------------------------
class Recorder(logging.Handler):
    """One recorder, hung on every logger that could carry the warning."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.seen: dict[int, logging.LogRecord] = {}

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.seen[id(record)] = record

    @property
    def count(self) -> int:
        return len(self.seen)


class capture_warnings:
    """Context manager yielding a `Recorder` over the block it wraps."""

    def __enter__(self) -> Recorder:
        self.recorder = Recorder()
        self.loggers = [logging.getLogger(), logging.getLogger("curator")]
        self.levels = []
        for log in self.loggers:
            log.addHandler(self.recorder)
            self.levels.append(log.level)
            log.setLevel(min(log.level or logging.WARNING, logging.WARNING))
        return self.recorder

    def __exit__(self, *exc):
        for log, level in zip(self.loggers, self.levels):
            log.removeHandler(self.recorder)
            log.setLevel(level)
        return False
