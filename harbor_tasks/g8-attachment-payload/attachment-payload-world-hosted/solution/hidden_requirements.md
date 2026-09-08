# g8 — Canonical attachment blocks for multimodal prompts

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | — |
| `spec` | the ticket + both hidden requirements | — |
| `clues` | the ticket + all 51 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.4` where the 51 remarks live in chat, the wiki and mail | — |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Two requirements, `g8.r1` and `g8.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

**Nine facts, not ten.** `g8.r1` declares all five; `g8.r2` declares four — it has
no `observability`. `score.py` takes its keys from `tasks.json` rather than from a
fixed list of five, precisely so an absent fact is not invented and does not divide
the mean by the wrong number, so each of the nine is worth one ninth.
`open_feature` (did the agent build the feature at all?) carries weight **0.0**:
building the feature scores nothing, only recovering what nobody wrote down does.

The facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g8.r1` — three ceilings, at three different layers, in a fixed order

**In one sentence:** a per-kind size ceiling runs inside the block builder *before*
the provider's own hook, a whole-prompt ceiling runs after every block is built,
and a count limit runs before anything is serialised at all.

#### `rule` — the per-kind ceiling

Each base64 payload is measured in megabytes **from its base64 length** and
recorded on the block as a `size_mb: float` field.

| block kind | raises above |
|---|---|
| `"image"` | strictly greater than **20.0** MB |
| `"document"` | strictly greater than **24.0** MB |

The raise is `AttachmentTooLarge(kind, size_mb, limit_mb)` — an `AttachmentError`
subclass storing `.kind`, `.size_mb` and `.limit_mb`, with the message:

```
f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit."
```

**Ordering is load-bearing.** The measurement and the comparison happen inside
`_canonical_attachment_block`, *before* the payload is offered to the provider's
`file_upload_limit_check` hook.

#### `scope` — the whole-prompt ceiling belongs to a different function

A **45.0 MB** ceiling belongs to `_handle_multi_modal_prompt`, and only to it:

- it runs after every attachment has been converted to a block, so all
  `file_upload_limit_check` calls have already run
- it sums the `size_mb` of the `source == "base64"` blocks and compares **strictly
  greater** against `45.0`
- on overflow it raises the same exception type with `kind == "prompt"`, `size_mb`
  equal to the whole-prompt sum, and `limit_mb == 45.0`

`_canonical_attachment_block` / `_format_multimodal` **never** apply it.

#### `exclusions_or_crossover` — a URL block is not measured

A `source == "url"` block is never measured: its `size_mb` is `None`, it is not
compared against any per-kind ceiling, and it contributes **nothing** to the
45.0 MB prompt sum.

#### `failure_behavior` — more than twelve attachments

`_ATTACHMENT_COUNT_LIMIT: int = 12`, and `TooManyAttachments(AttachmentError)` with
`__init__(self, count: int, limit: int)` storing `.count` and `.limit`, message:

```
f"Prompt has {count} attachments, over the limit of {limit}."
```

`_handle_multi_modal_prompt` counts `len(message.attachments())` **first** and
raises when the count is strictly greater than 12. Nothing is serialised and
`file_upload_limit_check` is not called.

40 texts and one image is fine. 12 attachments is fine.

#### `observability` — the document token cost

In `calculate_input_tokens`, a `"file"` or `"document"` block costs **1400** tokens
(`_OPENAI_TOKENS_PER_DOCUMENT = 1400`). With a 1-token-per-character encoder:

```python
[text "hello", image_url, anthropic image, file, document, unknown "thinking"]
   5      +      85      +       85       + 1400 +  1400   +        0        == 2975
```

> **The herring** — what the team decided first and later reversed: the first
> version used a single 20 MB ceiling for every kind and ran the provider's own
> `file_upload_limit_check` first. It was reversed after 22 MB PDFs that Anthropic
> accepts were rejected by the shared check, and the ordering was flipped so the
> shared ceiling speaks before the provider hook.

---

### `g8.r2` — a fingerprint over the payload string, and a filename cap that keeps the extension

**In one sentence:** every block carries a short sha256 of the payload *as
written*, the derived filename is truncated without losing its extension, and
`detail` is normalised to a fixed vocabulary rather than passed through.

#### `rule` — the fingerprint

`attachment.py` defines:

```python
_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12

