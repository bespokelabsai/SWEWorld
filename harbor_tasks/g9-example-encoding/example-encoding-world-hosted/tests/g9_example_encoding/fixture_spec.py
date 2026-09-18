"""g9 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know what
was asked in order to work out what the answer should have been). One derivation,
so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. With a
fixed fixture those values never change — g9's were the same four messages, the
same `max_seq_length=40`, the same 91/51/`[30..38]` every run, and they are
written down in the world the agent is told to read — so a tree that implements
nothing could hardcode a passing `observations.json` from an `atexit` hook.
Re-drawing the conversation, the window and the byte ladder every run means the
answers are not knowable in advance, and the only way to produce them is to run
an implementation that actually applies the policy.

WHAT LIVES HERE, AND WHAT MAY NOT. This file holds the scenario inputs and the
two test-double templates, curator's own tokenizer-free rendering, and nothing
else. The templates and the token geometry they imply are the TICKET's own
(instruction.md specifies the double, the single `encode` call,
`window_start = max(0, len(tokens) - max_seq_length)`, the prefix-tokenization
boundary trick, and at :83 the `<|role|>\n` text and the `len // 4` count of the
tokenizer-free path), so naming them leaks nothing that is scored.
What is scored is the POLICY over that geometry, and every part of it stays in
`judge.py`: that a span beginning before the boundary earns nothing, that the
tokenizer-free path follows the same policy from character offsets, the
retained-prompt floor, the bytes-per-token budget and the strict `>`, and the
report's fields and counters. Nothing here may be expressed in terms of any of
them — which is why, for instance, the Fireworks scenario draws a token budget
and a dense ladder of content lengths INDEPENDENTLY and lets the judge work out
where the cut falls, instead of sizing a line to the budget (that arithmetic
would spell out the bytes-per-token factor for anyone reading this file).

The one input that brushes an answer is `tight_max_seq_length`: a window that
leaves "very little" prompt before the final turn has to be drawn from some
range, and the range says roughly where the floor is without saying what it is.
The scenario that must NOT be refused leaves 22 tokens or more by construction,
this one leaves at most 9, and the number in between is the judge's.

WHY A MOVING FIXTURE IS STILL A REPRODUCIBLE VERIFIER. The inputs vary; the
VERDICT does not, and the verdict is what a grading run produces. Three
properties hold it:

  * **a run is a pure function of its seed.** `random.Random(seed)` is the only
    source of variation in the suite — no clock, no network, no mutable service,
    no hash-order dependence (`run_suites` pins `PYTHONHASHSEED=0` for both
    processes), and the tokenizers are the deterministic doubles the ticket
    itself specifies. Replaying a seed reproduces the run: measured, the same
    seed twice gives a byte-identical `observations.json`, and `derive()` twice
    gives an identical dict.
  * **the judge applies the same policy to whatever was drawn**, so a correct
    implementation passes every draw and an incorrect one fails every draw. The
    reference solution passes all eight facts on 44 distinct random seeds;
    twenty-three deliberately wrong variants each fail exactly one fact, on
    every seed tried; three correct implementations written differently pass
    all eight; a tree that implements nothing scores 0 of 8.
  * **a draw that could not grade a fact is refused, not tolerated.**
    `judge.fixture_defect` evaluates every invariant the facts depend on before
    grading anything — the narrow window really cutting the first assistant turn
    in half, the windowed tokenizer-free example really windowing with its
    boundary in the prompt, the dense window leaving the conversation whole, a
    byte ladder that straddles the budget, a batch with a keep and a drop, five
    role cases that are five different reasons — and, if one fails,
    every fact fails with that one message. Measured over 20,000 seeds: no
    defect, so the gate exists for the draw nobody has seen rather than for a
    known flake. The figures above are recorded in `task.toml`'s
    `verification_explanation`, which is where a reviewer looks for them, and
    what each fact asserts is spelled out in the `judge_*` function that grades
    it — there is no second document to consult.

What a fixed fixture would buy instead is a submission that emits the one set of
observations that has always been correct and implements nothing: measured, and
the reason the seed is here.
"""
from __future__ import annotations

import random

# Letters only, and no look-alikes: a content run ends up in the failure message
# a human reads when a run goes wrong.
_ALPHABET = "abcdefghijkmnpqrstuvwxyz"

