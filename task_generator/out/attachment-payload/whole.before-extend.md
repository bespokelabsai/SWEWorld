# Canonical attachment blocks for multimodal prompts

## Target

### Files that change
- `src/bespokelabs/curator/types/attachment.py` — **NEW**. The canonical block model,
  the three attachment exceptions, the size ceilings, the MIME normalizer.
- `src/bespokelabs/curator/types/prompt.py` — `Image.model_post_init` (line 87),
  `File.set_mime_type` (line 103), `BaseType` (add `is_remote`), `_MultiModalPrompt`
  (add `attachments()`).
- `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` —
  `_format_multimodal` (line 134) and `_handle_multi_modal_prompt` (line 159) are
  rewritten around `_canonical_attachment_block` / `_render_attachment_block`; add
  module-level `_render_openai_block`.
- `src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py` —
  delete the `_format_multimodal` override (lines 111-128), add module-level
  `_render_anthropic_block` and a `_render_attachment_block` override.
- `src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py` —
  delete the `_format_multimodal` override (lines 163-181), add a
  `_render_attachment_block` override that dispatches on
  `_uses_anthropic_multimodal_format()`.
- `src/bespokelabs/curator/request_processor/openai_request_mixin.py` —
  `calculate_input_tokens` (lines 9-24).

### Existing machinery that may be REUSED (do not reimplement)
- `bespokelabs.curator.file_utilities.get_base64_size(b64_string) -> float` (MB, from
  base64 length; `file_utilities.py:25-29`). This is the *only* sizer.
- `BaseType.serialize()` on `Image`/`File` (`prompt.py:60`, `prompt.py:110`) — produces the
  base64 text (or returns the URL for a non-local `Image`).
- `BaseType._is_local_uri`, `BaseType._load_file_as_b64`, `BaseType.is_local`
  (`prompt.py:21-34`).
- `_MultiModalPrompt.load` / `.model_validate` and `BaseOnlineRequestProcessor._unpack_multimodal`
  (`base_online_request_processor.py:110`) — unchanged.
- `LiteLLMOnlineRequestProcessor._uses_anthropic_multimodal_format`
  (`litellm_online_request_processor.py:159`) — unchanged, reused as the litellm dispatch key.
- `mimetypes`, `os.path`, `pydantic`, `logger` (`bespokelabs.curator.log`).

### What must be BUILT
- `AttachmentBlock` (pydantic model), `AttachmentError`, `UnknownAttachmentMimeType`,
  `AttachmentTooLarge`, `MissingLocalAttachment`, `normalize_mime_type`,
  `_ATTACHMENT_SIZE_LIMIT_MB`, `_ATTACHMENT_PROMPT_LIMIT_MB`, `_FALLBACK_ATTACHMENT_FILENAME`.
- `BaseType.is_remote`, `_MultiModalPrompt.attachments()`.
- `BaseOnlineRequestProcessor._canonical_attachment_block`,
  `BaseOnlineRequestProcessor._render_attachment_block`, `_render_openai_block`,
  `_render_anthropic_block`.
- `_OPENAI_TOKENS_PER_DOCUMENT` and the block-type dispatch in `calculate_input_tokens`.

### Known latent bugs in this area (real, with locations)
1. `openai_request_mixin.py:20-22` — every non-`text` block is indexed as `msg["image_url"]`.
   An anthropic-shaped block (`{"type": "image", "source": ...}`) or any document block
   raises `KeyError: 'image_url'`. **P9 fixes this.**
2. `base_online_request_processor.py:136` — `mime_type = mime_type or "image/png"` labels a
   `File` whose MIME could not be guessed as a PNG image. **P2/P3 fix this.**
3. `base_online_request_processor.py:138` — the remote-URL branch returns before
   `file_upload_limit_check`, so no size ceiling of any kind applies to a URL attachment.
   **P4 makes this an explicit, asserted policy rather than an accident.**
4. `base_online_request_processor.py:138` — a mistyped local path (`/tmp/nope.png`) is neither
   local nor a URL, and is shipped to the provider as `{"url": "/tmp/nope.png"}`.
   **P10 fixes this.**
5. Out of scope by instruction, listed for completeness: `File` has no `detail` attribute
   (`prompt.py:96` vs `base_online_request_processor.py:150`), and
   `litellm_online_request_processor.py:139` gates on `self.config.model.split("/")[0]`, which
   misses an unprefixed model name. Neither is graded; P1 and P4 are written so that a correct
   implementation does not depend on either.

