# t4.r2 — Docker code executor image pinning

## The hidden requirement

- **rule** — When a caller overrides the image via `backend_params={'image': ...}`, the executor must still enforce the same non-root user and read-only filesystem mount constraints applied to the default pinned image — an overridden image must not be allowed to run as root inside the container even if the custom image's own Dockerfile defaults to root.
- **scope** — Security constraints applied regardless of which image is used.
- **failure_behavior** — If the enforced non-root/read-only settings are incompatible with a custom image (e.g. it requires root), the container must fail to start with a clear error, not silently run with elevated privileges.

12 of 12 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [L1](L1.md) | yes | nikolai | #code-review | S1 |
| [L10](L10.md) | yes | dario | #pipeline | S4 |
| [L11](L11.md) | yes | gideon | #viewer | S4 |
| [L12](L12.md) | yes | nikolai | mail:mail-t4-plant | S4 |
| [L2](L2.md) | yes | konrad | mail:weekly-2025-01-13 | S1 |
| [L3](L3.md) | yes | dermot | #code-review | S1 |
| [L4](L4.md) | yes | dario | #cookbooks | S2 |
| [L5](L5.md) | yes | nikolai | #code-review | S2 |
| [L6](L6.md) | yes | nikolai | mail:mail-t4-plant | S2 |
| [L7](L7.md) | yes | nikolai | #code-review | S3 |
| [L8](L8.md) | yes | dermot | #code-review | S3 |
| [L9](L9.md) | yes | nikolai | mail:mail-t4-plant | S3 |