# Roles outside ALLOWED_ROLES. Plausible names, because the reason the sequence
# is rejected should not be that the role is obvious nonsense.
_UNKNOWN_ROLES = ("tool", "function", "developer", "observer", "critic")

# One accented character per run, so a serialised line's UTF-8 length runs ahead
# of its character count.
_ACCENTS = "éöüñáîçß"


class TokenizerFailure(RuntimeError):
    """What the raising tokenizer doubles raise, and what must reach the caller.

    instruction.md:36 deletes the `try/except Exception: weights = [1.0] * ...`
    fallback: a tokenizer that raises while spans are computed propagates
    unchanged. "Unchanged" is a claim about the class and the message the caller
    sees, so the class lives here — imported by the doubles in `probe_support`
    and by `judge.py`, which cannot import `probe_support` (that module imports
    curator) and must not hold a second copy of a name it compares against.
    Deliberately neither an `EncodingError` nor a `ValueError`: a submission that
    translates it into one of its own errors has not propagated it.
    """

    MESSAGE = "the tokenizer double failed on purpose"


def render_chat(pairs, add_generation_prompt: bool = False) -> str:
    """`FakeTokenizer.apply_chat_template`: `[role]content\\n` per message, plus a
    bare `[assistant]` header when a generation prompt is asked for.

    Here rather than in `probe_support` because the judge needs the identical
    rendering to know what the untruncated sequence was, and it cannot import
    `probe_support` (that module imports curator). Two copies of a template whose
    exact character counts decide every expected token index would be a bug
    waiting for the first edit.
    """
    text = "".join(f"[{role}]{content}\n" for role, content in pairs)
    return text + "[assistant]" if add_generation_prompt else text


def render_mock(pairs, add_generation_prompt: bool = False) -> str:
    """curator's own tokenizer-free rendering, `<|{role}|>\\n{content}\\n` per message.

    Neither a double nor an answer: it is the text the pristine tree already
    builds, and instruction.md:83 states it outright ("the mock path keeps the
    `<|role|>\\n` template and the `len // 4` token count"). It lives here
    because the windowed tokenizer-free scenario in `derive` has to be SIZED in
    it — a window is a count of tokens, and on this path a token is four
    characters of this text — and because the judge needs the identical
    rendering to know what the untruncated sequence was. What is NOT stated
    anywhere, and stays in `judge.py`, is whether the window and the mask apply
    on this path at all.

    `add_generation_prompt` is accepted and ignored: this path has no generation
    header, and taking the argument keeps the three renderings interchangeable
    where a caller passes one.
    """
    return "".join(f"<|{role}|>\n{content}\n" for role, content in pairs)


def render_short_header(pairs, add_generation_prompt: bool = False) -> str:
    """`ShortHeaderTokenizer.apply_chat_template`: contents only, and a
    one-character generation header, for the cases that need the final assistant
    turn to start very close to the beginning of the sequence."""
    text = "".join(content for _, content in pairs)
    return text + "A" if add_generation_prompt else text


def _run(rnd: random.Random, length: int) -> str:
    """A run of one letter, `'u' * 30`-style: readable in a diff, and one token
    per character under the double."""
    return rnd.choice(_ALPHABET) * length


def _pairs(rnd: random.Random, count: int) -> list:
    """`count` legal user/assistant exchanges, as padding in front of a defect."""
    out = []
    for _ in range(count):
        out.append(["user", _run(rnd, rnd.randint(2, 6))])
        out.append(["assistant", _run(rnd, rnd.randint(2, 6))])
    return out


