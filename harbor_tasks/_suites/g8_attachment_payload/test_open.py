"""attachment-payload — the openly stated feature: one canonical attachment block.

Everything asserted here is written down in the ticket: the new
`types/attachment.py` module with `AttachmentBlock` (a frozen pydantic model
with the six fields the ticket declares), `AttachmentError`,
`UnknownAttachmentMimeType`, `MissingLocalAttachment`, `EmptyAttachment` — all
three with the exact messages the ticket writes — `normalize_mime_type` and
`_FALLBACK_ATTACHMENT_FILENAME`; `BaseType.is_remote` and
`_MultiModalPrompt.attachments()`; the single MIME policy with its four worked
values and its one warning per failed guess; `_canonical_attachment_block`
deciding `kind` from the MIME rather than from the Python class and refusing in
the ticket's order (missing local path, unresolvable MIME, empty payload); the
two module-level renderers and their exact dicts; `_format_multimodal` surviving
as a one-shot; the litellm dispatch on `_uses_anthropic_multimodal_format()`;
attachments before text in `_handle_multi_modal_prompt`; `calculate_input_tokens`
dispatching on `block["type"]` instead of indexing `msg["image_url"]`; and the
constraints section's "reuse these as they are", checked against the pristine
tree because every behavioural check above runs through the new layer instead.

Nothing here touches a hidden fact. It never mentions a size ceiling, a
`size_mb` field, an attachment count or what a document block COSTS the
estimator (r1); it never mentions a fingerprint, a filename cap or a detail
vocabulary (r2). Every payload below is a few bytes and every filename short, so
any ceiling and any cap agree; every `detail` is the default `"auto"`, which
survives normalization unchanged. Pricing a document block is asserted only to
be an int that no longer raises.

The harness contract the specification fixes — `StubOnline`, `FakeEncoder`, the
answer-free inputs (`PDF_BYTES`, `PDF_B64`, `REMOTE_JPEG`), `attachment_symbol`,
`block_of`, `write` — now lives in `probe_support.py`, so the worker (`probe.py`)
and this human reference share ONE definition and cannot drift. This module
re-imports those names, which is also how test_r1/test_r2 keep resolving their
`from test_open import ...`. The expected VALUES asserted below stay here (and in
`judge.py`); `probe_support` holds none of them.
"""
from __future__ import annotations

import base64
import os
import pathlib
from types import SimpleNamespace

import pytest

from probe_support import (  # noqa: F401 - several are re-exported for test_r1/test_r2
    ATTACHMENT_IMPORT_ERROR,
    FakeEncoder,
    File,
    Image,
    PDF_B64,
    PDF_BYTES,
    REMOTE_JPEG,
    StubOnline,
    _MultiModalPrompt,
    attachment_module,
    attachment_symbol,
    block_of,
    capture_warnings,
    get_base64_size,
    importable,
    raising_stub,
    write,
)