### Python / dependencies
Python `^3.10` (project floor; the checkout runs on 3.10 and 3.13). pydantic `>=2.9.2`,
`pillow`, `litellm==1.83.7`, `pytest`, `pytest-asyncio` — all already dependencies. No new
dependency. Nothing in this specification imports `aiohttp`, opens a socket, sleeps, or spawns
anything.

---

## The API

```python
# src/bespokelabs/curator/types/attachment.py  (NEW)

import typing as t
from pydantic import BaseModel, ConfigDict

_ATTACHMENT_SIZE_LIMIT_MB: dict[str, float] = {"image": 20.0, "document": 24.0}
_ATTACHMENT_PROMPT_LIMIT_MB: float = 45.0
_FALLBACK_ATTACHMENT_FILENAME: str = "attachment.bin"


class AttachmentBlock(BaseModel):
    """Provider-independent description of one attachment."""

    kind: t.Literal["image", "document"]
    source: t.Literal["url", "base64"]
    mime_type: str                       # always lowercase, no parameters
    payload: str                         # the URL when source == "url", else base64 text
    filename: str                        # never empty
    detail: str | None = None            # str when kind == "image", None when kind == "document"
    size_mb: float | None = None         # float when source == "base64", None when source == "url"

    model_config = ConfigDict(frozen=True)


class AttachmentError(ValueError):
    """Base class for every attachment rejection."""


class UnknownAttachmentMimeType(AttachmentError):
    url: str
    attachment_type: str                 # "image" or "file" — the BaseType.type ClassVar

    def __init__(self, url: str, attachment_type: str) -> None:
        self.url = url
        self.attachment_type = attachment_type
        super().__init__(f"Cannot determine MIME type for {attachment_type} attachment: {url!r}")


class AttachmentTooLarge(AttachmentError):
    kind: str                            # "image", "document" or "prompt"
    size_mb: float
    limit_mb: float

    def __init__(self, kind: str, size_mb: float, limit_mb: float) -> None:
        self.kind = kind
        self.size_mb = size_mb
        self.limit_mb = limit_mb
        super().__init__(f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit.")


class MissingLocalAttachment(AttachmentError):
    url: str

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Attachment path is neither an http(s) URL nor an existing file: {url!r}")


def normalize_mime_type(value: str | None) -> str | None:
    """Lowercase, strip surrounding whitespace, drop ``;``-parameters. None/"" -> None."""
```

```python
# src/bespokelabs/curator/types/prompt.py

class BaseType(BaseModel):
    @property
    def is_remote(self) -> bool:
        """True iff url starts with 'http://' or 'https://' (case-insensitive)."""

class Image(BaseType):
    def model_post_init(self, __context) -> None: ...          # see P2

class File(BaseType):
    @field_validator("mime_type", mode="before")
    @classmethod
    def set_mime_type(cls, value, values) -> str | None: ...    # see P2

class _MultiModalPrompt(BaseType):
    def attachments(self) -> list[BaseType]:
        """self.images + self.files, in that order. New list; inputs untouched."""
```

```python
# src/bespokelabs/curator/request_processor/online/base_online_request_processor.py

def _render_openai_block(block: AttachmentBlock) -> dict: ...    # module level, pure

class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
    def _canonical_attachment_block(self, data: BaseType) -> AttachmentBlock: ...
    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
        return _render_openai_block(block)
    def _format_multimodal(self, data, mime_type=None) -> dict:
        """Back-compatible one-shot: build canonical, then render. mime_type is ignored."""
        return self._render_attachment_block(self._canonical_attachment_block(data))
    def _handle_multi_modal_prompt(self, message: _MultiModalPrompt) -> list[dict]: ...
```

```python
# src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
def _render_anthropic_block(block: AttachmentBlock) -> dict: ...  # module level, pure

class AnthropicOnlineRequestProcessor(BaseOnlineRequestProcessor):
    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
        return _render_anthropic_block(block)

# src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
class LiteLLMOnlineRequestProcessor(BaseOnlineRequestProcessor):
    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
        if self._uses_anthropic_multimodal_format():
            return _render_anthropic_block(block)
        return _render_openai_block(block)
```

```python
# src/bespokelabs/curator/request_processor/openai_request_mixin.py
_OPENAI_TOKENS_PER_IMAGE = {"low": 85}      # unchanged
_OPENAI_TOKENS_PER_DOCUMENT = 1400          # new

def calculate_input_tokens(message: str | list[dict], token_encoding) -> int: ...
```

### The rendered block shapes, field by field

`_render_openai_block(block)` returns exactly one of:

| kind / source | dict |
|---|---|
| image / url | `{"type": "image_url", "image_url": {"url": block.payload, "detail": block.detail}}` |
| image / base64 | `{"type": "image_url", "image_url": {"url": f"data:{block.mime_type};base64,{block.payload}", "detail": block.detail}}` |
| document / url | `{"type": "file", "file": {"filename": block.filename, "file_url": block.payload}}` |
| document / base64 | `{"type": "file", "file": {"filename": block.filename, "file_data": f"data:{block.mime_type};base64,{block.payload}"}}` |

`_render_anthropic_block(block)` returns exactly one of:

| source | dict |
|---|---|
| url | `{"type": block.kind, "source": {"type": "url", "url": block.payload}}` |
| base64 | `{"type": block.kind, "source": {"type": "base64", "media_type": block.mime_type, "data": block.payload}}` |

No other keys in either renderer. `detail` and `filename` never appear in an anthropic block.

### Test harness contract (the only fixtures allowed)

```python
class StubOnline(BaseOnlineRequestProcessor):
    backend = "base"
    def __init__(self):                       # bypass BaseRequestProcessor.__init__
        self.calls: list[str] = []
    def validate_config(self): ...
    def requests_to_responses(self, files): ...
    def estimate_total_tokens(self, messages): ...
    def estimate_output_tokens(self): ...
    def create_api_specific_request_online(self, generic_request): ...
    def file_upload_limit_check(self, base64_image: str) -> None:
        self.calls.append(base64_image)       # or raise, per the test

class FakeEncoder:
    def encode(self, text, disallowed_special=()):
        return list(text)                     # 1 token per character
```
Instances are made with `object.__new__(StubOnline)` plus `self.calls = []`, or by a
no-arg `__init__` as above; no `config`, no cost processor, no I/O. A `tmp_path` file is the
only other fixture.

---

## Parts

### P1 — `AttachmentBlock`, and kind decided by MIME rather than by class

**Behaviour.** `_canonical_attachment_block(data)` converts any `Image` or `File` into a frozen
`AttachmentBlock`. `kind` is `"image"` if the resolved `mime_type` starts with the literal
`"image/"` and `"document"` otherwise — the Python class of the attachment is not consulted, so
`File(url=".../diagram.png")` yields `kind == "image"` and
`Image(content=b"...", mime_type="application/pdf")` yields `kind == "document"`.
`detail` is `data.detail` when `kind == "image"` and the attribute exists, `"auto"` when it does
not, and `None` when `kind == "document"`. `filename` is
`os.path.basename(data.url.split("?", 1)[0])` when that is non-empty, else
`_FALLBACK_ATTACHMENT_FILENAME` (`"attachment.bin"`). Providers see this object and nothing else;
`_render_attachment_block` is the only provider seam.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No canonical layer at all.* Keep the status quo shape of the code: each provider overrides
   `_format_multimodal` and builds its own dict straight from the `Image`/`File`. This is what
   the repository does today in three places, and it is a perfectly defensible "providers own
   their vocabulary" design.
2. *Kind from the Python class.* `isinstance(data, Image) -> "image"`, `isinstance(data, File)
   -> "document"`. The types are named for exactly this, `_MultiModalPrompt` already keeps them
   in two separate lists, and it is the reading most people take.
3. *Kind from a substring test*, `"image" if "image" in mime_type else "document"` — which is
   literally what `litellm_online_request_processor.py:169` does today.
4. *`detail` carried only for `Image`*, since `File` has no such attribute, giving a document
   block `detail` of `None` and an image-typed `File` an `AttributeError`.

**The observable.** With a local file `chart.png` containing 4 bytes:
`StubOnline()._canonical_attachment_block(File(url=str(tmp/"chart.png")))` returns an
`AttachmentBlock` with `kind == "image"`, `detail == "auto"`, `filename == "chart.png"`,
`mime_type == "image/png"`, `source == "base64"`. Alternative 2/4 give `kind == "document"` and
`detail is None`; alternative 1 gives no `AttachmentBlock` at all (`AttributeError` /
`TypeError` on the call). Symmetrically,
`_canonical_attachment_block(Image(content=b"%PDF-1.4\n", mime_type="application/pdf"))` has
`kind == "document"`, `detail is None`, `filename == "attachment.bin"`.

**Arbitrary:** invented name (`AttachmentBlock` and its seven field names, `_render_attachment_block`
as the single seam) + policy with no local evidence (kind from MIME prefix, not from class;
`"attachment.bin"` fallback).

---

### P2 — One MIME policy: normalize, guess from the URL path, default only for inline content

