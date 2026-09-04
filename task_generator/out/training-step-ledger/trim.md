# g11 — the requirement, reduced to what is graded

**715 words → 505** across 9 facts and 96 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g11.r1.rule` | 133 → 89 | 18 | 5 |
| `g11.r1.scope` | 57 → 34 | 12 | 2 |
| `g11.r1.exclusions_or_crossover` | 58 → 33 | 5 | 3 |
| `g11.r1.failure_behavior` | 71 → 61 | 9 | 2 |
| `g11.r1.observability` | 86 → 79 | 17 | 1 |
| `g11.r2.rule` | 126 → 69 | 14 | 6 |
| `g11.r2.exclusions_or_crossover` | 68 → 48 | 12 | 2 |
| `g11.r2.failure_behavior` | 47 → 32 | 5 | 3 |
| `g11.r2.observability` | 69 → 60 | 4 | 2 |

## `g11.r1.rule`

**Now (89 words):**

`CheckpointInfo` gains a last field `reasons: Tuple[str, ...] = ()`, and `save_checkpoint` gains a keyword-only `reasons: Sequence[str] = ("interval",)`. The vocabulary is exactly three strings held in a module constant `CHECKPOINT_REASONS: Tuple[str, str, str] = ("interval", "epoch", "final")` in `step_ledger.py`, and `canonical_reasons(reasons: Sequence[str]) -> Tuple[str, ...]` deduplicates and orders them by that ledger order. A step that fires several triggers produces exactly one `save_checkpoint` call whose `reasons` is that canonical tuple. The stored `name` comes from `checkpoint_name(prefix, step)` = `CHECKPOINT_NAME_TEMPLATE.format(prefix=..., step=...)` with `CHECKPOINT_NAME_TEMPLATE = "{prefix}-s{step:06d}"`: `checkpoint_name("checkpoint", 2) == "checkpoint-s000002"`.

**Dropped, because no assertion checks it:**

- Opening framing sentence, a why that nothing grades: "A checkpoint carries the trigger vocabulary that produced it."
- The count in "gains a tenth and last field" -- dropped "tenth and"; no assertion counts fields, and #12 only checks `reasons` is last, which "a last field" still states.
- The gloss restating the ordering already fixed verbatim by the `CHECKPOINT_REASONS` literal: "-- `interval` before `epoch` before `final`, NOT alphabetically and not in the order the triggers were noticed."
- The consequence clause derivable from the template literal: "so the step is zero-padded to six digits and names sort lexicographically" (#9 and #11 still follow from `"{prefix}-s{step:06d}"`).
- The second worked example of the name template: "`checkpoint_name("ckpt", 1234567) == "ckpt-s1234567"`" (#10 follows from the template literal, which is kept).

**Kept despite looking like padding:** `checkpoint_name("checkpoint", 2) == "checkpoint-s000002"` reads like a redundant example of the template, but assertions #2 and #9 turn on that exact literal, so the one worked example stays. The `CHECKPOINT_REASONS` and `CHECKPOINT_NAME_TEMPLATE` literals and the `("interval",)` default are verbatim because #1, #2, #14 and #15 read them directly; "exactly one `save_checkpoint` call" stays for #16 and #17.

## `g11.r1.scope`

**Now (34 words):**

The `"final"` trigger fires at `step == plan.total_steps` regardless of configuration. The `"interval"` and `"epoch"` triggers remain conditional on their config fields. Applies to `TinkerTrainer` only; `FireworksTrainer` writes no checkpoints and gains no reasons.

**Dropped, because no assertion checks it:**

- "so every completed run ends with at least one checkpoint" — a consequence clause saying why the rule matters. No assertion checks "at least one checkpoint" as a property; #2, #3, #9 and #10 check exact step lists and reason tuples, which the surviving "regardless of configuration" already forces.
- "even under the default config where `checkpoint_every_n_steps == 0` and `checkpoint_every_epoch is False`" — a worked example of the same rule, naming the default field values. Nothing asserts those literals; the default-config run is graded only through `bare.checkpoints == [3]` and `reasons_of(bare) == [("final",)]`, which follow from "regardless of configuration" plus "the `"interval"` and `"epoch"` triggers remain conditional on their config fields".

**Kept despite looking like padding:** "regardless of configuration" reads like emphasis but is the rule itself: it is what makes the default-config run (#2, #3) and the single-step run (#9, #10) emit a checkpoint at all, and what appends `"final"` to the last epoch checkpoint in #7. "remain conditional on their config fields" is what holds the bare run at `[3]` instead of firing interval or epoch, and separates #4/#5 from #6/#7. The `FireworksTrainer` clause is graded twice — "writes no checkpoints" by #11, "gains no reasons" by #12.

## `g11.r1.exclusions_or_crossover`

**Now (33 words):**

The `epoch` recorded on a checkpoint is `plan.epoch_of_batch(checkpoint.batches_completed)`, never the `for epoch in range(...)` loop variable. A checkpoint whose reasons include `"epoch"` for the end of epoch 1 therefore records `epoch == 2`.

**Dropped, because no assertion checks it:**

- "describes the position, not the trigger:" — a restatement of the rule the colon then states precisely as `plan.epoch_of_batch(checkpoint.batches_completed)` vs the loop variable; nothing reads it
- "at the moment a trigger fired" — timing gloss on the loop variable, no assertion turns on when the trigger fired
- "when the window carrying epoch 1's last batch closed inside epoch 2" — the why behind the `epoch == 2` result; the example's value is already pinned without it

**Kept despite looking like padding:** The whole second sentence reads like a worked example of the first, but it is the only place the requirement says a checkpoint's reasons can contain `\"epoch\"`, which assertion #2 checks directly (`assert \"epoch\" in read_field(checkpoint, \"reasons\")`), and it is the only place the off-by-one is made concrete (epoch 1's trigger records 2), which assertion #5 checks as `!= [1, 2, 3]`. The identifiers `plan.epoch_of_batch` and `checkpoint.batches_completed` stay verbatim because assertion #4 compares against `plan.epoch_of_batch(b)`.

