---
title: "Getting Started: Curator Dev Setup & Repo Tour"
author: konrad
created_at: 2024-10-29T09:00:00+00:00
---

# Getting Started: Curator Dev Setup & Repo Tour

Welcome to Millrow. This page gets you to a working local environment and gives you enough of a map of the repo that you can find things without asking someone every five minutes.

Written against what we have as of late October 2024. If something is out of date, drop a comment or ping me (Konrad) on Slack.

---

## Prerequisites

- Python 3.10 or newer (we have not formally tested 3.13 yet, so I'd stick to 3.10 or 3.11 if you can)
- Git, obviously
- A virtual environment tool, `venv` is fine, we dont mandate anything fancier
- Access to the Millrow Gitea instance (if you cant clone yet, talk to whoever handles provisioning, that was priya last I checked)

---

## Cloning the Repo

```
git clone https://gitea.millrow.internal/millrow/curator.git
cd curator
```

If you get a certificate error on the Gitea host, there's a note on the engineering wiki about the internal CA. Check engineering > dev environment setup. I'm not going to repeat it here because it tends to drift.

---

## Local Python Environment

```
python -m venv .venv
source .venv/bin/activate      # windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The `-e` flag matters. We reference the package by name in several places internally and if you do a normal install you'll chase confusing import errors.

There is a `requirements-dev.txt` at the root as well, but it's mostly redundant with what `pyproject.toml` pulls in. I usually just use the editable install and it works.

Verify the install came through:

```
python -c "import curator; print(curator.__version__)"
```

If that errors, something went wrong with the editable install. Most common cause I've seen is having a stale `.egg-info` from a previous checkout, deleting it and re-running pip install usually sorts it.

---

## Repo Layout

High level, these are the directories you'll actually spend time in:

```
curator/
  curator/          <- the library itself, this is what you edit
  examples/         <- cookbooks and usage examples
  ci/               <- CI configs and release tooling
  tests/
  docs/             <- mostly auto-generated, don't edit by hand
  pyproject.toml
  README.md
```

### curator/ (the library)

This is where all the real code lives. A few entrypoints worth knowing early:

- `curator/__init__.py`, what gets exported when someone does `import curator`. If you add something new and wonder why it's not visible, check here first.
- `curator/pipeline.py`, the main pipeline runner, most data flows pass through here
- `curator/filters/`, filter classes, one file per filter type roughly
- `curator/utils/`, shared utilities, some of this is a bit of a junk drawer honestly

I'd spend 20 minutes just reading pipeline.py before touching anything. It's not long and it makes the rest of the structure make more sense.

### examples/

Cookbooks for common tasks, aimed at library users but useful for us too when testing behavior. Not all of them are kept fully up to date (TBD, we should probably triage these, some are clearly stale).

If you add a new feature, adding an example here is expected, not optional.

### ci/

Release scripts and CI definitions. We use GitHub Actions (the configs are also checked in here for reference even though they live in `.github/` too, so there are two copies and they should match, though sometimes they dont, I need to sort that out).

- Release tagging is semi-manual right now, the script in `ci/release.sh` walks you through it
- The full release process is documented on the wiki under engineering > release process, worth reading before you touch anything here

---

## Running Tests

```
pytest tests/
```

That's it for the basic run. There is a slower integration test suite:

```
pytest tests/ -m integration
```

Don't run the integration suite casually, it hits some external things and is slow. I think it also requires some env vars set, I dont have the full list in front of me, need to check with whoever last touched `tests/conftest.py` (sam probably).

Coverage report:

```
pytest tests/ --cov=curator --cov-report=term-missing
```

We don't have a hard coverage gate right now. We probably should.

---

## Verifying the Library Locally

Beyond the test suite, the quickest sanity check is running one of the examples:

```
python examples/basic_pipeline.py
```

If that runs without errors you're in a good state. It exercises the core pipeline path without needing any external services.

For anything more involved, the cookbooks in `examples/` cover specific use cases. I'd look at `examples/filter_demo.py` as a second check, it exercises more of the filter layer.

---

## Things That Bite New Developers

- The editable install issue above (see Python Environment section)
- `PYTHONPATH` conflicts if you have curator installed system-wide for some reason. Use the venv, dont skip it.
- Some of the older cookbooks import things that were moved or renamed and will error on import. Not your fault, they just haven't been updated. (TBD on triage)
- If tests start failing unexpectedly, check whether you're on the right branch. We have a few long-lived feature branches that are not in a passing state right now.

---

## Open Questions

- Do we need a Makefile with common targets? Right now new people have to read docs to know which pytest invocation to use. I think we do, need to bring it up.
- Integration test env vars: need a definitive list somewhere. Nobody seems to own this currently.
- Docker-based dev environment: a few people have asked. I haven't looked at this seriously yet, not sure if it's worth the maintenance overhead for a library project.