def _conversation(rnd: random.Random, final: int) -> list:
    """A four-message user/assistant/user/assistant exchange whose final
    assistant turn is `final` characters long."""
    return [["user", _run(rnd, rnd.randint(24, 40))],
            ["assistant", _run(rnd, rnd.randint(8, 16))],
            ["user", _run(rnd, rnd.randint(3, 9))],
            ["assistant", _run(rnd, final)]]


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)

    # --- the conversation the windowing scenarios all use -------------------
    good = _conversation(rnd, rnd.randint(6, 14))

    # Where the template puts things. Ticket geometry, not policy: the total
    # length of the rendered conversation, the index the first assistant turn
    # opens at (the prefix rendered WITH a generation prompt), the index it
    # closes at, and the index the final one opens at.
    total = len(render_chat(good))
    first_open = len(render_chat(good[:1], True))
    first_close = len(render_chat(good[:2]))
    last_open = len(render_chat(good[:3], True))

    # Three windows, described by where their left boundary falls. Given as a
    # max_seq_length, because that is what the formatter takes.
    #   - inside the first assistant turn, never at either end of it;
    #   - in the prompt before the first assistant turn, and never at index 0
    #     (a window that starts at 0 is not a window and grades nothing);
    #   - within a few tokens of the final assistant turn.
    inside = rnd.randint(1, first_close - first_open - 1)
    before = rnd.randint(1, 8)
    close = rnd.randint(0, 9)

    spec: dict = {
        "seed": seed,
        "good": good,
        "good_max_seq_length": total - (first_open + inside),
        "wide_max_seq_length": total - (first_open - before),
        "tight_max_seq_length": total - (last_open - close),
    }

    # An example whose assistant turn alone is longer than the window above, so
    # the window lands past the whole prompt.
    spec["too_long"] = [
        ["user", _run(rnd, rnd.randint(6, 14))],
        ["assistant", _run(rnd, spec["good_max_seq_length"] + rnd.randint(8, 40))],
    ]

    # --- the tokenizer-free path -------------------------------------------
    # A budget far wider than the conversation: this path is about the policy,
    # not the window.
    spec["plain"] = [["user", _run(rnd, rnd.randint(4, 12))],
                     ["assistant", _run(rnd, rnd.randint(6, 16))]]
    spec["plain_max_seq_length"] = rnd.randint(256, 2048)

    # --- the one-character generation header --------------------------------
    spec["short_header"] = [["user", _run(rnd, rnd.randint(2, 5))],
                            ["assistant", _run(rnd, rnd.randint(3, 8))]]
    spec["short_header_max_seq_length"] = rnd.randint(256, 1024)

    # --- the five role sequences, in the ticket's order ---------------------
    # Each is built so that one particular rule is the FIRST one it breaks; the
    # judge works out which reason and which index that is, and also checks that
    # the five are five different reasons, so a degenerate draw cannot quietly
    # grade the same case twice.
    unknown_role = _UNKNOWN_ROLES[rnd.randrange(len(_UNKNOWN_ROLES))]
    spec["role_cases"] = [
        [],
        _pairs(rnd, rnd.randint(0, 2))
        + [[unknown_role, _run(rnd, 3)], ["assistant", _run(rnd, 3)]],
        _pairs(rnd, rnd.randint(1, 2))
        + [["system", _run(rnd, 4)], ["user", _run(rnd, 3)], ["assistant", _run(rnd, 3)]],
        [["system", _run(rnd, 4)]] + _pairs(rnd, rnd.randint(0, 2))
        + [["user", _run(rnd, 3)], ["user", _run(rnd, 3)], ["assistant", _run(rnd, 3)]],
        [["system", _run(rnd, 4)]] + _pairs(rnd, rnd.randint(1, 2)) + [["user", _run(rnd, 3)]],
    ]
    spec["legal_messages"] = _pairs(rnd, 1)
    spec["legal_example"] = [["system", _run(rnd, 5)]] + _pairs(rnd, 1)
    # The malformed batch member: one of the invalid sequences above, so an abort
    # is provoked by a real role error rather than by anything else.
    spec["bad_roles"] = spec["role_cases"][rnd.choice([1, 2, 3, 4])]

    # --- the Fireworks byte ladder ------------------------------------------
    # A token budget, and a dense ladder of contents whose serialised lines cover
    # every length in a band that the budget falls inside whatever the draw. The
    # two are drawn independently ON PURPOSE (see the header): sizing a line to
    # the budget would state the conversion this fact exists to grade. Because
    # the ascii rung lengths are consecutive, one rung always lands exactly on
    # the budget, which is what separates "over" from "not under".
    spec["fw_max_seq_length"] = rnd.randint(34, 46)
    assistant = _run(rnd, rnd.randint(1, 4))
    letter = rnd.choice(_ALPHABET)
    accent = _ACCENTS[rnd.randrange(len(_ACCENTS))]
    padding = rnd.randint(4, 10)
    ladder = [[["user", letter * i], ["assistant", assistant]] for i in range(61)]
    ladder += [[["user", accent * j + letter * padding], ["assistant", assistant]]
               for j in range(1, 26)]
    rnd.shuffle(ladder)
    spec["fw_examples"] = ladder

    # --- the Fireworks report pass -----------------------------------------
    # Well clear of the budget in both directions: which INDICES are dropped is
    # what this pass grades, and it should not turn on the boundary the ladder
    # above already covers.
    spec["fw_report_max_seq_length"] = rnd.randint(40, 60)
    report_examples = [[["user", _run(rnd, rnd.randint(0, 20))],
                        ["assistant", _run(rnd, rnd.randint(1, 4))]]
                       for _ in range(rnd.randint(2, 3))]
    report_examples += [[["user", _run(rnd, rnd.randint(120, 200))],
                         ["assistant", _run(rnd, rnd.randint(1, 4))]]
                        for _ in range(rnd.randint(1, 2))]
    rnd.shuffle(report_examples)
    spec["fw_report_examples"] = report_examples

    # --- the batch pass -----------------------------------------------------
    # Conversations with a short final turn, and examples whose assistant turn
    # alone outruns the window, shuffled together. Which of them survive
    # `good_max_seq_length` is the judge's arithmetic, not this file's.
    batch = [_conversation(rnd, rnd.randint(4, 10)) for _ in range(rnd.randint(1, 3))]
    batch += [[["user", _run(rnd, rnd.randint(6, 14))],
               ["assistant", _run(rnd, spec["good_max_seq_length"] + rnd.randint(8, 40))]]
              for _ in range(rnd.randint(1, 2))]
    rnd.shuffle(batch)
    spec["batch"] = batch
    # The same rows under a budget wider than any of them.
    spec["clean_max_seq_length"] = rnd.randint(600, 1500)

    # --- FireworksDataFormatter.from_config ---------------------------------
    # One context length below curator's default and one above it: the ticket
    # says the configured value wins either way.
    spec["context_small"] = rnd.randint(64, 512)
    spec["context_large"] = rnd.randint(2049, 8192)

    # --- the conversation again, under a tokenizer that is not 1:1 ----------
    # `DenseTokenizer` returns two ids per character, so a token index is NOT a
    # character offset (see probe_support). The window is drawn far wider than
    # any draw of `good` can reach, because this scenario grades where the spans
    # came from and not the windowing the three windows above already grade.
    # Drawn after everything else on purpose: every draw before it is the one
    # that seed always made, so the invariants measured over 20,000 seeds still
    # hold. The scenario below is appended for the same reason.
    spec["dense_max_seq_length"] = rnd.randint(4096, 8192)

    # --- the tokenizer-free path, WINDOWED ----------------------------------
    # `plain` above is drawn far wider than its conversation, so it grades the
    # masking on this path and never the window. That left one half of one fact
    # untested, and it was measured: a tree that windowed the tokenizer path and
    # left this one unwindowed scored every fact while the repository's own
    # `tests/finetune/test_data_formatter.py::test_max_seq_length` — which
    # instruction.md:83 says must still pass — failed on it.
    #
    # The boundary is placed INSIDE THE PROMPT, before the first assistant turn,
    # so what this grades is the window and the mask that follows it, and not the
    # straddle rule the three tokenizer windows already grade: no fact should
    # fail twice for one wrong policy. The third message is long, which is what
    # leaves plenty of prompt in front of the final turn whatever the draw; the
    # judge checks all of that before it grades anything.
    plain_windowed = [["user", _run(rnd, rnd.randint(200, 260))],
                      ["assistant", _run(rnd, rnd.randint(8, 16))],
                      ["user", _run(rnd, rnd.randint(60, 90))],
                      ["assistant", _run(rnd, rnd.randint(6, 14))]]
    spec["plain_windowed"] = plain_windowed
    # A token is four characters of the rendered text on this path, and the first
    # assistant turn opens at least fifty tokens in, so a boundary eight to
    # twenty-four tokens from the left is inside the prompt by construction.
    spec["plain_windowed_max_seq_length"] = (len(render_mock(plain_windowed)) // 4
                                            - rnd.randint(8, 24))
    return spec
