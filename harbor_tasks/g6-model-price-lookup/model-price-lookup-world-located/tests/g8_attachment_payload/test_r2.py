"""attachment-payload — hidden requirement r2: what the canonical block records about itself.

    rule              every block carries a short content fingerprint,
                      `"sha256:" + sha256(payload).hexdigest()[:12]`, computed by a pure
                      `attachment_fingerprint(payload)` and set on the block from its own
                      payload — `b"%PDF-1.4\\n"` fingerprints as "sha256:fc1c4358d4aa"
    scope             the derived `filename` is capped at 64 characters with the extension
                      kept, `name[: 64 - len(ext)] + ext`; only `filename` is capped, the
                      payload keeps the full url and the attachment's own `url` is untouched
    exclusions        a url block is fingerprinted too, rather than left without one, and
                      the digest is taken over the payload STRING — the url exactly as
                      given, query and fragment included, and the base64 text rather than
                      the bytes it decodes to
    failure_behavior  an image `detail` outside ("auto", "low", "high") is normalized to
                      "auto" at block-build time with exactly one warning, rather than
                      passed through to the provider or rejected at construction;
                      `Image.detail` itself keeps whatever the caller wrote

The four separate cleanly: `rule` and `exclusions` read `fingerprint` off base64
and url blocks respectively, `scope` reads `filename` off a block whose payload it
also checks was left alone, and `failure_behavior` reads `detail`. No test here
asserts a size, a count or a token price — those are r1's.
"""
from __future__ import annotations

import base64
import hashlib
import logging

import pytest

from harness import read_field
from test_open import (
    PDF_B64,
    PDF_BYTES,
    REMOTE_JPEG,
    StubOnline,
    attachment_symbol,
    block_of,
    importable,
    write,
)

try:
    from bespokelabs.curator.types.prompt import File, Image
except Exception:  # pragma: no cover — reported by importable(), per test
    File = Image = None


def render_openai(block) -> dict:
    """The OpenAI renderer named by the open ticket, looked up when it is needed.

    Imported lazily and reported by name: a tree without it should say so, not
    fail these tests with a `NoneType` from a module-level import that collapsed.
    """
    from bespokelabs.curator.request_processor.online import base_online_request_processor as base

    fn = getattr(base, "_render_openai_block", None)
    if fn is None:
        pytest.fail("base_online_request_processor has no _render_openai_block(); the open ticket names it.")
    return fn(block)


def digest_of(text: str) -> str:
    """The fingerprint r2 describes, spelled out here rather than imported."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


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


class Recorder(logging.Handler):
    """One recorder, hung on every logger that could carry the warning.

    Which module says it is not the requirement; that it is said once is. The
    handler goes on the root logger and on curator's own, and records are deduped
    by identity, so "exactly one" still means one in total however the
    implementation routes it.
    """

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.seen: dict[int, logging.LogRecord] = {}

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.seen[id(record)] = record

    @property
    def count(self) -> int:
        return len(self.seen)


class capture_warnings:
    """Context manager yielding a `Recorder` over the block it wraps."""

    def __enter__(self) -> Recorder:
        self.recorder = Recorder()
        self.loggers = [logging.getLogger(), logging.getLogger("curator")]
        self.levels = []
        for log in self.loggers:
            log.addHandler(self.recorder)
            self.levels.append(log.level)
            log.setLevel(min(log.level or logging.WARNING, logging.WARNING))
        return self.recorder

    def __exit__(self, *exc):
        for log, level in zip(self.loggers, self.levels):
            log.removeHandler(self.recorder)
            log.setLevel(level)
        return False


# =============================================================================
# rule — a short sha256 fingerprint on every block, taken from its payload
# =============================================================================
def test_rule__every_block_carries_a_short_sha256_fingerprint_of_its_payload(tmp_path):
    """A "sha256:" prefix plus twelve hex characters, taken from the block's own payload."""
    importable()
    stub = StubOnline()

    pdf = File(url=write(tmp_path, "report.pdf", PDF_BYTES))
    block = block_of(stub, pdf)
    fingerprint = read_field(block, "fingerprint")
    assert fingerprint == "sha256:fc1c4358d4aa"
    assert fingerprint == digest_of(PDF_B64)
    assert fingerprint.startswith("sha256:") and len(fingerprint) == len("sha256:") + 12

    # it follows the payload, so a second attachment with different bytes differs
    other = block_of(stub, Image(content=b"x"))
    assert read_field(other, "fingerprint") == "sha256:5e21d86b709b" == digest_of("eA==")
    assert read_field(other, "fingerprint") != fingerprint
    assert read_field(other, "payload") == "eA=="

    # the same bytes fingerprint the same way, whatever carried them
    same_bytes = block_of(stub, Image(content=PDF_BYTES, mime_type="application/pdf"))
    assert read_field(same_bytes, "fingerprint") == "sha256:fc1c4358d4aa"

    # the helper r2 names, where it exists, is the pure function it describes
    helper = attachment_symbol("attachment_fingerprint", required=False)
    if helper is not None:
        assert helper(PDF_B64) == "sha256:fc1c4358d4aa"
        assert helper("eA==") == "sha256:5e21d86b709b"
        assert helper("") == digest_of("")
    hex_len = attachment_symbol("_ATTACHMENT_FINGERPRINT_HEX_LEN", "ATTACHMENT_FINGERPRINT_HEX_LEN", required=False)
    if hex_len is not None:
        assert hex_len == 12


