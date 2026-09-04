"""attachment-payload — the openly stated feature: one canonical attachment block.

Everything asserted here is written down in the ticket: the new
`types/attachment.py` module with `AttachmentBlock`, `AttachmentError`,
`UnknownAttachmentMimeType`, `MissingLocalAttachment`, `normalize_mime_type` and
`_FALLBACK_ATTACHMENT_FILENAME`; `BaseType.is_remote` and
`_MultiModalPrompt.attachments()`; the single MIME policy with its four worked
values; `_canonical_attachment_block` deciding `kind` from the MIME rather than
from the Python class; the two module-level renderers and their exact dicts;
`_format_multimodal` surviving as a one-shot; the litellm dispatch on
`_uses_anthropic_multimodal_format()`; attachments before text in
`_handle_multi_modal_prompt`; and `calculate_input_tokens` dispatching on
`block["type"]` instead of indexing `msg["image_url"]`.

Nothing here touches a hidden fact. It never mentions a size ceiling, a
`size_mb` field, an attachment count or what a document block COSTS the
estimator (r1); it never mentions a fingerprint, a filename cap or a detail
vocabulary (r2). Every payload below is a few bytes and every filename short, so
any ceiling and any cap agree; every `detail` is the default `"auto"`, which
survives normalization unchanged. Pricing a document block is asserted only to
be an int that no longer raises.

`StubOnline` and `FakeEncoder` live here because test_r1 and test_r2 import
them; they are the harness contract the specification fixes.
"""
from __future__ import annotations

import base64
import os
from types import SimpleNamespace

import pytest

# Imported defensively and re-raised per test: a missing attachment module is
# one fact failing per requirement, not three files pytest refuses to collect.
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
PDF_B64 = base64.b64encode(PDF_BYTES).decode()  # "JVBERi0xLjQK"
REMOTE_JPEG = "https://cdn.example.com/photos/cat.jpeg?size=large"


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


