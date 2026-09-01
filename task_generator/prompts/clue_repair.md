An engineer read this company's chat, wiki and mail, built what they thought the
team had settled, and got one thing wrong. You are fixing the remarks, not the
engineer.

## What the team actually settled — {{req_id}}, {{field}}

{{fact}}

## What the remarks currently say about it

{{leaves}}

## Everything else this requirement's remarks say

A reader meets all of these, in date order, and takes the latest word as the settled
one. If one of them points away from what the team actually settled, that is the
defect — say so by rewriting it, even though it is not listed above.

{{others}}

## What the engineer built from them, and how it failed

```
{{failure}}
```

That is the measurement. The information is missing, or it is there in a form that
reads as something else — a name used as a noun when it had to be a function, a
value nobody connects to the thing it is a value *of*, a chain of reasoning with a
step nobody says out loud.

## What to write

Return rewrites of the remarks above, and at most one new remark if no existing one
can carry the missing piece without becoming a specification.

Everything that made these remarks work has to survive:

- **One or two sentences, under thirty words**, in that person's own voice. Look at
  how they already write above and keep it — the typos, the lowercase, the way they
  open.
- **Never state the conclusion.** The remark is evidence. If you find yourself
  writing "which means" or "so we should", stop at the observation.
- **A remark answers something.** Each one below is already sitting in a real
  conversation; a rewrite has to still make sense as a reply to what was around it.
- **Identifiers appear literally.** If the fix is that a name was missing, the name
  goes in the text, character for character, and into `verbatim`.

And the thing that failed:

- **Do not put the whole missing piece in one remark.** Split it the way the rest of
  the tree is split — one person notices the thing, somebody else, elsewhere, says
  what it is called or what it produced. Two halves that only add up when a reader
  has both is the point of the exercise; a single remark that settles the fact on
  its own has made the task easier than the spec arm.
- If the failure is a name the engineer chose differently, somebody has to have
  typed that name. The natural way is a person quoting it from something they ran:
  the traceback they pasted, the field they read, the attribute they went looking
  for and found missing.
- If the failure is a step nobody says, the step is usually the boring middle: what
  was done TO the thing that was described. Give it to whoever would have done it.
- **Never write a remark that contradicts the settled thing.** A remark that is
  wrong on purpose is a herring, herrings are planted separately, and one dated
  after the remark it contradicts simply overwrites it in the reader's head.

A new remark needs a `holder` from the roster and a `source` it can appear in:

{{roster}}
