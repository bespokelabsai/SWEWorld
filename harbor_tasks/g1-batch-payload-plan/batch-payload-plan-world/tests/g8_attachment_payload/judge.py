"""g8 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and
applies the assertions the g8 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged. No agent
code runs here, so the report cannot be forged; and `test.sh` locks this file to
0600 root, so the worker cannot read the numbers below to forge an observation
that matches them. That pair is what closes the forgery in tasks/lessons.md
(2026-09-09) that a uid alone could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files
stay the human-readable source of truth and the fact<->test bijection. Everything
below is either an expected answer literal or a stdlib re-derivation of one (the
fingerprint FORMULA `digest_of`, the base64 of an input payload) — a re-derivation
is safe here because this file is unreachable by the worker, and it would be a
forgery leak in `probe_support.py`, which the worker copies into its jail.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# Answer-free INPUTS, re-derived here so the expected render dicts can embed the
# exact base64 the renderers produce. Inputs, not answers — but this file holds
# both, and the worker cannot read either.
PDF_BYTES = b"%PDF-1.4\n"
PDF_B64 = base64.b64encode(PDF_BYTES).decode()      # "JVBERi0xLjQK"
B64_1234 = base64.b64encode(b"1234").decode()       # "MTIzNA=="
B64_X = base64.b64encode(b"x").decode()             # "eA=="
REMOTE_JPEG = "https://cdn.example.com/photos/cat.jpeg?size=large"
LONG_PDF_URL = (
    "https://cdn.example.com/reports/"
    "2024-q4-consolidated-financial-statements-and-notes-final-approved-v3.pdf"
)


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ne(got, want, msg=""):
    if got == want:
        raise Fail(f"{msg}: {got!r} == {want!r} (should differ)")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def approx_eq(a, b, *, rel: float = 1e-9, abs_: float = 1e-12) -> bool:
    return abs(a - b) <= max(rel * abs(b), abs_)


def approxs(got, want, msg="", *, rel=1e-9, abs_=1e-12):
    if not approx_eq(got, want, rel=rel, abs_=abs_):
        raise Fail(f"{msg}: {got!r} !~ {want!r}")


def digest_of(text: str) -> str:
    """The fingerprint r2 describes: `"sha256:" + sha256(text)[:12]`."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def raised(info, *, mro=None, string=None, msg=""):
    """The `pytest.raises(...)` half: it raised, of the expected type, with the
    expected message. Exception ATTRIBUTES are checked by the caller, because
    float attrs (size_mb, limit_mb) need an approx comparison eq cannot give."""
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    if string is not None:
        eq(info.get("str"), string, f"{msg}: message")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["fallback_name"], "attachment.bin", "_FALLBACK_ATTACHMENT_FILENAME")
    ok("ValueError" in o["attachment_error_mro"], "AttachmentError subclasses ValueError")
    ok("AttachmentError" in o["unknown_mime_mro"], "UnknownAttachmentMimeType subclasses AttachmentError")
    ok("AttachmentError" in o["missing_local_mro"], "MissingLocalAttachment subclasses AttachmentError")
    eq(o["normalize_pdf"], "application/pdf", "normalize_mime_type pdf")
    ok(o["normalize_none"] is None, "normalize_mime_type(None)")
    ok(o["normalize_empty"] is None, "normalize_mime_type('')")

    eq(o["mime_remote_jpeg"], "image/jpeg", "remote jpeg mime (query stripped)")
    ok(o["mime_asset"] is None, "no image/png fallback")
    eq(o["mime_file_pdf"], "application/pdf", "file pdf mime")
    eq(o["mime_png_content"], "image/png", "png sniffed from content")

    ok(o["is_remote_jpeg"] is True, "remote jpeg is_remote")
    ok(o["is_remote_upper"] is True, "uppercase https is_remote")
    ok(o["is_remote_s3"] is False, "s3 not remote")
    ok(o["is_remote_local"] is False, "local file not remote")

    eq(o["attachment_types"], ["image", "file"], "attachments() order")
    ok(o["attachments_fresh"], "attachments() returns a fresh list")
    eq(o["images_files_len"], [1, 1], "images/files unchanged")

    ok(o["file_block_isinstance"] is True, "block is an AttachmentBlock")
    eq(o["file_block_triple"], ["image", "base64", "image/png"], "png file -> image block")
    eq(o["file_block_name_detail"], ["chart.png", "auto"], "png file name/detail")
    eq(o["image_block_triple"], ["document", "base64", "application/pdf"], "pdf image -> document block")
    eq(o["image_block_name_detail"], ["attachment.bin", None], "pdf image name/detail")
    eq(o["image_block_payload"], PDF_B64, "pdf image payload")

    raised(o["frozen"], msg="block is frozen")

    eq(o["remote_block_triple"], ["image", "url", REMOTE_JPEG], "remote jpeg -> url block")
    eq(o["remote_block_name_detail"], ["cat.jpeg", "auto"], "remote jpeg name/detail")

    raised(o["miss_typo"], mro="MissingLocalAttachment", msg="missing typo")
    eq(o["miss_typo"].get("url"), "/tmp/definitely-missing/typo.png", "missing typo url")
    raised(o["miss_s3"], mro="MissingLocalAttachment", msg="missing s3")
    eq(o["miss_s3"].get("url"), "s3://bucket/report.pdf", "missing s3 url")
    raised(o["miss_notes"], mro="MissingLocalAttachment", msg="missing beats unguessable")

    raised(o["unknown_download"], mro="UnknownAttachmentMimeType", msg="unknown download")
    eq(o["unknown_download"].get("url"), "https://example.com/download", "unknown download url")
    eq(o["unknown_download"].get("attachment_type"), "file", "unknown download attachment_type")
    ok("ValueError" in o["unknown_download"].get("mro", []), "unknown download is a ValueError")
    raised(o["unknown_asset"], mro="UnknownAttachmentMimeType", msg="unknown asset")
    eq(o["unknown_asset"].get("attachment_type"), "image", "unknown asset attachment_type")
    raised(o["unknown_extensionless"], mro="UnknownAttachmentMimeType", msg="unknown extensionless")

    eq(o["render_openai_pdf"], {
        "type": "file",
        "file": {"filename": "report.pdf", "file_data": f"data:application/pdf;base64,{PDF_B64}"},
    }, "openai render of local pdf")
    eq(o["render_openai_remote"], {
        "type": "image_url",
        "image_url": {"url": REMOTE_JPEG, "detail": "auto"},
    }, "openai render of remote image")
    eq(o["render_openai_file"], {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{B64_1234}", "detail": "auto"},
    }, "openai render of png file")
    eq(o["remote_pdf_kind_source"], ["document", "url"], "remote pdf kind/source")
    eq(o["render_openai_remote_pdf"], {
        "type": "file",
        "file": {"filename": "report.pdf", "file_url": "https://cdn.example.com/report.pdf"},
    }, "openai render of remote pdf")

    eq(o["render_anthropic_pdf"], {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": PDF_B64},
    }, "anthropic render of local pdf")
    eq(o["render_anthropic_remote"], {
        "type": "image",
        "source": {"type": "url", "url": REMOTE_JPEG},
    }, "anthropic render of remote image")
    ok(o["anthropic_method_matches"], "anthropic._render_attachment_block == module renderer")
    ok(o["lite_anthropic_matches"], "litellm anthropic-model dispatch")
    ok(o["lite_openai_matches"], "litellm openai-model dispatch")
    ok(o["format_multimodal_matches"], "_format_multimodal one-shot")
    ok(o["format_multimodal_mime_matches"], "_format_multimodal ignores mime_type")

    eq(o["content_types"], ["image_url", "file", "text"], "attachments before text")
    eq(o["content"], [
        {"type": "image_url", "image_url": {"url": REMOTE_JPEG, "detail": "auto"}},
        {"type": "file", "file": {"filename": "report.pdf", "file_data": f"data:application/pdf;base64,{PDF_B64}"}},
        {"type": "text", "text": "Summarise these"},
    ], "handle_multi_modal_prompt content")
    eq(o["ordered_types"], ["image_url", "file", "text", "text"], "two texts stay in order")
    eq(o["ordered_texts"], ["a", "b"], "text order preserved")
    ok(o["ordered_fresh"], "handle_multi_modal_prompt returns a fresh list")

    eq(o["calc_hello_str"], 5, "calc of a bare string")
    eq(o["calc_hello_block"], 5, "calc of a text block")
    eq(o["calc_image_content0"], 85, "calc of an image block")
    eq(o["tokens_per_image_low"], 85, "_OPENAI_TOKENS_PER_IMAGE['low']")
    eq(o["calc_anthropic_image"], 85, "calc of an anthropic image block")
    for i, priced in enumerate(o["priced_docs"]):
        ok(priced >= 0, f"document block priced non-negative [{i}]")
    ok(all(o["priced_docs_is_int"]), "document block priced as an int")

    eq(o["local_pdf_basename"], "report.pdf", "local pdf basename")
    ok(o["get_base64_size_pdf"] > 0, "get_base64_size positive")


