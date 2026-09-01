"""Offline harness for the curator grading suites.

Nothing here may reach the network, and every fake sits one layer *below* the
code under test. That placement is the whole design: t4's agent edits
`fetch_response` and `call_single_request` directly, so a fake that replaced
those would be replaced along with them and the test would grade itself. Faking
`aiohttp.ClientSession.post` instead survives whatever the agent renames.

The transport fake is also the oracle of record. "How many of the last run's
requests were served from the local cache versus sent to the backend" is,
literally, a count of HTTP posts — so t1 is graded on that count rather than on
the agent's own bookkeeping, which would otherwise be marking its own homework.
"""
from __future__ import annotations

import json
import socket
import types

import pytest

_CHAT_COMPLETION = {"id": "chatcmpl-verifier", "object": "chat.completion",
                    "created": 0}


# =============================================================================
# The fake transport
# =============================================================================
class _AsyncLines:
    """`response.content`, for the streaming path.

    DeepSeek sets `_longlived_response = True` and `_handle_longlive_response`
    does `async for line in response.content`. A fake without this hangs t4
    rather than failing it, which reads as a broken verifier.
    """

    def __init__(self, blob: bytes):
        self._it = iter([blob] if blob else [])

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def text(self):
        return json.dumps(self._payload)

    @property
    def content(self):
        return _AsyncLines(json.dumps(self._payload).encode())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _envelope(payload: dict, body: str) -> dict:
    """Wrap `body` in a chat-completion, honouring any response_format.

    `create_api_specific_request_online` puts the raw model_json_schema at
    payload["response_format"]["json_schema"]["schema"], and the parser will
    reject a plain string against it.
    """
    fmt = payload.get("response_format") or {}
    schema = (fmt.get("json_schema") or {}).get("schema") or {}
    props = schema.get("properties") or {}
    if props:
        body = json.dumps({k: (body if (v or {}).get("type", "string") == "string"
                               else 1) for k, v in props.items()})
    return {**_CHAT_COMPLETION,
            "model": payload.get("model", "gpt-4o-mini"),
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": body}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 6,
                      "total_tokens": 18}}