## `g11.r1.failure_behavior`

**Now (61 words):**

`canonical_reasons` raises `StepLedgerError` on any string outside `CHECKPOINT_REASONS`. A repeat `save_checkpoint` under a name equal to the last entry of `self._checkpoints` replaces that entry in place — merging both reason tuples through `canonical_reasons` and taking the new `loss`: `save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))` then the same name with `loss=0.25, reasons=("final",)` leaves `len(trainer.get_checkpoints()) == 1`, `reasons == ("interval", "final")`, `loss == 0.25`.

**Dropped, because no assertion checks it:**

- — `canonical_reasons(("periodic",))` raises": a worked example of the rule stated immediately before it. Assertions #1-#3 check only that `StepLedgerError` is raised; no assertion turns on which string triggered it, and "any string outside `CHECKPOINT_REASONS`" already tells an implementer to reject `"periodic"`.
- "instead of appending a second record": a restatement of "replaces that entry in place" in different words. The behavior it describes is graded by `len(stored) == 1` (#4), which the surviving clause and the worked example already pin.

**Kept despite looking like padding:** The two-call worked example reads long, but every literal in it is graded and nothing in it could go: `save_checkpoint("checkpoint-s000002", step=2, epoch=2, loss=0.5, reasons=("interval",))` supplies the name asserted in #9 and the first reason of the merge in #5/#7; the follow-up supplies `0.25` (#6, #8) and `("final",)` (#5, #7). The phrase "a name equal to the last entry of `self._checkpoints`" also had to stay: #9 asserts `["checkpoint-s000002", "checkpoint-s000003"]`, so a non-matching name must append rather than merge, and only the "last entry" scoping makes that follow.

## `g11.r1.observability`

**Now (79 words):**

For the end-to-end run (10 examples, `batch_size=3`, `epochs=2`, `gradient_accumulation_steps=3`, `checkpoint_every_n_steps=2`, `checkpoint_every_epoch=True`, `seed=0`): `[c.name for c in result.checkpoints] == ["checkpoint-s000002", "checkpoint-s000003"]`, `[c.reasons for c in result.checkpoints] == [("interval", "epoch"), ("epoch", "final")]`, and `[(c.step, c.epoch, c.batches_completed) for c in result.checkpoints] == [(2, 2, 6), (3, 2, 8)]`. `[f.name for f in dataclasses.fields(CheckpointInfo)]` ends `[..., "dataset_signature", "reasons"]` with length 10 and `CheckpointInfo(name="a", path="b", step=1, epoch=1, loss=0.5).reasons == ()`. The default-config fixture of `tests/finetune/test_trainer.py:19-46` yields exactly one checkpoint, `"checkpoint-s000001"`, with `reasons == ("final",)`.

**Dropped, because no assertion checks it:**

- Restatement of the cited fixture's own configuration: "(2 examples, `batch_size=2`, `epochs=1`, no checkpoint options)". The fixture is already located precisely by `tests/finetune/test_trainer.py:19-46`, so these values are the file repeating itself; no assertion reads them. #12, #16 and #17 read `total_steps`, `loss_history` and `final_loss` off that fixture run as it already exists.

**Kept despite looking like padding:** The seven end-to-end config values read like setup padding, but four assertions turn on them and nothing else in the text supplies them: #8 (`[c.batch_size ...] == [3, 3]`) needs `batch_size=3`, #9 needs `gradient_accumulation_steps=3`, #10 (`dataset_signature`) needs the 10-example dataset, and #11 (exact losses 2.304145731814669 and 2.228222171221575) needs `seed=0` together with every other value. `checkpoint_every_n_steps=2` and `checkpoint_every_epoch=True` produce the reason tuples in #5; `epochs=2` produces the epoch column in #6. The path list in #7 is the `mock://checkpoints/` prefix over the names already pinned by #4.

## `g11.r2.rule`

**Now (69 words):**

`learning_rate_at(step, total_steps, base_lr, warmup_steps, *, min_lr_ratio: float = MIN_LR_RATIO) -> float` where `MIN_LR_RATIO: float = 0.1` is a module constant of `step_ledger.py`. With `effective_warmup = min(warmup_steps, total_steps)`, for `1 <= step <= effective_warmup` the rate is `base_lr * step / effective_warmup`. After warmup the rate decays: `progress = min((step - effective_warmup) / max(total_steps - effective_warmup, 1), 1.0)` and `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)`.

**Dropped, because no assertion checks it:**

- "Warmup is **inclusive and 1-based**:" - a label restating what the retained `for 1 <= step <= effective_warmup` specifies exactly.
- "so the step numbered `warmup_steps` is the first step at the full base rate" - a "so" consequence of `base_lr * step / effective_warmup` evaluated at `step == effective_warmup`.
- "and the first optimizer step is never zero" - consequence clause; assertion #5 (`ramp[0] > 0.0`) follows from the retained 1-based ramp formula.
- "**linearly to a floor of one tenth of the base rate**" - prose restatement of `lr = base_lr * (1.0 - (1.0 - min_lr_ratio) * progress)` with the default `0.1`; both survive verbatim.
- "not to zero and not flat" - emphasis by negation of the same decay rule; assertions #6, #9 and #10 fall out of the retained formula.
- "so the floor `min_lr_ratio * base_lr` is reached exactly at `step == total_steps`" - a "so" clause; the retained `progress` expression is 1.0 at `step == total_steps`, which is assertions #8, #11 and #13.

**Kept despite looking like padding:** "is a module constant of `step_ledger.py`" and the literal `MIN_LR_RATIO: float = 0.1` look redundant with the signature default, but assertion #1 looks the name up by symbol (`sym("MIN_LR_RATIO") == 0.1`), so the constant, its value and the module it lives in all had to stay. The signature line stays whole for #2 and #3 (keyword-only kind, default 0.1). Both formulas stay verbatim because every numeric assertion (#4, #6-#14) is computed from them.

## `g11.r2.exclusions_or_crossover`

**Now (48 words):**

Beyond the end of the run the rate is clamped at the floor and does not fall below it or go negative: `learning_rate_at(99, 8, 1e-4, 2) == pytest.approx(1e-05)`. A resumed run whose `epochs` grew continues down the new, longer schedule from `completed_steps + 1` using the same function.

**Dropped, because no assertion checks it:**

- , the same value as `learning_rate_at(8, 8, 1e-4, 2)`" — a second worked example of the same clamp; assertions #1-#5 are already pinned by "clamped at the floor" plus the literal 1e-05 in the surviving example
- "— it does not re-enter warmup and does not restart the decay" — a restatement of "continues down the new, longer schedule from `completed_steps + 1` using the same function", said again in the negative for emphasis; assertions #9-#12 follow from the surviving clause

**Kept despite looking like padding:** "or go negative" reads like belt-and-braces next to "does not fall below it", but assertion #6 (`min(...) >= 0.0`) checks non-negativity across steps 1-199 as its own condition, so the clause stays. "using the same function" also stays because assertion #12 compares the resumed rates against `learning_rate_at(3, 4, BASE, 2)` / `learning_rate_at(4, 4, BASE, 2)` directly.

## `g11.r2.failure_behavior`

**Now (32 words):**

`warmup_steps` greater than `total_steps` is clipped to the run length rather than raising: `[learning_rate_at(s, 3, 1e-4, 10) for s in range(1, 4)] == pytest.approx([1e-4/3, 2e-4/3, 1e-04], rel=1e-12)` — ending exactly at `base_lr`.

**Dropped, because no assertion checks it:**

- "or producing rates below the intended ramp" — a restatement of the clipping rule; the only "not too low" check is `min(clipped) > 0.0`, which the worked example's values already pin.
- "pure warmup," — says again in different words that the whole run is the ramp, which the clipping rule plus the example already state.
- "with no decay segment at all" — the why/consequence of clipping; no assertion checks for the absence of a decay segment except through values the example already fixes.

**Kept despite looking like padding:** "rather than raising" reads like rationale but stays for assertion #4 ("nothing raised") — the call must return rather than error when `warmup_steps > total_steps`. "ending exactly at `base_lr`" stays for #2 and #5: #5 uses `learning_rate_at(1, 1, BASE, 99)`, a case outside the worked example, and only the general "ends at `base_lr`" statement produces it.

## `g11.r2.observability`

**Now (60 words):**

`[learning_rate_at(s, 8, 1e-4, 2) for s in range(1, 9)] == pytest.approx([5e-05, 1e-04, 8.5e-05, 7e-05, 5.5e-05, 4e-05, 2.5e-05, 1e-05], rel=1e-12)`; `[learning_rate_at(s, 4, 1e-4, 0) for s in range(1, 5)] == pytest.approx([7.75e-05, 5.5e-05, 3.25e-05, 1e-05], rel=1e-12)`. In the end-to-end run the three optimizer steps carry `5e-05`, `1e-04`, `1e-05`, and those are the values pushed on `TrainingStats.learning_rate` for the batches of each window.

**Dropped, because no assertion checks it:**

- "With `base_lr=1e-4`:" — a preamble naming a value that already appears as the literal `1e-4` in the third argument of both graded calls, so no assertion loses anything.
- "with no warmup the decay starts immediately," — the reason clause for the second example. "with no warmup" restates the `0` already written in `learning_rate_at(s, 4, 1e-4, 0)`, and "the decay starts immediately" is the why behind the list `[7.75e-05, 5.5e-05, 3.25e-05, 1e-05]`, which assertion #2 grades directly against the literals.

**Kept despite looking like padding:** Both `learning_rate_at` examples look like one rule demonstrated twice, but they are not: assertion #1 grades the 8-step, warmup-2 schedule and assertion #2 grades the 4-step, warmup-0 schedule, each against its own list of literals. Dropping either would leave a graded ordering of exact values unstated. The closing clause "and those are the values pushed on `TrainingStats.learning_rate` for the batches of each window" also reads as a restatement of "the three optimizer steps carry `5e-05`, `1e-04`, `1e-05`", but assertion #4 reads the field name `learning_rate` off `recorder.stats` and grades one entry per batch, not one per step — that clause is what turns three step values into the eight-element list, so it stays. "the three optimizer steps" stays for assertion #3 (`result.total_steps == 3`).
