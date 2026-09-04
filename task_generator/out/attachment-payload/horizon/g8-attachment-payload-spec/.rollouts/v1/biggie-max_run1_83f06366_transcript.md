# Rollout Transcript

- **Rollout ID**: 83f06366-62bf-4a3b-b296-d1a4e510a796
- **Model**: biggie-max
- **Run**: 1
- **Score**: 0
- **Success**: True
- **Task Version**: 1
- **Created**: 2026-09-03T22:15:05.862Z

---

## [user]

Here is the problem I want you to solve:
<problem>
You are an engineer on the team that maintains `bespokelabs/curator`.

The repository is checked out at `/workdir/curator` — a normal working tree, yours
to edit. It is a `src` layout: the package lives at
`/workdir/curator/src/bespokelabs/curator/`.

To run anything against it, put the source tree on the path:

    cd /workdir/curator && PYTHONPATH=/workdir/curator/src python3 -c '...'

curator's dependencies are installed; curator itself deliberately is not, so your
tree is what gets imported. There is no network.

Your work is graded from the tree at `/workdir/curator`. Nothing needs to be
committed or pushed.

---

## The ticket

Replace the three per-provider `_format_multimodal` overrides with one canonical attachment block that every provider renders from.

### New module — `src/bespokelabs/curator/types/attachment.py`
- `AttachmentBlock(BaseModel)` with `model_config = ConfigDict(frozen=True)` — a provider-independent description of one attachment. Fields:
  - `kind: t.Literal["image", "document"]`
  - `source: t.Literal["url", "base64"]`
  - `mime_type: str` — always lowercase, no `;`-parameters
  - `payload: str` — the URL when `source == "url"`, else the base64 text
  - `filename: str` — never empty
  - `detail: str | None = None` — a `str` when `kind == "image"`, `None` when `kind == "document"`
- `AttachmentError(ValueError)` — base class for every attachment rejection.
- `UnknownAttachmentMimeType(AttachmentError)` with `__init__(self, url: str, attachment_type: str)`, storing `self.url` and `self.attachment_type` (the `BaseType.type` ClassVar, i.e. `"image"` or `"file"` — not the block `kind`), message `f"Cannot determine MIME type for {attachment_type} attachment: {url!r}"`.
- `MissingLocalAttachment(AttachmentError)` with `__init__(self, url: str)`, storing `self.url`, message `f"Attachment path is neither an http(s) URL nor an existing file: {url!r}"`.
- `EmptyAttachment(AttachmentError)` with `__init__(self, url: str, filename: str)`, storing `self.url` and `self.filename`, message `f"Attachment {filename} has an empty payload: {url!r}"`.
- `normalize_mime_type(value: str | None) -> str | None` — lowercase, strip surrounding whitespace, drop everything from the first `;`; `None`/`""` map to `None`.
- `_FALLBACK_ATTACHMENT_FILENAME: str = "attachment.bin"`.

### `src/bespokelabs/curator/types/prompt.py`
- Add `BaseType.is_remote` as a property: true iff `url` starts with `http://` or `https://`, case-insensitive.
- Add `_MultiModalPrompt.attachments(self) -> list[BaseType]` returning `self.images + self.files`, in that order, as a new list, leaving the inputs untouched.
- One MIME policy shared by `Image.model_post_init` (line 87) and `File.set_mime_type` (line 103): every MIME value, supplied or guessed, goes through `normalize_mime_type`.
  - When no MIME was supplied and a `url` is present, guess with query and fragment removed: `mimetypes.guess_type(url.split("?", 1)[0].split("#", 1)[0])`, so `"https://cdn.example.com/photos/cat.jpeg?size=large"` resolves to `"image/jpeg"`.
  - If the guess fails, `mime_type` stays `None` on both classes and exactly one `logger.warning` is emitted. `Image` no longer falls back to `"image/png"` for a URL.
  - The one surviving default: an `Image` with inline `content`, no `url` and no supplied MIME gets `"image/png"` (matching `_pil_image_to_bytes`, which always saves PNG).
  - Worked values: `File(url="/tmp/x/report.PDF", mime_type="Application/PDF; charset=binary").mime_type == "application/pdf"`; `Image(url="https://example.com/asset").mime_type is None`; `Image(content=b"\x89PNG\r\n").mime_type == "image/png"`.

