Multimodal attachments: what block an image or a non-image file becomes on the way
to a provider, who is allowed to reject one for being too big, and what one costs.

The area, concretely:
- `src/bespokelabs/curator/types/prompt.py` — two MIME policies, twenty lines apart.
  `Image.model_post_init` (line 87) ends `self.mime_type = mime_type.lower() if
  mime_type else "image/png"`: an unguessable type becomes a default, and warns.
  `File.set_mime_type` (line 103) ends `return mime_type.lower() if mime_type else
  None`: the same situation yields nothing, and says nothing.
- `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py`
  — `_format_multimodal` (line 134) emits `{"type": "image_url", ...}` for `Image`
  and `File` alike, having first done `mime_type = mime_type or "image/png"`
  (line 136), so a `File` whose MIME could not be guessed is formatted as a PNG.
  `_handle_multi_modal_prompt` (line 159) feeds both lists through it.
- The provider subclasses disagree about the block vocabulary:
  `anthropic_online_request_processor.py` (lines 111-128) always emits
  `{"type": "image", ...}` with `media_type` and never a document block;
  `litellm_online_request_processor.py` (line 169) picks `"image" if "image" in
  mime_type else "document"`; the openai path inherits the base. Remote URLs take a
  different shape again in each.
- Three size checks that between them cover very little: anthropic's (lines 199-205,
  against `_ANTHROPIC_ALLOWED_IMAGE_SIZE_MB = 20`), openai's (lines 250-254), and
  litellm's (lines 138-145), which is gated on `self.config.model.split("/")[0]`
  against a `{"openai": 20}` table — so `"openai/gpt-4o"` is checked and `"gpt-4o"`
  is not. All three are reached only from the base64 branch, so a remote URL is never
  checked by any of them. The size itself is approximated from the base64 length in
  `file_utilities.py` (lines 25-29).
- `src/bespokelabs/curator/request_processor/openai_request_mixin.py` —
  `calculate_input_tokens` (lines 9-24) assumes every non-text block is
  `msg["image_url"]` and charges a flat 85 tokens, so an anthropic-shaped or
  `document` block raises `KeyError`. Anthropic charges a flat 1024; litellm declares
  1024 for an image and 2048 for a document.
- `openai_batch_request_processor.py:66` declares multimodal support, but the
  unpacking (`_unpack_multimodal`) exists only on the online base and is called only
  from there, so the batch path serializes the raw prompt object.

Nothing states whether there is one canonical block vocabulary that providers
translate out of or whether each provider owns its own shape; what an unguessable
MIME type should do, and whether images and non-images answer that the same way;
whether a size ceiling is per provider, per kind or global, and whether it applies to
a remote URL; or what a non-image attachment costs an estimator. Read all of it and
design one attachment-to-payload policy.

Out of scope: do not build the specification around the two one-line defects a
careful reader fixes unaided — that `File` has no `detail` attribute, and that
`split("/")[0]` misses an unprefixed model name. Grade the policy, not the typos.

Constraints: pure and deterministic, no network, no sleeping, no threads. Testable by
constructing `Image`, `File` and `_MultiModalPrompt` directly, and by driving a
concrete stub subclass of `BaseOnlineRequestProcessor` — `file_upload_limit_check` is
abstract, so the stub must supply it. A temp-directory file for the local branch and a
fake encoder object with `.encode()` are the only fixtures allowed. The suite must not
depend on `tests/integrations/test_multimodal.py`'s VCR cassettes or output hashes.
