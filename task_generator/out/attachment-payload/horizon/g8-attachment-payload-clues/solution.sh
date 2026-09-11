#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
index c5e4c90..e1b148b 100644
--- a/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/anthropic_online_request_processor.py
@@ -13,6 +13,7 @@ from bespokelabs.curator.cost import cost_processor_factory
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
+from bespokelabs.curator.types.attachment import AttachmentBlock
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse, _TokenUsage
 
@@ -30,6 +31,20 @@ _MULTIMODAL_SUPPORTED_PREFIXES = (
 _ANTHROPIC_ALLOWED_IMAGE_SIZE_MB = 20  # MB
 
 
+def _render_anthropic_block(block: AttachmentBlock) -> dict:
+    """Render a canonical attachment block in the Anthropic content vocabulary."""
+    if block.source == "url":
+        return {"type": block.kind, "source": {"type": "url", "url": block.payload}}
+    return {
+        "type": block.kind,
+        "source": {
+            "type": "base64",
+            "media_type": block.mime_type,
+            "data": block.payload,
+        },
+    }
+
+
 class AnthropicOnlineRequestProcessor(BaseOnlineRequestProcessor):
     """Anthropic-specific implementation of the OnlineRequestProcessor.
 
@@ -108,24 +123,9 @@ class AnthropicOnlineRequestProcessor(BaseOnlineRequestProcessor):
 
         return response.headers
 
-    def _format_multimodal(self, data, mime_type="image/png"):
-        """Format multimodal prompt data for API request."""
-        mime_type = mime_type or "image/png"
-        if data.url and not data.is_local:
-            return {"type": "image", "source": {"type": "url", "url": data.url}}
-        else:
-            base64_content = data.serialize()
-            self.file_upload_limit_check(base64_content)
-
-            content = {
-                "type": "image",
-                "source": {
-                    "type": "base64",
-                    "media_type": mime_type,
-                    "data": base64_content,
-                },
-            }
-            return content
+    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
+        """Render a canonical attachment block for the Anthropic API."""
+        return _render_anthropic_block(block)
 
     def get_header_based_rate_limits(self) -> tuple[int, _TokenUsage]:
         """Get rate limits from Anthropic API headers.
diff --git a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
index 085c2ec..4d1bc6f 100644
--- a/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/base_online_request_processor.py
@@ -17,6 +17,7 @@ from dataclasses import dataclass, field
 import aiofiles
 import aiohttp
 
+from bespokelabs.curator.file_utilities import get_base64_size
 from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
 from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP
@@ -24,14 +25,52 @@ from bespokelabs.curator.request_processor.base_request_processor import BaseReq
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
 from bespokelabs.curator.request_processor.event_loop import run_in_event_loop
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
+from bespokelabs.curator.types.attachment import (
+    _ATTACHMENT_COUNT_LIMIT,
+    _ATTACHMENT_PROMPT_LIMIT_MB,
+    _ATTACHMENT_SIZE_LIMIT_MB,
+    _FALLBACK_ATTACHMENT_FILENAME,
+    _MAX_ATTACHMENT_FILENAME_LEN,
+    AttachmentBlock,
+    AttachmentTooLarge,
+    EmptyAttachment,
+    MissingLocalAttachment,
+    TooManyAttachments,
+    UnknownAttachmentMimeType,
+    attachment_fingerprint,
+    normalize_detail,
+    normalize_mime_type,
+)
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
-from bespokelabs.curator.types.prompt import _MultiModalPrompt
+from bespokelabs.curator.types.prompt import BaseType, _MultiModalPrompt
 from bespokelabs.curator.types.token_usage import _TokenUsage
 
 _MAX_OUTPUT_MVA_WINDOW = 50
 
 
+def _attachment_filename(url: str) -> str:
+    """Derive a capped filename from an attachment url."""
+    name = os.path.basename(url.split("?", 1)[0]) or _FALLBACK_ATTACHMENT_FILENAME
+    if len(name) <= _MAX_ATTACHMENT_FILENAME_LEN:
+        return name
+    ext = os.path.splitext(name)[1]
+    if len(ext) >= _MAX_ATTACHMENT_FILENAME_LEN:
+        return name[:_MAX_ATTACHMENT_FILENAME_LEN]
+    return name[: _MAX_ATTACHMENT_FILENAME_LEN - len(ext)] + ext
+
+
+def _render_openai_block(block: AttachmentBlock) -> dict:
+    """Render a canonical attachment block in the OpenAI content vocabulary."""
+    if block.kind == "image":
+        url = block.payload if block.source == "url" else f"data:{block.mime_type};base64,{block.payload}"
+        return {"type": "image_url", "image_url": {"url": url, "detail": block.detail}}
+
+    if block.source == "url":
+        return {"type": "file", "file": {"filename": block.filename, "file_url": block.payload}}
+    return {"type": "file", "file": {"filename": block.filename, "file_data": f"data:{block.mime_type};base64,{block.payload}"}}
+
+
 @dataclass
 class APIRequest:
     """Stores an API request's inputs, outputs, and other metadata.
@@ -131,36 +170,102 @@ class BaseOnlineRequestProcessor(BaseRequestProcessor, ABC):
         """Check if the image size is within the allowed limit."""
         pass
 
-    def _format_multimodal(self, data, mime_type="image/png"):
-        """Format multimodal prompt data for API request."""
-        mime_type = mime_type or "image/png"
-        if data.url and not data.is_local:
-            return {"type": "image_url", "image_url": {"url": data.url}}
-        else:
-            base64_content = data.serialize()
-            self.file_upload_limit_check(base64_content)
-
-            content = {
-                "type": "image_url",
-                "image_url": {
-                    "url": f"data:{mime_type};base64,{base64_content}",
-                },
-            }
-            if "image" in mime_type:
-                content["image_url"].update({"detail": data.detail})
-            return content
-
-    def _handle_multi_modal_prompt(self, message):
-        content = []
-        texts = message.texts
-
-        for text in texts:
-            content.append({"type": "text", "text": text})
-        for image in message.images:
-            content.append(self._format_multimodal(image, mime_type=image.mime_type))
-        for file in message.files:
-            content.append(self._format_multimodal(file, mime_type=file.mime_type))
+    def _canonical_attachment_block(self, data: BaseType) -> AttachmentBlock:
+        """Convert an attachment into its provider-independent block.
+
+        Args:
+            data (BaseType): The ``Image`` or ``File`` to convert.
+
+        Returns:
+            AttachmentBlock: The canonical description of the attachment.
+
+        Raises:
+            MissingLocalAttachment: If the url is neither remote nor an existing file.
+            UnknownAttachmentMimeType: If the MIME type could not be resolved.
+            EmptyAttachment: If the attachment serializes to an empty payload.
+            AttachmentTooLarge: If the payload is over the ceiling for its kind.
+        """
+        if data.url and not data.is_remote and not data.is_local:
+            raise MissingLocalAttachment(data.url)
+
+        mime_type = normalize_mime_type(data.mime_type)
+        if mime_type is None:
+            raise UnknownAttachmentMimeType(data.url, data.type)
+
+        kind = "image" if mime_type.startswith("image/") else "document"
+        detail = normalize_detail(getattr(data, "detail", "auto")) if kind == "image" else None
+        filename = _attachment_filename(data.url)
+
+        if data.is_remote:
+            return AttachmentBlock(
+                kind=kind,
+                source="url",
+                mime_type=mime_type,
+                payload=data.url,
+                filename=filename,
+                detail=detail,
+                size_mb=None,
+                fingerprint=attachment_fingerprint(data.url),
+            )
+
+        payload = data.serialize()
+        if not payload:
+            raise EmptyAttachment(data.url, filename)
+
+        size_mb = get_base64_size(payload)
+        limit_mb = _ATTACHMENT_SIZE_LIMIT_MB[kind]
+        if size_mb > limit_mb:
+            raise AttachmentTooLarge(kind, size_mb, limit_mb)
+        self.file_upload_limit_check(payload)
+
+        return AttachmentBlock(
+            kind=kind,
+            source="base64",
+            mime_type=mime_type,
+            payload=payload,
+            filename=filename,
+            detail=detail,
+            size_mb=size_mb,
+            fingerprint=attachment_fingerprint(payload),
+        )
+
+    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
+        """Render a canonical attachment block for this provider."""
+        return _render_openai_block(block)
+
+    def _format_multimodal(self, data, mime_type=None):
+        """Format multimodal prompt data for API request.
+
+        Note:
+            ``mime_type`` is ignored, the attachment carries its own MIME type.
+        """
+        return self._render_attachment_block(self._canonical_attachment_block(data))
+
+    def _handle_multi_modal_prompt(self, message: _MultiModalPrompt) -> list[dict]:
+        """Render a multimodal prompt as a content list, attachments before texts.
+
+        Args:
+            message (_MultiModalPrompt): The prompt to render.
+
+        Returns:
+            list[dict]: One block per attachment, then one block per text.
+
+        Raises:
+            TooManyAttachments: If the prompt carries more attachments than allowed.
+            AttachmentTooLarge: If the attachments add up to more than the prompt ceiling.
+        """
+        attachments = message.attachments()
+        if len(attachments) > _ATTACHMENT_COUNT_LIMIT:
+            raise TooManyAttachments(len(attachments), _ATTACHMENT_COUNT_LIMIT)
+
+        blocks = [self._canonical_attachment_block(attachment) for attachment in attachments]
+
+        total_mb = sum(block.size_mb for block in blocks if block.source == "base64")
+        if total_mb > _ATTACHMENT_PROMPT_LIMIT_MB:
+            raise AttachmentTooLarge("prompt", total_mb, _ATTACHMENT_PROMPT_LIMIT_MB)
 
+        content = [self._render_attachment_block(block) for block in blocks]
+        content.extend({"type": "text", "text": text} for text in message.texts)
         return content
 
     @property
diff --git a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
index 276755b..676fbe3 100644
--- a/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
+++ b/src/bespokelabs/curator/request_processor/online/litellm_online_request_processor.py
@@ -10,8 +10,10 @@ from litellm import supports_response_schema
 from bespokelabs.curator.file_utilities import get_base64_size
 from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor.config import OnlineRequestProcessorConfig
-from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor
+from bespokelabs.curator.request_processor.online.anthropic_online_request_processor import _render_anthropic_block
+from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest, BaseOnlineRequestProcessor, _render_openai_block
 from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker, TokenLimitStrategy
+from bespokelabs.curator.types.attachment import AttachmentBlock
 from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
 from bespokelabs.curator.types.token_usage import _TokenUsage
@@ -161,25 +163,11 @@ class LiteLLMOnlineRequestProcessor(BaseOnlineRequestProcessor):
         model_name = (model or self.config.model).split("/", 1)[-1]
         return model_name.startswith("claude-")
 
-    def _format_multimodal(self, data, mime_type="image/png"):
-        mime_type = mime_type or "image/png"
-        if not self._uses_anthropic_multimodal_format():
-            return super()._format_multimodal(data, mime_type=mime_type)
-
-        block_type = "image" if "image" in mime_type else "document"
-        if data.url and not data.is_local:
-            return {"type": block_type, "source": {"type": "url", "url": data.url}}
-
-        base64_content = data.serialize()
-        self.file_upload_limit_check(base64_content)
-        return {
-            "type": block_type,
-            "source": {
-                "type": "base64",
-                "media_type": mime_type,
-                "data": base64_content,
-            },
-        }
+    def _render_attachment_block(self, block: AttachmentBlock) -> dict:
+        """Render a canonical attachment block in the vocabulary the model expects."""
+        if self._uses_anthropic_multimodal_format():
+            return _render_anthropic_block(block)
+        return _render_openai_block(block)
 
     @staticmethod
     def _has_anthropic_pdf_document(messages: list[dict]) -> bool:
diff --git a/src/bespokelabs/curator/request_processor/openai_request_mixin.py b/src/bespokelabs/curator/request_processor/openai_request_mixin.py
index 23cf81e..d7b839e 100644
--- a/src/bespokelabs/curator/request_processor/openai_request_mixin.py
+++ b/src/bespokelabs/curator/request_processor/openai_request_mixin.py
@@ -4,6 +4,7 @@ from bespokelabs.curator.types.generic_request import GenericRequest
 
 # TODO: Add logic for high res detailed images
 _OPENAI_TOKENS_PER_IMAGE = {"low": 85}
+_OPENAI_TOKENS_PER_DOCUMENT = 1400
 
 
 def calculate_input_tokens(message, token_encoding) -> int:
@@ -13,13 +14,14 @@ def calculate_input_tokens(message, token_encoding) -> int:
     else:
         tokens = 0
         for msg in message:
-            if msg["type"] == "text":
-                msg = msg["text"]
-                tokens += len(token_encoding.encode(str(msg), disallowed_special=()))
-            else:
-                msg = msg["image_url"]
+            block_type = msg.get("type")
+            if block_type == "text":
+                tokens += len(token_encoding.encode(str(msg.get("text", "")), disallowed_special=()))
+            elif block_type in ("image_url", "image"):
                 # Note: Currently estimating low res image tokens. Need to add logic for high res images
                 tokens += _OPENAI_TOKENS_PER_IMAGE["low"]
+            elif block_type in ("file", "document"):
+                tokens += _OPENAI_TOKENS_PER_DOCUMENT
 
         return tokens
 
diff --git a/src/bespokelabs/curator/types/attachment.py b/src/bespokelabs/curator/types/attachment.py
new file mode 100644
index 0000000..bade4a0
--- /dev/null
+++ b/src/bespokelabs/curator/types/attachment.py
@@ -0,0 +1,151 @@
+"""Provider-independent description of the attachments carried by a multimodal prompt.
+
+An :class:`AttachmentBlock` is the single currency the request processors speak: the
+base processor turns every ``Image``/``File`` into one of these, and each provider only
+has to know how to render it.
+"""
+
+import hashlib
+import typing as t
+
+from pydantic import BaseModel, ConfigDict
+
+from bespokelabs.curator.log import logger
+
+_ATTACHMENT_SIZE_LIMIT_MB: dict[str, float] = {"image": 20.0, "document": 24.0}
+_ATTACHMENT_PROMPT_LIMIT_MB: float = 45.0
+_ATTACHMENT_COUNT_LIMIT: int = 12
+_FALLBACK_ATTACHMENT_FILENAME: str = "attachment.bin"
+_MAX_ATTACHMENT_FILENAME_LEN: int = 64
+_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")
+_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12
+
+
+class AttachmentBlock(BaseModel):
+    """Provider-independent description of one attachment."""
+
+    kind: t.Literal["image", "document"]
+    source: t.Literal["url", "base64"]
+    mime_type: str
+    payload: str
+    filename: str
+    detail: str | None = None
+    size_mb: float | None = None
+    fingerprint: str
+
+    model_config = ConfigDict(frozen=True)
+
+
+class AttachmentError(ValueError):
+    """Base class for every attachment rejection."""
+
+
+class UnknownAttachmentMimeType(AttachmentError):  # noqa: N818
+    """Raised when the MIME type of an attachment cannot be resolved."""
+
+    url: str
+    attachment_type: str
+
+    def __init__(self, url: str, attachment_type: str) -> None:
+        """Initialize with the attachment url and its ``BaseType.type``."""
+        self.url = url
+        self.attachment_type = attachment_type
+        super().__init__(f"Cannot determine MIME type for {attachment_type} attachment: {url!r}")
+
+
+class AttachmentTooLarge(AttachmentError):  # noqa: N818
+    """Raised when an attachment, or a whole prompt, is over its size ceiling."""
+
+    kind: str
+    size_mb: float
+    limit_mb: float
+
+    def __init__(self, kind: str, size_mb: float, limit_mb: float) -> None:
+        """Initialize with the offending kind, the measured size and the limit, in MB."""
+        self.kind = kind
+        self.size_mb = size_mb
+        self.limit_mb = limit_mb
+        super().__init__(f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit.")
+
+
+class MissingLocalAttachment(AttachmentError):  # noqa: N818
+    """Raised when an attachment path is neither a remote URL nor an existing file."""
+
+    url: str
+
+    def __init__(self, url: str) -> None:
+        """Initialize with the offending url."""
+        self.url = url
+        super().__init__(f"Attachment path is neither an http(s) URL nor an existing file: {url!r}")
+
+
+class TooManyAttachments(AttachmentError):  # noqa: N818
+    """Raised when a single message carries more attachments than the limit allows."""
+
+    count: int
+    limit: int
+
+    def __init__(self, count: int, limit: int) -> None:
+        """Initialize with the attachment count and the limit."""
+        self.count = count
+        self.limit = limit
+        super().__init__(f"Prompt has {count} attachments, over the limit of {limit}.")
+
+
+class EmptyAttachment(AttachmentError):  # noqa: N818
+    """Raised when an attachment serializes to an empty payload."""
+
+    url: str
+    filename: str
+
+    def __init__(self, url: str, filename: str) -> None:
+        """Initialize with the attachment url and its derived filename."""
+        self.url = url
+        self.filename = filename
+        super().__init__(f"Attachment {filename} has an empty payload: {url!r}")
+
+
+def normalize_mime_type(value: str | None) -> str | None:
+    """Lowercase a MIME type, strip whitespace and drop any ``;``-parameters.
+
+    Args:
+        value: The raw MIME type, if any.
+
+    Returns:
+        str | None: The normalized MIME type, or None when nothing was provided.
+    """
+    if not value:
+        return None
+    normalized = str(value).split(";", 1)[0].strip().lower()
+    return normalized or None
+
+
+def normalize_detail(value: str | None) -> str:
+    """Normalize an image detail against the supported vocabulary.
+
+    Args:
+        value: The detail requested by the caller, if any.
+
+    Returns:
+        str: One of ``_SUPPORTED_IMAGE_DETAILS``, falling back to "auto".
+    """
+    if value is None:
+        return "auto"
+    detail = str(value).strip().lower()
+    if detail in _SUPPORTED_IMAGE_DETAILS:
+        return detail
+    logger.warning(f"Unsupported image detail {value!r}, falling back to 'auto'.")
+    return "auto"
+
+
+def attachment_fingerprint(payload: str) -> str:
+    """Compute a short, stable fingerprint of an attachment payload.
+
+    Args:
+        payload: The base64 text of the attachment, or its URL.
+
+    Returns:
+        str: A ``sha256:``-prefixed, truncated hex digest of the payload string.
+    """
+    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
+    return f"sha256:{digest[:_ATTACHMENT_FINGERPRINT_HEX_LEN]}"
diff --git a/src/bespokelabs/curator/types/prompt.py b/src/bespokelabs/curator/types/prompt.py
index c3a4f3e..3a03531 100644
--- a/src/bespokelabs/curator/types/prompt.py
+++ b/src/bespokelabs/curator/types/prompt.py
@@ -9,6 +9,7 @@ from PIL import Image as PIL_Image
 from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator
 
 from bespokelabs.curator.log import logger
+from bespokelabs.curator.types.attachment import normalize_mime_type
 
 
 class BaseType(BaseModel):
@@ -34,6 +35,17 @@ class BaseType(BaseModel):
             return self._is_local_uri(self.url)
         return False
 
+    @property
+    def is_remote(self):
+        """Check if the attachment is served over http(s)."""
+        return self.url.lower().startswith(("http://", "https://"))
+
+    @staticmethod
+    def _guess_mime_type(url):
+        """Guess the MIME type of a url, ignoring its query and fragment."""
+        mime_type, _ = mimetypes.guess_type(url.split("?", 1)[0].split("#", 1)[0])
+        return normalize_mime_type(mime_type)
+
 
 def _pil_image_to_bytes(image: PIL_Image.Image) -> bytes:
     buffer = BytesIO()
@@ -86,26 +98,37 @@ class Image(BaseType):
 
     def model_post_init(self, __context):
         """Run after initialization."""
-        if self.mime_type is None and self.url:
-            mime_type, _ = mimetypes.guess_type(self.url)
-            if not mime_type:
-                logger.warning(f"Failed to guess MIME type for {self.url}.")
-            self.mime_type = mime_type.lower() if mime_type else "image/png"
+        mime_type = normalize_mime_type(self.mime_type)
+        if mime_type is None:
+            if self.url:
+                mime_type = self._guess_mime_type(self.url)
+                if mime_type is None:
+                    logger.warning(f"Failed to guess MIME type for {self.url}.")
+            else:
+                # Inline content is always PNG, see `_pil_image_to_bytes`.
+                mime_type = "image/png"
+        self.mime_type = mime_type
 
 
 class File(BaseType):
     """A class to represent a file for multimodal prompts."""
 
+    # `validate_default` so that an omitted MIME type is guessed from the url too.
+    mime_type: str | None = Field(None, validate_default=True, description="The MIME type of the file.")
+
     type: t.ClassVar[str] = "file"
 
     @field_validator("mime_type", mode="before")
     @classmethod
     def set_mime_type(cls, value, values):
         """Set MIME type if not provided."""
-        if value is None and "url" in values.data:
-            mime_type, _ = mimetypes.guess_type(values.data["url"])
-            return mime_type.lower() if mime_type else None
-        return value
+        mime_type = normalize_mime_type(value)
+        if mime_type is None and values.data.get("url"):
+            url = values.data["url"]
+            mime_type = cls._guess_mime_type(url)
+            if mime_type is None:
+                logger.warning(f"Failed to guess MIME type for {url}.")
+        return mime_type
 
     def serialize(self) -> str:
         """Convert file to base64."""
@@ -121,6 +144,10 @@ class _MultiModalPrompt(BaseType):
     images: t.List[Image] = Field(default_factory=list, description="The images of the prompt.")
     files: t.List[File] = Field(default_factory=list, description="The files of the prompt.")
 
+    def attachments(self) -> t.List[BaseType]:
+        """Return every attachment of the prompt, images first, then files."""
+        return [*self.images, *self.files]
+
     @classmethod
     def load(cls, messages):
         prompt = {"texts": [], "images": [], "files": []}
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
