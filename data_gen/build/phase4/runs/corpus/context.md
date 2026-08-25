# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-01-31 — 2 conversation(s), 22 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs merged today close SimpleLLM consolidation; PR 427 multimodal support is next and needs eyes.

    Today is Friday 31 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today close SimpleLLM consolidation; PR 427 multimodal support is next and needs eyes.
    
    What it should get through:
      1. Land PR 427 or identify what needs fixing before merge   [Emil Brandvold must raise this]
           - Emil describes what PR 427 adds to the LLM interface
           - Nikolai flags if executor changes conflict
           - Dario confirms cost tracking still works
      2. Confirm PR 428 and PR 429 close the interface debt without side effects   [Dermot Callaghan must raise this]
           - Dermot walks both fixes — args[0] removal and litellm.cost check
           - Nikolai confirms docker/multiprocessing backends still work
           - Team agrees the month's interface consolidation is done
    
    On the agenda: Review PR 427 multimodal support against cost interface; Confirm PR 428 and PR 429 merged without regressions; Settle PR 427 blocking status for v0.1.18
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 427 either clears review or goes back to Emil with specific feedback; PR 428 and PR 429 confirmed stable.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 216 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 427: Feat/multi modal support (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Knowledge of the SimpleLLM consolidation arc and what PR 427 multimodal support needs from the core
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 427 or identify what needs fixing before merge   *** MUST RAISE ***
      2. Confirm PR 428 and PR 429 close the interface debt without side effects
      3. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 427 or identify what needs fixing before merge
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just shipped two cost-handling fixes (PR 428 and PR 429) that close out interface consolidation
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 427 or identify what needs fixing before merge
      2. Confirm PR 428 and PR 429 close the interface debt without side effects   *** MUST RAISE ***
    goal        Confirm PR 428 and PR 429 close the interface debt without side effects
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Approved both cost fixes and knows what the multiprocessing and docker backends need
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Land PR 427 or identify what needs fixing before merge
      2. Confirm PR 428 and PR 429 close the interface debt without side effects
    goal        Three PRs merged today close SimpleLLM consolidation; PR 427 multimodal support is next and needs eyes.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Approved the cost fix in PR 429 and owns the request layer
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 427 or identify what needs fixing before merge
      2. Confirm PR 428 and PR 429 close the interface debt without side effects
    goal        Three PRs merged today close SimpleLLM consolidation; PR 427 multimodal support is next and needs eyes.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 427 either clears review or goes back to Emil with specific feedback; PR 428 and PR 429 confirmed stable.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Twelve commits landed today across core LLM and docs; week ending with SimpleLLM consolidation closing and multimodal support opening.

    Today is Friday 31 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Twelve commits landed today across core LLM and docs; week ending with SimpleLLM consolidation closing and multimodal support opening.
    
    What it should get through:
      1. Agree whether PR 427 multimodal support lands this week or defers to v0.1.18   [Emil Brandvold must raise this]
           - Emil describes PR 427 scope and readiness
           - Dario and Nikolai confirm no conflicts with their pending work
           - Team decides merge timing
      2. Confirm the cost refactoring in PR 428/#429 didn't regress the interface   [Dermot Callaghan must raise this]
           - Dermot walks both fixes
           - Team confirms they are mergeable and low-risk
      3. Sync on executor refactor impact and settle next week's blockers   [Nikolai Berresford must raise this]
           - Nikolai describes the executor rename and what it unblocks
           - Dario flags any impact on pending work
           - Team notes open issues like PR 407 verifiers and PR 411 CI cache
    
    On the agenda: What shipped today and what's pending; State of the SimpleLLM consolidation and multimodal support; Unblock list for next week
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Shared understanding of what is shipping this week vs next; confirmation that SimpleLLM consolidation is done and executor refactor is safe.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 216 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 427: Feat/multi modal support (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Landed 11 commits today: code executor rename, multiprocessing and docker backend fixes, PostHog telemetry wiring, and the Bespoke-Stratos directory rename
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Agree whether PR 427 multimodal support lands this week or defers to v0.1.18
      2. Confirm the cost refactoring in PR 428/#429 didn't regress the interface
      3. Sync on executor refactor impact and settle next week's blockers   *** MUST RAISE ***
      4. that the doc "Postmortem: v0.1.17.post1 hotfix" is done, and where the others can find it   *** MUST RAISE ***
    goal        Sync on executor refactor impact and settle next week's blockers
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Shipped docs news section (PR 426) and opened multimodal support (PR 427); driving the SimpleLLM consolidation to close
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Agree whether PR 427 multimodal support lands this week or defers to v0.1.18   *** MUST RAISE ***
      2. Confirm the cost refactoring in PR 428/#429 didn't regress the interface
      3. Sync on executor refactor impact and settle next week's blockers
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Agree whether PR 427 multimodal support lands this week or defers to v0.1.18
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Two cost-handling fixes merged same-day; knows the state of the core LLM interface
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree whether PR 427 multimodal support lands this week or defers to v0.1.18
      2. Confirm the cost refactoring in PR 428/#429 didn't regress the interface   *** MUST RAISE ***
      3. Sync on executor refactor impact and settle next week's blockers
    goal        Confirm the cost refactoring in PR 428/#429 didn't regress the interface
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Approved the cost fix and owns the request layer; driving docs consolidation
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree whether PR 427 multimodal support lands this week or defers to v0.1.18
      2. Confirm the cost refactoring in PR 428/#429 didn't regress the interface
      3. Sync on executor refactor impact and settle next week's blockers
    goal        Twelve commits landed today across core LLM and docs; week ending with SimpleLLM consolidation closing and multimodal support opening.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Shared understanding of what is shipping this week vs next; confirmation that SimpleLLM consolidation is done and executor refactor is safe.


==============================================================================
# 2025-02-03 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs opened or merged today; PR 438 and PR 439 are fresh and need initial review passes

    Today is Monday 3 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs opened or merged today; PR 438 and PR 439 are fresh and need initial review passes
    
    What it should get through:
      1. Get PR 438 (general refactor) approved and ready to merge   [Emil Brandvold must raise this]
           - Emil walks through what PR 438 refactors and why
           - Dario and Konrad probe for design concerns
           - Clear decision: approve or request changes
      2. send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    
    On the agenda: Review status of PR 438 and PR 439; Clear path to merge for blocked PRs; Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 438 either approved or has specific changes requested; PR 439 is reviewed and path forward is clear. PR 430 (OpenRouter examples) is still blocked but acknowledged.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 221 changes merged to date

    On the table
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 427: Feat/multi modal support (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 438: Ref/general (Emil Brandvold)
      - PR 439: Anon telemetry (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 726 function/class names and 61 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just merged two PRs on cost mapping and token estimation; now has PR 438 (general refactor) waiting for eyes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get PR 438 (general refactor) approved and ready to merge   *** MUST RAISE ***
      2. send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    goal        Get PR 438 (general refactor) approved and ready to merge
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Already approved PR 435 and PR 437; familiar with the cost-accounting work
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Get PR 438 (general refactor) approved and ready to merge
      2. send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    goal        Four PRs opened or merged today; PR 438 and PR 439 are fresh and need initial review passes
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior context on request-processing architecture; reviewer of PR 438
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get PR 438 (general refactor) approved and ready to merge
      2. send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    goal        Four PRs opened or merged today; PR 438 and PR 439 are fresh and need initial review passes
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Already commented on PR 438; can weigh in on design questions
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get PR 438 (general refactor) approved and ready to merge
      2. send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped   *** MUST RAISE ***
      3. that "Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 438 either approved or has specific changes requested; PR 439 is reviewed and path forward is clear. PR 430 (OpenRouter examples) is still blocked but acknowledged.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 9 commits landed over weekend and into Monday; 2 PRs merged; 2 new workstreams starting; handover doc due today

    Today is Monday 3 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 9 commits landed over weekend and into Monday; 2 PRs merged; 2 new workstreams starting; handover doc due today
    
    What it should get through:
      1. Debrief what shipped over Sat-Sun and surface any breakage   [Nikolai Berresford must raise this]
           - Nikolai and Gideon describe their commits
           - Dario or Emil surface any test failures or provider issues
           - Team decides if anything needs immediate hotfix
      2. Scope multimodal and cost-map work; decide execution order   [Emil Brandvold must raise this]
           - Emil describes both WS-026 and WS-027 scope
           - Dario and Gideon ask about dependencies and blockers
           - Team settles: tackle cost-map first (unblocks online), then multimodal
      3. Confirm Dario Kestrel→Emil Brandvold handover is live and supported   [Dario Kestrel must raise this]
           - Dario walks through what's transferring: request loop, provider backends, rate limiting
           - Emil confirms he has what he needs
           - Team acknowledges Dario Kestrel is now in support mode, not driving
    
    On the agenda: What landed while we were away (Sat-Sun); Two new workstreams: multimodal and cost-map hardening; Handover: request-processing core and backends (Dario Kestrel → Emil Brandvold)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team knows what shipped and whether it broke anything. Emil and Dario are in sync on handover. WS-026 and WS-027 are scoped; team has decided which lands first. Gideon knows what multimodal means for CLI/progress display.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 221 changes merged to date

    On the table
      - weekly-2025-01-27 (Konrad Feltrin)
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - handover-request-processing-core-and-provider-bac (Dario Kestrel)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 427: Feat/multi modal support (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 438: Ref/general (Emil Brandvold)
      - PR 439: Anon telemetry (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 726 function/class names and 61 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just shipped cost-map defaults and token-estimation fixes; running two new workstreams (WS-026, WS-027)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Debrief what shipped over Sat-Sun and surface any breakage
      2. Scope multimodal and cost-map work; decide execution order   *** MUST RAISE ***
      3. Confirm Dario Kestrel→Emil Brandvold handover is live and supported
    goal        Scope multimodal and cost-map work; decide execution order
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just shipped verifiers-for-code work; now opening telemetry PR; recently landed code-execution features
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Debrief what shipped over Sat-Sun and surface any breakage   *** MUST RAISE ***
      2. Scope multimodal and cost-map work; decide execution order
      3. Confirm Dario Kestrel→Emil Brandvold handover is live and supported
      4. what "Weekly update: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Debrief what shipped over Sat-Sun and surface any breakage
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Fixed kluster online example over the weekend
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Debrief what shipped over Sat-Sun and surface any breakage
      2. Scope multimodal and cost-map work; decide execution order
      3. Confirm Dario Kestrel→Emil Brandvold handover is live and supported
    goal        9 commits landed over weekend and into Monday; 2 PRs merged; 2 new workstreams starting; handover doc due today
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. About to hand off request-processing ownership to Emil; context on what's blocked and unblocked
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Debrief what shipped over Sat-Sun and surface any breakage
      2. Scope multimodal and cost-map work; decide execution order
      3. Confirm Dario Kestrel→Emil Brandvold handover is live and supported   *** MUST RAISE ***
      4. that "Handing off request-processing core and provider backends" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Handing off request-processing core and provider backends" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Dario Kestrel→Emil Brandvold handover is live and supported
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team knows what shipped and whether it broke anything. Emil and Dario are in sync on handover. WS-026 and WS-027 are scoped; team has decided which lands first. Gideon knows what multimodal means for CLI/progress display.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 8 commits to provider-integrations, 7 to bulk-llm-inference, 7 to online-request-processing landed; two critical PRs merged (PR 435 token fix, PR 437 cost-map defaults); cost accounting is a blocker for multimodal work

    Today is Monday 3 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 8 commits to provider-integrations, 7 to bulk-llm-inference, 7 to online-request-processing landed; two critical PRs merged (PR 435 token fix, PR 437 cost-map defaults); cost accounting is a blocker for multimodal work
    
    What it should get through:
      1. Validate token-estimation fix solves output cost prediction   [Emil Brandvold must raise this]
           - Emil walks through the bug and fix
           - Dermot and Dario confirm it covers the case they saw
           - Team agrees fix is minimal and safe
      2. Identify remaining gaps in cost and rate-limit defaults   [Emil Brandvold must raise this]
           - Emil lists which providers are now in the default JSON
           - Dario flags togetherai rate limits and klusterai cost quirks still missing
           - Team decides if these block next release or can follow
      3. Land initial scope for multimodal image/file support in online path   [Emil Brandvold must raise this]
           - Emil describes what multimodal means: base64 images, PDFs, file refs
           - Gideon asks about progress display for image payloads
           - Dario notes serialization changes needed in image type
    
    On the agenda: Token estimation fix (max_tokens from generations params); Cost and rate-limit default map: completeness and coverage; Path to multimodal support (images/files in online pipeline)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Token estimation fix is validated. Cost-map gaps are enumerated; team agrees on a cutoff for this sprint vs. next release. Multimodal work has a clear entry point: start with image serialization in pipeline, then wire up to online request loop. Emil knows what Dario is handing off and what he owns now; it is settled that the team agrees adding a model means updating the maintained support list as a routine step
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 221 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 427: Feat/multi modal support (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 438: Ref/general (Emil Brandvold)
      - PR 439: Anon telemetry (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 726 function/class names and 61 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just shipped cost-map JSON defaults and token-estimation fix for max_tokens param; knows what still needs hardening
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate token-estimation fix solves output cost prediction   *** MUST RAISE ***
      2. Identify remaining gaps in cost and rate-limit defaults   *** MUST RAISE ***
      3. Land initial scope for multimodal image/file support in online path   *** MUST RAISE ***
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate token-estimation fix solves output cost prediction
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Built original cost-accounting layer; knows where the gaps are (togetherai, klusterai rate limits)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate token-estimation fix solves output cost prediction
      2. Identify remaining gaps in cost and rate-limit defaults
      3. Land initial scope for multimodal image/file support in online path
    goal        8 commits to provider-integrations, 7 to bulk-llm-inference, 7 to online-request-processing landed; two critical PRs merged (PR 435 token fix, PR 437 cost-map defaults); cost accounting is a blocker for multimodal work
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Approved the token-estimation and cost-map PRs; familiar with hardening needs
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate token-estimation fix solves output cost prediction
      2. Identify remaining gaps in cost and rate-limit defaults
      3. Land initial scope for multimodal image/file support in online path
    goal        8 commits to provider-integrations, 7 to bulk-llm-inference, 7 to online-request-processing landed; two critical PRs merged (PR 435 token fix, PR 437 cost-map defaults); cost accounting is a blocker for multimodal work
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just fixed kluster online example; saw the cost/rate-limit pain point firsthand
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate token-estimation fix solves output cost prediction
      2. Identify remaining gaps in cost and rate-limit defaults
      3. Land initial scope for multimodal image/file support in online path
      4. Our new-model routine hasn't changed in months: model name into the support list, price entry, one smoke run against a two-field pydantic model. Step one is the only step people actually forget.   *** MUST SETTLE (clue t2.r2.l3) ***
    goal        the team agrees adding a model means updating the maintained support list as a routine step
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Token estimation fix is validated. Cost-map gaps are enumerated; team agrees on a cutoff for this sprint vs. next release. Multimodal work has a clear entry point: start with image serialization in pipeline, then wire up to online request loop. Emil knows what Dario is handing off and what he owns now; it is settled that the team agrees adding a model means updating the maintained support list as a routine step


==============================================================================
# 2025-02-04 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three PRs merged today across multimodal, cost accounting and telemetry; Emil Brandvold is driving four active workstreams, all mid-flight; need to sync on what's working and what still needs eyes

    Today is Tuesday 4 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today across multimodal, cost accounting and telemetry; Emil Brandvold is driving four active workstreams, all mid-flight; need to sync on what's working and what still needs eyes
    
    What it should get through:
      1. Confirm multimodal test hardening is stable   [Emil Brandvold must raise this]
           - Emil Brandvold describes the multimodal test fixture changes and the content/url bug fixes
           - Dario Kestrel or Priya Vandersloot flags any concerns about the test assumptions or fixture scope
           - confirmation or deferral of next batch of multimodal work
      2. Unblock or defer PR 430 (reasoning with OpenRouter examples)   [Dario Kestrel must raise this]
           - Dario Kestrel states the blocker on PR 430 and what it needs
           - group clarifies whether this is high priority or can wait
           - decision on who picks it up or whether it waits
      3. Confirm cost-map hardening path is clear   [Emil Brandvold must raise this]
           - Emil Brandvold describes the config validator and cost-processor validation approach
           - Nikolai Berresford or Dario Kestrel pushes back if there are concerns about coverage or provider-specific edge cases
           - agreement on scope of what needs testing before the next release
    
    On the agenda: What merged today and what's still in flight; Multimodal test and config validator status; Cost-map hardening and provider backend handoff
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Three workstreams confirmed moving in the right direction; PR 430 either unblocked or deferred with clear reasoning; next steps on cost-map validation clear to the team
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 224 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 713 function/class names and 60 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. What went in today: multimodal test fixture hardening, cost-processor validation, generation_params per-row support, telemetry dataclass updates
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm multimodal test hardening is stable   *** MUST RAISE ***
      2. Unblock or defer PR 430 (reasoning with OpenRouter examples)
      3. Confirm cost-map hardening path is clear   *** MUST RAISE ***
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Handover doc: Request-processing core and provider backends, dario to emil" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm multimodal test hardening is stable
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Eyes on the multimodal and cost changes; context on the request-processing handover from Dario Kestrel to Emil Brandvold
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm multimodal test hardening is stable
      2. Unblock or defer PR 430 (reasoning with OpenRouter examples)   *** MUST RAISE ***
      3. Confirm cost-map hardening path is clear
    goal        Unblock or defer PR 430 (reasoning with OpenRouter examples)
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Telemetry work just merged; understands what the dataclass changes unlock
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm multimodal test hardening is stable
      2. Unblock or defer PR 430 (reasoning with OpenRouter examples)
      3. Confirm cost-map hardening path is clear
    goal        Three PRs merged today across multimodal, cost accounting and telemetry; Emil Brandvold is driving four active workstreams, all mid-flight; need to sync on what's working and what still needs eyes
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Knowledge of the multimodal prompt changes and their integration points
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Confirm multimodal test hardening is stable
      2. Unblock or defer PR 430 (reasoning with OpenRouter examples)
      3. Confirm cost-map hardening path is clear
    goal        Three PRs merged today across multimodal, cost accounting and telemetry; Emil Brandvold is driving four active workstreams, all mid-flight; need to sync on what's working and what still needs eyes
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Three workstreams confirmed moving in the right direction; PR 430 either unblocked or deferred with clear reasoning; next steps on cost-map validation clear to the team


------------------------------------------------------------------------------
## #code-review — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs merged today; Dario Kestrel has PR 430 blocked for 3 days; stale PR queue needs attention; team needs to confirm merges are clean and plan next review cycles

    Today is Tuesday 4 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today; Dario Kestrel has PR 430 blocked for 3 days; stale PR queue needs attention; team needs to confirm merges are clean and plan next review cycles
    
    What it should get through:
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes   [Emil Brandvold must raise this]
           - Emil Brandvold summarizes what each PR does and any known edge cases
           - Konrad Feltrin or Dario Kestrel flags anything that needs immediate follow-up
           - agreement that the merges are safe or identification of what needs patching
      2. Unblock or defer PR 430   [Dario Kestrel must raise this]
           - Dario Kestrel states what PR 430 is waiting on and the cost of keeping it open
           - team clarifies whether this is blocking the next release
           - decision: unblock, defer, or reassign
      3. Plan next steps on stale PRs (PR 362, PR 411)   [Emil Brandvold must raise this]
           - brief check on whether PR 362 and PR 411 are still needed
           - if yes, who is going to unblock them or close them
           - confirmation of process so PRs don't age past the merge median
    
    On the agenda: Status of three merged PRs (PR 427, PR 438, PR 439); Blockers on PR 430 (OpenRouter examples); Stale PR queue: PR 362, PR 411
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three merges confirmed stable; PR 430 status clarified; stale PR plan set so queue stays healthy; it is settled that the id is only recorded at completion so no unconfirmed batch id ever lands on disk
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 224 changes merged to date

    On the table
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 713 function/class names and 60 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Three PRs merged today; knows the code paths affected and what they unblock
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes   *** MUST RAISE ***
      2. Unblock or defer PR 430
      3. Plan next steps on stale PRs (PR 362, PR 411)   *** MUST RAISE ***
      4. Agreed on doing the id write on completion. Half the providers hand you back a batch object that goes to failed or expired within a minute of submit, and if we've already got that id sitting on disk every rerun goes and polls a dead job. Completion is the only point where the id means something, so that's where it gets recorded.   *** MUST SETTLE (clue t3.r1.h2) ***
    goal        Confirm the three merged PRs are stable and don't need quick follow-up fixes
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Review of PR PR 427 multimodal work; context on what's blocking PR 430
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes
      2. Unblock or defer PR 430   *** MUST RAISE ***
      3. Plan next steps on stale PRs (PR 362, PR 411)
    goal        Unblock or defer PR 430
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Telemetry PR PR 439 just merged; owns the dataclass changes
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes
      2. Unblock or defer PR 430
      3. Plan next steps on stale PRs (PR 362, PR 411)
    goal        Three PRs merged today; Dario Kestrel has PR 430 blocked for 3 days; stale PR queue needs attention; team needs to confirm merges are clean and plan next review cycles
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Eyes on PR 427 and PR 438; founding maintainer perspective on architecture
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes
      2. Unblock or defer PR 430
      3. Plan next steps on stale PRs (PR 362, PR 411)
    goal        Three PRs merged today; Dario Kestrel has PR 430 blocked for 3 days; stale PR queue needs attention; team needs to confirm merges are clean and plan next review cycles
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Context on generation_params per-row changes and release integration
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Confirm the three merged PRs are stable and don't need quick follow-up fixes
      2. Unblock or defer PR 430
      3. Plan next steps on stale PRs (PR 362, PR 411)
    goal        Three PRs merged today; Dario Kestrel has PR 430 blocked for 3 days; stale PR queue needs attention; team needs to confirm merges are clean and plan next review cycles
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three merges confirmed stable; PR 430 status clarified; stale PR plan set so queue stays healthy; it is settled that the id is only recorded at completion so no unconfirmed batch id ever lands on disk


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Five changes to core request-processing services landed today; multimodal support is new surface; cost-map validation is new constraint; need to confirm no regressions and plan next hardening steps

    Today is Tuesday 4 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five changes to core request-processing services landed today; multimodal support is new surface; cost-map validation is new constraint; need to confirm no regressions and plan next hardening steps
    
    What it should get through:
      1. Confirm multimodal test coverage doesn't regress existing request-processing paths   [Emil Brandvold must raise this]
           - Emil Brandvold walks through the test changes and what they cover
           - Gideon Halloway flags any gaps in content vs url vs mixed payloads
           - Dario Kestrel checks whether this aligns with the request-processing design we landed in the handover
      2. Lock in the per-row generation_params pattern for cost accounting   [Emil Brandvold must raise this]
           - Emil Brandvold describes how generation_params flows through cost tracking and caching
           - Dario Kestrel questions whether this is the right abstraction for temperature/top_p variations per row
           - agreement or defer to next workstream
      3. Validate config validator covers non-standard provider backends   [Emil Brandvold must raise this]
           - Emil Brandvold states which provider backends the validator is tested against
           - Dermot Callaghan flags any custom backends (inference.net, kluster) that might not have test coverage
           - decision: add more test cases or document the validator's scope
    
    On the agenda: Multimodal test coverage and content/url fixture changes; Per-row generation_params integration and cost accounting; Config validator scope and backward compatibility
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Multimodal and cost-map changes confirmed backward-compatible; no breaking changes to existing provider integrations; next hardening priorities clear
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 224 changes merged to date

    On the table
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 713 function/class names and 60 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Five commits across request-processing core, multimodal support, cost validation; knows what test coverage changed and what the cost-processor config validator does
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm multimodal test coverage doesn't regress existing request-processing paths   *** MUST RAISE ***
      2. Lock in the per-row generation_params pattern for cost accounting   *** MUST RAISE ***
      3. Validate config validator covers non-standard provider backends   *** MUST RAISE ***
      4. what "Handover doc: Request-processing core and provider backends, dario to emil" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm multimodal test coverage doesn't regress existing request-processing paths
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Historical context on request-processing design; fresh eyes on whether the multimodal changes fit the architecture
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm multimodal test coverage doesn't regress existing request-processing paths
      2. Lock in the per-row generation_params pattern for cost accounting
      3. Validate config validator covers non-standard provider backends
    goal        Five changes to core request-processing services landed today; multimodal support is new surface; cost-map validation is new constraint; need to confirm no regressions and plan next hardening steps
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Visibility into viewer integration and how cost/progress display will reflect the new changes
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm multimodal test coverage doesn't regress existing request-processing paths
      2. Lock in the per-row generation_params pattern for cost accounting
      3. Validate config validator covers non-standard provider backends
    goal        Five changes to core request-processing services landed today; multimodal support is new surface; cost-map validation is new constraint; need to confirm no regressions and plan next hardening steps
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Stability perspective; knows which provider backends are most fragile
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm multimodal test coverage doesn't regress existing request-processing paths
      2. Lock in the per-row generation_params pattern for cost accounting
      3. Validate config validator covers non-standard provider backends
    goal        Five changes to core request-processing services landed today; multimodal support is new surface; cost-map validation is new constraint; need to confirm no regressions and plan next hardening steps
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Multimodal and cost-map changes confirmed backward-compatible; no breaking changes to existing provider integrations; next hardening priorities clear


==============================================================================
# 2025-02-05 — 4 conversation(s), 50 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 14 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five PRs opened in two days; two merged but three carrying design questions and blocking issues that need eyes before they land.

    Today is Wednesday 5 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five PRs opened in two days; two merged but three carrying design questions and blocking issues that need eyes before they land.
    
    What it should get through:
      1. PR 445 litellm multimodal passes review and is unblocked to merge   [Emil Brandvold must raise this]
           - Emil Brandvold raises the multimodal prompt type issues and cost calculation gaps uncovered in testing
           - Konrad Feltrin and Dermot Callaghan flag backend integration risks if file handling is incomplete
           - team signals whether remaining comments are blockers or post-merge polish
      2. PR 443 generation_params per-row approach is settled or deferred   [Priya Vandersloot must raise this]
           - Priya Vandersloot walks through the param-binding fix and empty dataset edge case
           - Emil Brandvold flags the kwargs issue and whether it breaks existing code
           - team decides: merge as-is, iterate post-merge, or defer pending broader param refactor
      3. PR 449 version bump lands and release train is unblocked   [Nikolai Berresford must raise this]
           - Nikolai Berresford confirms PR 449 has all fixes needed since post1
           - team confirms no other pending fixes need to ship in this bump
           - sign-off on merge
    
    On the agenda: PR 445 multimodal litellm: remaining edge cases and test coverage; PR 443 per-row generation_params: param binding and empty dataset handling; PR 449 version bump and kwargs fix: release readiness
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 445 and PR 449 unblocked to merge by midday; PR 443 either merged, deferred, or has a clear iteration path. Weekly notes updated with the week's fix cadence.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 226 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - Release notes: v0.1.17.post1 (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 445: Feat/multimodal/litellm (Emil Brandvold)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 686 function/class names and 55 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Deep context on multimodal implementation across all backends and test harness changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 445 litellm multimodal passes review and is unblocked to merge   *** MUST RAISE ***
      2. PR 443 generation_params per-row approach is settled or deferred
      3. PR 449 version bump lands and release train is unblocked
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 445 litellm multimodal passes review and is unblocked to merge
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Implementation of per-row generation_params, knows the param-binding problem space
    owns        multimodal-prompts, release-and-ci
    agenda
      1. PR 445 litellm multimodal passes review and is unblocked to merge
      2. PR 443 generation_params per-row approach is settled or deferred   *** MUST RAISE ***
      3. PR 449 version bump lands and release train is unblocked
    goal        PR 443 generation_params per-row approach is settled or deferred
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Fix for push_to_hub on private datasets; version bump expertise
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 445 litellm multimodal passes review and is unblocked to merge
      2. PR 443 generation_params per-row approach is settled or deferred
      3. PR 449 version bump lands and release train is unblocked   *** MUST RAISE ***
      4. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 449 version bump lands and release train is unblocked
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Holistic view of integration patterns and backward compat risk
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 445 litellm multimodal passes review and is unblocked to merge
      2. PR 443 generation_params per-row approach is settled or deferred
      3. PR 449 version bump lands and release train is unblocked
    goal        Five PRs opened in two days; two merged but three carrying design questions and blocking issues that need eyes before they land.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release coordination perspective and provider backend knowledge
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 445 litellm multimodal passes review and is unblocked to merge
      2. PR 443 generation_params per-row approach is settled or deferred
      3. PR 449 version bump lands and release train is unblocked
    goal        Five PRs opened in two days; two merged but three carrying design questions and blocking issues that need eyes before they land.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 445 and PR 449 unblocked to merge by midday; PR 443 either merged, deferred, or has a clear iteration path. Weekly notes updated with the week's fix cadence.


------------------------------------------------------------------------------
## #engineering — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three workstreams in mid-flight and kickoff; multimodal is shipping piecemeal and the team needs to sync on what's next and whether the velocity is sustainable.

    Today is Wednesday 5 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three workstreams in mid-flight and kickoff; multimodal is shipping piecemeal and the team needs to sync on what's next and whether the velocity is sustainable.
    
    What it should get through:
      1. Team confirms multimodal surface coverage and unblocks next phase   [Emil Brandvold must raise this]
           - Emil Brandvold walks through what litellm multimodal covers and what's still TODO for other backends
           - Dario Kestrel flags cost accounting and cache risks; what tests prove they're handled
           - team sizes the remaining work: is it next sprint or post-v0.1.18?
      2. Per-row generation_params design is validated or flagged for iteration   [Priya Vandersloot must raise this]
           - Priya Vandersloot explains the param binding approach and empty dataset fix
           - team flags whether the kwargs change breaks backward compat
           - decision: ship in next version bump or wait for broader param refactor
      3. Patch train strategy is confirmed or adjusted   [Emil Brandvold must raise this]
           - Emil Brandvold reports: since post1 we've landed 8 fixes, test suite is clean, no incident backlog
           - team assesses: is post4/post5 normal velocity or are we in emergency mode?
           - decision on release cadence and when to call v0.1.19
    
    On the agenda: Multimodal support across backends: what shipped, what's pending; Generation_params per row and cost estimation edge cases; Patch train cadence: is it sustainable or are we accumulating debt?
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team has shared understanding of multimodal surface coverage, cost accounting confidence, and patch velocity. Emil updates the week's notes; next sprint planning can proceed.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 226 changes merged to date

    On the table
      - notes-2025-02-03 (Emil Brandvold)
      - Weekly sync notes: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped (Emil Brandvold)
      - Postmortem: v0.1.17.post1 hotfix (Nikolai Berresford)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 445: Feat/multimodal/litellm (Emil Brandvold)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 686 function/class names and 55 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Status on three live workstreams; context on multimodal surface coverage and what tests are still missing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Team confirms multimodal surface coverage and unblocks next phase   *** MUST RAISE ***
      2. Per-row generation_params design is validated or flagged for iteration
      3. Patch train strategy is confirmed or adjusted   *** MUST RAISE ***
      4. that the doc "Weekly sync notes: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped" is done, and where the others can find it   *** MUST RAISE ***
      5. what "Weekly sync notes: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Postmortem: v0.1.17.post1 hotfix" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Team confirms multimodal surface coverage and unblocks next phase
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Per-row generation_params implementation and empty dataset edge case handling
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Team confirms multimodal surface coverage and unblocks next phase
      2. Per-row generation_params design is validated or flagged for iteration   *** MUST RAISE ***
      3. Patch train strategy is confirmed or adjusted
    goal        Per-row generation_params design is validated or flagged for iteration
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. push_to_hub fix for private datasets; version bump cadence
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Team confirms multimodal surface coverage and unblocks next phase
      2. Per-row generation_params design is validated or flagged for iteration
      3. Patch train strategy is confirmed or adjusted
    goal        Three workstreams in mid-flight and kickoff; multimodal is shipping piecemeal and the team needs to sync on what's next and whether the velocity is sustainable.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Provider integration perspective and examples/cookbooks surface readiness
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Team confirms multimodal surface coverage and unblocks next phase
      2. Per-row generation_params design is validated or flagged for iteration
      3. Patch train strategy is confirmed or adjusted
    goal        Three workstreams in mid-flight and kickoff; multimodal is shipping piecemeal and the team needs to sync on what's next and whether the velocity is sustainable.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing core view; knows the cost accounting and cache invalidation risks
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Team confirms multimodal surface coverage and unblocks next phase
      2. Per-row generation_params design is validated or flagged for iteration
      3. Patch train strategy is confirmed or adjusted
    goal        Three workstreams in mid-flight and kickoff; multimodal is shipping piecemeal and the team needs to sync on what's next and whether the velocity is sustainable.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team has shared understanding of multimodal surface coverage, cost accounting confidence, and patch velocity. Emil updates the week's notes; next sprint planning can proceed.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Multimodal cost calculation and fixture caching are live in PR 445; the team needs to validate that cost maps and cache invalidation are hardened before this ships to users.

    Today is Wednesday 5 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Multimodal cost calculation and fixture caching are live in PR 445; the team needs to validate that cost maps and cache invalidation are hardened before this ships to users.
    
    What it should get through:
      1. Cost map for multimodal is validated as accurate across providers   [Emil Brandvold must raise this]
           - Emil Brandvold reports: OpenAI cost estimator is in, tested against live pricing
           - Dario Kestrel flags: are we handling file size variance correctly, or is the estimate brittle?
           - team confirms: either tests prove accuracy or we defer multimodal cost to post-ship
      2. Cache invalidation is hardened against multimodal fixture changes   [Dario Kestrel must raise this]
           - Dario Kestrel walks through the fixture-based cache key and whether image file content changes invalidate
           - Emil Brandvold confirms: does the file type support change affect the key?
           - team decides: is the current cache semantics safe or do we need a schema version bump?
      3. Progress bar accurately reflects multimodal cost and token counts   [Gideon Halloway must raise this]
           - Gideon Halloway asks: is token counting aware of image tokens?
           - Emil Brandvold confirms: cost counter sums correctly across multimodal rows
           - signal: is this ready to ship or does it need hardening before release?
    
    On the agenda: Cost estimation for image modality across providers; Cache invalidation when multimodal fixtures change; Token counting and cost accuracy in progress bar
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team is confident that cost estimates are accurate and cache invalidation is safe. Any gaps are either fixed immediately or marked as post-ship hardening with an issue filed; it is settled that the team agrees the default must be a fixed literal tag in the source, changed only deliberately
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 226 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 445: Feat/multimodal/litellm (Emil Brandvold)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 686 function/class names and 55 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Cost estimation implementation for image modality in OpenAI backend; file type support and caching implications
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost map for multimodal is validated as accurate across providers   *** MUST RAISE ***
      2. Cache invalidation is hardened against multimodal fixture changes
      3. Progress bar accurately reflects multimodal cost and token counts
      4. The way out of this is that the default sitting in the source is a literal tag that only changes when one of us deliberately edits that line and puts up a PR. No floating alias, no resolving it at runtime, no env lookup. If the container people get changes, it should be because we changed it on purpose in a release.   *** MUST SETTLE (clue t4.r1.L10) ***
      5. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Cost map for multimodal is validated as accurate across providers
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Historical perspective on cost accounting bugs and caching footguns; knows the provider quirks
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost map for multimodal is validated as accurate across providers
      2. Cache invalidation is hardened against multimodal fixture changes
      3. Progress bar accurately reflects multimodal cost and token counts
    goal        Multimodal cost calculation and fixture caching are live in PR 445; the team needs to validate that cost maps and cache invalidation are hardened before this ships to users.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Core request-processing logic; knows the token counting and resume semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost map for multimodal is validated as accurate across providers
      2. Cache invalidation is hardened against multimodal fixture changes   *** MUST RAISE ***
      3. Progress bar accurately reflects multimodal cost and token counts
    goal        Cache invalidation is hardened against multimodal fixture changes
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress tracking and cost counter accuracy perspective
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Cost map for multimodal is validated as accurate across providers
      2. Cache invalidation is hardened against multimodal fixture changes
      3. Progress bar accurately reflects multimodal cost and token counts   *** MUST RAISE ***
    goal        Progress bar accurately reflects multimodal cost and token counts
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team is confident that cost estimates are accurate and cache invalidation is safe. Any gaps are either fixed immediately or marked as post-ship hardening with an issue filed; it is settled that the team agrees the default must be a fixed literal tag in the source, changed only deliberately


------------------------------------------------------------------------------
## #help — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: A user filed a report that a second pass with different sampling settings returned identical data

    Today is Wednesday 5 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: A user filed a report that a second pass with different sampling settings returned identical data
    
    What it should get through:
    
    On the agenda: Dermot Callaghan relays it: the user raised temperature from 0.7 to 1.0 for a diversity pass, got byte-identical rows back, and ended up deleting ~/.curator to get any new data at all; Dario Kestrel says he hit the same thing bumping max_tokens on a long-form run and assumed the provider was truncating, and lands on the obvious thing, that if you move the sampling knobs the run should just go and cost money again; open question neither answers: whether seed belongs in the same bucket as temperature and top_p
    
    Wrap when: Agreed it is a genuine bug rather than user error, no owner assigned, seed question left hanging; it is settled that Dario Kestrel had sampling-parameter changes ignored on resume, and notes the batch path never digests request bodies
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 226 changes merged to date

    On the table
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 445: Feat/multimodal/litellm (Emil Brandvold)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 686 function/class names and 55 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: max_tokens.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        A user filed a report that a second pass with different sampling settings returned identical data
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. and it is not just the prompt text. same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it happily resumed the earlier job, so my two arms of the ablation were the identical settings twice.   *** MUST SETTLE (clue t3.r2.l_pay_dario) ***
         must contain literally: max_tokens
    goal        Dario Kestrel had sampling-parameter changes ignored on resume, and notes the batch path never digests request bodies
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Agreed it is a genuine bug rather than user error, no owner assigned, seed question left hanging; it is settled that Dario Kestrel had sampling-parameter changes ignored on resume, and notes the batch path never digests request bodies; Dario Kestrel had sampling-parameter changes ignored on resume, and notes the batch path never digests request bodies


==============================================================================
# 2025-02-06 — 4 conversation(s), 41 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Release shipped today; 8 new PRs need triage and sign-off; 2 older PRs stuck

    Today is Thursday 6 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Release shipped today; 8 new PRs need triage and sign-off; 2 older PRs stuck
    
    What it should get through:
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day   [Emil Brandvold must raise this]
           - Gideon flags PR 457 as unblocked; Emil approves
           - Dario and Emil review PR 459 and PR 460 together
           - One of them gets LGTM within the hour
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring   [Dario Kestrel must raise this]
           - Dario surfaces that PR 430 is his reasoning examples work; not blocking v0.1.18
           - Emil or Dermot confirm PR 362 is low priority, can land anytime
    
    On the agenda: Hotfix incident and v0.1.18 release merged; what's left in the queue; Where PR 457, PR 459, PR 460 stand and what they need; Older stale PRs (PR 362, PR 430) — are they shipping or deferring
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 457, PR 459, PR 460 merged and shipping. PR 362 and PR 430 clearly marked as backlog or next-release.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 14 release(s) shipped, currently v0.1.18
      - 230 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)
      - PR 456: add `curator` tag to hf_card_template (Tomasz Wieland)
      - PR 457: fix: Rich error log overlap by progress bar fix (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 678 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Shipped 10 commits across multimodal image support and batch stability; knows what landed and what still needs review
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day   *** MUST RAISE ***
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring
      3. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 457, PR 459, PR 460 approved and merged by end of day
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just merged hotfix PR 461 and readme PR 462; understands what went wrong with prompt formatter
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring
    goal        Release shipped today; 8 new PRs need triage and sign-off; 2 older PRs stuck
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Owns the Rich CLI fix for error log overlap (PR 457); fresh perspective on display bugs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring
    goal        Release shipped today; 8 new PRs need triage and sign-off; 2 older PRs stuck
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Just opened PR 460 (logging cost retrieval in debug only); blocked on PR 430 but reviewing others
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring   *** MUST RAISE ***
    goal        Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Approved multimodal PRs; knows the code well
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Get PR 457, PR 459, PR 460 approved and merged by end of day
      2. Clarify next steps on stale PR 362 and PR 430 — shipping in a future release or deferring
    goal        Release shipped today; 8 new PRs need triage and sign-off; 2 older PRs stuck
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 457, PR 459, PR 460 merged and shipping. PR 362 and PR 430 clearly marked as backlog or next-release.


------------------------------------------------------------------------------
## #incidents — 9 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Revert recorded in incident log; hotfix PR 461 merged but then reverted; need to understand and close it

    Today is Thursday 6 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Revert recorded in incident log; hotfix PR 461 merged but then reverted; need to understand and close it
    
    What it should get through:
      1. Understand why the prompt formatter fix required a revert and what the actual root cause is   [Nikolai Berresford must raise this]
           - Nikolai walks through what broke after PR 461 landed
           - Emil checks logs or runs test to confirm the symptom
           - Either confirms it was the right fix being applied wrong, or a deeper issue
      2. Land a corrected version of the hotfix before end of day or defer to post4   [Emil Brandvold must raise this]
           - Nikolai and Emil agree on the fix
           - Dario signs off
           - Land it directly or defer
    
    On the agenda: What the revert was — which commits, what the symptom was; Why it was needed — reproduce the issue; Next attempt: what changes before we re-land
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Incident root cause clear. Either the fix lands again today (with tweaks), or it is deferred to the next patch with clear reasoning.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 14 release(s) shipped, currently v0.1.18
      - 230 changes merged to date

    On the table
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)
      - PR 456: add `curator` tag to hf_card_template (Tomasz Wieland)
      - PR 457: fix: Rich error log overlap by progress bar fix (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 678 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Merged hotfix PR 461 (fix prompt formatter) that triggered the revert; understands what broke and what the fix was
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Understand why the prompt formatter fix required a revert and what the actual root cause is   *** MUST RAISE ***
      2. Land a corrected version of the hotfix before end of day or defer to post4
      3. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand why the prompt formatter fix required a revert and what the actual root cause is
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Running four concurrent workstreams; can quickly triage whether the incident is multimodal-related or elsewhere
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand why the prompt formatter fix required a revert and what the actual root cause is
      2. Land a corrected version of the hotfix before end of day or defer to post4   *** MUST RAISE ***
    goal        Land a corrected version of the hotfix before end of day or defer to post4
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Approved the hotfix; senior context on request processing
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Understand why the prompt formatter fix required a revert and what the actual root cause is
      2. Land a corrected version of the hotfix before end of day or defer to post4
    goal        Revert recorded in incident log; hotfix PR 461 merged but then reverted; need to understand and close it
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Core pipeline context; can spot systemic issues
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Understand why the prompt formatter fix required a revert and what the actual root cause is
      2. Land a corrected version of the hotfix before end of day or defer to post4
    goal        Revert recorded in incident log; hotfix PR 461 merged but then reverted; need to understand and close it
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Incident root cause clear. Either the fix lands again today (with tweaks), or it is deferred to the next patch with clear reasoning.


------------------------------------------------------------------------------
## #releases — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.18 tagged and released; Emil must write release notes today; incident hotfix affects messaging

    Today is Thursday 6 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.18 tagged and released; Emil must write release notes today; incident hotfix affects messaging
    
    What it should get through:
      1. Draft and approve release notes for v0.1.18   [Emil Brandvold must raise this]
           - Emil outlines what shipped: multimodal, local urls, readme, hotfix
           - Dario and Nikolai spot check for accuracy
           - Konrad confirms readme content is reflected
      2. Communicate v0.1.18 ship and hotfix status to stakeholders   [Dario Kestrel must raise this]
           - Emil flags that the hotfix was reverted; needs explanation
           - Dario drafts the announcement email clarifying what shipped and what's next
           - Nikolai or Konrad offer any last thoughts
    
    On the agenda: What actually shipped in v0.1.18: multimodal, local urls, readme, hotfix; Release notes draft: complete and accurate; Known issues or gotchas: hotfix reverted, what's next
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Release notes completed and published. Announcement email sent with clarity on what shipped and what the next patch will address.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 14 release(s) shipped, currently v0.1.18
      - 230 changes merged to date

    On the table
      - Release notes: v0.1.18 (Emil Brandvold)
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - announce-v0-1-18 (Dario Kestrel)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)
      - PR 456: add `curator` tag to hf_card_template (Tomasz Wieland)
      - PR 457: fix: Rich error log overlap by progress bar fix (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 678 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Owns the release; knows what shipped and what had to be reverted; writing the release notes right now
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Draft and approve release notes for v0.1.18   *** MUST RAISE ***
      2. Communicate v0.1.18 ship and hotfix status to stakeholders
      3. that the doc "Release notes: v0.1.18" is done, and where the others can find it   *** MUST RAISE ***
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Draft and approve release notes for v0.1.18
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior engineer; can spot if anything important is missing from the release notes or if the changelog needs clarification
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Draft and approve release notes for v0.1.18
      2. Communicate v0.1.18 ship and hotfix status to stakeholders   *** MUST RAISE ***
      3. that "v0.1.18 is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Communicate v0.1.18 ship and hotfix status to stakeholders
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just shipped readme updates; can confirm what actually shipped in the release
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Draft and approve release notes for v0.1.18
      2. Communicate v0.1.18 ship and hotfix status to stakeholders
    goal        v0.1.18 tagged and released; Emil must write release notes today; incident hotfix affects messaging
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Owns the examples; knows if the readme changes are reflected in the release notes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Draft and approve release notes for v0.1.18
      2. Communicate v0.1.18 ship and hotfix status to stakeholders
    goal        v0.1.18 tagged and released; Emil must write release notes today; incident hotfix affects messaging
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Release notes completed and published. Announcement email sent with clarity on what shipped and what the next patch will address.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: The counting has to live somewhere and the online processor and the cache layer both half-own it today

    Today is Thursday 6 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The counting has to live somewhere and the online processor and the cache layer both half-own it today
    
    What it should get through:
    
    On the agenda: Gideon Halloway points out the progress bar total and the number of rows that actually come back disagree whenever a dataset contains the same prompt twice; the second copy never shows up on either side of the tally; Dario Kestrel argues the count belongs in the cache layer since that is the only place that knows what matched, Gideon Halloway wants it in the online processor where the request actually goes out; not settled; Emil Brandvold says he has no idea whether batch mode and the offline vLLM path would report the same two numbers and will go and check
    
    Wrap when: Layer question deferred; Emil Brandvold owes an answer on batch and offline parity; it is settled that the team agrees unhashable-schema rows should proceed to the backend and be reported as sends
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 14 release(s) shipped, currently v0.1.18
      - 230 changes merged to date

    On the table
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 449: bump pyproject.toml and fix litellm version (Nikolai Berresford)
      - PR 456: add `curator` tag to hf_card_template (Tomasz Wieland)
      - PR 457: fix: Rich error log overlap by progress bar fix (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 678 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Recipes that construct their schema on the fly are never going to be reusable and I am fine with that. What I am not fine with is being worse off than someone who never had a cache at all. Those rows should just go to the provider and show up in the sent column at the end.   *** MUST SETTLE (clue t1.r1.l_unhash_3) ***
    goal        the team agrees unhashable-schema rows should proceed to the backend and be reported as sends
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        The counting has to live somewhere and the online processor and the cache layer both half-own it today
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        The counting has to live somewhere and the online processor and the cache layer both half-own it today
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Layer question deferred; Emil Brandvold owes an answer on batch and offline parity; it is settled that the team agrees unhashable-schema rows should proceed to the backend and be reported as sends