**Behaviour.** `normalize_mime_type` lowercases, strips whitespace, and drops everything from the
first `;`, mapping `None`/`""` to `None`; both `Image` and `File` push every MIME through it,
whether the value was supplied or guessed. When no MIME was supplied and a `url` is present, the
guess is made from the URL with query and fragment removed —
`mimetypes.guess_type(url.split("?", 1)[0].split("#", 1)[0])` — so
`"https://cdn.example.com/photos/cat.jpeg?size=large"` resolves to `"image/jpeg"`. If the guess
fails, `mime_type` stays `None` on **both** classes and exactly one `logger.warning` is emitted;
`Image` no longer falls back to `"image/png"` for a URL. The one surviving default: an `Image`
with inline `content` and no `url` and no supplied MIME gets `"image/png"`, matching
`_pil_image_to_bytes`, which always saves PNG.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Keep the two policies as they are* — `Image` defaults to `"image/png"` whenever the guess
   fails (URL or not), `File` yields `None` silently. Twenty lines apart in the current file.
2. *Unify upward*: give `File` the same `"image/png"` fallback the base formatter already
   applies at `base_online_request_processor.py:136`, so nothing downstream ever sees `None`.
3. *Unify on a neutral sentinel*: `"application/octet-stream"` for anything unguessable, in
   either class. This is the standard answer and needs no exception type.
4. *Guess from the raw URL* (no query stripping), which is what `mimetypes.guess_type` is
   normally handed and what the current code does.

**The observable.** Four exact values:
`Image(url="https://cdn.example.com/photos/cat.jpeg?size=large").mime_type == "image/jpeg"`
(alternative 4 gives `"image/png"` under the current code, `None` under 1/3-style handling);
`Image(url="https://example.com/asset").mime_type is None` (alternatives 1/2 give
`"image/png"`, 3 gives `"application/octet-stream"`);
`File(url="/tmp/x/report.PDF", mime_type="Application/PDF; charset=binary").mime_type ==
"application/pdf"` (no normalization gives `"Application/PDF; charset=binary"`);
`Image(content=b"\x89PNG\r\n").mime_type == "image/png"`.

**Arbitrary:** deliberate departure (`Image` stops defaulting to `image/png` for URLs — the code
plainly does the opposite) + policy with no local evidence (query/fragment stripping before the
guess; parameter stripping; the inline-content carve-out).

---

### P3 — An unresolvable MIME type is refused, at block build time, with a named exception

**Behaviour.** `_canonical_attachment_block` raises `UnknownAttachmentMimeType(url=data.url,
attachment_type=data.type)` when the resolved `mime_type` is `None`. `attachment_type` carries the
`BaseType.type` ClassVar — `"image"` or `"file"` — not the block `kind`, which does not exist yet
at this point. The refusal happens when the block is built, not when the model is constructed, so
`Image(url=...)`/`File(url=...)` themselves never raise for a missing MIME.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Substitute a fallback and continue* — `"application/octet-stream"` (or `"image/png"`, as
   `base_online_request_processor.py:136` does today) and send the block anyway.
2. *Raise a bare `ValueError`* with a message, adding no new type. Nothing in the repo defines a
   custom exception for prompts; every existing rejection in this area is a plain
   `ValueError`/`TypeError` (`base_online_request_processor.py:113`,
   `anthropic_online_request_processor.py:204`).
3. *Validate at construction time* with a pydantic `model_validator`, so the failure surfaces
   when the user builds the `File` rather than when a processor formats it.
4. *Skip the attachment* with a warning and drop it from the content list.

**The observable.** `pytest.raises(UnknownAttachmentMimeType)` around
`StubOnline()._canonical_attachment_block(File(url="https://example.com/download"))`; the caught
exception satisfies `exc.url == "https://example.com/download"`, `exc.attachment_type == "file"`,
`isinstance(exc, AttachmentError)` and `isinstance(exc, ValueError)`. For the image side,
`Image(url="https://example.com/asset")` raises with `exc.attachment_type == "image"`. And
`File(url="https://example.com/download")` on its own — construction only — does **not** raise
(alternative 3 fails here). Alternative 1 produces a dict, alternative 2 an exception with no
`.url`/`.attachment_type`, alternative 4 an empty content list.

**Arbitrary:** invented name (`UnknownAttachmentMimeType`, its `AttachmentError` base, and the
`attachment_type` attribute spelled with the `BaseType.type` vocabulary rather than the block
`kind` vocabulary).

---

### P4 — A per-kind ceiling owned by the base, checked before the provider hook

