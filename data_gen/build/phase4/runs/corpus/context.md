# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-02-21 — 5 conversation(s), 49 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: One day-old PR on a performance perf issue tied to batch mode; needs senior eyes before merge window closes

    Today is Friday 21 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One day-old PR on a performance perf issue tied to batch mode; needs senior eyes before merge window closes
    
    What it should get through:
      1. Approve async batch response refactor or flag blocking concerns   [Dario Kestrel must raise this]
           - Emil: context on why async matters here (cost, UX), Dario Kestrel questions retry semantics, Emil Brandvold clarifies those are preserved
           - Gideon: asks about progress bar during file write, Emil Brandvold confirms it still fires
           - Dario approves or flags one blocker for later
    
    On the agenda: PR PR 532: async batch response file method; Impact on retry/resume paths; Progress bar during I/O
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR approved with any minor comments addressed, or one clear blocking item identified for next session
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Performance issue identified and PR structure ready; context on batch-mode internals
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve async batch response refactor or flag blocking concerns
    goal        One day-old PR on a performance perf issue tied to batch mode; needs senior eyes before merge window closes
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing semantics; knows how batch response ties to resume
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve async batch response refactor or flag blocking concerns   *** MUST RAISE ***
    goal        Approve async batch response refactor or flag blocking concerns
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress tracking and observability angle
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Approve async batch response refactor or flag blocking concerns
    goal        One day-old PR on a performance perf issue tied to batch mode; needs senior eyes before merge window closes
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR approved with any minor comments addressed, or one clear blocking item identified for next session


------------------------------------------------------------------------------
## #engineering — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Friday wrap; four merged PRs, one fresh PR, executor and telemetry work landing, one blocker stale for two weeks

    Today is Friday 21 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Friday wrap; four merged PRs, one fresh PR, executor and telemetry work landing, one blocker stale for two weeks
    
    What it should get through:
      1. Confirm executor cleanup scope and docker example fix timeline   [Nikolai Berresford must raise this]
           - Nikolai: docker backend doesn't match examples, need to ship fix before people copy-paste it
           - Konrad: saw the cleanup list, some things can simplify — raises priority
           - Nikolai: clarifies what lands today vs deferred
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly   [Dario Kestrel must raise this]
           - Emil: 468 has been open 14 days, needs to land or get bumped
           - Dario: states whether he can unblock today or points to next window
           - Team: notes decision
    
    On the agenda: Merged this week: executor, telemetry config, logger, push-to-viewer; Executor docker example fix and cleanup scope; PR PR 468 blocker status and next steps
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Executor scope locked for end of day; PR 468 either unblocked or deferred to next week with clear reason
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Four PRs merged this week; telemetry fix live; push-to-viewer feature landing; batch async perf issue flagged
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm executor cleanup scope and docker example fix timeline
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly
    goal        Friday wrap; four merged PRs, one fresh PR, executor and telemetry work landing, one blocker stale for two weeks
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Executor PRs landed; cleanup work underway; docker example mismatch flagged
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm executor cleanup scope and docker example fix timeline   *** MUST RAISE ***
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly
    goal        Confirm executor cleanup scope and docker example fix timeline
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Executor review in progress; simplification opportunities spotted
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm executor cleanup scope and docker example fix timeline
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly
    goal        Friday wrap; four merged PRs, one fresh PR, executor and telemetry work landing, one blocker stale for two weeks
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Unblocking perspective on 468 and what lands next
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm executor cleanup scope and docker example fix timeline
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly   *** MUST RAISE ***
    goal        Acknowledge PR PR 468 blocker and unblock or defer explicitly
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress bar frequency update merged
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm executor cleanup scope and docker example fix timeline
      2. Acknowledge PR PR 468 blocker and unblock or defer explicitly
    goal        Friday wrap; four merged PRs, one fresh PR, executor and telemetry work landing, one blocker stale for two weeks
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Executor scope locked for end of day; PR 468 either unblocked or deferred to next week with clear reason


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Six commits to online-request-processing and bulk-llm-inference landed this week; async batch refactor opens Friday; progress bar integration live

    Today is Friday 21 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six commits to online-request-processing and bulk-llm-inference landed this week; async batch refactor opens Friday; progress bar integration live
    
    What it should get through:
      1. Confirm push-to-viewer and progress bar wiring safe for release   [Emil Brandvold must raise this]
           - Emil: viewer link was wrong, fixed in last two commits, PRs 518 and 520 landed
           - Gideon: progress bar fires during upload now, no blocking issues
           - Dario: nods, no cache/resume concerns
      2. Surface any resume/caching risk from async batch file method before merge   [Dario Kestrel must raise this]
           - Emil: raising async batch file refactor as a perf win, want Dario Kestrel's eyes
           - Dario: asks if file writes block resume checkpoints, Emil Brandvold confirms they don't
           - Emil or Dario: flags if anything needs serialization order guarantees
    
    On the agenda: Push-to-viewer landing: link constant, progress bar on upload; Async batch file method: impact on resume and caching; Progress tracking during I/O operations
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Viewer and progress bar rollout confirmed safe; async batch refactor either approved or one concern flagged for implementation review; it is settled that the team agrees batch-mode reuse behaviour is currently unverified and has regressed before
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: e2e.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Push-to-viewer PRs landed; async batch file refactor ready; viewer link constant fixed; progress bar wiring live
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm push-to-viewer and progress bar wiring safe for release   *** MUST RAISE ***
      2. Surface any resume/caching risk from async batch file method before merge
    goal        Confirm push-to-viewer and progress bar wiring safe for release
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress bar frequency tuning merged; observability working end-to-end
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm push-to-viewer and progress bar wiring safe for release
      2. Surface any resume/caching risk from async batch file method before merge
      3. We only ever assert on reuse counts in the online tests. The batch e2e checks the reassembled output and nothing else, which is exactly how the last regression rode out to a release. It bit me on the Azure batch run too.   *** MUST SETTLE (clue t1.r1.l_scope_2) ***
         must contain literally: e2e
    goal        the team agrees batch-mode reuse behaviour is currently unverified and has regressed before
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing internals knowledge; resume and caching guardrails
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm push-to-viewer and progress bar wiring safe for release
      2. Surface any resume/caching risk from async batch file method before merge   *** MUST RAISE ***
    goal        Surface any resume/caching risk from async batch file method before merge
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Viewer and progress bar rollout confirmed safe; async batch refactor either approved or one concern flagged for implementation review; it is settled that the team agrees batch-mode reuse behaviour is currently unverified and has regressed before