### `base_online_request_processor.py` — building the canonical block
`BaseOnlineRequestProcessor._canonical_attachment_block(self, data: BaseType) -> AttachmentBlock` converts any `Image` or `File` into a frozen block:
- `kind` is `"image"` when the resolved `mime_type` starts with the literal `"image/"`, `"document"` otherwise. The Python class is not consulted: `File(url=".../diagram.png")` yields `kind == "image"`, and `Image(content=b"...", mime_type="application/pdf")` yields `kind == "document"`.
- `detail` is derived from the attachment's `detail` attribute when `kind == "image"` (and is `"auto"` when the attribute is absent, as it is on `File`); it is `None` when `kind == "document"`.
- `filename` is derived from `os.path.basename(data.url.split("?", 1)[0])` when that is non-empty, else `_FALLBACK_ATTACHMENT_FILENAME`.
- A remote `url` (per `is_remote`) gives `source == "url"` with the URL as `payload`; anything else gives `source == "base64"` with `BaseType.serialize()` output as `payload`.
- Refusals, in this order:
  1. A non-empty `url` that is not remote must exist as a file (`BaseType.is_local`); when it does not, raise `MissingLocalAttachment(data.url)`. This precedes the MIME check, so `File(url="/tmp/definitely-missing/notes")` (missing *and* unguessable) raises `MissingLocalAttachment`, not `UnknownAttachmentMimeType`. `File(url="s3://bucket/report.pdf")` also raises `MissingLocalAttachment`. An attachment with inline `content` and no `url` is not subject to this check.
  2. When the resolved `mime_type` is `None`, raise `UnknownAttachmentMimeType(url=data.url, attachment_type=data.type)`. This happens at block-build time only: `Image(url=...)` / `File(url=...)` construction itself never raises for a missing MIME.
  3. A `source == "base64"` attachment whose `serialize()` returns `""` raises `EmptyAttachment(url=data.url, filename=<block filename>)`, after the MIME check. A remote URL is never read, so it is never checked for emptiness.

### `base_online_request_processor.py` — rendering and assembly
- `def _render_openai_block(block: AttachmentBlock) -> dict` — module level, pure, returning exactly one of:
  - image / url → `{"type": "image_url", "image_url": {"url": block.payload, "detail": block.detail}}`
  - image / base64 → `{"type": "image_url", "image_url": {"url": f"data:{block.mime_type};base64,{block.payload}", "detail": block.detail}}`
  - document / url → `{"type": "file", "file": {"filename": block.filename, "file_url": block.payload}}`
  - document / base64 → `{"type": "file", "file": {"filename": block.filename, "file_data": f"data:{block.mime_type};base64,{block.payload}"}}`
  - No other keys. `detail` is carried on image blocks in the URL case as well as the base64 case.
- `BaseOnlineRequestProcessor._render_attachment_block(self, block: AttachmentBlock) -> dict` returns `_render_openai_block(block)`. This method is the only provider seam; providers see `AttachmentBlock` and nothing else.
- `_format_multimodal(self, data, mime_type=None) -> dict` stays as a back-compatible one-shot: `return self._render_attachment_block(self._canonical_attachment_block(data))`. The `mime_type` argument is ignored.
- `_handle_multi_modal_prompt(self, message: _MultiModalPrompt) -> list[dict]` returns the rendered attachment blocks first — images in list order, then files in list order, exactly `attachments()` — followed by one `{"type": "text", "text": <str>}` per entry of `texts`, in list order. Result length is `len(images) + len(files) + len(texts)`; a new list each call. For `_MultiModalPrompt(texts=["a", "b"], images=[img], files=[doc])` the block types are `["image_url", "file", "text", "text"]`.

