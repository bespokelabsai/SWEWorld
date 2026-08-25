---
title: "WS-033 design: Code Execution & Verifiers"
author: emil
created_at: 2025-02-10T09:35:00+00:00
---

# WS-033 design: Code Execution & Verifiers

## Problem

Synthetic training data that includes code needs to be verifiably correct, not just syntactically plausible. Without execution and verification we end up shipping rows where the code looks fine but produces wrong output or fails entirely. That degrades model quality downstream in ways that are hard to trace back to the data.

## Approach

Execution and verification are split into two distinct layers deliberately.

The **executor** is a thin wrapper: it takes a code string, runs it in an isolated subprocess with a configurable timeout, and returns stdout, stderr, and exit code. It does not try to interpret whether the output is correct. That is not its job.

The **verifier layer** sits on top and interprets the executor output. Verifiers are pluggable, each one implementing the same interface, and the pipeline supports chaining them. A row passes only if every verifier in the chain returns pass. Default chain is:

- syntax check
- execution (exit code 0, no crash)
- output assertion (stdout matches expected)

Chaining keeps each verifier small and testable in isolation, and lets us add or swap steps without touching the executor.

## Interfaces

Executor:

```
execute(code: str, input: str | None, timeout: float) -> ExecutionResult
```

Verifier:

```
verify(result: ExecutionResult, expected: Any | None) -> VerifierResult
```

VerifierResult carries a boolean verdict and an optional reason string. The reason string is what gets written to the failure log when a row is rejected.

## Key decisions

**Subprocess per call, not per batch.** Each execute() call gets its own subprocess. Overhead is higher per row, but state cannot leak between rows and a bad code sample cannot corrupt the next one. At current volumes this is acceptable. Worth revisiting if throughput becomes a bottleneck.

**Timed-out calls are hard-killed and marked failed, not retried.** Code that times out once will almost certainly time out again. Retrying burns budget and delays the run. If we see a lot of timeouts on a particular generator config, that is a signal to look at the generator, not to raise the timeout.

**Executor failures and verifier failures are tracked separately.** A crash or timeout is infrastructure noise and should not count against data quality metrics. A wrong-output failure is a data quality signal and should. Downstream consumers need to know which is which, so we cannot flatten them into a single "failed" flag.

**No outbound network access inside the sandbox.** Code that needs a live API call to verify is not verifiable in batch, full stop. This is a correctness constraint as much as a security one.

## Open questions

- Should verifier verdicts be stored per-row in metadata.db, or only aggregated at the run level? My instinct is per-row, because aggregates make it hard to rerun just the failed rows. But i dont own the schema, so needs to be confirmed with whoever does.
- What happens when the verifier chain is empty? Pass by default feels dangerous (silent data quality hole). Require at least one verifier feels right to me but may be too strict for early prototyping. Not resolved yet.

## Status

Design complete. Implementation is Nikolai Berresford's under the code-execution workstream.