------------------------------------------------------------------------------
## #viewer — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Four commits to curator-viewer this week; two PRs merged for push-to-viewer and logger; ready to confirm landing

    Today is Friday 21 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four commits to curator-viewer this week; two PRs merged for push-to-viewer and logger; ready to confirm landing
    
    What it should get through:
      1. Confirm push-to-viewer and progress bar shipped correctly   [Emil Brandvold must raise this]
           - Emil: both merged, link constant was last fix needed, progress bar fires during upload
           - Dario: checks for any regression in viewer client or download
           - Konrad: no issues for recipe examples noted
    
    On the agenda: PRs PR 518 and PR 520 landed: push-to-viewer + progress bar; Viewer client link constant and update scope; Integration with curator-viewer surface for next release
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Feature confirmed shipped; no regressions reported; ready for next release cycle
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Push-to-viewer PRs merged and live; link constant fixed; progress bar on upload wired; logger integration complete
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm push-to-viewer and progress bar shipped correctly   *** MUST RAISE ***
    goal        Confirm push-to-viewer and progress bar shipped correctly
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Viewer surface ownership; feedback on link/progress integration
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm push-to-viewer and progress bar shipped correctly
    goal        Four commits to curator-viewer this week; two PRs merged for push-to-viewer and logger; ready to confirm landing
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Feature confirmed shipped; no regressions reported; ready for next release cycle


------------------------------------------------------------------------------
## #help — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: A test helper touching the stats path broke the release-and-ci suite

    Today is Friday 21 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: A test helper touching the stats path broke the release-and-ci suite
    
    What it should get through:
    
    On the agenda: Dermot Callaghan: the helper called into the stats path with CURATOR_DISABLE_CACHE set in the environment and got None back, which turned into an AttributeError two frames later; he has wrapped it in a try and hates it; Emil Brandvold says he also wants plain zeros rather than an exception when no run has happened yet in the process; neither can decide whether cache-off and no-run-yet should look different to the caller
    
    Wrap when: Workaround stays in the test helper; the two edge cases go on the PR as comments; it is settled that the team agrees ordinary sqlite opens fail against the shared cache mount even for pure counting
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. the shared example cache on the box is mounted so only the nightly job can write to it, everybody else gets it as a read-only mount. Any script that opens the metadata sqlite the normal way dies with "attempt to write a readonly database" before it has read a single row, because sqlite wants to put a journal next to the file. Bit me twice trying to count entries.   *** MUST SETTLE (clue t1.r2.L5) ***
    goal        the team agrees ordinary sqlite opens fail against the shared cache mount even for pure counting
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        A test helper touching the stats path broke the release-and-ci suite
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Workaround stays in the test helper; the two edge cases go on the PR as comments; it is settled that the team agrees ordinary sqlite opens fail against the shared cache mount even for pure counting


==============================================================================
# 2025-02-24 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today need review; two older PRs still waiting

    Today is Monday 24 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today need review; two older PRs still waiting
    
    What it should get through:
      1. Get eyes on PR 533 (viewer resume integration)   [Emil Brandvold must raise this]
           - Emil raises the integration points
           - Konrad checks for persistence concerns
           - Land or identify blocking questions
      2. Get eyes on PR 536 (Claude 3.7 reasoning)   [Dario Kestrel must raise this]
           - Dario notes the three related issues (token rate limits, thinking tokens, LiteLLM gaps)
           - Nikolai flags what needs to ship before merge
           - Determine if this lands or needs a follow-up
    
    On the agenda: PR 533: resume and hosted curator viewer integration; PR 536: Claude 3.7 reasoning model support; Quick pass on stale PRs 468 and 532
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both PRs get initial review; 468 and 532 may stay open pending other work landing first
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. understanding of resume/viewer integration work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get eyes on PR 533 (viewer resume integration)   *** MUST RAISE ***
      2. Get eyes on PR 536 (Claude 3.7 reasoning)
      3. that "Weekly update: week of Feb 17 — 0.1.19 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Get eyes on PR 533 (viewer resume integration)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Claude 3.7 reasoning implementation
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get eyes on PR 533 (viewer resume integration)
      2. Get eyes on PR 536 (Claude 3.7 reasoning)   *** MUST RAISE ***
    goal        Get eyes on PR 536 (Claude 3.7 reasoning)
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Both PRs get initial review; 468 and 532 may stay open pending other work landing first