# The names the ticket places in `types/attachment.py` by name, and the block
# fields it declares. `attachment_symbol` sweeps four modules on purpose (a
# hidden requirement's symbols may be spelled anywhere); these the ticket does
# place, so where they live is itself part of the stated feature.
TICKET_ATTACHMENT_NAMES = (
    "AttachmentBlock",
    "AttachmentError",
    "UnknownAttachmentMimeType",
    "MissingLocalAttachment",
    "EmptyAttachment",
    "normalize_mime_type",
    "_FALLBACK_ATTACHMENT_FILENAME",
)
TICKET_BLOCK_FIELDS = ("kind", "source", "mime_type", "payload", "filename", "detail")


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
    EmptyAttachment = attachment_symbol("EmptyAttachment")
    normalize_mime_type = attachment_symbol("normalize_mime_type")
    fallback_name = attachment_symbol("_FALLBACK_ATTACHMENT_FILENAME")

    # -- the module's own vocabulary ----------------------------------------
    assert fallback_name == "attachment.bin"
    assert issubclass(AttachmentError, ValueError)
    assert issubclass(UnknownAttachmentMimeType, AttachmentError)
    assert issubclass(MissingLocalAttachment, AttachmentError)
    assert issubclass(EmptyAttachment, AttachmentError)
    assert normalize_mime_type("  Application/PDF; charset=binary ") == "application/pdf"
    assert normalize_mime_type(None) is None
    assert normalize_mime_type("") is None

    # -- the module the ticket names holds the names it declares there -------
    assert attachment_module is not None, f"types/attachment.py did not import: {ATTACHMENT_IMPORT_ERROR!r}"
    for name in TICKET_ATTACHMENT_NAMES:
        assert hasattr(attachment_module, name), f"types/attachment.py does not export {name}"
    assert attachment_module.__file__.replace("\\", "/").endswith(
        "bespokelabs/curator/types/attachment.py")

    # -- one MIME policy, shared by Image and File --------------------------
    assert Image(url=REMOTE_JPEG).mime_type == "image/jpeg"          # query stripped
    # a failed guess leaves mime_type None and says so exactly once, on both classes
    with capture_warnings() as unguessable_image:
        assert Image(url="https://example.com/asset").mime_type is None  # no image/png fallback
    assert unguessable_image.count == 1
    with capture_warnings() as unguessable_file:
        assert File(url="https://example.com/download").mime_type is None
    assert unguessable_file.count == 1
    with capture_warnings() as guessable:
        assert File(url="https://cdn.example.com/reports/report.pdf").mime_type == "application/pdf"
    assert guessable.count == 0
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

    # -- the block is the pydantic model the ticket declares ----------------
    import pydantic

    with pytest.raises(Exception):
        file_block.kind = "document"
    with pytest.raises(Exception):
        file_block.payload = "tampered"
    assert issubclass(AttachmentBlock, pydantic.BaseModel)
    assert dict(AttachmentBlock.model_config or {}).get("frozen") is True
    for field in TICKET_BLOCK_FIELDS:
        assert field in AttachmentBlock.model_fields
    assert {name: AttachmentBlock.model_fields[name].is_required() for name in TICKET_BLOCK_FIELDS} == {
        "kind": True, "source": True, "mime_type": True, "payload": True,
        "filename": True, "detail": False,
    }
    assert AttachmentBlock.model_fields["detail"].default is None
    # the Literal fields, exercised through a block the seam really built, so
    # this never has to name the fields a hidden requirement added
    dumped = file_block.model_dump()
    assert type(file_block).model_validate(dumped) == file_block
    with pytest.raises(pydantic.ValidationError):
        type(file_block).model_validate({**dumped, "kind": "video"})
    with pytest.raises(pydantic.ValidationError):
        type(file_block).model_validate({**dumped, "source": "ftp"})

    # -- a remote url is a url block; a missing local path is refused -------
    remote_block = block_of(stub, remote_jpeg)
    assert (remote_block.kind, remote_block.source, remote_block.payload) == ("image", "url", REMOTE_JPEG)
    assert (remote_block.filename, remote_block.detail) == ("cat.jpeg", "auto")

    File(url="https://example.com/download")  # construction alone never raises
    Image(url="/tmp/definitely-missing/typo.png")

    with pytest.raises(MissingLocalAttachment) as caught:
        block_of(stub, Image(url="/tmp/definitely-missing/typo.png"))
    assert caught.value.url == "/tmp/definitely-missing/typo.png"
    assert str(caught.value) == ("Attachment path is neither an http(s) URL nor an existing file: "
                                "'/tmp/definitely-missing/typo.png'")

    with pytest.raises(MissingLocalAttachment) as caught:
        block_of(stub, File(url="s3://bucket/report.pdf"))
    assert caught.value.url == "s3://bucket/report.pdf"
    assert str(caught.value) == ("Attachment path is neither an http(s) URL nor an existing file: "
                                "'s3://bucket/report.pdf'")

    # missing beats unguessable: the ordering of the two checks
    with pytest.raises(MissingLocalAttachment):
        block_of(stub, File(url="/tmp/definitely-missing/notes"))

    # -- an unresolvable MIME is refused, at block build time ---------------
    with pytest.raises(UnknownAttachmentMimeType) as caught:
        block_of(stub, File(url="https://example.com/download"))
    assert caught.value.url == "https://example.com/download"
    assert caught.value.attachment_type == "file"      # BaseType.type, not the block kind
    assert isinstance(caught.value, ValueError)
    assert str(caught.value) == ("Cannot determine MIME type for file attachment: "
                                "'https://example.com/download'")

    with pytest.raises(UnknownAttachmentMimeType) as caught:
        block_of(stub, Image(url="https://example.com/asset"))
    assert caught.value.attachment_type == "image"
    assert str(caught.value) == ("Cannot determine MIME type for image attachment: "
                                "'https://example.com/asset'")

    extensionless = File(url=write(tmp_path, "notes", b"hello"))
    with pytest.raises(UnknownAttachmentMimeType):
        block_of(stub, extensionless)

    # -- an empty payload is refused, AFTER the MIME check ------------------
    empty_url = write(tmp_path, "empty.pdf", b"")
    assert File(url=empty_url).serialize() == ""
    with pytest.raises(EmptyAttachment) as caught:
        block_of(stub, File(url=empty_url))
    assert (caught.value.url, caught.value.filename) == (empty_url, "empty.pdf")
    assert str(caught.value) == f"Attachment empty.pdf has an empty payload: {empty_url!r}"
    # the MIME check speaks first, so an empty file with an unguessable name is
    # refused for its MIME rather than for being empty
    with pytest.raises(UnknownAttachmentMimeType):
        block_of(stub, File(url=write(tmp_path, "empty-notes", b"")))

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

    # -- the helpers the ticket says to reuse as they are --------------------
    # Source, not behaviour: every check above goes through the NEW layer, so a
    # rewritten `serialize()` is invisible to all of them. The graded copy of
    # this lives in `judge.py` (`_check_reused_as_is`), which reads the pristine
    # tree root staged for it; here it reads the same tree through `harness`.
    import ast

    import bespokelabs.curator as curator_pkg
    from harness import baseline_text

    def body_of(src, classname, funcname):
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ClassDef) and node.name == classname:
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == funcname:
                        statements = [s for s in child.body
                                      if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
                        return ast.dump(ast.Module(body=statements, type_ignores=[])) + ast.dump(child.args)
        return None

    live = pathlib.Path(curator_pkg.__file__).parent
    for rel, classname, funcname in (
        ("types/prompt.py", "Image", "serialize"),
        ("types/prompt.py", "File", "serialize"),
        ("types/prompt.py", "BaseType", "_is_local_uri"),
        ("types/prompt.py", "BaseType", "_load_file_as_b64"),
        ("types/prompt.py", "BaseType", "is_local"),
        ("types/prompt.py", "_MultiModalPrompt", "load"),
        ("request_processor/online/base_online_request_processor.py",
         "BaseOnlineRequestProcessor", "_unpack_multimodal"),
    ):
        shipped = baseline_text(rel)
        if shipped is None:
            continue  # no baseline to diff against locally; judge.py fails closed instead
        mine = (live / rel).read_text()
        assert body_of(mine, classname, funcname) == body_of(shipped, classname, funcname), (
            f"{classname}.{funcname} in {rel} was rewritten; the ticket says to reuse it as it is")
    prompt_src = (live / "types/prompt.py").read_text()
    assert body_of(prompt_src, "_MultiModalPrompt", "model_validate") is None
