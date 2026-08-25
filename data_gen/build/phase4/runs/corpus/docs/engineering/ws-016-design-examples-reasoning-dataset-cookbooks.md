---
title: "WS-016 design: Examples & Reasoning-Dataset Cookbooks"
author: dario
created_at: 2025-01-06T09:56:00+00:00
---

# WS-016 Design: Examples & Reasoning-Dataset Cookbooks

## Scope

WS-016 owns the examples-cookbooks surface: runnable examples shipped alongside curator, reasoning-dataset pipelines built on top of them, and the verifiers that confirm code execution produces correct output.

In scope:
- Runnable cookbook examples (one file per use-case, self-contained, no hidden deps)
- vLLM offline inference examples, once the offline processor integration lands
- Reasoning-dataset pipeline templates that wrap a cookbook into a full curator run
- Code-execution verifiers (assert-based, not LLM-judged) that gate dataset quality
- README and index structure that surfaces all of the above

Deferred (not this release):
- Fine-tuning handoff: the boundary between a curated dataset and a training job. Blocked on the finetuning workstream starting, which hasnt happened yet.
- Agentic curation examples: depend on agentic-curation, which doesnt exist yet.

---

## Example Structure

Each example is a single Python file under `examples/`. It imports curator, defines a prompter or dataset class, runs a small curator job, and either prints or saves output. Two rules:

- No example requires credentials beyond what the env file provides
- No example should take more than a few minutes on a small sample (I'd say 5 min as a soft ceiling but havent formalized that)

Cookbooks that exercise a specific provider live in a subdirectory named for that provider, so `examples/vllm/`, `examples/anthropic/`, etc. The flat `examples/` root is for provider-agnostic stuff.

Each example file carries a module-level docstring. First line is the title, second paragraph is the description. The index generation script (see README section below) reads these, so the format needs to be consistent or the script breaks silently.

---

## Reasoning-Dataset Pipelines

A reasoning-dataset pipeline is a cookbook that produces a JSONL dataset suitable for fine-tuning. The structure is fixed across all pipelines:

1. Define the prompt structure (question, chain-of-thought, answer)
2. Run curator over a seed set
3. Pass each row through a code-execution verifier
4. Write surviving rows to a JSONL file

The verifier step is the distinguishing piece. A plain cookbook doesnt have it. Verifiers are plain Python functions: given a row dict, return True or False. They live in `examples/verifiers/` and are imported by the pipeline, not embedded in it. This keeps the pipeline files readable and lets verifiers be shared across pipelines.

I want to be clear that verifiers are assert-based, not LLM-judged. LLM-as-judge is not happening here. The point is deterministic quality gating, which is the whole reason to have verifiers at all. If a row cant be verified with code, it probably shouldnt be in a reasoning dataset anyway, but I expect there will be edge cases and we'll need to decide what to do with them. Open question for now.

---

## vLLM Integration

vLLM examples are blocked on the offline processor interface stabilizing. That work is owned by Emil Brandvold under the local-offline-inference workstream, not by WS-016.

Once the interface is settled, WS-016 adds:
- A vLLM provider example showing basic offline inference
- A vLLM reasoning-dataset pipeline that runs the full pipeline locally

The interface contract: the vLLM example imports from curator, not from vLLM directly. curator's provider layer owns the vLLM dependency. If an example is reaching into vLLM internals directly thats a bug in the example.

Timing-wise, this is not gating the release, but should land in the same milestone if Emil's side moves fast enough. Need to stay in sync with him on that.

---

## README and Index

The main README lists every example with a one-line description and a link. The index is generated, not hand-maintained.

The generation script reads module-level docstrings from each example file and writes the README section. This means:
- Adding a new example automatically shows up in the index (once you run the script)
- The docstring format has to be right or the entry is malformed

Hand-maintaining the list is the current state. The generation script is new work for this release. There is a question (see below) about whether the script itself lands this release or we defer it and keep hand-maintaining for now.

---

## Open Questions

- **README generation script:** new work, is it in scope for this release or do we keep hand-maintaining the list? I lean toward shipping it because manual maintenance will immediately fall behind, but decision should happen before we cut the release.
- **vLLM example timing:** blocked on Emil's offline processor interface. Not a gate, but the longer it slips the more likely it misses the milestone.
- **Rows that cant be code-verified:** what do we do with them? Silently drop, log and drop, or allow a passthrough flag per pipeline? Havent decided.

---

## Non-Goals

- WS-016 does not own the offline processor (local-offline-inference, Emil Brandvold)
- Does not own the curator viewer or any UI surface
- Does not own fine-tuning infrastructure, just the handoff boundary (and even that is deferred)
