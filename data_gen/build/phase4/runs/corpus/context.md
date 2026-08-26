# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-05-13 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five pull requests older than the era median merge time need review and decision

    Today is Tuesday 13 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five pull requests older than the era median merge time need review and decision
    
    What it should get through:
      1. Clarify why the five PRs are stalled and what each needs to merge   [Emil Brandvold must raise this]
           - Emil surfaces the oldest and most critical ones (652, 654)
           - Nikolai flags blockers on 653 and 663
           - They land on a priority order
      2. Establish whether any are actually blocked on external input or just need eyes   [Nikolai Berresford must raise this]
           - Nikolai explains what's holding 663
           - Emil checks whether reviewer bandwidth or code issues are the constraint
    
    On the agenda: Review status of five stale PRs (652, 653, 654, 658, 663); Identify blockers preventing merge; Decide priority and next steps for unblocking
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Priority list for PR review; understanding of whether the backlog is a bandwidth problem or a design problem waiting for decision
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 346 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release engineering expertise and visibility into which PRs are blocking deployment
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify why the five PRs are stalled and what each needs to merge   *** MUST RAISE ***
      2. Establish whether any are actually blocked on external input or just need eyes
    goal        Clarify why the five PRs are stalled and what each needs to merge
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution knowledge and ownership of outstanding changes
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Clarify why the five PRs are stalled and what each needs to merge
      2. Establish whether any are actually blocked on external input or just need eyes   *** MUST RAISE ***
    goal        Establish whether any are actually blocked on external input or just need eyes
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Priority list for PR review; understanding of whether the backlog is a bandwidth problem or a design problem waiting for decision


------------------------------------------------------------------------------
## #pipeline — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: PR 666 merged; brief sync to confirm logger cleanup is complete in the provider/request layer

    Today is Tuesday 13 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 666 merged; brief sync to confirm logger cleanup is complete in the provider/request layer
    
    What it should get through:
      1. Confirm logger.warning migration is complete and merged cleanly   [Emil Brandvold must raise this]
           - Emil notes the PR merged
           - Dermot confirms no regressions in request layer tests
    
    On the agenda: Confirm PR 666 (logger.warning migration) closes the issue; Check for any remaining deprecated logging patterns in the request pipeline
    
    Out today: Dario Kestrel (no commit, review or comment 2025-05-08..2025-05-25) — their input is missing and people may say so
    
    No longer here: Gideon Halloway, Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Handoff complete; no follow-up work needed on logging cleanup this cycle
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 346 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release engineering and provider integration context
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm logger.warning migration is complete and merged cleanly   *** MUST RAISE ***
    goal        Confirm logger.warning migration is complete and merged cleanly
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Request processing expertise and understanding of any remaining deprecation warnings
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm logger.warning migration is complete and merged cleanly
    goal        PR 666 merged; brief sync to confirm logger cleanup is complete in the provider/request layer
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Handoff complete; no follow-up work needed on logging cleanup this cycle


==============================================================================
# 2025-05-20 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil landed a perf fix for batch-mode and wants to frame the work before moving deeper.

    Today is Tuesday 20 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil landed a perf fix for batch-mode and wants to frame the work before moving deeper.
    
    What it should get through:
      1. Confirm that lazy loading in Gemini download is the right fix   [Emil Brandvold must raise this]
           - Emil describes the upfront work in the current path
           - Nikolai asks whether this affects other providers or just Gemini
           - Emil clarifies scope and landing
    
    On the agenda: The performance issue Emil found in Gemini batch downloads; Why making it lazy matters for large jobs; Whether the fix in PR 654 covers all download paths
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Emil and Nikolai align on whether this is a one-off Gemini fix or a pattern to apply elsewhere; no blocking decision, just framing for the next step.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 347 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 328 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the performance problem in Gemini's batch download path and the fix he just landed
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm that lazy loading in Gemini download is the right fix   *** MUST RAISE ***
    goal        Confirm that lazy loading in Gemini download is the right fix
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. perspective on code execution and release mechanics from his own PRs
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm that lazy loading in Gemini download is the right fix
    goal        Emil landed a perf fix for batch-mode and wants to frame the work before moving deeper.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Emil and Nikolai align on whether this is a one-off Gemini fix or a pattern to apply elsewhere; no blocking decision, just framing for the next step.