# ---------------------------------------------------------------------------
# r1 — the size and count ceilings the base owns
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    ok("AttachmentError" in o["too_large_mro"], "AttachmentTooLarge subclasses AttachmentError")
    approxs(o["measured"], 8.58306884765625e-06, "measured size_mb")
    ok(o["measured_is_float"], "size_mb is a float")
    approxs(o["get_base64_size_pdf"], 8.58306884765625e-06, "get_base64_size")
    approxs(o["measured"], o["get_base64_size_pdf"], "measured == get_base64_size")

    raised(o["over_image"], mro="AttachmentTooLarge",
           string="image attachment is 24.0 MB, over the 20.0 MB limit.", msg="image over 20 MB")
    eq(o["over_image"].get("kind"), "image", "over-image kind")
    approxs(o["over_image"].get("size_mb"), 24.0, "over-image size_mb")
    approxs(o["over_image"].get("limit_mb"), 20.0, "over-image limit_mb")
    eq(o["refusing_calls_after_over"], 0, "refused by the base, before the hook")

    raised(o["doc_runtime"], mro="RuntimeError", string="provider", msg="document under 24 MB reaches hook")
    eq(o["doc_kind"], "document", "same bytes as document")
    approxs(o["doc_size_mb"], 24.0, "document size_mb")
    eq(o["recording_calls_len"], 1, "document offered once")
    ok(o["recording_calls_is_payload"], "document offered its own payload")


