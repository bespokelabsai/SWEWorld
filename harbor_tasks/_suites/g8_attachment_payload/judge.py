"""g8 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator), plus —
for the ticket's "reuse these as they are" constraint — the submitted source
under SUBMISSION_SRC and the pristine tree under CURATOR_BASELINE_DIR, which it
parses with `ast` and never imports. It applies the assertions the g8 suite has
always made, writing a `junit.xml` whose
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

import ast
import base64
import hashlib
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

# `-I` also drops the script's own directory, and `fixture_spec` sits beside
# this file: the run's INPUTS, the same derivation the worker ran.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402

# Answer-free INPUTS, re-derived here so the expected render dicts can embed the
# exact base64 the renderers produce. Inputs, not answers — but this file holds
# both, and the worker cannot read either.
# `main` re-derives these from the seed root drew, through the same
# `fixture_spec.derive` the worker used, before any fact is judged. They are the
# bytes this run attached, so an observations file recorded from a DIFFERENT run
# carries a different base64 and a different fingerprint and fails here. That is
# what closed the measured forgery: a pristine tree (no `types/attachment.py` at
# all) plus a twelve-line `atexit` hook replaying a recorded observations file
# scored reward 1.0 while the fixture never moved.
PDF_BYTES = b""
PDF_B64 = ""
PNG_B64 = ""
B64_X = base64.b64encode(b"x").decode()             # "eA==" - a fixed tiny input
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


# ---------------------------------------------------------------------------
# "Reuse these as they are" — the source half of the ticket
#
# The ticket's constraints section names seven pieces of curator that this
# change must leave alone (`instruction.md`: "Reuse `BaseType.serialize()`,
# `BaseType._is_local_uri` / `_load_file_as_b64` / `is_local`,
# `_MultiModalPrompt.load` / `.model_validate`, and `_unpack_multimodal` as they
# are"). They live INSIDE the two files the ticket also edits, so no whole-file
# `protected_files` entry can express it: a submission that rewrote `serialize()`
# to suit its own block builder passed every behavioural check, because every
# check goes through the new layer.
#
# So the judge compares them, function by function, against the pristine tree
# root stages at CURATOR_BASELINE_DIR. AST, not text: a reflowed line or a
# reworded docstring is not a behaviour change, while a new branch or a changed
# call is. Nothing is imported — `ast.parse` only reads.
# ---------------------------------------------------------------------------
_REUSED_AS_IS = (
    ("types/prompt.py", "Image", "serialize"),
    ("types/prompt.py", "File", "serialize"),
    ("types/prompt.py", "BaseType", "_is_local_uri"),
    ("types/prompt.py", "BaseType", "_load_file_as_b64"),
    ("types/prompt.py", "BaseType", "is_local"),
    ("types/prompt.py", "_MultiModalPrompt", "load"),
    ("request_processor/online/base_online_request_processor.py",
     "BaseOnlineRequestProcessor", "_unpack_multimodal"),
)
# `.model_validate` is pydantic's own; "reuse it as it is" means the prompt model
# does not grow an override of it.
_NOT_OVERRIDDEN = (("types/prompt.py", "_MultiModalPrompt", "model_validate"),)


def _submission_text(rel: str) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for candidate in (root / "bespokelabs/curator" / rel, root / "src/bespokelabs/curator" / rel):
        if candidate.is_file():
            return judge_io.read_text(candidate)
    raise Fail(f"cannot read submitted {rel} under {root}")


def _baseline_text(rel: str) -> str:
    """The file as the world shipped it.

    A missing baseline FAILS rather than skips: "unchanged" is exactly the claim
    that cannot be checked without something to compare against, and a check
    that passes when its evidence is absent is worse than no check.
    """
    root = os.environ.get("CURATOR_BASELINE_DIR")
    if not root:
        raise Fail("CURATOR_BASELINE_DIR is unset: cannot prove the reused helpers are unchanged")
    path = pathlib.Path(root) / rel
    if not path.is_file():
        raise Fail(f"no pristine {rel} at {path}: cannot prove the reused helpers are unchanged")
    return judge_io.read_text(path)


def _tree(src: str, what: str) -> ast.Module:
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise Fail(f"{what} does not parse: {exc}")


# --- resolving what the module BINDS, rather than searching for a match ------
#
# "Is this still the code the world shipped?" means nothing unless it reads the
# method Python binds. The first version walked the tree and took the first
# class/def of the name, which is the opposite of what Python does, and that was
# a full bypass of the whole reward. Measured on this suite: the identical
# rewrite of `File.serialize` that fails honestly (reward 0) passed 10/10 with a
# decoy `class File` carrying the pristine method inserted ABOVE the real one,
# and passed again with every class body left byte-identical and
# `File.serialize = _mine`, `Image.serialize = _mine` and
# `_MultiModalPrompt.model_validate = classmethod(...)` appended at module level
# — the last of which also walked past the "does not override model_validate"
# assertion.
#
# So: module level only; a name defined twice is REFUSED rather than resolved
# (nothing in this ticket has a reason to define one of these twice); and every
# later rebinding of the name is refused wherever it sits. Refusal, not
# reachability analysis, is why there is no dead-code list here: a second `def`
# or an assignment of the name under `if False:`, `while False:`, `for _ in []:`
# or after a `return` is rejected exactly like a live one, so a submission
# cannot argue its decoy about which branch runs.
def _module_class(tree: ast.Module, cls: str, what: str) -> ast.ClassDef:
    nodes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls]
    if len(nodes) > 1:
        raise Fail(f"{what}: class {cls} is defined {len(nodes)} times at module level; Python "
                   "binds the last one, so a decoy class cannot stand in for it")
    if not nodes:
        raise Fail(f"{what}: no module-level class {cls}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == cls
                                                for t in node.targets):
            raise Fail(f"{what}: the name {cls} is reassigned at line {node.lineno}, so the class "
                       "read here is not the one the module exports")
    return nodes[0]


def _rebindings(tree: ast.Module, cls: str, name: str, what: str) -> None:
    """Refuse every module-level way of replacing `cls.name` after its `def`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Attribute) and t.attr == name and isinstance(t.value, ast.Name)
                and t.value.id == cls for t in node.targets):
            raise Fail(f"{what}: {cls}.{name} is reassigned at line {node.lineno}, so the method "
                       "read here is not the one the class ends up with")
        if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr"
                and len(node.args) >= 2 and isinstance(node.args[0], ast.Name)
                and node.args[0].id == cls and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == name):
            raise Fail(f"{what}: setattr({cls}, {name!r}, ...) at line {node.lineno} replaces the "
                       "method after its definition")


