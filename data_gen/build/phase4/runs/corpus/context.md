# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-05-27 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nolan Whitfield landed a fix touching multimodal-prompts and bulk-llm-inference; team needs to understand impact and confirm approach

    Today is Tuesday 27 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nolan Whitfield landed a fix touching multimodal-prompts and bulk-llm-inference; team needs to understand impact and confirm approach
    
    What it should get through:
      1. Understand the null value fix and its scope   [Emil Brandvold must raise this]
           - Emil Brandvold walks through the commit and its rationale
           - Konrad Feltrin and Nikolai Berresford question the default-app-id pattern
           - group agrees on whether this is a hotfix or part of the o3 work
      2. Assess impact on multimodal and bulk-inference paths   [Konrad Feltrin must raise this]
           - Konrad Feltrin flags any downstream consumers of default app id
           - Emil Brandvold checks multimodal integration
           - group decides if a follow-up is needed
    
    On the agenda: Review Nolan Whitfield's null value fix for default app id; Check for ripple effects across bulk-llm-inference and multimodal-prompts; Decide on merge or further changes
    
    Out today: Dermot Callaghan (no commit, review or comment 2025-05-18..2025-06-25) — their input is missing and people may say so
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees the fix is sound or identifies changes needed; Nolan Whitfield can merge or iterate same day
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 355 changes merged to date

    On the table
      - Weekly Notes — Week of May 19 (someone)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. understanding of the multimodal-prompts service and its integration points
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand the null value fix and its scope   *** MUST RAISE ***
      2. Assess impact on multimodal and bulk-inference paths
      3. what "notes-2025-05-19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand the null value fix and its scope
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. platform-wide context and ability to spot ripple effects
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Understand the null value fix and its scope
      2. Assess impact on multimodal and bulk-inference paths   *** MUST RAISE ***
    goal        Assess impact on multimodal and bulk-inference paths
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. expertise in code-execution and telemetry surfaces that might be affected
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Understand the null value fix and its scope
      2. Assess impact on multimodal and bulk-inference paths
    goal        Nolan Whitfield landed a fix touching multimodal-prompts and bulk-llm-inference; team needs to understand impact and confirm approach
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team agrees the fix is sound or identifies changes needed; Nolan Whitfield can merge or iterate same day


