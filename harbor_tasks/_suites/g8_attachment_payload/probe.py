"""g8 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers, so a value here is the value the test saw. The judge holds the
assertions those tests made. A submission that returns forged values only forges
values the judge still checks against the real expectations — which is
implementing them. Floats (a base64 size like 8.58e-06) go through `json`, whose
float encoding is `repr`, so every value round-trips to the identical double and
the judge's approx comparison means what it meant in-process.

The huge base64 payloads r1 uses to cross a megabyte ceiling are NEVER written
to the observations file — a comparison against one is reduced to a bool or a
length here, so the JSON stays a few kilobytes rather than tens of megabytes.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import traceback
from types import SimpleNamespace

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# probe_support owns the curator imports and the answer-free helpers/inputs;
# reuse them so a probe calls curator exactly as the reference test does.
# Importing it runs the submission's `import bespokelabs.curator` — this
# process's whole purpose, and why it is disposable. The worker never imports
# test_open, whose source carries the expected answer literals.
import fixture_spec  # noqa: E402 - the run's inputs; stdlib only, no answers
import probe_support as S  # noqa: E402
from probe_support import File, Image, _MultiModalPrompt  # noqa: E402
from harness import read_field  # noqa: E402

# Answer-free INPUTS r1/r2 drive curator with. `get_base64_size` reads
# (len * 3) // 4 - padding bytes, so these lengths measure to exact megabytes
# with no rounding to argue about. These are inputs, not answers, and they are
# never serialized to the observations file (see the module docstring).
PAYLOAD_24MB = "A" * 33_554_432   # -> 24.0 MB
PAYLOAD_18MB = "A" * 25_165_824   # -> 18.0 MB
PAYLOAD_6MB = "A" * 8_388_608     # -> 6.0 MB

LONG_PDF_URL = (
    "https://cdn.example.com/reports/"
    "2024-q4-consolidated-financial-statements-and-notes-final-approved-v3.pdf"
)
EXACTLY_64_URL = (
    "https://cdn.example.com/reports/"
    "2024-q4-consolidated-financial-statements-and-notes-final-v3.pdf"
)
LONG_EXTENSIONLESS_URL = (
    "https://cdn.example.com/exports/"
    "ledger-entries-consolidated-2024-q4-final-copy-for-review-board-appendix"
)

# The attributes the g8 exceptions carry, captured off a raised instance so the
# judge can check the (kind, size_mb, limit_mb) / (count, limit) / url /
# attachment_type the reference tests read. `filename` is EmptyAttachment's, and
# it is what lets the judge rebuild that exception's stated message: the payload
# it refuses lives in a throwaway directory, so the url half of the message is
# only knowable from what the probe recorded.
_EXC_ATTRS = ("url", "attachment_type", "filename", "kind", "size_mb", "limit_mb", "count", "limit")

# The names the ticket puts in `types/attachment.py` by name. Answer-free: it is
# the ticket's own list, and the probe only records WHERE each one was found.
# `probe_support.attachment_symbol` deliberately sweeps four modules, because a
# hidden requirement's symbols may be spelled anywhere; these seven the ticket
# does place, so the module they are reachable from is itself a graded fact.
_TICKET_ATTACHMENT_NAMES = (
    "AttachmentBlock",
    "AttachmentError",
    "UnknownAttachmentMimeType",
    "MissingLocalAttachment",
    "EmptyAttachment",
    "normalize_mime_type",
    "_FALLBACK_ATTACHMENT_FILENAME",
)

# The block fields the ticket declares, in the order it declares them. The
# implementation may carry more (a hidden requirement adds two); these six it
# must carry, with `detail` the only optional one.
_TICKET_BLOCK_FIELDS = ("kind", "source", "mime_type", "payload", "filename", "detail")


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, its message and
    whichever of the attachment exception attributes the instance carries."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in _EXC_ATTRS:
            if hasattr(exc, attr):
                info[attr] = getattr(exc, attr)
        return info
    return {"raised": False, "mro": []}


def _set_attr(obj, name, value):
    """Assign one attribute, so the frozen-block check can record raised/not."""
    setattr(obj, name, value)


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open() -> dict:
    S.importable()
    tmp = S.make_tmp_dir()
    o: dict = {}

    AttachmentBlock = S.attachment_symbol("AttachmentBlock")
    AttachmentError = S.attachment_symbol("AttachmentError")
    UnknownAttachmentMimeType = S.attachment_symbol("UnknownAttachmentMimeType")
    MissingLocalAttachment = S.attachment_symbol("MissingLocalAttachment")
    EmptyAttachment = S.attachment_symbol("EmptyAttachment")
    normalize_mime_type = S.attachment_symbol("normalize_mime_type")
    fallback_name = S.attachment_symbol("_FALLBACK_ATTACHMENT_FILENAME")

    # -- the module's own vocabulary ----------------------------------------
    o["fallback_name"] = fallback_name
    o["attachment_error_mro"] = [c.__name__ for c in AttachmentError.__mro__]
    o["unknown_mime_mro"] = [c.__name__ for c in UnknownAttachmentMimeType.__mro__]
    o["missing_local_mro"] = [c.__name__ for c in MissingLocalAttachment.__mro__]
    o["empty_attachment_mro"] = [c.__name__ for c in EmptyAttachment.__mro__]
    o["normalize_pdf"] = normalize_mime_type("  Application/PDF; charset=binary ")
    o["normalize_none"] = normalize_mime_type(None)
    o["normalize_empty"] = normalize_mime_type("")

    # -- the module the ticket names actually holds the names it declares ---
    module = S.attachment_module
    o["attachment_module_file"] = getattr(module, "__file__", None)
    o["attachment_module_exports"] = {
        name: (module is not None and hasattr(module, name)) for name in _TICKET_ATTACHMENT_NAMES
    }

    # -- one MIME policy, shared by Image and File --------------------------
    o["mime_remote_jpeg"] = Image(url=S.REMOTE_JPEG).mime_type
    # "exactly one logger.warning" when a url's MIME cannot be guessed, on BOTH
    # classes, and none when it can be. Counted, never judged, here.
    with S.capture_warnings() as unguessable_image:
        o["mime_asset"] = Image(url="https://example.com/asset").mime_type
    o["mime_asset_warn_count"] = unguessable_image.count
    with S.capture_warnings() as unguessable_file:
        o["mime_download"] = File(url="https://example.com/download").mime_type
    o["mime_download_warn_count"] = unguessable_file.count
    with S.capture_warnings() as guessable:
        o["mime_quiet_guess"] = File(url="https://cdn.example.com/reports/report.pdf").mime_type
    o["mime_quiet_warn_count"] = guessable.count
    o["mime_file_pdf"] = File(url="/tmp/x/report.PDF", mime_type="Application/PDF; charset=binary").mime_type
    o["mime_png_content"] = Image(content=b"\x89PNG\r\n").mime_type

    # -- is_remote, and attachments() ---------------------------------------
    o["is_remote_jpeg"] = Image(url=S.REMOTE_JPEG).is_remote
    o["is_remote_upper"] = Image(url="HTTPS://EXAMPLE.COM/a.png").is_remote
    o["is_remote_s3"] = File(url="s3://bucket/report.pdf").is_remote
    o["is_remote_local"] = File(url=S.write(tmp, "report.pdf", S.PDF_BYTES)).is_remote

    local_pdf = File(url=S.write(tmp, "report.pdf", S.PDF_BYTES))
    remote_jpeg = Image(url=S.REMOTE_JPEG)
    prompt = _MultiModalPrompt(texts=["Summarise these"], images=[remote_jpeg], files=[local_pdf])
    o["attachment_types"] = [a.type for a in prompt.attachments()]
    o["attachments_fresh"] = prompt.attachments() is not prompt.attachments()
    o["images_files_len"] = [len(prompt.images), len(prompt.files)]

    stub = S.StubOnline()

    # -- kind comes from the MIME type, never from the Python class ---------
    png_file = File(url=S.write(tmp, "chart.png", S.PNG_BYTES))
    file_block = S.block_of(stub, png_file)
    o["file_block_isinstance"] = isinstance(file_block, AttachmentBlock)
    o["file_block_triple"] = [read_field(file_block, "kind"), read_field(file_block, "source"),
                              read_field(file_block, "mime_type")]
    o["file_block_name_detail"] = [read_field(file_block, "filename"), read_field(file_block, "detail")]

    pdf_image = Image(content=S.PDF_BYTES, mime_type="application/pdf")
    image_block = S.block_of(stub, pdf_image)
    o["image_block_triple"] = [read_field(image_block, "kind"), read_field(image_block, "source"),
                               read_field(image_block, "mime_type")]
    o["image_block_name_detail"] = [read_field(image_block, "filename"), read_field(image_block, "detail")]
    o["image_block_payload"] = read_field(image_block, "payload")

    # -- the block is the pydantic model the ticket declares ----------------
    # frozen: assignment must raise, on more than the one field, and the
    # `frozen=True` config the ticket spells out must really be on the model.
    o["frozen"] = raises(_set_attr, file_block, "kind", "document")
    o["frozen_payload"] = raises(_set_attr, file_block, "payload", "tampered")
    import pydantic

    o["block_is_basemodel"] = isinstance(file_block, pydantic.BaseModel) and issubclass(
        AttachmentBlock, pydantic.BaseModel)
    o["block_config_frozen"] = dict(getattr(AttachmentBlock, "model_config", None) or {}).get("frozen")
    block_fields = dict(getattr(AttachmentBlock, "model_fields", None) or {})
    o["block_field_names"] = sorted(block_fields)
    o["block_required"] = {
        name: bool(block_fields[name].is_required()) for name in _TICKET_BLOCK_FIELDS if name in block_fields
    }
    o["block_detail_default"] = (
        block_fields["detail"].default if "detail" in block_fields else "<no detail field>")
    # The typed Literal fields, exercised through the model the implementation
    # actually built: re-validating its own dump must round-trip, and a `kind` or
    # `source` outside the ticket's vocabulary must be rejected. Going through
    # `model_validate` of a real block's dump keeps this answer-free — it never
    # has to name the fields a hidden requirement added.
    dumped = file_block.model_dump()
    o["block_revalidates"] = type(file_block).model_validate(dumped) == file_block
    o["block_bad_kind"] = raises(type(file_block).model_validate, {**dumped, "kind": "video"})
    o["block_bad_source"] = raises(type(file_block).model_validate, {**dumped, "source": "ftp"})

    # -- a remote url is a url block; a missing local path is refused -------
    remote_block = S.block_of(stub, remote_jpeg)
    o["remote_block_triple"] = [read_field(remote_block, "kind"), read_field(remote_block, "source"),
                                read_field(remote_block, "payload")]
    o["remote_block_name_detail"] = [read_field(remote_block, "filename"), read_field(remote_block, "detail")]

    # construction alone never raises
    File(url="https://example.com/download")
    Image(url="/tmp/definitely-missing/typo.png")

    o["miss_typo"] = raises(S.block_of, stub, Image(url="/tmp/definitely-missing/typo.png"))
    o["miss_s3"] = raises(S.block_of, stub, File(url="s3://bucket/report.pdf"))
    # missing beats unguessable: the ordering of the two checks
    o["miss_notes"] = raises(S.block_of, stub, File(url="/tmp/definitely-missing/notes"))

    # -- an unresolvable MIME is refused, at block build time ---------------
    o["unknown_download"] = raises(S.block_of, stub, File(url="https://example.com/download"))
    o["unknown_asset"] = raises(S.block_of, stub, Image(url="https://example.com/asset"))
    extensionless_url = S.write(tmp, "notes", b"hello")
    o["extensionless_url"] = extensionless_url
    o["unknown_extensionless"] = raises(S.block_of, stub, File(url=extensionless_url))

    # -- an empty payload is refused, AFTER the MIME check ------------------
    # The url half of this message is a throwaway path, so the probe records the
    # path it used and the judge rebuilds the stated message from it.
    empty_url = S.write(tmp, "empty.pdf", b"")
    o["empty_url"] = empty_url
    o["empty_serializes_to"] = File(url=empty_url).serialize()
    o["empty_payload"] = raises(S.block_of, stub, File(url=empty_url))
    # ordering: an empty file whose MIME is also unguessable is refused for the
    # MIME, because that check speaks first
    o["empty_unguessable"] = raises(S.block_of, stub, File(url=S.write(tmp, "empty-notes", b"")))

    # -- the OpenAI rendering, all four shapes ------------------------------
    from bespokelabs.curator.request_processor.online.base_online_request_processor import _render_openai_block

    pdf_block = S.block_of(stub, local_pdf)
    o["render_openai_pdf"] = _render_openai_block(pdf_block)
    o["render_openai_remote"] = _render_openai_block(remote_block)
    o["render_openai_file"] = _render_openai_block(file_block)
    remote_pdf_block = S.block_of(stub, Image(url="https://cdn.example.com/report.pdf", mime_type="application/pdf"))
    o["remote_pdf_kind_source"] = [read_field(remote_pdf_block, "kind"), read_field(remote_pdf_block, "source")]
    o["render_openai_remote_pdf"] = _render_openai_block(remote_pdf_block)

    # -- the Anthropic rendering --------------------------------------------
    from bespokelabs.curator.request_processor.online.anthropic_online_request_processor import (
        AnthropicOnlineRequestProcessor,
        _render_anthropic_block,
    )

    o["render_anthropic_pdf"] = _render_anthropic_block(pdf_block)
    o["render_anthropic_remote"] = _render_anthropic_block(remote_block)
    anthropic = object.__new__(AnthropicOnlineRequestProcessor)
    o["anthropic_method_matches"] = anthropic._render_attachment_block(pdf_block) == _render_anthropic_block(pdf_block)

    # -- litellm dispatches on the format it already detects ----------------
    from bespokelabs.curator.request_processor.online.litellm_online_request_processor import (
        LiteLLMOnlineRequestProcessor,
    )

    lite = object.__new__(LiteLLMOnlineRequestProcessor)
    lite.config = SimpleNamespace(model="anthropic/claude-3-5-sonnet-20241022")
    o["lite_anthropic_matches"] = lite._render_attachment_block(pdf_block) == _render_anthropic_block(pdf_block)
    lite.config = SimpleNamespace(model="openai/gpt-4o-mini")
    o["lite_openai_matches"] = lite._render_attachment_block(pdf_block) == _render_openai_block(pdf_block)

    # -- _format_multimodal survives as a one-shot, ignoring its mime_type --
    o["format_multimodal_matches"] = stub._format_multimodal(local_pdf) == _render_openai_block(pdf_block)
    o["format_multimodal_mime_matches"] = (
        stub._format_multimodal(local_pdf, mime_type="image/png") == _render_openai_block(pdf_block))

    # -- attachments first, then text, in list order ------------------------
    content = stub._handle_multi_modal_prompt(prompt)
    o["content_types"] = [b["type"] for b in content]
    o["content"] = content
    two_texts = _MultiModalPrompt(texts=["a", "b"], images=[Image(url=S.REMOTE_JPEG)], files=[local_pdf])
    ordered = stub._handle_multi_modal_prompt(two_texts)
    o["ordered_types"] = [b["type"] for b in ordered]
    o["ordered_texts"] = [ordered[2]["text"], ordered[3]["text"]]
    o["ordered_fresh"] = stub._handle_multi_modal_prompt(two_texts) is not ordered

    # -- the estimator no longer indexes every non-text block as image_url --
    from bespokelabs.curator.request_processor.openai_request_mixin import (
        _OPENAI_TOKENS_PER_IMAGE,
        calculate_input_tokens,
    )

    encoder = S.FakeEncoder()
    o["calc_hello_str"] = calculate_input_tokens("hello", encoder)
    o["calc_hello_block"] = calculate_input_tokens([{"type": "text", "text": "hello"}], encoder)
    o["calc_image_content0"] = calculate_input_tokens([content[0]], encoder)
    o["tokens_per_image_low"] = _OPENAI_TOKENS_PER_IMAGE["low"]
    o["calc_anthropic_image"] = calculate_input_tokens([_render_anthropic_block(remote_block)], encoder)
    priced = [calculate_input_tokens([content[1]], encoder),
              calculate_input_tokens([_render_anthropic_block(pdf_block)], encoder)]
    o["priced_docs"] = priced
    o["priced_docs_is_int"] = [isinstance(p, int) for p in priced]

    o["local_pdf_basename"] = os.path.basename(local_pdf.url)
    o["get_base64_size_pdf"] = S.get_base64_size(S.PDF_B64)
    return o


# ---------------------------------------------------------------------------
# r1 — the size and count ceilings the base owns
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    S.importable()
    tmp = S.make_tmp_dir()
    AttachmentTooLarge = S.attachment_symbol("AttachmentTooLarge")
    o = {"too_large_mro": [c.__name__ for c in AttachmentTooLarge.__mro__]}

    # the measurement is taken from the base64 length, in MB, and kept on the block
    stub = S.StubOnline()
    block = S.block_of(stub, File(url=S.write(tmp, "report.pdf", S.PDF_BYTES)))
    measured = read_field(block, "size_mb")
    o["measured"] = measured
    o["measured_is_float"] = isinstance(measured, float)
    o["get_base64_size_pdf"] = S.get_base64_size(S.PDF_B64)

    # an image payload over 20.0 MB is refused, by name, with the stated attributes
    refusing = S.raising_stub("provider")
    o["over_image"] = raises(S.block_of, refusing, Image(content=PAYLOAD_24MB))
    # refused by the BASE, before the provider hook (which raises for anything) is consulted
    o["refusing_calls_after_over"] = len(refusing.calls)

    # the same 24.0 MB, resolved as a document, clears the higher ceiling and is
    # handed to the provider hook, which is what refuses it with RuntimeError
    o["doc_runtime"] = raises(S.block_of, refusing, Image(content=PAYLOAD_24MB, mime_type="application/pdf"))

    # a recording stub sees the same document accepted, sized and offered
    recording = S.StubOnline()
    document = S.block_of(recording, Image(content=PAYLOAD_24MB, mime_type="application/pdf"))
    o["doc_kind"] = read_field(document, "kind")
    o["doc_size_mb"] = read_field(document, "size_mb")
    o["recording_calls_len"] = len(recording.calls)
    o["recording_calls_is_payload"] = recording.calls == [PAYLOAD_24MB]
    return o


def probe_r1_scope() -> dict:
    S.importable()
    S.attachment_symbol("AttachmentTooLarge")  # the exception this fact refuses with
    images = [
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_6MB),
    ]
    stub = S.StubOnline()
    o = {"over": raises(stub._handle_multi_modal_prompt,
                        _MultiModalPrompt(texts=["over"], images=images))}
    # every image is individually legal (18.0 and 6.0 are both under 20.0), so only
    # the aggregate could have refused this prompt; the fourth was still built and
    # offered before anything was compared
    o["stub_calls_len"] = len(stub.calls)

    # control: the first two alone are 36.0 MB, and pass
    control = S.StubOnline()
    content = control._handle_multi_modal_prompt(_MultiModalPrompt(texts=[], images=images[:2]))
    o["control_content_len"] = len(content)
    o["control_calls_len"] = len(control.calls)
    return o


def probe_r1_exclusions() -> dict:
    S.importable()
    S.attachment_symbol("AttachmentTooLarge")  # the ceiling url blocks are excluded from must exist
    tmp = S.make_tmp_dir()
    o = {}

    stub = S.StubOnline()
    remote = S.block_of(stub, Image(url=S.REMOTE_JPEG))
    o["remote_source"] = read_field(remote, "source")
    o["remote_size_mb"] = read_field(remote, "size_mb")
    o["stub_calls_len"] = len(stub.calls)

    # a prompt of only remote urls passes both ceilings, whatever is behind them
    urls = S.StubOnline()
    remote_only = _MultiModalPrompt(
        texts=["describe"],
        images=[Image(url=S.REMOTE_JPEG) for _ in range(5)],
        files=[File(url="https://cdn.example.com/reports/report.pdf")],
    )
    o["urls_content_len"] = len(urls._handle_multi_modal_prompt(remote_only))
    o["urls_calls_len"] = len(urls.calls)

    # a url alongside a base64 payload contributes nothing to the prompt sum
    mixed = S.StubOnline()
    content = mixed._handle_multi_modal_prompt(
        _MultiModalPrompt(
            texts=[],
            images=[Image(url=S.REMOTE_JPEG) for _ in range(5)],
            files=[
                File(url="https://cdn.example.com/reports/report.pdf"),
                File(url=S.write(tmp, "small.pdf", S.PDF_BYTES)),
            ],
        )
    )
    o["mixed_content_len"] = len(content)
    o["mixed_calls"] = mixed.calls
    return o


def probe_r1_failure_behavior() -> dict:
    S.importable()
    TooManyAttachments = S.attachment_symbol("TooManyAttachments")
    o = {"too_many_mro": [c.__name__ for c in TooManyAttachments.__mro__]}
    limit = S.attachment_symbol("_ATTACHMENT_COUNT_LIMIT", "ATTACHMENT_COUNT_LIMIT", required=False)
    o["count_limit"] = limit

    tiny = Image(content=b"x")
    stub = S.StubOnline()
    o["thirteen"] = raises(stub._handle_multi_modal_prompt,
                           _MultiModalPrompt(texts=["a"], images=[tiny] * 13))
    # counted first: not one of the thirteen was serialized or offered
    o["stub_calls_len"] = len(stub.calls)

    # twelve is fine — the comparison is strictly greater
    twelve = S.StubOnline()
    content = twelve._handle_multi_modal_prompt(_MultiModalPrompt(texts=["a"], images=[tiny] * 12))
    o["twelve_content_len"] = len(content)
    o["twelve_calls_len"] = len(twelve.calls)

    # texts are not attachments, so forty of them next to one image is fine
    texts = S.StubOnline()
    content = texts._handle_multi_modal_prompt(_MultiModalPrompt(texts=["a"] * 40, images=[tiny]))
    o["texts_content_len"] = len(content)
    o["texts_calls_len"] = len(texts.calls)
    return o


def probe_r1_observability() -> dict:
    S.importable()
    from bespokelabs.curator.request_processor.openai_request_mixin import calculate_input_tokens

    encoder = S.FakeEncoder()
    text_block = {"type": "text", "text": "hello"}
    openai_image = {"type": "image_url", "image_url": {"url": "x", "detail": "auto"}}
    anthropic_image = {"type": "image", "source": {"type": "url", "url": "x"}}
    openai_file = {
        "type": "file",
        "file": {"filename": "r.pdf", "file_data": f"data:application/pdf;base64,{S.PDF_B64}"},
    }
    anthropic_document = {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": S.PDF_B64},
    }
    unknown = {"type": "thinking", "thinking": "ignored"}

    o = {
        "calc_openai_file": calculate_input_tokens([openai_file], encoder),
        "calc_anthropic_document": calculate_input_tokens([anthropic_document], encoder),
        "calc_openai_image": calculate_input_tokens([openai_image], encoder),
        "calc_anthropic_image": calculate_input_tokens([anthropic_image], encoder),
    }
    total = calculate_input_tokens(
        [text_block, openai_image, anthropic_image, openai_file, anthropic_document, unknown], encoder)
    o["total"] = total
    o["total_is_int"] = isinstance(total, int)

    per_document = S.attachment_symbol("_OPENAI_TOKENS_PER_DOCUMENT", "OPENAI_TOKENS_PER_DOCUMENT", required=False)
    if per_document is None:
        from bespokelabs.curator.request_processor import openai_request_mixin
        per_document = getattr(openai_request_mixin, "_OPENAI_TOKENS_PER_DOCUMENT", None)
    o["per_document"] = per_document
    o["b64_roundtrip"] = base64.b64decode(S.PDF_B64) == S.PDF_BYTES
    return o


# ---------------------------------------------------------------------------
# r2 — what the canonical block records about itself
# ---------------------------------------------------------------------------
def probe_r2_rule() -> dict:
    S.importable()
    tmp = S.make_tmp_dir()
    stub = S.StubOnline()

    pdf = File(url=S.write(tmp, "report.pdf", S.PDF_BYTES))
    block = S.block_of(stub, pdf)
    o = {"fingerprint": read_field(block, "fingerprint")}

    other = S.block_of(stub, Image(content=b"x"))
    o["other_fingerprint"] = read_field(other, "fingerprint")
    o["other_payload"] = read_field(other, "payload")

    same_bytes = S.block_of(stub, Image(content=S.PDF_BYTES, mime_type="application/pdf"))
    o["same_bytes_fingerprint"] = read_field(same_bytes, "fingerprint")

    helper = S.attachment_symbol("attachment_fingerprint", required=False)
    o["helper_present"] = helper is not None
    if helper is not None:
        o["helper_pdf"] = helper(S.PDF_B64)
        o["helper_x"] = helper("eA==")
        o["helper_empty"] = helper("")
    hex_len = S.attachment_symbol("_ATTACHMENT_FINGERPRINT_HEX_LEN", "ATTACHMENT_FINGERPRINT_HEX_LEN", required=False)
    o["hex_len"] = hex_len
    return o


def probe_r2_scope() -> dict:
    S.importable()
    from bespokelabs.curator.request_processor.online import base_online_request_processor as base
    render_openai = base._render_openai_block

    stub = S.StubOnline()
    long_pdf = File(url=LONG_PDF_URL)
    block = S.block_of(stub, long_pdf)
    o = {"capped": read_field(block, "filename")}
    o["payload"] = read_field(block, "payload")
    o["url_unchanged"] = long_pdf.url == LONG_PDF_URL
    o["render_openai"] = render_openai(block)

    o["boundary"] = read_field(S.block_of(stub, File(url=EXACTLY_64_URL)), "filename")
    extensionless = S.block_of(stub, File(url=LONG_EXTENSIONLESS_URL, mime_type="application/pdf"))
    o["extensionless_filename"] = read_field(extensionless, "filename")
    o["short_filename"] = read_field(S.block_of(stub, File(url="https://cdn.example.com/a/report.pdf")), "filename")
    return o


def probe_r2_exclusions() -> dict:
    S.importable()
    tmp = S.make_tmp_dir()
    stub = S.StubOnline()

    remote = S.block_of(stub, Image(url=S.REMOTE_JPEG))
    o = {"remote_source": read_field(remote, "source"),
         "remote_fingerprint": read_field(remote, "fingerprint")}

    inline = S.block_of(stub, Image(content=S.REMOTE_JPEG))
    o["inline_source"] = read_field(inline, "source")
    o["inline_payload"] = read_field(inline, "payload")
    o["inline_fingerprint"] = read_field(inline, "fingerprint")

    bare = S.block_of(stub, Image(url="https://cdn.example.com/photos/cat.jpeg"))
    o["bare_fingerprint"] = read_field(bare, "fingerprint")
    fragment = S.block_of(stub, Image(url="https://cdn.example.com/photos/cat.jpeg#page=2"))
    o["fragment_fingerprint"] = read_field(fragment, "fingerprint")

    local = S.block_of(stub, File(url=S.write(tmp, "report.pdf", S.PDF_BYTES)))
    o["local_fingerprint"] = read_field(local, "fingerprint")
    return o


def probe_r2_failure_behavior() -> dict:
    S.importable()
    from bespokelabs.curator.request_processor.online import base_online_request_processor as base
    render_openai = base._render_openai_block

    stub = S.StubOnline()
    # construction never rejects a detail; the model keeps what the caller wrote
    o = {"written_detail": Image(content=b"x", detail="ultra").detail,
         "high_detail": Image(content=b"x", detail="HIGH").detail}

    # the block carries the normalized value
    o["block_high"] = read_field(S.block_of(stub, Image(content=b"x", detail="HIGH")), "detail")
    o["block_low"] = read_field(S.block_of(stub, Image(content=b"x", detail=" Low ")), "detail")
    o["block_auto"] = read_field(S.block_of(stub, Image(content=b"x", detail="auto")), "detail")

    # an unknown detail is downgraded rather than sent or refused, and says so once
    with S.capture_warnings() as recorder:
        downgraded = S.block_of(stub, Image(content=b"x", detail="ultra"))
    o["downgraded_detail"] = read_field(downgraded, "detail")
    o["downgrade_warn_count"] = recorder.count

    # a supported detail, and an absent one, say nothing
    with S.capture_warnings() as quiet:
        o["quiet_high"] = read_field(S.block_of(stub, Image(content=b"x", detail="high")), "detail")
        o["quiet_default"] = read_field(S.block_of(stub, Image(content=b"x")), "detail")
    o["quiet_warn_count"] = quiet.count

    # the normalized value is what reaches the provider
    o["render_high"] = render_openai(S.block_of(stub, Image(content=b"x", detail="HIGH")))
    o["render_downgraded_detail"] = render_openai(downgraded)["image_url"]["detail"]

    # the helpers r2 names, where they exist
    normalize_detail = S.attachment_symbol("normalize_detail", required=False)
    o["normalize_detail_present"] = normalize_detail is not None
    if normalize_detail is not None:
        o["nd_none"] = normalize_detail(None)
        o["nd_high"] = normalize_detail("HIGH")
        o["nd_low"] = normalize_detail(" Low ")
        with S.capture_warnings() as recorder:
            o["nd_ultra"] = normalize_detail("ultra")
        o["nd_ultra_warn_count"] = recorder.count
    vocabulary = S.attachment_symbol("_SUPPORTED_IMAGE_DETAILS", "SUPPORTED_IMAGE_DETAILS", required=False)
    o["vocabulary"] = list(vocabulary) if vocabulary is not None else None
    return o


PROBES = {
    "test_open::test_open_feature__one_canonical_block_every_provider_renders_from": probe_open,
    "test_r1::test_rule__per_kind_ceiling_measured_on_the_block_and_checked_before_the_hook": probe_r1_rule,
    "test_r1::test_scope__the_prompt_aggregate_is_summed_after_every_block_was_built": probe_r1_scope,
    "test_r1::test_exclusions__a_url_block_is_never_measured_and_never_counted": probe_r1_exclusions,
    "test_r1::test_failure_behavior__a_thirteenth_attachment_is_refused_before_anything_is_read": probe_r1_failure_behavior,
    "test_r1::test_observability__a_document_block_costs_fourteen_hundred_tokens": probe_r1_observability,
    "test_r2::test_rule__every_block_carries_a_short_sha256_fingerprint_of_its_payload": probe_r2_rule,
    "test_r2::test_scope__the_filename_is_capped_at_sixty_four_with_its_extension_kept": probe_r2_scope,
    "test_r2::test_exclusions__a_url_block_is_fingerprinted_over_its_url_text": probe_r2_exclusions,
    "test_r2::test_failure_behavior__an_unsupported_detail_is_downgraded_to_auto_with_one_warning": probe_r2_failure_behavior,
}


def main(out_path: str, seed: str) -> int:
    # The run's inputs, re-drawn from the seed root chose, before any probe
    # builds an attachment. `fixture_spec` says why: with fixed bytes an
    # `observations.json` recorded from one run satisfies every other one, and a
    # pristine tree plus an `atexit` hook scored reward 1.0 that way.
    S.apply_seed(fixture_spec.derive(seed))
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
