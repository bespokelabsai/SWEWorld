# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-04-11 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Two tags shipped same day; post1 is a hotfix that needs explaining

    Today is Friday 11 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two tags shipped same day; post1 is a hotfix that needs explaining
    
    What it should get through:
      1. 0.1.23 release notes finalized and mailed   [Emil Brandvold must raise this]
           - Emil walks through what batch cancellation fix and viewer cleanup mean for users
           - Dermot confirms the three merged PRs are captured
           - Mail goes out to the team
      2. 0.1.23.post1 hotfix explained and announced   [Emil Brandvold must raise this]
           - Dermot explains why post1 was necessary (failed-requests jsonl or conftest issue)
           - Emil captures it in release notes
           - Second announcement goes out same day
    
    On the agenda: 0.1.23 release notes and announcement; 0.1.23.post1 hotfix rationale and second announcement; changelog accuracy for both tags
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both v0.1.23 and v0.1.23.post1 are documented, announced, and the team knows what each fixes. No confusion about which version to use.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 323 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - announce-v0-1-23 (Emil Brandvold)
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - v0.1.23.post1 Release Notes (Emil Brandvold)
      - announce-v0-1-23-post1 (Emil Brandvold)
      - release-v0-1-23 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 363 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release-and-ci; writing release notes for both tags
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. 0.1.23 release notes finalized and mailed   *** MUST RAISE ***
      2. 0.1.23.post1 hotfix explained and announced   *** MUST RAISE ***
      3. that the doc "v0.1.23 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.23 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. that the doc "v0.1.23.post1 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
      6. that "v0.1.23.post1 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      7. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      8. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        0.1.23 release notes finalized and mailed
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. fixed batch cancellation, removed dead viewer code, knows what went into each tag
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. 0.1.23 release notes finalized and mailed
      2. 0.1.23.post1 hotfix explained and announced
    goal        Two tags shipped same day; post1 is a hotfix that needs explaining
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. founder perspective on what gets released
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. 0.1.23 release notes finalized and mailed
      2. 0.1.23.post1 hotfix explained and announced
    goal        Two tags shipped same day; post1 is a hotfix that needs explaining
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. knows if any of his changes landed in the release
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. 0.1.23 release notes finalized and mailed
      2. 0.1.23.post1 hotfix explained and announced
    goal        Two tags shipped same day; post1 is a hotfix that needs explaining
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both v0.1.23 and v0.1.23.post1 are documented, announced, and the team knows what each fixes. No confusion about which version to use.


------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three open PRs; two are stale and blocking other work

    Today is Friday 11 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three open PRs; two are stale and blocking other work
    
    What it should get through:
      1. PR 626 approved and ready to merge   [Emil Brandvold must raise this]
           - Emil explains the cost schema change
           - Dermot or Gideon checks it against the metadata uses
           - Approval or blockers surface
      2. PR 468 and PR 583 stale PR blockers identified   [Nikolai Berresford must raise this]
           - Nikolai raises that PR 468 is stalled and needs a path forward
           - Emil or Dermot explains what's blocking or if it can land now
           - Next step is clear (rebase, review cycle, or descope)
    
    On the agenda: Status of PR 468 (n-samples, 63 days old); PR 583 metadata db param (35 days old); PR 626 metadata cost schema (new today, needs approval)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 626 gets approved. The team knows what it takes to unblock PR 468 (n-samples) and PR 583 (metadata db), or those PRs are descoped.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 323 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 363 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. two PRs open today: 0.1.23 bump and metadata cost schema update
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 626 approved and ready to merge   *** MUST RAISE ***
      2. PR 468 and PR 583 stale PR blockers identified
    goal        PR 626 approved and ready to merge
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. version bump and viewer cleanup PR; knows what the cleanup unblocks
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 626 approved and ready to merge
      2. PR 468 and PR 583 stale PR blockers identified
    goal        Three open PRs; two are stale and blocking other work
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. PR 468 waiting 63 days; knows what n-samples feature unblocks
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 626 approved and ready to merge
      2. PR 468 and PR 583 stale PR blockers identified   *** MUST RAISE ***
    goal        PR 468 and PR 583 stale PR blockers identified
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. founder review; approved PR 627
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 626 approved and ready to merge
      2. PR 468 and PR 583 stale PR blockers identified
    goal        Three open PRs; two are stale and blocking other work
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. approved PR 627
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. PR 626 approved and ready to merge
      2. PR 468 and PR 583 stale PR blockers identified
    goal        Three open PRs; two are stale and blocking other work
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 626 gets approved. The team knows what it takes to unblock PR 468 (n-samples) and PR 583 (metadata db), or those PRs are descoped.


------------------------------------------------------------------------------
## #incidents — 8 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact

    Today is Friday 11 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact
    
    What it should get through:
      1. Post1 hotfix impact and user guidance clear   [Dermot Callaghan must raise this]
           - Dermot states what broke in 0.1.23 (flaky litellm cost, conftest, or viewer artifact)
           - Emil checks if it blocks anyone's workflows
           - Guidance (mandatory upgrade vs optional) is decided
    
    On the agenda: Why post1 was needed; What it fixes in 0.1.23; Whether users should upgrade
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: The team and users understand whether v0.1.23.post1 is a mandatory upgrade or a minor patch, and why it went out the same day.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 323 changes merged to date

    On the table
      - v0.1.23.post1 Release Notes (Emil Brandvold)
      - announce-v0-1-23-post1 (Emil Brandvold)
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 363 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. knows what the hotfix fixes (failed-requests jsonl, conftest, or viewer code)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Post1 hotfix impact and user guidance clear   *** MUST RAISE ***
      2. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Post1 hotfix impact and user guidance clear
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. release notes context and communication
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Post1 hotfix impact and user guidance clear
    goal        Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. observability and run perspective
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Post1 hotfix impact and user guidance clear
    goal        Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. platform perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Post1 hotfix impact and user guidance clear
    goal        Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. aware of the release
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Post1 hotfix impact and user guidance clear
    goal        Hotfix release v0.1.23.post1 shipped same day as 0.1.23; team needs to know the impact
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   The team and users understand whether v0.1.23.post1 is a mandatory upgrade or a minor patch, and why it went out the same day.


