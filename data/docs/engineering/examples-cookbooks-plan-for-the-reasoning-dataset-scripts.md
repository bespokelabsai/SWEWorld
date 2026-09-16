---
title: "Examples & Cookbooks: Plan for the Reasoning-Dataset Scripts"
author: dermot
created_at: 2024-11-08T13:57:45+00:00
---

# Examples & Cookbooks: Plan for the Reasoning-Dataset Scripts

## What we are building

Three distinct layers, each with a clear owner and a clear output.

- **Runnable examples**, self-contained scripts, clone and run against a live curator endpoint
    - each targets one real use case (batch inference, multimodal prompts, provider swap, etc.)
    - must produce actual output, not stubs or placeholder calls
- **Reasoning-dataset pipelines**, the scripts that move a curated dataset through the multi-step reasoning scaffold
    - steps: prompt assembly -> LLM call -> response parsing -> trace capture
    - every row in the final corpus needs a provenance record from these scripts (this is the "receipts" requirement for Millrow)
- **Code-execution verifiers**, lightweight harnesses that check a generated response against a ground-truth signal
    - unit test pass/fail, schema match, numeric tolerance (those are the three cases i have confirmed so far)
    - called by the pipeline scripts, not by the user directly

## Scope for this milestone

**In**

- [ ] one end-to-end pipeline script, canonical reasoning-dataset shape: single-turn, one provider, structured output
- [ ] verifier interface (inputs, outputs, error contract) + one reference implementation
- [ ] at least two runnable examples covering distinct curator feature surface
- [ ] README that lets a new engineer reproduce any example from scratch, no prior context assumed

**Out**

- multi-provider routing, provider-integrations workstream not yet started
- fine-tuning handoff scripts, finetuning workstream not yet started
- agentic or multi-turn pipeline variants

Nothing in scope here should depend on either of those two workstreams landing first.

## Delivery shape

All deliverables live in the examples-cookbooks service. No new top-level services.

Scripts are plain Python. No framework beyond curator itself. Each script carries a `, dry-run` flag that validates inputs and prints what it would do, without spending tokens or writing output. I want this flag there from day one, not retrofitted.

The verifier interface is a single function signature:

```
verify(response: str, ground_truth: Any) -> VerifierResult
```

Implementations are one file per verifier, under a `verifiers/` subdirectory. The reference implementation for this milestone will be the schema-match case, because that is the one the pipeline script actually needs to run end-to-end.

## Timeline

```
Oct 31  kickoff, repo skeleton in place, verifier interface merged
Nov  7  first pipeline script runnable end-to-end, one verifier implementation done
Nov 14  second example, README, milestone close
```

Oct 31 is tomorrow so the skeleton and interface need to be ready to show at the kickoff, not drafted.

## Open questions

- Which two examples? Candidates i have in mind: structured output vs. free-form, and single-provider vs. explicit provider argument. I lean toward structured output + explicit provider argument because they cover more of the API surface with less overlap, but this decision needs to be made at the kickoff.
- Verifier output format: sidecar file next to the output, or structured JSON to stdout only? No strong preference on my end. That said, it affects how the pipeline scripts consume the result so we cant leave it open past Oct 31. Need whoever is writing the pipeline script to weigh in.

## TBD

- Exact shape of VerifierResult (fields, error states), i have a draft but want one more pair of eyes before it merges
- Who owns the README? I assumed the person who writes the second example, but not confirmed
