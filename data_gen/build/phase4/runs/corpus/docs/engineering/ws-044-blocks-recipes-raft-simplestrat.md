---
title: "WS-044: Blocks & Recipes (RAFT, SimpleStrat)"
author: emil
created_at: 2025-03-07T09:14:00+00:00
---

# WS-044: Blocks & Recipes (RAFT, SimpleStrat)

blocks-and-recipes is the layer that sits between a user-supplied recipe (a declarative description of what rows to generate) and the actual LLM calls. This workstream adds two named strategy implementations and nails down the shared interface both must satisfy.

## Context

A recipe declares *what* to generate. The blocks layer decides *how* to generate it. Before this workstream, there was no first-class strategy concept; generation behavior was implicit in which code path got invoked. That made recipes harder to read and made it easy to get surprising behavior when defaults changed.

RAFT and SimpleStrat are the first two strategies. They cover the two cases we have actual demand for right now.

## RAFT

RAFT (Retrieval-Augmented Fine-Tuning) structures output as `(question, context_docs, chain_of_thought, answer)` tuples. The point is to produce data suitable for fine-tuning a model to reason over retrieved documents, not just to answer questions from memory.

**Schema additions (PR 571, merged)**

- RaftBlock wraps a document corpus field and a question template
- emits one row per `(question, distractor_set)` pair
- generation params:
  - `num_distractors` (int, default 1)
  - `p_gold_doc` (float, default 1.0), probability the gold doc is included in the context window alongside the distractors
- `chain_of_thought` is a required output field; rows missing it fail validation at the cost-processor boundary and are dropped

**Cost accounting**

Token estimates go through the existing cost processor. RaftBlock reports input tokens per distractor doc, so the per-row estimate scales with `num_distractors + 1`. If you set `num_distractors` to something large, the cost estimate will look alarming, which is correct behavior.

**Open question on num_distractors**

Currently `num_distractors` can be set at the recipe level (block config) or per-request (generation params), and the per-request value wins when both are present. I'm not sure this is right. Having it be per-request means two calls from the same recipe can produce structurally different rows, which makes cost estimation harder to reason about and could produce inconsistent training data. My preference would be to pin it to block config and not allow per-request override, but i want to check with whoever owns the cost-processor integration before we change it.

**Failure behavior on missing CoT**

If the model returns an answer without a chain_of_thought field, the row is silently dropped. This is strict and i think it might be wrong. Silent dropping means a recipe run can finish with fewer rows than expected and nothing surfaces as an error. If i had to guess, most people would not notice until they looked at output counts. Should probably be a logged warning at minimum, maybe a hard error depending on what the caller wants. Leaving this open for now, see questions section.

## SimpleStrat

SimpleStrat is a thin wrapper for single-prompt, single-response generation. One LLM call per row, no retrieval, no distractor logic.

It exists because recipes need a way to declare their strategy explicitly. A recipe that omits the strategy field and relies on defaults is ambiguous when defaults change. A recipe that says `strategy: simple` is unambiguous.

**Interface**

- SimpleStratBlock takes a prompt template and an optional output schema
- `strategy: simple` in a recipe routes to this block
- no other configuration required

This is the common case. Most recipes in the current corpus would use this if they were written today.

## Shared Interface

Both blocks satisfy BaseBlock:

- `generate(row: dict, params: GenerationParams) -> dict`, returns the completed row
- `estimate_tokens(row: dict, params: GenerationParams) -> TokenEstimate`, called by the cost processor before any LLM call

Retry logic is not part of the interface. That is the caller's responsibility, either bulk-llm-inference or online-request-processing depending on which execution path is active. The blocks themselves do not retry.

## Status

- [x] RAFT schema changes merged (PR 571)
- [ ] SimpleStrat implementation open in PR 579, not yet merged
- [ ] CoT failure behavior decision (see questions)
- [ ] Confirm `num_distractors` scoping with cost-processor owner

Both implementations are behind the blocks-and-recipes service. No changes to online-request-processing or batch-mode interfaces required.

## Questions

- `num_distractors` as block config vs generation param, currently both, per-request wins. Is that intentional long-term or just how it landed?
- Silent row drop on missing CoT: is that the right failure mode? I think surfacing it is better but dont want to change it unilaterally
- Are there other strategies already being discussed that should inform how BaseBlock is spec'd? dont want to design ourselves into a corner if something like a multi-turn or tree-of-thought strategy is coming soon