def judge_r1_scope(o):
    raised(o["over"], mro="AttachmentTooLarge", msg="prompt aggregate")
    eq(o["over"].get("kind"), "prompt", "aggregate kind")
    approxs(o["over"].get("size_mb"), 60.0, "aggregate size_mb (whole prompt)")
    approxs(o["over"].get("limit_mb"), 45.0, "aggregate limit_mb")
    eq(o["stub_calls_len"], 4, "all four blocks built and offered")
    eq(o["control_content_len"], 2, "36 MB control content")
    eq(o["control_calls_len"], 2, "36 MB control calls")


def judge_r1_exclusions(o):
    eq(o["remote_source"], "url", "remote is a url block")
    ok(o["remote_size_mb"] is None, "url block is not measured")
    eq(o["stub_calls_len"], 0, "url block not offered")
    eq(o["urls_content_len"], 7, "remote-only prompt content")
    eq(o["urls_calls_len"], 0, "remote-only prompt offers nothing")
    eq(o["mixed_content_len"], 7, "mixed prompt content")
    eq(o["mixed_calls"], [PDF_B64], "only the one document is offered")


def judge_r1_failure_behavior(o):
    ok("AttachmentError" in o["too_many_mro"], "TooManyAttachments subclasses AttachmentError")
    ok("ValueError" in o["too_many_mro"], "TooManyAttachments subclasses ValueError")
    if o["count_limit"] is not None:
        eq(o["count_limit"], 12, "_ATTACHMENT_COUNT_LIMIT")
    raised(o["thirteen"], mro="TooManyAttachments",
           string="Prompt has 13 attachments, over the limit of 12.", msg="thirteen attachments")
    eq(o["thirteen"].get("count"), 13, "thirteen count")
    eq(o["thirteen"].get("limit"), 12, "thirteen limit")
    eq(o["stub_calls_len"], 0, "counted before anything read")
    eq(o["twelve_content_len"], 13, "twelve attachments + one text")
    eq(o["twelve_calls_len"], 12, "twelve offered")
    eq(o["texts_content_len"], 41, "forty texts + one image")
    eq(o["texts_calls_len"], 1, "texts are not attachments")