class FakeTransport:
    """Stands in for every provider call, and counts them."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.script: list[str] | None = None
        self.body = "verifier-answer"

    @property
    def n(self) -> int:
        return len(self.calls)

    def reset(self) -> None:
        self.calls.clear()

    def delta(self, fn):
        """Run `fn` and report how many provider calls it made."""
        before = self.n
        out = fn()
        return out, self.n - before

    def post(self, _session, url, **kw):
        payload = kw.get("json") or {}
        self.calls.append((url, payload))
        if self.script:
            body = self.script.pop(0) if self.script else self.body
        else:
            body = self.body
        return _FakeResponse(_envelope(payload, body))


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture(autouse=True)
def offline_env(monkeypatch, tmp_path):
    """Everything that would otherwise phone home, and a private cache dir.

    CURATOR_VIEWER=false matters more than it looks: with it unset
    `Client.create_session` never sets `_session`, so every `stream_response`
    and `log_cost_projection` short-circuits instead of posting.
    """
    for key, value in {
        "TELEMETRY_ENABLED": "false",
        "CURATOR_VIEWER": "false",
        "CURATOR_DISABLE_RICH_DISPLAY": "1",
        "OPENAI_API_KEY": "sk-verifier",
        "ANTHROPIC_API_KEY": "sk-verifier",
        "HF_HUB_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "HF_DATASETS_CACHE": str(tmp_path / "hf"),
        "CURATOR_CACHE_DIR": str(tmp_path / "curator-cache"),
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CURATOR_DISABLE_CACHE", raising=False)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """A hard floor under the fakes.

    Anything that escapes them fails loudly here instead of hanging for the
    verifier's whole timeout and being scored as a wrong answer.
    """
    def blocked(*a, **k):
        raise RuntimeError("verifier: network access attempted")
    monkeypatch.setattr(socket.socket, "connect", blocked)


@pytest.fixture
def transport(monkeypatch):
    """The online backend, fully offline.

    Two patches. The aiohttp POST every online processor ultimately makes, and
    the blocking `requests.post` that `OpenAIOnlineRequestProcessor.__init__`
    fires at `get_header_based_rate_limits()` for any non-DeepSeek URL — empty
    headers make rpm/tpm come back falsy, so the processor falls through to its
    own defaults. The method itself is NOT patched: t4's agent may edit it.
    """
    import aiohttp
    from bespokelabs.curator.request_processor.online import (
        openai_online_request_processor as oai)

    fake = FakeTransport()
    monkeypatch.setattr(aiohttp.ClientSession, "post",
                        lambda self, url, **kw: fake.post(self, url, **kw))
    monkeypatch.setattr(oai.requests, "post",
                        lambda *a, **k: types.SimpleNamespace(headers={},
                                                              status_code=200))
    return fake


class _BatchStub:
    """The provider side of the batch path, offline.

    Implements exactly the calls `OpenAIBatchRequestProcessor` makes and nothing
    else. `n_batches` is the oracle: submitting a batch is what costs money, so
    "the cache was consulted on the batch path" means that count stayed at zero.

    `sentinel` mode makes `files.create` raise, which turns "the estimate is
    printed BEFORE anything is submitted" from a wording question into an
    ordering one — whatever reached the terminal before the exception is, by
    construction, pre-flight.
    """

    class _Sentinel(RuntimeError):
        pass

    def __init__(self, sentinel: bool = False):
        self.api_key = "sk-verifier"
        self.sentinel = sentinel
        self.n_batches = 0
        self._responses: list[str] = []
        self.files = self._Files(self)
        self.batches = self._Batches(self)

    def reset(self) -> None:
        self.n_batches = 0

    class _Files:
        def __init__(self, outer):
            self.outer = outer
            self.uploaded: list[bytes] = []

        def create(self, file=None, purpose=None):
            if self.outer.sentinel:
                raise _BatchStub._Sentinel("submission reached")
            body = file.read() if hasattr(file, "read") else (file or b"")
            self.outer.uploaded.append(body)
            return types.SimpleNamespace(id="file-verifier")

        def wait_for_processing(self, ident):
            return types.SimpleNamespace(id=ident, status="processed")

        def content(self, ident):
            lines = []
            for raw in (self.outer.uploaded[-1] or b"").splitlines():
                try:
                    req = json.loads(raw)
                except ValueError:
                    continue
                payload = req.get("body") or {}
                lines.append(json.dumps({
                    "custom_id": req.get("custom_id", "0"),
                    "response": {"status_code": 200,
                                 "body": _envelope(payload, "verifier-answer")}}))
            return types.SimpleNamespace(text="\n".join(lines))

        def delete(self, ident):
            return types.SimpleNamespace(id=ident, deleted=True)

    class _Batches:
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kw):
            self.outer.n_batches += 1
            return types.SimpleNamespace(
                id="batch-verifier", status="completed",
                output_file_id="file-verifier", error_file_id=None,
                request_counts=types.SimpleNamespace(completed=1, failed=0,
                                                     total=1),
                metadata=kw.get("metadata") or {})

        def retrieve(self, ident):
            return self.create()


@pytest.fixture
def openai_batch_stub(monkeypatch):
    from bespokelabs.curator.request_processor.batch import (
        openai_batch_request_processor as batch)

    stub = _BatchStub()
    monkeypatch.setattr(batch, "AsyncOpenAI", lambda *a, **k: stub)
    return stub


@pytest.fixture
def openai_batch_sentinel(monkeypatch):
    """As above, but nothing may be submitted: the first upload raises."""
    from bespokelabs.curator.request_processor.batch import (
        openai_batch_request_processor as batch)

    stub = _BatchStub(sentinel=True)
    monkeypatch.setattr(batch, "AsyncOpenAI", lambda *a, **k: stub)
    return stub


# =============================================================================
# Tolerant readers
# =============================================================================
def surface(obj) -> list[str]:
    if isinstance(obj, dict):
        return sorted(obj)
    return sorted(k for k in dir(obj) if not k.startswith("_"))


def read_field(obj, *names, default=...):
    """A field by any of several names, from a dict, dataclass or model.

    The requirement fixes the field NAMES (`hit_rate`, `misses`); it does not
    fix the container, so an agent returning a dict, a dataclass or a pydantic
    model has all satisfied it.
    """
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    if hasattr(obj, "to_dict"):
        as_dict = obj.to_dict()
        for name in names:
            if name in as_dict:
                return as_dict[name]
    if default is not ...:
        return default
    raise AssertionError(
        f"expected one of {names} on {type(obj).__name__}; it has {surface(obj)}")


def cache_stats_of(llm):
    """`cache_stats()` is named in the ticket, so it is fair to require."""
    fn = getattr(llm, "cache_stats", None)
    if not callable(fn):
        pytest.fail("curator.LLM has no callable cache_stats(); its public "
                    f"surface is {surface(llm)}")
    return fn()


def baseline_tree() -> str:
    """The pristine curator the world shipped with.

    Root-readable at verify time, and the reason no test has to guess at an
    identifier the agent invented: anything not in here is theirs.
    """
    return "/opt/world-state/input/curator"