**Behaviour.** Every base64 attachment is measured once with `get_base64_size(payload)` and
compared against `_ATTACHMENT_SIZE_LIMIT_MB[block_kind]` — `20.0` MB for `"image"`, `24.0` MB for
`"document"`; strictly greater raises `AttachmentTooLarge(kind=<block kind>, size_mb=<measured>,
limit_mb=<limit>)`. This check runs inside `_canonical_attachment_block` **before**
`self.file_upload_limit_check(payload)` is called, so the provider hook only ever sees payloads
the global ceiling already accepted. A `source == "url"` block is not measured at all: `size_mb`
is `None` and `file_upload_limit_check` is not called for it.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Leave sizing to the providers*, i.e. keep the three existing per-provider checks
   (`anthropic_online_request_processor.py:199-205`, `openai_online_request_processor.py:250-254`,
   `litellm_online_request_processor.py:138-145`) as the only ceilings, since `file_upload_limit_check`
   is already the abstract hook designed for exactly this.
2. *One global ceiling regardless of kind*, `20` MB for everything, taking the number both
   existing constants already agree on.
3. *Provider hook first, global ceiling second*, on the reasoning that the provider's own limit
   is the more specific rule and should be given the chance to speak first.
4. *Fetch and measure remote URLs too* — or reject remote URLs outright as unmeasurable.

**The observable.** Two assertions, using a stub whose `file_upload_limit_check` raises
`RuntimeError("provider")` unconditionally:
(a) `Image(content="A" * 33_554_432)` (a 24.0 MB base64 payload) raises `AttachmentTooLarge`, not
`RuntimeError`, with `exc.kind == "image"`, `exc.size_mb == 24.0`, `exc.limit_mb == 20.0`
— alternative 3 raises `RuntimeError`, alternative 1 raises nothing from the base, alternative 2
gives `limit_mb == 20.0` here but fails (b);
(b) `Image(content="A" * 33_554_432, mime_type="application/pdf")` — the same 24.0 MB payload,
but `kind == "document"` by P1 — passes the base check entirely and reaches the provider hook
(`RuntimeError` is raised), because the document limit is `24.0` and the comparison is strict `>`;
under alternative 2 this raises `AttachmentTooLarge` with `limit_mb == 20.0`.
Plus: with a recording stub, a remote-URL attachment leaves `stub.calls == []` and
`block.size_mb is None`.

**Arbitrary:** chosen value (`24.0` MB for documents; nothing in the repository mentions a
document ceiling) + policy with no local evidence (per-kind global ceiling in the base, and the
base-before-provider ordering) + invented name (`AttachmentTooLarge` with `.kind`, `.size_mb`,
`.limit_mb`).

---

### P5 — A whole-prompt aggregate ceiling of 45.0 MB

**Behaviour.** After every attachment in a `_MultiModalPrompt` has been converted to a canonical
block (so after all per-attachment checks and all `file_upload_limit_check` calls),
`_handle_multi_modal_prompt` sums `block.size_mb` over the blocks whose `source == "base64"` and
raises `AttachmentTooLarge(kind="prompt", size_mb=<sum>, limit_mb=_ATTACHMENT_PROMPT_LIMIT_MB)`
when that sum is strictly greater than `45.0`. URL blocks contribute nothing to the sum. The
literal `"prompt"` is the `kind` value used for this one exception.

**Alternatives a competent engineer would plausibly choose instead.**
1. *No aggregate limit.* Per-attachment ceilings only — which is all any of the three existing
   checks does, and the obvious reading of "size ceiling".
2. *Aggregate checked incrementally*, raising as soon as the running total crosses the line, so
   the trailing attachments are never built, their provider hooks never fire, and the reported
   sum is the crossing total rather than the prompt total.
3. *An aggregate expressed as a count* ("at most N attachments per prompt") rather than as
   megabytes.
4. *Aggregate compared against the per-kind limit* (20/24) rather than a separate number.

**The observable.** Four images in one `_MultiModalPrompt` — three of
`Image(content="A" * 25_165_824)` (18.0 MB base64 each) followed by one of
`Image(content="A" * 8_388_608)` (6.0 MB), each individually under the 20.0 MB image ceiling,
60.0 MB in total — formatted by a recording stub: `AttachmentTooLarge` is raised with
`exc.kind == "prompt"`, `exc.size_mb == 60.0`, `exc.limit_mb == 45.0`, **and**
`len(stub.calls) == 4`. The fourth attachment is what separates the policies: every alternative
that checks incrementally crosses 45.0 at the third image and reports `exc.size_mb == 54.0` with
`len(stub.calls) <= 3`; alternative 1 returns a 4-element content list and no exception;
alternative 3 never raises for four attachments; alternative 4 gives `limit_mb == 20.0`.
A control: the first two images alone (36.0 MB) produce a 2-block content list with
`len(stub.calls) == 2` and no exception.