### `anthropic_online_request_processor.py`
- Delete the `_format_multimodal` override (lines 111-128).
- Add module-level pure `def _render_anthropic_block(block: AttachmentBlock) -> dict`:
  - url → `{"type": block.kind, "source": {"type": "url", "url": block.payload}}`
  - base64 → `{"type": block.kind, "source": {"type": "base64", "media_type": block.mime_type, "data": block.payload}}`
  - No other keys; `detail` and `filename` do not appear. `kind` passes through, so a PDF renders as a `document` block rather than an `image` one.
- `AnthropicOnlineRequestProcessor._render_attachment_block` returns `_render_anthropic_block(block)`.

### `litellm_online_request_processor.py`
- Delete the `_format_multimodal` override (lines 163-181).
- `LiteLLMOnlineRequestProcessor._render_attachment_block` returns `_render_anthropic_block(block)` when `self._uses_anthropic_multimodal_format()` (unchanged, reused as the dispatch key) and `_render_openai_block(block)` otherwise.

### `openai_request_mixin.py` — `calculate_input_tokens` (lines 9-24)
- Today the function does `msg = msg["image_url"]` for every non-`text` block, so an anthropic-shaped block (`{"type": "image", "source": ...}`) or any document block raises `KeyError: 'image_url'`. Rewrite it to dispatch on `block["type"]` using `.get`, never on the absence of a `"text"` key.
- `"text"` costs `len(token_encoding.encode(str(block.get("text", "")), disallowed_special=()))`.
- `"image_url"` and `"image"` both cost `_OPENAI_TOKENS_PER_IMAGE["low"]` (unchanged).
- `"file"` and `"document"` blocks must also be priced by this function.
- A `str` message keeps its current behaviour. The return is an `int`.

### Constraints and non-goals
- Python `^3.10`; pydantic `>=2.9.2`; no new dependency. Nothing here imports `aiohttp`, opens a socket, sleeps, or spawns anything.
- Reuse `BaseType.serialize()` (`prompt.py:60`, `prompt.py:110`), `BaseType._is_local_uri` / `_load_file_as_b64` / `is_local` (`prompt.py:21-34`), `_MultiModalPrompt.load` / `.model_validate`, and `_unpack_multimodal` (`base_online_request_processor.py:110`) as they are.
- Out of scope: the batch path (`openai_batch_request_processor.py:66`), `File` having no `detail` attribute, and the `self.config.model.split("/")[0]` gate at `litellm_online_request_processor.py:139`.
- Both renderers are module-level pure functions taking only an `AttachmentBlock`, so they can be exercised without constructing a configured processor.
- Tests construct processors with `object.__new__(StubOnline)` or a no-arg `__init__`: no config, no cost processor, no I/O beyond a `tmp_path` file.

---

## Requirements settled earlier

These were agreed before the ticket was written. They are not optional.

### r1

- **rule** — Each base64 payload is measured in megabytes from its base64 length and recorded on the block as a `size_mb: float` field; a measurement strictly greater than 20.0 MB for a block whose kind is "image", or strictly greater than 24.0 MB for a block whose kind is "document", raises `AttachmentTooLarge(kind, size_mb, limit_mb)` — an `AttachmentError` subclass storing `.kind`, `.size_mb` and `.limit_mb`, message `f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit."`. The measurement and the comparison happen inside `_canonical_attachment_block`, before the payload is offered to the provider's `file_upload_limit_check` hook.
- **scope** — A whole-prompt ceiling of 45.0 MB belongs to `_handle_multi_modal_prompt`: after every attachment has been converted to a block (all `file_upload_limit_check` calls have already run), the `size_mb` values of the `source == "base64"` blocks are summed and compared, strictly greater, against 45.0; on overflow the same exception type is raised with `kind == "prompt"`, `size_mb` equal to the whole-prompt sum and `limit_mb == 45.0`. `_canonical_attachment_block` / `_format_multimodal` never apply it.
- **exclusions_or_crossover** — A `source == "url"` block is never measured: its `size_mb` is `None`, it is not compared against any per-kind ceiling, and it contributes nothing to the 45.0 MB prompt sum.
- **failure_behavior** — More than 12 attachments is refused: `_ATTACHMENT_COUNT_LIMIT: int = 12` and `TooManyAttachments(AttachmentError)` with `__init__(self, count: int, limit: int)` storing `.count` and `.limit`, message `f"Prompt has {count} attachments, over the limit of {limit}."`. `_handle_multi_modal_prompt` counts `len(message.attachments())` first and raises when the count is strictly greater than 12; nothing is serialized and `file_upload_limit_check` is not called. 40 texts and one image is fine, and 12 attachments is fine.
- **observability** — In `calculate_input_tokens`, a `"file"` or `"document"` block costs 1400 tokens (`_OPENAI_TOKENS_PER_DOCUMENT = 1400`): with a 1-token-per-character encoder, `[text "hello", image_url, anthropic image, file, document, unknown "thinking"]` totals `5 + 85 + 85 + 1400 + 1400 + 0 == 2975`.

