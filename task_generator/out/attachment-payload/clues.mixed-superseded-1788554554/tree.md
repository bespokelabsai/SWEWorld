# The tree

## g8.r1

### g8.r1.g8r1-s1 — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*The leap nobody states:* a check that already knows the payload is too big should speak before one that has to go and ask

- **gideon** (2025-03-17, #pipeline): so basically I spent a minute base64ing a 31 MB png and the provider bounced it in two lines, nothing on our side looked at the size first
- **dermot** (2025-04-29, #pipeline): anthropic takes a 22 meg pdf without blinking, an image that size comes straight back. one ceiling for both kinds is going to be wrong.
- **emil** (2025-05-13, page:engineering/attachment-limits-for-multimodal-requests-and-where-we-check-them.md): ok, 20 for images and 24 for documents then. and something landing exactly on the number should still go out, not get refused.
- **dario** (2025-04-28, thread:<178770450521.2334287.16901596979904917532@world.local>): left it on 651: we hand a payload we already know is oversized to file_upload_limit_check. AttachmentTooLarge should have fired in the block builder, before that hook.

### g8.r1.g8r1-s2 — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*The leap nobody states:* you can only weigh bytes you are actually holding, and a link means somebody else is holding them

- **nils** (2025-03-26, #pipeline): my first pass sized the remote ones with a HEAD and the tests immediately started going out to the network. i'm not doing that in a formatter.
- **konrad** (2025-06-17, page:engineering/attachment-blocks-in-multimodal-requests-gemini-batch.md): look, for a link we never hold the bytes on our side, so size_mb just stays empty on those blocks.
- **nikolai** (2025-06-18, thread:new|g8.r1.g8r1-l7): also the running total shouldnt pick up linked attachements otherwise a prompt of ten cdn urls fails over bytes we never sent
- **gideon** (2025-04-24, #pipeline): so basically a 30 MB image sitting on a cdn is fine, they fetch it themselves - the ceiling only bites what we actually encode into the payload.

### g8.r1.g8r1-s3 — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*The leap nobody states:* limits on each file separately say nothing about the size of the one request they all go into

- **gideon** (2025-06-11, page:engineering/attachment-payloads-where-they-get-assembled-and-which-limit-is-actually-checked.md): so basically five pdfs, every one under its own ceiling, and the request still came back too large. about 60 across the lot, so per-attachment limits alone dont catch it.
- **dermot** (2025-03-19, #pipeline): the per-attachment path only ever sees one file, so the total gets summed in the multimodal handler once all the file_upload_limit_check calls have run
- **emil** (2025-03-14, #code-review): let me think through that - each block already carries size_mb off its encoded text, so the whole-prompt number is just summing size_mb, no re-reading anything.
- **nikolai** (2025-06-19, page:engineering/gemini-batch-attachments-the-two-size-ceilings-and-what-they-raise.md): mine came back prompt attachment is 51.2 MB over the 45.0 MB limit same exeption as the per file one kind just says prompt

### g8.r1.g8r1-s4 — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*The leap nobody states:* if a request is doomed on the count alone there is no reason to spend minutes encoding it first

- **konrad** (2025-05-06, thread:new|g8.r1.g8r1-l13): Look, a cookbook user handed us a folder of 200 pngs — we base64'd every single one of them and then the API refused the request anyway.
- **nikolai** (2025-03-17, #code-review): its `_ATTACHMENT_COUNT_LIMIT` in attachment.py not ATTACHMENT_MAX and we count the list before anythign gets read off disk or handed to the upload hook
- **dario** (2025-06-24, page:engineering/attachment-limits-on-multimodal-requests.md): mhm, that tracks. and TooManyAttachments sits under the same base as the other attachment errors, callers catch the one thing.
- **nils** (2025-03-18, #code-review): tried it with fourteen images and got `Prompt has 14 attachments, over the limit of 12.` — my forty text chunks didn't count toward it, which is right.

### g8.r1.g8r1-s5 — File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.

*The leap nobody states:* an attachment the model actually reads costs tokens, so estimating it at nothing makes the whole estimate useless

- **emil** (2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>): on your cost question — last night's pdf run came out at about the text length. document and file blocks are priced at zero in the input estimate, which isn't right.
- **konrad** (2025-06-10, page:engineering/estimating-request-payload-size-before-chunking-a-batch-file.md): look, call a document 1400 and move on. its an estimate not a bill.
- **dermot** (2025-04-02, thread:new|g8.r1.g8r1-l19): the document price sits next to the image table as `_OPENAI_TOKENS_PER_DOCUMENT`, and the anthropic-shaped document blocks take the same number as the openai file ones.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): one ceiling for both, 20 mb whether it's an image or a document - the size check in _canonical_attachment_block doesn't branch on block.kind at all.
- **emil** (2025-01-22): ordering is settled then: file_upload_limit_check runs first, our 20 MB ceiling only gets a say after the provider has already had the payload.

## g8.r2

### g8.r2.g8r2-s1 — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*The leap nobody states:* If a short handle is wanted on the block and a helper plus a length constant exist for producing it, then the block must be built with that handle already filled in from the payload it was built from.

- **gideon** (2025-05-02, #pipeline): honestly though, I'm diffing two 200-line base64 blobs in the log just to tell if it's the same picture agian. want a short handle sitting on the block itself.
- **konrad** (2025-03-17, #engineering): review nit: you added `_ATTACHMENT_FINGERPRINT_HEX_LEN` but `attachment_fingerprint` still slices `12` off the hex by hand in two places. 12 is right, just use the constant in both.
- **nils** (2025-04-22, page:engineering/block-identity-and-cache-keys-for-strategy-recipes.md): i think `fingerprint` has to be required on the block, filled from the payload we already built there. optional is a field half the providers forget to set.
- **dario** (2025-06-17, thread:new|g8.r2.g8r2-s1-l4): i pinned it in a scratch test: the `%PDF-1.4` fixture comes out sha256:fc1c4358d4aa and `Image(content=b"x")` sha256:5e21d86b709b, same every run.

### g8.r2.g8r2-s2 — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*The leap nobody states:* If the digest is taken over whatever string sits in payload and nothing is ever fetched or decoded first, then url blocks and base64 blocks are the same case and no normalising of the url happens before hashing.

- **emil** (2025-03-19, #engineering): my dedupe run yesterday - remote blocks came back with an empty `fingerprint`, inline ones had theirs, so every cdn image counted as new. url-sourced has to be covered too.
- **konrad** (2025-05-27, page:engineering/ws-055-release-engineering-ci-test-suite.md): On the fingerprint rule: for url blocks we are going with A from the review thread, we hash the string we put in the payload, nobody fetches it.
- **dario** (2025-06-11, thread:new|g8.r2.g8r2-s2-l3): on the url ones i think we hash it as given, query and fragment included — `?size=large` and `?size=small` are different pictures, two rows beats one wrong one.
- **dermot** (2025-03-25, #engineering): back on the fingerprint: for the inline ones we hash the b64 text we already hold, decoding a 40mb pdf back to bytes just to digest it is daft

### g8.r2.g8r2-s3 — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*The leap nobody states:* If only the displayed name is too long and the link must stay whole, then the cap applies to the derived filename alone and has to keep the suffix that identifies the file.

- **nikolai** (2025-06-12, page:engineering/attachment-payload-filenames-we-send-to-providers.md): basename on the q4 statements pdf comes out at 73 chars and it blew out the providers filename field  not sending that through as it is
- **gideon** (2025-03-27, #viewer): so basically we cap the name we derive at 64 but keep the extension on the end, a .pdf that loses its tail is useless in the viewer
- **nils** (2025-05-29, page:engineering/viewer-download-row-long-dataset-names-in-the-summary-table.md): only shorten the name we display, not the url. i trimmed the link along with it once and the download 404'd, whole query string gone.
- **dermot** (2025-04-02, thread:new|g8.r2.g8r2-s3-l4): anything at or under `_MAX_ATTACHMENT_FILENAME_LEN` goes through exactly as it came in, no rewriting at all. people grep the logs for those names.

### g8.r2.g8r2-s4 — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*The leap nobody states:* If a fixed set is the only thing the provider accepts and off-vocabulary values must not fail the run, the block copy is the thing that gets fixed and the miss is worth exactly one log line.

- **konrad** (2025-05-13, thread:new|g8.r2.g8r2-s4-l1): Look, the cookbook page still has detail="HIGH" on it and that went straight into the block as HIGH, untouched. two people copied that page this week.
- **dario** (2025-03-20, #engineering): i think normalize_detail should trim and lowercase before it compares — whatever the caller typed stays on the image itself, we only fix the copy that goes on the block.
- **nikolai** (2026-01-23, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): adding a wiki bullet for attachment.py while 690 is still moving the mime helper the fallback filename and now `_SUPPORTED_IMAGE_DETAILS` = auto / low / high thats the accepted set
- **gideon** (2025-03-24, #engineering): so basically if someone puts junk in there we shouldnt kill the run, just fall back to auto and warn once. unset is auto too, silently, no log line.

### herrings — believed at the time, reversed later

- **dario** (2025-02-03): one more from the 427 review while you're in there: detail goes to the provider exactly as the caller wrote it, no lowercasing, no checking it against a list
- **konrad** (2025-02-12): Look, one that's settled: detail is pass-through, whatever string the caller sets is what lands in the request. Validating that vocabulary is the providers job, not ours.

