# t3.r1 — Batch job status persistence across process restarts

## The hidden requirement

- **rule** — The batch job ID must be persisted to the on-disk cache directory (keyed the same way as the existing prompt cache) immediately after successful submission, before polling begins, so a crash during polling doesn't lose the ability to resume.
- **scope** — Batch job ID persistence, submission-time only.
- **failure_behavior** — If persistence itself fails (disk full, permissions), the batch submission must still be allowed to proceed — losing resumability is preferable to blocking the job outright, but a warning must be logged.

13 of 13 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [L1](L1.md) | yes | dario | #pipeline | SC1 |
| [L10](L10.md) | yes | emil | #code-review | SC3 |
| [L11](L11.md) | yes | dario | mail:mail-t1-plant | SC3 |
| [L2](L2.md) | yes | emil | #cookbooks | SC1 |
| [L3](L3.md) | yes | emil | mail:mail-t3-plant | SC1 |
| [L4](L4.md) | yes | dermot | page:design-ws-055-release-and-ci | SC1 |
| [L5](L5.md) | yes | dario | #pipeline | SC2 |
| [L6](L6.md) | yes | emil | page:design-ws-050-batch-mode | SC2 |
| [L7](L7.md) | yes | gideon | #viewer | SC2 |
| [L8](L8.md) | yes | emil | mail:mail-t3-plant | SC2 |
| [L9](L9.md) | yes | dario | #incidents | SC3 |
| [h1](h1.md) | yes | dario | #code-review |  |
| [h2](h2.md) | yes | emil | #code-review |  |
