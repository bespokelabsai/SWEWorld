
## What you are being shown

Every remark in this requirement, oldest first — not only the ones filed under
the fact in question. Each is labelled either *filed under this fact* or with
the facts it is filed under and the source it lives in.

**Read all of them before calling anything a conflict.** A remark that settles
the point may be filed under a sibling fact, or live in mail or the wiki rather
than in chat, and `covers` is truncated to two entries so it is not a reliable
index of what a remark carries. A statement is only a conflict if nothing later
in this list — from ANY source — puts it right.

You are reading a company's chat, wiki and mail the way a new engineer would: in
date order, with no answer key, trusting what people say.

Below is one thing the team really decided, and every remark in the corpus that
touches it. Your job is to find remarks that would lead that reader to the WRONG
conclusion.

## What they actually decided

```
{{requirement}}
```

## Every remark that touches it, oldest first

{{remarks}}

## What counts

A conflict is a statement a reader would take as **an answer to this same
question**, that differs from the decision above. It does not have to contradict
it word for word — an aside that pins the value in passing counts, and counts for
more, because nobody argues with an aside.

The one that prompted this check read:

> "so the cut takes from both ends: first 16k, last 48k"

against a decision that the head gets three quarters and the tail one. Every
number in it appears in the real decision. Their roles are swapped. That is the
shape to look for: not a wrong number, a wrong sentence.

**Not conflicts:**

- A remark that is partial. Saying "we keep both ends" without giving the split is
  the design working — each remark is meant to carry a piece.
- A remark that raises an option and is answered in the same conversation. People
  think out loud; the thread settling it is the point.
- Colour. Log sizes, row counts, byte totals from somebody's terminal. Those pin
  nothing.

**`reversed_by`** is for a LATER remark that plainly overturns an earlier one:
somebody names the old decision, says it is gone, and says what replaced it. A
remark that merely states the truth, without referring to the wrong one, is NOT a
reversal — a reader who sees both has no way to know which is current, and that
is exactly the failure this check exists to find.

Return one row per conflict, and nothing for a decision the corpus states
consistently.
