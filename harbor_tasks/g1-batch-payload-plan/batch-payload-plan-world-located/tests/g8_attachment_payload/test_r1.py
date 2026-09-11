"""attachment-payload — hidden requirement r1: the size and count ceilings the base owns.

    rule              every base64 payload is measured once, in MB, from its base64
                      length, kept on the block as `size_mb`, and compared strictly
                      against a per-kind ceiling — 20.0 MB for a block whose kind is
                      "image", 24.0 MB for one whose kind is "document" — raising
                      `AttachmentTooLarge(kind, size_mb, limit_mb)` inside
                      `_canonical_attachment_block`, BEFORE the payload is offered to
                      `file_upload_limit_check`
    scope             a whole-prompt aggregate of 45.0 MB belongs to
                      `_handle_multi_modal_prompt` and is evaluated after every block has
                      been built and every provider hook has fired: 3x18.0 + 6.0 reports
                      `kind == "prompt"`, `size_mb == 60.0` (the prompt total, not the
                      crossing total) and four hook calls
    exclusions        a url block is never measured: `size_mb is None`, no per-kind
                      ceiling is applied to it, it is never offered to the hook, and it
                      adds nothing to the 45.0 MB prompt sum
    failure_behavior  more than 12 attachments in one message is refused with
                      `TooManyAttachments(count, limit)`, counted before a single block is
                      built, so nothing is serialized and the hook is never called; texts
                      are not counted and 12 attachments are fine
    observability     `calculate_input_tokens` prices a "file" or "document" block at 1400
                      tokens rather than the image rate, so the mixed list totals 2975

The sizes are chosen so the five separate. `rule` crosses 20.0 with a 24.0 MB
image and clears 24.0 with the identical bytes labelled a document; `scope`
crosses the aggregate only, with every attachment individually legal and a fourth
one past the crossing point; `exclusions` never crosses anything; `failure_behavior`
uses 13 four-byte payloads, far under every megabyte ceiling; `observability`
touches no attachment at all.
"""
from __future__ import annotations

import base64

import pytest

from harness import read_field
from test_open import (
    PDF_B64,
    PDF_BYTES,
    REMOTE_JPEG,
    FakeEncoder,
    StubOnline,
    attachment_symbol,
    block_of,
    importable,
    raising_stub,
    write,
)

try:
    from bespokelabs.curator.file_utilities import get_base64_size
    from bespokelabs.curator.types.prompt import File, Image, _MultiModalPrompt
except Exception:  # pragma: no cover — reported by importable(), per test
    File = Image = _MultiModalPrompt = get_base64_size = None


# `get_base64_size` reads (len * 3) // 4 - padding bytes, so these strings measure
# exactly, with no rounding to argue about.
PAYLOAD_24MB = "A" * 33_554_432   # -> 24.0 MB
PAYLOAD_18MB = "A" * 25_165_824   # -> 18.0 MB
PAYLOAD_6MB = "A" * 8_388_608     # -> 6.0 MB


def too_large():
    """The exception r1 names, from wherever the implementation defined it."""
    return attachment_symbol("AttachmentTooLarge")


def triple(exc):
    """(kind, size_mb, limit_mb) off the raised exception, however it spells them."""
    return (read_field(exc, "kind"), read_field(exc, "size_mb"), read_field(exc, "limit_mb"))