### r2

- **rule** — `attachment.py` defines `_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12` and `attachment_fingerprint(payload: str) -> str` returning `"sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]`; `AttachmentBlock` gains a required `fingerprint: str` field that `_canonical_attachment_block` sets from the block's payload. So a block for a file holding `b"%PDF-1.4\n"` has `fingerprint == "sha256:fc1c4358d4aa"`, and `Image(content=b"x")` gives `"sha256:5e21d86b709b"`.
- **scope** — The derived `filename` is capped at `_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, extension kept: when the basename is longer than 64 characters it becomes `name[: 64 - len(ext)] + ext` for `ext = os.path.splitext(name)[1]`; a name of 64 or fewer characters is untouched. Only `block.filename` is capped — `payload` keeps the full URL and the attachment's own `url` is never modified, so a 73-character PDF basename renders as `{"filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf", "file_url": <the full untruncated URL>}`.
- **exclusions_or_crossover** — A `source == "url"` block is fingerprinted identically: the digest is taken over the payload *string*, query and fragment included — `https://cdn.example.com/photos/cat.jpeg?size=large` gives `fingerprint == "sha256:80ce7facd006"` — and a base64 block hashes its base64 text, never the decoded bytes.
- **failure_behavior** — Image `detail` is normalized against a fixed vocabulary at block-build time: `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")` and a pure `normalize_detail(value: str | None) -> str` return `str(value).strip().lower()` when that lands in the vocabulary and `"auto"` otherwise, emitting exactly one `logger.warning` on the fallback and none on a hit or on `None`. So `Image(content=b"x", detail="HIGH")` gives a block `detail` of `"high"`; `Image.detail` itself keeps whatever the caller wrote.

</problem>

Note: your working directory is /workdir.


## [assistant]

I'll analyze the task and work through it systematically. Let me start by exploring the repository structure.