==============================================================================
# 2025-05-21 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: PR PR 658 merged; agent response format not yet finalized; examples stale; downstream work waiting on clarity.

    Today is Wednesday 21 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 658 merged; agent response format not yet finalized; examples stale; downstream work waiting on clarity.
    
    What it should get through:
      1. Settle response object shape for agent outputs   [Emil Brandvold must raise this]
           - Emil lays out what the agent currently returns and what's missing
           - Konrad presses on how it feeds into fine-tuning pipelines
           - Decision: add response object before PR PR 653 lands
      2. Align examples with live agent implementation   [Emil Brandvold must raise this]
           - Emil walks through what changed in agent API
           - Nikolai asks if it affects the recipe cookbooks
           - Agreement to update examples before documenting
    
    On the agenda: Response object design for agents; Example script sync with actual agent usage; Unblocking dependent work
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Response object shape decided; examples marked for update; path clear for PR 653 and downstream code-execution work.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 348 changes merged to date

    On the table
      - Weekly Notes — Week of May 19 (Emil Brandvold)
      - notes-2025-05-19 (Emil Brandvold)
      - Weekly Notes — Week of May 19 (Emil Brandvold)
      - notes-2025-05-19 (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 282 function/class names and 29 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. where the agent work stands, what's unblocked next, which examples need updating
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Settle response object shape for agent outputs   *** MUST RAISE ***
      2. Align examples with live agent implementation   *** MUST RAISE ***
      3. that the doc "Weekly Notes — Week of May 19" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Weekly Notes — Week of May 19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly Notes — Week of May 19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Settle response object shape for agent outputs
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. perspective on how response format lands in downstream pipelines
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Settle response object shape for agent outputs
      2. Align examples with live agent implementation
    goal        PR PR 658 merged; agent response format not yet finalized; examples stale; downstream work waiting on clarity.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. knows the recipe/cookbooks patterns and CI constraints
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Settle response object shape for agent outputs
      2. Align examples with live agent implementation
    goal        PR PR 658 merged; agent response format not yet finalized; examples stale; downstream work waiting on clarity.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Response object shape decided; examples marked for update; path clear for PR 653 and downstream code-execution work.


==============================================================================
# 2025-05-22 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil's agentic multiturn feature merged today; three PRs aging without closure

    Today is Thursday 22 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil's agentic multiturn feature merged today; three PRs aging without closure
    
    What it should get through:
      1. Confirm PR 667 approach before it lands   [Emil Brandvold must raise this]
           - Emil describes the agent-on-top-of-LLM pattern and stopping criterion
           - Konrad questions integration with existing recipes
           - Nikolai flags how code execution verification fits in
      2. Prioritize stale PR closure path   [Konrad Feltrin must raise this]
           - Emil notes PR 652 blocked 27 days on viewer download feature
           - Nikolai acknowledges PR 653 and PR 663 need attention but may wait
           - Konrad suggests clearing these before next feature cycle
    
    On the agenda: Review of PR 667 agentic multiturn example changes; Integration with existing curation pipeline; Status of stale PRs (PR 652, PR 653, PR 663)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 667 lands with clear understanding of multiturn agent semantics; team aligns on stale PR triage for next week
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 349 changes merged to date

    On the table
      - Weekly Notes — Week of May 19 (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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
      - — and 285 function/class names and 29 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The multiturn agent implementation and feature design
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 667 approach before it lands   *** MUST RAISE ***
      2. Prioritize stale PR closure path
      3. what "Weekly Notes — Week of May 19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 667 approach before it lands
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Expertise in examples and recipes; already reviewed PR 667
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 667 approach before it lands
      2. Prioritize stale PR closure path   *** MUST RAISE ***
    goal        Prioritize stale PR closure path
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution and verification perspective for agentic systems
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm PR 667 approach before it lands
      2. Prioritize stale PR closure path
    goal        Emil's agentic multiturn feature merged today; three PRs aging without closure
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 667 lands with clear understanding of multiturn agent semantics; team aligns on stale PR triage for next week


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil shipped agentic multiturn; Konrad completed factory cleanup; kickoff stage conversation

    Today is Thursday 22 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil shipped agentic multiturn; Konrad completed factory cleanup; kickoff stage conversation
    
    What it should get through:
      1. Explain agentic curation pattern and unblocks   [Emil Brandvold must raise this]
           - Emil walks through agent-on-LLM with stopping criterion
           - Konrad asks how it fits with RAFT and SimpleStrat recipes
           - Nikolai probes code execution verifier integration
      2. Understand factory cleanup scope and impact   [Konrad Feltrin must raise this]
           - Konrad explains the three cleanup commits
           - Emil asks if any PRs are affected
           - Konrad confirms it's prep for the next wave
    
    On the agenda: Emil's multiturn agent feature and what it unblocks; Integration with code execution and verification; Cleanup work Konrad did in factory and linting
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team has shared mental model of agentic curation; factory cleanup understood as technical debt; next phase clear
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 349 changes merged to date

    On the table
      - Weekly Notes — Week of May 19 (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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
      - — and 285 function/class names and 29 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Agentic curation feature implementation and release coordination
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Explain agentic curation pattern and unblocks   *** MUST RAISE ***
      2. Understand factory cleanup scope and impact
      3. what "Weekly Notes — Week of May 19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Explain agentic curation pattern and unblocks
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Examples, recipes, code-execution integration perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Explain agentic curation pattern and unblocks
      2. Understand factory cleanup scope and impact   *** MUST RAISE ***
    goal        Understand factory cleanup scope and impact
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Understanding of code execution, telemetry, and data-generation recipes
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Explain agentic curation pattern and unblocks
      2. Understand factory cleanup scope and impact
    goal        Emil shipped agentic multiturn; Konrad completed factory cleanup; kickoff stage conversation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team has shared mental model of agentic curation; factory cleanup understood as technical debt; next phase clear


==============================================================================
# 2025-05-23 — 3 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 7 opened and 11 reviewed today; three PRs older than the era median merge; two drivers present

    Today is Friday 23 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 opened and 11 reviewed today; three PRs older than the era median merge; two drivers present
    
    What it should get through:
      1. Confirm agentic response format and viewer link integration merged cleanly   [Emil Brandvold must raise this]
           - Emil flags the five merges and their scope
           - Konrad confirms he reviewed and approved the key ones
           - Both agree the OpenAI-compatible format is locked
      2. Decide what to do with 28-day-old PR 652 and similar stale work   [Konrad Feltrin must raise this]
           - Konrad raises that 652 sits waiting
           - Emil notes it was his own PR and may need rebasing or rethinking
           - They defer to next week or mark it blocked
    
    On the agenda: Review status of five merged agentic/examples PRs; Triage stale PRs: 652, 653, 663; Konrad's factory cleanup rationale
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Five merged PRs confirmed; stale PRs triaged or deferred; factory cleanup acknowledged as straightforward and safe.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 354 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 674: Delete HOSTED_CURATOR_VIEWER environment variable. (Konrad Feltrin)

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
    role        Core Platform Engineer, Request Processing. drove five features merged in two days; knows the agentic API surface and examples refresh inside-out
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm agentic response format and viewer link integration merged cleanly   *** MUST RAISE ***
      2. Decide what to do with 28-day-old PR 652 and similar stale work
    goal        Confirm agentic response format and viewer link integration merged cleanly
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. factory cleanup done; familiar with the viewer environment variable removal scope
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm agentic response format and viewer link integration merged cleanly
      2. Decide what to do with 28-day-old PR 652 and similar stale work   *** MUST RAISE ***
    goal        Decide what to do with 28-day-old PR 652 and similar stale work
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Five merged PRs confirmed; stale PRs triaged or deferred; factory cleanup acknowledged as straightforward and safe.


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Four commits to agentic-curation merged today; feature landing after two-day sprint; no blockers reported

    Today is Friday 23 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four commits to agentic-curation merged today; feature landing after two-day sprint; no blockers reported
    
    What it should get through:
      1. Agentic multi-turn lands with OpenAI-compatible response format and viewer trace links   [Emil Brandvold must raise this]
           - Emil explains the five-PR sequence and what each shipped
           - Konrad confirms factory cleanup is orthogonal and safe
           - Both agree the shape matches OpenAI and traces are now observable
      2. Confirm OpenAI format does not break existing user code or downstream integrations   [Emil Brandvold must raise this]
           - Emil flags any breaking changes are in the agent response shape only
           - Konrad notes the environment variable removal is unrelated
           - They agree to mention both in release notes
    
    On the agenda: Agentic multi-turn feature summary: response format and viewer integration; OpenAI compatibility impact on downstream code; Factory cleanup and environment variable removal merged in parallel
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Agentic multi-turn feature confirmed shipped and stable; OpenAI format locked in; cleanup work acknowledged as safe parallels.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 354 changes merged to date

    On the table
      - v0.1.24 Release Notes (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 674: Delete HOSTED_CURATOR_VIEWER environment variable. (Konrad Feltrin)

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
    role        Core Platform Engineer, Request Processing. just landed five commits making agentic curation response format OpenAI-compatible and adding viewer trace links
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Agentic multi-turn lands with OpenAI-compatible response format and viewer trace links   *** MUST RAISE ***
      2. Confirm OpenAI format does not break existing user code or downstream integrations   *** MUST RAISE ***
      3. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Agentic multi-turn lands with OpenAI-compatible response format and viewer trace links
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. shipping the environment variable cleanup and factory simplification in parallel
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Agentic multi-turn lands with OpenAI-compatible response format and viewer trace links
      2. Confirm OpenAI format does not break existing user code or downstream integrations
    goal        Four commits to agentic-curation merged today; feature landing after two-day sprint; no blockers reported
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Agentic multi-turn feature confirmed shipped and stable; OpenAI format locked in; cleanup work acknowledged as safe parallels.


------------------------------------------------------------------------------
## #cookbooks — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Two changes to examples-cookbooks merged today; release-and-ci changes in flight; examples flagged out of date and now refreshed

    Today is Friday 23 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two changes to examples-cookbooks merged today; release-and-ci changes in flight; examples flagged out of date and now refreshed
    
    What it should get through:
      1. Provider-swap and agentic examples are current and ready to ship   [Emil Brandvold must raise this]
           - Emil flagged examples were out of date and opens refresh PR
           - Konrad approves the changes
           - Both confirm they reflect the current API
      2. Examples remain functional against live provider APIs and do not bitrot   [Konrad Feltrin must raise this]
           - Konrad asks if examples have been run locally
           - Emil says they follow the new OpenAI format
           - They agree to add a reminder about testing before release
    
    On the agenda: Refreshed provider-swap and agentic examples merged; Verify all example code matches current API surface; Examples readiness for next release
    
    Out today: Dermot Callaghan (no commit, review or comment 2025-05-18..2025-06-25) — their input is missing and people may say so
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Provider and agentic examples confirmed current; API surface alignment verified; examples flagged as release-ready pending testing.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 354 changes merged to date

    On the table
      - v0.1.24 Release Notes (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 674: Delete HOSTED_CURATOR_VIEWER environment variable. (Konrad Feltrin)

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
    role        Core Platform Engineer, Request Processing. refreshed provider examples and agentic curation examples; knows what changed in the example code
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Provider-swap and agentic examples are current and ready to ship   *** MUST RAISE ***
      2. Examples remain functional against live provider APIs and do not bitrot
      3. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Provider-swap and agentic examples are current and ready to ship
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. reviewed the examples; familiar with what the cleanup touched
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Provider-swap and agentic examples are current and ready to ship
      2. Examples remain functional against live provider APIs and do not bitrot   *** MUST RAISE ***
    goal        Examples remain functional against live provider APIs and do not bitrot
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Provider and agentic examples confirmed current; API surface alignment verified; examples flagged as release-ready pending testing.