# =============================================================================
# rule — a per-kind ceiling, measured on the block, checked before the hook
# =============================================================================
def test_rule__per_kind_ceiling_measured_on_the_block_and_checked_before_the_hook(tmp_path):
    """20.0 MB for an image, 24.0 MB for a document, strictly greater, base first."""
    importable()
    AttachmentTooLarge = too_large()
    assert issubclass(AttachmentTooLarge, attachment_symbol("AttachmentError"))

    # the measurement is taken from the base64 length, in MB, and kept on the block
    stub = StubOnline()
    block = block_of(stub, File(url=write(tmp_path, "report.pdf", PDF_BYTES)))
    measured = read_field(block, "size_mb")
    assert isinstance(measured, float)
    assert measured == get_base64_size(PDF_B64) == 8.58306884765625e-06

    # an image payload over 20.0 MB is refused, by name, with the stated attributes
    refusing = raising_stub("provider")
    with pytest.raises(AttachmentTooLarge) as caught:
        block_of(refusing, Image(content=PAYLOAD_24MB))
    exc = caught.value
    assert triple(exc) == ("image", 24.0, 20.0)
    assert str(exc) == "image attachment is 24.0 MB, over the 20.0 MB limit."
    # ...and it is refused by the BASE, before the provider hook is consulted: the
    # hook here raises RuntimeError for anything it is shown, and was shown nothing
    assert refusing.calls == []

    # the very same 24.0 MB, resolved as a document, is inside the higher ceiling and
    # is handed on to the provider hook, which is what refuses it
    with pytest.raises(RuntimeError) as runtime:
        block_of(refusing, Image(content=PAYLOAD_24MB, mime_type="application/pdf"))
    assert str(runtime.value) == "provider"

    # a recording stub sees the same document accepted, sized and offered
    recording = StubOnline()
    document = block_of(recording, Image(content=PAYLOAD_24MB, mime_type="application/pdf"))
    assert read_field(document, "kind") == "document"
    assert read_field(document, "size_mb") == 24.0
    assert recording.calls == [PAYLOAD_24MB]


# =============================================================================
# scope — a 45.0 MB aggregate, owned by the prompt, taken after the fact
# =============================================================================
def test_scope__the_prompt_aggregate_is_summed_after_every_block_was_built():
    """3 x 18.0 + 6.0: sixty megabytes, four hook calls, one "prompt" refusal."""
    importable()
    AttachmentTooLarge = too_large()

    images = [
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_18MB),
        Image(content=PAYLOAD_6MB),
    ]
    stub = StubOnline()
    with pytest.raises(AttachmentTooLarge) as caught:
        stub._handle_multi_modal_prompt(_MultiModalPrompt(texts=["over"], images=images))
    exc = caught.value
    # every image is individually legal (18.0 and 6.0 are both under 20.0), so only
    # the aggregate can have refused this prompt
    assert triple(exc) == ("prompt", 60.0, 45.0)
    # the sum is the whole prompt's, not the running total at the crossing point:
    # the fourth attachment was built and offered before anything was compared
    assert len(stub.calls) == 4

    # control: the first two alone are 36.0 MB, and pass
    control = StubOnline()
    content = control._handle_multi_modal_prompt(_MultiModalPrompt(texts=[], images=images[:2]))
    assert len(content) == 2
    assert len(control.calls) == 2


# =============================================================================
# exclusions — a url block is not measured, not compared and not offered
# =============================================================================
def test_exclusions__a_url_block_is_never_measured_and_never_counted(tmp_path):
    """`size_mb is None` for a remote attachment, and it adds nothing to the sum."""
    importable()
    too_large()          # the ceiling this fact excludes url blocks from must exist

    stub = StubOnline()
    remote = block_of(stub, Image(url=REMOTE_JPEG))
    assert read_field(remote, "source") == "url"
    assert read_field(remote, "size_mb") is None
    assert stub.calls == []          # nothing was read, so nothing was offered

    # a prompt made only of remote urls passes both ceilings, whatever is behind them
    urls = StubOnline()
    remote_only = _MultiModalPrompt(
        texts=["describe"],
        images=[Image(url=REMOTE_JPEG) for _ in range(5)],
        files=[File(url="https://cdn.example.com/reports/report.pdf")],
    )
    content = urls._handle_multi_modal_prompt(remote_only)
    assert len(content) == 7
    assert urls.calls == []

    # and a url alongside a base64 payload contributes nothing to the prompt sum:
    # six remote attachments beside one small document weigh what the document
    # weighs. (Deliberately a few bytes, not a few megabytes: this fact is that
    # urls are not counted, and it must hold whatever the per-kind ceiling is.)
    mixed = StubOnline()
    content = mixed._handle_multi_modal_prompt(
        _MultiModalPrompt(
            texts=[],
            images=[Image(url=REMOTE_JPEG) for _ in range(5)],
            files=[
                File(url="https://cdn.example.com/reports/report.pdf"),
                File(url=write(tmp_path, "small.pdf", PDF_BYTES)),
            ],
        )
    )
    assert len(content) == 7
    assert mixed.calls == [PDF_B64]


