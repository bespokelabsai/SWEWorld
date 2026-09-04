# g8 — the requirement, reduced to what is graded

**685 words → 521** across 9 facts and 92 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g8.r1.rule` | 125 → 90 | 12 | 6 |
| `g8.r1.scope` | 91 → 69 | 5 | 6 |
| `g8.r1.exclusions_or_crossover` | 42 → 30 | 7 | 1 |
| `g8.r1.failure_behavior` | 83 → 66 | 11 | 4 |
| `g8.r1.observability` | 45 → 40 | 8 | 2 |
| `g8.r2.rule` | 55 → 45 | 11 | 2 |
| `g8.r2.scope` | 98 → 73 | 10 | 2 |
| `g8.r2.exclusions_or_crossover` | 54 → 39 | 9 | 2 |
| `g8.r2.failure_behavior` | 92 → 69 | 19 | 4 |

## `g8.r1.rule`

**Now (90 words):**

Each base64 payload is measured in megabytes from its base64 length and recorded on the block as a `size_mb: float` field; a measurement strictly greater than 20.0 MB for a block whose kind is "image", or strictly greater than 24.0 MB for a block whose kind is "document", raises `AttachmentTooLarge(kind, size_mb, limit_mb)` — an `AttachmentError` subclass storing `.kind`, `.size_mb` and `.limit_mb`, message `f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit."`. The measurement and the comparison happen inside `_canonical_attachment_block`, before the payload is offered to the provider's `file_upload_limit_check` hook.

**Dropped, because no assertion checks it:**

- "The base owns a per-kind ceiling on base64 attachment payloads:" — framing/ownership claim; the two per-kind ceilings and the base-before-hook ordering are both stated outright later, so nothing graded rests on this lead-in.
- "once" (from "measured once in megabytes") — a no-double-measurement claim; no assertion counts measurements.
- "(the block kind)" — gloss on `.kind`; the attribute name and its position in the constructor triple survive for #5.
- "(the measured value)" — gloss on `.size_mb`; name and position survive.
- "(the ceiling that was exceeded)" — gloss on `.limit_mb`; name and position survive.
- ", so the provider hook only ever sees payloads the shared ceiling already accepted" — a "so" clause restating the ordering the preceding clause already specifies.

**Kept despite looking like padding:** "The measurement and the comparison happen inside `_canonical_attachment_block`, before the payload is offered to the provider's `file_upload_limit_check` hook" reads like a why-clause but is the rule itself: #7 checks the hook was never called for the over-limit image (`refusing.calls == []`), #12 checks it was called with exactly `[PAYLOAD_24MB]`, and #8/#9 need the document path to reach the hook and surface its RuntimeError. Both occurrences of "strictly greater" also stay: #8/#10/#11 turn on 24.0 passing the document ceiling rather than tripping it, while #5/#6 turn on the same 24.0 tripping the image ceiling.

## `g8.r1.scope`

**Now (69 words):**

A whole-prompt ceiling of 45.0 MB belongs to `_handle_multi_modal_prompt`: after every attachment has been converted to a block (all `file_upload_limit_check` calls have already run), the `size_mb` values of the `source == "base64"` blocks are summed and compared, strictly greater, against 45.0; on overflow the same exception type is raised with `kind == "prompt"`, `size_mb` equal to the whole-prompt sum and `limit_mb == 45.0`. `_canonical_attachment_block` / `_format_multimodal` never apply it.

**Dropped, because no assertion checks it:**

- "aggregate" (in "A whole-prompt aggregate ceiling") — redundant with "whole-prompt", which is kept and carries the scope that assertion #2's 60.0 depends on.
- "also exists, and it" (in "of 45.0 MB also exists, and it belongs to") — announces that the rule exists rather than stating it; no assertion reads it.
- "of the prompt" (in "after every attachment of the prompt has been converted") — restates the scope already fixed by "whole-prompt ceiling".
- "so after all per-attachment checks and" — the "so" consequence framing plus a cross-reference to the per-attachment checks specified elsewhere; the ordering fact assertion #3 turns on survives in the retained "(all `file_upload_limit_check` calls have already run)".
- "the literal" (in "raised with the literal `kind == \"prompt\"`") — emphasis only; the exact value `kind == "prompt"` graded by assertion #2 is still stated verbatim.
- "It is not evaluated incrementally, and" — the same rule said a second time in different words; already pinned by "after every attachment has been converted to a block ... are summed" and by "`size_mb` equal to the whole-prompt sum".

**Kept despite looking like padding:** The parenthetical "(all `file_upload_limit_check` calls have already run)" reads like an aside, but assertion #3 (`len(stub.calls) == 4`) counts exactly those calls and requires all four to precede the comparison, so the identifier and the ordering had to stay. "`size_mb` equal to the whole-prompt sum" is likewise kept for #2 (60.0) and for #3's whole-prompt-not-running-total point, and the closing sentence naming `_canonical_attachment_block` / `_format_multimodal` is kept for #4 (`len(content) == 2`) and #5 (`len(control.calls) == 2`), which only pass if those two paths refuse nothing.

## `g8.r1.exclusions_or_crossover`

**Now (30 words):**