------------------------------------------------------------------------------
## #engineering — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario Kestrel lost most of an afternoon to a persona-hub rerun that got a 400 back on every row after the dataset was already loaded and the run was already registered

    Today is Monday 24 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel lost most of an afternoon to a persona-hub rerun that got a 400 back on every row after the dataset was already loaded and the run was already registered
    
    What it should get through:
    
    On the agenda: Dario Kestrel pastes the provider 400 body and points out the field it objected to has been in that Pydantic model since the file was written, so nothing about the run made it late-breaking; Gideon Halloway asks what actually happens between LLM() being constructed and the first HTTP request, because as far as he can tell nothing looks at response_format at all until a provider looks at it; Dermot Callaghan says the shape of the fix he wants is that it stops before anything goes out, not a nicer error after the fact, but he does not want to guess the rules from one 400
    
    Wrap when: agreement that some pre-dispatch check on response_format is worth building; nobody has claimed it, and what counts as incompatible is left as a list to be gathered; it is settled that the team agrees editing a response model currently yields stored objects shaped like the old schema
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: confidence.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel lost most of an afternoon to a persona-hub rerun that got a 400 back on every row after the dataset was already loaded and the run was already registered
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel lost most of an afternoon to a persona-hub rerun that got a 400 back on every row after the dataset was already loaded and the run was already registered
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel lost most of an afternoon to a persona-hub rerun that got a 400 back on every row after the dataset was already loaded and the run was already registered
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Added a confidence field to the response model on the ungrounded QA example, reran, and got back last week's objects with no confidence on them. Then the downstream validator threw on every row and I spent an hour looking at the validator.   *** MUST SETTLE (clue t1.r1.l_schema_1) ***
         must contain literally: confidence
    goal        the team agrees editing a response model currently yields stored objects shaped like the old schema
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   agreement that some pre-dispatch check on response_format is worth building; nobody has claimed it, and what counts as incompatible is left as a list to be gathered; it is settled that the team agrees editing a response model currently yields stored objects shaped like the old schema