# =============================================================================
# scope — the filename is capped at 64, extension kept, and nothing else is cut
# =============================================================================
def test_scope__the_filename_is_capped_at_sixty_four_with_its_extension_kept():
    """A 73-character basename renders as 64 characters beside the full url."""
    importable()
    stub = StubOnline()

    long_pdf = File(url=LONG_PDF_URL)
    block = block_of(stub, long_pdf)
    capped = read_field(block, "filename")
    assert capped == "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf"
    assert len(capped) == 64 and capped.endswith(".pdf")

    # only the filename is cut: the payload is the whole url, and the attachment
    # itself was never modified
    assert read_field(block, "payload") == LONG_PDF_URL
    assert long_pdf.url == LONG_PDF_URL
    assert render_openai(block) == {
        "type": "file",
        "file": {
            "filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf",
            "file_url": LONG_PDF_URL,
        },
    }

    # exactly 64 is untouched — the cap applies to what is LONGER than 64
    boundary = read_field(block_of(stub, File(url=EXACTLY_64_URL)), "filename")
    assert boundary == "2024-q4-consolidated-financial-statements-and-notes-final-v3.pdf"
    assert len(boundary) == 64

    # with no extension there is nothing to keep, so it is the first 64 characters
    extensionless = block_of(stub, File(url=LONG_EXTENSIONLESS_URL, mime_type="application/pdf"))
    assert read_field(extensionless, "filename") == "ledger-entries-consolidated-2024-q4-final-copy-for-review-board-"
    assert len(read_field(extensionless, "filename")) == 64

    # a short name is left exactly as it came
    assert read_field(block_of(stub, File(url="https://cdn.example.com/a/report.pdf")), "filename") == "report.pdf"