A `source == "url"` block is never measured: its `size_mb` is `None`, it is not compared against any per-kind ceiling, and it contributes nothing to the 45.0 MB prompt sum.

**Dropped, because no assertion checks it:**

- — a prompt of remote URLs of any size passes both ceilings": a restatement of the two preceding clauses in different words, and a consequence ("of any size passes") that no assertion checks; nothing tests a prompt built solely of large remote URLs.

**Kept despite looking like padding:** "it is not compared against any per-kind ceiling, and it contributes nothing to the 45.0 MB prompt sum" reads like it repeats "never measured", but both halves had to stay. `stub.calls == []` and `urls.calls == []` require the url block to be skipped before any measurement call is made, and `mixed.calls == [PDF_B64]` requires that skipping to hold when a measured block sits beside it — so the requirement must name both exclusion points, not just say "not measured". `size_mb` is `None` is read directly by assertion #2 and `source == "url"` by #1. `len(content) == 7` forces the block to still appear in content despite being unmeasured, which "never measured" (rather than "dropped" or "rejected") is what preserves.

## `g8.r1.failure_behavior`

**Now (66 words):**

More than 12 attachments is refused: `_ATTACHMENT_COUNT_LIMIT: int = 12` and `TooManyAttachments(AttachmentError)` with `__init__(self, count: int, limit: int)` storing `.count` and `.limit`, message `f"Prompt has {count} attachments, over the limit of {limit}."`. `_handle_multi_modal_prompt` counts `len(message.attachments())` first and raises when the count is strictly greater than 12; nothing is serialized and `file_upload_limit_check` is not called. 40 texts and one image is fine, and 12 attachments is fine.

**Dropped, because no assertion checks it:**

- "in one message" — no assertion inspects message structure, only the attachment count.
- "before any block is built," — restatement of "counts `len(message.attachments())` first"; #7 follows from counting first plus nothing being serialized.
- "for an over-count prompt" — trailing qualifier; the clause is already scoped to the raising path.
- "`texts` are not counted, so" — the why. What is graded is the outcome (41 content blocks, 1 serializer call), not the reason texts are exempt.

**Kept despite looking like padding:** "40 texts and one image is fine, and 12 attachments is fine" reads like two redundant examples after the rule, but neither can go: the 40-texts case is the only source for #10 (`len(content) == 41`) and #11 (`len(texts.calls) == 1`), and the 12-attachment case the only source for #8 (`len(content) == 13`) and #9 (`len(twelve.calls) == 12`). "nothing is serialized and `file_upload_limit_check` is not called" stayed whole because #7's comment covers both "serialized or offered". Result is 66 words rather than 58: the identifier, the `__init__` signature and the f-string are graded verbatim and cannot be compressed.

## `g8.r1.observability`

**Now (40 words):**

In `calculate_input_tokens`, a `"file"` or `"document"` block costs 1400 tokens (`_OPENAI_TOKENS_PER_DOCUMENT = 1400`): with a 1-token-per-character encoder, `[text "hello", image_url, anthropic image, file, document, unknown "thinking"]` totals `5 + 85 + 85 + 1400 + 1400 + 0 == 2975`.

**Dropped, because no assertion checks it:**

- "not the image rate" — a contrast clause saying what the price is not; no assertion checks a negation, and the image rate itself (85) survives verbatim in the worked example that #3, #4 and #5 read.
- "exactly" — emphasis on a number the same sentence already states twice, as `1400 tokens` and as `_OPENAI_TOKENS_PER_DOCUMENT = 1400`.

**Kept despite looking like padding:** The worked example `[text "hello", image_url, anthropic image, file, document, unknown "thinking"]` totalling `5 + 85 + 85 + 1400 + 1400 + 0 == 2975` reads like a second demonstration of the opening rule, but it is the requirement's only statement that an image block costs 85 (#3, #4), that the total is 2975 (#5), and that an unknown block costs 0 — so it stays word for word. The constant `_OPENAI_TOKENS_PER_DOCUMENT = 1400` restates the 1400 given a few words earlier, but #7 reads a per-document constant by value, so the name and number stay. Nothing in the requirement speaks to #6 (`isinstance(total, int)`) or #8 (`base64.b64decode(PDF_B64) == PDF_BYTES`), so there was no text to cut for those.

## `g8.r2.rule`

**Now (45 words):**

`attachment.py` defines `_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12` and `attachment_fingerprint(payload: str) -> str` returning `"sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]`; `AttachmentBlock` gains a required `fingerprint: str` field that `_canonical_attachment_block` sets from the block's payload. So a block for a file holding `b"%PDF-1.4\n"` has `fingerprint == "sha256:fc1c4358d4aa"`, and `Image(content=b"x")` gives `"sha256:5e21d86b709b"`.

**Dropped, because no assertion checks it:**

- "Every canonical block carries a short content fingerprint." — a lead-in summary of the sentence that follows it. No assertion checks that blocks "carry" anything; #1–#7 read the `fingerprint` field that the surviving spec sentence already names precisely.
- the word "pure" in "a pure `attachment_fingerprint(payload: str) -> str`" — purity is never asserted; #8, #9 and #10 only call the helper and compare its return value.