==============================================================================
# 2025-02-25 — 4 conversation(s), 50 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five commits landed today touching core request processing, caching, and viewer integration; two PRs (533, 536) are under active review and older PRs (468, 532) need movement.

    Today is Tuesday 25 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits landed today touching core request processing, caching, and viewer integration; two PRs (533, 536) are under active review and older PRs (468, 532) need movement.
    
    What it should get through:
      1. Confirm PR 533 (resume/hosted curator viewer) is ready to land or needs rework   [Emil Brandvold must raise this]
           - Emil outlines the four commits adding session ID tracking across the run lifecycle
           - Dario flags whether the tag fix in 539 creates any conflicts with the metadata surface
           - Decision: either merge 533 or identify what's blocking it
      2. Resolve curator tag fix without breaking the viewer integration   [Dario Kestrel must raise this]
           - Dario explains what broke in the tag and why commit 924692c fixes it
           - Emil confirms session ID work doesn't touch the same code paths
           - Either 539 lands now or gets deferred after 533
      3. Validate that metadatadb schema changes don't create downstream friction   [Emil Brandvold must raise this]
           - Emil walks through the schema validation logic in commit 557bbcff
           - Dermot offers feedback on whether this approach matches the rest of the validation pattern
           - Consensus on whether this is ready or needs another pass
    
    On the agenda: Session ID threading through request processor and resume flow; Curator tag fix and LLM interface consistency; Metadata schema validation in metadatadb
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 533 either lands or gets a clear list of blockers; PR 539 lands or defers cleanly; the team agrees the metadata schema changes are sound.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Four commits on session ID and metadata handling across request processing and caching
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 533 (resume/hosted curator viewer) is ready to land or needs rework   *** MUST RAISE ***
      2. Resolve curator tag fix without breaking the viewer integration
      3. Validate that metadatadb schema changes don't create downstream friction   *** MUST RAISE ***
      4. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 533 (resume/hosted curator viewer) is ready to land or needs rework
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. The curator tag fix (commit 924692c) that touches the same LLM interface surface
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 533 (resume/hosted curator viewer) is ready to land or needs rework
      2. Resolve curator tag fix without breaking the viewer integration   *** MUST RAISE ***
      3. Validate that metadatadb schema changes don't create downstream friction
    goal        Resolve curator tag fix without breaking the viewer integration
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Fresh perspective on whether the schema validation approach in metadatadb is sound
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm PR 533 (resume/hosted curator viewer) is ready to land or needs rework
      2. Resolve curator tag fix without breaking the viewer integration
      3. Validate that metadatadb schema changes don't create downstream friction
    goal        Five commits landed today touching core request processing, caching, and viewer integration; two PRs (533, 536) are under active review and older PRs (468, 532) need movement.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 533 either lands or gets a clear list of blockers; PR 539 lands or defers cleanly; the team agrees the metadata schema changes are sound.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Five commits landed today; four workstreams are mid-flight; two PRs older than the merge median (468, 532) need attention; one day-old PR (533) needs momentum.

    Today is Tuesday 25 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits landed today; four workstreams are mid-flight; two PRs older than the merge median (468, 532) need attention; one day-old PR (533) needs momentum.
    
    What it should get through:
      1. Confirm Emil's session ID and request processor work is unblocking the resume flow   [Emil Brandvold must raise this]
           - Emil summarizes the commits: session ID in metadata, request processor update for hosted curator, metadatadb schema validation
           - Dario and Nikolai flag any cross-service concerns
           - Team agrees this is the right direction or identifies what to change
      2. Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth   [Dario Kestrel must raise this]
           - Dario explains the three review comments he posted on 536
           - Team decides if it's a blocker for release or can ship after 0.1.19
           - If blocker: what is the fix; if not: merge or defer
      3. Understand if the request processor changes create work for other teams   [Emil Brandvold must raise this]
           - Emil notes which services are touched by the commits (bulk-llm-inference, provider-integrations, online-request-processing)
           - Nikolai and Gideon (if involved) flag any observability or executor concerns
           - Decision: no surprises or identify what needs follow-up
    
    On the agenda: Session ID and resume flow progress; Curator tag fix and LLM interface status; Claude 3.7 reasoning PR (536) and any blocking feedback; How request processor changes affect downstream services
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team has a shared picture of what the four commits do, knows whether PR 536 is in the way, and agrees there are no hidden cross-service issues.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - Release notes: 0.1.19 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Four commits on session ID, request processing internals, and metadatadb; driving three active workstreams in provider integrations, online request processing, and release/CI
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Emil's session ID and request processor work is unblocking the resume flow   *** MUST RAISE ***
      2. Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth
      3. Understand if the request processor changes create work for other teams   *** MUST RAISE ***
      4. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Emil's session ID and request processor work is unblocking the resume flow
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. The curator tag fix and three review comments on PR 536 (Claude 3.7 Reasoning)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm Emil's session ID and request processor work is unblocking the resume flow
      2. Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth   *** MUST RAISE ***
      3. Understand if the request processor changes create work for other teams
      4. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Perspective on code execution hardening (ws-033) and overlap with the session ID / resume work
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm Emil's session ID and request processor work is unblocking the resume flow
      2. Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth
      3. Understand if the request processor changes create work for other teams
    goal        Five commits landed today; four workstreams are mid-flight; two PRs older than the merge median (468, 532) need attention; one day-old PR (533) needs momentum.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. One review comment on PR 533; context on cookbooks and multimodal prompt handling
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm Emil's session ID and request processor work is unblocking the resume flow
      2. Land or defer PR 536 (Claude 3.7 Reasoning) without further back-and-forth
      3. Understand if the request processor changes create work for other teams
    goal        Five commits landed today; four workstreams are mid-flight; two PRs older than the merge median (468, 532) need attention; one day-old PR (533) needs momentum.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team has a shared picture of what the four commits do, knows whether PR 536 is in the way, and agrees there are no hidden cross-service issues.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Five commits to core pipeline services today (bulk-llm-inference, online-request-processing, caching-and-resume, provider-integrations); ws-025 and ws-026 are mid-flight; PR 532 (batch response file async) is four days old and stale.

    Today is Tuesday 25 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits to core pipeline services today (bulk-llm-inference, online-request-processing, caching-and-resume, provider-integrations); ws-025 and ws-026 are mid-flight; PR 532 (batch response file async) is four days old and stale.
    
    What it should get through:
      1. Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle   [Emil Brandvold must raise this]
           - Emil walks through commit d0c3445 (update request processor for prev run hosted curator) and the metadatadb schema change
           - Dario confirms the LLM interface surface is unaffected by the session ID metadata
           - Gideon confirms observability (progress bar, cost tracking) still works correctly
      2. Unblock PR 532 (batch response file async) or understand what it's waiting on   [Emil Brandvold must raise this]
           - Emil or Dario flags whether 532 is part of the current push or waiting on something else
           - Team decides: merge this week or defer; it has been four days without movement
           - If merge: quick review; if defer: document the dependency
      3. Confirm provider backend integrations (Azure, inference.net) are tracking correctly with cost maps   [Emil Brandvold must raise this]
           - Emil notes the issue opened today (Issue 538: Azure OpenAI + Batch API support)
           - Team assesses: is this blocking anything or is it groundwork for later
           - Quick decision on priority: now, after this release, or backlog
    
    On the agenda: Session ID and request processor refactoring for hosted curator; Batch response file handling and async method updates; Provider backend status (Azure, inference.net); Metadata and cost map tracking
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Request processor refactoring is validated; PR 532 has a clear path forward; team agrees on the priority of Azure OpenAI support (Issue 538).
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Four commits on session ID tracking, request processor refactoring for hosted curator, and metadatadb schema validation; driving provider-integrations, online-request-processing, and release-and-ci workstreams
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle   *** MUST RAISE ***
      2. Unblock PR 532 (batch response file async) or understand what it's waiting on   *** MUST RAISE ***
      3. Confirm provider backend integrations (Azure, inference.net) are tracking correctly with cost maps   *** MUST RAISE ***
      4. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. The curator tag fix; three comments on PR 536 (Claude 3.7 Reasoning) touching the LLM interface
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle
      2. Unblock PR 532 (batch response file async) or understand what it's waiting on
      3. Confirm provider backend integrations (Azure, inference.net) are tracking correctly with cost maps
    goal        Five commits to core pipeline services today (bulk-llm-inference, online-request-processing, caching-and-resume, provider-integrations); ws-025 and ws-026 are mid-flight; PR 532 (batch response file async) is four days old and stale.
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observer perspective on whether the progress bar upload feature (noted in ws-034) is working as expected
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle
      2. Unblock PR 532 (batch response file async) or understand what it's waiting on
      3. Confirm provider backend integrations (Azure, inference.net) are tracking correctly with cost maps
    goal        Five commits to core pipeline services today (bulk-llm-inference, online-request-processing, caching-and-resume, provider-integrations); ws-025 and ws-026 are mid-flight; PR 532 (batch response file async) is four days old and stale.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. One comment on PR 533; context from recent work on multimodal and batch handling
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate the request processor refactoring for hosted curator doesn't break existing run lifecycle
      2. Unblock PR 532 (batch response file async) or understand what it's waiting on
      3. Confirm provider backend integrations (Azure, inference.net) are tracking correctly with cost maps
    goal        Five commits to core pipeline services today (bulk-llm-inference, online-request-processing, caching-and-resume, provider-integrations); ws-025 and ws-026 are mid-flight; PR 532 (batch response file async) is four days old and stale.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Request processor refactoring is validated; PR 532 has a clear path forward; team agrees on the priority of Azure OpenAI support (Issue 538).