==============================================================================
# 2025-05-28 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four pull requests older than the era median merge time (25.6h); two are from present contributors

    Today is Wednesday 28 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four pull requests older than the era median merge time (25.6h); two are from present contributors
    
    What it should get through:
      1. Unblock PR PR 652 (viewer dataset download)   [Emil Brandvold must raise this]
           - Emil explains 33-day stall and what unblocks it
           - Nikolai or Konrad signals review capacity
           - Decision on merge or rework path
      2. Clear path for torch-import and finetuning PRs   [Nikolai Berresford must raise this]
           - Nikolai surfaces PR 653 and PR 663 status
           - Emil signals whether they gate the release
           - Decide if these land before v0.1.25 or after
    
    On the agenda: Surface the blocker history on open PRs; Triage which need review vs which need rework; Determine merge sequence and any gating
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear which PRs are ready for merge, which need rework, and whether any gate the v0.1.25 release that Konrad is tracking
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 355 changes merged to date

    On the table
      - Weekly Notes — Week of May 19 (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on PR PR 652 (viewer dataset download) that has been open 33 days
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock PR PR 652 (viewer dataset download)   *** MUST RAISE ***
      2. Clear path for torch-import and finetuning PRs
      3. that the doc "Weekly Notes — Week of May 26" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Weekly Notes — Week of May 19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock PR PR 652 (viewer dataset download)
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. context on PRs PR 653 (finetuning client) and PR 663 (torch import fix) that have been waiting 32 and 21 days
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Unblock PR PR 652 (viewer dataset download)
      2. Clear path for torch-import and finetuning PRs   *** MUST RAISE ***
    goal        Clear path for torch-import and finetuning PRs
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear which PRs are ready for merge, which need rework, and whether any gate the v0.1.25 release that Konrad is tracking


==============================================================================
# 2025-05-29 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two o3 PRs opened the same day; need to coordinate landing without reverting each other

    Today is Thursday 29 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two o3 PRs opened the same day; need to coordinate landing without reverting each other
    
    What it should get through:
      1. Resolve which of PR 678 or PR 679 is the canonical add and merge it first   [Konrad Feltrin must raise this]
           - Konrad explains the two commits are duplicates with different refactor scope
           - Emil describes what PR 678 was targeting
           - They land on: one is the keeper, one closes-as-duplicate or rebases
      2. Confirm o3 structured-output support has test coverage before merge   [Emil Brandvold must raise this]
           - Emil or Konrad walks through what the PR adds
           - Someone asks if test_structured_outputs covers o3
           - Agreement on what coverage exists or needs adding before land
    
    On the agenda: Review both o3 PRs (PR 678 and PR 679) for overlap; Decide merge order to avoid conflicts; Validate structured-output test coverage
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: One PR merged, one closed or rebased; o3 added to structured-output models list with confirmed test coverage.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 355 changes merged to date

    On the table
      - Weekly Notes — Week of May 26 (someone)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 678: ref: added o3 support for structured outputs (Emil Brandvold)
      - PR 679: Add o3 to list of models supporting structured outputs (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just committed the o3 structured-output additions; knows what needs review
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Resolve which of PR 678 or PR 679 is the canonical add and merge it first   *** MUST RAISE ***
      2. Confirm o3 structured-output support has test coverage before merge
      3. what "notes-2025-05-26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Resolve which of PR 678 or PR 679 is the canonical add and merge it first
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. opened the parallel PR 678 refactor; can spot overlap or conflicts
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Resolve which of PR 678 or PR 679 is the canonical add and merge it first
      2. Confirm o3 structured-output support has test coverage before merge   *** MUST RAISE ***
    goal        Confirm o3 structured-output support has test coverage before merge
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   One PR merged, one closed or rebased; o3 added to structured-output models list with confirmed test coverage.


------------------------------------------------------------------------------
## #engineering — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: o3 support for structured outputs is shipping; quick sync to confirm state and next moves

    Today is Thursday 29 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: o3 support for structured outputs is shipping; quick sync to confirm state and next moves
    
    What it should get through:
      1. Confirm o3 structured-output support is complete and move workstream to closing   [Konrad Feltrin must raise this]
           - Konrad notes both commits landed and o3 is now in the model list
           - Emil confirms this unblocks any downstream release work
           - Agreement that ws-069 is wrapping
    
    On the agenda: o3 structured output now in the list; Any remaining gaps in provider support; What's next for the provider breadth work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team aware o3 structured-output support is shipped; workstream ws-069 marked for close-out.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 355 changes merged to date

    On the table
      - Weekly Notes — Week of May 26 (someone)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 678: ref: added o3 support for structured outputs (Emil Brandvold)
      - PR 679: Add o3 to list of models supporting structured outputs (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just shipped o3 structured-output support; knows the current state
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm o3 structured-output support is complete and move workstream to closing   *** MUST RAISE ***
      2. what "notes-2025-05-26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm o3 structured-output support is complete and move workstream to closing
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release and provider integrations; can assess if this unblocks anything downstream
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm o3 structured-output support is complete and move workstream to closing
    goal        o3 support for structured outputs is shipping; quick sync to confirm state and next moves
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team aware o3 structured-output support is shipped; workstream ws-069 marked for close-out.


==============================================================================
# 2025-05-30 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Both o3 support and the version bump merged this morning; the release is ready to ship.

    Today is Friday 30 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Both o3 support and the version bump merged this morning; the release is ready to ship.
    
    What it should get through:
      1. Confirm the release notes cover all merged work   [Emil Brandvold must raise this]
           - Emil runs through the two commits
           - Konrad confirms o3 coverage is accurate
           - Both agree it's complete
      2. Get the announcement out to the team   [Emil Brandvold must raise this]
           - Emil drafts the mail
           - Konrad approves
           - Emil sends
    
    On the agenda: Review what landed in 0.1.25; Write and post the release notes; Announce to the team
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.25 release notes are written, the announcement is posted, and the team knows the release shipped; it is settled that the team agrees the o3 family has to be present in the support table
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 357 changes merged to date

    On the table
      - v0.1.25 Release Notes (Emil Brandvold)
      - v0.1.24 Release Notes (Emil Brandvold)
      - announce-v0-1-25 (Emil Brandvold)
      - release-v0-1-25 (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: o3-mini.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release-and-ci; just bumped the version and merged the PR
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm the release notes cover all merged work   *** MUST RAISE ***
      2. Get the announcement out to the team   *** MUST RAISE ***
      3. lost a morning to this last week: o3-mini shipped with schema support day one and our table had no o3 entry at all, so everything o3 fell straight through to the unsupported branch and I sat there rewriting my pydantic model convinced it was me   *** MUST SETTLE (clue t2.r1.L3) ***
         must contain literally: o3-mini
      4. that the doc "v0.1.25 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
      5. that "v0.1.25 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      6. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "v0.1.25 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm the release notes cover all merged work
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. context on o3 support that shipped in this release
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm the release notes cover all merged work
      2. Get the announcement out to the team
    goal        Both o3 support and the version bump merged this morning; the release is ready to ship.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.25 release notes are written, the announcement is posted, and the team knows the release shipped; it is settled that the team agrees the o3 family has to be present in the support table


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs are older than the era's median merge time (25.6h); they have been open 23–35 days. The team is here and should decide on them.

    Today is Friday 30 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs are older than the era's median merge time (25.6h); they have been open 23–35 days. The team is here and should decide on them.
    
    What it should get through:
      1. Understand why PR 652 has been open 35 days   [Emil Brandvold must raise this]
           - Emil asks what's blocking it
           - Konrad or Nikolai Berresford surface the blocker
           - The room agrees on next step
      2. Get review and merge clarity on Nikolai Berresford's two PRs   [Nikolai Berresford must raise this]
           - Nikolai summarizes what's in each
           - Konrad and Emil review the asks
           - The room commits to review cycle or notes why they can't
    
    On the agenda: Check status of PR 652 (dataset download from viewer); Check status of PR 653 (finetuning client); Check status of PR 663 (torch not installed fix); Assess blocker on PR 675
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: The team surfaces what is blocking the stale PRs and agrees on next steps: either merge them, assign review, or defer them past the consolidation phase; it is settled that the team agrees the sandbox properties do not currently survive a caller-supplied image
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 357 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 280 function/class names and 28 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns examples-cookbooks and code-execution; familiar with blocked work
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Understand why PR 652 has been open 35 days
      2. Get review and merge clarity on Nikolai Berresford's two PRs
    goal        Four PRs are older than the era's median merge time (25.6h); they have been open 23–35 days. The team is here and should decide on them.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release-and-ci; context on why PR 680 had to land first
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand why PR 652 has been open 35 days   *** MUST RAISE ***
      2. Get review and merge clarity on Nikolai Berresford's two PRs
    goal        Understand why PR 652 has been open 35 days
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. authored the finetuning client and torch fix
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Understand why PR 652 has been open 35 days
      2. Get review and merge clarity on Nikolai Berresford's two PRs   *** MUST RAISE ***
      3. Got asked at the demo whether the sandbox guarantees still hold if you bring your own image. I said "should do", then went and checked afterwards, and now I would like to un-say it.   *** MUST SETTLE (clue t4.r2.L7) ***
    goal        Get review and merge clarity on Nikolai Berresford's two PRs
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   The team surfaces what is blocking the stale PRs and agrees on next steps: either merge them, assign review, or defer them past the consolidation phase; it is settled that the team agrees the sandbox properties do not currently survive a caller-supplied image


==============================================================================
# 2025-06-02 — 2 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #viewer — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Viewer-specific feature merged; service owners need to know what changed

    Today is Monday 2 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Viewer-specific feature merged; service owners need to know what changed
    
    What it should get through:
      1. Confirm download plumbing in viewer surface is clean and testable   [Emil Brandvold must raise this]
           - Emil outlines the download endpoint
           - Konrad checks dependencies on cost tracking
           - Emil confirms no new blockers
      2. send Week of May 26 recap: v0.1.25 shipped   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Week of May 26 recap: v0.1.25 shipped
    
    On the agenda: PR PR 652 merged into viewer code; How downloads are exposed in the UI surface; Dependencies on cost tracking and resume logic; Week of May 26 recap: v0.1.25 shipped
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Viewer owners understand what the feature exposes; any integration gaps are spotted
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 359 changes merged to date

    On the table
      - Handover: Status Tracking, Cost Reporting & the Viewer Surface (Gideon Halloway)
      - weekly-2025-05-26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 681: If the model is not known, let the cost be None. (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 278 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Implementation details of PR 652; what the download endpoint now exposes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm download plumbing in viewer surface is clean and testable   *** MUST RAISE ***
      2. send Week of May 26 recap: v0.1.25 shipped
      3. what "Handover: Status Tracking, Cost Reporting & the Viewer Surface" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm download plumbing in viewer surface is clean and testable
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Context on how downloads interact with caching and persistence
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm download plumbing in viewer surface is clean and testable
      2. send Week of May 26 recap: v0.1.25 shipped   *** MUST RAISE ***
      3. that "Week of May 26 recap: v0.1.25 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Week of May 26 recap: v0.1.25 shipped
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Viewer owners understand what the feature exposes; any integration gaps are spotted


------------------------------------------------------------------------------
## #general — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Konrad is writing the dormancy plan today; team needs to understand the pace shift

    Today is Monday 2 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad is writing the dormancy plan today; team needs to understand the pace shift
    
    What it should get through:
      1. Set expectations for reduced team capacity and slower review cycle   [Konrad Feltrin must raise this]
           - Konrad sketches the era and what changed
           - Emil acknowledges the shift
           - Nikolai confirms understanding of PR queue implications
    
    On the agenda: Dormancy era begins: v0.1.25 shipped, last active contributors winding down; Expectations for review turnaround and issue triage going forward; How to handle stale PRs in the queue
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Team understands the dormancy era constraints; stale PRs and slow reviews are not surprising
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 359 changes merged to date

    On the table
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - weekly-2025-05-26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 681: If the model is not known, let the cost be None. (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 278 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Plan for the dormancy era and slower review pace
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Set expectations for reduced team capacity and slower review cycle   *** MUST RAISE ***
      2. that the doc "Winding down to maintenance mode after v0.1.26" is done, and where the others can find it   *** MUST RAISE ***
      3. what "Week of May 26 recap: v0.1.25 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Set expectations for reduced team capacity and slower review cycle
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Awareness of what shipped last week
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Set expectations for reduced team capacity and slower review cycle
    goal        Konrad is writing the dormancy plan today; team needs to understand the pace shift
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Presence and acknowledgment of the new era
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Set expectations for reduced team capacity and slower review cycle
    goal        Konrad is writing the dormancy plan today; team needs to understand the pace shift
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands the dormancy era constraints; stale PRs and slow reviews are not surprising

