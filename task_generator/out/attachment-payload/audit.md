# Audit — g8 (attachment-payload)

| fact | bracket | audit | why |
|---|---|---|---|
| `g8.r1.rule` | hidden | **retest** | Retest — the fact is real and discriminating, but two graded properties are not in the fact text.

1. Pin the unit in the fact and the clue. Replace "measured o |
| `g8.r1.scope` | hidden | **narrow** | Narrow the fact and adjust one assertion.

1. Delete the clause "and `_canonical_attachment_block` / `_format_multimodal` never apply it" from the fact text. It |
| `g8.r1.exclusions_or_crossover` | hidden | **cut** | Cut `r1.exclusions_or_crossover`. It has no content its siblings do not already carry: `r1.rule` ("each base64 payload is measured once") and `r1.scope` ("the ` |
| `g8.r1.failure_behavior` | hidden | **retest** | Retest, keeping the fact. The clue-derived code (the constant, the exception class, the guard at the head of `_handle_multi_modal_prompt`) is genuinely divergen |
| `g8.r1.observability` | hidden | **retest** | Keep the fact — it is genuinely discriminating and cheaply testable — and fix the test, in three edits:

1. **Split the unknown-block rule out of the deciding t |
| `g8.r2.rule` | hidden | ship | Ship r2.rule, after three cheap verifications I could not run here (no file tools in this session):

1. CLUE PRECISION — the decisive assertion is a literal equ |
| `g8.r2.scope` | hidden | ship | Ship as-is. The divergent action is concrete (the `_MAX_ATTACHMENT_FILENAME_LEN = 64` constant plus the `name[: 64 - len(ext)] + ext` slice), the ticket activel |
| `g8.r2.exclusions_or_crossover` | hidden | **cut** | Cut `r2.exclusions_or_crossover` as a separate graded fact and fold its one piece of real content into `r2.rule`. Concretely: delete `test_exclusions__a_url_blo |
| `g8.r2.failure_behavior` | hidden | **retest** | Retest — keep the fact, fix two things in the grader. (1) Scope the warning count to this fact: have `Recorder.emit` keep only records whose `record.getMessage( |

## g8.r1.rule — retest

**Divergent action.** In `_canonical_attachment_block`, after resolving `kind`/`source`/`payload` and before offering the payload to `file_upload_limit_check`:

```python
_PER_KIND_LIMIT_MB: dict[str, float] = {"image": 20.0, "document": 24.0}

size_mb = None
if source == "base64":
    size_mb = get_base64_size(payload)
    limit_mb = _PER_KIND_LIMIT_MB[kind]
    if size_mb > limit_mb:
        raise AttachmentTooLarge(kind, size_mb, limit_mb)
self.file_upload_limit_check(payload)
return AttachmentBlock(..., size_mb=size_mb)
```

plus `class AttachmentTooLarge(AttachmentError)` in `attachment.py` storing `.kind/.size_mb/.limit_mb`, and a `size_mb: float | None` field added to the frozen model. A ticket-only agent writes none of it: the ticket enumerates `AttachmentBlock`'s fields as a closed list of six and the refusals as a closed numbered list of three, so a blind agent's block has no `size_mb`, no size comparison, and no `AttachmentTooLarge` symbol for `attachment_symbol()` to find.

**The assertion.** `assert triple(exc) == ("image", 24.0, 20.0)` — i.e. `(read_field(exc, "kind"), read_field(exc, "size_mb"), read_field(exc, "limit_mb"))` off the `AttachmentTooLarge` raised for `Image(content=PAYLOAD_24MB)`.

It depends on three things beyond this requirement. (1) The measurement convention of the pre-existing `get_base64_size` — mebibytes of the *decoded* byte count — which the fact text does not state; the `24.0` literal is only correct under that one convention. (2) `Image.serialize()` returning a `str` `content` verbatim rather than re-encoding it; if it re-encodes, every number in the file shifts by 4/3 and the fact fails for an open-path reason. (3) `kind` resolution from `mime_type` (`"image/"` prefix), which is ticket-owned. The companion assertions `refusing.calls == []` / `recording.calls == [PAYLOAD_24MB]` add a fourth dependency: that the base calls `file_upload_limit_check` at all.

**Catalog A.** clean

**Catalog B.**
- `observable_belongs_to_another_fact` — The ordering half of the rule is graded entirely through `file_upload_limit_check` call records — `assert refusing.calls == []` and `assert recording.calls == [PAYLOAD_24MB]`. That hook is never mentioned in the visible ticket, and r1.rule only constrains position *relative* to it, never mandates calling it or fixes its signature. `recording.calls == [PAYLOAD_24MB]` therefore grades 'you invoke the provider hook, once, with the raw base64 string' — a contract owned by `test_open`'s `StubOnline`/`raising_stub`, not by this fact. If the open bracket does not already pin it, a clue-informed, ceiling-correct implementation fails here. (I could not read `test_open.py` to settle which.)

**A correct build the test rejects:**

```
A clue-informed agent who implements the sentence as written — "measured once in megabytes from its base64 length" — and takes megabyte to mean 10^6, or takes "base64 length" to mean the length of the base64 text:

```python
_PER_KIND_LIMIT_MB: dict[str, float] = {"image": 20.0, "document": 24.0}


def _payload_size_mb(payload: str) -> float:
    """Megabytes, measured from the base64 length."""
    return len(payload) / 1_000_000


# ... inside _canonical_attachment_block, before the provider hook:
size_mb = None
if source == "base64":
    size_mb = _payload_size_mb(payload)
    limit_mb = _PER_KIND_LIMIT_MB[kind]
    if size_mb > limit_mb:
        raise AttachmentTooLarge(kind, size_mb, limit_mb)
self.file_upload_limit_check(payload)
```

This has the ceiling, the field, the exception, the strict comparison and the base-before-hook ordering — everything the fact asserts — and is rejected: `triple(exc)` is `("image", 33.554432, 20.0)`, not `("image", 24.0, 20.0)`, and the 24 MB document now crosses its own ceiling instead of reaching the hook, so `pytest.raises(RuntimeError)` fails too. The milder decimal-MB-of-decoded-bytes reading (`get_base64_size`-style byte count `/ 1_000_000`) fails identically at `25.165824 != 24.0`, and even the `size_mb` smoke assertion `measured == 8.58306884765625e-06` rejects it (`9e-06`). The test is resolving a unit ambiguity the requirement text leaves open.
```

**Recommendation.** Retest — the fact is real and discriminating, but two graded properties are not in the fact text.

1. Pin the unit in the fact and the clue. Replace "measured once in megabytes from its base64 length" with: "measured once with `bespokelabs.curator.file_utilities.get_base64_size(payload)` — decoded bytes divided by 1024**2 — and recorded as `size_mb`." Right now the test's `assert measured == get_base64_size(PDF_B64) == 8.58306884765625e-06` and the `24.0`/`18.0`/`6.0` literals are only reachable under one of three literal readings of the sentence, and the fact never says which. This is the change that matters most; without it a correct agent fails on arithmetic.

2. Decide who owns `file_upload_limit_check`. If `test_open` already asserts that `_canonical_attachment_block` calls the hook once with the base64 payload, keep `assert recording.calls == [PAYLOAD_24MB]` and add the hook to the visible ticket's description of `_canonical_attachment_block` so the contract is stated where it is graded. If it does not, drop that assertion and grade the ordering the way the fact states it — the oversize image raises `AttachmentTooLarge` and `refusing.calls == []` — which does not require an implementation to invoke a hook the ticket never asked for.

3. Optional, cheap: `PAYLOAD_24MB`/`PAYLOAD_18MB` cost ~83 MB of resident `str` before any `serialize()` copy. Shrinking the ceilings in the fact (e.g. 2.0/2.4 MB) would preserve every discrimination the docstring claims at a hundredth of the memory. Only do this if the clue's numbers move with it.


## g8.r1.scope — narrow

**Divergent action.** In `_handle_multi_modal_prompt`, after the per-attachment loop and outside `_canonical_attachment_block`:

```python
blocks = [self._canonical_attachment_block(a) for a in attachments]
total_mb = sum(b.size_mb for b in blocks if b.size_mb is not None)
if total_mb > _PROMPT_ATTACHMENT_SIZE_LIMIT_MB:   # 45.0
    raise AttachmentTooLarge("prompt", total_mb, _PROMPT_ATTACHMENT_SIZE_LIMIT_MB)
```

Three things here are unreachable from the ticket: the module constant `45.0`, the literal string `"prompt"` occupying the `kind` slot of an exception whose `kind` is otherwise a block kind, and the placement of the sum in the prompt method rather than incrementally inside the block builder. A ticket-only agent writes `_handle_multi_modal_prompt` exactly as the ticket specifies it — render blocks, then texts, no refusal — and emits none of these.

**The assertion.** `assert triple(exc) == ("prompt", 60.0, 45.0)` — the whole-prompt sum, not the running total at the crossing point (54.0), against the literal 45.0 with the literal kind "prompt". It does depend on more than this fact: the exception class, its three attribute names, and the exactness of `size_mb` as a float are all defined by the sibling `rule`, so `rule` must be implemented for this assertion to be reachable at all. The companion `assert len(stub.calls) == 4` depends on `rule`'s hook-invocation clause outright.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The trailing clause '`_canonical_attachment_block` / `_format_multimodal` never apply it' is satisfied by doing nothing. Applying a 45.0 MB ceiling in the per-block path is deliberate extra work no engineer does, and the sibling `rule` ('strictly greater than 20.0 MB ... 24.0 MB') already makes it impossible for that ceiling to fire on a single block. The clause tests no restraint and the test file never probes it.

**Catalog B.**
- `state_is_unreachable` — For the clause '`_canonical_attachment_block` / `_format_multimodal` never apply it': a single block exceeding 45.0 MB cannot exist, because the sibling per-kind ceilings refuse at 20.0 (image) and 24.0 (document) first. 'Correctly not applying a 45.0 ceiling per block' and 'never being in a position where it could matter' are indistinguishable. The core of the fact — the aggregate at 45.0 with `kind == "prompt"` — is reachable and is what the test exercises.
- `contradicts_a_sibling` — Same clause, read the other way: `rule` guarantees no block survives above 24.0 MB, which is the precondition that would have to be false for the per-block-path prohibition to be observable. The rubric's pattern exactly — 'satisfying the rule makes the failure branch unreachable.' No contradiction exists in the graded part: 3x18.0 + 6.0 keeps every attachment under 20.0, so `scope`'s scenario and `rule`'s ceilings coexist cleanly.
- `observable_belongs_to_another_fact` — `assert len(stub.calls) == 4` measures hook invocation, a channel invented and owned by the sibling `rule` ('before the payload is offered to the provider's `file_upload_limit_check` hook'), and `triple(exc)` reads `.kind/.size_mb/.limit_mb` off an exception `rule` defines, at a float precision `rule` pins. A scope-correct agent whose block builder does not call the hook per base64 payload fails scope's test for a rule defect. Severity is limited by these being fields of the same requirement r1 and by scope owning its own discriminator (`size_mb == 60.0` separates aggregate from incremental on its own), but the per-field grade is not independent.

**A correct build the test rejects:**

```
A clue-faithful agent who is told there is a 45.0 MB whole-prompt ceiling but not told when it is evaluated, and who sizes the prompt up front to avoid rendering work it is about to throw away:

```python
def _handle_multi_modal_prompt(self, message):
    attachments = message.attachments()
    if len(attachments) > _ATTACHMENT_COUNT_LIMIT:
        raise TooManyAttachments(len(attachments), _ATTACHMENT_COUNT_LIMIT)
    payloads = [None if a.is_remote else a.serialize() for a in attachments]
    total_mb = sum(get_base64_size(p) for p in payloads if p is not None)
    if total_mb > _PROMPT_ATTACHMENT_SIZE_LIMIT_MB:      # 45.0
        raise AttachmentTooLarge("prompt", total_mb, _PROMPT_ATTACHMENT_SIZE_LIMIT_MB)
    blocks = [self._canonical_attachment_block(a) for a in attachments]
    return [self._render_attachment_block(b) for b in blocks] + [
        {"type": "text", "text": t} for t in message.texts
    ]
```

This is a whole-prompt aggregate, at 45.0, in `_handle_multi_modal_prompt`, not incremental, reporting the whole-prompt sum — it produces the identical `("prompt", 60.0, 45.0)` triple and passes `triple(exc)`. It is rejected solely by `assert len(stub.calls) == 4`, because it refuses before any hook fires. Whether that rejection is fair turns entirely on whether the clue states the ordering; I could not read the clue set to check.
```

**Recommendation.** Narrow the fact and adjust one assertion.

1. Delete the clause "and `_canonical_attachment_block` / `_format_multimodal` never apply it" from the fact text. It is unreachable — the sibling's 20.0/24.0 per-kind ceilings mean no single block ever reaches 45.0 — and it is satisfied by inaction. Nothing in the test grades it, and nothing could. Keep the positive placement claim ("it belongs to `_handle_multi_modal_prompt`"), which the test does grade via the 4-block scenario.

2. Keep "It is not evaluated incrementally" only if the clue explicitly says the sum is taken after every block is built and every hook has fired. If it does not, drop `assert len(stub.calls) == 4` — as written it is the sole rejector of the pre-pass implementation quoted in `correct_fail`, which is otherwise a faithful reading, and it grades through the sibling `rule`'s hook channel rather than through anything scope owns. The `size_mb == 60.0` assertion already separates aggregate from incremental on its own (an incremental implementation reports 54.0).

3. Optional, to give scope an observable that does not route through `rule`: add two 24.0 MB documents in one prompt — each individually legal under the 24.0 document ceiling — and assert the aggregate raises with `size_mb == 48.0` while `block_of(stub, <one of them>)` does not raise. That pins the aggregate/per-block split using only scope's own constant.


## g8.r1.exclusions_or_crossover — cut

**Divergent action.** The only candidate is the url branch of `_canonical_attachment_block` plus a nullable field: `size_mb: float | None = None` on `AttachmentBlock`, and `if data.is_remote and data.url: source, payload, size_mb = "url", data.url, None` with `size_mb = get_base64_size(payload)` and the per-kind comparison living only in the `else` (base64) branch. But that code is written entirely off `r1.rule` ("each base64 payload is measured once ... recorded on the block as a size_mb field"). An agent shown `r1.rule` and `r1.scope` and NOT shown this fact writes byte-identical code, because both siblings already restrict themselves to base64 blocks. So relative to its own siblings there is no divergent action; the blind-vs-informed gap the bracket measured is entirely `r1.rule`'s gap, borrowed.

**The assertion.** `assert read_field(remote, "size_mb") is None` (in `test_exclusions__a_url_block_is_never_measured_and_never_counted`). It depends on more than this requirement: the field `size_mb` only exists because of `r1.rule`, the symbol lookup `too_large()` on the line above is `r1.rule`'s `AttachmentTooLarge`, and `stub.calls == []` / `mixed.calls == [PDF_B64]` depend on `r1.rule`'s unspecified `file_upload_limit_check(payload)` calling convention (payload string vs. block vs. decoded bytes — the requirement only says "the payload is offered to the hook"). Nothing in this test can fail while `r1.rule` is implemented as its own text describes.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The whole fact is a prohibition — "is never measured ... not compared ... contributes nothing". Satisfying it requires writing no code at all in the url branch; violating it requires deliberately calling `get_base64_size(a_url_string)`, i.e. weighing a ~50-character URL as if it were base64. No engineer does that on purpose, so the rule never tests restraint.
- `model_already_knows_it` — It is forced by physics plus the ticket's own constraint list: "Nothing here imports `aiohttp`, opens a socket, sleeps, or spawns anything." You cannot know a remote URL's byte size without fetching it, and fetching is banned. Excluding url blocks from a size ceiling is not a fact to be learned, it is the only implementable option.
- `ticket_gives_it_away` — The open ticket already teaches this exact exclusion for the sibling payload check: refusal 3 reads "A `source == "base64"` attachment whose `serialize()` returns `""` raises `EmptyAttachment` ... A remote URL is never read, so it is never checked for emptiness." Same branch, same reasoning, spelled out openly. Once an agent learns from a clue that a size ceiling exists, the ticket has already told them which attachments are subject to payload inspection.
- `entailed_by_the_open_feature` — The open ticket fixes the branch structure: "A remote `url` (per `is_remote`) gives `source == "url"` with the URL as `payload`; anything else gives `source == "base64"` with `BaseType.serialize()` output as `payload`." There is exactly one place a base64 payload comes into existence, and it is the `else` arm. Any measurement of a base64 payload lands there by construction; the url arm has no payload to weigh.
- `obvious_implementation_does_it` — Given `r1.rule`'s literal wording — "each base64 payload is measured once in megabytes from its base64 length" — the obvious implementation puts `get_base64_size(payload)` and the ceiling comparison inside the base64 branch and leaves the url branch alone. The test cannot distinguish "read the exclusions clue" from "read the rule clue and wrote the normal branch".

**Catalog B.**
- `contradicts_a_sibling` — `r1.rule` specifies the field as "recorded on the block as a `size_mb: float` field", on an `AttachmentBlock` whose `model_config = ConfigDict(frozen=True)` pydantic model. This fact requires `size_mb is None` for url blocks. An agent that types the field exactly as the rule clue spells it (`size_mb: float`) gets a pydantic `ValidationError` when it tries to pass `None`, and an agent that keeps `float` and uses `0.0` is failed by the assertion. The two facts cannot both be implemented literally.
- `behaviour_has_no_consequence` — Two of the fact's three clauses are unobservable at any realistic input. A violating implementation that measured the url string would get `get_base64_size("https://...")` ≈ 0.00004 MB — it would still clear the 20.0/24.0 ceilings and still not move the 45.0 sum. The test's own comment concedes the aggregate half is untestable on its merits: "Deliberately a few bytes, not a few megabytes". Only the sentinel value differs, and the sentinel is spelling, not behaviour.
- `observable_belongs_to_another_fact` — Every channel this test uses is `r1.rule`'s: the `size_mb` field, the `AttachmentTooLarge` symbol (`too_large()  # the ceiling this fact excludes url blocks from must exist`), and the `StubOnline.calls` hook recorder (`mixed.calls == [PDF_B64]`, which grades `r1.rule`'s unspecified hook calling convention, not this fact). Grading through them double-counts `r1.rule`.
- `no_independent_content` — `r1.rule` says "each base64 payload is measured"; `r1.scope` says "the `size_mb` values of the `source == "base64"` blocks are summed". Both siblings already state the restriction affirmatively. This fact is their contrapositive with a sentinel bolted on. There is no way to fail it without failing or contradicting `r1.rule`.

**A correct build the test rejects:**

```
class AttachmentBlock(BaseModel):
    model_config = ConfigDict(frozen=True)
    ...
    size_mb: float = 0.0   # r1.rule spells this `size_mb: float`; a url carries no payload to weigh

def _canonical_attachment_block(self, data: BaseType) -> AttachmentBlock:
    ...
    if data.url and data.is_remote:
        source, payload, size_mb = "url", data.url, 0.0
    else:
        source, payload = "base64", data.serialize()
        if not payload:
            raise EmptyAttachment(url=data.url, filename=filename)
        size_mb = get_base64_size(payload)
        limit = 20.0 if kind == "image" else 24.0
        if size_mb > limit:
            raise AttachmentTooLarge(kind, size_mb, limit)
        self.file_upload_limit_check(payload)
    return AttachmentBlock(kind=kind, source=source, mime_type=mime, payload=payload,
                           filename=filename, detail=detail, size_mb=size_mb)

# This satisfies every behavioural clause of the audited fact: the URL is never
# measured, never compared against 20.0/24.0, never offered to the hook, and
# contributes 0.0 — nothing — to the 45.0 MB prompt sum. It is also strictly more
# faithful to r1.rule's declared `size_mb: float` than the golden is. It is failed
# by `assert read_field(remote, "size_mb") is None`.
```

**Recommendation.** Cut `r1.exclusions_or_crossover`. It has no content its siblings do not already carry: `r1.rule` ("each base64 payload is measured once") and `r1.scope` ("the `size_mb` values of the `source == "base64"` blocks are summed") both state the restriction affirmatively, the open ticket already teaches the identical url exclusion for `EmptyAttachment` ("A remote URL is never read, so it is never checked for emptiness"), and the ticket's no-socket constraint makes measuring a remote payload impossible anyway. Delete `test_exclusions__a_url_block_is_never_measured_and_never_counted` and, if anything, move its remote-only-prompt case into `r1.scope`'s test as a control.

Two fixes to make regardless of that decision, because they currently mis-grade a correct agent on the sibling facts:
1. Reconcile the type. `r1.rule` must say `size_mb: float | None = None` (not `size_mb: float`), or the golden's `None` for url blocks is unreachable on a frozen pydantic model that follows the rule's own annotation. As written the two facts contradict each other.
2. Pin the hook contract in `r1.rule`. `mixed.calls == [PDF_B64]` requires `file_upload_limit_check` to be called with the base64 string; the requirement only says "the payload is offered to the hook", so passing the block, the decoded bytes, or `(payload, mime_type)` is an equally legitimate reading that the test rejects.

If you need a fifth field on r1 and want to keep an exclusion, replace it with one that has an independent observable and cannot be derived from the rule's own scoping — e.g. what happens to `size_mb` and the aggregate for a base64 block that was refused by the provider hook, or an interaction between the count ceiling and the aggregate. Do not grade a sentinel value that the rule's declared type forbids.


## g8.r1.failure_behavior — retest

**Divergent action.** In `attachment.py`: `_ATTACHMENT_COUNT_LIMIT: int = 12` plus `class TooManyAttachments(AttachmentError): def __init__(self, count: int, limit: int): self.count = count; self.limit = limit; super().__init__(f"Prompt has {count} attachments, over the limit of {limit}.")`; and as the first two statements of `_handle_multi_modal_prompt`, before any call to `self._canonical_attachment_block`: `attachments = message.attachments()` / `if len(attachments) > _ATTACHMENT_COUNT_LIMIT: raise TooManyAttachments(len(attachments), _ATTACHMENT_COUNT_LIMIT)`. A ticket-only agent writes `_handle_multi_modal_prompt` with no cardinality guard at all — the ticket's spec is "Result length is len(images) + len(files) + len(texts)", unconditionally.

**The assertion.** `with pytest.raises(TooManyAttachments) as caught: stub._handle_multi_modal_prompt(...[tiny] * 13...)` followed by `assert (read_field(exc, \"count\"), read_field(exc, \"limit\")) == (13, 12)` and `assert str(exc) == \"Prompt has 13 attachments, over the limit of 12.\"`. That assertion depends on nothing but this requirement. The test as a whole does not: `assert len(twelve.calls) == 12` and `assert len(texts.calls) == 1` depend on r1.rule/r1.scope's placement of `self.file_upload_limit_check`, and `assert stub.calls == []` depends on it too (passing vacuously when it was never wired).

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Only for one sub-assertion, not the fact. '`file_upload_limit_check` is not called for an over-count prompt' is graded by `assert stub.calls == []`, which is satisfied by any implementation that never calls the hook at all — including every blind one. It witnesses nothing about ordering. The fact still requires an active raise, so the fact as a whole is not inaction-passable.

**Catalog B.**
- `observable_belongs_to_another_fact` — `assert len(twelve.calls) == 12` and `assert len(texts.calls) == 1` grade the `file_upload_limit_check` recorder, which is `r1.rule`'s and `r1.scope`'s channel ('BEFORE the payload is offered to `file_upload_limit_check`'; 'four hook calls'; 'it is never offered to the hook'). This fact says nothing about hook counts on an accepted prompt. A correct count cap with the hook sited only on document payloads fails this fact's test at `len(calls) == 0`.
- `fake_defines_the_trigger` — Partial. The trigger (13 attachments) is authored by the test directly, which is fine. But the 'counted first' half of the fact is observed only through `StubOnline.calls`, a stub-owned hook whose call sites are defined by a *different* fact's spec — the fake decides what 'nothing was read' looks like, and it reads empty for an implementation that simply never wired the hook.

**A correct build the test rejects:**

```
```python
# attachment.py — this fact implemented exactly as stated
_ATTACHMENT_COUNT_LIMIT: int = 12

class TooManyAttachments(AttachmentError):
    def __init__(self, count: int, limit: int):
        self.count, self.limit = count, limit
        super().__init__(f"Prompt has {count} attachments, over the limit of {limit}.")

# base_online_request_processor.py
def _canonical_attachment_block(self, data):
    ...
    if source == "base64":
        size_mb = get_base64_size(payload)
        limit_mb = 20.0 if kind == "image" else 24.0
        if size_mb > limit_mb:
            raise AttachmentTooLarge(kind, size_mb, limit_mb)
        # the hook is named file_upload_limit_check: it prices *uploaded files*,
        # so only document payloads are offered to it. r1.rule only constrains the
        # ORDER ("the provider hook only ever sees payloads the shared ceiling
        # already accepted"), never that images are offered at all.
        if kind == "document":
            self.file_upload_limit_check(payload)
    return AttachmentBlock(..., size_mb=size_mb)

def _handle_multi_modal_prompt(self, message):
    attachments = message.attachments()
    if len(attachments) > _ATTACHMENT_COUNT_LIMIT:
        raise TooManyAttachments(len(attachments), _ATTACHMENT_COUNT_LIMIT)
    blocks = [self._canonical_attachment_block(a) for a in attachments]
    total = sum(b.size_mb for b in blocks if b.source == "base64")
    if total > 45.0:
        raise AttachmentTooLarge("prompt", total, 45.0)
    return [self._render_attachment_block(b) for b in blocks] + [
        {"type": "text", "text": t} for t in message.texts
    ]
```
This raises `TooManyAttachments(13, 12)` with the exact message, counts before a single block is built, does not count texts, and accepts 12 — every clause of r1.failure_behavior — yet the test rejects it at `assert len(twelve.calls) == 12` (twelve images produce zero hook calls) and again at `assert len(texts.calls) == 1`.
```

**Recommendation.** Retest, keeping the fact. The clue-derived code (the constant, the exception class, the guard at the head of `_handle_multi_modal_prompt`) is genuinely divergent and no ticket-only implementation reaches it. Change the test: (1) delete `assert len(twelve.calls) == 12` and `assert len(texts.calls) == 1` — they grade r1.rule/r1.scope's `file_upload_limit_check` placement, not this fact; (2) replace `assert stub.calls == []`, which passes by inaction, with a channel this fact owns: give the test a `StubOnline` subclass whose `_canonical_attachment_block` appends to a `built` list before delegating to `super()`, then assert `built == []` for the 13-attachment prompt and `len(built) == 12` / `len(built) == 1` for the two controls. That measures "counted before a single block is built" directly and leaves the pass/fail of this fact dependent only on this fact's implementation. Keep unchanged: the `pytest.raises` block, the `(count, limit) == (13, 12)` and message assertions, the `AttachmentError`/`ValueError` subclass checks, the optional `_ATTACHMENT_COUNT_LIMIT == 12` probe, and `len(content) == 13` / `41`.


## g8.r1.observability — retest

**Divergent action.** In `openai_request_mixin.calculate_input_tokens`, the informed agent writes a module-level `_OPENAI_TOKENS_PER_DOCUMENT: int = 1400` and a dispatch arm `elif block.get("type") in ("file", "document"): total += _OPENAI_TOKENS_PER_DOCUMENT`. The blind agent writes the same arm with a different right-hand side — overwhelmingly `_OPENAI_TOKENS_PER_IMAGE["low"]` (85), because the ticket's own sentence order is "`"image_url"` and `"image"` both cost `_OPENAI_TOKENS_PER_IMAGE["low"]` (unchanged). `"file"` and `"document"` blocks must also be priced by this function." — or `0`, or `len(encoding.encode(block["file"]["file_data"]))`. The divergence is a single integer literal, but it is a real one: nothing in the ticket, the codebase, or public provider docs points at 1400.

**The assertion.** `assert calculate_input_tokens([openai_file], encoder) == 1400` (with its twin `assert calculate_input_tokens([anthropic_document], encoder) == 1400`, and `assert calculate_input_tokens([openai_image], encoder) == 85` as the contrast that rules out the image rate). These three are clean: they isolate one block each and depend on nothing but this requirement's implementation. The later `assert total == 5 + 85 + 85 + 1400 + 1400 + 0 == 2975` is NOT clean — it additionally requires that an unrecognized `"thinking"` block cost 0, a rule the open ticket never states, and it requires the `FakeEncoder` text path. There is also a harness-level coupling shared by every test in the suite: `importable()` runs first, so a tree whose `attachment.py` fails to import fails this fact for reasons belonging entirely to the open ticket.

**Catalog A.** clean

**Catalog B.**
- `fake_defines_the_trigger` — Borderline but worth recording. `FakeEncoder` (1 token per character) is a reaction-side scale and does not touch the flat 1400 — that part is clean. But the fake DOES author the `5` in `5 + 85 + 85 + 1400 + 1400 + 0`, and more importantly the test's own dict literal `{"type": "thinking", "thinking": "ignored"}` is where the `+ 0` term comes from: the test picks an unrecognized type and then asserts the answer to how unrecognized types are priced, a question neither the ticket nor this fact's headline settles. The trigger for the 0-term is authored by the test.

**A correct build the test rejects:**

```
```python
# openai_request_mixin.py — prices documents at exactly 1400, per the clue,
# but is conservative about block types it does not recognize rather than
# silently pricing them at zero (the ticket says nothing about unknown types).
_OPENAI_TOKENS_PER_DOCUMENT = 1400

def calculate_input_tokens(messages, token_encoding):
    if isinstance(messages, str):
        return len(token_encoding.encode(messages, disallowed_special=()))
    total = 0
    for block in messages:
        kind = block.get("type")
        if kind == "text":
            total += len(token_encoding.encode(str(block.get("text", "")), disallowed_special=()))
        elif kind in ("image_url", "image"):
            total += _OPENAI_TOKENS_PER_IMAGE["low"]
        elif kind in ("file", "document"):
            total += _OPENAI_TOKENS_PER_DOCUMENT
        else:
            # don't undercount a block shape we don't know yet
            total += len(token_encoding.encode(str(block), disallowed_special=()))
    return total
```
This passes `calculate_input_tokens([openai_file], encoder) == 1400`, `[anthropic_document] == 1400`, `[openai_image] == 85` and `[anthropic_image] == 85` — it implements the audited fact exactly — and then fails `assert total == 2975`, because `{"type": "thinking", "thinking": "ignored"}` costs `len(str(block))` ≈ 40 instead of 0. Unknown-block pricing is a separate rule that this fact's headline ("a file or document block costs exactly 1400") does not carry, and that the ticket's only relevant sentence ("dispatch on `block["type"]` using `.get`, never on the absence of a `"text"` key") does not settle.
```

**Recommendation.** Keep the fact — it is genuinely discriminating and cheaply testable — and fix the test, in three edits:

1. **Split the unknown-block rule out of the deciding total.** Either drop `unknown` from the mixed list (making it `5 + 85 + 85 + 1400 + 1400 == 2975 - 0`, i.e. re-baseline to 2975 with five entries), or keep it but assert it separately as `assert calculate_input_tokens([unknown], encoder) == 0` so a failure is attributable to the unknown-type rule rather than to the document price. If unknown-types-cost-0 is meant to be graded, it belongs in the open ticket's `calculate_input_tokens` bullet list ("a block whose `type` is none of these contributes 0"), not smuggled into an arithmetic identity in a hidden fact about documents.

2. **Relax the constant-shape check.** Replace `assert per_document == 1400` with something that accepts a mapping (`assert 1400 in (per_document.values() if isinstance(per_document, dict) else (per_document,))`), or delete it — the four single-block assertions already pin the price exactly, and the symbol check only adds a way for a correct implementation to fail on naming style.

3. **Re-file the fact.** This is not an observability of r1's size/count ceilings; it has no relationship to them. Either move it under a requirement about the estimator, or state r1 as covering two things. As written, a reader of r1 cannot tell why this clause is there, and the clue that reveals "documents are 1400" has to be planted independently of the clue that reveals the 20/24/45 MB ceilings anyway.

After edits 1 and 2, re-run the blind bracket: the fact should still come back `hidden`, since the divergence (1400 vs `_OPENAI_TOKENS_PER_IMAGE["low"]`) is untouched by any of them.


## g8.r2.rule — ship

**Divergent action.** In `attachment.py`: `_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12` and `def attachment_fingerprint(payload: str) -> str: return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_ATTACHMENT_FINGERPRINT_HEX_LEN]`, plus a seventh required field `fingerprint: str` on the frozen `AttachmentBlock`; and in `_canonical_attachment_block`, after `payload` is decided (url text or `serialize()` output), passing `fingerprint=attachment_fingerprint(payload)` into the block constructor. The blind agent constructs `AttachmentBlock(kind=..., source=..., mime_type=..., payload=..., filename=..., detail=...)` with exactly the six fields the ticket lists and imports no `hashlib` at all.

**The assertion.** `assert fingerprint == \"sha256:fc1c4358d4aa\"`, immediately reinforced by `assert fingerprint == digest_of(PDF_B64)`. It depends on one thing outside this requirement: the OPEN ticket's definition of `payload` (a non-remote `url` gives `source == \"base64\"` with `BaseType.serialize()` output as `payload`). An agent who fingerprints correctly but botches base64 serialization fails r2.rule as collateral. That coupling is to A, not to a sibling hidden fact, and is unavoidable since the fingerprint is defined over the payload — but it means this assertion is not hermetic to r2.

**Catalog A.** clean

**Catalog B.** clean

**Recommendation.** Ship r2.rule, after three cheap verifications I could not run here (no file tools in this session):

1. CLUE PRECISION — the decisive assertion is a literal equality with three free parameters. Confirm the planted clue states, verbatim and together: the `"sha256:"` prefix, truncation to 12 hex characters, that the digest covers the payload STRING (base64 text, not decoded bytes), and the field name `fingerprint`. A clue reading "we stamp each block with a short content hash" leaves an informed agent to guess all four and fail `== "sha256:fc1c4358d4aa"`. This is the only realistic way this fact fails a correct agent.

2. `read_field` LENIENCY — confirm `harness.read_field(block, "fingerprint")` resolves a pydantic `@computed_field` or plain `@property`, not just an entry in `model_fields`. Deriving the fingerprint from `payload` as a computed property is a legitimate reading of "carries a fingerprint" and is observationally identical; if `read_field` inspects `model_fields`, add a getattr fallback.

3. REQUIRED-FIELD BLAST RADIUS — r2.rule and r1.rule each add a REQUIRED field to a frozen model. Confirm `test_open.py` never constructs `AttachmentBlock(...)` with an exhaustive or positional field list (it should always go through `block_of`), or a correct hidden implementation will red the open suite.

Separately, and outside this field: cut or rewrite r2.exclusions_or_crossover. As written it is satisfied by the same single expression as `rule`, so it grades one line twice. If you want it to carry weight, point it at something `rule` does not force — e.g. that a url block's fingerprint is computed even though the URL is never fetched, asserted against a *fake that would raise if read*.


## g8.r2.scope — ship

**Divergent action.** In the filename-derivation branch of `_canonical_attachment_block` (or a helper in `attachment.py`), the informed agent writes a cap keyed on a new constant `_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, extension-preserving:

```python
name = os.path.basename(data.url.split("?", 1)[0]) or _FALLBACK_ATTACHMENT_FILENAME
if len(name) > _MAX_ATTACHMENT_FILENAME_LEN:
    ext = os.path.splitext(name)[1]
    name = name[: _MAX_ATTACHMENT_FILENAME_LEN - len(ext)] + ext if len(ext) < _MAX_ATTACHMENT_FILENAME_LEN else name[:_MAX_ATTACHMENT_FILENAME_LEN]
filename = name
```

The blind agent writes exactly the ticket's sentence and stops: `filename = os.path.basename(data.url.split("?", 1)[0]) or _FALLBACK_ATTACHMENT_FILENAME`, with no `len(...) >` branch, no `splitext` call, and no length constant anywhere in the tree. The two diverge concretely on the presence of the `64 - len(ext)` slice.

**The assertion.** `assert capped == "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf"` (with `capped = read_field(block_of(stub, File(url=LONG_PDF_URL)), "filename")`).

Dependencies: it needs `_canonical_attachment_block` to exist and to derive a filename from the basename at all — both open-ticket obligations — and it needs the `.pdf` MIME guess to succeed so the block builds instead of raising `UnknownAttachmentMimeType`. Given the open ticket is implemented, the *value* of this assertion depends on nothing but r2.scope: no sibling fact, no r1 fact, and no other hidden requirement can change it. The adjacent `render_openai(block) == {...}` line is the one place where an open-ticket renderer bug could sink this fact for an unrelated reason.

**Catalog A.** clean

**Catalog B.** clean

**Recommendation.** Ship as-is. The divergent action is concrete (the `_MAX_ATTACHMENT_FILENAME_LEN = 64` constant plus the `name[: 64 - len(ext)] + ext` slice), the ticket actively points the other way, the three boundary literals check out by hand (73→64 with `.pdf` kept, 64 untouched, 72-with-no-extension→first 64), and no Catalog A or B pattern lands.

Two non-blocking notes for whoever maintains this:

1. The `render_openai(block) == {"type": "file", "file": {...}}` full-dict equality inside the scope test imports the open ticket's document/url branch into r2.scope's verdict. Since the preceding bare `capped == ...` line already decides the fact, consider weakening the render check to `render_openai(block)["file"]["filename"] == capped and render_openai(block)["file"]["file_url"] == LONG_PDF_URL` so a renderer bug is charged to the open ticket rather than to this hidden fact. Optional; it only affects triage, not discrimination.

2. This fact overrides the ticket's filename sentence rather than extending it, so the clue must read as authoritative about the cap. If validation condition 3 (ticket + clues) ever regresses here, fix the clue's wording — not the test.

Unrelated inconsistency spotted while auditing, worth a look but outside this fact: the ticket derives the filename by splitting on `?` only, so `Image(url=".../cat.jpeg#page=2")` yields filename `"cat.jpeg#page=2"`, which contradicts the comment in r2.exclusions' test that a fragment "neither reaches the filename". No assertion depends on it today.


## g8.r2.exclusions_or_crossover — cut

**Divergent action.** None exists that is distinct from the sibling r2.rule. Given rule ("a required `fingerprint: str` field that `_canonical_attachment_block` sets from the block's payload") and the open ticket ("A remote `url` ... gives `source == "url"` with the URL as `payload`"), the code both a clue-informed and a rule-informed agent writes is the same single expression at the one construction site: `fingerprint=attachment_fingerprint(payload)`. There is no url branch, no `.split("?")`, no decode step for this fact to add. The only code that *violates* it is an extra special case (`attachment_fingerprint(data.url.split("?", 1)[0])` or leaving the field off url blocks), i.e. deliberate additional work. Per the rubric's diagnostic, that makes this a coincidence relative to its own sibling.

**The assertion.** `assert fingerprint == read_field(inline, "fingerprint")` (with `assert fingerprint is not None` gating it). It depends on two things other than this requirement: (1) r2.rule — if `fingerprint` does not exist or is not `attachment_fingerprint(payload)`, this fails for rule's reason, not this one; and (2) the open ticket's own payload/MIME semantics — it requires `Image(content=REMOTE_JPEG).serialize()` to return the str unchanged (asserted as `read_field(inline, "payload") == REMOTE_JPEG`), and the neighbouring `fragment` case requires the ticket's fragment-stripping MIME guess, without which `Image(url=".../cat.jpeg#page=2")` raises `UnknownAttachmentMimeType` and this test errors for a reason entirely outside r2.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The fact is a negative carve-out — 'fingerprinted identically rather than left without one' and 'never the decoded bytes'. Both are satisfied by writing no url-specific code and by not decoding. `fingerprint: str` is a required pydantic field on a frozen model, so omitting a url block's fingerprint is not even inaction, it is a validation error the agent must work around. Restraint is never tested.
- `ticket_gives_it_away` — The residual content of this fact — that the digest covers the URL 'exactly as given, query and fragment included' — is handed over by the open ticket's own definition of the thing being hashed: 'A remote `url` (per `is_remote`) gives `source == "url"` with the URL as `payload`.' Once the sibling says 'set from the block's payload', the ticket has already said what that payload is.
- `obvious_implementation_does_it` — The single most natural implementation of r2.rule is one line at the one place a block is constructed: `AttachmentBlock(..., payload=payload, fingerprint=attachment_fingerprint(payload))`. That is source-agnostic by construction and passes every assertion in this test. An agent who read only the `rule` half of the clue passes `exclusions` without ever considering url blocks.

**Catalog B.**
- `observable_belongs_to_another_fact` — The only channel is `read_field(block, "fingerprint")`, which is exactly r2.rule's channel. r2.rule's test already asserts the full digest semantics including the base64-text half of this fact: `assert fingerprint == digest_of(PDF_B64)` and `assert fingerprint == "sha256:fc1c4358d4aa"` for a file holding `PDF_BYTES`. Grading this fact through that field double-counts `rule`: any tree that fails `rule` fails this too, mechanically.
- `no_independent_content` — The fact restates its neighbour. Half of it ('a base64 block hashes its base64 text, never the decoded bytes') is already decided by rule's exact-value assertions; the other half ('a url block is fingerprinted too, over the payload string') is the arithmetic of rule's 'sets from the block's payload' plus the ticket's 'the URL as `payload`'. The single non-redundant assertion in the entire test is `read_field(bare, "fingerprint") != fingerprint` (the query participates), which is a one-line clarification of rule, not a fact.

**Recommendation.** Cut `r2.exclusions_or_crossover` as a separate graded fact and fold its one piece of real content into `r2.rule`. Concretely: delete `test_exclusions__a_url_block_is_fingerprinted_over_its_url_text` and add to `test_rule__...` the two lines that are not already there — `assert read_field(block_of(stub, Image(url=REMOTE_JPEG)), \"fingerprint\") == digest_of(REMOTE_JPEG)` and `assert read_field(block_of(stub, Image(url=\"https://cdn.example.com/photos/cat.jpeg\")), \"fingerprint\") != digest_of(REMOTE_JPEG)`. Also reword r2.rule to say the field is set from `block.payload` for every source, so the clue carries the query-inclusion consequence directly instead of needing a second sentence. If you would rather keep four facts in r2, replace this one with something that requires its own branch and cannot be derived from `rule` plus the ticket — e.g. a fingerprint that must survive a specific re-derivation path, or a distinct field with its own construction rule. Separately, whatever survives should stop relying on `Image(url=\".../cat.jpeg#page=2\")`: that case is decided by the open ticket's fragment-stripping MIME guess and will red this fact for an unrelated defect.


## g8.r2.failure_behavior — retest

**Divergent action.** In `attachment.py`, `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")` plus `def normalize_detail(value): candidate = str(value).strip().lower() if value is not None else "auto"; if candidate in _SUPPORTED_IMAGE_DETAILS: return candidate; logger.warning(...); return "auto"`, wired into `_canonical_attachment_block` as `detail = normalize_detail(getattr(data, "detail", "auto")) if kind == "image" else None`. The blind agent writes the line the ticket's wording points at instead: `detail = getattr(data, "detail", "auto") if kind == "image" else None` — no vocabulary tuple, no `.strip().lower()`, no fallback branch, no warning. The concrete divergence is the `if candidate in _SUPPORTED_IMAGE_DETAILS: ... else: logger.warning(); return "auto"` branch and the `.strip().lower()` on it.

**The assertion.** `assert read_field(block_of(stub, Image(content=b"x", detail="HIGH")), "detail") == "high"` (with `assert read_field(downgraded, "detail") == "auto"` as its partner for the unknown-value half). It depends on more than this requirement: it needs the open ticket's `_canonical_attachment_block` to exist and to take the inline-content path, and the surrounding `assert recorder.count == 1` / `assert quiet.count == 0` depend on the *global* WARNING count on the root logger plus on curator's log routing (`capture_warnings` attaches to `logging.getLogger("curator")`, which is not an ancestor of `bespokelabs.curator.*`, so capture rides entirely on propagation to root).

**Catalog A.**
- `model_already_knows_it` — `("auto", "low", "high")` is the published OpenAI `image_url.detail` enum, reproduced from priors by any model. The clue therefore contributes only the *policy* (normalize at block-build, downgrade rather than reject, warn once) — not the vocabulary itself, which is the part of the fact stated most concretely: `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")`.
- `obvious_implementation_does_it` — Partially, and this is the live risk the one blind sample may have missed. The ticket makes the agent write, in this very module, `normalize_mime_type` — "lowercase, strip surrounding whitespace" — and also establishes the unknown-value idiom "If the guess fails, `mime_type` stays `None` ... and exactly one `logger.warning` is emitted." A symmetric `normalize_detail` doing `.strip().lower()` plus a warned fallback is the primed, house-style move in a file the agent is already writing, against an enum it already knows.

**Catalog B.**
- `observable_belongs_to_another_fact` — The warning-count channel is shared with the open ticket's own MIME rule ("exactly one `logger.warning` is emitted"), and `recorder`/`quiet` count every WARNING record on root, not just detail ones. The final assertion also re-grades the open feature: `assert render_openai(...) == {"type": "image_url", "image_url": {"url": "data:image/png;base64,eA==", "detail": "high"}}` fails an agent whose only mistake is in `_render_openai_block` or the `image/png` inline default.

**A blind build that passes anyway:**

```
```python
# base_online_request_processor.py, ticket only — the agent has just written
# normalize_mime_type ("lowercase, strip") next door, and knows the OpenAI enum.
_SUPPORTED_DETAILS = ("auto", "low", "high")

...
if kind == "image":
    raw = getattr(data, "detail", "auto")
    detail = str(raw).strip().lower() if raw is not None else "auto"
    if detail not in _SUPPORTED_DETAILS:
        logger.warning("Unsupported image detail %r; using 'auto'.", raw)
        detail = "auto"
else:
    detail = None
```
This is ticket-only defensive code: the ticket hands over the `.strip().lower()` idiom in `normalize_mime_type` and the "unknown value -> fallback + exactly one `logger.warning`" idiom in the MIME rule, and `("auto","low","high")` is published OpenAI surface. It passes every assertion in the failure_behavior test, including `quiet.count == 0`, without the helper existing (so the `normalize_detail is not None` and `_SUPPORTED_IMAGE_DETAILS` guarded branches are skipped). Not the modal blind implementation, but a plausible one the single blind sample did not draw.
```

**A correct build the test rejects:**

```
```python
# attachment.py — the helper kept PURE, exactly as the fact's own word demands.
_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")

def normalize_detail(value: str | None) -> str:
    """Pure: no I/O, no logging."""
    if value is None:
        return "auto"
    candidate = str(value).strip().lower()
    return candidate if candidate in _SUPPORTED_IMAGE_DETAILS else "auto"

# base_online_request_processor.py — the warning lives at the call site.
detail = normalize_detail(getattr(data, "detail", "auto"))
if raw is not None and detail == "auto" and str(raw).strip().lower() != "auto":
    logger.warning("Unsupported image detail %r; falling back to 'auto'.", raw)
```
Every block-level and render-level assertion passes and exactly one warning is emitted per downgraded block. The test still fails it at `with capture_warnings() as recorder: assert normalize_detail("ultra") == "auto"` / `assert recorder.count == 1`, because the guarded branch demands the *helper itself* warn. The fact says "a **pure** `normalize_detail(value: str | None) -> str` ... emitting exactly one `logger.warning`" — those clauses contradict, and this is the reading that honours "pure". A second correct-fails variant: any implementation that logs a warning when the filename falls back to `_FALLBACK_ATTACHMENT_FILENAME` (all probes use `Image(content=b"x")` with no `url`) reads `recorder.count == 2` and `quiet.count > 0`; nothing forbids that warning.
```

**Recommendation.** Retest — keep the fact, fix two things in the grader. (1) Scope the warning count to this fact: have `Recorder.emit` keep only records whose `record.getMessage()` contains the rejected value (`"ultra"`) or the word `detail`, and assert on that filtered count, so an unrelated-but-legal warning on the `attachment.bin` filename fallback in the same `_canonical_attachment_block` call cannot fail a correct agent. (2) In the `if normalize_detail is not None:` branch, drop `assert recorder.count == 1` and keep only `assert normalize_detail("ultra") == "auto"` — the fact calls the helper "pure", so warning at the call site must be allowed; grade "exactly one warning" solely at block-build time. Optionally (3) drop the full-dict `render_openai(...) == {...}` equality in favour of `render_openai(...)["image_url"]["detail"] == "high"`, so a broken `_render_openai_block` fails the open ticket rather than r2. Also worth re-running the blind bracket with a second sample seeded toward defensive enum-clamping, given the ticket's neighbouring `normalize_mime_type` primes `.strip().lower()` and the fallback-plus-one-warning shape.