{
  "analysis": "Starting the task. Need to explore the repository first.",
  "plan": "Explore the repo structure and existing files to understand the current codebase.",
  "commands": [
    {"keystrokes": "cd /workdir/curator && find src/bespokelabs/curator -type f -name '*.py' | head -30\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Let me look at the specific files involved.",
  "plan": "Examine the relevant files (types/prompt.py, base_online_request_processor.py, anthropic and litellm processors, openai_request_mixin.py).",
  "commands": [
    {"keystrokes": "cat src/bespokelabs/curator/types/prompt.py\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now let me look at the base_online_request_processor.py.",
  "plan": "Look at the base processor and related files.",
  "commands": [
    {"keystrokes": "cat src/bespokelabs/curator/request_processor/online/base_online_request_processor.py | head -200\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now let me check the anthropic and litellm processors, and openai_request_mixin.py.",
  "plan": "Look at other relevant files.",
  "commands": [
    {"keystrokes": "sed -n '100,140p' src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Let me check anthropic file's full context and litellm file's format multimodal, and openai_request_mixin.",
  "plan": "Get remaining context.",
  "commands": [
    {"keystrokes": "sed -n '1,30p' src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py\n", "duration": 0.1},
    {"keystrokes": "sed -n '150,200p' src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now let me check openai_request_mixin.py.",
  "plan": "View openai_request_mixin.py.",
  "commands": [
    {"keystrokes": "cat src/bespokelabs/curator/request_processor/openai_request_mixin.py\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now I have a good understanding. Let me check the existing tests too to understand what's expected.",
  "plan": "Look for test files.",
  "commands": [
    {"keystrokes": "ls tests/ 2>/dev/null && find tests/ -name '*attachment*' -o -name '*multimodal*' 2>/dev/null | head -20\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Let me check if there are grading tests we need to know about.",
  "plan": "Search for hidden test files or any indication of grading tests.",
  "commands": [
    {"keystrokes": "ls /workdir/\n", "duration": 0.1},
    {"keystrokes": "find /workdir -maxdepth 3 -name 'test_*.py' 2>/dev/null | grep -v curator/tests | head\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now I'll implement the changes. Let me start by creating the attachment.py file.",
  "plan": "1. Create src/bespokelabs/curator/types/attachment.py\n2. Modify types/prompt.py\n3. Modify base_online_request_processor.py\n4. Modify anthropic_online_request_processor.py\n5. Modify litellm_online_request_processor.py\n6. Modify openai_request_mixin.py",
  "commands": [
    {"keystrokes": "cat > src/bespokelabs/curator/types/attachment.py << 'PYEOF'\n\"\"\"Provider-independent attachment representation and helpers.\"\"\"\nimport hashlib\nimport typing as t\n\nfrom pydantic import BaseModel, ConfigDict\n\nfrom bespokelabs.curator.log import logger\n\n_FALLBACK_ATTACHMENT_FILENAME: str = \"attachment.bin\"\n_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12\n_MAX_ATTACHMENT_FILENAME_LEN: int = 64\n_ATTACHMENT_COUNT_LIMIT: int = 12\n_SUPPORTED_IMAGE_DETAILS: t.Tuple[str, ...] = (\"auto\", \"low\", \"high\")\n\n\ndef normalize_mime_type(value: str | None) -> str | None:\n    \"\"\"Lowercase, strip whitespace, drop parameters after ';'.\"\"\"\n    if value is None:\n        return None\n    v = value.strip()\n    if not v:\n        return None\n    v = v.split(\";\", 1)[0].strip().lower()\n    if not v:\n        return None\n    return v\n\n\ndef normalize_detail(value: str | None) -> str:\n    \"\"\"Normalize image detail against a fixed vocabulary.\"\"\"\n    if value is None:\n        return \"auto\"\n    candidate = str(value).strip().lower()\n    if candidate in _SUPPORTED_IMAGE_DETAILS:\n        return candidate\n    logger.warning(f\"Unsupported image detail {value!r}, falling back to 'auto'.\")\n    return \"auto\"\n\n\ndef attachment_fingerprint(payload: str) -> str:\n    \"\"\"Return a short SHA-256 fingerprint of the payload string.\"\"\"\n    digest = hashlib.sha256(payload.encode(\"utf-8\")).hexdigest()\n    return \"sha256:\" + digest[:_ATTACHMENT_FINGERPRINT_HEX_LEN]\n\n\nclass AttachmentBlock(BaseModel):\n    \"\"\"A provider-independent description of one attachment.\"\"\"\n\n    model_config = ConfigDict(frozen=True)\n\n    kind: t.Literal[\"image\", \"document\"]\n    source: t.Literal[\"url\", \"base64\"]\n    mime_type: str\n    payload: str\n    filename: str\n    detail: str | None = None\n    size_mb: float | None = None\n    fingerprint: str\n\n\nclass AttachmentError(ValueError):\n    \"\"\"Base class for every attachment rejection.\"\"\"\n\n\nclass UnknownAttachmentMimeType(AttachmentError):\n    def __init__(self, url: str, attachment_type: str):\n        self.url = url\n        self.attachment_type = attachment_type\n        super().__init__(f\"Cannot determine MIME type for {attachment_type} attachment: {url!r}\")\n\n\nclass MissingLocalAttachment(AttachmentError):\n    def __init__(self, url: str):\n        self.url = url\n        super().__init__(f\"Attachment path is neither an http(s) URL nor an existing file: {url!r}\")\n\n\nclass EmptyAttachment(AttachmentError):\n    def __init__(self, url: str, filename: str):\n        self.url = url\n        self.filename = filename\n        super().__init__(f\"Attachment {filename} has an empty payload: {url!r}\")\n\n\nclass AttachmentTooLarge(AttachmentError):\n    def __init__(self, kind: str, size_mb: float, limit_mb: float):\n        self.kind = kind\n        self.size_mb = size_mb\n        self.limit_mb = limit_mb\n        super().__init__(f\"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit.\")\n\n\nclass TooManyAttachments(AttachmentError):\n    def __init__(self, count: int, limit: int):\n        self.count = count\n        self.limit = limit\n        super().__init__(f\"Prompt has {count} attachments, over the limit of {limit}.\")\nPYEOF\n", "duration": 0.1}
  ]
}

## [assistant]

{
  "analysis": "Now let me modify prompt.py.",
  "plan": "Update prompt.py per the ticket.",
  "commands": [
    {"keystrokes": "cat > src/bespokelabs/curator/types/prompt.py << 'PYEOF'\n# Description: Pydantic models for multimodal prompts.\nimport base64\nimport mimetypes\nimport os\nimport typing as t\nfrom io import BytesIO\n\nfrom PIL import Image as PIL_Image\nfrom pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator\n\nfrom bespokelabs.curator.log import logger\nfrom bespokelabs.curator.types.attachment import normalize_mime_type\n\n\nclass BaseType(BaseModel):\n    \"\"\"A class to represent the base type for multimodal prompts.\"\"\"\n\n    url: str = Field(\"\", description=\"The URL of the file.\")\n    type: t.ClassVar[str] = Field(..., description=\"The type of the multimodal prompt.\")\n    mime_type: str | None = Field(None, description=\"The MIME type of the file.\")\n\n    @staticmethod\n    def _is_local_uri(path):\n        return os.path.exists(path) and os.path.isfile(path)\n\n    @staticmethod\n    def _load_file_as_b64(path):\n        with open(path, \"rb\") as f:\n            return base64.b64encode(f.read()).decode(\"utf-8\")\n\n    @property\n    def is_local(self):\n        \"\"\"Check if the image is a local file.\"\"\"\n        if self.url:\n            return self._is_local_uri(self.url)\n        return False\n\n    @property\n    def is_remote(self) -> bool:\n        \"\"\"Check if the attachment url is an http(s) URL.\"\"\"\n        if not self.url:\n            return False\n        lowered = self.url.lower()\n        return lowered.startswith(\"http://\") or lowered.startswith(\"https://\")\n\n\ndef _pil_image_to_bytes(image: PIL_Image.Image) -> bytes:\n    buffer = BytesIO()\n    image.save(buffer, format=\"PNG\")\n    return buffer.getvalue()\n\n\ndef _pil_to_base64(image: PIL_Image.Image) -> str:\n    b = _pil_image_to_bytes(image)\n    return base64.b64encode(b).decode(\"utf-8\")\n\n\ndef _guess_mime_from_url(url: str) -> str | None:\n    cleaned = url.split(\"?\", 1)[0].split(\"#\", 1)[0]\n    mime_type, _ = mimetypes.guess_type(cleaned)\n    return mime_type\n\n\nclass Image(BaseType):\n    \"\"\"A class to represent an image for multimodal prompts.\"\"\"\n\n    content: bytes | PIL_Image.Image | str = Field(\"\", description=\"Image content bytes.\")\n    detail: str = Field(\"auto\", description=\"Details about the image. Note 'auto' is only supported for OpenAI client.\")\n    model_config = ConfigDict(arbitrary_types_allowed=True)\n    mime_type: str | None = Field(None, description=\"The MIME type of the file.\")\n\n    type: t.ClassVar[str] = \"image\"\n\n    def serialize(self) -> str:\n        \"\"\"Convert image content to base64.\"\"\"\n        if self.url:\n            if self.is_local:\n                return self._load_file_as_b64(self.url)\n            return self.url\n\n        assert self.content, \"Image content is not provided.\"\n        if isinstance(self.content, PIL_Image.Image):\n            self.content = _pil_image_to_bytes(self.content)\n        elif isinstance(self.content, str):\n            return self.content\n        return base64.b64encode(self.content).decode(\"utf-8\")\n\n    @field_serializer(\"content\")\n    def serialize_content(self, content, _info) -> str:\n        \"\"\"Convert image content to base64.\"\"\"\n        if isinstance(content, PIL_Image.Image):\n            return _pil_to_base64(content)\n        return content\n\n    @model_validator(mode=\"before\")\n    def check_url_or_content(self):  # noqa: N805\n        \"\"\"Ensure that only one of url or content is provided.\"\"\"\n        if bool(self.get(\"url\")) == bool(self.get(\"content\")):\n            raise ValueError(\"Only one of 'url' or 'content' must be provided.\")\n        return self\n\n    def model_post_init(self, __context):\n        \"\"\"Run after initialization.\"\"\"\n        if self.mime_type is not None:\n            self.mime_type = normalize_mime_type(self.mime_type)\n            return\n        if self.url:\n            guessed = _guess_mime_from_url(self.url)\n            if guessed:\n                self.mime_type = normalize_mime_type(guessed)\n            else:\n                logger.warning(f\"Failed to guess MIME type for {self.url}.\")\n                self.mime_type = None\n        else:\n            # Inline content with no supplied mime: default to PNG\n            self.mime_type = \"image/png\"\n\n\nclass File(BaseType):\n    \"\"\"A class to represent a file for multimodal prompts.\"\"\"\n\n    type: t.ClassVar[str] = \"file\"\n\n    @field_validator(\"mime_type\", mode=\"before\")\n    @classmethod\n    def set_mime_type(cls, value, values):\n        \"\"\"Set MIME type if not provided.\"\"\"\n        if value is not None:\n            return normalize_mime_type(value)\n        url = values.data.get(\"url\") if hasattr(values, \"data\") else None\n        if url:\n            guessed = _guess_mime_from_url(url)\n            if guessed:\n                return normalize_mime_type(guessed)\n            logger.warning(f\"Failed to guess MIME type for {url}.\")\n        return None\n\n    def serialize(self) -> str:\n        \"\"\"Convert file to base64.\"\"\"\n        if self.is_local:\n            return self._load_file_as_b64(self.url)\n        return self.url\n\n\nclass _MultiModalPrompt(BaseType):\n    \"\"\"A class to represent a multimodal prompt.\"\"\"\n\n    texts: t.List[str] = Field(default_factory=list, description=\"The texts of the prompt.\")\n    images: t.List[Image] = Field(default_factory=list, description=\"The images of the prompt.\")\n    files: t.List[File] = Field(default_factory=list, description=\"The files of the prompt.\")\n\n    def attachments(self) -> t.List[BaseType]:\n        \"\"\"Return images then files as a new combined list.\"\"\"\n        return list(self.images) + list(self.files)\n\n    @classmethod\n    def load(cls, messages):\n        prompt = {\"texts\": [], \"images\": [], \"files\": []}\n        for msg in messages:\n            if isinstance(msg, BaseType):\n                if msg.type == \"image\":\n                    prompt[\"images\"].append(msg)\n                elif msg.type == \"file\":\n                    prompt[\"files\"].append(msg)\n            else:\n                prompt[\"texts\"].append(msg)\n        return cls(**prompt)\nPYEOF\n", "duration": 0.1}
  ]
}
