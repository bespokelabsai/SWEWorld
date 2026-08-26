---
title: "Winding down to maintenance mode after v0.1.26"
author: konrad
created_at: 2025-06-04T09:35:00+00:00
---

# Winding down to maintenance mode after v0.1.26

Milestone target for v0.1.26 is the last coordinated release before Millrow services move to dormancy. Once it ships, no new features enter any of the services below. This page is the record of what that means in practice and who is responsible for what.

## What maintenance mode means

- No new features merged, no non-critical PRs
- Incoming issues triaged by the service owner, but not actioned unless they are blocking (i.e., breaking a current workflow, not just inconvenient)
- Each service owner signs off that their service is stable and documented before we close the milestone
  - "documented" means the README and any relevant wiki pages reflect current behavior, not a prior version
- PRs already in-flight at the time v0.1.26 ships are reviewed on a case-by-case basis, the default is to defer them unless the author makes a case for criticality

The intent is that after this point the services run, but they do not grow.

## Per-service status

**finetuning** (Konrad Feltrin)
In maintenance mode as of v0.1.26. PR 653 (Shreyas's finetuning client work) is the last in-flight item before dormancy. I have reviewed the README and it reflects current behavior. No further feature work is planned on my end.

**agentic-curation** (Emil Brandvold)
Stopping criterion integrated. PR 685 covers the multi-turn agent changes, which are heading into the next sprint before the milestone closes. Emil to confirm sign-off once 685 is merged.

**batch-mode** (Emil Brandvold)
[Emil to fill in]

**blocks-and-recipes** (Emil Brandvold)
[Emil to fill in]

**bulk-llm-inference** (Dario Kestrel)
[Dario to fill in]

**caching-and-resume** (Dario Kestrel)
[Dario to fill in]

**code-execution** (Nikolai Berresford)
[Nikolai to fill in]

**curator-viewer** (Dario Kestrel)
[Dario to fill in]

**examples-cookbooks** (Dario Kestrel)
[Dario to fill in]

**local-offline-inference** (Emil Brandvold)
[Emil to fill in]

## Release and CI notes

TBD, Emil owns this section. He mentioned there are notes from the Jun 2 sync on the wiki, so presumably those cover the release checklist and any CI gate changes. Emil to fill in here before we close the milestone.

## Open issues going into dormancy

These are known and open. The decision to enter maintenance mode does not resolve them, it just means they sit. If any of them turn out to be blocking in practice, that is the bar for revisiting.

- issue 52: support for multiple samples per request
- issue 124: `inspect(func)` cache invalidation on comments / whitespace changes
- issue 233: automatic rate limit detection

My read is that none of these are blocking for v0.1.26, but I have not checked whether Dario or Nikolai see issue 233 differently given how bulk-llm-inference behaves under load. Worth a quick check before we sign off.

## Sign-off checklist

- [x] finetuning (Konrad Feltrin)
- [ ] agentic-curation (Emil Brandvold)
- [ ] batch-mode (Emil Brandvold)
- [ ] blocks-and-recipes (Emil Brandvold)
- [ ] bulk-llm-inference (Dario Kestrel)
- [ ] caching-and-resume (Dario Kestrel)
- [ ] code-execution (Nikolai Berresford)
- [ ] curator-viewer (Dario Kestrel)
- [ ] examples-cookbooks (Dario Kestrel)
- [ ] local-offline-inference (Emil Brandvold)
