# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-01-10 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs landed today across coverage, caching, and backend config; stale PRs need triage

    Today is Friday 10 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs landed today across coverage, caching, and backend config; stale PRs need triage
    
    What it should get through:
      1. Confirm 80% coverage floor is appropriate scope   [Emil Brandvold must raise this]
           - Emil raises what PR 337 actually covers (core LLM, caching, request processing)
           - Dermot asks if viewer and viewer-specific path should count
           - lands on: core surfaces only, viewer has separate test path
      2. Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)   [Dermot Callaghan must raise this]
           - Dermot: PR 335 unlocks testing with cache off; PR 338 fixes regression from factory refactor
           - Emil: confirms integration tests pass with both changes
           - lands on: both merge same-day
    
    On the agenda: Four PRs merged today: test coverage, cache control, backend defaults, ruff fixes; Coverage floor discussion and what the 80% should cover; Stale PR triage — six PRs older than two weeks
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Coverage floor confirmed, all four PRs live in main, stale PR triage begun
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 163 changes merged to date

    On the table
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 171: enhance GenericRequest test coverage (Otto Brennan)
      - PR 173: Refactor Prompter to support class-based approach (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1073 function/class names and 119 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on integration test coverage changes and batch backend testing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm 80% coverage floor is appropriate scope   *** MUST RAISE ***
      2. Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)
      3. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm 80% coverage floor is appropriate scope
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. cache disabling feature and SimpleLLM default backend fix
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm 80% coverage floor is appropriate scope
      2. Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)   *** MUST RAISE ***
    goal        Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request processing context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm 80% coverage floor is appropriate scope
      2. Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)
    goal        Four PRs landed today across coverage, caching, and backend config; stale PRs need triage
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. platform-level perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm 80% coverage floor is appropriate scope
      2. Merge PR 335 (cache disable) and PR 338 (SimpleLLM backend default)
    goal        Four PRs landed today across coverage, caching, and backend config; stale PRs need triage
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Coverage floor confirmed, all four PRs live in main, stale PR triage begun


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Week landed multiple hardening changes; two releases planned; SimpleLLM refactor reached stability

    Today is Friday 10 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Week landed multiple hardening changes; two releases planned; SimpleLLM refactor reached stability
    
    What it should get through:
      1. Confirm SimpleLLM factory and backend-param split is stable   [Emil Brandvold must raise this]
           - Emil: PR#334 added backend overload tests; PR 337 adds 80% coverage
           - Dermot: notes PR 338 removes regression from earlier factory commit
           - lands on: stable, ready to ship
      2. Lock in release 0.1.15 blockers and target date   [Dermot Callaghan must raise this]
           - Dermot: lists ruff/black, coverage floor, SimpleLLM defaults as done
           - Emil: confirms integration tests exercise new backends
           - lands on: 0.1.15 release candidate Monday
    
    On the agenda: Week recap: 12 commits, 4 merged, coverage and ruff infrastructure in; SimpleLLM refactor stability — factory defaults and integration tests; Two releases target (0.1.15 next week) — blockers or go?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: SimpleLLM refactor confirmed stable; 0.1.15 release candidate locked for Monday; hardening week complete
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 163 changes merged to date

    On the table
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - Release notes: v0.1.14 (Emil Brandvold)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 171: enhance GenericRequest test coverage (Otto Brennan)
      - PR 173: Refactor Prompter to support class-based approach (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1073 function/class names and 119 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. week's fix summary — cache control, backend defaults, ruff/black alignment
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm SimpleLLM factory and backend-param split is stable
      2. Lock in release 0.1.15 blockers and target date   *** MUST RAISE ***
      3. what "Release notes: v0.1.14" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Lock in release 0.1.15 blockers and target date
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. SimpleLLM factory refactor progress and integration test overhaul
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm SimpleLLM factory and backend-param split is stable   *** MUST RAISE ***
      2. Lock in release 0.1.15 blockers and target date
      3. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm SimpleLLM factory and backend-param split is stable
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request processing steady state
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm SimpleLLM factory and backend-param split is stable
      2. Lock in release 0.1.15 blockers and target date
    goal        Week landed multiple hardening changes; two releases planned; SimpleLLM refactor reached stability
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. platform-level view
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm SimpleLLM factory and backend-param split is stable
      2. Lock in release 0.1.15 blockers and target date
    goal        Week landed multiple hardening changes; two releases planned; SimpleLLM refactor reached stability
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   SimpleLLM refactor confirmed stable; 0.1.15 release candidate locked for Monday; hardening week complete


------------------------------------------------------------------------------
## #incidents — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Revert triggered by SimpleLLM backend-default regression; fix in PR 338

    Today is Friday 10 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Revert triggered by SimpleLLM backend-default regression; fix in PR 338
    
    What it should get through:
      1. Confirm revert root cause addressed by PR 338   [Dermot Callaghan must raise this]
           - Dermot: factory refactor left backend=None off SimpleLLM
           - Emil: integration tests caught it in batch backend overload test
           - lands on: PR 338 fixes, revert can be undone after merge
    
    On the agenda: Revert commit 89a4146ac29c — what failed and when; Root cause: SimpleLLM default backend None expectation broken; Confirm PR 338 lands fix and unblocks next release
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Root cause confirmed fixed; no blockers to release; revert reverted once PR 338 lands
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 163 changes merged to date

    On the table
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 171: enhance GenericRequest test coverage (Otto Brennan)
      - PR 173: Refactor Prompter to support class-based approach (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1073 function/class names and 119 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. revert details and what caused it
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm revert root cause addressed by PR 338   *** MUST RAISE ***
      2. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm revert root cause addressed by PR 338
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. regression detection from integration tests
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm revert root cause addressed by PR 338
    goal        Revert triggered by SimpleLLM backend-default regression; fix in PR 338
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. impact assessment
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm revert root cause addressed by PR 338
    goal        Revert triggered by SimpleLLM backend-default regression; fix in PR 338
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Root cause confirmed fixed; no blockers to release; revert reverted once PR 338 lands


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Cache control and backend defaults merged; integration test coverage expanded to batch and resume paths

    Today is Friday 10 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Cache control and backend defaults merged; integration test coverage expanded to batch and resume paths
    
    What it should get through:
      1. Cache disable feature ready for users   [Dermot Callaghan must raise this]
           - Dermot: CURATOR_DISABLE_CACHE env var lands with PR 335
           - Emil: integration tests cover cache-off path in PR 337
           - lands on: feature ships with 0.1.15
      2. Backend factory and defaults stable for all provider paths   [Emil Brandvold must raise this]
           - Emil: batch backend overload tests in PR 334 confirm factory handling
           - Dermot: PR 338 sets SimpleLLM backend=None by default
           - lands on: all provider paths exercised in CI
    
    On the agenda: Cache disable feature (PR 335): testing without serialization; Backend selection and defaults (PR 338): SimpleLLM, factory, type-dict config; Integration test expansion: batch, resume, multi-backend overload (PR 334, PR 337)
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cache control live; backend factory stable across all provider integrations; batch and resume paths in CI
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 163 changes merged to date

    On the table
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 171: enhance GenericRequest test coverage (Otto Brennan)
      - PR 173: Refactor Prompter to support class-based approach (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1073 function/class names and 119 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. cache disable feature (PR 335), backend defaults fix (PR 338), integration test expansion
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cache disable feature ready for users   *** MUST RAISE ***
      2. Backend factory and defaults stable for all provider paths
    goal        Cache disable feature ready for users
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. batch backend testing and SimpleLLM factory overload tests
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cache disable feature ready for users
      2. Backend factory and defaults stable for all provider paths   *** MUST RAISE ***
    goal        Backend factory and defaults stable for all provider paths
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request processing steady state
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cache disable feature ready for users
      2. Backend factory and defaults stable for all provider paths
    goal        Cache control and backend defaults merged; integration test coverage expanded to batch and resume paths
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Cache control live; backend factory stable across all provider integrations; batch and resume paths in CI


==============================================================================
# 2025-01-13 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two major PRs opened today touch the core LLM interface; both need review before they can merge.

    Today is Monday 13 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two major PRs opened today touch the core LLM interface; both need review before they can merge.
    
    What it should get through:
      1. Approve or request changes on PR PR 360 LLM interface   [Dario Kestrel must raise this]
           - Dermot walks through the SimpleLLM removal and new factory method
           - Dario flags backward compatibility concerns with example scripts
           - Konrad asks about deprecation warnings for old callers
      2. send Weekly update: week of Jan 6 — v0.1.14 shipped   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Jan 6 — v0.1.14 shipped
    
    On the agenda: Review PR PR 360: Updated LLM class interface changes; Discuss fix_json check in PR PR 359 and config validation; Plan documentation updates for new interface; Weekly update: week of Jan 6 — v0.1.14 shipped
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR PR 360 receives approval or concrete change requests; PR PR 359 clarified for separate config-validation work; team agrees on deprecation messaging for SimpleLLM removal.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 175 changes merged to date

    On the table
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - weekly-2025-01-06 (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 359: Add fix_json check (Petar Kovalenko)

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
      - issue 122: Prompter as a Class to inherit and define prompt and parse funcs 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1000 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. owns the bulk-llm-inference and examples-cookbooks services; authored most of the LLM class interface changes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Approve or request changes on PR PR 360 LLM interface
      2. send Weekly update: week of Jan 6 — v0.1.14 shipped
    goal        Two major PRs opened today touch the core LLM interface; both need review before they can merge.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. perspective on backward compatibility and end-user impact; working on example cleanup
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve or request changes on PR PR 360 LLM interface   *** MUST RAISE ***
      2. send Weekly update: week of Jan 6 — v0.1.14 shipped
      3. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Approve or request changes on PR PR 360 LLM interface
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. maintainer perspective on API stability
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Approve or request changes on PR PR 360 LLM interface
      2. send Weekly update: week of Jan 6 — v0.1.14 shipped   *** MUST RAISE ***
      3. that "Weekly update: week of Jan 6 — v0.1.14 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Jan 6 — v0.1.14 shipped
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. drove the original SimpleLLM folding work; understands the config refactor
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve or request changes on PR PR 360 LLM interface
      2. send Weekly update: week of Jan 6 — v0.1.14 shipped
    goal        Two major PRs opened today touch the core LLM interface; both need review before they can merge.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR PR 360 receives approval or concrete change requests; PR PR 359 clarified for separate config-validation work; team agrees on deprecation messaging for SimpleLLM removal.


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Major refactoring of the core LLM class landed; many commits today fixing call sites across examples and local inference.

    Today is Monday 13 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Major refactoring of the core LLM class landed; many commits today fixing call sites across examples and local inference.
    
    What it should get through:
      1. Confirm all example scripts comply with new LLM interface   [Dermot Callaghan must raise this]
           - Dermot outlines the nine commits fixing examples
           - Emil notes the backend-params split affects vLLM offline
           - Dario asks if CONTRIBUTING.md needs update on new patterns
    
    On the agenda: Status on SimpleLLM removal and LLM interface refactor; Example script fixes landing today; Plan remaining cleanup work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees all critical example fixes are in flight; remaining cleanup work is identified.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 175 changes merged to date

    On the table
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 359: Add fix_json check (Petar Kovalenko)

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
      - issue 122: Prompter as a Class to inherit and define prompt and parse funcs 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1000 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 9 commits today fixing examples and the LLM interface; hands-on knowledge of what broke
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm all example scripts comply with new LLM interface   *** MUST RAISE ***
      2. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm all example scripts comply with new LLM interface
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. drove the SimpleLLM folding refactor; understands the backend-params split
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm all example scripts comply with new LLM interface
    goal        Major refactoring of the core LLM class landed; many commits today fixing call sites across examples and local inference.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. working on docs and example cleanup for the same interface changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm all example scripts comply with new LLM interface
    goal        Major refactoring of the core LLM class landed; many commits today fixing call sites across examples and local inference.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team agrees all critical example fixes are in flight; remaining cleanup work is identified.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 8 commits touch bulk-llm-inference and 6 touch local-offline-inference; interface refactoring has cascading effects on processors.

    Today is Monday 13 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 8 commits touch bulk-llm-inference and 6 touch local-offline-inference; interface refactoring has cascading effects on processors.
    
    What it should get through:
      1. Stabilize LLM interface for request processors   [Emil Brandvold must raise this]
           - Emil explains the typed-dict and backend-params changes
           - Dermot outlines the instance method fixes
           - Dario asks if caching layer needs changes
      2. Confirm vLLM offline processor fixes are sufficient   [Dermot Callaghan must raise this]
           - Dermot walks through the instance method fix in vLLM caller
           - Emil confirms backward compatibility
           - Dario notes caching implications
      3. write up Postmortem: release-and-ci revert on Jan 10   [Dario Kestrel must raise this]
           - Dario Kestrel says they will write Postmortem: release-and-ci revert on Jan 10 — Explains the file revert on Jan 10 and how it was caught.
    
    On the agenda: LLM class interface stability and rollout; Offline processor fixes for vLLM; Progress on caching and typed-dict updates; Postmortem: release-and-ci revert on Jan 10
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27), Ilse Vandekerckhove (no commit, review or comment 2025-01-11..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confirms LLM interface is ready for 0.1.15 work; offline processor fixes land without regression.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 175 changes merged to date

    On the table
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - Postmortem: release-and-ci revert on Jan 10 (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 359: Add fix_json check (Petar Kovalenko)

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
      - issue 122: Prompter as a Class to inherit and define prompt and parse funcs 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1000 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. author of the core refactoring; understands backward compatibility concerns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Stabilize LLM interface for request processors   *** MUST RAISE ***
      2. Confirm vLLM offline processor fixes are sufficient
      3. write up Postmortem: release-and-ci revert on Jan 10
      4. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Stabilize LLM interface for request processors
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 9 fixes to instance methods and offline processor
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Stabilize LLM interface for request processors
      2. Confirm vLLM offline processor fixes are sufficient   *** MUST RAISE ***
      3. write up Postmortem: release-and-ci revert on Jan 10
    goal        Confirm vLLM offline processor fixes are sufficient
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. owns caching and online-request-processing; needs to verify interface stability
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Stabilize LLM interface for request processors
      2. Confirm vLLM offline processor fixes are sufficient
      3. write up Postmortem: release-and-ci revert on Jan 10   *** MUST RAISE ***
      4. that the doc "Postmortem: release-and-ci revert on Jan 10" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Postmortem: release-and-ci revert on Jan 10
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team confirms LLM interface is ready for 0.1.15 work; offline processor fixes land without regression.


==============================================================================
# 2025-01-14 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: v0.1.15 shipped with LLM interface changes and perf work; need quick sign-off on remaining PRs before moving on

    Today is Tuesday 14 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.15 shipped with LLM interface changes and perf work; need quick sign-off on remaining PRs before moving on
    
    What it should get through:
      1. Confirm LLM interface refactor is backwards-compatible and ready   [Dermot Callaghan must raise this]
           - Dermot posts the interface changes and what broke
           - Konrad asks about caller expectations; Dario Kestrel flags the example updates
           - Emil confirms lazy imports don't break the signature
      2. Land config validation fixes without reverting   [Petar Kovalenko must raise this]
           - Petar explains the fix_json PR and config bug
           - Dermot asks if we need a follow-up test
           - Emil confirms the lazy-import change doesn't interact with it
      3. Signal that example updates are done and 0.1.15 is solid   [Dario Kestrel must raise this]
           - Dario summarizes the venv and example fixes that landed
           - Konrad approves the documentation
           - Dermot confirms no blockers for the release
    
    On the agenda: LLM interface refactor impact on 0.1.15; Fix_json and config validation safety; Example script fixes from interface change; Documentation and contributing guide updates
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: All PRs approved; team confident 0.1.15 is stable and examples are up to date.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 9 release(s) shipped, currently v0.1.15
      - 181 changes merged to date

    On the table
      - Postmortem: cache hashing regression revert on Jan 13 (Dermot Callaghan)
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release sequencing and LLM interface stability
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm LLM interface refactor is backwards-compatible and ready   *** MUST RAISE ***
      2. Land config validation fixes without reverting
      3. Signal that example updates are done and 0.1.15 is solid
      4. the page you are writing, Postmortem: cache hashing regression revert on Jan 13, has to say this in your own words: For anyone new to this area: there is exactly one function that decides whether a row is reused or sent, and every processor calls it, online, batch and the local vLLM one.   *** MUST SETTLE (clue t1.r1.l_scope_3) ***
         must contain literally: vLLM
      5. that the doc "Postmortem: cache hashing regression revert on Jan 13" is done, and where the others can find it   *** MUST RAISE ***
      6. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm LLM interface refactor is backwards-compatible and ready
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider integration and performance changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm LLM interface refactor is backwards-compatible and ready
      2. Land config validation fixes without reverting
      3. Signal that example updates are done and 0.1.15 is solid
    goal        v0.1.15 shipped with LLM interface changes and perf work; need quick sign-off on remaining PRs before moving on
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Design perspective on interface changes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm LLM interface refactor is backwards-compatible and ready
      2. Land config validation fixes without reverting
      3. Signal that example updates are done and 0.1.15 is solid
    goal        v0.1.15 shipped with LLM interface changes and perf work; need quick sign-off on remaining PRs before moving on
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. Config bug fixes and validation logic
    owns        (nothing specific)
    agenda
      1. Confirm LLM interface refactor is backwards-compatible and ready
      2. Land config validation fixes without reverting   *** MUST RAISE ***
      3. Signal that example updates are done and 0.1.15 is solid
    goal        Land config validation fixes without reverting
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Integration testing and example script fixes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm LLM interface refactor is backwards-compatible and ready
      2. Land config validation fixes without reverting
      3. Signal that example updates are done and 0.1.15 is solid   *** MUST RAISE ***
      4. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Signal that example updates are done and 0.1.15 is solid
    available   around today

### 4. How it should land

    lands as  partial
    leaving   All PRs approved; team confident 0.1.15 is stable and examples are up to date.


------------------------------------------------------------------------------
## #releases — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.15 already shipped; need to finalize release notes and announce

    Today is Tuesday 14 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.15 already shipped; need to finalize release notes and announce
    
    What it should get through:
      1. Release notes capture the real changes without overstating them   [Emil Brandvold must raise this]
           - Emil drafts what shipped: LLM interface refactor, lazy imports, fix_json, docs
           - Dermot asks if we mention the performance win
           - Konrad checks that examples credit is there
      2. Release announcement goes to the right people with the right timing   [Dermot Callaghan must raise this]
           - Dermot proposes the recipients and timing
           - Emil confirms
           - Dario notes any caveats about the contributing guide change
    
    On the agenda: What's in v0.1.15 and why; Release notes accuracy; Announcement timing and recipients
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Release notes finalized and announcement scheduled; v0.1.15 is officially out; it is settled that Dermot Callaghan got rows paired with the wrong answers because a resumed job's request set was smaller than the current one
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 9 release(s) shipped, currently v0.1.15
      - 181 changes merged to date

    On the table
      - Release notes: v0.1.15 (Emil Brandvold)
      - announce-v0-1-15 (Dermot Callaghan)
      - announce-v0-1-15 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering and publishing process
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Release notes capture the real changes without overstating them
      2. Release announcement goes to the right people with the right timing   *** MUST RAISE ***
      3. appending to the input dataset between restarts is a trap too. I added 200 rows to a 800 row set, restarted, resumed job came back with 800 results for 1000 requests and reassembly slotted them in by index. half the rows carried an answer to somebody else's question and it looked completely fine on inspection.   *** MUST SETTLE (clue t3.r2.l_pay_dermot) ***
      4. that "v0.1.15 is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Release announcement goes to the right people with the right timing
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. What shipped and the lazy-import perf win
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Release notes capture the real changes without overstating them   *** MUST RAISE ***
      2. Release announcement goes to the right people with the right timing
      3. that the doc "Release notes: v0.1.15" is done, and where the others can find it   *** MUST RAISE ***
      4. what "v0.1.15 is out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture the real changes without overstating them
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Documentation state for the release
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture the real changes without overstating them
      2. Release announcement goes to the right people with the right timing
    goal        v0.1.15 already shipped; need to finalize release notes and announce
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release impact on examples and cookbooks
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Release notes capture the real changes without overstating them
      2. Release announcement goes to the right people with the right timing
    goal        v0.1.15 already shipped; need to finalize release notes and announce
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. CI and release stability
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Release notes capture the real changes without overstating them
      2. Release announcement goes to the right people with the right timing
    goal        v0.1.15 already shipped; need to finalize release notes and announce
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Release notes finalized and announcement scheduled; v0.1.15 is officially out; it is settled that Dermot Callaghan got rows paired with the wrong answers because a resumed job's request set was smaller than the current one; Dermot Callaghan got rows paired with the wrong answers because a resumed job's request set was smaller than the current one


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: LLM interface refactored (ws-012); examples are now broken and need quick fixes (ws-016); both shipped today

    Today is Tuesday 14 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: LLM interface refactored (ws-012); examples are now broken and need quick fixes (ws-016); both shipped today
    
    What it should get through:
      1. Identify which examples are actually broken by the refactor   [Dario Kestrel must raise this]
           - Dario lists which example scripts call the old interface
           - Dermot explains what the new signature looks like
           - Konrad asks if there's a migration path or if we just fix them
      2. Examples are up to date and documented   [Dario Kestrel must raise this]
           - Dario confirms the venv instructions and example updates are in PR 364
           - Konrad approves the documentation
           - Dermot notes the citation bump
    
    On the agenda: Interface changes and what examples need to do; Example script fixes that landed today; Citation and documentation updates; Blocking issues for cookbooks vs. just cleanup
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples working again and team confident in ws-016 progress; it is settled that Nikolai Berresford fixes the docker backend on the latest tag with no override
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 9 release(s) shipped, currently v0.1.15
      - 181 changes merged to date

    On the table
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)
      - PR 248: More graceful handling, pt 2 (Dermot Callaghan)
      - PR 307: Unify token counting logic across processors (Millrow Refactor Bot)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. What example scripts need to fix after interface change
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Identify which examples are actually broken by the refactor   *** MUST RAISE ***
      2. Examples are up to date and documented   *** MUST RAISE ***
      3. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Identify which examples are actually broken by the refactor
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Details of the interface change and what callers need to do
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Identify which examples are actually broken by the refactor
      2. Examples are up to date and documented
    goal        LLM interface refactored (ws-012); examples are now broken and need quick fixes (ws-016); both shipped today
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Design perspective on how examples should illustrate the interface
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Identify which examples are actually broken by the refactor
      2. Examples are up to date and documented
    goal        LLM interface refactored (ws-012); examples are now broken and need quick fixes (ws-016); both shipped today
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. What the refactored backend params look like
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Identify which examples are actually broken by the refactor
      2. Examples are up to date and documented
    goal        LLM interface refactored (ws-012); examples are now broken and need quick fixes (ws-016); both shipped today
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Release context
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Identify which examples are actually broken by the refactor
      2. Examples are up to date and documented
      3. On the docker backend I'm just going with bespokelabs/sandbox:latest for the image. The sandbox image gets rebuilt whenever we patch the runtime deps, and if we hardcode a version string in the executor then every dep bump needs a curator release to reach anyone. latest means users pull the fixed image on their next docker run and we do nothing. No knob for it either, one image, one tag, less surface.   *** MUST SETTLE (clue t4.r1.h1) ***
    goal        Nikolai Berresford fixes the docker backend on the latest tag with no override
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Examples working again and team confident in ws-016 progress; it is settled that Nikolai Berresford fixes the docker backend on the latest tag with no override; Nikolai Berresford fixes the docker backend on the latest tag with no override


==============================================================================
# 2025-01-15 — 4 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.15.post1 shipped same-day as the fixes; team confirms it is live.

    Today is Wednesday 15 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.15.post1 shipped same-day as the fixes; team confirms it is live.
    
    What it should get through:
      1. Release notes capture what changed and why   [Dermot Callaghan must raise this]
           - Dermot summarizes the three commits
           - Dario confirms the README change is user-facing enough to call out
           - Emil nods on the cost fix
    
    On the agenda: Three quick fixes landed and tagged; Release notes written and ready
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.15.post1 release notes are live; team has recorded what the patch fixed.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - Release notes: v0.1.15.post1 (Dermot Callaghan)
      - Release notes: v0.1.15 (Emil Brandvold)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. The three fixes that went into v0.1.15.post1 and confidence they are minimal and safe
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Release notes capture what changed and why   *** MUST RAISE ***
      2. that the doc "Release notes: v0.1.15.post1" is done, and where the others can find it   *** MUST RAISE ***
      3. what "Release notes: v0.1.15" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture what changed and why
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on whether the README fix is sufficient for users
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture what changed and why
    goal        v0.1.15.post1 shipped same-day as the fixes; team confirms it is live.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Sign-off that cost calculation is now correct
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Release notes capture what changed and why
    goal        v0.1.15.post1 shipped same-day as the fixes; team confirms it is live.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.15.post1 release notes are live; team has recorded what the patch fixed.


------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened and merged same day; team is reviewing the quick fixes before release.

    Today is Wednesday 15 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened and merged same day; team is reviewing the quick fixes before release.
    
    What it should get through:
      1. Cost division by minutes instead of requests is correct   [Dermot Callaghan must raise this]
           - Dermot explains the regression: was dividing by request count, not elapsed time
           - Konrad confirms the fix is minimal and correct
           - Emil signs off that it makes sense
      2. README example matches the current LLM interface   [Dario Kestrel must raise this]
           - Dario flags that the example was broken by the recent LLM class refactor
           - Emil approves the fix
           - Dermot confirms it now runs
      3. Typo in first docs example is caught and fixed   [Dermot Callaghan must raise this]
           - Dermot posts the fix
           - Emil approves it
    
    On the agenda: Cost calculation fix for rate-per-minute; README example corrected; Docs typo in first example
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three PRs are reviewed, approved, and merged; the team knows what went wrong and what was fixed; it is settled that Konrad Feltrin rejects a caller-supplied docker image tag in backend_params
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - announce-v0-1-15-post1 (Dermot Callaghan)
      - Weekly sync notes: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped (Dario Kestrel)
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Two bugfixes and the rationale for each; cost-per-minute calculation and typo in docs
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost division by minutes instead of requests is correct   *** MUST RAISE ***
      2. README example matches the current LLM interface
      3. Typo in first docs example is caught and fixed   *** MUST RAISE ***
      4. that "v0.1.15.post1 hotfix is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Cost division by minutes instead of requests is correct
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. The README update and context on what broke in the examples
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost division by minutes instead of requests is correct
      2. README example matches the current LLM interface   *** MUST RAISE ***
      3. Typo in first docs example is caught and fixed
      4. that the doc "Weekly sync notes: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped" is done, and where the others can find it   *** MUST RAISE ***
      5. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        README example matches the current LLM interface
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Approval on the docs fix
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost division by minutes instead of requests is correct
      2. README example matches the current LLM interface
      3. Typo in first docs example is caught and fixed
    goal        Three PRs opened and merged same day; team is reviewing the quick fixes before release.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Approval on the cost calculation fix
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Cost division by minutes instead of requests is correct
      2. README example matches the current LLM interface
      3. Typo in first docs example is caught and fixed
      4. Re: adding an image override to backend_params for CodeExecutor. I'd rather not. The docker backend only works against our sandbox image anyway, the entrypoint and the mounted paths are ours, so pointing it at some arbitrary tag mostly gets you a confusing failure. Keep backend_params to concurrency and timeout and let the tag be whatever we ship as current.   *** MUST SETTLE (clue t4.r1.h2) ***
    goal        Konrad Feltrin rejects a caller-supplied docker image tag in backend_params
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three PRs are reviewed, approved, and merged; the team knows what went wrong and what was fixed; it is settled that Konrad Feltrin rejects a caller-supplied docker image tag in backend_params; Konrad Feltrin rejects a caller-supplied docker image tag in backend_params


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: String of small fixes and version bump landed same-day; team syncs on what broke and what changed.

    Today is Wednesday 15 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: String of small fixes and version bump landed same-day; team syncs on what broke and what changed.
    
    What it should get through:
      1. Cost calculation regression is fixed and users are not overcharged   [Dermot Callaghan must raise this]
           - Dermot explains the cost division bug
           - Emil confirms it was caught by the online request processing tests
           - Team nods that the fix is safe to ship same-day
      2. README and example scripts are unbroken after LLM class refactor   [Dario Kestrel must raise this]
           - Dario reports that the example scripts broke when the LLM class changed
           - Dermot confirms the fix is simple: use instance method instead of class method
           - Nikolai notes this is part of the examples cleanup work
    
    On the agenda: Four commits landed: cost fix, typo, version bump, docs; Examples work moving forward despite the LLM class break
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team is aware of the hotfix bundle and the examples work is moving forward; no one is surprised by the fixes.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Four commits: cost calculation fix, typo fix, version bump, docs example fix
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost calculation regression is fixed and users are not overcharged   *** MUST RAISE ***
      2. README and example scripts are unbroken after LLM class refactor
    goal        Cost calculation regression is fixed and users are not overcharged
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on the examples work and what examples broke with the LLM class refactor
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost calculation regression is fixed and users are not overcharged
      2. README and example scripts are unbroken after LLM class refactor   *** MUST RAISE ***
      3. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        README and example scripts are unbroken after LLM class refactor
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Observation that cost estimation needs better guards
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost calculation regression is fixed and users are not overcharged
      2. README and example scripts are unbroken after LLM class refactor
    goal        String of small fixes and version bump landed same-day; team syncs on what broke and what changed.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Release-and-ci perspective on the version bump
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Cost calculation regression is fixed and users are not overcharged
      2. README and example scripts are unbroken after LLM class refactor
    goal        String of small fixes and version bump landed same-day; team syncs on what broke and what changed.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team is aware of the hotfix bundle and the examples work is moving forward; no one is surprised by the fixes.


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Cost calculation regression was caught and fixed same-day; batch job throughput work is ongoing.

    Today is Wednesday 15 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Cost calculation regression was caught and fixed same-day; batch job throughput work is ongoing.
    
    What it should get through:
      1. Cost per minute is now calculated correctly and doesn't regress again   [Dermot Callaghan must raise this]
           - Dermot explains: was dividing by request count instead of elapsed time
           - Emil reports the test suite caught it when running batch jobs
           - Dario suggests adding a guard for models with no listed price
    
    On the agenda: Cost division by minutes is now correct; Progress bar tracking for batch jobs
    
    Meeting today: Weekly sync
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost calculation fix is confirmed safe; team understands the regression and how it was caught.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 996 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. The cost division regression and the fix
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost per minute is now calculated correctly and doesn't regress again   *** MUST RAISE ***
    goal        Cost per minute is now calculated correctly and doesn't regress again
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Testing and validation of the cost calculation on real batch jobs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost per minute is now calculated correctly and doesn't regress again
    goal        Cost calculation regression was caught and fixed same-day; batch job throughput work is ongoing.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. History of how cost estimation has broken before
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost per minute is now calculated correctly and doesn't regress again
    goal        Cost calculation regression was caught and fixed same-day; batch job throughput work is ongoing.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Cost calculation fix is confirmed safe; team understands the regression and how it was caught.


==============================================================================
# 2025-01-16 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: New PR needs eyes before merge; blocking SimpleLLM refactor work.

    Today is Thursday 16 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: New PR needs eyes before merge; blocking SimpleLLM refactor work.
    
    What it should get through:
      1. Approve messages input refactor approach   [Dermot Callaghan must raise this]
           - Dario Kestrel outlines the helper-function split and why it matters for SimpleLLM
           - Dermot Callaghan checks test coverage and queries the dataset conversion test
           - Dario Kestrel addresses concerns or they agree it's ready
    
    On the agenda: Review PR PR 371: messages list input handling; Verify test coverage for dataset conversion; Check for SimpleLLM caller compatibility
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR PR 371 approved or with clear actionable feedback for revision.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 371: Allow lists of messages as simple input (Dario Kestrel)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 994 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. the shape of the messages input changes and what SimpleLLM callers expect
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve messages input refactor approach
    goal        New PR needs eyes before merge; blocking SimpleLLM refactor work.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. perspective on multimodal prompt handling and the test coverage needed
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Approve messages input refactor approach   *** MUST RAISE ***
    goal        Approve messages input refactor approach
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR PR 371 approved or with clear actionable feedback for revision.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Mid-flight refactor with multiple commits landing; config defaults and SimpleLLM compatibility at risk.

    Today is Thursday 16 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Mid-flight refactor with multiple commits landing; config defaults and SimpleLLM compatibility at risk.
    
    What it should get through:
      1. Map backend=None default impact across SimpleLLM callers   [Emil Brandvold must raise this]
           - Emil Brandvold outlines what the factory split changed
           - Dario Kestrel notes which callers are affected
           - Dermot Callaghan raises the postmortem-2025-01-13 cache-hashing pattern and whether this repeats
      2. Clarify messages input contract for downstream code   [Dario Kestrel must raise this]
           - Dario Kestrel walks through the test case changes
           - Emil Brandvold asks what the contract is now
           - Dermot Callaghan flags any schema-validation issues
    
    On the agenda: Assess config-bug surface from backend-params split; Plan rollout of messages input changes; Identify what SimpleLLM callers need to change
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clear plan for what SimpleLLM callers must adjust; config defaults documented or fixed before wider rollout.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 184 changes merged to date

    On the table
      - Postmortem: cache hashing regression revert on Jan 13 (Dermot Callaghan)
      - Postmortem: release-and-ci revert on Jan 10 (Dario Kestrel)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 371: Allow lists of messages as simple input (Dario Kestrel)

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

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 994 function/class names and 104 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. overall refactor direction and what the factory/typed-dict changes unblock
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Map backend=None default impact across SimpleLLM callers   *** MUST RAISE ***
      2. Clarify messages input contract for downstream code
      3. that the doc "Postmortem: v0.1.15.post1 hotfix" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Postmortem: cache hashing regression revert on Jan 13" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Postmortem: release-and-ci revert on Jan 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Map backend=None default impact across SimpleLLM callers
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. the messages-input refactor and where it sits relative to other changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Map backend=None default impact across SimpleLLM callers
      2. Clarify messages input contract for downstream code   *** MUST RAISE ***
    goal        Clarify messages input contract for downstream code
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. postmortem context from recent reverts and what config defaults need care
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Map backend=None default impact across SimpleLLM callers
      2. Clarify messages input contract for downstream code
    goal        Mid-flight refactor with multiple commits landing; config defaults and SimpleLLM compatibility at risk.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear plan for what SimpleLLM callers must adjust; config defaults documented or fixed before wider rollout.