**Kept despite looking like padding:** The second worked example, "and `Image(content=b\"x\")` gives `\"sha256:5e21d86b709b\"`", reads like a redundant demonstration of a rule the `b\"%PDF-1.4\\n\"` example already pins, but three assertions turn on its literals: #4 on `\"sha256:5e21d86b709b\"`, #9 on `helper(\"eA==\") == \"sha256:5e21d86b709b\"`, and #6 on `payload == \"eA==\"` (the base64 of `b\"x\"`). #5 additionally requires the two fingerprints to differ, so both digests must stay stated. The formula stays verbatim for #8/#9/#10, the constant name and value for #11, and #3's prefix-and-length check falls out of that same formula.

## `g8.r2.scope`

**Now (73 words):**

The derived `filename` is capped at `_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, extension kept: when the basename is longer than 64 characters it becomes `name[: 64 - len(ext)] + ext` for `ext = os.path.splitext(name)[1]`; a name of 64 or fewer characters is untouched. Only `block.filename` is capped — `payload` keeps the full URL and the attachment's own `url` is never modified, so a 73-character PDF basename renders as `{"filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf", "file_url": <the full untruncated URL>}`.

**Dropped, because no assertion checks it:**

- "which is exactly 64 characters and still ends in its extension" — a "which" clause restating what the surviving formula `name[: 64 - len(ext)] + ext` already produces; #2's length and suffix follow from it.
- "when `len(ext) >= 64` the name is simply cut to its first 64 characters" — no assertion exercises an extension of 64 or more characters. The extensionless case in #8/#9 is `ext = ""`, which the surviving formula covers.

**Kept despite looking like padding:** The 73-character PDF example reads like a demonstration, but #1 and #5 grade on its literals: the exact string "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf" and the `filename`/`file_url` pairing with the untruncated URL. The trailing "a name of 64 or fewer characters is untouched" also looks like a trivial edge note, but #6, #7 and #10 rest entirely on it.

## `g8.r2.exclusions_or_crossover`

**Now (39 words):**

A `source == "url"` block is fingerprinted identically: the digest is taken over the payload *string*, query and fragment included — `https://cdn.example.com/photos/cat.jpeg?size=large` gives `fingerprint == "sha256:80ce7facd006"` — and a base64 block hashes its base64 text, never the decoded bytes.

**Dropped, because no assertion checks it:**

- "rather than left without one" — a restatement of presence; "is fingerprinted" already carries assertion #2 (`fingerprint is not None`), so the contrast is emphasis, not a checked fact.
- "so a url block hashes its URL exactly as given," — a "so" clause restating "the digest is taken over the payload *string*" in different words; no assertion reads it that isn't already covered by the payload-string rule plus "query and fragment included".

**Kept despite looking like padding:** The worked example — `https://cdn.example.com/photos/cat.jpeg?size=large` gives `fingerprint == "sha256:80ce7facd006"` — reads like decoration, since no assertion compares against that literal digest. It stays because it is the single worked example and the only place the digest's shape is pinned (sha256, `sha256:` prefix, 12 hex characters); assertion #9, `hashlib.sha256(PDF_BYTES).hexdigest()[:12] not in text_id`, only bites against a 12-character truncation, and the URL literal is the value assertion #4 reads back as `REMOTE_JPEG`. Similarly, "query and fragment included" looks like an aside but is exactly the rule assertions #6 and #7 turn on, and "never the decoded bytes" is what #9 checks.

## `g8.r2.failure_behavior`

**Now (69 words):**

Image `detail` is normalized against a fixed vocabulary at block-build time: `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")` and a pure `normalize_detail(value: str | None) -> str` return `str(value).strip().lower()` when that lands in the vocabulary and `"auto"` otherwise, emitting exactly one `logger.warning` on the fallback and none on a hit or on `None`. So `Image(content=b"x", detail="HIGH")` gives a block `detail` of `"high"`; `Image.detail` itself keeps whatever the caller wrote.

**Dropped, because no assertion checks it:**

- , not passed through" — restatement of "is normalized"; no assertion distinguishes the two phrasings.
- "`" Low "` gives `"low"`" — second worked example of the strip/lower rule, already pinned by the `"HIGH"` example and by the literal `str(value).strip().lower()`.
- "and `"ultra"` is downgraded to `"auto"` with a warning" — third worked example; the fallback-to-`"auto"`-plus-exactly-one-`logger.warning` rule is already stated verbatim earlier in the sentence.
- "instead of being sent or rejected" — rationale/contrast with alternatives nobody implements; no assertion checks a rejection path or a raw pass-through send.

**Kept despite looking like padding:** "at block-build time" reads like scene-setting but stays: it is the only thing separating the normalized block value (#3, #4, #5, #6, #8, #9) from the untouched `Image.detail` (#1, #2). The `"HIGH"` worked example stays as the single concrete tie between an `Image` input and the block's `detail` output, which #3 and #11 both read. The exact tuple literal and its ordering stay for #18; the `normalize_detail` signature and `str(value).strip().lower()` stay for #13–#16; the warning counts stay for #7, #10, #17.