**Arbitrary:** chosen value (`45.0` MB, and the `"prompt"` kind literal) + policy with no local
evidence (an aggregate ceiling exists at all, and it is evaluated after the whole prompt is
built rather than incrementally).

---

### P6 — Attachments precede text in the rendered content list

**Behaviour.** `_handle_multi_modal_prompt` returns the rendered attachment blocks first — images
in list order, then files in list order, exactly `_MultiModalPrompt.attachments()` — followed by
one `{"type": "text", "text": <str>}` block per entry of `texts`, in list order. The returned list
has `len(images) + len(files) + len(texts)` elements and is a new list each call.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Text first, then images, then files* — precisely what `_handle_multi_modal_prompt`
   (`base_online_request_processor.py:159-170`) does today; copying the existing loop order is
   the single most likely outcome.
2. *Interleave by the caller's original tuple order*, reconstructing the order in which the
   prompt function returned the parts.
3. *Text last but files before images*, grouping "documents then images then prose".

**The observable.** For `_MultiModalPrompt(texts=["a", "b"], images=[img], files=[doc])` the
returned list `c` satisfies `len(c) == 4`, `[b["type"] for b in c] == ["image_url", "file",
"text", "text"]`, `c[2]["text"] == "a"`, `c[3]["text"] == "b"`. Alternative 1 gives
`["text", "text", "image_url", "file"]`, alternative 3 `["file", "image_url", "text", "text"]`.

**Arbitrary:** deliberate departure (the surrounding code plainly emits text first; reading it
leads you to the wrong answer).

---

### P7 — The OpenAI rendering, including a `file` block for documents

**Behaviour.** `_render_openai_block` maps a canonical block to the four dicts tabulated in
*The API*. Two points that are not forced: an image block carries `"detail"` in **both** the
URL and the base64 case (the current code attaches `detail` only on the base64 branch, and only
when `"image" in mime_type`), and a document block is `{"type": "file", "file": {...}}` carrying
`"filename"` in both cases — `"file_data"` with the `data:` URI when base64, `"file_url"` when
remote.

**Alternatives a competent engineer would plausibly choose instead.**
1. *One shape for everything*: `{"type": "image_url", "image_url": {...}}` for images and
   documents alike, which is exactly what `_format_multimodal` does today for both lists.
2. *Omit `detail` for remote URLs* (current behaviour) or omit it whenever the caller left it at
   the default `"auto"`.
3. *Document base64 as `{"type": "file", "file": {"file_data": ...}}` with no `filename`*, since
   nothing in `Image`/`File` models a filename.
4. *`{"type": "input_file", ...}`* or `{"type": "document", ...}` as the document block tag.

**The observable.** For `File(url=str(tmp/"report.pdf"))` containing `b"%PDF-1.4\n"`,
`_render_openai_block(block)` equals exactly
`{"type": "file", "file": {"filename": "report.pdf", "file_data": "data:application/pdf;base64,JVBERi0xLjQK"}}`
— key set `{"type", "file"}`, inner key set exactly `{"filename", "file_data"}`. For
`Image(url="https://cdn.example.com/photos/cat.jpeg?size=large")` it equals exactly
`{"type": "image_url", "image_url": {"url": "https://cdn.example.com/photos/cat.jpeg?size=large",
"detail": "auto"}}` — alternative 2 omits the `"detail"` key, alternative 1 renders the PDF as an
`image_url`, alternatives 3/4 differ in the inner key set or the `"type"` literal.

**Arbitrary:** policy with no local evidence (a distinct `file` block exists at all in the
OpenAI-shaped path; `filename` is part of it) + deliberate departure (`detail` on URL images).

---

### P8 — The Anthropic rendering

**Behaviour.** `_render_anthropic_block` maps the canonical block to
`{"type": kind, "source": {...}}`, with `{"type": "url", "url": payload}` for a remote block and
`{"type": "base64", "media_type": mime_type, "data": payload}` for a base64 one. `kind` passes
through unchanged, so a PDF becomes a `document` block — the anthropic processor currently emits
`{"type": "image"}` for everything. `detail` and `filename` never appear.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Always `"image"`*, as `anthropic_online_request_processor.py:111-128` does today.
2. *Carry `detail`* into the anthropic block, or a `"title"` field derived from `filename`, both
   of which Anthropic's document blocks accept.

**The observable.** `_render_anthropic_block(pdf_block)` equals exactly
`{"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
"data": "JVBERi0xLjQK"}}`, and `_render_anthropic_block(remote_jpeg_block)` equals exactly
`{"type": "image", "source": {"type": "url", "url": "https://cdn.example.com/photos/cat.jpeg?size=large"}}`.
Both dicts compare equal by `==`, so any extra key fails.