------------------------------------------------------------------------------
## #cookbooks — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: the Bespoke-Stratos reproduction script gets edited between runs and Dermot Callaghan wants to know what reattach will do to it

    Today is Friday 11 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: the Bespoke-Stratos reproduction script gets edited between runs and Dermot Callaghan wants to know what reattach will do to it
    
    What it should get through:
    
    On the agenda: Dermot Callaghan on appending 500 new prompts to the input dataset, rerunning, and getting the old shorter batch's results back with the new rows silently missing; Emil Brandvold says the same script is run by two people on the same machine against different slices and he does not want either of them landing in the other's batch; Dario Kestrel asks whether a changed dataset should mean a whole new batch or a top-up batch for the extra rows, and nobody wants to own that answer today
    
    Wrap when: agreed the input rows have to matter somehow; top-up-vs-fresh deferred, Emil Brandvold says he will look at what the resume path does for online mode; it is settled that the team agrees resume state keyed independently of the prompt cache fingerprint goes stale and resumes the wrong job
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 323 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 363 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        the Bespoke-Stratos reproduction script gets edited between runs and Dermot Callaghan wants to know what reattach will do to it
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. When I was poking at this last month I stashed the id in a .curator_batch file in the working directory. Worked right up until I edited the prompt template, reran, and it cheerfully picked the previous job back up and handed me answers for the old prompts. The response cache didn't make that mistake, my file did.   *** MUST SETTLE (clue t3.r1.L2) ***
    goal        the team agrees resume state keyed independently of the prompt cache fingerprint goes stale and resumes the wrong job
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        the Bespoke-Stratos reproduction script gets edited between runs and Dermot Callaghan wants to know what reattach will do to it
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   agreed the input rows have to matter somehow; top-up-vs-fresh deferred, Emil Brandvold says he will look at what the resume path does for online mode; it is settled that the team agrees resume state keyed independently of the prompt cache fingerprint goes stale and resumes the wrong job