# =============================================================================
# failure_behavior — at most twelve attachments, counted before anything is read
# =============================================================================
def test_failure_behavior__a_thirteenth_attachment_is_refused_before_anything_is_read():
    """`TooManyAttachments(13, 12)`, and an empty `calls` list behind it."""
    importable()
    TooManyAttachments = attachment_symbol("TooManyAttachments")
    assert issubclass(TooManyAttachments, attachment_symbol("AttachmentError"))
    assert issubclass(TooManyAttachments, ValueError)

    limit = attachment_symbol("_ATTACHMENT_COUNT_LIMIT", "ATTACHMENT_COUNT_LIMIT", required=False)
    if limit is not None:
        assert limit == 12

    tiny = Image(content=b"x")
    stub = StubOnline()
    with pytest.raises(TooManyAttachments) as caught:
        stub._handle_multi_modal_prompt(_MultiModalPrompt(texts=["a"], images=[tiny] * 13))
    exc = caught.value
    assert (read_field(exc, "count"), read_field(exc, "limit")) == (13, 12)
    assert str(exc) == "Prompt has 13 attachments, over the limit of 12."
    # counted first: not one of the thirteen was serialized or offered
    assert stub.calls == []

    # twelve is fine — the comparison is strictly greater
    twelve = StubOnline()
    content = twelve._handle_multi_modal_prompt(_MultiModalPrompt(texts=["a"], images=[tiny] * 12))
    assert len(content) == 13
    assert len(twelve.calls) == 12

    # texts are not attachments, so forty of them next to one image is fine
    texts = StubOnline()
    content = texts._handle_multi_modal_prompt(_MultiModalPrompt(texts=["a"] * 40, images=[tiny]))
    assert len(content) == 41
    assert len(texts.calls) == 1


# =============================================================================
# observability — what a document block costs the OpenAI estimator
# =============================================================================
def test_observability__a_document_block_costs_fourteen_hundred_tokens():
    """5 + 85 + 85 + 1400 + 1400 + 0 == 2975, with one token per character."""
    importable()
    from bespokelabs.curator.request_processor.openai_request_mixin import calculate_input_tokens

    encoder = FakeEncoder()
    text_block = {"type": "text", "text": "hello"}
    openai_image = {"type": "image_url", "image_url": {"url": "x", "detail": "auto"}}
    anthropic_image = {"type": "image", "source": {"type": "url", "url": "x"}}
    openai_file = {
        "type": "file",
        "file": {"filename": "r.pdf", "file_data": f"data:application/pdf;base64,{PDF_B64}"},
    }
    anthropic_document = {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": PDF_B64},
    }
    unknown = {"type": "thinking", "thinking": "ignored"}

    # a document is priced flat, at neither the image rate nor its payload length
    assert calculate_input_tokens([openai_file], encoder) == 1400
    assert calculate_input_tokens([anthropic_document], encoder) == 1400
    assert calculate_input_tokens([openai_image], encoder) == 85
    assert calculate_input_tokens([anthropic_image], encoder) == 85

    total = calculate_input_tokens(
        [text_block, openai_image, anthropic_image, openai_file, anthropic_document, unknown],
        encoder,
    )
    assert total == 5 + 85 + 85 + 1400 + 1400 + 0 == 2975
    assert isinstance(total, int)

    per_document = attachment_symbol("_OPENAI_TOKENS_PER_DOCUMENT", "OPENAI_TOKENS_PER_DOCUMENT", required=False)
    if per_document is None:
        from bespokelabs.curator.request_processor import openai_request_mixin

        per_document = getattr(openai_request_mixin, "_OPENAI_TOKENS_PER_DOCUMENT", None)
    if per_document is not None:
        assert per_document == 1400

    assert base64.b64decode(PDF_B64) == PDF_BYTES
