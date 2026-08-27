# t3.r2 — Batch job status persistence across process restarts

## The hidden requirement

- **rule** — On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job.
- **scope** — Resume-time validation.
- **failure_behavior** — Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results.

12 of 12 carried.

| clue | said | holder | where | subconclusion |
|---|---|---|---|---|
| [l_beh_dermot](l_beh_dermot.md) | yes | dermot | #pipeline | sc_behavior |
| [l_beh_emil](l_beh_emil.md) | yes | emil | #general | sc_behavior |
| [l_beh_gideon](l_beh_gideon.md) | yes | gideon | #engineering | sc_behavior |
| [l_model_dermot](l_model_dermot.md) | yes | dermot | #cookbooks | sc_model |
| [l_model_emil](l_model_emil.md) | yes | emil | #pipeline | sc_model |
| [l_model_gideon](l_model_gideon.md) | yes | gideon | #pipeline | sc_model |
| [l_pay_dario](l_pay_dario.md) | yes | dario | #help | sc_payload |
| [l_pay_dermot](l_pay_dermot.md) | yes | dermot | #releases | sc_payload |
| [l_pay_emil](l_pay_emil.md) | yes | emil | #pipeline | sc_payload |
| [l_prov_dario](l_prov_dario.md) | yes | dario | #incidents | sc_provider |
| [l_prov_emil](l_prov_emil.md) | yes | emil | #code-review | sc_provider |
| [l_prov_gideon](l_prov_gideon.md) | yes | gideon | #viewer | sc_provider |
