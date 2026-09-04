"""An OpenAI-compatible provider, in-process, on a real socket.

This replaces every monkeypatch the suites used to install. That is not tidiness:
five of the eight tests that failed even when the agent was handed the
requirement failed inside a fake, not inside the agent's code —

  * `_BatchStub` read `uploaded` off the wrong object, and its methods were not
    `async`, so `await client.files.create(...)` raised and no batch was ever
    counted;
  * the streaming fake could not satisfy `_handle_longlive_response`, so every
    DeepSeek test died with "All requests failed";
  * patching `aiohttp.ClientSession.post` meant t4's tests grade a layer the
    agent is expected to edit, so a correct edit invalidated the fake.

A real socket has none of those failure modes. curator's own client code runs
end to end — its retry loop, its streaming reader, its batch poller — and the
only thing that changes is which host answers.

The server is also the ORACLE. "How many of the last run's requests were served
from the local cache versus sent to the backend" is, read literally, a count of
requests this server received. That is invariant to every internal detail an
agent might reorganise, which is exactly what the old counter was not.

Provider detection keeps working because the hostname is real. curator decides
DeepSeek with `if "api.deepseek.com" in self.url`, so the tests point `base_url`
at `http://api.deepseek.com:<port>` and the verifier maps that name to
127.0.0.1 in /etc/hosts. The substring matches, the name resolves locally, and
no code is faked to make it happen.
"""
from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Hostnames the tests use. They have to be real names that resolve, because
# curator picks its provider branch off the URL.
HOSTS = ("api.openai.com", "api.deepseek.com", "api.anthropic.com")

_COMPLETION = {"id": "chatcmpl-verifier", "object": "chat.completion", "created": 0}


class FakeProvider:
    """Scripts responses, counts requests, and serves both curator paths."""

    def __init__(self):
        self.requests: list[dict] = []      # dataset requests only; see `completion`
        self.probes = 0                     # rate-limit probes, counted apart
        self.script: list[str] | None = None
        self.body = "verifier answer"
        self.batches_created = 0
        self._files: dict[str, bytes] = {}
        self._batches: dict[str, dict] = {}
        self._seq = 0
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None

    # -- the oracle --------------------------------------------------------
    @property
    def n(self) -> int:
        """Requests that actually reached the backend."""
        return len(self.requests)

    def reset(self) -> None:
        with self._lock:
            self.requests.clear()
            self.batches_created = 0
            self.probes = 0

    def delta(self, fn):
        """Run `fn` and report how many requests it sent."""
        before = self.n
        out = fn()
        return out, self.n - before

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> "FakeProvider":
        handler = _handler_for(self)
        # Port 0: the OS picks a free one. A fixed port collides with the
        # previous test's socket in TIME_WAIT and fails one test in a run for
        # no reason anybody can reproduce.
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    def url(self, host: str = "api.openai.com") -> str:
        """A base_url curator will accept, on a name that picks the provider."""
        return f"http://{host}:{self.port}/v1"

    # -- what a request gets back ------------------------------------------
    def _next_body(self) -> str:
        with self._lock:
            if self.script:
                return self.script.pop(0) if self.script else self.body
            return self.body

    def completion(self, payload: dict) -> dict:
        """Answer a chat completion, counting only the ones that are work.

        `get_header_based_rate_limits` posts `{"model": ..., "messages": []}` to
        the completions endpoint on every processor construction, purely to read
        rate-limit headers off the reply. It is a real request on the wire and
        it is NOT one of the dataset's — counting it made a two-row run look
        like three requests, which would have quietly broken every cache
        assertion in t1, since those turn on the exact count.
        """
        if not (payload.get("messages") or []):
            with self._lock:
                self.probes += 1
            return {**_COMPLETION, "model": payload.get("model", ""),
                    "choices": [], "usage": {"prompt_tokens": 0,
                                             "completion_tokens": 0,
                                             "total_tokens": 0}}
        with self._lock:
            self.requests.append(payload)
        body = self._next_body()
        fmt = payload.get("response_format") or {}
        schema = (fmt.get("json_schema") or {}).get("schema") or {}
        props = schema.get("properties") or {}
        if props:
            # The parser rejects a bare string against a schema, so answer in
            # the shape the caller asked for.
            body = json.dumps({k: (body if (v or {}).get("type", "string") == "string"
                                   else 1) for k, v in props.items()})
        return {**_COMPLETION,
                "model": payload.get("model", "gpt-4o-mini"),
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": body}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 6,
                          "total_tokens": 18}}

    # -- the batch surface -------------------------------------------------
    def add_file(self, blob: bytes) -> str:
        with self._lock:
            self._seq += 1
            ident = f"file-{self._seq}"
            self._files[ident] = blob
        return ident

    def make_batch(self, input_file_id: str, metadata: dict) -> dict:
        """Answer a batch as already completed, with its output file ready.

        Completing immediately keeps the poller to one round trip. The tests
        care about how many batches were submitted, never about the wait.
        """
        with self._lock:
            self._seq += 1
            ident = f"batch-{self._seq}"
            self.batches_created += 1
            source = self._files.get(input_file_id, b"")

        lines = []
        for raw in source.splitlines():
            try:
                request = json.loads(raw)
            except ValueError:
                continue
            payload = request.get("body") or {}
            lines.append(json.dumps({
                "custom_id": request.get("custom_id", "0"),
                "response": {"status_code": 200,
                             "body": self.completion(payload)}}))
        out_id = self.add_file("\n".join(lines).encode())

        # Timestamps matter. curator derives `finished_at` from
        # `completed_at or failed_at or expired_at or cancelled_at`
        # (openai_batch_request_processor.py:137) and feeds it into a
        # GenericResponse field that is a real datetime — so a batch without
        # any of the four fails pydantic validation with an opaque
        # "1 validation error ... datetime_type" from deep inside the parser.
        # Non-zero, because 0 is a valid unix timestamp but reads as "unset" to
        # anyone debugging this later.
        stamp = 1_700_000_000
        batch = {"id": ident, "object": "batch", "status": "completed",
                 "input_file_id": input_file_id, "output_file_id": out_id,
                 "error_file_id": None, "endpoint": "/v1/chat/completions",
                 "completion_window": "24h", "created_at": stamp,
                 "in_progress_at": stamp, "finalizing_at": stamp,
                 "completed_at": stamp + 1, "expires_at": stamp + 86400,
                 "failed_at": None, "expired_at": None,
                 "cancelling_at": None, "cancelled_at": None,
                 "metadata": metadata or {},
                 "request_counts": {"total": len(lines), "completed": len(lines),
                                    "failed": 0}}
        with self._lock:
            self._batches[ident] = batch
        return batch

    def batch(self, ident: str) -> dict | None:
        return self._batches.get(ident)

    def file_content(self, ident: str) -> bytes:
        return self._files.get(ident, b"")