# =============================================================================
# exclusions — a url block is fingerprinted too, over the payload string
# =============================================================================
def test_exclusions__a_url_block_is_fingerprinted_over_its_url_text(tmp_path):
    """A url block gets one too, and the digest covers the payload STRING.

    Deliberately relational rather than literal: which digest, how long and with
    what prefix is r2's `rule`, and asserting the exact string here would fail
    this fact for an implementation whose only mistake was in that one. What is
    asserted is that a url block HAS a fingerprint, that it is the fingerprint of
    its url text exactly as given — query and fragment included — and that a
    base64 block's covers its base64 text rather than the bytes it decodes to.
    """
    importable()
    stub = StubOnline()

    remote = block_of(stub, Image(url=REMOTE_JPEG))
    assert read_field(remote, "source") == "url"
    fingerprint = read_field(remote, "fingerprint")
    assert fingerprint is not None            # a url block is not left without one

    # The same characters, carried as a base64 payload instead of a url: an
    # `Image` with inline `str` content serializes to that string unchanged, so
    # the two blocks have identical payloads by different routes. Fingerprinting
    # the payload string gives them the same id; hashing something else (the url
    # minus its query, the decoded bytes, the whole block) does not.
    inline = block_of(stub, Image(content=REMOTE_JPEG))
    assert read_field(inline, "source") == "base64"
    assert read_field(inline, "payload") == REMOTE_JPEG
    assert fingerprint == read_field(inline, "fingerprint")

    # the query is part of what is hashed: the same asset without it differs
    bare = block_of(stub, Image(url="https://cdn.example.com/photos/cat.jpeg"))
    assert read_field(bare, "fingerprint") != fingerprint
    # ...and so is a fragment, though neither reaches the filename
    fragment = block_of(stub, Image(url="https://cdn.example.com/photos/cat.jpeg#page=2"))
    assert read_field(fragment, "fingerprint") != read_field(bare, "fingerprint")

    # a base64 block covers its base64 TEXT, never the bytes it decodes to
    local = block_of(stub, File(url=write(tmp_path, "report.pdf", PDF_BYTES)))
    text_id = read_field(local, "fingerprint")
    assert text_id is not None
    assert hashlib.sha256(PDF_BYTES).hexdigest()[:12] not in text_id


# =============================================================================
# failure_behavior — an unknown detail is downgraded, once, with a warning
# =============================================================================
def test_failure_behavior__an_unsupported_detail_is_downgraded_to_auto_with_one_warning():
    """From "HIGH" to "high", " Low " to "low", and "ultra" to "auto" with one warning."""
    importable()
    stub = StubOnline()

    # construction never rejects a detail; the model keeps what the caller wrote
    written = Image(content=b"x", detail="ultra")
    assert written.detail == "ultra"
    assert Image(content=b"x", detail="HIGH").detail == "HIGH"

    # the block carries the normalized value
    assert read_field(block_of(stub, Image(content=b"x", detail="HIGH")), "detail") == "high"
    assert read_field(block_of(stub, Image(content=b"x", detail=" Low ")), "detail") == "low"
    assert read_field(block_of(stub, Image(content=b"x", detail="auto")), "detail") == "auto"

    # an unknown detail is downgraded rather than sent or refused, and says so once
    with capture_warnings() as recorder:
        downgraded = block_of(stub, Image(content=b"x", detail="ultra"))
    assert read_field(downgraded, "detail") == "auto"
    assert recorder.count == 1

    # a supported detail, and an absent one, say nothing
    with capture_warnings() as quiet:
        assert read_field(block_of(stub, Image(content=b"x", detail="high")), "detail") == "high"
        assert read_field(block_of(stub, Image(content=b"x")), "detail") == "auto"
    assert quiet.count == 0

    # the normalized value is what reaches the provider
    assert render_openai(block_of(stub, Image(content=b"x", detail="HIGH"))) == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,eA==", "detail": "high"},
    }
    assert render_openai(downgraded)["image_url"]["detail"] == "auto"

    # the helpers r2 names, where they exist
    normalize_detail = attachment_symbol("normalize_detail", required=False)
    if normalize_detail is not None:
        assert normalize_detail(None) == "auto"
        assert normalize_detail("HIGH") == "high"
        assert normalize_detail(" Low ") == "low"
        with capture_warnings() as recorder:
            assert normalize_detail("ultra") == "auto"
        assert recorder.count == 1
    vocabulary = attachment_symbol("_SUPPORTED_IMAGE_DETAILS", "SUPPORTED_IMAGE_DETAILS", required=False)
    if vocabulary is not None:
        assert tuple(vocabulary) == ("auto", "low", "high")

    assert base64.b64encode(b"x").decode() == "eA=="