------------------------------------------------------------------------------
## #releases — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Weekly tag is Thursday and Dario Kestrel wants to know whether to rush the PR

    Today is Tuesday 25 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Weekly tag is Thursday and Dario Kestrel wants to know whether to rush the PR
    
    What it should get through:
    
    On the agenda: Dermot Callaghan says a reporting method landing on its own is fine, but anything that changes how entries are matched invalidates every user's cache directory and needs a loud changelog line and its own week; Emil Brandvold drafts the changelog wording for cache_stats() and asks for a docs sentence covering what the method reports when caching is switched off; Dario Kestrel asks whether the two can really ship separately given the numbers will be wrong until the matching is fixed; not resolved
    
    Wrap when: Method provisionally allowed in this cut, keying change pushed to the next one, Dario Kestrel's objection noted and not answered; it is settled that the team agrees first-time users hit a traceback before any run exists
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 267 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 532: ref: make batch response file method async (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)

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
      - — and 559 function/class names and 30 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Weekly tag is Thursday and Dario Kestrel wants to know whether to rush the PR
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. same shape in the onboarding notebook. Cell two of the quickstart asks how much the run will cost, user has never generated anything, they get a traceback and file an issue saying curator is broken on their machine. Three of those in the last two weeks and all three were day-one installs.   *** MUST SETTLE (clue t1.r2.L8) ***
    goal        the team agrees first-time users hit a traceback before any run exists
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Weekly tag is Thursday and Dario Kestrel wants to know whether to rush the PR
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Method provisionally allowed in this cut, keying change pushed to the next one, Dario Kestrel's objection noted and not answered; it is settled that the team agrees first-time users hit a traceback before any run exists


==============================================================================
# 2025-02-26 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five PRs in flight, three merged today, executor hardening landed and shipping in hotfix

    Today is Wednesday 26 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five PRs in flight, three merged today, executor hardening landed and shipping in hotfix
    
    What it should get through:
      1. Confirm executor hardening ready to ship in v0.1.19.post1   [Nikolai Berresford must raise this]
           - Nikolai Berresford raises: docker backend fix and examples now updated, executor in good shape
           - Konrad Feltrin confirms: refactor is clean, no blocking issues
           - Emil Brandvold notes: batch response file landed same day, reinforces stability
      2. Announce code execution launch with updated README   [Konrad Feltrin must raise this]
           - Konrad Feltrin: PR 547 up with launch news and links
           - Nikolai Berresford: checks accuracy against what actually shipped
           - Dario Kestrel or Emil Brandvold: approves for merge
      3. Get cost estimation revamp (PR 546) unblocked for online processor work   [Gideon Halloway must raise this]
           - Gideon Halloway explains the online processor cost structure changes
           - Emil Brandvold or Dario Kestrel: flags any integration concerns
           - Gideon Halloway: adjusts scope if needed
    
    On the agenda: Executor hardening PRs (PR 540, PR 541) post-merge review; README and release notes for code execution launch (PR 547); Cost estimation revamp (PR 546) initial feedback; Stale PRs blocking: PR 536 (Claude reasoning), PR 468 (n-samples), PR 533 (viewer)
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 540, PR 541, PR 545 post-mortems posted; PR 547 approved and merged; PR 546 feedback captured; team confident v0.1.19.post1 is solid; it is settled that the team agrees a caller-supplied image currently runs the task as uid 0 while the shipped image does not
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 272 changes merged to date

    On the table
      - Release notes: v0.1.19.post1 (Nikolai Berresford)
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 547: Update README.md to add code execution launch news (Konrad Feltrin)

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
      - — and 507 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: print(os.getuid()).

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. The executor fixes and version bump merged; knows what the docker backend changes were and why they matter
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm executor hardening ready to ship in v0.1.19.post1   *** MUST RAISE ***
      2. Announce code execution launch with updated README
      3. Get cost estimation revamp (PR 546) unblocked for online processor work
      4. Sanity check on my own build: first line of the task is `print(os.getuid())`. Against the python:3.11-slim I put together for the RAFT verifier it prints 0. Same snippet against the sandbox image we ship prints 1000. Took me an embarrassing while to work out that difference was coming from the image and not from anything I passed.   *** MUST SETTLE (clue t4.r2.L1) ***
         must contain literally: print(os.getuid())
      5. that the doc "Release notes: v0.1.19.post1" is done, and where the others can find it   *** MUST RAISE ***
      6. that "v0.1.19.post1 hotfix is out" has gone out, and what you asked in it   *** MUST RAISE ***
      7. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm executor hardening ready to ship in v0.1.19.post1
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. The executor refactor work and the README update announcing the code execution launch
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm executor hardening ready to ship in v0.1.19.post1
      2. Announce code execution launch with updated README   *** MUST RAISE ***
      3. Get cost estimation revamp (PR 546) unblocked for online processor work
    goal        Announce code execution launch with updated README
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Batch response file async work landed; knows the broader test stability picture
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm executor hardening ready to ship in v0.1.19.post1
      2. Announce code execution launch with updated README
      3. Get cost estimation revamp (PR 546) unblocked for online processor work
    goal        Five PRs in flight, three merged today, executor hardening landed and shipping in hotfix
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost estimation revamp starting; fresh perspective on the PR queue
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm executor hardening ready to ship in v0.1.19.post1
      2. Announce code execution launch with updated README
      3. Get cost estimation revamp (PR 546) unblocked for online processor work   *** MUST RAISE ***
      4. that the doc "Weekly sync notes: week of Feb 24 — v0.1.19.post1 and v0.1.20 shipped" is done, and where the others can find it   *** MUST RAISE ***
    goal        Get cost estimation revamp (PR 546) unblocked for online processor work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 540, PR 541, PR 545 post-mortems posted; PR 547 approved and merged; PR 546 feedback captured; team confident v0.1.19.post1 is solid; it is settled that the team agrees a caller-supplied image currently runs the task as uid 0 while the shipped image does not