def judge_r1_observability(o):
    eq(o["calc_openai_file"], 1400, "openai file priced flat")
    eq(o["calc_anthropic_document"], 1400, "anthropic document priced flat")
    eq(o["calc_openai_image"], 85, "openai image rate")
    eq(o["calc_anthropic_image"], 85, "anthropic image rate")
    eq(o["total"], 2975, "mixed list total")
    ok(o["total_is_int"], "total is an int")
    if o["per_document"] is not None:
        eq(o["per_document"], 1400, "_OPENAI_TOKENS_PER_DOCUMENT")
    ok(o["b64_roundtrip"], "PDF_B64 decodes to PDF_BYTES")


# ---------------------------------------------------------------------------
# r2 — what the canonical block records about itself
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    eq(o["fingerprint"], "sha256:fc1c4358d4aa", "pdf fingerprint")
    eq(o["fingerprint"], digest_of(PDF_B64), "pdf fingerprint == digest_of(PDF_B64)")
    ok(o["fingerprint"].startswith("sha256:") and len(o["fingerprint"]) == len("sha256:") + 12,
       "fingerprint shape")
    eq(o["other_fingerprint"], "sha256:5e21d86b709b", "other fingerprint")
    eq(o["other_fingerprint"], digest_of("eA=="), "other fingerprint == digest_of('eA==')")
    ne(o["other_fingerprint"], o["fingerprint"], "fingerprint follows payload")
    eq(o["other_payload"], "eA==", "other payload")
    eq(o["same_bytes_fingerprint"], "sha256:fc1c4358d4aa", "same bytes fingerprint the same")
    if o["helper_present"]:
        eq(o["helper_pdf"], "sha256:fc1c4358d4aa", "attachment_fingerprint(PDF_B64)")
        eq(o["helper_x"], "sha256:5e21d86b709b", "attachment_fingerprint('eA==')")
        eq(o["helper_empty"], digest_of(""), "attachment_fingerprint('')")
    if o["hex_len"] is not None:
        eq(o["hex_len"], 12, "_ATTACHMENT_FINGERPRINT_HEX_LEN")


def judge_r2_scope(o):
    eq(o["capped"], "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf", "capped filename")
    ok(len(o["capped"]) == 64 and o["capped"].endswith(".pdf"), "capped is 64 chars, .pdf kept")
    eq(o["payload"], LONG_PDF_URL, "payload is the whole url")
    ok(o["url_unchanged"], "attachment url untouched")
    eq(o["render_openai"], {
        "type": "file",
        "file": {
            "filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf",
            "file_url": LONG_PDF_URL,
        },
    }, "openai render carries the capped filename and full url")
    eq(o["boundary"], "2024-q4-consolidated-financial-statements-and-notes-final-v3.pdf", "exactly 64 untouched")
    ok(len(o["boundary"]) == 64, "boundary length")
    eq(o["extensionless_filename"], "ledger-entries-consolidated-2024-q4-final-copy-for-review-board-",
       "extensionless capped to first 64")
    ok(len(o["extensionless_filename"]) == 64, "extensionless length")
    eq(o["short_filename"], "report.pdf", "short name left as-is")


def judge_r2_exclusions(o):
    eq(o["remote_source"], "url", "remote is a url block")
    ok(o["remote_fingerprint"] is not None, "url block has a fingerprint")
    eq(o["inline_source"], "base64", "inline content is base64")
    eq(o["inline_payload"], REMOTE_JPEG, "inline payload is the string unchanged")
    eq(o["remote_fingerprint"], o["inline_fingerprint"], "same payload string, same fingerprint")
    ne(o["bare_fingerprint"], o["remote_fingerprint"], "query is part of what is hashed")
    ne(o["fragment_fingerprint"], o["bare_fingerprint"], "fragment is part of what is hashed")
    ok(o["local_fingerprint"] is not None, "base64 block has a fingerprint")
    ok(hashlib.sha256(PDF_BYTES).hexdigest()[:12] not in o["local_fingerprint"],
       "base64 block covers its base64 text, not the decoded bytes")