def _class_body_bindings(klass: ast.ClassDef, name: str, what: str) -> None:
    """Refuse a second binding of `name` anywhere in the class body, at any depth."""
    for stmt in klass.body:
        # The direct `def`s and the class's other members are the class as it
        # reads; what is looked for here is a SECOND binding of this one name,
        # which is every other kind of statement a class body can hold.
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for node in ast.walk(stmt):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                raise Fail(f"{what}: {klass.name}.{name} is also defined at line {node.lineno}, "
                           "under a conditional or a loop in the class body")
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target] if isinstance(node, ast.AnnAssign) else [])
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                raise Fail(f"{what}: {klass.name}.{name} is rebound by an assignment in the class "
                           f"body at line {node.lineno}")


def _bound_method(tree: ast.Module, classname: str, funcname: str, what: str):
    """`classname.funcname` as the module binds it, or a Fail naming the dodge."""
    klass = _module_class(tree, classname, what)
    direct = [stmt for stmt in klass.body
              if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == funcname]
    if len(direct) > 1:
        raise Fail(f"{what}: {classname}.{funcname} is defined {len(direct)} times in one class "
                   "body; Python binds the last one, so a duplicate definition is not the "
                   "implementation the world shipped")
    _class_body_bindings(klass, funcname, what)
    _rebindings(tree, classname, funcname, what)
    return direct[0] if direct else None


def _normalized(node) -> str:
    """One function's shape, with its docstring and its formatting removed.

    `ast.dump` without attributes already drops line numbers and column offsets,
    so whitespace and comments cannot decide this; dropping a leading docstring
    expression means a reworded docstring cannot either. What is left is the
    decorators, the signature and the statements — the behaviour the ticket says
    to leave alone.
    """
    body = list(node.body)
    if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:] or [ast.Pass()]
    # Dumped piece by piece rather than by rebuilding a FunctionDef: the node's
    # own field list grew a `type_params` entry in 3.12, and a constructor call
    # that misses a field dumps a node this check would then compare unequal to
    # an identical one.
    return " | ".join([
        node.name,
        ast.dump(node.args),
        ast.dump(node.returns) if node.returns is not None else "",
        ";".join(ast.dump(decorator) for decorator in node.decorator_list),
        ast.dump(ast.Module(body=body, type_ignores=[])),
    ])


