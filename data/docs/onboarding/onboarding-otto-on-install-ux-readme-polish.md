---
title: "Onboarding: otto on install UX & README polish"
author: konrad
created_at: 2024-11-14T09:14:00+00:00
---

# Onboarding: Otto on Install UX & README Polish

Welcome Otto. This is the working doc for your first few weeks, not a formal onboarding package. It covers what you own right now, where to start, and who to ask about what.

## What you own right now

- PR 104, logo size fix in README for mobile, this is the first thing to get merged
- install UX polish, broadly: missing steps, confusing error messages, anything that tripped you up during your own setup
- README changes that are small and targeted (not a rewrite, not a restructure)

That's the scope. Dont expand it without checking in first.

## PR 104

This is the immediate priority. Logo renders too large on mobile because the HTML width attribute isn't constrained properly, details are in the PR itself.

- read the issue thread before touching anything, there was some back-and-forth about whether to use HTML or markdown syntax and I want to make sure we land on the right side of that
- get it reviewed and merged, ping #engineering if it stalls
- once it's in, it's done, don't revisit it

## Install UX

This is the open-ended part of the work. The goal is that a new user can clone the repo, follow the README, and be running without having to google something or ask in Slack.

The best source of truth here is your own setup experience. What confused you, what was missing, what errored in a way that didn't tell you what to do next. Write those down as you go, even rough notes.

- check the issues tracker first, some of this is already filed and I dont want duplicate work
- small targeted fixes are better than a single large PR, easier to review
- if you're changing something in the install flow that touches how examples or cookbooks are expected to behave, flag it to me before merging, that area has some implicit expectations I havent fully documented yet (this is a known gap, we can work through it together)

TBD: there are a couple of open questions about the install flow that I know are sitting in issues but I haven't triaged them recently. Otto, can you do a pass through the tracker and note anything that looks like it belongs to install UX? I'll take a look with you.

## README changes

Keep these small. The README has gotten a little long and I know there's a temptation to reorganize it but now is not the time.

- fix broken things (missing steps, wrong commands, outdated paths)
- logo fix via PR 104
- if you think a section needs rewriting, flag it as a comment or a `[TODO]` in a branch and we can discuss, dont just change it

## Who to ask about what

- me (Konrad) for: install flow decisions, examples-cookbooks expectations, anything that feels like it might break existing users
- #engineering for: day-to-day questions, getting eyes on a PR, anything blocking
- I dont know who owns the CI pipeline right now, need to check before pointing you there. if something in CI behaves unexpectedly, bring it to #engineering first

## First week shape

Rough order, not a strict schedule.

1. get set up locally if you havent already, note everything that was confusing
2. read through PR 104, understand the existing discussion, get it merged
3. do a pass through the issues tracker for anything install-UX related
4. pick one or two small install fixes and open PRs

By end of week 1 I'd like PR 104 merged and at least one issue identified (even if not fixed yet). That's realistic.

## Open questions

- what's the actual policy on HTML vs markdown image syntax in the README? the PR 104 thread touches this but there's no settled answer
- are there platforms besides mobile where the logo is broken? nobody checked desktop at small viewport as far as I know
- install flow on Windows, I have no idea how well tested this is
