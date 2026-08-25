---
title: "Handover: Packaging, Version Bumps & Release Cutting"
author: dermot
created_at: 2025-03-03T10:03:00+00:00
---

# Handover: Packaging, Version Bumps & Release Cutting

Written by Dermot Callaghan. This passes the release-cutting role to Emil Brandvold effective immediately. We are currently at v0.1.20, eighteen releases shipped total.

Emil, read this end to end before you cut your first release. It is not long but the order matters.

---

## Current state

- Repo: bespokelabs/curator
- Current version: v0.1.20
- Publish target: PyPI, package name `bespokelabs-curator`
- CI: Gitea, trusted-publisher OIDC to PyPI (no API token in secrets)

---

## Before you start

- Check that main is green. Do not cut from a red pipeline, even if the failure looks unrelated.
- Confirm every milestone PR you expected is actually merged. Easy to miss one that was still in review.
- Check for open issues tagged to the milestone with a blocking label. If any are open, decide with the team whether to defer them or defer the release.

---

## Step 1: Version bump

Version lives in pyproject.toml under `[project]`, key `version`.

- We are in the 0.1.x range. Patch bump by default.
- Bump minor only if the milestone explicitly introduced new user-facing capability (not just fixes or internal refactors). When in doubt, patch.
- Make the change on a branch, not directly on main.
- PR title should be `release: bump to vX.Y.Z`. One approval is enough, get it merged before tagging anything.

Do not tag before the bump commit is on main. I have seen this go wrong and it is annoying to unwind.

---

## Step 2: Tag and push

After the bump PR is merged and you have pulled main:

```
git pull origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

The tag push triggers the release workflow. Stay with it. If the workflow fails before the publish step, delete the tag (`git push origin --delete vX.Y.Z`, then `git tag -d vX.Y.Z`), fix whatever broke, and re-tag. Do not leave a broken tag sitting there.

---

## Step 3: CI release workflow

Three jobs, in order:

1. Build sdist and wheel via `python -m build`
2. Run the test suite against the built artifact (not source, this is intentional, see gotchas)
3. Publish to PyPI via trusted-publisher OIDC

If job 2 fails, job 3 does not run. Fix the failure, delete the tag, re-tag.

If job 3 fails on its own (rare, usually a PyPI connectivity blip), you can re-run just the publish job without re-tagging. Check the job logs first to confirm it is not a config issue.

---

## Step 4: GitHub release

Once the publish job is green:

- Go to Releases on the Gitea repo, draft a new release from the tag
- Title: `vX.Y.Z`
- Body: changelog entries for this version. Assemble these from CHANGELOG.md or from merged PR titles since the previous tag. Keep it factual and short.
- Publish the release.

---

## Step 5: Verify the publish

In a clean environment (virtualenv or a fresh shell with no curator installed):

```
pip install bespokelabs-curator==X.Y.Z
python -c "import bespokelabs.curator; print('ok')"
```

If this fails, do not sit on it. A broken release on PyPI cannot be deleted, it can only be yanked. File a yank via the PyPI web UI immediately and open an incident so people know not to pull that version. TBD who the second contact is for incidents while Emil is still getting oriented, I will confirm this separately.

---

## Known gotchas

- **Trusted publisher config**: the OIDC publisher on PyPI is tied to the exact workflow filename and the branch name. If someone renames the workflow file as part of a CI refactor, the publish will 403. You would need to update the trusted publisher entry in PyPI project settings before re-running. I am not entirely sure who has admin access to the PyPI project beyond me, need to check this and add Emil before the first release.
- **Testing against the artifact, not source**: the test suite can pass against source even if the package manifest is wrong and a file is missing from the sdist. The CI workflow deliberately installs and tests the built artifact for this reason. Do not shortcut it.
- **CHANGELOG discipline**: we do not auto-generate the changelog. If merged PR titles are vague or messy, the release notes will be useless. Chase people on their PR titles before the release, not after.
- **Tagging before the bump is on main**: produces a release from the wrong commit. Always merge the bump PR first, then pull, then tag.

---

## Open questions

- [ ] confirm Emil has PyPI project membership (maintainer role) before first release
- [ ] confirm who else has PyPI admin access besides me
- [ ] check whether the Gitea webhook that triggers on tag push needs any permission update now that ownership is changing (not sure, need to look)

---

## Contacts

For the transition period I am available for questions. Ping me on Slack or email before filing a yank or opening an incident, atleast while you are getting familiar with the flow.