def attachment_fingerprint(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
```

`AttachmentBlock` gains a **required** `fingerprint: str` field, which
`_canonical_attachment_block` sets from the block's payload.

| payload | fingerprint |
|---|---|
| a file holding `b"%PDF-1.4\n"` | `"sha256:fc1c4358d4aa"` |
| `Image(content=b"x")` | `"sha256:5e21d86b709b"` |

#### `scope` — the filename cap

`_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, **extension kept**. When the basename is
longer than 64 characters it becomes `name[: 64 - len(ext)] + ext` for
`ext = os.path.splitext(name)[1]`; a name of 64 or fewer characters is untouched.

Only `block.filename` is capped — `payload` keeps the full URL and the attachment's
own `url` is never modified. So a 73-character PDF basename renders as:

```json
{"filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf",
 "file_url": "<the full untruncated URL>"}
```

#### `exclusions_or_crossover` — a URL block is fingerprinted the same way

The digest is taken over the payload **string**, query and fragment included:

```python
"https://cdn.example.com/photos/cat.jpeg?size=large"  ->  "sha256:80ce7facd006"
```

And a base64 block hashes its **base64 text**, never the decoded bytes.

#### `failure_behavior` — `detail` is normalised, not rejected

```python
_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")
```

A pure `normalize_detail(value: str | None) -> str` returns
`str(value).strip().lower()` when that lands in the vocabulary, and `"auto"`
otherwise — emitting **exactly one** `logger.warning` on the fallback, and none on
a hit or on `None`.

So `Image(content=b"x", detail="HIGH")` gives a block `detail` of `"high"`;
`Image.detail` itself keeps whatever the caller wrote.

#### `observability` — not declared

This requirement has no `observability` fact, which is why g8 is graded on nine
facts rather than ten. Nothing to implement, and nothing scored here.

> **The herring** — what the team decided first and later reversed: `detail` was
> originally handed to the provider exactly as the caller wrote it. That was
> reversed after a typo'd `"hgih"` produced a provider 400 mid-run, and the team
> chose a silent downgrade to `"auto"` with a warning over failing the request.

---

## Where the remarks are spread

51 remarks in total — 43 clues, 4 herrings and 4 reversals — across 1 surfaces and 10 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **51** | `#pipeline` 11, `#code-review` 7, `#engineering` 6, `#releases` 5, `#cookbooks` 5, `#general` 5, `#viewer` 5, `#incidents` 4, `#random` 2, `#help` 1 |

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g8.r1

### g8.r1.s1 — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*The leap nobody states:* If the team wants a size stamped on the block and separate numbers for images and documents, and wants their own error raised before the provider's check runs, then the measurement and the comparison both live in the block constructor.

- **gideon** (2025-04-15, #pipeline): so basically the 31 meg screenshot went out to openai before anything objected, we paid for the upload and got a 400 back. that has to be caught localy.
- **dario** (2025-04-23, #pipeline): we already have the base64 string in hand when the block gets built, so i'd weigh that rather than decoding, and hang size_mb off the block itself rather than nesting it.
- **emil** (2025-04-29, #pipeline): from the run: `image attachment is 21.3 MB, over the 20.0 MB limit.` documents shouldn't sit on that number. and it's strictly over - exactly 20.0 goes through fine.
- **dermot** (2025-04-16, #pipeline): yeah - AttachmentTooLarge fires before we ever reach file_upload_limit_check, it subclasses AttachmentError like the rest and AttachmentError is a ValueError, so the old ValueError handlers still catch it.
- **nils** (2025-06-02, #general): let me think - the base64 text is what actually goes over the wire, so size_mb is what get_base64_size hands back for that string. it works the real byte count out of the length arithmetically instead of decoding, and the divisor in there is 1024*1024, not a 1000-based megabyte.
- **nikolai** (2025-05-06, #incidents): AttachmentTooLarge(kind, size_mb, limit_mb) and it keeps all three as .kind .size_mb and .limit_mb so a test can asssert on them not scrape a traceback

### g8.r1.s2 — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*The leap nobody states:* Per-attachment ceilings can all pass while the assembled body is still too big, so the total has to be checked somewhere that sees all the blocks at once, which is the assembly step and not the single-attachment path.

- **konrad** (2025-03-19, #pipeline): look, nine photos in one cookbook cell, every one of them under its own ceiling, and the request still came back rejected for body size. the per-attachment limit isn't catching this.
- **nils** (2025-03-14, #code-review): the base64 ones are what the wire actually carries, so the ceiling wants to be over those summed - 45 MB is about where they stopped accepting us
- **gideon** (2025-03-17, #code-review): so basically that total lives only in _handle_multi_modal_prompt - _format_multimodal still hands back both blocks for an over-45 set - and reusing the exception with kind prompt reads fine.
- **dario** (2025-03-18, #code-review): mhm - so even for a prompt that busts 45, every attachment still gets its file_upload_limit_check call first; the whole-prompt number comes after all of them, not woven in between.

### g8.r1.s3 — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*The leap nobody states:* We never hold the bytes for a link, so any number we put there would either require a network fetch or be made up, and neither belongs in a size check.

- **nikolai** (2025-03-19, #code-review): ran the branch locally and it's pulling down remote images just to weigh them, so my unit tests started reaching for the network, which i'd rather they didnt
- **emil** (2025-03-20, #code-review): let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. url blocks skip the per-kind ceilings and file_upload_limit_check entirely.
- **konrad** (2025-03-14, #engineering): look, for a url block we never hold the bytes, so size_mb stays empty and file_upload_limit_check never gets called on it - the hook only ever sees base64.
- **nils** (2025-03-17, #engineering): makes sense to me — a prompt that is twelve remote links has nothing of ours in the body, so those url blocks should be contributing nothing to the whole-prompt total.

### g8.r1.s4 — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*The leap nobody states:* If the complaint is the work done before the refusal, the count check has to come before any serializing or hook call, and a count is the only thing you can know that early.

- **gideon** (2025-03-14, #code-review): notebook handed us sixty images, we base64'd each one and passed that string itself into file_upload_limit_check before anything gave up. so basically the guard runs ahead of all that
- **konrad** (2025-03-19, #engineering): look, _ATTACHMENT_COUNT_LIMIT stays at 12 and texts don't count toward it - twelve is fine, thirteen is not. a cell with forty text chunks and one image is normal, nowhere near it.
- **nikolai** (2025-03-20, #engineering): ran it against the 31 image prompt and got `Prompt has 31 attachments, over the limit of 12.` which is exactly what i wanted to see instead of the memory spike
- **dario** (2025-03-24, #engineering): i think TooManyAttachments carries the count and the ceiling it broke, another AttachmentError subclass like AttachmentTooLarge, and it fires before we serialize a single one of them

### g8.r1.s5 — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*The leap nobody states:* Documents currently contribute nothing to the estimate, and the fix mirrors how images are already priced: one flat number per block.

- **gideon** (2025-05-02, #pipeline): honestly though, while I was poking at the same path - my anthropic run counted 85 per image and zero for the two document blocks, so the estimate is only half the mesage.
- **dermot** (2025-05-06, #releases): yeah ok - _OPENAI_TOKENS_PER_DOCUMENT beside the image constant, flat number whether it comes in as file or document. the image one is 85 for an image_url block, same as anthropic's.
- **emil** (2025-05-30, #releases): let me think through that - anthropic puts a pdf page near 1400 tokens, so we charge 1400 flat for each document block. the total comes back a plain int.
- **dario** (2025-05-05, #cookbooks): i think an unknown block kind - a thinking block say - just contributes zero to the estimate, we dont raise on it and we don't charge its text either

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): one ceiling, 20 mb, same number for images and documents — and honestly the provider's file_upload_limit_check runs first, ours only speaks once that hook clears.
- **konrad** (2025-01-22): right, settled the ordring: file_upload_limit_check runs first, then the shared 20 MB ceiling. one limit covers every kind, no per-kind numbers.

## g8.r2

### g8.r2.sc1 — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*The leap nobody states:* If you cannot compare two attachments without shipping megabytes of payload around, the thing you put on the block has to be small, stable, and self-describing about how it was made.

- **nils** (2025-04-07, #general): spent yesterday afternoon trying to demonstrate that two runs sent the same pdf. there is nothing on the block to compare, and we never log payloads - they're megabytes.
- **dermot** (2025-04-23, #pipeline): while we're in there, give the record a short digest of the payload and make fingerprint required. optional means half the call sites forget it and we're back to guessing
- **konrad** (2025-05-06, #code-review): took Dermot's review nit, no inline [:12] slice - `_ATTACHMENT_FINGERPRINT_HEX_LEN` sits next to the helper now. `attachment_fingerprint` takes the payload string and hands back the "sha256:" prefix already on it.
- **gideon** (2025-04-25, #viewer): so basically I pinned it in the test - tmp file with just %PDF-1.4 in it comes out sha256:fc1c4358d4aa, same value every run, algoritm is right there in the string
- **gideon** (2025-04-09, #incidents): so basically I expected attachment_fingerprint to special case the empty payload and it doesnt, "" just goes through sha256 like any other payload, prefix and all.

### g8.r2.sc2 — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*The leap nobody states:* A name that got shortened for readability is only safe to shorten if the part carrying meaning survives and nothing that has to be fetched or sent was shortened with it.

- **nikolai** (2025-03-21, #cookbooks): yep these finance exports land with 73-character basenames, full title plus two dates plus final - and the block is just {"type": "file", "file": {"filename": ..., "file_url": ...}} so its mostly filename
- **emil** (2025-04-03, #viewer): honestly 64 is plenty for the block name, past that its just the date written twice - `_MAX_ATTACHMENT_FILENAME_LEN` = 64, and a name thats exactly 64 we leave alone, only longer ones get cut.
- **konrad** (2025-03-24, #cookbooks): Look, I chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf. Suffix stays on; no extension means just the first 64 characters.
- **dario** (2025-04-11, #releases): honestly the 404 came from trimming the url along with the name - we only shorten the display name we derive, the payload url and the caller's File.url both stay untouched.

### g8.r2.sc3 — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*The leap nobody states:* If the digest is computed over whatever string the block already holds, the same rule covers both source kinds with no fetching and no decoding step.

- **gideon** (2025-04-10, #viewer): so basically my dedupe pass kept every remote image, the fingerprint comes back empty for anythng with an http url. half the run is remote tbh.
- **nikolai** (2025-04-11, #incidents): ran the same cat.jpeg twice A with ?size=large and B without and they came out as two seperate cache entries thats the behaviour i want just want it written down
- **dario** (2025-04-24, #pipeline): honestly we never open a remote one, so the helper hashes the stored url string exactly as we send it, query and anchor included, no kind marker and no salt.
- **emil** (2025-04-25, #random): honestly i tried decoding every payload before hashing and the 40k pass crawled — hashing the base64 text as-is pins the one-byte image at sha256:5e21d86b709b.
- **emil** (2025-04-21, #help): for what it's worth that pinned image value is straight out of the helper - attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", the block just stores what it gets back.
- **emil** (2025-04-17, #random): fwiw i ran it, attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006, and a base64 block whose text is that same string lands on the same digest.

### g8.r2.sc4 — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*The leap nobody states:* Case and whitespace differences are the user typing, not the user being wrong, so only a genuine miss deserves the fallback and the log line.

- **konrad** (2025-04-14, #viewer): Look, I burned an hour on a run where I passed detail="HIGH" and every image came back looking like auto. Shift key held down is not a typo.
- **emil** (2025-04-24, #viewer): for the module bullet - `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...]`, three entries, and index 0 is what the fallback hands back. `normalize_detail` is the only reader - give it None and you get "auto".
- **nils** (2025-04-21, #general): detail warning fired on all 40k images last night, most of which never set one - that's noise. and it rewrote Image.detail under me, we shouldn't mutate the source, my fixtures diff now
- **dermot** (2025-05-13, #pipeline): yeah ok - if it isn't one of the three we fall back to auto and log that once. nothing set at all logs nothing and the block still goes out with detail "auto".
- **nikolai** (2025-06-16, #pipeline): checked the openai side each image goes out as type image_url with an image_url object carrying url and detail and for inline we send the url as data:image/png;base64, then the payload

### herrings — believed at the time, reversed later

- **dario** (2025-01-31): for what it's worth the rest of 427 reads fine to me, detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid
- **konrad** (2025-02-13): Right, so no allowlist on detail then, its the caller's string and we just forward it. validating provider enums is not our job.


---


## Where every remark is

51 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #releases | konrad | [`g8.r1.g8-pre-r1-single-ceiling-dario`](#g8r1g8-pre-r1-single-ceiling-dario) | 9 | **herring** | — |
| 2025-01-22 | chat | #cookbooks | dermot | [`g8.r1.g8-pre-r1-single-ceiling-konrad`](#g8r1g8-pre-r1-single-ceiling-konrad) | 7 | **herring** | — |
| 2025-01-31 | chat | #engineering | emil | [`g8.r2.detail-passthrough-1`](#g8r2detail-passthrough-1) | 7 | **herring** | — |
| 2025-02-13 | chat | #general | gideon | [`g8.r2.detail-passthrough-2`](#g8r2detail-passthrough-2) | 7 | **herring** | — |
| 2025-03-14 | chat | #code-review | dario | [`g8.r1.s4-gideon`](#g8r1s4-gideon) | 7 | clue | `failure_behavior` |
| 2025-03-14 | chat | #engineering | dario | [`g8.r1.s3-konrad`](#g8r1s3-konrad) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-14 | chat | #code-review | gideon | [`g8.r1.s2-nils`](#g8r1s2-nils) | 8 | clue | `scope` |
| 2025-03-17 | chat | #code-review | nikolai | [`g8.r1.s2-gideon`](#g8r1s2-gideon) | 7 | clue | `scope` |
| 2025-03-17 | chat | #engineering | gideon | [`g8.r1.s3-nils`](#g8r1s3-nils) | 7 | clue | `exclusions_or_crossover`, `scope` |
| 2025-03-18 | chat | #code-review | gideon | [`g8.r1.s2-dario`](#g8r1s2-dario) | 7 | clue | `scope` |
| 2025-03-19 | chat | #engineering | gideon | [`g8.r1.s4-konrad`](#g8r1s4-konrad) | 7 | clue | `failure_behavior` |
| 2025-03-19 | chat | #pipeline | petar | [`g8.r1.s2-konrad`](#g8r1s2-konrad) | 8 | clue | `scope` |
| 2025-03-19 | chat | #code-review | nikolai | [`g8.r1.s3-nikolai`](#g8r1s3-nikolai) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-20 | chat | #cookbooks | dermot | [`g8.r1.rev2`](#g8r1rev2) | 8 | **reversal** of `g8.r1.g8-pre-r1-single-ceiling-konrad` | `rule` |
| 2025-03-20 | chat | #code-review | konrad | [`g8.r1.s3-emil`](#g8r1s3-emil) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-20 | chat | #engineering | dermot | [`g8.r1.s4-nikolai`](#g8r1s4-nikolai) | 9 | clue | `failure_behavior` |
| 2025-03-21 | chat | #cookbooks | dario | [`g8.r2.l5`](#g8r2l5) | 7 | clue | `scope` |
| 2025-03-24 | chat | #engineering | gideon | [`g8.r1.s4-dario`](#g8r1s4-dario) | 8 | clue | `failure_behavior` |
| 2025-03-24 | chat | #cookbooks | nikolai | [`g8.r2.l7`](#g8r2l7) | 7 | clue | `scope` |
| 2025-03-31 | chat | #releases | konrad | [`g8.r1.rev1`](#g8r1rev1) | 8 | **reversal** of `g8.r1.g8-pre-r1-single-ceiling-dario` | `rule` |
| 2025-04-03 | chat | #viewer | konrad | [`g8.r2.l6`](#g8r2l6) | 8 | clue | `scope` |
| 2025-04-07 | chat | #general | konrad | [`g8.r2.l1`](#g8r2l1) | 8 | clue | `rule` |
| 2025-04-09 | chat | #incidents | emil | [`g8.r2.say22`](#g8r2say22) | 8 | clue | `rule` |
| 2025-04-10 | chat | #viewer | konrad | [`g8.r2.l9`](#g8r2l9) | 7 | clue | `exclusions_or_crossover`, `rule` |
| 2025-04-11 | chat | #releases | nikolai | [`g8.r2.l8`](#g8r2l8) | 8 | clue | `scope` |
| 2025-04-11 | chat | #incidents | gideon | [`g8.r2.l10`](#g8r2l10) | 8 | clue | `exclusions_or_crossover` |
| 2025-04-14 | chat | #viewer | dermot | [`g8.r2.l13`](#g8r2l13) | 7 | clue | `failure_behavior` |
| 2025-04-15 | chat | #pipeline | dermot | [`g8.r1.s1-gideon`](#g8r1s1-gideon) | 8 | clue | `rule` |
| 2025-04-16 | chat | #pipeline | theo | [`g8.r1.s1-dermot`](#g8r1s1-dermot) | 9 | clue | `rule` |
| 2025-04-17 | chat | #random | nikolai | [`g8.r2.say23`](#g8r2say23) | 8 | clue | `exclusions_or_crossover` |
| 2025-04-18 | chat | #incidents | dermot | [`g8.r2.rev1`](#g8r2rev1) | 9 | **reversal** of `g8.r2.detail-passthrough-1` | `failure_behavior` |
| 2025-04-21 | chat | #general | gideon | [`g8.r2.l15`](#g8r2l15) | 8 | clue | `failure_behavior` |
| 2025-04-21 | chat | #help | petar | [`g8.r2.say21`](#g8r2say21) | 7 | clue | `rule` |
| 2025-04-23 | chat | #pipeline | nils | [`g8.r1.s1-dario`](#g8r1s1-dario) | 9 | clue | `rule` |
| 2025-04-23 | chat | #pipeline | nils | [`g8.r2.l2`](#g8r2l2) | 8 | clue | `rule` |
| 2025-04-24 | chat | #pipeline | emil | [`g8.r2.l11`](#g8r2l11) | 8 | clue | `exclusions_or_crossover` |
| 2025-04-24 | chat | #viewer | konrad | [`g8.r2.l14`](#g8r2l14) | 7 | clue | `failure_behavior` |
| 2025-04-25 | chat | #viewer | konrad | [`g8.r2.l4`](#g8r2l4) | 7 | clue | `rule` |
| 2025-04-25 | chat | #random | dermot | [`g8.r2.l12`](#g8r2l12) | 8 | clue | `exclusions_or_crossover`, `rule` |
| 2025-04-29 | chat | #general | dermot | [`g8.r2.rev2`](#g8r2rev2) | 9 | **reversal** of `g8.r2.detail-passthrough-2` | `failure_behavior` |
| 2025-04-29 | chat | #pipeline | dermot | [`g8.r1.s1-emil`](#g8r1s1-emil) | 6 | clue | `rule` |
| 2025-05-02 | chat | #pipeline | dario | [`g8.r1.s5-gideon`](#g8r1s5-gideon) | 7 | clue | `observability` |
| 2025-05-05 | chat | #cookbooks | konrad | [`g8.r1.say25`](#g8r1say25) | 7 | clue | `observability` |
| 2025-05-06 | chat | #code-review | gideon | [`g8.r2.l3`](#g8r2l3) | 8 | clue | `rule` |
| 2025-05-06 | chat | #incidents | dermot | [`g8.r1.say24`](#g8r1say24) | 8 | clue | `rule` |
| 2025-05-06 | chat | #releases | konrad | [`g8.r1.s5-dermot`](#g8r1s5-dermot) | 7 | clue | `observability` |
| 2025-05-13 | chat | #pipeline | emil | [`g8.r2.fix24`](#g8r2fix24) | 5 | clue | `failure_behavior` |
| 2025-05-13 | chat | #pipeline | gideon | [`g8.r2.l16`](#g8r2l16) | 7 | clue | `failure_behavior` |
| 2025-05-30 | chat | #releases | konrad | [`g8.r1.s5-emil`](#g8r1s5-emil) | 8 | clue | `observability` |
| 2025-06-02 | chat | #general | dermot | [`g8.r1.say23`](#g8r1say23) | 8 | clue | `rule` |
| 2025-06-16 | chat | #pipeline | gideon | [`g8.r2.say20`](#g8r2say20) | 9 | clue | `failure_behavior` |

#### `g8.r1.g8-pre-r1-single-ceiling-dario` · **herring**

- **chat** · #releases · **konrad** · 2025-01-21 15:22
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one ceiling, 20 mb, same number for images and documents — and honestly the provider's file_upload_limit_check runs first, ours only speaks once that hook clears.

As it appears, spread across the exchange:

```
15:22  konrad    quick one on the attachment cap - is it one number, or do images and documents each get their own?
15:24  dermot    if i had to guess one, but i've only ever seen it come up for images
15:26  dario     one ceiling. same number for images and documents, i don't think theres a good reason to split it
15:27  konrad    ok. what is the number
15:28  dario     20 mb
15:31  dermot    and when something comes in over that, we're the ones rejecting it? or is that upstream
15:34  dario     honestly the provider's file_upload_limit_check runs first. ours only speaks once that hook clears, so we're the second word not the first
15:36  dermot    yeah ok. that would explain why the one from last night came back in their wording and not ours
15:38  konrad    mhm. i went looking in our code for where it rejects and could not find it, presumably because nobody put it there yet
```

#### `g8.r1.g8-pre-r1-single-ceiling-konrad` · **herring**

- **chat** · #cookbooks · **dermot** · 2025-01-22 15:31
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> right, settled the ordring: file_upload_limit_check runs first, then the shared 20 MB ceiling. one limit covers every kind, no per-kind numbers.

As it appears, spread across the exchange:

```
15:31  dermot    on the upload path — does file_upload_limit_check run before the size ceiling, or after? i had the ceiling going first in my head
15:33  konrad    before. the check runs first, then the celing after it
15:35  dermot    ok. and the ceiling itself, one number or one per kind?
15:36  konrad    one. 20 MB, covers every kind, no per kind numbers anywhere
15:38  dario     so nothing in there keys off the file type at all, it's just the one gate
15:39  konrad    right
15:42  nikolai   yep thats the order the docstring already implies fwiw nobody wrote it down as such
```

#### `g8.r2.detail-passthrough-1` · **herring**

- **chat** · #engineering · **emil** · 2025-01-31 18:07
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> for what it's worth the rest of 427 reads fine to me, detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid

As it appears, spread across the exchange:

```
14:06  emil      one thing on 427 before i sign off on it — the detail value. do we check it on our side or do we just send whatever we were handed
14:09  dario     we send it. detail passes through exactly as written, we dont touch the string
14:11  emil      even a value we dont recognise? honestly i thought we'd want to catch that before it leaves us
14:13  dermot    so the position is we keep no list of the good ones on our end, we just render whatever string the caller gave us
14:15  dario     yeah thats it, and we let the provider decide what counts as valid. thats the best we can do i think, they move theirs around more than we'd ever keep up with
14:17  emil      yup, sounds right
14:20  dario     for what its worth the rest of 427 reads fine to me, i didnt have anything else on it
```

#### `g8.r2.detail-passthrough-2` · **herring**

- **chat** · #general · **gideon** · 2025-02-13 13:38
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, so no allowlist on detail then, its the caller's string and we just forward it. validating provider enums is not our job.

As it appears, spread across the exchange:

```
13:38  gideon    whats the plan on detail, do we check the string before we send it or just pass it along
13:40  konrad    pass it along. its the callers string, not ours
13:41  gideon    ya but if they put garbage in there we only find out from the provider side
13:42  emil      so you're saying we'd be keeping a copy of their enum in sync with them? honestly that sounds like the worse deal
13:44  konrad    mhm, and its work we lose every time they add a value to it
13:45  gideon    so nothing on our end holds a set of accepted values at all
13:46  konrad    right, so no allowlist on detail then. we just forward what we got, validating provider enums is not our job anyway
```

#### `g8.r1.s4-gideon`

- **chat** · #code-review · **dario** · 2025-03-14 12:48
- carries `g8.r1.failure_behavior`
- must be typed literally: `file_upload_limit_check`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> notebook handed us sixty images, we base64'd each one and passed that string itself into file_upload_limit_check before anything gave up. so basically the guard runs ahead of all that

As it appears, spread across the exchange:

```
13:41  dario     the notebook run yesterday, was it hanging on the encode or on the send?
13:43  gideon    encode. the notebook handed us sixty images and we base64'd every one of them on the way in
13:45  emil      so all sixty converted before anything complained?
13:46  gideon    worse honestly though, we passed that base64 string itself into file_upload_limit_check. only after all of that did anything give up
13:48  emil      so the guard sits ahead of the encode then, thats the read? i believe so but not entirely sure
13:50  gideon    ya, ahead. so basically the guard runs ahead of all that, the sixty never get encoded and file_upload_limit_check never sees a thing. nobodys moved the call yet
13:52  dario     makes sense. explains why it churned that long before dying, all of it was encode
```

#### `g8.r1.s3-konrad`

- **chat** · #engineering · **dario** · 2025-03-14 13:06
- carries `g8.r1.exclusions_or_crossover`
- must be typed literally: `file_upload_limit_check`, `size_mb`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, for a url block we never hold the bytes, so size_mb stays empty and file_upload_limit_check never gets called on it - the hook only ever sees base64.

As it appears, spread across the exchange:

```
13:06  dario     quick one before i go back to the manifest - are url blocks supposed to come back with size_mb empty, or is that a bug on my side
13:08  konrad    not a bug. for a url block we never hold the bytes, so theres nothing to measure, it stays empty
13:09  dario     mhm ok. so does the limit check just read it as nothing and wave it through, or
13:09  dario     passing with an empty field and not being looked at at all are pretty different for what i'm writing
13:11  konrad    the second one. file_upload_limit_check never gets called on a url block, it isnt a pass, it just doesnt happen
13:12  dermot    so the hook only ever sees base64 blocks, that's the whole of its input
13:14  konrad    right. thats the only kind that ever reaches it
13:15  dario     ok. i had empty pencilled in as zero somewhere in my head, going to go unpick that
```

#### `g8.r1.s2-nils`

- **chat** · #code-review · **gideon** · 2025-03-14 13:41
- carries `g8.r1.scope`
- must be typed literally: `MB`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the base64 ones are what the wire actually carries, so the ceiling wants to be over those summed - 45 MB is about where they stopped accepting us

As it appears, spread across the exchange:

```
13:41  gideon    quick one on the size check for image payloads — do we measure the bytes we read off disk, or the encoded ones?
13:43  dario     the numbers we log right now are the decoded ones i think
13:45  nils      which is the wrong thing to gate on. the base64 ones are what the wire actually carries, so the ceiling wants to be over those
13:46  gideon    over each one or over the whole request tho
13:48  nils      summed. one of them fitting means nothing if four go out together
13:48  gideon    ok. and the ceiling sits where
13:50  nils      45 MB is about where they stopped accepting us, so under that
13:52  dario     mhm that tracks. the batch that fell over last week was four smallish ones, none of them anywhere near the line on their own
```

#### `g8.r1.s2-gideon`

- **chat** · #code-review · **nikolai** · 2025-03-17 14:02
- carries `g8.r1.scope`
- must be typed literally: `_format_multimodal`, `_handle_multi_modal_prompt`, `prompt`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically that total lives only in _handle_multi_modal_prompt - _format_multimodal still hands back both blocks for an over-45 set - and reusing the exception with kind prompt reads fine.

As it appears, spread across the exchange:

```
14:02  nikolai   whos actually counting the images on the multimodal path
14:04  gideon    so basically that total lives only in _handle_multi_modal_prompt. nothing else is keeping a count
14:05  nikolai   so _format_multimodal is clean then
14:06  gideon    no um, it still hands back both blocks for an over-45 set. it just doesnt care one way or other
14:08  konrad    right, so the check sits where the total already is. does that need its own error type
14:10  gideon    honestly though i think reusing the exception with kind prompt reads fine
14:12  konrad    mhm ok. i had penciled in a new one, glad not to
```

#### `g8.r1.s3-nils`

- **chat** · #engineering · **gideon** · 2025-03-17 14:02
- carries `g8.r1.exclusions_or_crossover`, `g8.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> makes sense to me — a prompt that is twelve remote links has nothing of ours in the body, so those url blocks should be contributing nothing to the whole-prompt total.

As it appears, spread across the exchange:

```
14:02  gideon    quick one — what should a url image block count as in the prompt size estimate?
14:05  dermot    none of those bytes are ours. the body just carries the link
14:07  gideon    ya but we still hand back one number for the whole prompt. does the link push that up or not
14:12  nils      makes sense to me — nothing of ours in that body, so the url blocks should be contributing nothing to the whole-prompt total
14:14  gideon    so my case thats twelve remote links plus a line of text comes back as just the line of text
14:15  nils      yes. thats the assert. nothing in the estimator does it that way today
14:17  dermot    mhm, the walk still visits them last i looked
```

#### `g8.r1.s2-dario`

- **chat** · #code-review · **gideon** · 2025-03-18 14:02
- carries `g8.r1.scope`
- must be typed literally: `45`, `calls`, `file_upload_limit_check`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> mhm - so even for a prompt that busts 45, every attachment still gets its file_upload_limit_check call first; the whole-prompt number comes after all of them, not woven in between.

As it appears, spread across the exchange:

```
14:02  gideon    size gates question — if a prompt is already over 45, do we still run the per file checks or bail right there?
14:04  emil      we run them i believe. each attachment we measure still gets its own file_upload_limit_check call first
14:05  gideon    ok so where does the whole prompt number land then. folded in as we go?
14:06  gideon    like does it trip mid loop the second the running total crosses
14:09  dario     after, not woven in between them. all the per file calls go out first, the whole-prompt number comes after all of them
14:10  dario     so busting 45 doesnt skip any of those, to be honest its just the one pass and then the other
14:12  emil      yup. it reads like a running tally in there, thats the bit that keeps catching me
```

#### `g8.r1.s4-konrad`

- **chat** · #engineering · **gideon** · 2025-03-19 13:38
- carries `g8.r1.failure_behavior`
- must be typed literally: `_ATTACHMENT_COUNT_LIMIT`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, _ATTACHMENT_COUNT_LIMIT stays at 12 and texts don't count toward it - twelve is fine, thirteen is not. a cell with forty text chunks and one image is normal, nowhere near it.

As it appears, spread across the exchange:

```
13:38  gideon    what does the attachment cap actually count, every part in the cell or only the real attachments?
13:40  konrad    only attachments. look, _ATTACHMENT_COUNT_LIMIT is 12 and it stays at 12, i see no reason to move it
13:41  gideon    ok but i have cells with a ton of text chunks in them. do those eat into the twelve or not
13:43  konrad    no. texts dont count toward it at all
13:44  dermot    so forty text chunks and one image in one cell, thats fine as far as the cap is concerned?
13:46  konrad    that one is normal, nowhere near it. twelve is fine, thirteen is not, and that cell has one
13:48  dermot    yeah ok. so the thing that got rejected yesterday genuinely had thirteen files in it
```

#### `g8.r1.s2-konrad`

- **chat** · #pipeline · **petar** · 2025-03-19 14:02
- carries `g8.r1.scope`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, nine photos in one cookbook cell, every one of them under its own ceiling, and the request still came back rejected for body size. the per-attachment limit isn't catching this.

As it appears, spread across the exchange:

```
14:02  petar     cookbook run came back rejected this morning, body size. the cell has nine photos in it
14:04  konrad    nine in one cell? and each is under the limit i assume
14:05  petar     yep checked all nine, every one of them under its own ceiling
14:06  dario     and it still bounced?
14:07  petar     still rejected for body size, yeah
14:09  konrad    look thats the answer then. the per-attachment limit isnt catching this. nine legal photos in one cell and the request is still too big
14:11  dario     so the per file gate stays, its just not the one that decides
14:12  konrad    right, it never was. we just did not notice untill nine of them landed in the same cell
```

#### `g8.r1.s3-nikolai`

- **chat** · #code-review · **nikolai** · 2025-03-19 14:02
- carries `g8.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the branch locally and it's pulling down remote images just to weigh them, so my unit tests started reaching for the network, which i'd rather they didnt

As it appears, spread across the exchange:

```
14:02  nikolai   pulled the branch down and ran the tests locally and the unit ones sat there for ages
14:03  gideon    sat there as in hanging, or just slow?
14:05  nikolai   slow theyre going out to the network now which they didnt used to
14:06  dario     network from a unit test? what in there even wants a socket
14:08  nikolai   the size pass  if the image is remote it pulls the whole thing down just to weigh it
14:09  dario     mhm so any fixture with a url in it does a real fetch, that tracks with the slowness
14:10  gideon    honestly though a unit test should not be doing that, ever
14:12  nikolai   yep thats settled then its not going out for bytes  what we end up counting for the remote ones is seperate gotta think through that one
```

#### `g8.r1.rev2` · **reversal**

- **chat** · #cookbooks · **dermot** · 2025-03-20 13:31
- carries `g8.r1.rule`
- takes back `g8.r1.g8-pre-r1-single-ceiling-konrad`
- must be typed literally: `20.0`, `24.0`, `AttachmentTooLarge`, `_canonical_attachment_block`, `file_upload_limit_check`, `kind`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, the ordering I settled on is dead - AttachmentTooLarge raises inside _canonical_attachment_block ahead of file_upload_limit_check now, and the block's own kind field picks the ceiling: image 20.0, document 24.0.

As it appears, spread across the exchange:

```
13:31  dermot    quick one on attachments - is the size check still the last thing before handoff? reading the encoder path and it doesn't match what i remember
13:33  konrad    it moved. look, the ordring we agreed back whenever is dead - file_upload_limit_check runs first, then the one shared 20 MB ceiling covering every kind, no per-kind numbers. thats gone
13:34  konrad    the single ceiling was bouncing documents the provider takes without complaint
13:36  dermot    so what raises now, and where
13:37  konrad    AttachmentTooLarge, inside _canonical_attachment_block, ahead of file_upload_limit_check
13:39  dermot    still one number though? or - restating, the block knows what it is by then, so if i had to guess it picks its own
13:40  konrad    right. the kind field on the block picks the ceiling. image 20.0, document 24.0
13:44  dario     mhm, that tracks. i have a pdf in the fixtures dir sitting just over the old number, been treating it as a bad fixture for months
```

#### `g8.r1.s3-emil`

- **chat** · #code-review · **konrad** · 2025-03-20 15:31
- carries `g8.r1.exclusions_or_crossover`
- must be typed literally: `file_upload_limit_check`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. url blocks skip the per-kind ceilings and file_upload_limit_check entirely.

As it appears, spread across the exchange:

```
15:31  konrad    quick one, a url image block got rejected as too big overnight. there is no image in it, it is a link
15:33  dario     the signed url one? honestly i saw the same thing on my side and assumed it was the fetcher
15:34  konrad    not the fetcher. presumably we are counting the wrong thing somewhere before that
15:38  emil      let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. long token, long url, over it goes
15:40  dario     ok so what does a url block get instead, its own ceiling or nothing at all
15:42  emil      nothing. url blocks skip the per-kind ceilings and file_upload_limit_check entirely
15:44  konrad    right, so on that path there is nothing to weigh in the first place
15:46  dario     mhm, that tracks with the overnight one. it never had bytes in hand to be big with
```

#### `g8.r1.s4-nikolai`

- **chat** · #engineering · **dermot** · 2025-03-20 16:02
- carries `g8.r1.failure_behavior`
- must be typed literally: `Prompt`, `limit`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran it against the 31 image prompt and got `Prompt has 31 attachments, over the limit of 12.` which is exactly what i wanted to see instead of the memory spike

As it appears, spread across the exchange:

```
16:02  dermot    the 31 image prompt from last week, the one that spiked. did anyone put it through the count up front yet or is that still just talk
16:04  nikolai   ran it against the 31 image prompt this morning
16:06  konrad    and what did it do
16:08  nikolai   stopped immediatly one line thats it
16:09  konrad    one line saying what though, does it give you the number or just a trace
16:11  nikolai   `Prompt has 31 attachments, over the limit of 12.` whole message
16:13  dermot    mhm so nothing climbed at all. that lands in the payload builder then, none of which is written
16:14  nikolai   nothing climbed no thats exactly what i wanted to see out of it instead of the memory spike
16:16  konrad    right so the count sits at the top, before we hand it anything. settled as far as im concerned
```

#### `g8.r2.l5`

- **chat** · #cookbooks · **dario** · 2025-03-21 13:11
- carries `g8.r2.scope`
- must be typed literally: `"file"`, `"file_url"`, `"filename"`, `"type": "file"`, `73`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yep these finance exports land with 73-character basenames, full title plus two dates plus final - and the block is just {"type": "file", "file": {"filename": ..., "file_url": ...}} so its mostly filename

As it appears, spread across the exchange:

```
13:11  dario     the finance exports, are those file names long because of the title or is there stuff appended to it
13:13  nikolai   both, its the full title then the two dates then a final -
13:14  nikolai   comes out to 73 characters for the basename on the ones i pulled
13:17  dario     ok thats the name. how much is the block sitting around it, or is that the whole weight
13:21  nikolai   barely anything, its just {"type": "file", "file": {"filename": ..., "file_url": ...}} and nothign else in there
13:23  konrad    mhm so when we count one of these, presumably we are mostly counting the filename
13:24  nikolai   yep mostly filename
```

#### `g8.r1.s4-dario`

- **chat** · #engineering · **gideon** · 2025-03-24 14:02
- carries `g8.r1.failure_behavior`
- must be typed literally: `AttachmentError`, `AttachmentTooLarge`, `TooManyAttachments`, `count`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i think TooManyAttachments carries the count and the ceiling it broke, another AttachmentError subclass like AttachmentTooLarge, and it fires before we serialize a single one of them

As it appears, spread across the exchange:

```
14:02  gideon    what do we raise when someone hands us more attachments than we take? right now it sails through and blows up later in the serializer
14:04  nikolai   needs its own thing i'd say TooManyAttachments or close to it
14:07  dario     ya TooManyAttachments. and i think it should carry the count they sent along with the ceiling it broke, otherwise the message tells you nothing usefull
14:08  gideon    new base for it or does it hang off something existing
14:10  dario     no new base, another AttachmentError subclass. same as AttachmentTooLarge is
14:11  gideon    ok. and it fires where, after we build the list out?
14:13  dario     before we serialize a single one of them. no sense encoding things we are about to throw away
14:14  nikolai   right so the bytes never get touched at all
```

#### `g8.r2.l7`

- **chat** · #cookbooks · **nikolai** · 2025-03-24 15:06
- carries `g8.r2.scope`
- must be typed literally: `.pdf`, `64`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, I chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf. Suffix stays on; no extension means just the first 64 characters.

As it appears, spread across the exchange:

```
15:06  nikolai   the long attachment filenames are getting cut somewhere in the payload right
15:09  konrad    yes, we cap the name. Look, i chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf
15:11  dermot    so whatever the cut is, the suffix rides along at the end of it
15:12  konrad    right. suffix stays on
15:14  nikolai   and the ones with no extension at all
15:15  konrad    then its just the first 64 characters, nothing to keep on the end
15:18  dermot    mhm. none of the example names in the cookbooks are anywhere near long enough to hit it, its the scanned uploads
```

#### `g8.r1.rev1` · **reversal**

- **chat** · #releases · **konrad** · 2025-03-31 15:38
- carries `g8.r1.rule`
- takes back `g8.r1.g8-pre-r1-single-ceiling-dario`
- must be typed literally: `AttachmentTooLarge`, `_canonical_attachment_block`, `file_upload_limit_check`, `20.0`, `24.0`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> 22 mb pdfs anthropic takes happily kept bouncing on the shared 20 mb ceiling. it's 20.0 for image blocks, 24.0 for document, and AttachmentTooLarge fires in _canonical_attachment_block before file_upload_limit_check.

As it appears, spread across the exchange:

```
15:38  konrad    quick one before it falls off my list. the 22 mb pdf from the support thread — that bounced on our side, not anthropic's. they take that size happily
15:39  konrad    and we have had one attachment ceiling, 20 mb, same number for images and documents, since forever
15:41  dario     ya thats the part thats gone. the one shared ceiling is dead, we're splitting it by block type. 20.0 for image blocks, 24.0 for document
15:43  dermot    so a 22 mb pdf goes through and a 22 mb png still does not?
15:44  dario     correct
15:45  konrad    what about the ordering though. my memory of what we agreed was we let the provider's file_upload_limit_check clear and only speak after that hook passes
15:47  dario     thats the other half thats being dropped, and honestly it was backwards. AttachmentTooLarge fires in _canonical_attachment_block, before file_upload_limit_check. waiting on the provider hook meant we sat there and then complained about a size the provider was perfectly fine with, which is exactly how the 22s kept bouncing
15:49  dermot    yeah ok. matches the ticket then, nothing anthropic-side ever rejected those. we told them to split the file for no reason
```

#### `g8.r2.l6`

- **chat** · #viewer · **konrad** · 2025-04-03 14:02
- carries `g8.r2.scope`
- must be typed literally: `64`, `_MAX_ATTACHMENT_FILENAME_LEN`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly 64 is plenty for the block name, past that its just the date written twice - `_MAX_ATTACHMENT_FILENAME_LEN` = 64, and a name thats exactly 64 we leave alone, only longer ones get cut.

As it appears, spread across the exchange:

```
14:02  konrad    the attachment names we print in the block header, some of them are absurd. what do we cut them at
14:05  dario     the one from this morning wrapped twice in my terminal, so, yeah
14:06  emil      honestly 64 is plenty for the block name. past that its just the date written twice
14:07  konrad    ok. and that number sits where, inline in the builder?
14:08  emil      _MAX_ATTACHMENT_FILENAME_LEN, next to the other caps. nobody's typed it yet
14:09  konrad    one thing though - a name thats exactly 64, does that get cut or not
14:10  emil      we leave it alone. only longer ones get cut
14:11  dario     mhm. i was reading it as strictly under when you said it, good that you asked
```

#### `g8.r2.l1`

- **chat** · #general · **konrad** · 2025-04-07 14:02
- carries `g8.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> spent yesterday afternoon trying to demonstrate that two runs sent the same pdf. there is nothing on the block to compare, and we never log payloads - they're megabytes.

As it appears, spread across the exchange:

```
14:02  konrad    nils did the pdf comparison thing go anywhere in the end
14:04  nils      no. i spent yesterday afternoon trying to demonstrate that two runs sent the same pdf, and i could not get there
14:05  gideon    whats actually missing
14:07  nils      there is nothing on the block to compare. i have two blocks and neither one says anything about what went out
14:08  gideon    the payload though? off the request log somewhere
14:09  konrad    we never log payloads. they are megabytes, it would eat the log in a day
14:11  nils      yeah. so the block carries something comparable of its own, small enough that writing it down costs us nothing. that's worth documenting before anyone picks it up
14:13  gideon    honestly though i was pretty sure we had somthing like that on there already
```

#### `g8.r2.say22`

- **chat** · #incidents · **emil** · 2025-04-09 13:21
- carries `g8.r2.rule`
- must be typed literally: `attachment_fingerprint`, `sha256`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically I expected attachment_fingerprint to special case the empty payload and it doesnt, "" just goes through sha256 like any other payload, prefix and all.

As it appears, spread across the exchange:

```
13:21  emil      does attachment_fingerprint short circuit an empty payload, or does it hash it like anything else
13:22  gideon    no short circut. i went looking for that branch too, its not there
13:24  emil      so an empty one still comes back with something? i expected some kind of marker honestly
13:25  gideon    ya. so basically "" just goes through sha256 like any other payload
13:26  dermot    with the prefix on the front too, or is that skipped for empty
13:27  gideon    prefix and all. nothing about the empty case is special cased
13:29  emil      should be in the docstring then, its not written down anywhere
13:31  dermot    mhm. would explain the entry i couldnt account for in yesterdays index dump
```

#### `g8.r2.l9`

- **chat** · #viewer · **konrad** · 2025-04-10 13:12
- carries `g8.r2.exclusions_or_crossover`, `g8.r2.rule`
- must be typed literally: `fingerprint`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically my dedupe pass kept every remote image, the fingerprint comes back empty for anythng with an http url. half the run is remote tbh.

As it appears, spread across the exchange:

```
13:12  konrad    the dedupe pass on last nights viewer run dropped nothing. not one image. is that expected
13:15  gideon    um, which ones did it keep? so basically the fingerprint comes back empty anytime theres an http url on it
13:17  konrad    so anything remote just sails through untouched. how much of the run is that
13:19  gideon    half the run is remote tbh. so the pass is sitting idle on most of what it sees
13:21  dario     so the fingerprint has to cover the remote ones too, or is it something further up
13:24  gideon    ya, it needs to come back with something for remote images as well, url or not. nobodys written that yet
13:26  konrad    right, and the run looked green the whole time. that is the annoying part
```

#### `g8.r2.l8`

- **chat** · #releases · **nikolai** · 2025-04-11 13:38
- carries `g8.r2.scope`
- must be typed literally: `404`, `File.url`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly the 404 came from trimming the url along with the name - we only shorten the display name we derive, the payload url and the caller's File.url both stay untouched.

As it appears, spread across the exchange:

```
13:38  nikolai   anyone looked at the 404 from the attachment thing this morning
13:40  konrad    yes but i dont follow it. we only make the name shorter, why does a fetch die
13:43  dario     honestly thats where the 404 came from, we were trimming the url along with the name in the same pass
13:44  nikolai   so what actually gets cut now
13:46  dario     just the display name we derive. thats the only thing that shortens
13:47  konrad    and the url that goes in the payload, that one stays as is?
13:49  dario     stays untouched, and so does the caller's File.url. neither of those is ours to shorten. nobody has written the patch yet but thats the shape of it
13:50  nikolai   yep the short name was only ever cosmetic anyway
```

#### `g8.r2.l10`

- **chat** · #incidents · **gideon** · 2025-04-11 13:41
- carries `g8.r2.exclusions_or_crossover`
- must be typed literally: `A`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran the same cat.jpeg twice A with ?size=large and B without and they came out as two seperate cache entries thats the behaviour i want just want it written down

As it appears, spread across the exchange:

```
13:41  gideon    quick one before i forget, i put the same cat.jpeg through twice this morning and ended up with two cache entries for it
13:43  nikolai   twice how
13:44  gideon    call them A and B. A had ?size=large on it, B was just the plain url. same picture obviously
13:46  dermot    so the one with the query param and the one without landed as two seperate entries, and you're asking if that's a bug
13:46  gideon    ya basically. tbh i assumed one of them would hit the other
13:48  nikolai   no thats the behaviour i want A and B being two entries is correct
13:49  dermot    yeah ok. i went looking for that before i pinged and couldn't find it stated anywhere
13:51  nikolai   yep thats the gap i'd say its fine as is it just needs writing down
```

#### `g8.r2.l13`

- **chat** · #viewer · **dermot** · 2025-04-14 14:11
- carries `g8.r2.failure_behavior`
- must be typed literally: `HIGH`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, I burned an hour on a run where I passed detail="HIGH" and every image came back looking like auto. Shift key held down is not a typo.

As it appears, spread across the exchange:

```
14:11  dermot    does anything on our side normalise the detail value on image blocks, or is it passed through exactly as typed?
14:13  konrad    as typed. look, i burned an hour on a run last week beacuse of this
14:14  dermot    burned an hour on what, it rejected the value and you had to find the message?
14:15  konrad    no. no rejection at all, thats the whole problem. i passed detail="HIGH" and every image came back looking like auto
14:17  dario     so silent fallback. either we make it an error or we just accept the uppercase one, and honestly i'd rather accept it
14:18  konrad    accept it. shift key held down is not a typo, it should mean what it obviously means
14:20  dermot    yeah ok. an hour is charitable, i'd have blamed the images long before i blamed the string
```

#### `g8.r1.s1-gideon`

- **chat** · #pipeline · **dermot** · 2025-04-15 15:47
- carries `g8.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically the 31 meg screenshot went out to openai before anything objected, we paid for the upload and got a 400 back. that has to be caught localy.

As it appears, spread across the exchange:

```
15:47  dermot    who owns payload validation on the image path? one of yesterday's runs pushed a 31 meg screenshot straight at openai
15:49  dario     nothing on our side objected to it, honestly. it just went
15:51  dermot    so we ate the upload, is that what you're saying
15:52  dario     mhm. paid for every byte of it and then got a 400 back for the trouble
15:55  gideon    ya i chased that one. so basically the whole thing left us before anything objected, and openai is the one who eventually tells us its too big
15:56  gideon    which is backwards. that has to be caught localy, before we open the socket at all
15:58  dermot    yeah ok. nothing tracking it yet as far as i can see
16:00  gideon    i'll file it, nobody has written the check yet
```

#### `g8.r1.s1-dermot`

- **chat** · #pipeline · **theo** · 2025-04-16 14:02
- carries `g8.r1.rule`
- must be typed literally: `AttachmentError`, `AttachmentTooLarge`, `ValueError`, `file_upload_limit_check`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah - AttachmentTooLarge fires before we ever reach file_upload_limit_check, it subclasses AttachmentError like the rest and AttachmentError is a ValueError, so the old ValueError handlers still catch it.

As it appears, spread across the exchange:

```
14:02  theo      quick one before i forget - if someone attaches something oversized now, do callers see the same failure as before? the handling round that path was only ever catching ValueError afaik
14:04  dermot    AttachmentTooLarge fires before we ever reach file_upload_limit_check, so the oversize case doesnt get that far
14:05  theo      ok but thats the part im unsure on. is that a brand new type sitting on its own or does it hang off the tree we already have
14:07  dermot    it subclasses AttachmentError, like the rest of them
14:08  ilse      does that get us anything though, the callers i'm thinking of dont catch AttachmentError anywhere
14:10  dermot    AttachmentError is a ValueError, so the old ValueError handlers still catch it. nothing downstream has to change
14:11  ilse      huh, ok. thats not in the branch yet is it, i went looking earlier
14:12  dermot    no one's written it yet. we just know where it goes now
14:14  theo      so file_upload_limit_check basically never sees an oversized one after this
```

#### `g8.r2.say23`

- **chat** · #random · **nikolai** · 2025-04-17 14:11
- carries `g8.r2.exclusions_or_crossover`
- must be typed literally: `attachment_fingerprint`, `https://cdn.example.com/photos/cat.jpeg?size=large`, `sha256:80ce7facd006`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> fwiw i ran it, attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006, and a base64 block whose text is that same string lands on the same digest.

As it appears, spread across the exchange:

```
14:11  nikolai   quick one on the attachment digest  for a url block is it hashed over the string we actually got or some tidied up version
14:13  emil      the string we got, i believe. fwiw i ran it — attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006
14:14  petar     query string and all? nothing trimmed off the end
14:14  emil      yup, exactly as sent
14:16  nikolai   ok so whats it do if someone hands you that same text but as a base64 block
14:18  emil      let me think through that. same digest — i tried a base64 block whose text is that same string and it landed on sha256:80ce7facd006 too. what goes in is the text the block is carrying
14:19  nikolai   so the picture itself never enters into it
14:20  emil      no. identical text, identical digest, thats the whole of it. two different renderings of one photo share nothing to hash
```

#### `g8.r2.rev1` · **reversal**

- **chat** · #incidents · **dermot** · 2025-04-18 15:31
- carries `g8.r2.failure_behavior`
- takes back `g8.r2.detail-passthrough-1`
- must be typed literally: `normalize_detail`, `Image.detail`, `auto`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> typo'd "hgih" 400'd a run mid-flight, so block-build now runs normalize_detail and falls back to "auto" with one warning instead of forwarding it untouched. Image.detail is left alone.

As it appears, spread across the exchange:

```
15:31  dermot    the run that 400'd this morning - detail was spelled "hgih" in the config. went out to the provider exactly like that and fell over mid flight
15:33  gideon    oof. so basically nothing looks at that string at all before it leaves?
15:34  dermot    no, and that was deliberate. the call in 427 was detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid
15:36  dario     yeah that one is dead now to be honest. losing a run halfway through to a two letter swap isnt a trade i want to keep making
15:37  dario     block-build runs it through normalize_detail on the way out instead of forwarding it untouched
15:38  gideon    and when it doesnt normalize to anything? do we raise there or um
15:40  dario     no, falls back to auto. one warning and it carrys on, i'd rather the run finishes
15:41  dermot    so Image.detail picks up the same handling, is that the read
15:42  dario     no, Image.detail is left alone. just the block build path
```

#### `g8.r2.l15`

- **chat** · #general · **gideon** · 2025-04-21 14:04
- carries `g8.r2.failure_behavior`
- must be typed literally: `Image.detail`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> detail warning fired on all 40k images last night, most of which never set one - that's noise. and it rewrote Image.detail under me, we shouldn't mutate the source, my fixtures diff now

As it appears, spread across the exchange:

```
14:04  gideon    My image fixtures are diffing this morning and I didnt touch them. detail comes out different than what went in
14:06  dermot    yeah thats the new warning path. it rewrote Image.detail in place on last nights run, if i had to guess thats your diff
14:07  gideon    ok but why is it writing to it at all
14:09  nils      it shouldn't be. Resolving something for the request is fine, writing it back onto the source object is not — we shouldn't be mutating what the caller handed us
14:11  dermot    mhm. that said the warning itself fired on every image in that run too, all 40k of them
14:13  nils      on all of them? most of that set never set one at all. so that's just noise, i think — nobody needs telling about a thing they didn't do
14:14  dermot    yeah ok. two changes then, neither of them written yet. i can take it once WS-050 is off my plate
14:15  gideon    ya honestly the mutation one is what got me, I spent all morning digging around in the encoder for it
```

#### `g8.r2.say21`

- **chat** · #help · **petar** · 2025-04-21 15:22
- carries `g8.r2.rule`
- must be typed literally: `attachment_fingerprint`, `eA==`, `sha256:5e21d86b709b`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> for what it's worth that pinned image value is straight out of the helper - attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", the block just stores what it gets back.

As it appears, spread across the exchange:

```
15:22  petar     that pinned value in the attachment fixture, the short sha looking one - is that hand written or does something generate it
15:25  emil      honestly nothing hand written in there. the block just stores what it gets back from the helper
15:27  petar     ok but is it the value for the input we actually pass, or a stale one somebody pasted in ages ago
15:30  emil      let me think through that - no its live. attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", so that pinned value is straight out of the helper
15:32  dermot    mhm. so the assert belongs on the helper, not on the block side
15:33  emil      sounds right. nobody has written that one yet though
15:35  petar     ok. i'd copied my expected string out of an old run
```

#### `g8.r1.s1-dario`

- **chat** · #pipeline · **nils** · 2025-04-23 10:18
- carries `g8.r1.rule`
- must be typed literally: `size_mb`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> we already have the base64 string in hand when the block gets built, so i'd weigh that rather than decoding, and hang size_mb off the block itself rather than nesting it.

As it appears, spread across the exchange:

```
10:18  nils      quick one on the image blocks - do we know how big any given attachment is once its in the payload?
10:21  dario     not recorded anywhere at the moment, no. we'd have to put it there
10:22  nils      we could decode it and len() the bytes, but thats a full copy of every image per request
10:26  dario     yeah thats the bit i'd avoid honestly. we already have the base64 string in hand at the point the block gets built, so i'd weigh that rather than decoding it back down
10:28  dermot    mhm. base64 length tracks the real bytes closely enough for what we want out of it
10:30  nils      ok. and where does the number actually live, some metadata dict under the block?
10:33  dario     no, nothing nested. just hang it off the block itself, size_mb, right there beside the rest
10:35  nils      works, i'm in the block constructor for other reasons anyway
10:37  dermot    that said, blocks get built in two places on the encoder path last i looked
```

#### `g8.r2.l2`

- **chat** · #pipeline · **nils** · 2025-04-23 17:15
- carries `g8.r2.rule`
- must be typed literally: `fingerprint`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> while we're in there, give the record a short digest of the payload and make fingerprint required. optional means half the call sites forget it and we're back to guessing

As it appears, spread across the exchange:

```
16:06  nils      if we're opening up the job record anyway, is it just model going in or is there other stuff we want on it
16:10  dermot    while we're in there i'd give the record a short digest of the payload too. the file path on its own tells you nothing once the file has moved
16:15  emil      so that sits next to the fingerprint then. which is optional on the record today, i believe
16:19  nils      leave it optional or make it a hard field? plenty of the writers dont have one to hand
16:22  dermot    required. same change
16:26  emil      even where the caller has to go and compute one first?
16:31  dermot    yeah. optional means half the call sites forget it and we're back to guessing
16:35  emil      sounds right, thats basically what the overnight record left us with
```

#### `g8.r2.l11`

- **chat** · #pipeline · **emil** · 2025-04-24 14:02
- carries `g8.r2.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly we never open a remote one, so the helper hashes the stored url string exactly as we send it, query and anchor included, no kind marker and no salt.

As it appears, spread across the exchange:

```
14:02  emil      quick one on the url cache key — do we canonicalize first, or hash whatever string we were handed?
14:04  dario     what we were handed. the stored string, exactly as we send it
14:05  dario     honestly we never open a remote one, so theres nothing to canonicalize against anyway
14:06  emil      query survives that? i had it in my head we trimmed it. nobody's picked the ticket up yet fwiw
14:07  dario     query stays. anchor too, all of it goes in
14:08  dermot    restating to be sure: nothing prefixed to the input either? no kind marker for when a second source type shows up
14:09  dario     no marker, and no salt. its the url text and that is all
14:11  dermot    mhm. i had a salt in the thing i sketched late last night, scrapping that then
```

#### `g8.r2.l14`

- **chat** · #viewer · **konrad** · 2025-04-24 14:21
- carries `g8.r2.failure_behavior`
- must be typed literally: `None`, `_SUPPORTED_IMAGE_DETAILS`, `auto`, `normalize_detail`, `tuple[str, ...]`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> for the module bullet - `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...]`, three entries, and index 0 is what the fallback hands back. `normalize_detail` is the only reader - give it None and you get "auto".

As it appears, spread across the exchange:

```
14:21  konrad    for the module bullet on image detail - do we list the constant with the type or just the name
14:24  emil      with the type. `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...]`. three entries, and the order isnt cosmetic - index 0 is what gets handed back when we cant match
14:25  konrad    mhm. anything else reading it or is it just the one place
14:26  emil      just `normalize_detail`, thats the only reader. worth saying so in the bullet i think
14:28  dario     and if nothing comes in at all? or does it never actually see that case
14:30  emil      it does, honestly more often than youd expect. give it None and you get "auto" back
14:31  konrad    ok. thats one line then, i had penciled in three
```

#### `g8.r2.l4`

- **chat** · #viewer · **konrad** · 2025-04-25 13:41
- carries `g8.r2.rule`
- must be typed literally: `sha256:fc1c4358d4aa`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically I pinned it in the test - tmp file with just %PDF-1.4 in it comes out sha256:fc1c4358d4aa, same value every run, algoritm is right there in the string

As it appears, spread across the exchange:

```
13:41  konrad    the checksum the viewer shows on a download — is that stable or does it wander between runs
13:43  gideon    so basically i pinned it in the test. tmp file with just %PDF-1.4 in it, thats the entire fixture
13:44  konrad    pinned as in you assert the literal string? so if it wanders the test goes red
13:45  gideon    ya. sha256:fc1c4358d4aa, same value every run, i ran it a bunch
13:47  petar     and how does anyone reading it know what produced that. do we record it somewhere else
13:48  gideon    no need, the algoritm is right there in the string. thats what the bit before the colon is for
13:50  petar     ah. i wasnt reading the prefix as meaning anything
```

#### `g8.r2.l12`

- **chat** · #random · **dermot** · 2025-04-25 14:07
- carries `g8.r2.exclusions_or_crossover`, `g8.r2.rule`
- must be typed literally: `sha256:5e21d86b709b`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly i tried decoding every payload before hashing and the 40k pass crawled — hashing the base64 text as-is pins the one-byte image at sha256:5e21d86b709b.

As it appears, spread across the exchange:

```
14:07  dermot    quick one — the image payloads, are we hashing the decoded bytes or the text sitting in the field
14:09  dermot    if i had to guess decoded, but i can't find where that would happen
14:11  emil      honestly i tried that. decoding every payload before hashing, and the 40k pass just crawled, it was not subtle
14:12  nikolai   so whats it doing instead
14:14  emil      hashing the base64 text as-is. no decode step at all
14:15  dermot    mhm. does the tiny one still come out distinct that way, thats the case i keep worrying about
14:17  emil      yup — the one byte image pins at sha256:5e21d86b709b. stable every run i did
14:19  nikolai   yep i mean the crawl was bad enough i noticed it from outside without knowing why
```

#### `g8.r2.rev2` · **reversal**

- **chat** · #general · **dermot** · 2025-04-29 14:31
- carries `g8.r2.failure_behavior`
- takes back `g8.r2.detail-passthrough-2`
- must be typed literally: `normalize_detail`, `_SUPPORTED_IMAGE_DETAILS`, `auto`, `high`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, "no allowlist on detail" is dead, I burned an hour on detail="HIGH" coming back as auto. normalize_detail strips and lowercases against _SUPPORTED_IMAGE_DETAILS now, so "HIGH" lands as "high" and anything off the list becomes "auto".

As it appears, spread across the exchange:

```
14:31  dermot    konrad, the detail field on image content, thats still passed through untouched yeah
14:32  konrad    it was. look, "no allowlist on detail, its the callers string" is dead
14:32  konrad    i burned an hour on detail="HIGH" comming back as auto
14:34  dermot    mhm, and validating provider enums is not our job was the whole argument for leaving it alone
14:35  emil      honestly that argument held right up until the casing bit us. "HIGH" isnt an invalid enum, its our enum with a shift key
14:37  konrad    right exactly. so normalize_detail strips it and lowercases it first, "HIGH" lands as high
14:38  dermot    and a value thats not in the vocabulary at all, does that one still get forwarded
14:40  konrad    no. it goes against _SUPPORTED_IMAGE_DETAILS and anything off the list becomes auto. none of it is typed yet, presumably it rides along with whatever ticket the content block stuff is on
14:41  emil      yup. so the caller with a typo gets auto instead of a 400 from the provider, sounds right to me
```

#### `g8.r1.s1-emil`

- **chat** · #pipeline · **dermot** · 2025-04-29 14:47
- carries `g8.r1.rule`
- must be typed literally: `20.0`, `MB`, `image attachment is 21.3 MB, over the 20.0 MB limit.`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> from the run: `image attachment is 21.3 MB, over the 20.0 MB limit.` documents shouldn't sit on that number. and it's strictly over - exactly 20.0 goes through fine.

As it appears, spread across the exchange:

```
14:47  dermot    the run last night came back with `image attachment is 21.3 MB, over the 20.0 MB limit.` — i haven't touched the attachment doc yet, do i quote that verbatim or keep it loose
14:52  emil      keep it loose i think. the docs shouldn't sit on that number, the error already says it at runtime
14:54  dermot    yeah ok. prose then, no figure in the text
14:56  gideon    wait what about something landing exactly on the line though? does that get rejected or no
14:59  emil      goes through fine. its strictly over — 20.0 on the nose is not over, so it passes
15:01  gideon    ya thats what i had in my head, just wanted someone to say it out loud
```

#### `g8.r1.s5-gideon`

- **chat** · #pipeline · **dario** · 2025-05-02 15:56
- carries `g8.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly though, while I was poking at the same path - my anthropic run counted 85 per image and zero for the two document blocks, so the estimate is only half the mesage.

As it appears, spread across the exchange:

```
14:02  dario     the estimate on that multimodal batch came in way under what we got billed. either images are cheap or we're not counting them
14:04  dermot    if i had to guess they're counted, nothing in the walk skips an image block that i saw
14:06  gideon    honestly though, while i was poking at the same path - my anthropic run counted 85 per image, so those are in
14:07  dario     and the pdfs? that request had document blocks in it too
14:09  gideon    zero for the two document blocks. so the estimate is only half the mesage
14:11  dario     that tracks with how far off it was
14:12  dermot    so not a zero fallback, they're just never reaching the count
```

#### `g8.r1.say25`

- **chat** · #cookbooks · **konrad** · 2025-05-05 14:02
- carries `g8.r1.observability`
- must be typed literally: `thinking`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> i think an unknown block kind - a thinking block say - just contributes zero to the estimate, we dont raise on it and we don't charge its text either

As it appears, spread across the exchange:

```
14:02  konrad    quick one, what happens in the token estimate when a block kind isnt one we handle
14:04  dermot    not entirely sure. if i had to guess it hits the else and raises
14:06  konrad    thats what i was afraid of. a thinking block coming back would take the whole estimate down with it
14:10  dario     honestly i think it just contributes zero and we carry on, we dont raise on it
14:11  konrad    ok. and the text sitting inside it, that still counts toward the number?
14:13  dario     no we dont charge its text either. the block is zero, contents and all
14:15  dermot    yeah ok. simpler than i had it in my head
```

#### `g8.r2.l3`

- **chat** · #code-review · **gideon** · 2025-05-06 09:52
- carries `g8.r2.rule`
- must be typed literally: `[:12]`, `_ATTACHMENT_FINGERPRINT_HEX_LEN`, `attachment_fingerprint`, `sha256:`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> took Dermot's review nit, no inline [:12] slice - `_ATTACHMENT_FINGERPRINT_HEX_LEN` sits next to the helper now. `attachment_fingerprint` takes the payload string and hands back the "sha256:" prefix already on it.

As it appears, spread across the exchange:

```
15:11  gideon    konrad quick one - did you keep the [:12] inline in the fingerprint bit? dermot flagged it in review and i lost the thread
15:13  konrad    no i took the nit. its a named constant now, _ATTACHMENT_FINGERPRINT_HEX_LEN, sitting right next to the helper
15:14  gideon    ok. and the helper itself, what does it want handed to it
15:16  konrad    the payload string, thats all. attachment_fingerprint does the rest of it
15:17  gideon    so callers still glue the prefix on themselves after?
15:19  konrad    no, it comes back with sha256: already on it. nothing prefixes at the call site anymore
15:20  gideon    ya honestly inline it just read as a magic 12 to me, no clue what it was counting
15:22  dermot    mhm. thats all the nit was, the name does the work now
```

#### `g8.r1.say24`

- **chat** · #incidents · **dermot** · 2025-05-06 14:07
- carries `g8.r1.rule`
- must be typed literally: `AttachmentTooLarge(kind, size_mb, limit_mb)`, `.kind`, `.size_mb`, `.limit_mb`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> AttachmentTooLarge(kind, size_mb, limit_mb) and it keeps all three as .kind .size_mb and .limit_mb so a test can asssert on them not scrape a traceback

As it appears, spread across the exchange:

```
14:07  dermot    the oversize attachment test is still matching on the traceback text. broke again this morning
14:08  gideon    ya someone reworded the message. so what do we raise instead tbh
14:10  nikolai   our own one AttachmentTooLarge(kind, size_mb, limit_mb)
14:11  dermot    three args in. are those kept or just for building the message string
14:13  nikolai   kept .kind .size_mb .limit_mb so a test asserts on the fields and not the traceback
14:14  gideon    exactly what i was after. nobody has written it yet though right
14:15  nikolai   nope still the plain string today
14:16  dermot    yeah ok, so the wording can move around later and nothing cares
```

#### `g8.r1.s5-dermot`

- **chat** · #releases · **konrad** · 2025-05-06 15:02
- carries `g8.r1.observability`
- must be typed literally: `85`, `_OPENAI_TOKENS_PER_DOCUMENT`, `image_url`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah ok - _OPENAI_TOKENS_PER_DOCUMENT beside the image constant, flat number whether it comes in as file or document. the image one is 85 for an image_url block, same as anthropic's.

As it appears, spread across the exchange:

```
15:02  konrad    Quick one on the openai cost estimate. Do we have anything for pdfs there or is it only the image constant right now
15:05  dermot    only the image one at the moment. we'd sit a sibling next to it, _OPENAI_TOKENS_PER_DOCUMENT
15:07  konrad    And that scales per page? Also some of these arrive as a file block not a document one, presumably that changes the lookup
15:09  dermot    no, flat number whether it comes in as file or document. same value both ways, we are not counting pages
15:10  konrad    right. anyway what is the image one set to, I never actually looked at it
15:12  dermot    85 for an image_url block. same as anthropic's
15:14  nikolai   yep and nobody has ever argued with that number on the anthropic side so
```

#### `g8.r2.fix24`

- **chat** · #pipeline · **emil** · 2025-05-13 10:14
- carries `g8.r2.failure_behavior`
- must be typed literally: `_SUPPORTED_IMAGE_DETAILS`, `low`, `high`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> checked the ordering thing low sits ahead of high in `_SUPPORTED_IMAGE_DETAILS` cheapest first same order their docs table lsits them in

As it appears, spread across the exchange:

```
10:14  emil      picking up the model support table action item from thursday — the image detail param for multimodal requests is the bit i keep stalling on. where does the constant actually live, request layer or the provider shim? and it's just the two values plus auto, i believe
10:21  nikolai   checked the ordering nit low sits ahead of high in `_SUPPORTED_IMAGE_DETAILS` cheapest first same order their docs table lists them in
10:26  dario     mhm, that tracks. honestly i'd leave it wherever it is right now, the cookbook PRs are blocked on the table existing not on where the tuple sits
10:33  emil      yup. i'll write the table rows against that ordering then so we're not churning it in two weeks, we need to be intentional here. still not entirely sure auto belongs in the same
10:35  nikolai   auto is a diffrent question imo it's not a detail level its a fallback
```

#### `g8.r2.l16`

- **chat** · #pipeline · **gideon** · 2025-05-13 15:22
- carries `g8.r2.failure_behavior`
- must be typed literally: `auto`, `detail`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah ok - if it isn't one of the three we fall back to auto and log that once. nothing set at all logs nothing and the block still goes out with detail "auto".

As it appears, spread across the exchange:

```
15:22  gideon    what happens if the value someone sets isnt one of the three? do we hard fail on it
15:24  dermot    no. we fall back to auto and log that once
15:25  gideon    is that one line per bad value, or one for the whole run
15:26  dermot    one each time we fall back. we dont track what weve already said - a run that trips it twice says it twice
15:27  dario     and if nothing is set at all, does that warn too, or is that just the default and we stay quiet
15:29  dermot    yeah ok - nothing set at all logs nothing. and the block still goes out with detail "auto" either way
15:31  dario     so a blank one and a typo'd one look identical downstream. fine by me
```

#### `g8.r1.s5-emil`

- **chat** · #releases · **konrad** · 2025-05-30 13:52
- carries `g8.r1.observability`
- must be typed literally: `1400`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - anthropic puts a pdf page near 1400 tokens, so we charge 1400 flat for each document block. the total comes back a plain int.

As it appears, spread across the exchange:

```
13:52  konrad    the counter fell over on a pdf attachment yesterday. what do we count a document block as, off the top of my head we never picked a number
13:56  emil      let me think through that - anthropic puts a pdf page near 1400 tokens, so thats the number we work from
13:57  konrad    per page? we dont have the page count in hand at that point
14:00  emil      no, flat. 1400 for each document block, we dont open the file to look
14:02  dario     and what does the total come back as, i had it pencilled as a float in my head for some reason
14:04  emil      plain int, nothing wrapped round it
14:06  konrad    mhm. so a two page pdf and a two hundred page one land on the counter the same
14:07  emil      yup. untill someone hands us a page count thats where we are
```

#### `g8.r1.say23`

- **chat** · #general · **dermot** · 2025-06-02 11:02
- carries `g8.r1.rule`
- must be typed literally: `1024*1024`, `get_base64_size`, `size_mb`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - the base64 text is what actually goes over the wire, so size_mb is what get_base64_size hands back for that string. it works the real byte count out of the length arithmetically instead of decoding, and the divisor in there is 1024*1024, not a 1000-based megabyte.

As it appears, spread across the exchange:

```
11:02  dermot    quick one on attachments — size_mb, is that the file we read off disk or the encoded thing
11:05  nils      let me think. the base64 text is what actually goes over the wire, so it's measured on that string, not the file bytes
11:07  dermot    so we encode and then measure the encoded blob. feels like a lot of work just to learn a number
11:10  nils      not really — size_mb is just what get_base64_size hands back for that string. it works the real byte count out of the length arithmetically, it doesn't decode anything to find out
11:11  dermot    ah ok. thats cheap then
11:13  petar     and mb is which mb here, the honest one or the disk-vendor one
11:16  nils      the divisor in there is 1024*1024. a 1000-based megabyte would quietly shift the boundary and i'd rather not have that argument later
11:18  petar     right, that lines up with the totals looking a touch smaller than i kept expecting
```

#### `g8.r2.say20`

- **chat** · #pipeline · **gideon** · 2025-06-16 14:12
- carries `g8.r2.failure_behavior`
- must be typed literally: `image_url`, `data:image/png;base64,`, `detail`, `url`, `type`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> checked the openai side each image goes out as type image_url with an image_url object carrying url and detail and for inline we send the url as data:image/png;base64, then the payload

As it appears, spread across the exchange:

```
14:12  gideon    quick one before i wire the vision path — what shape does an image actually go out in on the request? i keep guessing and getting 400s back
14:16  nikolai   checked the openai side this morning each image goes out as type image_url
14:18  emil      so one of those per image rather than one entry holding all of them, is that the read?
14:19  nikolai   yep one per image and it carries an image_url object alongside
14:21  gideon    ok but whats in that object? i had it in my head as just the url but i swear there was a second key
14:23  nikolai   url and detail
14:24  gideon    right and the inline ones? we dont have anything to put in url for those, theyre bytes in memory
14:26  nikolai   same object nothing special we send the url as data:image/png;base64, and then the payload straight after it
14:28  gideon    ahh. so the branch i wrote last week that dropped the raw b64 in bare was never going to work, that's the 400s right there
```