**Arbitrary:** none — derivable from `litellm_online_request_processor.py:163-181`, which already
writes this exact mapping (block type from the MIME, `source.url` vs
`source.type/media_type/data`). An engineer refactoring the three `_format_multimodal` overrides
into one seam will land here without being told.

---

### P9 — What a non-image block costs the OpenAI estimator

**Behaviour.** `calculate_input_tokens` dispatches on `block["type"]` with `.get`, never on the
absence of `"text"`: `"text"` costs `len(token_encoding.encode(str(block.get("text", "")),
disallowed_special=()))`; `"image_url"` and `"image"` cost `_OPENAI_TOKENS_PER_IMAGE["low"]` =
`85`; `"file"` and `"document"` cost `_OPENAI_TOKENS_PER_DOCUMENT` = `1400`; **any other**
`"type"` costs `0` and raises nothing. A `str` message keeps its current behaviour. The return
is an `int`.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Keep the `else: msg = msg["image_url"]` branch* and charge 85 for anything non-text — the
   current code, which happens to `KeyError` on a document block.
2. *Charge documents the anthropic numbers already in the tree*: `1024` for an image and `2048`
   for a document (`litellm_online_request_processor.py:32-33`), or `85`/`170*n` from OpenAI's
   published image formula.
3. *Raise on an unrecognised block type* (`ValueError`/`KeyError`) rather than silently
   contributing zero, on the grounds that an unknown block is a bug worth surfacing.
4. *Size documents from their payload*, e.g. `len(file_data) // 4` tokens, since the base64 is
   right there.

**The observable.** With `FakeEncoder` (1 token per character) and the mixed content list
```python
[{"type": "text", "text": "hello"},
 {"type": "image_url", "image_url": {"url": "x", "detail": "auto"}},
 {"type": "image", "source": {"type": "url", "url": "x"}},
 {"type": "file", "file": {"filename": "r.pdf", "file_data": "data:application/pdf;base64,JVBERi0xLjQK"}},
 {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "JVBERi0xLjQK"}},
 {"type": "thinking", "thinking": "ignored"}]
```
`calculate_input_tokens(content, FakeEncoder()) == 5 + 85 + 85 + 1400 + 1400 + 0 == 2975`.
Alternative 1 raises `KeyError: 'image_url'`; alternative 2 totals `5+1024+1024+2048+2048+0`;
alternative 3 raises on the `"thinking"` block; alternative 4 gives a payload-derived number.

**Arbitrary:** chosen value (`1400` tokens per document — no file in the repository suggests it,
and it is not any published OpenAI number) + policy with no local evidence (unknown block types
cost zero and are tolerated; anthropic-shaped blocks are priced by the OpenAI estimator rather
than rejected).

---

### P10 — A path that is neither http(s) nor an existing file is refused

**Behaviour.** `BaseType.is_remote` is true iff `url` starts with `http://` or `https://`
(case-insensitive). `_canonical_attachment_block` treats a remote URL as `source == "url"`; any
other non-empty `url` must exist as a file (`BaseType.is_local`), and when it does not,
`MissingLocalAttachment(url=data.url)` is raised — **before** the MIME check of P3, so a path
that is both missing and unguessable reports the missing file. An attachment with inline
`content` and no `url` is never subject to this check.

**Alternatives a competent engineer would plausibly choose instead.**
1. *Anything not local is remote* — `if data.url and not data.is_local: -> url block`, exactly
   `base_online_request_processor.py:138`, which quietly ships `/tmp/typo.png` to the provider as
   a URL.
2. *Raise `FileNotFoundError`* (or a bare `ValueError`), the natural exception for a missing
   path, with no `.url` attribute and no shared `AttachmentError` base.
3. *Widen the remote test* to any `scheme://` (`urlparse(url).scheme != ""`), admitting `s3://`,
   `gs://` and `data:` as remote.
4. *Check MIME first*, since MIME resolution already happened on the model and is the cheaper
   test.

**The observable.** `pytest.raises(MissingLocalAttachment)` around
`StubOnline()._canonical_attachment_block(Image(url="/tmp/definitely-missing/typo.png"))`, with
`exc.url == "/tmp/definitely-missing/typo.png"` and `isinstance(exc, AttachmentError)`.
Alternative 1 returns `{"type": "image_url", "image_url": {"url": "/tmp/definitely-missing/typo.png",
"detail": "auto"}}`; alternative 2 fails the `isinstance` and the `.url` attribute.
Ordering discriminator against alternative 4: `File(url="/tmp/definitely-missing/notes")` — no
extension, no file — raises `MissingLocalAttachment`, **not** `UnknownAttachmentMimeType`.
Scheme discriminator against alternative 3: `File(url="s3://bucket/report.pdf")` raises
`MissingLocalAttachment` with `exc.url == "s3://bucket/report.pdf"` (alternative 3 renders a
`file_url` block).

