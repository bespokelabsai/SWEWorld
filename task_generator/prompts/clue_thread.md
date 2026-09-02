Write the conversation in which this team worked something out. Not a conversation
with a fact dropped into it — a conversation that exists *because* they were working
this out.

## What they settle

By the end of the exchange a reader must be able to recover all of this:

```
{{text}}
```

**Do not put that in one message.** A single turn carrying the whole thing is a
person reciting a specification, and it is the tell that gives this away as planted.
Split it: somebody raises the question, somebody answers part of it, the first person
pushes on the part that is still unclear, and the answer completes it. Two speakers
minimum, and no one turn may contain the whole of it.

Every piece has to survive the split, though. Fragmenting is not dropping — if a
detail above ends up in nobody's message, the conversation is worthless to the reader
who needs it.

{{verbatim}}

## The shape

**The decision is settled. The work is not.** By the end of the exchange the team
knows what they are going to do — that is the whole point, and a reader has to be
able to tell. What has not happened yet is somebody writing the code.

Those are different things and the difference is load-bearing. Hedge the schedule if
you like — who picks it up, which ticket it lands on. **Never hedge the substance.**
An exchange that ends "the shape isn't settled", "fields keep moving", "don't write
anything against it yet" tells a reader there is no decision here to find, and the
decision is the only reason this conversation exists.

Nobody reports having finished it and nobody quotes output from a working
implementation. Past tense is right for the *problem* — a run that broke, a file that
came back wrong, something somebody tried — and wrong for the *solution*.

**Do not end on a stock closing line.** Real conversations stop; they do not sign
off.

{{avoid}} Somebody answers, somebody says "yep", the next thing in the channel is about
something else. A closer that would fit under any of these exchanges is a closer that
will appear under all of them, and fifty threads ending the same way is the loudest
tell in the corpus.

{{reversal}}

## The room

`#{{channel}}` on **{{date}}**. These people were posting that week:

{{people}}

### Who speaks — two rules, and they are checked

**1. Every message must be from somebody on that list, spelled exactly as it is
written there.** That list is the whole company. A name not on it belongs to
nobody: it would appear in your four messages and nowhere else in nine months of
chat, and an agent who looks it up finds a person with no history, which is this
generator announcing itself. Never `alex`, never `the on-call`, never a first name
you find natural — the list or nothing. Every message needs an author; a turn with
an empty one is rejected.

**2. At least two different people must speak, and {{holder}} must be one of
them.** Two is the floor, three is better.

These two pull against each other and rule 2 is the one that quietly loses. Told to
stay inside a short list, the easy way out is one person posting six times — and
that is not a conversation, it is somebody thinking out loud with nobody to think
against. It also destroys the point of the exercise: the remark is meant to be
*split across speakers*, so one voice means one turn ends up carrying the whole
thing, which is the tell this rewrite exists to remove.

If the list feels too short for what you want to write: use two of the named people
and give one of them more of the turns. Two people going back and forth four times
is a real conversation. One person posting four times is a monologue and will be
thrown away.

Both are enforced in code after you answer, and an exchange that breaks either is
rewritten from scratch — so there is nothing to be gained by stretching them.

{{nearby}}

Anything under "what else is in that channel that day" is **not part of this
conversation**. It is there so you can tell what the room was already talking about
and write around it. Do not copy those messages, do not merge them in, do not
continue them.

## How they write

{{voices}}

## Rules

- **Five to nine messages, and most of them SHORT.** This is the rule that gets
  broken. Real messages in this company are one-liners: the median is 89
  characters and a quarter of them are under 60 — "right", "yep thats the one",
  "mhm, and the empty case?". A previous run made every turn a paragraph, and 64%
  of them were longer than the 90th percentile of everything else in the corpus,
  which turns a planted thread into a visibly different texture on the page.
  Carry the material in MORE turns rather than bigger ones: a short question, a
  short answer, a short push-back. One or two turns may be long where somebody is
  actually explaining something. The rest should be the length of a reply typed
  without thinking about it.
- Long enough that the question gets asked and answered;
  short enough to be a chat exchange rather than a design document.
- **{{holder}} is in it**, and is the one who settles the point.
- **Never state the requirement as a requirement.** No "we must", no "the rule is",
  no numbered list. These are two or three colleagues talking, and what makes it a
  decision is that somebody says the thing and nobody argues.
- **Nobody summarises at the end.** A closing message that recaps what was agreed
  hands the whole thing back in one paragraph and undoes the fragmenting.
- Same register as the rest of that channel: lowercase, half-finished sentences, the
  occasional typo. Nobody writes well in chat.

Return the messages in order with the author and the minute, plus — for each distinct
piece of the material above — which message carries it.