def _check_reused_as_is():
    for rel, classname, funcname in _REUSED_AS_IS:
        mine_tree = _tree(_submission_text(rel), f"the submitted {rel}")
        base_tree = _tree(_baseline_text(rel), f"the pristine {rel}")
        theirs = _bound_method(base_tree, classname, funcname,
                               f"fixture drift: the pristine {rel}")
        ok(theirs is not None, f"pristine {classname}.{funcname} not found in {rel}; baseline unusable")
        mine = _bound_method(mine_tree, classname, funcname, rel)
        ok(mine is not None,
           f"{classname}.{funcname} is gone from {rel}; the ticket says to reuse it as it is")
        if _normalized(mine) != _normalized(theirs):
            raise Fail(f"{classname}.{funcname} in {rel} was rewritten (line {mine.lineno}); "
                       "the ticket says to reuse it as it is")
    for rel, classname, funcname in _NOT_OVERRIDDEN:
        base_tree = _tree(_baseline_text(rel), f"the pristine {rel}")
        ok(_bound_method(base_tree, classname, funcname,
                         f"fixture drift: the pristine {rel}") is None,
           f"pristine {classname} already defines {funcname}; this check has the wrong baseline")
        # Same three refusals, read the other way round: the name must not be
        # bound in the class AT ALL, and `_bound_method` raises on the two
        # roundabout bindings (a def under a conditional, `cls.name = ...` or
        # `setattr(cls, "name", ...)`) before it can return None.
        mine_tree = _tree(_submission_text(rel), f"the submitted {rel}")
        ok(_bound_method(mine_tree, classname, funcname, rel) is None,
           f"{classname} now overrides {funcname}; the ticket says to reuse pydantic's as it is")


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
    ok("AttachmentError" in o["empty_attachment_mro"], "EmptyAttachment subclasses AttachmentError")

    # the module the ticket names holds every name it declares there
    for name, present in sorted(o["attachment_module_exports"].items()):
        ok(present, f"bespokelabs.curator.types.attachment does not export {name}")
    module_file = (o["attachment_module_file"] or "").replace("\\", "/")
    ok(module_file.endswith("bespokelabs/curator/types/attachment.py"),
       f"the attachment module is {module_file!r}, not types/attachment.py")

    eq(o["normalize_pdf"], "application/pdf", "normalize_mime_type pdf")
    ok(o["normalize_none"] is None, "normalize_mime_type(None)")
    ok(o["normalize_empty"] is None, "normalize_mime_type('')")

    eq(o["mime_remote_jpeg"], "image/jpeg", "remote jpeg mime (query stripped)")
    ok(o["mime_asset"] is None, "no image/png fallback")
    ok(o["mime_download"] is None, "unguessable file mime stays None")
    eq(o["mime_asset_warn_count"], 1, "one warning for an unguessable image url")
    eq(o["mime_download_warn_count"], 1, "one warning for an unguessable file url")
    eq(o["mime_quiet_guess"], "application/pdf", "a guessable url resolves")
    eq(o["mime_quiet_warn_count"], 0, "a successful guess is quiet")
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

    # frozen, the declaration and the behaviour: the ticket writes
    # `model_config = ConfigDict(frozen=True)` on a pydantic model, so a plain
    # class whose one __setattr__ happens to raise is not what it asked for
    raised(o["frozen"], msg="block is frozen")
    raised(o["frozen_payload"], msg="block payload is frozen")
    ok(o["block_is_basemodel"] is True, "AttachmentBlock is not a pydantic BaseModel")
    ok(o["block_config_frozen"] is True,
       f"AttachmentBlock.model_config frozen is {o['block_config_frozen']!r}, not True")
    for field in ("kind", "source", "mime_type", "payload", "filename", "detail"):
        ok(field in o["block_field_names"], f"AttachmentBlock has no {field} field: {o['block_field_names']}")
    eq({k: v for k, v in sorted(o["block_required"].items())},
       {"detail": False, "filename": True, "kind": True, "mime_type": True,
        "payload": True, "source": True},
       "which declared block fields are required")
    ok(o["block_detail_default"] is None, f"detail default is {o['block_detail_default']!r}, not None")
    ok(o["block_revalidates"] is True, "a block does not re-validate from its own dump")
    raised(o["block_bad_kind"], mro="ValidationError", msg="kind outside the ticket's Literal")
    raised(o["block_bad_source"], mro="ValidationError", msg="source outside the ticket's Literal")

    eq(o["remote_block_triple"], ["image", "url", REMOTE_JPEG], "remote jpeg -> url block")
    eq(o["remote_block_name_detail"], ["cat.jpeg", "auto"], "remote jpeg name/detail")

    # the refusals, with the messages the ticket writes out
    raised(o["miss_typo"], mro="MissingLocalAttachment", msg="missing typo",
           string="Attachment path is neither an http(s) URL nor an existing file: "
                  "'/tmp/definitely-missing/typo.png'")
    eq(o["miss_typo"].get("url"), "/tmp/definitely-missing/typo.png", "missing typo url")
    raised(o["miss_s3"], mro="MissingLocalAttachment", msg="missing s3",
           string="Attachment path is neither an http(s) URL nor an existing file: "
                  "'s3://bucket/report.pdf'")
    eq(o["miss_s3"].get("url"), "s3://bucket/report.pdf", "missing s3 url")
    raised(o["miss_notes"], mro="MissingLocalAttachment", msg="missing beats unguessable",
           string="Attachment path is neither an http(s) URL nor an existing file: "
                  "'/tmp/definitely-missing/notes'")

    raised(o["unknown_download"], mro="UnknownAttachmentMimeType", msg="unknown download",
           string="Cannot determine MIME type for file attachment: 'https://example.com/download'")
    eq(o["unknown_download"].get("url"), "https://example.com/download", "unknown download url")
    eq(o["unknown_download"].get("attachment_type"), "file", "unknown download attachment_type")
    ok("ValueError" in o["unknown_download"].get("mro", []), "unknown download is a ValueError")
    raised(o["unknown_asset"], mro="UnknownAttachmentMimeType", msg="unknown asset",
           string="Cannot determine MIME type for image attachment: 'https://example.com/asset'")
    eq(o["unknown_asset"].get("attachment_type"), "image", "unknown asset attachment_type")
    # the extensionless payload sits in a throwaway directory, so its message is
    # rebuilt from the path the probe recorded rather than from a literal
    raised(o["unknown_extensionless"], mro="UnknownAttachmentMimeType", msg="unknown extensionless",
           string=f"Cannot determine MIME type for file attachment: {o['extensionless_url']!r}")

    # an empty payload, refused after the MIME check, with its stated message
    eq(o["empty_serializes_to"], "", "an empty local file serializes to ''")
    raised(o["empty_payload"], mro="EmptyAttachment", msg="empty payload",
           string=f"Attachment empty.pdf has an empty payload: {o['empty_url']!r}")
    eq(o["empty_payload"].get("url"), o["empty_url"], "empty payload url")
    eq(o["empty_payload"].get("filename"), "empty.pdf", "empty payload filename")
    ok("AttachmentError" in o["empty_payload"].get("mro", []), "EmptyAttachment is an AttachmentError")
    raised(o["empty_unguessable"], mro="UnknownAttachmentMimeType",
           msg="the MIME check speaks before the empty check")

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
        "image_url": {"url": f"data:image/png;base64,{PNG_B64}", "detail": "auto"},
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

    # the constraints section: the helpers this change is told to reuse as they
    # are, compared with the pristine tree. Source, not behaviour — every
    # behavioural check above goes through the NEW layer, so a rewritten
    # `serialize()` is invisible to all of them.
    _check_reused_as_is()


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
    eq(o["fingerprint"], digest_of(PDF_B64), "pdf fingerprint")
    eq(o["fingerprint"], digest_of(PDF_B64), "pdf fingerprint == digest_of(PDF_B64)")
    ok(o["fingerprint"].startswith("sha256:") and len(o["fingerprint"]) == len("sha256:") + 12,
       "fingerprint shape")
    eq(o["other_fingerprint"], "sha256:5e21d86b709b", "other fingerprint")
    eq(o["other_fingerprint"], digest_of("eA=="), "other fingerprint == digest_of('eA==')")
    ne(o["other_fingerprint"], o["fingerprint"], "fingerprint follows payload")
    eq(o["other_payload"], "eA==", "other payload")
    eq(o["same_bytes_fingerprint"], digest_of(PDF_B64), "same bytes fingerprint the same")
    if o["helper_present"]:
        eq(o["helper_pdf"], digest_of(PDF_B64), "attachment_fingerprint(PDF_B64)")
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


def main(obs_path: str, out_path: str, seed: str) -> int:
    global PDF_BYTES, PDF_B64, PNG_B64
    # A missing seed FAILS every fact rather than grading against a guess: the
    # expected base64 and fingerprints below ARE the seed's, and a judge that
    # invented its own inputs would be grading a run that never happened.
    spec = fixture_spec.derive(seed) if seed else None
    if spec is not None:
        PDF_BYTES = spec["pdf_bytes"]
        PDF_B64 = base64.b64encode(PDF_BYTES).decode()
        PNG_B64 = base64.b64encode(spec["png_bytes"]).decode()
    try:
        observations = json.loads(judge_io.read_text(obs_path))
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        if spec is None:
            results.append((classname, name, "no run seed: the inputs this run used are unknown"))
            continue
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
    raise SystemExit(main(sys.argv[1], sys.argv[2],
                          sys.argv[3] if len(sys.argv) > 3 else ""))