**Arbitrary:** invented name (`MissingLocalAttachment` with `.url`) + policy with no local
evidence (http/https is the whole definition of remote; missing-file beats unknown-MIME in the
check order).

---

## End to end

**Setup.** `tmp/report.pdf` contains the 9 bytes `b"%PDF-1.4\n"`
(`base64` → `"JVBERi0xLjQK"`, `get_base64_size("JVBERi0xLjQK")` → `8.58306884765625e-06`).

```python
stub = StubOnline()                      # file_upload_limit_check appends to stub.calls
prompt = _MultiModalPrompt(
    texts=["Summarise these"],
    images=[Image(url="https://cdn.example.com/photos/cat.jpeg?size=large")],
    files=[File(url=str(tmp / "report.pdf"))],
)
content = stub._handle_multi_modal_prompt(prompt)
```

**Models after construction.**
```python
prompt.images[0].mime_type == "image/jpeg"      # query stripped before guessing (P2)
prompt.files[0].mime_type  == "application/pdf"
[a.type for a in prompt.attachments()] == ["image", "file"]
```

**Canonical blocks** (`[stub._canonical_attachment_block(a) for a in prompt.attachments()]`):
```python
AttachmentBlock(kind="image", source="url", mime_type="image/jpeg",
                payload="https://cdn.example.com/photos/cat.jpeg?size=large",
                filename="cat.jpeg", detail="auto", size_mb=None)
AttachmentBlock(kind="document", source="base64", mime_type="application/pdf",
                payload="JVBERi0xLjQK", filename="report.pdf", detail=None,
                size_mb=8.58306884765625e-06)
```

**`content`, exactly:**
```python
[
    {"type": "image_url",
     "image_url": {"url": "https://cdn.example.com/photos/cat.jpeg?size=large",
                   "detail": "auto"}},
    {"type": "file",
     "file": {"filename": "report.pdf",
              "file_data": "data:application/pdf;base64,JVBERi0xLjQK"}},
    {"type": "text", "text": "Summarise these"},
]
```

**Side effects and derived values.**
```python
stub.calls == ["JVBERi0xLjQK"]                  # the URL image was never offered (P4)
calculate_input_tokens(content, FakeEncoder()) == 85 + 1400 + 15 == 1500
```

**Same prompt, anthropic renderer** (`[_render_anthropic_block(b) for b in blocks]` plus the text
block, in the same P6 order):
```python
[
    {"type": "image", "source": {"type": "url",
                                 "url": "https://cdn.example.com/photos/cat.jpeg?size=large"}},
    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                    "data": "JVBERi0xLjQK"}},
    {"type": "text", "text": "Summarise these"},
]
```

**One rejection, end to end.** Replacing the file with `File(url=str(tmp / "notes"))` (an existing
extension-less file) raises `UnknownAttachmentMimeType` with `attachment_type == "file"`;
replacing it with `File(url="/tmp/definitely-missing/notes")` raises `MissingLocalAttachment`
with `.url == "/tmp/definitely-missing/notes"`; in both cases `stub.calls == []`, because the
image was remote and the file never reached the hook.

---

## Cannot be specified

**The batch path (`openai_batch_request_processor.py:66`).** That processor advertises
`_multimodal_prompt_supported = True`, but `_unpack_multimodal` lives on
`BaseOnlineRequestProcessor` (`base_online_request_processor.py:110`) and is called from exactly
one place, the online request loop (`base_online_request_processor.py:368`), so the batch path
writes the raw `_MultiModalPrompt` dump into `requests_*.jsonl`. This is a real defect and the
obvious home for canonical blocks. It is left out of this specification because the honest test
for it — that a batch request file contains rendered blocks — needs
`OpenAIBatchRequestProcessor.__init__`, which constructs an `AsyncOpenAI` client and a working
directory, and the paths that would exercise it (`create_request_files` →
`submit_batch`) are network-bound. Any smaller test would assert that a method was moved rather
than that the batch payload changed, which grades a refactor, not a behaviour. Everything above
is exercised through pure calls on `_MultiModalPrompt`, `_canonical_attachment_block`, the two
module-level renderers, and `calculate_input_tokens`.