# =============================================================================
# the open feature
# =============================================================================
def test_open_feature__one_canonical_block_every_provider_renders_from(tmp_path):
    """The canonical layer, end to end: MIME policy, block, both renderers, order."""
    importable()
    if ATTACHMENT_IMPORT_ERROR is not None and attachment_symbol("AttachmentBlock", required=False) is None:
        pytest.fail(f"bespokelabs.curator.types.attachment could not be imported: {ATTACHMENT_IMPORT_ERROR!r}")

    AttachmentBlock = attachment_symbol("AttachmentBlock")
    AttachmentError = attachment_symbol("AttachmentError")
    UnknownAttachmentMimeType = attachment_symbol("UnknownAttachmentMimeType")
    MissingLocalAttachment = attachment_symbol("MissingLocalAttachment")
    normalize_mime_type = attachment_symbol("normalize_mime_type")
    fallback_name = attachment_symbol("_FALLBACK_ATTACHMENT_FILENAME")

    # -- the module's own vocabulary ----------------------------------------
    assert fallback_name == "attachment.bin"
    assert issubclass(AttachmentError, ValueError)
    assert issubclass(UnknownAttachmentMimeType, AttachmentError)
    assert issubclass(MissingLocalAttachment, AttachmentError)
    assert normalize_mime_type("  Application/PDF; charset=binary ") == "application/pdf"
    assert normalize_mime_type(None) is None
    assert normalize_mime_type("") is None

    # -- one MIME policy, shared by Image and File --------------------------
    assert Image(url=REMOTE_JPEG).mime_type == "image/jpeg"          # query stripped
    assert Image(url="https://example.com/asset").mime_type is None  # no image/png fallback
    assert File(url="/tmp/x/report.PDF", mime_type="Application/PDF; charset=binary").mime_type == "application/pdf"
    assert Image(content=b"\x89PNG\r\n").mime_type == "image/png"    # the one surviving default

    # -- is_remote, and attachments() ---------------------------------------
    assert Image(url=REMOTE_JPEG).is_remote is True
    assert Image(url="HTTPS://EXAMPLE.COM/a.png").is_remote is True
    assert File(url="s3://bucket/report.pdf").is_remote is False
    assert File(url=write(tmp_path, "report.pdf", PDF_BYTES)).is_remote is False

    local_pdf = File(url=write(tmp_path, "report.pdf", PDF_BYTES))
    remote_jpeg = Image(url=REMOTE_JPEG)
    prompt = _MultiModalPrompt(texts=["Summarise these"], images=[remote_jpeg], files=[local_pdf])
    assert [a.type for a in prompt.attachments()] == ["image", "file"]
    assert prompt.attachments() is not prompt.attachments()
    assert len(prompt.images) == 1 and len(prompt.files) == 1

    stub = StubOnline()

    # -- kind comes from the MIME type, never from the Python class ---------
    png_file = File(url=write(tmp_path, "chart.png", b"1234"))
    file_block = block_of(stub, png_file)
    assert isinstance(file_block, AttachmentBlock)
    assert (file_block.kind, file_block.source, file_block.mime_type) == ("image", "base64", "image/png")
    assert (file_block.filename, file_block.detail) == ("chart.png", "auto")

    pdf_image = Image(content=PDF_BYTES, mime_type="application/pdf")
    image_block = block_of(stub, pdf_image)
    assert (image_block.kind, image_block.source, image_block.mime_type) == ("document", "base64", "application/pdf")
    assert (image_block.filename, image_block.detail) == ("attachment.bin", None)
    assert image_block.payload == PDF_B64

    # frozen
    with pytest.raises(Exception):
        file_block.kind = "document"

    # -- a remote url is a url block; a missing local path is refused -------
    remote_block = block_of(stub, remote_jpeg)
    assert (remote_block.kind, remote_block.source, remote_block.payload) == ("image", "url", REMOTE_JPEG)
    assert (remote_block.filename, remote_block.detail) == ("cat.jpeg", "auto")

    File(url="https://example.com/download")  # construction alone never raises
    Image(url="/tmp/definitely-missing/typo.png")

    with pytest.raises(MissingLocalAttachment) as caught:
        block_of(stub, Image(url="/tmp/definitely-missing/typo.png"))
    assert caught.value.url == "/tmp/definitely-missing/typo.png"

    with pytest.raises(MissingLocalAttachment) as caught:
        block_of(stub, File(url="s3://bucket/report.pdf"))
    assert caught.value.url == "s3://bucket/report.pdf"

    # missing beats unguessable: the ordering of the two checks
    with pytest.raises(MissingLocalAttachment):
        block_of(stub, File(url="/tmp/definitely-missing/notes"))

    # -- an unresolvable MIME is refused, at block build time ---------------
    with pytest.raises(UnknownAttachmentMimeType) as caught:
        block_of(stub, File(url="https://example.com/download"))
    assert caught.value.url == "https://example.com/download"
    assert caught.value.attachment_type == "file"      # BaseType.type, not the block kind
    assert isinstance(caught.value, ValueError)

    with pytest.raises(UnknownAttachmentMimeType) as caught:
        block_of(stub, Image(url="https://example.com/asset"))
    assert caught.value.attachment_type == "image"

    extensionless = File(url=write(tmp_path, "notes", b"hello"))
    with pytest.raises(UnknownAttachmentMimeType):
        block_of(stub, extensionless)

    # -- the OpenAI rendering, all four shapes ------------------------------
    from bespokelabs.curator.request_processor.online.base_online_request_processor import _render_openai_block

    pdf_block = block_of(stub, local_pdf)
    assert _render_openai_block(pdf_block) == {
        "type": "file",
        "file": {"filename": "report.pdf", "file_data": f"data:application/pdf;base64,{PDF_B64}"},
    }
    assert _render_openai_block(remote_block) == {
        "type": "image_url",
        "image_url": {"url": REMOTE_JPEG, "detail": "auto"},
    }
    assert _render_openai_block(file_block) == {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{base64.b64encode(b'1234').decode()}", "detail": "auto"},
    }
    # a document served over http(s): built through the seam rather than by hand,
    # so the block model may carry whatever other fields the implementation gave it
    remote_pdf_block = block_of(stub, Image(url="https://cdn.example.com/report.pdf", mime_type="application/pdf"))
    assert (remote_pdf_block.kind, remote_pdf_block.source) == ("document", "url")
    assert _render_openai_block(remote_pdf_block) == {
        "type": "file",
        "file": {"filename": "report.pdf", "file_url": "https://cdn.example.com/report.pdf"},
    }

    # -- the Anthropic rendering --------------------------------------------
    from bespokelabs.curator.request_processor.online.anthropic_online_request_processor import (
        AnthropicOnlineRequestProcessor,
        _render_anthropic_block,
    )

    assert _render_anthropic_block(pdf_block) == {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": PDF_B64},
    }
    assert _render_anthropic_block(remote_block) == {
        "type": "image",
        "source": {"type": "url", "url": REMOTE_JPEG},
    }
    anthropic = object.__new__(AnthropicOnlineRequestProcessor)
    assert anthropic._render_attachment_block(pdf_block) == _render_anthropic_block(pdf_block)

    # -- litellm dispatches on the format it already detects ----------------
    from bespokelabs.curator.request_processor.online.litellm_online_request_processor import (
        LiteLLMOnlineRequestProcessor,
    )

    lite = object.__new__(LiteLLMOnlineRequestProcessor)
    lite.config = SimpleNamespace(model="anthropic/claude-3-5-sonnet-20241022")
    assert lite._render_attachment_block(pdf_block) == _render_anthropic_block(pdf_block)
    lite.config = SimpleNamespace(model="openai/gpt-4o-mini")
    assert lite._render_attachment_block(pdf_block) == _render_openai_block(pdf_block)

    # -- _format_multimodal survives as a one-shot, ignoring its mime_type --
    assert stub._format_multimodal(local_pdf) == _render_openai_block(pdf_block)
    assert stub._format_multimodal(local_pdf, mime_type="image/png") == _render_openai_block(pdf_block)

    # -- attachments first, then text, in list order ------------------------
    content = stub._handle_multi_modal_prompt(prompt)
    assert [b["type"] for b in content] == ["image_url", "file", "text"]
    assert content == [
        {"type": "image_url", "image_url": {"url": REMOTE_JPEG, "detail": "auto"}},
        {"type": "file", "file": {"filename": "report.pdf", "file_data": f"data:application/pdf;base64,{PDF_B64}"}},
        {"type": "text", "text": "Summarise these"},
    ]
    two_texts = _MultiModalPrompt(texts=["a", "b"], images=[Image(url=REMOTE_JPEG)], files=[local_pdf])
    ordered = stub._handle_multi_modal_prompt(two_texts)
    assert [b["type"] for b in ordered] == ["image_url", "file", "text", "text"]
    assert (ordered[2]["text"], ordered[3]["text"]) == ("a", "b")
    assert stub._handle_multi_modal_prompt(two_texts) is not ordered

    # -- the estimator no longer indexes every non-text block as image_url --
    from bespokelabs.curator.request_processor.openai_request_mixin import (
        _OPENAI_TOKENS_PER_IMAGE,
        calculate_input_tokens,
    )

    encoder = FakeEncoder()
    assert calculate_input_tokens("hello", encoder) == 5
    assert calculate_input_tokens([{"type": "text", "text": "hello"}], encoder) == 5
    assert calculate_input_tokens([content[0]], encoder) == _OPENAI_TOKENS_PER_IMAGE["low"] == 85
    assert calculate_input_tokens([_render_anthropic_block(remote_block)], encoder) == 85
    # a document block is priced rather than a KeyError; what it costs is r2's
    for document in (content[1], _render_anthropic_block(pdf_block)):
        priced = calculate_input_tokens([document], encoder)
        assert isinstance(priced, int) and priced >= 0

    assert os.path.basename(local_pdf.url) == "report.pdf"
    assert get_base64_size(PDF_B64) > 0
