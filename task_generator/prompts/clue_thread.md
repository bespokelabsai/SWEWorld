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

**Only these people may speak, and every message must name one of them.** They are
the whole company. Inventing a colleague is the most visible plant this generator
can produce: a name that appears in four messages and nowhere else in nine months
of chat is somebody an agent can look up and fail to find. If a conversation seems
to need a fourth voice, use one of the people above twice or write a shorter
exchange.

{{nearby}}

Anything under "what else is in that channel that day" is **not part of this
conversation**. It is there so you can tell what the room was already talking about
and write around it. Do not copy those messages, do not merge them in, do not
continue them.

## How they write

{{voices}}

## Rules

- **Four to seven messages.** Long enough that the question gets asked and answered;
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
