# Canonical attachment blocks for multimodal prompts

Collapse the three per-provider `_format_multimodal` overrides into one provider-independent attachment model, rendered per provider at a single seam, and teach the OpenAI token estimator about non-image blocks.

### New module `src/bespokelabs/curator/types/attachment.py`
- `class AttachmentBlock(BaseModel)` with `model_config = ConfigDict(frozen=True)` and exactly these fields:
  - `kind: t.Literal["image", "document"]` — `"image"` iff the resolved `mime_type` starts with the literal `"image/"`, `"document"` otherwise. The Python class of the attachment is **not** consulted: a `File` pointing at `diagram.png` is `kind == "image"`, an `Image` carrying `mime_type="application/pdf"` is `kind == "document"`.
  - `source: t.Literal["url", "base64"]` — whether the attachment is passed through by reference or inlined as base64 text.
  - `mime_type: str` — always lowercase, no `;`-parameters.
  - `payload: str` — the URL when `source == "url"`, otherwise the base64 text from `BaseType.serialize()`.
  - `filename: str` — `os.path.basename(data.url.split("?", 1)[0])` when non-empty, else `_FALLBACK_ATTACHMENT_FILENAME`.
  - `detail: str | None` — `data.detail` when `kind == "image"` and the attribute exists, `"auto"` when it does not, `None` when `kind == "document"`.
  - `size_mb: float | None` — `file_utilities.get_base64_size(payload)` for a base64 block, `None` for a URL block.
- `_FALLBACK_ATTACHMENT_FILENAME: str = "attachment.bin"`.
- `class AttachmentError(ValueError)` — the base class for every attachment rejection raised out of this feature. Attachments that cannot be turned into a block are rejected by raising a subclass of it, defined in this module.
- `def normalize_mime_type(value: str | None) -> str | None` — lowercase, strip surrounding whitespace, drop everything from the first `;`; `None`/`""` map to `None`.

### `src/bespokelabs/curator/types/prompt.py`
- One MIME policy shared by `Image.model_post_init` and `File.set_mime_type`: every value, supplied or guessed, goes through `normalize_mime_type`.
- When no MIME was supplied and a `url` is present, guess with query and fragment stripped first: `mimetypes.guess_type(url.split("?", 1)[0].split("#", 1)[0])`, so `"https://cdn.example.com/photos/cat.jpeg?size=large"` resolves to `"image/jpeg"`.
- If the guess fails, `mime_type` stays `None` on **both** classes and exactly one `logger.warning` is emitted. `Image` no longer falls back to `"image/png"` for a URL; the only surviving default is an `Image` with inline `content`, no `url` and no supplied MIME, which gets `"image/png"` (matching `_pil_image_to_bytes`, which always saves PNG).
- Add `BaseType.is_remote` (a `bool` property) and `_MultiModalPrompt.attachments() -> list[BaseType]`, returning `self.images + self.files` in that order as a new list, inputs untouched.

### `base_online_request_processor.py`
- `def _render_openai_block(block: AttachmentBlock) -> dict` — module level, pure. Exactly one of:
  - image/url → `{"type": "image_url", "image_url": {"url": block.payload, "detail": block.detail}}`
  - image/base64 → `{"type": "image_url", "image_url": {"url": f"data:{block.mime_type};base64,{block.payload}", "detail": block.detail}}`
  - document/url → `{"type": "file", "file": {"filename": block.filename, "file_url": block.payload}}`
  - document/base64 → `{"type": "file", "file": {"filename": block.filename, "file_data": f"data:{block.mime_type};base64,{block.payload}"}}`
  - No other keys; `detail` is present on image blocks in **both** the URL and base64 case.
- `BaseOnlineRequestProcessor._canonical_attachment_block(self, data: BaseType) -> AttachmentBlock` — the one place an `Image`/`File` becomes a block. Each inlined base64 payload is offered to `self.file_upload_limit_check(payload)`.
- `BaseOnlineRequestProcessor._render_attachment_block(self, block: AttachmentBlock) -> dict` — the only provider seam; base implementation returns `_render_openai_block(block)`.
- `_format_multimodal(self, data, mime_type=None) -> dict` stays for back-compat as `return self._render_attachment_block(self._canonical_attachment_block(data))`; the `mime_type` argument is ignored.
- `_handle_multi_modal_prompt(self, message: _MultiModalPrompt) -> list[dict]` returns the rendered blocks for `message.attachments()` (images in list order, then files in list order) **followed by** one `{"type": "text", "text": <str>}` per entry of `texts` in list order. Length is `len(images) + len(files) + len(texts)`; a new list each call.

### Provider renderers
- `anthropic_online_request_processor.py`: delete the `_format_multimodal` override; add module-level pure `_render_anthropic_block(block) -> dict` returning `{"type": block.kind, "source": {"type": "url", "url": block.payload}}` for a URL block and `{"type": block.kind, "source": {"type": "base64", "media_type": block.mime_type, "data": block.payload}}` for a base64 one — `kind` passes through unchanged, so a PDF is a `document` block, and `detail`/`filename` never appear. Override `_render_attachment_block` to call it.
- `litellm_online_request_processor.py`: delete the `_format_multimodal` override; override `_render_attachment_block` to return `_render_anthropic_block(block)` when `self._uses_anthropic_multimodal_format()` and `_render_openai_block(block)` otherwise.

### `openai_request_mixin.py`
- Fixes a live `KeyError: 'image_url'`: every non-`text` block is currently indexed as `msg["image_url"]`.
- Add `_OPENAI_TOKENS_PER_DOCUMENT = 1400`. `calculate_input_tokens` dispatches on `block["type"]` via `.get`, never on the absence of `"text"`: `"text"` costs `len(token_encoding.encode(str(block.get("text", "")), disallowed_special=()))`; `"image_url"` and `"image"` cost `_OPENAI_TOKENS_PER_IMAGE["low"]` (85); `"file"` and `"document"` cost `_OPENAI_TOKENS_PER_DOCUMENT`; any other `"type"` costs `0` and raises nothing. A `str` message keeps its current behaviour. Returns `int`.

### Constraints
- No new dependencies, no network, no threads, no sleeps. Python `^3.10`, pydantic `>=2.9.2`.
- `_MultiModalPrompt.load`/`model_validate`, `_unpack_multimodal`, `BaseType.serialize`, `BaseType.is_local`, `_uses_anthropic_multimodal_format` are unchanged and reused.
- Tests use a `StubOnline(BaseOnlineRequestProcessor)` built without config or I/O whose `file_upload_limit_check` records or raises, a 1-token-per-character fake encoder, and `tmp_path` files.