def _jsonl_from_multipart(body: bytes) -> bytes:
    """The uploaded JSONL, pulled out of a multipart body.

    Parsed by looking for the lines that are JSON rather than by walking MIME
    boundaries: the SDK's exact encoding is not the thing under test, and a
    boundary parser is one more piece of this harness that can be subtly wrong.
    """
    keep = [line for line in body.splitlines()
            if line.strip().startswith(b"{") and line.strip().endswith(b"}")]
    return b"\n".join(keep)


def _handler_for(provider: FakeProvider):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        # -- plumbing ------------------------------------------------------
        def log_message(self, *a):
            """Silence. The access log would land in the captured output the
            tests parse, and did."""

        def _read(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(length) if length else b""

        def _send(self, payload, status: int = 200, raw: bytes | None = None):
            body = raw if raw is not None else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type",
                             "application/json" if raw is None else "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # -- routes --------------------------------------------------------
        def do_POST(self):
            path = self.path.split("?")[0]
            body = self._read()

            if path.endswith("/chat/completions"):
                try:
                    payload = json.loads(body or b"{}")
                except ValueError:
                    payload = {}
                return self._send(provider.completion(payload))

            if path.endswith("/files"):
                ident = provider.add_file(_jsonl_from_multipart(body))
                return self._send({"id": ident, "object": "file",
                                   "status": "processed", "purpose": "batch",
                                   "filename": "requests.jsonl", "bytes": len(body),
                                   "created_at": 0})

            if path.endswith("/batches"):
                try:
                    payload = json.loads(body or b"{}")
                except ValueError:
                    payload = {}
                return self._send(provider.make_batch(
                    payload.get("input_file_id", ""), payload.get("metadata") or {}))

            return self._send({"error": {"message": f"no route for {path}"}}, 404)

        def do_GET(self):
            path = self.path.split("?")[0]

            m = re.search(r"/files/([^/]+)/content$", path)
            if m:
                return self._send(None, raw=provider.file_content(m.group(1)))

            m = re.search(r"/files/([^/]+)$", path)
            if m:
                return self._send({"id": m.group(1), "object": "file",
                                   "status": "processed", "purpose": "batch",
                                   "filename": "requests.jsonl", "bytes": 0,
                                   "created_at": 0})

            m = re.search(r"/batches/([^/]+)$", path)
            if m:
                found = provider.batch(m.group(1))
                if found is None:
                    return self._send({"error": {"message": "no such batch"}}, 404)
                return self._send(found)

            if path.endswith("/models"):
                return self._send({"object": "list", "data": []})

            return self._send({"error": {"message": f"no route for {path}"}}, 404)

        def do_DELETE(self):
            m = re.search(r"/files/([^/]+)$", self.path.split("?")[0])
            ident = m.group(1) if m else ""
            return self._send({"id": ident, "object": "file", "deleted": True})

    return Handler