------------------------------------------------------------------------------
## #releases — 6 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: hotfix-release shipped today: v0.1.19.post1

    Today is Wednesday 26 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: hotfix-release shipped today: v0.1.19.post1
    
    What it should get through:
      1. Team knows v0.1.19.post1 is live with curator tag fix and executor hardening   [Nikolai Berresford must raise this]
           - Nikolai Berresford announces the tag; posts release notes
           - Dario Kestrel confirms curator tag fix is the main blocker addressed
           - team acknowledges and moves on
    
    On the agenda: v0.1.19.post1 release announcement and changelog; What's fixed: curator tag, executor, batch response, bump version; Next: watch for any hotfix rollouts needed
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.19.post1 announcement posted; team aware of what shipped; no rollback needed
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 272 changes merged to date

    On the table
      - release-v0-1-19-post1 (Nikolai Berresford)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 547: Update README.md to add code execution launch news (Konrad Feltrin)

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
      - — and 507 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just shipped v0.1.19.post1; has the release notes ready
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Team knows v0.1.19.post1 is live with curator tag fix and executor hardening   *** MUST RAISE ***
      2. what "Release notes: v0.1.19.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Team knows v0.1.19.post1 is live with curator tag fix and executor hardening
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Curator tag fix in the hotfix; knows the impact of that bugfix
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Team knows v0.1.19.post1 is live with curator tag fix and executor hardening
    goal        hotfix-release shipped today: v0.1.19.post1
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Batch response async landed same day; part of the patch stability picture
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Team knows v0.1.19.post1 is live with curator tag fix and executor hardening
    goal        hotfix-release shipped today: v0.1.19.post1
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Executor refactor merged; part of the hardening story
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Team knows v0.1.19.post1 is live with curator tag fix and executor hardening
    goal        hotfix-release shipped today: v0.1.19.post1
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.19.post1 announcement posted; team aware of what shipped; no rollback needed


