# The tree

## g8.r1

### g8.r1.s1 — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*The leap nobody states:* If the team wants a size stamped on the block and separate numbers for images and documents, and wants their own error raised before the provider's check runs, then the measurement and the comparison both live in the block constructor.

- **gideon** (2025-04-15, #pipeline): so basically the 31 meg screenshot went out to openai before anything objected, we paid for the upload and got a 400 back. that has to be caught localy.
- **dario** (2025-04-23, #pipeline): we already have the base64 string in hand when the block gets built, so i'd weigh that rather than decoding, and hang size_mb off the block as a plain float.
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