==============================================================================
# 2025-04-14 — 3 conversation(s), 31 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened, two reviewed, stale work in code-review channel

    Today is Monday 14 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened, two reviewed, stale work in code-review channel
    
    What it should get through:
      1. Determine if PR 632 batch frequency fix is ready to merge   [Gideon Halloway must raise this]
           - Gideon outlines the fix for tqdm update frequency
           - Dario or Emil raises concern if there are edge cases
           - Group lands on approval or defers to one more check
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage   [Dario Kestrel must raise this]
           - Emil flags PR 626 is blocking cost work
           - Gideon notes PR 632 is independent
           - Nikolai suggests merge order or confirms both can land in parallel
      3. Signal to Emil that PR 626 can proceed after PR 632 lands   [Dermot Callaghan must raise this]
           - Dermot confirms PR 631 merge didn't surface new issues
           - Emil gets thumbs-up to pursue PR 626 merge in parallel
           - Nikolai notes any release-window constraints
    
    On the agenda: Review and merge readiness for PR 632 batch update frequency fix; Status of PR 631 (merged) and remaining work on projected totals; Unblock PR 626 metadata schema cost tracking
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 632 approved or deferred with clear next steps; PR 626 unblocked; merge ordering clarified for the team
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 327 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 634: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 362 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two fresh commits on progress tracking UI; owns the projected-total/remaining work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Determine if PR 632 batch frequency fix is ready to merge   *** MUST RAISE ***
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage
      3. Signal to Emil that PR 626 can proceed after PR 632 lands
    goal        Determine if PR 632 batch frequency fix is ready to merge
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider integrations context from his commit; approved PR 631
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Determine if PR 632 batch frequency fix is ready to merge
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage   *** MUST RAISE ***
      3. Signal to Emil that PR 626 can proceed after PR 632 lands
    goal        Clarify merge ordering for PR 626 and PR 632 to avoid blockage
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Metadata schema cost work; familiarity with online request processing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if PR 632 batch frequency fix is ready to merge
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage
      3. Signal to Emil that PR 626 can proceed after PR 632 lands
    goal        Three PRs opened, two reviewed, stale work in code-review channel
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release stability perspective; approved PR 631 yesterday
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Determine if PR 632 batch frequency fix is ready to merge
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage
      3. Signal to Emil that PR 626 can proceed after PR 632 lands   *** MUST RAISE ***
      4. that the doc "Postmortem: v0.1.23.post1 Hotfix" is done, and where the others can find it   *** MUST RAISE ***
      5. that "Weekly update: week of Apr 7" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Signal to Emil that PR 626 can proceed after PR 632 lands
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Release and CI perspective; metadata db disable work pending
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Determine if PR 632 batch frequency fix is ready to merge
      2. Clarify merge ordering for PR 626 and PR 632 to avoid blockage
      3. Signal to Emil that PR 626 can proceed after PR 632 lands
    goal        Three PRs opened, two reviewed, stale work in code-review channel
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 632 approved or deferred with clear next steps; PR 626 unblocked; merge ordering clarified for the team


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Two changes to online-request-processing and one to provider-integrations; progress-and-cli work is landing

    Today is Monday 14 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two changes to online-request-processing and one to provider-integrations; progress-and-cli work is landing
    
    What it should get through:
      1. Validate that projected-total and projected-remaining readout is now trustworthy   [Gideon Halloway must raise this]
           - Gideon walks through the UI improvements and accuracy fixes
           - Dario or Dermot raises a remaining edge case or asks about test coverage
           - Group confirms readout is now ship-ready or flags one more round of work
      2. Confirm batch statistics account is ready for testing   [Gideon Halloway must raise this]
           - Gideon outlines what the account tracks and what is still needed
           - Emil flags any dependency on metadata schema work
           - Group agrees on testing scope and timeline
      3. Ensure provider integrations layer is prepared for cost-tracking handoff   [Dario Kestrel must raise this]
           - Dario notes his provider integration commit context
           - Emil surfaces PR 626 metadata schema blocker if relevant
           - Group confirms cost tracking can proceed without additional pipeline changes
    
    On the agenda: Gideon's two commits on projected total/remaining readout; Batch statistics account checkpoint and testing plan; Impact on downstream provider integrations and cost tracking
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon's progress-tracking work validated; batch statistics account checkpoint assessed; provider integration path clear for cost work
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 327 changes merged to date

    On the table
      - Weekly Notes — Week of Apr 7 (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 634: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 362 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two commits improving projected total/remaining UI; checkpoint progress on batch statistics account
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate that projected-total and projected-remaining readout is now trustworthy   *** MUST RAISE ***
      2. Confirm batch statistics account is ready for testing   *** MUST RAISE ***
      3. Ensure provider integrations layer is prepared for cost-tracking handoff
      4. what "Weekly Notes — Week of Apr 7" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate that projected-total and projected-remaining readout is now trustworthy
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider integration perspective; one commit to integrations today; approved progress tracking work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate that projected-total and projected-remaining readout is now trustworthy
      2. Confirm batch statistics account is ready for testing
      3. Ensure provider integrations layer is prepared for cost-tracking handoff   *** MUST RAISE ***
    goal        Ensure provider integrations layer is prepared for cost-tracking handoff
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Platform engineering view; metadata schema cost work that feeds into progress tracking
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate that projected-total and projected-remaining readout is now trustworthy
      2. Confirm batch statistics account is ready for testing
      3. Ensure provider integrations layer is prepared for cost-tracking handoff
    goal        Two changes to online-request-processing and one to provider-integrations; progress-and-cli work is landing
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Stability and release perspective on progress UI changes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate that projected-total and projected-remaining readout is now trustworthy
      2. Confirm batch statistics account is ready for testing
      3. Ensure provider integrations layer is prepared for cost-tracking handoff
    goal        Two changes to online-request-processing and one to provider-integrations; progress-and-cli work is landing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Gideon's progress-tracking work validated; batch statistics account checkpoint assessed; provider integration path clear for cost work


------------------------------------------------------------------------------
## #viewer — 9 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Two changes to progress-and-cli and Gideon Halloway driving landing work

    Today is Monday 14 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two changes to progress-and-cli and Gideon Halloway driving landing work
    
    What it should get through:
      1. Confirm PR 631 improvements to projected total/remaining are correct and ship-ready   [Gideon Halloway must raise this]
           - Gideon walks through what changed and why it's more accurate
           - Dario or Dermot spot-checks the logic or raises edge case
           - Group agrees it's ready or flags a follow-up
      2. Validate batch update frequency fix doesn't harm UI responsiveness   [Gideon Halloway must raise this]
           - Gideon outlines the frequency change rationale
           - Emil flags any impact on progress bar refresh or cost counter
           - Group confirms the tradeoff is acceptable
      3. Assess whether cost and time projections are now user-facing   [Emil Brandvold must raise this]
           - Emil asks if projections are accurate enough to show
           - Dario notes PR 626 metadata schema cost work is still pending
           - Group acknowledges readout is ready but full cost tracking waits on schema
    
    On the agenda: Review of PR 631 merged progress-tracking improvements; Batch update frequency fix (PR 632) and UI responsiveness; Readiness of cost and time projections for users
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 631 validated as correct; PR 632 assessed for impact; group clear on next phase (likely PR 626 cost schema work); it is settled that Gideon Halloway saw a resumed job whose provider disagreed with the configured one, breaking the cost table
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 327 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 626: update metadata schema with cost (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 634: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 362 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two commits to progress UI and batch frequency; owns the readout work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 631 improvements to projected total/remaining are correct and ship-ready   *** MUST RAISE ***
      2. Validate batch update frequency fix doesn't harm UI responsiveness   *** MUST RAISE ***
      3. Assess whether cost and time projections are now user-facing
      4. got a weird one in the summary table after a restart: header said the run was on gemini, the batch object we were tracking was clearly a mistral one, and the cost column came out as gibberish because the token fields didn't line up. I can make the table defensive but the thing feeding it is wrong.   *** MUST SETTLE (clue t3.r2.l_prov_gideon) ***
    goal        Confirm PR 631 improvements to projected total/remaining are correct and ship-ready
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Bulk-inference and request-processing context; approved progress work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 631 improvements to projected total/remaining are correct and ship-ready
      2. Validate batch update frequency fix doesn't harm UI responsiveness
      3. Assess whether cost and time projections are now user-facing
    goal        Two changes to progress-and-cli and Gideon Halloway driving landing work
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release and stability perspective; foundational cookbook and inference owner
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm PR 631 improvements to projected total/remaining are correct and ship-ready
      2. Validate batch update frequency fix doesn't harm UI responsiveness
      3. Assess whether cost and time projections are now user-facing
    goal        Two changes to progress-and-cli and Gideon Halloway driving landing work
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Platform engineering view on progress tracking; owns the service
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 631 improvements to projected total/remaining are correct and ship-ready
      2. Validate batch update frequency fix doesn't harm UI responsiveness
      3. Assess whether cost and time projections are now user-facing   *** MUST RAISE ***
      4. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Assess whether cost and time projections are now user-facing
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 631 validated as correct; PR 632 assessed for impact; group clear on next phase (likely PR 626 cost schema work); it is settled that Gideon Halloway saw a resumed job whose provider disagreed with the configured one, breaking the cost table; Gideon Halloway saw a resumed job whose provider disagreed with the configured one, breaking the cost table


==============================================================================
# 2025-04-15 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs merged today touching request processing, batch mode, and structured outputs; three active workstreams need validation

    Today is Tuesday 15 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs merged today touching request processing, batch mode, and structured outputs; three active workstreams need validation
    
    What it should get through:
      1. Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream   [Emil Brandvold must raise this]
           - Emil outlines the structure output bug and the fix
           - Dario checks impact on online request processing
           - Emil confirms it unblocks cost accounting work
      2. Validate PR 638 (cost streaming) is ready to land or needs refinement   [Emil Brandvold must raise this]
           - Emil presents the cost streaming approach
           - Gideon flags any observability or telemetry concerns
           - Dario approves path forward
      3. Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings   [Gideon Halloway must raise this]
           - Gideon walks through the structured output mapping
           - Emil checks for Gemini/Anthropic interaction
           - Validation that it lands cleanly
    
    On the agenda: PR 639 batch mode structure outputs — is this the root cause or a symptom?; PR 638 cost streaming and delayed streaming — does this unblock the cost accounting work?; PR 637 GPT-4.1 structured output — any conflicts with existing mappings?
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three PRs validated as safe to leave open or merged; cost streaming path forward confirmed; no blocking concerns on GPT-4.1 integration
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 331 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 638: cost streaming in batch mode and delayed streaming support (Emil Brandvold)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 359 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Deep understanding of batch mode structure output bugs and cost streaming; owns the two active workstreams touching this code
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream   *** MUST RAISE ***
      2. Validate PR 638 (cost streaming) is ready to land or needs refinement   *** MUST RAISE ***
      3. Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. GPT-4.1 structured output context; observability perspective on request handling
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream
      2. Validate PR 638 (cost streaming) is ready to land or needs refinement
      3. Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings   *** MUST RAISE ***
    goal        Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing owner perspective; has already approved PR 639
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream
      2. Validate PR 638 (cost streaming) is ready to land or needs refinement
      3. Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings
    goal        Four PRs merged today touching request processing, batch mode, and structured outputs; three active workstreams need validation
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just landed metadata schema changes; understands downstream impact
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm PR 639 (batch mode structure outputs) is merged and blocks nothing downstream
      2. Validate PR 638 (cost streaming) is ready to land or needs refinement
      3. Verify PR 637 (GPT-4.1 structured output) does not conflict with existing provider mappings
    goal        Four PRs merged today touching request processing, batch mode, and structured outputs; three active workstreams need validation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three PRs validated as safe to leave open or merged; cost streaming path forward confirmed; no blocking concerns on GPT-4.1 integration


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three commits landed, four PRs merged; two active workstreams need team awareness; new feature flags and schema changes need communication

    Today is Tuesday 15 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three commits landed, four PRs merged; two active workstreams need team awareness; new feature flags and schema changes need communication
    
    What it should get through:
      1. Team understands batch mode structure output bugs are being resolved incrementally   [Emil Brandvold must raise this]
           - Emil: batch mode bugs (Gemini parts, finish reason) are two symptoms, not root cause
           - Gideon: notes any impact on CLI observability
           - Dario: confirms online request path is stable
      2. Cost accounting work is now unblocked by schema and streaming updates   [Emil Brandvold must raise this]
           - Emil: cost metadata schema landed, cost streaming PR open
           - Dario: confirms request processing side is ready
           - Gideon: flags any display concerns
      3. Metadata db opt-out flag is live and changes verifier behavior   [Nikolai Berresford must raise this]
           - Nikolai: flag is now available, verifier runs skip db on demand
           - Dario: understands impact on code-execution service
           - Dermot: notes any downstream effects
    
    On the agenda: What landed today: batch mode, cost schema, GPT-4.1, metadata db flag; What's in flight: cost streaming, rate limit detection, provider response shapes; Blockers and next steps
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team is aligned on what landed and what's still in flight; cost accounting work is unblocked; no surprises on metadata db opt-out behavior
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 331 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 638: cost streaming in batch mode and delayed streaming support (Emil Brandvold)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 359 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Two workstreams in mid-flight; batch mode bugs landing in quick succession; cost accounting coming into focus
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Team understands batch mode structure output bugs are being resolved incrementally   *** MUST RAISE ***
      2. Cost accounting work is now unblocked by schema and streaming updates   *** MUST RAISE ***
      3. Metadata db opt-out flag is live and changes verifier behavior
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Team understands batch mode structure output bugs are being resolved incrementally
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. GPT-4.1 structured output work; observability on request handling; recent CLI readout fixes
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Team understands batch mode structure output bugs are being resolved incrementally
      2. Cost accounting work is now unblocked by schema and streaming updates
      3. Metadata db opt-out flag is live and changes verifier behavior
    goal        Three commits landed, four PRs merged; two active workstreams need team awareness; new feature flags and schema changes need communication
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just kicked off code-execution metadata db opt-out; understands verifier impact
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Team understands batch mode structure output bugs are being resolved incrementally
      2. Cost accounting work is now unblocked by schema and streaming updates
      3. Metadata db opt-out flag is live and changes verifier behavior   *** MUST RAISE ***
    goal        Metadata db opt-out flag is live and changes verifier behavior
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing owner; already deep in cost accounting conversation
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Team understands batch mode structure output bugs are being resolved incrementally
      2. Cost accounting work is now unblocked by schema and streaming updates
      3. Metadata db opt-out flag is live and changes verifier behavior
    goal        Three commits landed, four PRs merged; two active workstreams need team awareness; new feature flags and schema changes need communication
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team is aligned on what landed and what's still in flight; cost accounting work is unblocked; no surprises on metadata db opt-out behavior


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Batch mode, cost streaming, and GPT-4.1 work all landed or are in-flight; request processing architecture needs to accommodate all three without conflicts

    Today is Tuesday 15 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Batch mode, cost streaming, and GPT-4.1 work all landed or are in-flight; request processing architecture needs to accommodate all three without conflicts
    
    What it should get through:
      1. Determine if batch mode response-shape bugs are root-cause or symptom of underlying Gemini integration issue   [Emil Brandvold must raise this]
           - Emil: outlines Gemini missing parts and finish reason issues
           - Dario: asks whether this is Gemini-specific or affects other batch backends
           - Gideon: suggests unified response-shape test harness
      2. Cost streaming architecture integrates cleanly with rate limiting and buffering without deadlock or latency issues   [Emil Brandvold must raise this]
           - Emil: presents cost streaming approach and buffer interaction
           - Gideon: raises observability and display concerns
           - Dario: validates no conflict with retry or resume logic
      3. GPT-4.1 structured output mapping does not conflict with Gemini or Anthropic paths and integrates into cost accounting   [Gideon Halloway must raise this]
           - Gideon: walks through GPT-4.1 mapping
           - Emil: checks interaction with cost streaming
           - Dario: confirms no duplication with existing structured output paths
    
    On the agenda: Batch mode response-shape bugs: Gemini parts, finish reason — one bug or two?; Cost streaming integration with existing buffering and rate limiting; GPT-4.1 structured output mapping — any provider interaction concerns?
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Batch mode bugs are diagnosed as Gemini-specific; cost streaming path is validated; GPT-4.1 integrates without conflict; it is settled that the team agrees a run whose image needed root completed with no indication anything was different
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 331 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 638: cost streaming in batch mode and delayed streaming support (Emil Brandvold)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 359 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Batch mode bugs across Gemini and other providers; cost streaming implementation; GPT-4.1 structured output
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if batch mode response-shape bugs are root-cause or symptom of underlying Gemini integration issue   *** MUST RAISE ***
      2. Cost streaming architecture integrates cleanly with rate limiting and buffering without deadlock or latency issues   *** MUST RAISE ***
      3. GPT-4.1 structured output mapping does not conflict with Gemini or Anthropic paths and integrates into cost accounting
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine if batch mode response-shape bugs are root-cause or symptom of underlying Gemini integration issue
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. GPT-4.1 structured output integration; observability on request throughput and cost; CLI display logic
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Determine if batch mode response-shape bugs are root-cause or symptom of underlying Gemini integration issue
      2. Cost streaming architecture integrates cleanly with rate limiting and buffering without deadlock or latency issues
      3. GPT-4.1 structured output mapping does not conflict with Gemini or Anthropic paths and integrates into cost accounting   *** MUST RAISE ***
    goal        GPT-4.1 structured output mapping does not conflict with Gemini or Anthropic paths and integrates into cost accounting
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Cost accounting architecture; request processing internals; recent PR 639 review
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Determine if batch mode response-shape bugs are root-cause or symptom of underlying Gemini integration issue
      2. Cost streaming architecture integrates cleanly with rate limiting and buffering without deadlock or latency issues
      3. GPT-4.1 structured output mapping does not conflict with Gemini or Anthropic paths and integrates into cost accounting
      4. Follow-up on my image mess: the entrypoint does an apt-get at container start, which is why it wanted to be root. The batch ran to completion, the numbers looked normal, and I only found out days later because I opened the Dockerfile for an unrelated reason. Nothing anywhere told me the run had been different from every other run.   *** MUST SETTLE (clue t4.r2.L10) ***
    goal        the team agrees a run whose image needed root completed with no indication anything was different
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Batch mode bugs are diagnosed as Gemini-specific; cost streaming path is validated; GPT-4.1 integrates without conflict; it is settled that the team agrees a run whose image needed root completed with no indication anything was different


==============================================================================
# 2025-04-16 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two new PRs opened today plus a stale one waiting; cost streaming landed and response object variant needs review before Gideon Halloway can move forward

    Today is Wednesday 16 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two new PRs opened today plus a stale one waiting; cost streaming landed and response object variant needs review before Gideon Halloway can move forward
    
    What it should get through:
      1. Confirm PR 643 response object approach does not conflict with PR 642 structured output mapping   [Emil Brandvold must raise this]
           - Emil explains the response object pattern to Dario Kestrel
           - Dario flags the Devraj Kulaskar overlap
           - Gideon clarifies where his batch work intersects
      2. Get PR 632 batch update frequency unblocked so Gideon Halloway can finalize CLI observability   [Gideon Halloway must raise this]
           - Gideon raises the blocker
           - Emil or Dario Kestrel reviews the threshold logic
           - Signoff deferred to async or quick iteration
      3. Document the cost-streaming pattern for future provider integrations   [Emil Brandvold must raise this]
           - Emil walks through what PR 638 changed
           - Dario asks about edge cases with batch API latency
           - Agreement on pattern or deferral to WS-054 notes
    
    On the agenda: Cost streaming in batch mode (PR 638 merged, PR 643 follow-up); Structured output support coordination (Devraj Kulaskar's PR 642, Gideon Halloway's concern); CLI batch update frequency review (PR 632)
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 643 signoff or light iteration; PR 632 move forward; clarity on whether Devraj Kulaskar's PR 642 and Gideon Halloway's batch work diverge or converge
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 332 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 642: Add gpt-4.1 structured output support (Devraj Kulaskar)
      - PR 643: feat: add response object in curator (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. cost streaming implementation in batch mode; response object refactoring
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 643 response object approach does not conflict with PR 642 structured output mapping   *** MUST RAISE ***
      2. Get PR 632 batch update frequency unblocked so Gideon Halloway can finalize CLI observability
      3. Document the cost-streaming pattern for future provider integrations   *** MUST RAISE ***
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 643 response object approach does not conflict with PR 642 structured output mapping
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on batch update frequency and CLI observability
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 643 response object approach does not conflict with PR 642 structured output mapping
      2. Get PR 632 batch update frequency unblocked so Gideon Halloway can finalize CLI observability   *** MUST RAISE ***
      3. Document the cost-streaming pattern for future provider integrations
      4. that the doc "Weekly Notes — Week of Apr 14" is done, and where the others can find it   *** MUST RAISE ***
    goal        Get PR 632 batch update frequency unblocked so Gideon Halloway can finalize CLI observability
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. senior review on request processing changes; knowledge of API incompatibilities emerging
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 643 response object approach does not conflict with PR 642 structured output mapping
      2. Get PR 632 batch update frequency unblocked so Gideon Halloway can finalize CLI observability
      3. Document the cost-streaming pattern for future provider integrations
    goal        Two new PRs opened today plus a stale one waiting; cost streaming landed and response object variant needs review before Gideon Halloway can move forward
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 643 signoff or light iteration; PR 632 move forward; clarity on whether Devraj Kulaskar's PR 642 and Gideon Halloway's batch work diverge or converge


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: One merged PR, two new ones opened, and a new issue raised; mid-flight workstream needs status alignment

    Today is Wednesday 16 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One merged PR, two new ones opened, and a new issue raised; mid-flight workstream needs status alignment
    
    What it should get through:
      1. Clarify whether GPT-4.1 structured output mapping merges from Devraj Kulaskar (direct) or Gideon Halloway (via batch work)   [Emil Brandvold must raise this]
           - Emil notes both PR 642 (Devraj Kulaskar) and Gideon Halloway's batch work touch this
           - Dario or Gideon Halloway says which is primary
           - Decision or deferral to code-review channel
      2. Triage Gemini 2.0/2.5 API incompatibility: blocker or known backlog   [Dario Kestrel must raise this]
           - Dario opens issue PR 641
           - Gideon or Emil Brandvold says if it affects live runs
           - Decision to hotfix or defer
      3. Confirm cost streaming pattern ready for next week's provider work   [Emil Brandvold must raise this]
           - Emil says PR 638 merged, PR 643 follows
           - Dario confirms no blocking concerns
           - Gideon notes CLI impact minimal
    
    On the agenda: Cost streaming landed; response object variant; GPT-4.1 structured output path (two directions?); Gemini 2.0/2.5 incompatibility triage
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Direction clear on GPT-4.1 path; Gemini issue triaged; cost streaming readiness confirmed for next sprint
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 332 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 642: Add gpt-4.1 structured output support (Devraj Kulaskar)
      - PR 643: feat: add response object in curator (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. cost streaming landed; response object variant ready; April Grind status
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify whether GPT-4.1 structured output mapping merges from Devraj Kulaskar (direct) or Gideon Halloway (via batch work)   *** MUST RAISE ***
      2. Triage Gemini 2.0/2.5 API incompatibility: blocker or known backlog
      3. Confirm cost streaming pattern ready for next week's provider work   *** MUST RAISE ***
    goal        Clarify whether GPT-4.1 structured output mapping merges from Devraj Kulaskar (direct) or Gideon Halloway (via batch work)
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI observability fixes; projected-total/remaining readout corrections
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clarify whether GPT-4.1 structured output mapping merges from Devraj Kulaskar (direct) or Gideon Halloway (via batch work)
      2. Triage Gemini 2.0/2.5 API incompatibility: blocker or known backlog
      3. Confirm cost streaming pattern ready for next week's provider work
    goal        One merged PR, two new ones opened, and a new issue raised; mid-flight workstream needs status alignment
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. API incompatibility issue opened (Gemini 2.0 vs 2.5)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clarify whether GPT-4.1 structured output mapping merges from Devraj Kulaskar (direct) or Gideon Halloway (via batch work)
      2. Triage Gemini 2.0/2.5 API incompatibility: blocker or known backlog   *** MUST RAISE ***
      3. Confirm cost streaming pattern ready for next week's provider work
    goal        Triage Gemini 2.0/2.5 API incompatibility: blocker or known backlog
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Direction clear on GPT-4.1 path; Gemini issue triaged; cost streaming readiness confirmed for next sprint


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Cost streaming landed in batch mode and response object variant opens; core request-layer services touch all three commit/PR areas

    Today is Wednesday 16 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Cost streaming landed in batch mode and response object variant opens; core request-layer services touch all three commit/PR areas
    
    What it should get through:
      1. Confirm cost streaming does not break rate-limit calculation or capacity checks   [Emil Brandvold must raise this]
           - Emil explains delayed streaming model
           - Dario asks if rate-limit accounting sees partial costs
           - Gideon notes whether has_capacity logic needs update
      2. Ensure projected-remaining readout survives cost streaming delays   [Gideon Halloway must raise this]
           - Gideon raises concern or confirms it works
           - Emil says if PR 643 handles it or deferred
           - Dario notes if bulk inference is affected
      3. Align batch and online cost representation so they stay consistent   [Emil Brandvold must raise this]
           - Emil walks through cost model across both paths
           - Dario flags any divergence in how costs accrue
           - Agreement or note for next sprint
    
    On the agenda: Cost streaming in batch mode and delayed support (PR 638, PR 643); Rate limit accounting with streaming costs; Progress bar and projected-remaining accuracy with cost delays
    
    Meeting today: Weekly sync
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost streaming safety confirmed or edge cases noted for code review; progress bar impact clear; batch/online cost consistency aligned
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 332 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 642: Add gpt-4.1 structured output support (Devraj Kulaskar)
      - PR 643: feat: add response object in curator (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. cost streaming implementation; batch mode response object refactor; April Grind progress
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm cost streaming does not break rate-limit calculation or capacity checks   *** MUST RAISE ***
      2. Ensure projected-remaining readout survives cost streaming delays
      3. Align batch and online cost representation so they stay consistent   *** MUST RAISE ***
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm cost streaming does not break rate-limit calculation or capacity checks
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Gemini incompatibility report; bulk inference perspective
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm cost streaming does not break rate-limit calculation or capacity checks
      2. Ensure projected-remaining readout survives cost streaming delays
      3. Align batch and online cost representation so they stay consistent
    goal        Cost streaming landed in batch mode and response object variant opens; core request-layer services touch all three commit/PR areas
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI observability context; progress bar impact of cost streaming
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm cost streaming does not break rate-limit calculation or capacity checks
      2. Ensure projected-remaining readout survives cost streaming delays   *** MUST RAISE ***
      3. Align batch and online cost representation so they stay consistent
    goal        Ensure projected-remaining readout survives cost streaming delays
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Cost streaming safety confirmed or edge cases noted for code review; progress bar impact clear; batch/online cost consistency aligned


------------------------------------------------------------------------------
## #cookbooks — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Konrad Feltrin reran the code-verification step of a published reasoning-dataset script on Monday and got a different pass rate than the number in the README, with no commit in between

    Today is Wednesday 16 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad Feltrin reran the code-verification step of a published reasoning-dataset script on Monday and got a different pass rate than the number in the README, with no commit in between
    
    What it should get through:
    
    On the agenda: Konrad Feltrin walks through the diff in pass rate and the fact that the only thing that moved was what docker pulled; Nikolai Berresford says the Docker backend of CodeExecutor asks for the sandbox image by name with no tag, so whatever is newest wins, and states the shape of the feature: a pinned tag plus a way for callers to override it through backend_params; open question nobody answers: which tag to pin to, and whether the pinned value lives in code or somewhere a user can set without editing curator
    
    Wrap when: agreement that the image has to stop floating and that callers need an override, with the tag value, the override key name and where the default lives all still undecided; Nikolai Berresford says he will look at what the sandbox repo actually publishes; it is settled that Dermot Callaghan got outputs from the old model after editing the model name and restarting
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 332 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 642: Add gpt-4.1 structured output support (Devraj Kulaskar)
      - PR 643: feat: add response object in curator (Emil Brandvold)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: gpt-4o, gpt-4o-mini.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Konrad Feltrin reran the code-verification step of a published reasoning-dataset script on Monday and got a different pass rate than the number in the README, with no commit in between
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit.   *** MUST SETTLE (clue t3.r2.l_model_dermot) ***
         must contain literally: gpt-4o-mini, gpt-4o
    goal        Dermot Callaghan got outputs from the old model after editing the model name and restarting
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   agreement that the image has to stop floating and that callers need an override, with the tag value, the override key name and where the default lives all still undecided; Nikolai Berresford says he will look at what the sandbox repo actually publishes; it is settled that Dermot Callaghan got outputs from the old model after editing the model name and restarting; Dermot Callaghan got outputs from the old model after editing the model name and restarting


==============================================================================
# 2025-04-17 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs merged today touch cost accounting and progress display; need to ensure they don't conflict

    Today is Thursday 17 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs merged today touch cost accounting and progress display; need to ensure they don't conflict
    
    What it should get through:
      1. Land PR 644 or identify what the stats-display contract needs to handle   [Gideon Halloway must raise this]
           - Gideon raises the fix and what it addresses
           - Emil checks whether it covers batch-mode cost rollup
           - Approval or request for revision
    
    On the agenda: Gideon's PR 644 stats-display fix: scope and edge cases; Whether Devraj Kulaskar's GPT-4.1 structured output mapping (merged PR 642) needs follow-up in the stats layer
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 644 approved or rework identified; it is settled that the team agrees the container's protections must not be a side effect of using the default tag
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. The stats-display fix and its interaction with batch-mode progress tracking
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 644 or identify what the stats-display contract needs to handle   *** MUST RAISE ***
    goal        Land PR 644 or identify what the stats-display contract needs to handle
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Context on the broader stats-display contract across online and batch modes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 644 or identify what the stats-display contract needs to handle
    goal        Two PRs merged today touch cost accounting and progress display; need to ensure they don't conflict
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Historical context on what the stats-display interface promised
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 644 or identify what the stats-display contract needs to handle
      2. Pinning the tag is a reproducibility fix. Whether the container is locked down is a different axis and I do not want it riding on which tag you happen to get handed.   *** MUST SETTLE (clue t4.r2.L8) ***
    goal        the team agrees the container's protections must not be a side effect of using the default tag
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 644 approved or rework identified; it is settled that the team agrees the container's protections must not be a side effect of using the default tag


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Two commits today touch provider-integrations and online-request-processing; need to ensure the structured-output mapping doesn't break cost or progress accounting

    Today is Thursday 17 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two commits today touch provider-integrations and online-request-processing; need to ensure the structured-output mapping doesn't break cost or progress accounting
    
    What it should get through:
      1. Confirm GPT-4.1 structured output mapping doesn't create blind spots in cost or progress tracking   [Emil Brandvold must raise this]
           - Emil raises the risk of a new response shape breaking accounting
           - Gideon describes what PR 644 covers
           - Dario confirms online-request-processing handles it or identifies what's missing
    
    On the agenda: Devraj's GPT-4.1 structured output mapping (merged PR 642) integration with stats layer; Whether the stats-display fix in PR 644 handles all response shapes
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Confidence that GPT-4.1 responses are tracked correctly, or a task identified for follow-up; it is settled that the team agrees STRUCTURED_OUTPUT_MODELS is the list that gets edited when a new model like o3 ships
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: STRUCTURED_OUTPUT_MODELS, o3.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Overall picture of the RPM and cost-accounting work, and where GPT-4.1 structured output fits
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm GPT-4.1 structured output mapping doesn't create blind spots in cost or progress tracking   *** MUST RAISE ***
    goal        Confirm GPT-4.1 structured output mapping doesn't create blind spots in cost or progress tracking
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. What the stats-display fix does and how it handles structured-output responses
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm GPT-4.1 structured output mapping doesn't create blind spots in cost or progress tracking
    goal        Two commits today touch provider-integrations and online-request-processing; need to ensure the structured-output mapping doesn't break cost or progress accounting
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Operational knowledge of online-request-processing internals and retry semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm GPT-4.1 structured output mapping doesn't create blind spots in cost or progress tracking
      2. o3 support was basically free for us. I put the model name into STRUCTURED_OUTPUT_MODELS the morning it went live and structured output worked on the online path that afternoon, no other diff.   *** MUST SETTLE (clue t2.r2.l1) ***
         must contain literally: STRUCTURED_OUTPUT_MODELS, o3
    goal        the team agrees STRUCTURED_OUTPUT_MODELS is the list that gets edited when a new model like o3 ships
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Confidence that GPT-4.1 responses are tracked correctly, or a task identified for follow-up; it is settled that the team agrees STRUCTURED_OUTPUT_MODELS is the list that gets edited when a new model like o3 ships


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Two mid-flight workstreams need a weekly sync; two new PRs opened; need to align on release readiness

    Today is Thursday 17 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two mid-flight workstreams need a weekly sync; two new PRs opened; need to align on release readiness
    
    What it should get through:
      1. Land or defer the open PRs based on workstream state   [Emil Brandvold must raise this]
           - Emil summarizes the backlog and risk
           - Dario flags whether any are blocking April Grind
           - Decision: merge, hold, or defer
    
    On the agenda: State of Batch Mode Provider Bug Sweep and what's left; State of April Grind: RPM, Cost Accounting, GPT-4.1; Whether this week's changes are ready to ship or need more vetting; Open PRs: PR 640 (DeepSeek API), PR 645 (dtype flag), PR 643 (response object)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Alignment on what ships this week and what waits; unblocked team to keep moving
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The state of both mid-flight workstreams: what landed, what's stuck, what's next
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land or defer the open PRs based on workstream state   *** MUST RAISE ***
    goal        Land or defer the open PRs based on workstream state
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Fresh perspective on the stats-display work and whether it unblocks anything downstream
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land or defer the open PRs based on workstream state
    goal        Two mid-flight workstreams need a weekly sync; two new PRs opened; need to align on release readiness
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. View of the request-processing backlog and any accumulating tech debt
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land or defer the open PRs based on workstream state
    goal        Two mid-flight workstreams need a weekly sync; two new PRs opened; need to align on release readiness
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release perspective and whether the week's changes are stable
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land or defer the open PRs based on workstream state
    goal        Two mid-flight workstreams need a weekly sync; two new PRs opened; need to align on release readiness
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Alignment on what ships this week and what waits; unblocked team to keep moving


------------------------------------------------------------------------------
## #random — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #random: gossip about a provider's batch queue being slow turns into war stories about batches nobody could recover

    Today is Thursday 17 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: gossip about a provider's batch queue being slow turns into war stories about batches nobody could recover
    
    What it should get through:
    
    On the agenda: Gideon Halloway on an Anthropic batch that hit the 24h window and expired while his laptop was shut, and the rerun happily reporting it as pending forever; Emil Brandvold mentions cancelling a Mistral batch from the dashboard mid-run and then having the script sit there waiting on it; Dermot Callaghan says in both of those cases the requests plainly have to go out again, they were never going to come back
    
    Wrap when: stays a war-story thread, but Dermot Callaghan's line about resending is the first time anyone says what should happen to dead batches; it is settled that the team agrees a counting helper that creates the directory can cause a full re-billed run
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)

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

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. self-inflicted, posting so nobody else does it. I typo'd the path in my cache-poking script last night, it did a mkdir -p on the way in, and this morning's cookbook run found a shiny empty cache directory at the typo, decided nothing was cached and re-sent 38k requests. Bill is real. The script only ever wanted to count rows.   *** MUST SETTLE (clue t1.r2.L4) ***
    goal        the team agrees a counting helper that creates the directory can cause a full re-billed run
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        gossip about a provider's batch queue being slow turns into war stories about batches nobody could recover
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        gossip about a provider's batch queue being slow turns into war stories about batches nobody could recover
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   stays a war-story thread, but Dermot Callaghan's line about resending is the first time anyone says what should happen to dead batches; it is settled that the team agrees a counting helper that creates the directory can cause a full re-billed run