------------------------------------------------------------------------------
## #cookbooks — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Code Executor Hardening landing with example updates and docker backend fix

    Today is Wednesday 26 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Code Executor Hardening landing with example updates and docker backend fix
    
    What it should get through:
      1. Examples updated and tested for code execution launch   [Nikolai Berresford must raise this]
           - Nikolai Berresford: examples now point to the working executor
           - Konrad Feltrin: confirms examples match the published recipe
           - Emil Brandvold or Dario Kestrel: spot any fixture issues
      2. Docker backend hardening is production-ready for code execution feature   [Nikolai Berresford must raise this]
           - Nikolai Berresford: explains the speed-up and the fix
           - Konrad Feltrin: refactor looks clean, no corners cut
           - team: satisfied the feature is solid
    
    On the agenda: Example updates for code execution launch (PR 540); Docker backend and executor refactor landed (PR 541); README announcement ready (PR 547); Any fixture or CI gaps for the launch
    
    Meeting today: Weekly sync
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples confirmed correct; docker backend speed-up and refactor validated; code execution launch ready to announce; it is settled that the team agrees only the no-override default is being constrained, caller overrides stay free
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 272 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 547: Update README.md to add code execution launch news (Konrad Feltrin)

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
      - — and 507 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: CodeExecutor, backend_params.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Docker backend fix and examples updated; knows the executor changes for published pipelines
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Examples updated and tested for code execution launch   *** MUST RAISE ***
      2. Docker backend hardening is production-ready for code execution feature   *** MUST RAISE ***
      3. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Examples updated and tested for code execution launch
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Owns the examples and is launching the code execution feature; knows what needs to be in the README
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Examples updated and tested for code execution launch
      2. Docker backend hardening is production-ready for code execution feature
      3. I have no problem with people pointing `CodeExecutor` at their own image through `backend_params`, that is their machine and their risk, we do not need to police it. What bothers me is the out of the box path where the user never passes anything and quietly gets a different container than they did last month.   *** MUST SETTLE (clue t4.r1.L9) ***
         must contain literally: CodeExecutor, backend_params
    goal        the team agrees only the no-override default is being constrained, caller overrides stay free
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release stability picture; knows whether the fixtures and CI are ready
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Examples updated and tested for code execution launch
      2. Docker backend hardening is production-ready for code execution feature
    goal        Code Executor Hardening landing with example updates and docker backend fix
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Curator tag fix; impacts how examples run
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Examples updated and tested for code execution launch
      2. Docker backend hardening is production-ready for code execution feature
    goal        Code Executor Hardening landing with example updates and docker backend fix
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Examples confirmed correct; docker backend speed-up and refactor validated; code execution launch ready to announce; it is settled that the team agrees only the no-override default is being constrained, caller overrides stay free


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil Brandvold went to add the check and found that by the time a request processor exists, the run has already touched the metadata DB and the cache directory

    Today is Wednesday 26 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil Brandvold went to add the check and found that by the time a request processor exists, the run has already touched the metadata DB and the cache directory
    
    What it should get through:
    
    On the agenda: Emil Brandvold says he put a throwaway assert in base_request_processor and it fired, but by then there was already a run directory with a fingerprint row in it, and the next invocation treated that directory as a resume candidate; Dario Kestrel argues response_format is not always known at construction time in the recipe paths, so a constructor-only check will miss cases; Dermot Callaghan on getting bitten by the leftover row twice in one morning: he had to rm the cache dir by hand before the corrected schema would run at all, and says whatever we do the run should be refused before it earns a place on disk
    
    Wrap when: two candidate hook points on the table, neither chosen; Emil Brandvold to write down what the metadata DB has already committed at each point; it is settled that the team agrees the directory cannot be snapshotted at import time because users set the env var afterwards
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 272 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 533: Feat/resume/hosted curator viewer (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 547: Update README.md to add code execution launch news (Konrad Feltrin)

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
      - — and 507 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: CURATOR_CACHE_DIR.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Emil Brandvold went to add the check and found that by the time a request processor exists, the run has already touched the metadata DB and the cache directory
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. related annoyance from the notebook walkthrough: people import curator in cell 1 and then set CURATOR_CACHE_DIR in cell 4 because that is the order the tutorial reads. The sizing helper I wrote grabs the path once when the module loads, so it kept telling them about the default directory for the rest of the session and I got two emails about it.   *** MUST SETTLE (clue t1.r2.L2) ***
         must contain literally: CURATOR_CACHE_DIR
    goal        the team agrees the directory cannot be snapshotted at import time because users set the env var afterwards
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Emil Brandvold went to add the check and found that by the time a request processor exists, the run has already touched the metadata DB and the cache directory
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   two candidate hook points on the table, neither chosen; Emil Brandvold to write down what the metadata DB has already committed at each point; it is settled that the team agrees the directory cannot be snapshotted at import time because users set the env var afterwards


==============================================================================
# 2025-02-27 — 4 conversation(s), 46 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: PR PR 533 (hosted curator viewer) merged today; need to land the feature cleanly and understand integration points

    Today is Thursday 27 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 533 (hosted curator viewer) merged today; need to land the feature cleanly and understand integration points
    
    What it should get through:
      1. Land PR 533 without regressions to caching or resume   [Emil Brandvold must raise this]
           - Emil walks through what PR 533 ships (hosted viewer metadata and push)
           - Dermot flags whether run lifecycle is clear
           - Gideon confirms cost tracking is unaffected
      2. Confirm token/cost path is correct for viewer requests   [Gideon Halloway must raise this]
           - Gideon explains blocked_capacity usage in token estimate
           - Emil clarifies whether push-to-viewer is metered differently
           - Landed or deferred to next PR
    
    On the agenda: Viewer feature scope: what PR 533 ships vs defers; Caching and resume story for hosted runs; Cost accounting in the new viewer path
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR PR 533 reviewed and merged; team understands the hosted viewer cost model and any deferred work is flagged
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 276 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 506 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The hosted viewer feature design, implementation state, and test coverage
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 533 without regressions to caching or resume   *** MUST RAISE ***
      2. Confirm token/cost path is correct for viewer requests
      3. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 533 without regressions to caching or resume
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Review perspective on the feature surface and integration points
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 533 without regressions to caching or resume
      2. Confirm token/cost path is correct for viewer requests
    goal        PR PR 533 (hosted curator viewer) merged today; need to land the feature cleanly and understand integration points
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Token estimation and capacity planning for the viewer backend
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 533 without regressions to caching or resume
      2. Confirm token/cost path is correct for viewer requests   *** MUST RAISE ***
    goal        Confirm token/cost path is correct for viewer requests
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR PR 533 reviewed and merged; team understands the hosted viewer cost model and any deferred work is flagged


------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 4 open PRs including 2 older than era median; PR 549 and PR 551 are ready; team needs to clear the backlog

    Today is Thursday 27 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 4 open PRs including 2 older than era median; PR 549 and PR 551 are ready; team needs to clear the backlog
    
    What it should get through:
      1. Land PR 549 (Anthropic bug fix) and PR 551 (README)   [Dario Kestrel must raise this]
           - Dario explains the Anthropic UnboundLocalError and the fix
           - Emil or Konrad approves
           - Both merged same-day
      2. Understand PR 546 (cost estimation) blockers and next step   [Gideon Halloway must raise this]
           - Gideon states what PR 546 is waiting on
           - Emil notes if it conflicts with today's viewer work
           - Decision: merge, rebase, or defer
      3. write up Postmortem: v0.1.19.post1 hotfix   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will write Postmortem: v0.1.19.post1 hotfix — Explains what forced the same-day v0.1.19.post1 hotfix release.
    
    On the agenda: PR PR 549: Anthropic batch bug and fix; PR PR 551: README update merge; PR PR 546 and PR 468: Older PRs status check; Postmortem: v0.1.19.post1 hotfix
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 549 and PR 551 merged; PR 546 and PR 468 have a clear owner and next step
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 276 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 506 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Two ready-to-land docs PRs and a bug fix for Anthropic batch
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 549 (Anthropic bug fix) and PR 551 (README)   *** MUST RAISE ***
      2. Understand PR 546 (cost estimation) blockers and next step
      3. write up Postmortem: v0.1.19.post1 hotfix
    goal        Land PR 549 (Anthropic bug fix) and PR 551 (README)
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Code review bandwidth and context on recent changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 549 (Anthropic bug fix) and PR 551 (README)
      2. Understand PR 546 (cost estimation) blockers and next step
      3. write up Postmortem: v0.1.19.post1 hotfix
    goal        4 open PRs including 2 older than era median; PR 549 and PR 551 are ready; team needs to clear the backlog
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Review perspective on PR PR 546 (cost estimation)
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 549 (Anthropic bug fix) and PR 551 (README)
      2. Understand PR 546 (cost estimation) blockers and next step   *** MUST RAISE ***
      3. write up Postmortem: v0.1.19.post1 hotfix
    goal        Understand PR 546 (cost estimation) blockers and next step
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Landed PR 547; can advise on README patterns
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Land PR 549 (Anthropic bug fix) and PR 551 (README)
      2. Understand PR 546 (cost estimation) blockers and next step
      3. write up Postmortem: v0.1.19.post1 hotfix   *** MUST RAISE ***
      4. that the doc "Postmortem: v0.1.19.post1 hotfix" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Postmortem: v0.1.19.post1 hotfix
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 549 and PR 551 merged; PR 546 and PR 468 have a clear owner and next step


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 5 commits to provider-integrations, 4 to online-request-processing today; hosted viewer and cost estimation both landing

    Today is Thursday 27 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 5 commits to provider-integrations, 4 to online-request-processing today; hosted viewer and cost estimation both landing
    
    What it should get through:
      1. Hosted viewer sits cleanly in request/resume flow without breaking cost accounting   [Emil Brandvold must raise this]
           - Emil explains where viewer metadata is added in the pipeline
           - Gideon confirms cost accounting is unaffected
           - Dario flags any Anthropic or batch-specific edge cases
      2. Token estimation with blocked_capacity is stable across batch and online   [Gideon Halloway must raise this]
           - Gideon walks through the blocked_capacity refactor (PR 546)
           - Emil notes tqdm removal and batch changes (#52ff459)
           - Landed or specific blockers called out
    
    On the agenda: Hosted viewer integration into request flow; Token estimation and blocked_capacity alignment; Batch vs online cost accounting parity
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Viewer and cost-estimation work are aligned; any conflicts or deferred items are explicit
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 276 changes merged to date

    On the table
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 506 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Hosted viewer implementation, batch refactoring (tqdm removal), online processor token estimation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Hosted viewer sits cleanly in request/resume flow without breaking cost accounting   *** MUST RAISE ***
      2. Token estimation with blocked_capacity is stable across batch and online
      3. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Hosted viewer sits cleanly in request/resume flow without breaking cost accounting
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Token estimation refactor using blocked_capacity
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Hosted viewer sits cleanly in request/resume flow without breaking cost accounting
      2. Token estimation with blocked_capacity is stable across batch and online   *** MUST RAISE ***
    goal        Token estimation with blocked_capacity is stable across batch and online
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on Anthropic integration and bug patterns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Hosted viewer sits cleanly in request/resume flow without breaking cost accounting
      2. Token estimation with blocked_capacity is stable across batch and online
    goal        5 commits to provider-integrations, 4 to online-request-processing today; hosted viewer and cost estimation both landing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Viewer and cost-estimation work are aligned; any conflicts or deferred items are explicit


------------------------------------------------------------------------------
## #general — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Dario Kestrel reworked the PR after the first review and wants it merged before the cut

    Today is Thursday 27 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel reworked the PR after the first review and wants it merged before the cut
    
    What it should get through:
    
    On the agenda: client construction is gone and it does a single pass over metadata.db; Gideon Halloway confirms it is fast now but the two counts still do not sum to len(dataset) on his dataset with repeated prompts; Dermot Callaghan asks him to prove it runs with no network at all and no provider keys in the environment, since he demos this on planes and has been caught out before; Emil Brandvold still has not checked batch mode and offline parity from two weeks ago and says he will do it before the tag
    
    Wrap when: Close to approval, blocked on the duplicate accounting and on Emil Brandvold's outstanding batch and offline check; it is settled that the team agrees counts pasted without their location cost multiple support round trips to interpret
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 17 release(s) shipped, currently v0.1.19.post1
      - 276 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 536: Claude 3.7 Reasoning (Dario Kestrel)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 506 function/class names and 22 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel reworked the PR after the first review and wants it merged before the cut
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. support thread from yesterday, three round trips. User pasted counts showing zero served locally, we were sure their re-run should have been almost free. I had to get them to echo their env, then ls two directories, before we worked out they had one cache from a docker session and another from their laptop shell. The counts on their own told me nothing.   *** MUST SETTLE (clue t1.r2.L10) ***
    goal        the team agrees counts pasted without their location cost multiple support round trips to interpret
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel reworked the PR after the first review and wants it merged before the cut
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel reworked the PR after the first review and wants it merged before the cut
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Close to approval, blocked on the duplicate accounting and on Emil Brandvold's outstanding batch and offline check; it is settled that the team agrees counts pasted without their location cost multiple support round trips to interpret