def judge_r2_failure_behavior(o):
    eq(o["written_detail"], "ultra", "construction keeps 'ultra'")
    eq(o["high_detail"], "HIGH", "construction keeps 'HIGH'")
    eq(o["block_high"], "high", "'HIGH' normalized to 'high'")
    eq(o["block_low"], "low", "' Low ' normalized to 'low'")
    eq(o["block_auto"], "auto", "'auto' stays 'auto'")
    eq(o["downgraded_detail"], "auto", "'ultra' downgraded to 'auto'")
    eq(o["downgrade_warn_count"], 1, "downgrade warns exactly once")
    eq(o["quiet_high"], "high", "supported detail is quiet")
    eq(o["quiet_default"], "auto", "absent detail is quiet")
    eq(o["quiet_warn_count"], 0, "no warning for supported/absent detail")
    eq(o["render_high"], {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{B64_X}", "detail": "high"},
    }, "normalized detail reaches the provider")
    eq(o["render_downgraded_detail"], "auto", "downgraded detail reaches the provider")
    if o["normalize_detail_present"]:
        eq(o["nd_none"], "auto", "normalize_detail(None)")
        eq(o["nd_high"], "high", "normalize_detail('HIGH')")
        eq(o["nd_low"], "low", "normalize_detail(' Low ')")
        eq(o["nd_ultra"], "auto", "normalize_detail('ultra')")
        eq(o["nd_ultra_warn_count"], 1, "normalize_detail('ultra') warns once")
    if o["vocabulary"] is not None:
        eq(o["vocabulary"], ["auto", "low", "high"], "_SUPPORTED_IMAGE_DETAILS")


JUDGES = {
    "test_open::test_open_feature__one_canonical_block_every_provider_renders_from": judge_open,
    "test_r1::test_rule__per_kind_ceiling_measured_on_the_block_and_checked_before_the_hook": judge_r1_rule,
    "test_r1::test_scope__the_prompt_aggregate_is_summed_after_every_block_was_built": judge_r1_scope,
    "test_r1::test_exclusions__a_url_block_is_never_measured_and_never_counted": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_thirteenth_attachment_is_refused_before_anything_is_read": judge_r1_failure_behavior,
    "test_r1::test_observability__a_document_block_costs_fourteen_hundred_tokens": judge_r1_observability,
    "test_r2::test_rule__every_block_carries_a_short_sha256_fingerprint_of_its_payload": judge_r2_rule,
    "test_r2::test_scope__the_filename_is_capped_at_sixty_four_with_its_extension_kept": judge_r2_scope,
    "test_r2::test_exclusions__a_url_block_is_fingerprinted_over_its_url_text": judge_r2_exclusions,
    "test_r2::test_failure_behavior__an_unsupported_detail_is_downgraded_to_auto_with_one_warning": judge_r2_failure_behavior,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g8_attachment_payload" '
             f'tests="{len(results)}" failures="{fails}" errors="0">']
    for classname, name, failure in results:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)}>'
        if failure:
            lines.append(head + f'<failure message={quoteattr(failure[:200])}>'
                         + escape(failure[:4000]) + '</failure></testcase>')
        else:
            lines.append(head + '</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def main(obs_path: str, out_path: str) -> int:
    try:
        observations = json.loads(pathlib.Path(obs_path).read_text())
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if probe is None:
            results.append((classname, name, "no observation from probe"))
            continue
        if not probe.get("ok"):
            results.append((classname, name, f"probe error: {probe.get('error', 'unknown')}"))
            continue
        try:
            judge(probe["obs"])
            results.append((classname, name, ""))
        except Fail as exc:
            results.append((classname, name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - a malformed observation is a failed fact, not a crash
            results.append((classname, name, f"judge error: {type(exc).__name__}: {exc}"))

    pathlib.Path(out_path).write_text(junit(results))
    for classname, name, failure in results:
        print(f"{'FAIL' if failure else 'pass'} {classname}::{name}"
              + (f"  {failure[:160]}" if failure else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
