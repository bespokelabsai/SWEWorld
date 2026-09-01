You are DELETING from a hidden requirement. You are not rewriting it.

Nothing about this task is scored except the assertions below. Everything the
requirement says beyond them is weight an implementer carries for no credit, and a
claim somebody has to be made to say in a corpus of chat and wiki pages for no
credit either.

## The requirement as it stands — {{key}}, {{words}} words

{{fact}}

## The {{count}} assertions that grade it

These are the whole of what is checked. Fixture guards are already excluded, so
every one is a real design decision somebody had to get right.

{{claims}}

## What to return

**The same text with material removed.** Keep the surviving sentences in their
original wording and their original order. This is a red pen, not a redraft.

**Your answer MUST be shorter than {{words}} words.** A longer answer is thrown away
and the original is kept, which wastes the call. Aim for {{target}} or fewer.

**"Unchanged" is a correct answer.** Some of these facts are already at their floor
— a 27-word sentence naming three files and a rule has nothing to give. If nothing
can go, return the text exactly as it is and say so in `dropped`.

### Delete

- The sentence that says *why*. A reason is never asserted.
- Clauses opening "because", "so that", "which means" — unless the clause is the
  rule itself.
- The second and third worked example demonstrating a rule one example already pins.
- Restatements: the same rule said again in different words for emphasis.
- History, rationale, and anything the ticket already states.

### Never touch

- **Exact names, values and orderings.** They are what is graded. Never paraphrase
  an identifier, never round a number, never reorder a key list, never turn
  `json.dumps(plan_document(plan, limits), indent=2)` into a description of it.
- The one worked example where an assertion turns on a literal — a digest, an exact
  document, an exact directory listing.
- Anything an assertion reads. If a test reaches for a name, a value or an ordering,
  the requirement keeps stating it precisely enough that an implementer produces
  exactly that.

### Do not

- **Do not add a "worked example" section, a bulleted list, or a restatement of an
  assertion.** Turning a 27-word sentence into 100 words of bullets that say the
  same thing is the exact failure this prompt exists to prevent. Prose that mirrors
  the assertion list is not a trim, it is a transcription.
- Do not convert specification into summary. "Records the plan" is a summary;
  "writes `json.dumps(...)` to `os.path.join(self.working_dir, PLAN_FILE_NAME)`" is
  the specification, and it stays.

List what you deleted, one entry per thing, quoting the words you removed — so a
reader can check that nothing graded went with them.
