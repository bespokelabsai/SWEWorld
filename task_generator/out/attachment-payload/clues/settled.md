# Was every graded thing said, or only implied? — g8

**53 of 92** assertions rest on something a remark says outright.

- `stated` **53** — a reader was told
- `implied` **26** — a reader has to work it out, and may not
- `absent` **3** — nothing in the corpus bears on it
- `not_required` **10** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 21 remark(s) rewritten, 7 added, 1 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g8.r1.exclusions_or_crossover#1` | n/a | `g8.r1.s3-konrad`, `g8.r1.s3-emil` | This is a sanity check that the fixture block came through as a url-sourced block, which is the pre-existing Anthropic block shape the feature does not change; no remark names a `source` attribute hol |
| `g8.r1.exclusions_or_crossover#2` | stated | `g8.r1.s3-konrad`, `g8.r1.s1-dario` | konrad names the attribute and its value for exactly this case — "for a url block we never hold the bytes at all, so size_mb just stays empty there, not some made up zero" — and dario confirms size_mb |
| `g8.r1.exclusions_or_crossover#3` | **implied** | `g8.r1.s3-konrad`, `g8.r1.s4-gideon`, `g8.r1.s3-nikolai` | Nobody says file_upload_limit_check is skipped for url blocks; the reader must join "we never hold the bytes" plus "we called file_upload_limit_check on each base64" and supply for themselves that no  |
| `g8.r1.exclusions_or_crossover#4` | stated | `g8.r1.s3-emil`, `g8.r1.s3-nils` | emil rules url-sourced blocks out of the per-kind ceilings outright and nils rules them out of the whole-prompt total, so an all-url prompt raising nothing and returning all its blocks is the decision |
| `g8.r1.exclusions_or_crossover#5` | **implied** | `g8.r1.s3-konrad`, `g8.r1.s4-gideon`, `g8.r1.s3-nikolai` | Same gap as #3 — the corpus decides url blocks are not weighed or compared, but never says the provider hook goes uncalled for them, so the reader has to conclude that on their own. |
| `g8.r1.exclusions_or_crossover#6` | stated | `g8.r1.s3-emil`, `g8.r1.s3-nils` | A mixed url/pdf prompt passing intact follows from emil's exclusion of url blocks from the per-kind ceilings and nils's exclusion of them from the 45 MB prompt sum, both of which are said outright. |
| `g8.r1.exclusions_or_crossover#7` | **implied** | `g8.r1.s4-gideon`, `g8.r1.s3-konrad`, `g8.r1.s3-emil` | gideon states the hook is called with each base64 payload, which covers the PDF half, but the exact-equality demands the url block contributed no call — and no remark says the hook is skipped for url  |
| `g8.r1.failure_behavior#1` | **absent** | `g8.r1.s4-dario`, `g8.r1.rev1` | No remark names an `AttachmentError` base class or says TooManyAttachments shares a hierarchy with AttachmentTooLarge; only the two concrete names ever appear. |
| `g8.r1.failure_behavior#10` | n/a | `g8.r1.s4-konrad` | This counts the blocks in the suite's own forty-texts-plus-one-image fixture rather than any behaviour of the code. |
| `g8.r1.failure_behavior#11` | **implied** | `g8.r1.s4-konrad` | Konrad says texts don't count toward the limit and that forty texts with one image is normal, but nobody says text blocks also bypass the attachment serialization path — the reader has to carry "doesn |
| `g8.r1.failure_behavior#2` | **absent** | `g8.r1.s4-dario` | Nothing in the corpus says any attachment exception derives from ValueError or from any builtin. |
| `g8.r1.failure_behavior#3` | stated | `g8.r1.s4-konrad` | Konrad attaches the number to the exact constant name: "_ATTACHMENT_COUNT_LIMIT stays at 12". |
| `g8.r1.failure_behavior#4` | stated | `g8.r1.s4-konrad`, `g8.r1.s4-dario`, `g8.r1.s4-nikolai` | Konrad decides "twelve is fine, thirteen is not" and dario names TooManyAttachments as the exception for the over-count case, with nikolai showing it firing on a 31-image prompt. |
| `g8.r1.failure_behavior#5` | stated | `g8.r1.s4-dario`, `g8.r1.s4-konrad` | Dario says the exception "should carry the count and the ceiling it broke", and konrad fixes the ceiling at 12 with thirteen as the failing case, giving both fields and both values. |
| `g8.r1.failure_behavior#6` | stated | `g8.r1.s4-nikolai` | Nikolai quotes the rendered message verbatim, `Prompt has 31 attachments, over the limit of 12.`, fixing the template and punctuation. |
| `g8.r1.failure_behavior#7` | stated | `g8.r1.s4-dario`, `g8.r1.s4-gideon` | Dario says it "has to fire before we serialize a single one of them" and gideon says the guard must run ahead of the per-attachment base64 and file_upload_limit_check calls. |
| `g8.r1.failure_behavior#8` | n/a | — | This measures the thirteen-attachment prompt the suite itself constructed, not any decision the corpus owed. |
| `g8.r1.failure_behavior#9` | stated | `g8.r1.s4-konrad`, `g8.r1.s4-gideon` | Konrad rules that "twelve is fine", and gideon describes the normal path as base64'ing and hook-calling every attachment, so twelve accepted attachments means twelve serialize calls. |
| `g8.r1.observability#1` | stated | `g8.r1.s5-dermot`, `g8.r1.s5-emil` | dermot commits to one flat number per block "whether it came in as a file or a document" and emil commits to that number being 1400, so a file block priced flat at 1400 is a decision made out loud. |
| `g8.r1.observability#2` | stated | `g8.r1.s5-emil`, `g8.r1.s5-dermot`, `g8.r1.s5-gideon` | emil says outright to charge 1400 flat for each pdf/document block, and gideon's complaint that documents counted zero establishes it is the token estimate being fixed. |
| `g8.r1.observability#3` | **implied** | `g8.r1.s5-gideon`, `g8.r1.s5-dermot` | gideon's "85 per image" is reported from an anthropic run and dermot only refers to "the image constant" without a value, so the reader must supply that an OpenAI image_url block is also 85. |
| `g8.r1.observability#4` | stated | `g8.r1.s5-gideon` | gideon reports his anthropic run counting 85 per image as the correct half of the estimate, naming both the block kind and the number. |
| `g8.r1.observability#5` | **implied** | `g8.r1.s5-gideon`, `g8.r1.s5-emil`, `g8.r1.s5-dermot` | the per-kind numbers are said but nobody anywhere says an unrecognised block type ("thinking") contributes zero rather than raising or being charged its text length, so the reader supplies the 0 term  |
| `g8.r1.observability#6` | **implied** | `g8.r1.s5-emil`, `g8.r1.s5-gideon` | nobody discusses the return type of the estimate; the reader gets int only by noticing every quoted count (85, 1400) is a whole number. |
| `g8.r1.observability#7` | stated | `g8.r1.s5-dermot`, `g8.r1.s5-emil` | dermot names _OPENAI_TOKENS_PER_DOCUMENT as the module constant holding the flat per-document number and emil states that number is 1400, and there is no other name the value could land in. |
| `g8.r1.observability#8` | n/a | — | this only checks that the suite's own PDF_B64 fixture decodes to its PDF_BYTES fixture, which the corpus owes nothing. |
| `g8.r1.rule#1` | **absent** | — | No remark names `AttachmentError` or says AttachmentTooLarge inherits from any base; the existence of a sibling exception (TooManyAttachments) and "reusing the same exception" never establish a shared |
| `g8.r1.rule#10` | **implied** | — | Konrad's "20.0 MB image kind, 24.0 document" names the kinds but never says the canonical block carries a field called `kind` recording them, so the reader supplies that the resolved kind is readable  |
| `g8.r1.rule#11` | stated | — | Dario says to weigh the base64 at block-build time and "hang size_mb off the block", and konrad refers to size_mb staying empty for url blocks, naming the field and its home. |
| `g8.r1.rule#12` | **implied** | — | Gideon says file_upload_limit_check was called on each base64'd attachment, but nobody says the argument is the base64 payload string itself, so the exact call record is left to the reader. |
| `g8.r1.rule#2` | **implied** | — | The reader must supply the decision that `size_mb` is a float rather than an int, a Decimal or a formatted string — nobody says it, only that quoted messages show decimal figures like 21.3 and 20.0. |
| `g8.r1.rule#3` | **implied** | — | Dario says to weigh the base64 string in hand rather than decoding, and nils says base64 is what the wire carries, but nobody gives the conversion (base64 character count divided by 1024*1024) that ma |
| `g8.r1.rule#4` | stated | — | Both revision remarks say plainly that the image ceiling is 20.0 MB and that AttachmentTooLarge is what fires, so a 24 MB image raising it was decided out loud. |
| `g8.r1.rule#5` | **implied** | — | Only TooManyAttachments is said to carry its count and ceiling, and only the overturned prompt-total remark hints at a settable kind; nobody says AttachmentTooLarge stores .kind, .size_mb and .limit_m |
| `g8.r1.rule#6` | stated | — | Emil quotes the message verbatim from a run — "image attachment is 21.3 MB, over the 20.0 MB limit." — giving the exact template, punctuation and slot order. |
| `g8.r1.rule#7` | stated | — | Dermot and both revision remarks say AttachmentTooLarge fires inside _canonical_attachment_block ahead of file_upload_limit_check, so the hook seeing nothing for an oversized image was decided explici |
| `g8.r1.rule#8` | **implied** | — | The 24.0 document ceiling and the hook-runs-after ordering are stated, but nobody says the comparison is strictly greater, so whether a payload measuring exactly 24.0 passes through to the hook or is  |
| `g8.r1.rule#9` | n/a | — | "provider" is the string the suite's own stub hook raises; the corpus owes nothing to a fixture's error text. |
| `g8.r1.scope#1` | stated | `g8.r1.s2-gideon`, `g8.r1.s1-dermot`, `g8.r1.rev1`, `g8.r1.s2-nils` | gideon says the whole-prompt total reuses "the same exception" with kind set to prompt, and AttachmentTooLarge is the exception named repeatedly elsewhere, so the reader is told the aggregate overflow |
| `g8.r1.scope#2` | stated | `g8.r1.s2-nils`, `g8.r1.s2-gideon`, `g8.r1.s2-dario`, `g8.r1.s2-konrad` | nils fixes the ceiling at 45 MB over the summed base64 blocks, gideon fixes kind="prompt" on the reused exception, and gideon/dario put the single check after every attachment so the reported size is  |
| `g8.r1.scope#3` | stated | `g8.r1.s2-dario`, `g8.r1.s4-gideon`, `g8.r1.s2-gideon` | dario says the whole-prompt number happens "once all the per-attachment hook calls have gone through, not woven in between them", and gideon describes file_upload_limit_check being called on each atta |
| `g8.r1.scope#4` | **implied** | `g8.r1.s2-gideon`, `g8.r1.rev1`, `g8.r1.rev2` | gideon says the total "belongs in _handle_multi_modal_prompt", but nobody names _format_multimodal or says it keeps building blocks for an over-45 set, so the reader must supply the exclusivity themse |
| `g8.r1.scope#5` | **implied** | `g8.r1.s4-gideon`, `g8.r1.s2-gideon`, `g8.r1.g8-pre-r1-single-ceiling-dario` | that the hook fires per attachment is said, but nobody states that the block-building path runs to completion for an aggregate-oversize prompt instead of short-circuiting, so the reader must infer the |
| `g8.r2.exclusions_or_crossover#1` | n/a | `g8.r2.l9`, `g8.r2.l11` | This establishes that the block the suite built from a remote link is the url-kind block before the fingerprint claims are checked; the url/base64 distinction is pre-existing surface the corpus talks  |
| `g8.r2.exclusions_or_crossover#2` | stated | `g8.r2.l9`, `g8.r2.l11`, `g8.r2.l2` | l9 reports that the fingerprint comes back empty for anything with an http url and l11 answers it out loud — hash the url string exactly as we send it — with l2 making fingerprint required on the reco |
| `g8.r2.exclusions_or_crossover#3` | n/a | `g8.r2.l12` | Precondition on the suite's own crossover fixture: it names the second block as the base64-source one, a kind the corpus assumes (l12 speaks of the base64 text) rather than decides. |
| `g8.r2.exclusions_or_crossover#4` | n/a | `g8.r2.l8` | It checks that the suite's deliberately odd fixture — a url string handed in as a base64 payload — came back out unaltered, which is payload passthrough the corpus already takes for granted (l8 only s |
| `g8.r2.exclusions_or_crossover#5` | **implied** | `g8.r2.l11`, `g8.r2.l12` | l11 says url blocks hash the url string and l12 says base64 blocks hash the base64 text, but nobody says the digest is taken over the payload string alone, so the reader must supply on their own that  |
| `g8.r2.exclusions_or_crossover#6` | stated | `g8.r2.l10`, `g8.r2.l11` | l10 pins that cat.jpeg with ?size=large and cat.jpeg without it must stay two separate entries and l11 says the query is included in the hash of the url string. |
| `g8.r2.exclusions_or_crossover#7` | stated | `g8.r2.l11` | l11 says the url string is hashed exactly as sent, query and anchor included, so a url carrying a fragment cannot digest to the same value as the bare one. |
| `g8.r2.exclusions_or_crossover#8` | stated | `g8.r2.l2`, `g8.r2.l12` | l2 asks that the record carry a short digest of the payload and that fingerprint be required rather than optional, and l12 says base64 payloads are hashed as-is, so such a block has a value. |
| `g8.r2.exclusions_or_crossover#9` | stated | `g8.r2.l12` | l12 says decoding every payload before hashing was tried and abandoned because the 40k pass crawled, and that the base64 text is hashed as-is, which is exactly the exclusion of the decoded-bytes diges |
| `g8.r2.failure_behavior#1` | stated | `g8.r2.rev1`, `g8.r2.l15` | rev1 says the fallback happens at block-build and "Image.detail is left alone" (said about a typo'd off-list value), and l15 complains the source object was rewritten and shouldn't be mutated. |
| `g8.r2.failure_behavior#10` | stated | `g8.r2.l16`, `g8.r2.l15` | l16 says a matching value or nothing set at all logs nothing, and l15 names the all-40k warning noise as the bug. |
| `g8.r2.failure_behavior#11` | **implied** | `g8.r2.rev2`, `g8.r2.detail-passthrough-1`, `g8.r2.rev1` | the "high" reaching the provider follows from rev1/rev2, but nobody states the OpenAI payload shape — the image_url wrapper, the data:image/png;base64 URL — that the rest of this dict comparison deman |
| `g8.r2.failure_behavior#12` | stated | `g8.r2.rev1`, `g8.r2.l16` | rev1 frames the fallback as happening "instead of forwarding it untouched", i.e. "auto" is what goes out to the provider for an off-list value. |
| `g8.r2.failure_behavior#13` | **implied** | `g8.r2.l16`, `g8.r2.rev2` | l16 says nothing-set is silent but never says what value it yields, so that normalize_detail takes None and returns "auto" is the reader's inference. |
| `g8.r2.failure_behavior#14` | stated | `g8.r2.rev2` | rev2 names the function and the exact mapping: normalize_detail lowercases so "HIGH" lands as "high". |
| `g8.r2.failure_behavior#15` | stated | `g8.r2.rev2` | rev2 says normalize_detail strips and lowercases against the vocabulary. |
| `g8.r2.failure_behavior#16` | stated | `g8.r2.rev2`, `g8.r2.rev1` | rev2 says anything off the list becomes "auto", attached to normalize_detail by name. |
| `g8.r2.failure_behavior#17` | stated | `g8.r2.rev1`, `g8.r2.l16` | exactly one warning on the fallback is stated by both rev1 and l16. |
| `g8.r2.failure_behavior#18` | stated | `g8.r2.l14`, `g8.r2.rev2` | l14 attaches the three members, in this order and "nothing else", to the name _SUPPORTED_IMAGE_DETAILS. |
| `g8.r2.failure_behavior#19` | n/a | — | this checks the suite's own base64 fixture arithmetic, not any behaviour the corpus owes. |
| `g8.r2.failure_behavior#2` | stated | `g8.r2.rev1`, `g8.r2.l15`, `g8.r2.l13` | rev1 names Image.detail as an attribute left untouched and l15 forbids mutating the source, with l13 already showing detail="HIGH" as the caller-written string. |
| `g8.r2.failure_behavior#3` | stated | `g8.r2.rev1`, `g8.r2.rev2` | rev1 puts normalize_detail at block-build and rev2 says "HIGH" lands as "high", so the block's detail carrying "high" was decided out loud. |
| `g8.r2.failure_behavior#4` | stated | `g8.r2.rev2` | rev2 says normalize_detail strips and lowercases, which is exactly " Low " → "low". |
| `g8.r2.failure_behavior#5` | stated | `g8.r2.rev2`, `g8.r2.l14`, `g8.r2.l16` | rev2's strip-and-lowercase-against-the-list rule plus l14/l16 putting "auto" among the three accepted values makes an on-list value pass through unchanged. |
| `g8.r2.failure_behavior#6` | stated | `g8.r2.rev1`, `g8.r2.rev2`, `g8.r2.l16` | rev1, rev2 and l16 all say an off-vocabulary value falls back to "auto" at block-build. |
| `g8.r2.failure_behavior#7` | stated | `g8.r2.rev1`, `g8.r2.l16` | rev1 says "one warning" and l16 says "log that once" for the fallback path. |
| `g8.r2.failure_behavior#8` | stated | `g8.r2.rev2`, `g8.r2.l14` | rev2 fixes "high" as the canonical member of the list, so an already-lowercase hit is preserved. |
| `g8.r2.failure_behavior#9` | **implied** | `g8.r2.l16`, `g8.r2.l15` | l16 only says an unset detail logs nothing — nobody says the block then carries "auto" rather than omitting the field, so the reader has to supply the default themselves. |
| `g8.r2.rule#1` | stated | `g8.r2.l4`, `g8.r2.l2` | Gideon pins the exact value for exactly this input: a tmp file holding %PDF-1.4 comes out as sha256:fc1c4358d4aa, and Dermot already named the block field fingerprint. |
| `g8.r2.rule#10` | **implied** | `g8.r2.l12`, `g8.r2.l3` | Nobody discusses an empty payload at all, so the reader has to decide on their own that the general rule applies uniformly with no special case. |
| `g8.r2.rule#11` | stated | `g8.r2.l3` | Konrad names _ATTACHMENT_FINGERPRINT_HEX_LEN and, in the same breath, the [:12] slice it replaces, attaching the number to that exact name. |
| `g8.r2.rule#2` | stated | `g8.r2.l12`, `g8.r2.l3`, `g8.r2.l4` | Emil commits out loud to hashing the base64 text as-is rather than decoding it, Konrad fixes the slice at 12, and the pinned values carry the sha256: prefix, which is the whole of what digest_of recom |
| `g8.r2.rule#3` | stated | `g8.r2.l3`, `g8.r2.l12`, `g8.r2.l4` | Both pinned fingerprints are written verbatim as sha256: followed by twelve hex characters and Konrad's nit fixes the slice at [:12], so the shape is on the page rather than reconstructed. |
| `g8.r2.rule#4` | stated | `g8.r2.l12`, `g8.r2.l2` | Emil pins the one-byte image at sha256:5e21d86b709b under the base64-as-is rule, which is precisely the value a b"x" payload produces, and Dermot names the field it lands in. |
| `g8.r2.rule#5` | stated | `g8.r2.l4`, `g8.r2.l12` | The corpus pins two different payloads at two different fingerprints, so distinct blocks carrying distinct values is asserted rather than inferred. |
| `g8.r2.rule#6` | n/a | `g8.r2.l12` | The base64 payload field predates this change and the requirement only adds fingerprint, so this checks existing block behaviour the corpus owes nothing about. |
| `g8.r2.rule#7` | stated | `g8.r2.l4` | Gideon's "same value every run" is exactly the determinism claim, tied to the same %PDF-1.4 bytes and the same pinned value. |
| `g8.r2.rule#8` | **implied** | `g8.r2.l3`, `g8.r2.l12`, `g8.r2.l4` | Konrad names attachment_fingerprint in a nit about an inline slice but never says it takes the base64 payload string or that the sha256: prefix comes from the helper rather than from the block-buildin |
| `g8.r2.rule#9` | **implied** | `g8.r2.l3`, `g8.r2.l12` | The value is pinned on the image block, not on the helper; nothing rules out a helper returning bare hex with the prefix added at the call site. |
| `g8.r2.scope#1` | stated | `g8.r2.l6`, `g8.r2.l7`, `g8.r2.l5` | Emil names the constant and its value 64 as a max, Konrad commits that the suffix stays on when we shorten, and Nikolai supplies the 73-character finance-export basename, so producing a 64-character n |
| `g8.r2.scope#10` | stated | `g8.r2.l6` | Emil's '64 is plenty for the name we put on the block, past that its just the date written twice' says shortening applies only past the cap, leaving a short name alone. |
| `g8.r2.scope#2` | stated | `g8.r2.l6`, `g8.r2.l7` | A constant literally named _MAX_ATTACHMENT_FILENAME_LEN = 64 fixes the length and Konrad's 'the suffix stays on when we shorten' fixes the ending, which is exactly what this assertion tests. |
| `g8.r2.scope#3` | stated | `g8.r2.l8` | Dario says it in one sentence: shortening only touches the display name we derive, and the url we put in the payload stays whole. |
| `g8.r2.scope#4` | **implied** | `g8.r2.l8`, `g8.r2.l15` | The reader is left to supply that non-mutation extends to the caller's File object — l8 protects only the url in the payload, and the one 'we shouldn't mutate the source' complaint (l15) is about Imag |
| `g8.r2.scope#5` | **implied** | `g8.r2.l5`, `g8.r2.l8`, `g8.r2.l7` | The capped filename and whole url are told, but nobody in this corpus names the wire shape — the keys type/file/filename/file_url are the reader's to guess from 'the file block we send is mostly filen |
| `g8.r2.scope#6` | **implied** | `g8.r2.l6`, `g8.r2.l7` | Nobody addresses the boundary, so the reader has to decide alone that a name of exactly 64 is left untouched rather than cut by a >= test, which would return a different string here. |
| `g8.r2.scope#7` | stated | `g8.r2.l6` | The named max of 64 fixes the length of this result under either boundary reading, so the cap remark carries it directly. |
| `g8.r2.scope#8` | **implied** | `g8.r2.l7`, `g8.r2.l6` | Konrad only ever discusses a .pdf suffix coming off the end; the reader must work out unaided that with no extension to reserve the rule degenerates to a plain 64-character prefix with nothing appende |
| `g8.r2.scope#9` | stated | `g8.r2.l6` | The max of 64 is stated outright and a long name capped by it is 64 characters regardless of how the extension question is resolved. |

### `g8.r1.exclusions_or_crossover#3` — implied

```python
assert stub.calls == []          # nothing was read, so nothing was offered
```

Nobody says file_upload_limit_check is skipped for url blocks; the reader must join "we never hold the bytes" plus "we called file_upload_limit_check on each base64" and supply for themselves that no bytes means no hook call rather than offering the url string.

### `g8.r1.exclusions_or_crossover#5` — implied

```python
assert urls.calls == []
```

Same gap as #3 — the corpus decides url blocks are not weighed or compared, but never says the provider hook goes uncalled for them, so the reader has to conclude that on their own.

### `g8.r1.exclusions_or_crossover#7` — implied

```python
assert mixed.calls == [PDF_B64]
```

gideon states the hook is called with each base64 payload, which covers the PDF half, but the exact-equality demands the url block contributed no call — and no remark says the hook is skipped for url blocks, only that they aren't measured.

### `g8.r1.failure_behavior#1` — absent

```python
assert issubclass(TooManyAttachments, attachment_symbol("AttachmentError"))
```

No remark names an `AttachmentError` base class or says TooManyAttachments shares a hierarchy with AttachmentTooLarge; only the two concrete names ever appear.

### `g8.r1.failure_behavior#11` — implied

```python
assert len(texts.calls) == 1
```

Konrad says texts don't count toward the limit and that forty texts with one image is normal, but nobody says text blocks also bypass the attachment serialization path — the reader has to carry "doesn't count" over into "isn't serialized as an attachment".

### `g8.r1.failure_behavior#2` — absent

```python
assert issubclass(TooManyAttachments, ValueError)
```

Nothing in the corpus says any attachment exception derives from ValueError or from any builtin.

### `g8.r1.observability#3` — implied

```python
assert calculate_input_tokens([openai_image], encoder) == 85
```

gideon's "85 per image" is reported from an anthropic run and dermot only refers to "the image constant" without a value, so the reader must supply that an OpenAI image_url block is also 85.

### `g8.r1.observability#5` — implied

```python
assert total == 5 + 85 + 85 + 1400 + 1400 + 0 == 2975
```

the per-kind numbers are said but nobody anywhere says an unrecognised block type ("thinking") contributes zero rather than raising or being charged its text length, so the reader supplies the 0 term themselves.

### `g8.r1.observability#6` — implied

```python
assert isinstance(total, int)
```

nobody discusses the return type of the estimate; the reader gets int only by noticing every quoted count (85, 1400) is a whole number.

### `g8.r1.rule#1` — absent

```python
assert issubclass(AttachmentTooLarge, attachment_symbol("AttachmentError"))
```

No remark names `AttachmentError` or says AttachmentTooLarge inherits from any base; the existence of a sibling exception (TooManyAttachments) and "reusing the same exception" never establish a shared parent class the test can look up.

### `g8.r1.rule#10` — implied

```python
assert read_field(document, "kind") == "document"
```

Konrad's "20.0 MB image kind, 24.0 document" names the kinds but never says the canonical block carries a field called `kind` recording them, so the reader supplies that the resolved kind is readable off the block.

### `g8.r1.rule#12` — implied

```python
assert recording.calls == [PAYLOAD_24MB]
```

Gideon says file_upload_limit_check was called on each base64'd attachment, but nobody says the argument is the base64 payload string itself, so the exact call record is left to the reader.

### `g8.r1.rule#2` — implied

```python
assert isinstance(measured, float)
```

The reader must supply the decision that `size_mb` is a float rather than an int, a Decimal or a formatted string — nobody says it, only that quoted messages show decimal figures like 21.3 and 20.0.

### `g8.r1.rule#3` — implied

```python
assert measured == get_base64_size(PDF_B64) == 8.58306884765625e-06
```

Dario says to weigh the base64 string in hand rather than decoding, and nils says base64 is what the wire carries, but nobody gives the conversion (base64 character count divided by 1024*1024) that makes the measurement equal this exact value rather than a decoded-byte or 1000-based megabyte.

### `g8.r1.rule#5` — implied

```python
assert triple(exc) == ("image", 24.0, 20.0)
```

Only TooManyAttachments is said to carry its count and ceiling, and only the overturned prompt-total remark hints at a settable kind; nobody says AttachmentTooLarge stores .kind, .size_mb and .limit_mb as attributes in that order.

### `g8.r1.rule#8` — implied

```python
# the very same 24.0 MB, resolved as a document, is inside the higher ceiling and
    # is handed on to the provider hook, which is what refuses it
    with pytest.raises(RuntimeError) as runtime:
```

The 24.0 document ceiling and the hook-runs-after ordering are stated, but nobody says the comparison is strictly greater, so whether a payload measuring exactly 24.0 passes through to the hook or is refused is left for the reader to settle.

### `g8.r1.scope#4` — implied

```python
assert len(content) == 2
```

gideon says the total "belongs in _handle_multi_modal_prompt", but nobody names _format_multimodal or says it keeps building blocks for an over-45 set, so the reader must supply the exclusivity themselves.

### `g8.r1.scope#5` — implied

```python
assert len(control.calls) == 2
```

that the hook fires per attachment is said, but nobody states that the block-building path runs to completion for an aggregate-oversize prompt instead of short-circuiting, so the reader must infer the aggregate check lives nowhere but the outer function.

### `g8.r2.exclusions_or_crossover#5` — implied

```python
assert fingerprint == read_field(inline, "fingerprint")
```

l11 says url blocks hash the url string and l12 says base64 blocks hash the base64 text, but nobody says the digest is taken over the payload string alone, so the reader must supply on their own that no source kind, prefix or salt is mixed in and that the two kinds therefore collide on an identical string.

### `g8.r2.failure_behavior#11` — implied

```python
# the normalized value is what reaches the provider
    assert render_openai(block_of(stub, Image(content=b"x", detail="HIGH"))) == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,eA==", "detail": "high"},
    }
```

the "high" reaching the provider follows from rev1/rev2, but nobody states the OpenAI payload shape — the image_url wrapper, the data:image/png;base64 URL — that the rest of this dict comparison demands.

### `g8.r2.failure_behavior#13` — implied

```python
assert normalize_detail(None) == "auto"
```

l16 says nothing-set is silent but never says what value it yields, so that normalize_detail takes None and returns "auto" is the reader's inference.

### `g8.r2.failure_behavior#9` — implied

```python
assert read_field(block_of(stub, Image(content=b"x")), "detail") == "auto"
```

l16 only says an unset detail logs nothing — nobody says the block then carries "auto" rather than omitting the field, so the reader has to supply the default themselves.

### `g8.r2.rule#10` — implied

```python
assert helper("") == digest_of("")
```

Nobody discusses an empty payload at all, so the reader has to decide on their own that the general rule applies uniformly with no special case.

### `g8.r2.rule#8` — implied

```python
assert helper(PDF_B64) == "sha256:fc1c4358d4aa"
```

Konrad names attachment_fingerprint in a nit about an inline slice but never says it takes the base64 payload string or that the sha256: prefix comes from the helper rather than from the block-building code.

### `g8.r2.rule#9` — implied

```python
assert helper("eA==") == "sha256:5e21d86b709b"
```

The value is pinned on the image block, not on the helper; nothing rules out a helper returning bare hex with the prefix added at the call site.

### `g8.r2.scope#4` — implied

```python
assert long_pdf.url == LONG_PDF_URL
```

The reader is left to supply that non-mutation extends to the caller's File object — l8 protects only the url in the payload, and the one 'we shouldn't mutate the source' complaint (l15) is about Image.detail, not attachments.

### `g8.r2.scope#5` — implied

```python
assert render_openai(block) == {
        "type": "file",
        "file": {
            "filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf",
            "file_url": LONG_PDF_URL,
        },
    }
```

The capped filename and whole url are told, but nobody in this corpus names the wire shape — the keys type/file/filename/file_url are the reader's to guess from 'the file block we send is mostly filename'.

### `g8.r2.scope#6` — implied

```python
assert boundary == "2024-q4-consolidated-financial-statements-and-notes-final-v3.pdf"
```

Nobody addresses the boundary, so the reader has to decide alone that a name of exactly 64 is left untouched rather than cut by a >= test, which would return a different string here.

### `g8.r2.scope#8` — implied

```python
assert read_field(extensionless, "filename") == "ledger-entries-consolidated-2024-q4-final-copy-for-review-board-"
```

Konrad only ever discusses a .pdf suffix coming off the end; the reader must work out unaided that with no extension to reserve the rule degenerates to a plain 64-character prefix with nothing appended.
