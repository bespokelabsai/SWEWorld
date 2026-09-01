{{brief}}

---

## The company these remarks belong to

{{company}}

## The feature, as the agent will be told it

**{{title}}**

{{description}}

## The hidden requirement you are building remarks for — {{req_id}}

{{requirement}}

{{reversed}}

## Names nobody can infer

A reader can work a rule out from evidence. Nobody can work out a **name** that was
never typed. These are graded literally — the tests reach for them by name, and a
solution that gets the whole idea right under a name of its own scores zero:

{{names}}

Every one must appear character for character inside the `text` of at least one
leaf, and that leaf must list it in `verbatim`.

Saying a name is not the same as writing the requirement down. A name is a token;
what keeps it a clue is that the remark says the name and leaves what it *means* to
a sibling remark. Somebody mentioning `plan_document` in passing has given the
reader a word, not a specification.

Spread them. No remark carries more than two, and the remarks that carry them
belong to different subconclusions, different people and different days wherever
the ground allows. A single message reciting six names is the answer key.

Ways a name really does turn up in a company's chat, wiki and mail — use these, not
a person announcing an interface:

- pasting the line that broke, error text and all
- quoting a review comment, an old ticket, or somebody else's message by its symbol
- a wiki bullet listing what a file holds, written while the shape was still moving
- naming the file, the key or the field they were looking at when it surprised them
- correcting how somebody else spelled it, in passing

## Values a reader has to arrive at

{{values}}

These need not be printed. A reader may reconstruct them instead — but then
something must make that possible: the string that was hashed, how much of the
digest was kept, the number that was chosen. If nothing in your remarks gets a
reader to the value, the fact scores zero for a solution that understood
everything else.

{{defect}}

## Who can say things, and where

These are the only people who exist. Each line is a persona id, how they write, and
the rooms they actually posted in during the period.

{{roster}}

Sources available for this requirement: **{{sources}}**
(`slack` = a channel conversation, `notion` = the wiki, `email` = internal mail.)

The corpus runs {{span}}.

## What to return

A tree in the schema you were given: subconclusions, and the leaves that imply them.

Two to four leaves per subconclusion, **never one**, and give each to somebody who
owns that ground. Aim for three or four subconclusions that together add up to the
whole requirement and nothing more.

`covers` names which parts of the requirement each leaf carries — at most two.
Across all leaves, every part listed above must be carried by at least one.

`verbatim` lists the identifiers a leaf's own text contains literally. It is the
only thing that protects a name between here and the corpus: a leaf claiming one it
does not contain is thrown out, and so is any later rewrite that loses one.
