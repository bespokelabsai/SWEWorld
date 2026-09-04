Write the mail exchange in which this team settled something. Not a chat thread with
addresses on it — mail, which people write differently from how they talk.

## What they settle

By the end of the exchange a reader must be able to recover all of this:

```
{{text}}
```

Unlike a chat room, mail does **not** want this broken into fragments. A person
writing mail composes: they set out the situation, make their point, and stop. Put
the substance in whole paragraphs. Two or three messages is a normal exchange and is
usually enough; more than four is a thread that would have moved to chat.

{{reversal}}

## How mail actually reads

- **It opens and closes.** A greeting by name, and a sign-off. Not every reply needs
  both — a fast reply down the chain often has neither — but the first message does.
- **It is more formal than chat and less formal than a document.** Full sentences.
  No `lol`, no bare `yeah`, no one-word turns, no emoji, no `@name` pings.
- **It carries context the reader may not have**, because mail is often read hours
  later by someone who was not in the room. A chat message can assume the last ten
  minutes; a mail cannot.
- **A reply quotes or names what it answers** — "on the window question", "re the
  second point" — rather than relying on adjacency.
- **Subjects are a sentence fragment**, not a title: "batch pricing on the klusterai
  window", not "Batch Pricing Discussion".
- Paragraphs, not bullet-fragments, unless the writer is genuinely enumerating.

## Who is writing

**{{holder}}** is the person who has to make the point above; the exchange is on or
about {{date}}. Others who might be on it: {{people}}

{{voices}}

Those voices describe how these people write. Mail flattens a voice somewhat — the
person who types in lowercase fragments in chat still capitalises in mail — so read
them for vocabulary and stance rather than for punctuation.

## Context

{{nearby}}

{{verbatim}}

{{leave}}

{{avoid}}

{{defect}}

## Shape of your answer

Return `messages`: each one `speaker` and `text`, in order. The first message is the
one that starts the thread; the rest are replies. Put the subject line as the first
line of the first message, on its own, prefixed `Subject: `. Do not write `From:`,
`To:`, `Date:` or quoted `>` blocks — the world adds those.
