You are deciding where one remark belongs in a company's real history, and adapting
it so it reads as though it was always there.

This company's chat, wiki and mail already exist. Nothing is being re-simulated. You
are looking at conversations that actually happened and choosing whether this remark
could plausibly have been part of one of them.

## The remark

**{{holder}}** would say, in substance:

> {{text}}

It is meant to leave the reader knowing: *{{settles}}*

What it must NOT resolve on its own — a sibling remark elsewhere supplies this:
*{{leaves_open}}*

{{verbatim}}

## How {{holder}} writes

{{voice}}

## Where it could go

{{candidates}}

## The question

**Could this remark realistically have been made in one of those places?**

Not "is it on topic" — whether a reader who knows this company would believe it was
always there. Concretely:

## The rooms, and what each is for

{{channels}}

**The room has to make sense for the remark, not merely contain matching words.**
This is a judgement about subject, not vocabulary: a decision about tokenizers and
loss masking belongs where people argue about training code, not in the room for
runnable examples because both mention "the cookbook". If none of the candidates
below sits in a room where this remark would plausibly be said, answer `none` and
name the channel it should be invented in — that is what `none` is for, and an
invented conversation in the right room is worth more than a real one in the wrong
room. Pick that channel from the list above, by its purpose.

- Is the room already chewing on something this answers or complicates? A remark
  that contributes to a live discussion belongs. One that arrives from nowhere,
  changes the subject, and gets no reaction does not.
- Would **{{holder}}** have been the one to say it, there, that day?
- Does anything already said make it redundant, or contradict it? If somebody has
  already made this point, the remark cannot also make it.
- For a page **section**: could this sentence have been in that document when it was
  written, in that author's voice, under that heading? Only its own author adds a
  section — a paragraph appearing under somebody else's name is the most visible
  kind of plant.
- For a page **comment**: a comment is signed by whoever leaves it, so it keeps
  **{{holder}}**'s voice, not the page author's, and it reads as somebody responding
  to what the page says — picking up a specific line, correcting it, or adding what
  the page left out.

**Choosing none is a real answer.** If no listed place fits, say so and describe the
conversation or document that should have existed instead — who was in it, what
prompted it, what else it would have been about. A remark forced into a room where
it does not belong is more visible than a new conversation that makes sense.

**And the place has to be about the same work the remark is about.** A document
about a neighbouring feature will pass every test above — the words match, the
author is right, the argument is live — and still lose the remark, because a
reader takes what a page is about as what a remark in it is about. A rule for how
this feature's file is serialised, planted in a page about a different feature's
file, is read as that other feature's rule and skipped. Measured: three of one
task's four page carriers were batch-mode documents, one of them invented for the
purpose, and the rollout that found them wrote "this discussion is a different
path … not directly related to the ticket" and scored zero on that requirement
while scoring full marks on the one whose pages were about the right feature. If
you invent a document, its subject is this work, not the work next to it.

## Adapt the wording

Return the remark as it would actually have appeared in the place you chose:
picking up the thread, answering the person above, using the words that room uses.

Three things must survive the rewrite:

1. **Everything it says.** You may change how it is said, never what. If the remark
   reports a symptom and a cost, the rewrite reports both.
2. **Every identifier listed above, character for character.** It is graded by
   name: a reader who never sees the token cannot produce it. If the smoother
   sentence cannot hold it, keep the identifier and lose the smoothness — a rewrite
   that drops one is thrown away and the original wording is planted instead.
3. **One sentence, two at the absolute most, under thirty words.** Never state the
   whole requirement — that is the arm this one is measured against. But if the
   remark states one settled decision, it keeps stating it: this instruction used to
   say "stop at the observation", and what came back was a corpus of people noticing
   things and nobody deciding anything, which a reader can read end to end and still
   not know what to build. Do not spell out what follows from the decision either;
   "which means" and "so we should" are still somebody else's job.

And it must not read as written for a reader. It is one person typing quickly.
