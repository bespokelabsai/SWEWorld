You are writing the **grading suite** for one implementation task in an agent
evaluation. The suite decides, per requirement, whether an agent recovered a
requirement nobody wrote down. It has to be exact, and it has to be fair.

## What the agent is told openly

{{ticket}}

## The hidden requirements — one test each

{{facts}}

## The full specification, for your reference only

{{whole}}

## The reference implementation

`{{oracle_tree}}` is the golden tree: the whole specification, implemented. Read
it. **Your suite must be green against it before you finish.** Run it with:

```
{{suite_cmd}}
```

That command applies the golden tree and runs your suite in a container that can
import curator. Nothing else on this machine can. Run it as often as you like; it
takes under a minute.

## Files to write

In `tests/` in your working directory, exactly these:

- `test_open.py` — the openly stated feature.
- `test_r1.py` — requirement 1.
- `test_r2.py` — requirement 2.

## Naming, which is how grading works

The grader reads the fact being tested **out of the function name**. Get this
wrong and a passing test scores zero.

- In `test_r<N>.py`, name each function `test_<field>__<short_prose>` where
  `<field>` is one of `rule`, `scope`, `exclusions`, `failure_behavior`,
  `observability` — matching the fields declared for that requirement, and
  nothing else.
- In `test_open.py`, name it `test_open_feature__<short_prose>`.
- **One decisive test per declared field.** If two functions map to the same
  field, the field scores only when both pass — so write one.

## What "decisive" means here

A test is decisive when it **fails on untouched curator** and **passes on the
golden tree**. A test that passes on untouched curator grades nothing: it credits
an agent who wrote no code at all.

For any requirement phrased as something that must NOT change — a preservation
constraint — this is the whole difficulty, because an untouched checkout satisfies
it by doing nothing. Guard those with `harness.require_feature(...)`, which fails
the test unless the feature it depends on actually exists. Three tests in an
earlier task scored full marks on an empty checkout for exactly this reason.

## What you may import

From the shared harness, already on the path:

- `from harness import read_field, surface, require_feature, baseline_text`
  - `read_field(obj, *names, default=...)` — a field by any of several names,
    from a dict, dataclass or pydantic model. **Use it.** The requirement fixes
    field NAMES where it names them; it never fixes the container, and an
    implementation returning a dataclass instead of a dict has satisfied it
    equally. A whole run once failed because a counter was called `sent` rather
    than `misses`.
  - `baseline_text(rel)` — one file as the world shipped it, to tell the agent's
    symbols from curator's own. Returns `None` where there is no baseline, and
    never raises, so guard it: `if shipped is not None:` — nothing to diff
    against is not a failed requirement.
    **Do not import `BASELINE`, and do not write an absolute path of your own.**
    The suite runs in two places: the container that brackets it, and a hosted
    image that has only `/workdir`, `/tests` and `/tmp`. A test that read
    `/opt/world-state/...` directly scored oracle 10 of 10 locally and 0.8889
    hosted, on a FileNotFoundError. `baseline_text` knows both locations.
- Fixtures from `conftest.py`: `provider` (a real fake provider on loopback, plus
  a private cache dir) and `output` (everything the run printed OR logged — an
  implementation is allowed to log rather than print).

## Hard constraints

- **No network.** Not even a hostname that resolves.
- **No timing, no sleeping, no threads, no second process, no unseeded
  randomness, no dict-order dependence.** The suite must give the same answer
  every run.
- **Never grade by timeout.** If the wrong implementation loops forever, assert
  on a value the correct one returns, not on how long the wrong one takes. A
  timeout cannot tell slow-but-correct from broken.
- **Assert exact things.** Integers, byte lengths, counts, exception types,
  structural shapes, orderings. Never "looks reasonable".
- **Test the requirement, and only it.** If your assertion for fact X would also
  fail when fact Y is wrong, split them. Facts that share an observable cannot be
  scored separately, and one of them will fail a correct implementation.
- **Accept every correct design.** Before you finish, for each test ask: is there
  a different, reasonable implementation of this requirement that my assertion
  rejects? If yes, loosen the assertion to the requirement's actual words.
- **Never grade WHERE a call lives.** Which module a `logger.warning`, a helper
  or a constant is written in is an implementation choice, not a requirement, and
  an agent reading scattered evidence will place it wherever the evidence points.
  A test that monkeypatched one module's `logger` failed a build that said exactly
  the same thing at exactly the same moment from the module next door — the only
  fact of ten that build missed, and the corpus pointed at the module it chose.
  Capture the effect wherever it is produced (patch every module in the package
  that holds the attribute, one recorder between them, so "exactly once" still
  means once in total). The same applies to which file exports a constant: import
  it from the package, not from the one module you happened to put it in, unless
  the requirement names that module.

- **Prefer to grade a fact through a name the ticket states.** A fact about an
  internal helper is usually observable in what the public entry point returns —
  where a boundary falls, what a count comes to, which exception escapes. Reaching
  straight into an internal helper is allowed when nothing else can see the fact,
  but if that is the only route, note it in a comment: it usually means either the
  ticket gave the helper away or the fact is not reachable from outside.
- Do not read or import anything from `curator/tests/` — its `conftest.py` pulls
  in VCR machinery this suite has no business depending on.

## Finish condition

`{{suite_cmd}}` reports every test passing against the golden tree, and you have
re-read each test once against the two questions above (does it fail on untouched
curator? does it reject a correct alternative design?).
