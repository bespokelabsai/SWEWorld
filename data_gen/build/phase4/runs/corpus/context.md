# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-01-24 — 3 conversation(s), 27 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today need eyes; four older PRs need triage

    Today is Friday 24 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today need eyes; four older PRs need triage
    
    What it should get through:
      1. Unblock PR 403 Gemini batch processor by confirming design   [Emil Brandvold must raise this]
           - Emil presents the batch processor approach
           - Dario or Nikolai asks about provider integration pattern reuse
           - Land on next steps: ready to merge or needs iteration
      2. Confirm PR 402 requirements.txt merge is safe   [Nikolai Berresford must raise this]
           - Nikolai confirms why the update was needed
           - Dario approves or flags version concerns
           - Merge or defer decision made
    
    On the agenda: PR 403 Gemini batch processor design and readiness; PR 402 requirements.txt update status; Example code breakage from interface changes
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 402 approved and merged; PR 403 design confirmed or iteration path clear. Older stale PRs (PR 378, PR 362, PR 161, PR 133) acknowledged but deferred until next week.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 200 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)

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
      - — and 855 function/class names and 87 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini batch processor implementation and provider integration patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock PR 403 Gemini batch processor by confirming design   *** MUST RAISE ***
      2. Confirm PR 402 requirements.txt merge is safe
    goal        Unblock PR 403 Gemini batch processor by confirming design
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Dependency update rationale and testing coverage
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Unblock PR 403 Gemini batch processor by confirming design
      2. Confirm PR 402 requirements.txt merge is safe   *** MUST RAISE ***
    goal        Confirm PR 402 requirements.txt merge is safe
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior review perspective and release coordination knowledge
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock PR 403 Gemini batch processor by confirming design
      2. Confirm PR 402 requirements.txt merge is safe
    goal        Two PRs opened today need eyes; four older PRs need triage
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 402 approved and merged; PR 403 design confirmed or iteration path clear. Older stale PRs (PR 378, PR 362, PR 161, PR 133) acknowledged but deferred until next week.


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: 7 commits to examples-cookbooks today; workstream is mid-flight

    Today is Friday 24 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 commits to examples-cookbooks today; workstream is mid-flight
    
    What it should get through:
      1. Identify and fix interface changes breaking example scripts   [Dario Kestrel must raise this]
           - Dario or Dermot says which examples are broken
           - Emil confirms what changed in the LLM interface
           - Quick fix list agreed: instance method vs static, base_url param removal, etc
      2. Push fixes out same-day to unblock users   [Dario Kestrel must raise this]
           - Dario assigns fixes to team members or does them himself
           - Nikolai confirms which fixes go in PR 402 vs new commits
           - Land on: all fixes out today or defer non-critical ones
    
    On the agenda: What interface changes broke examples; Quick fixes needed in examples; Test coverage to prevent regression
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: README and example scripts repaired; users following old examples will not hit interface errors. Fixes land in PR 402 or follow-up commits same-day.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 200 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)

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
      - — and 855 function/class names and 87 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Workstream ownership and understanding of what broke
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Identify and fix interface changes breaking example scripts   *** MUST RAISE ***
      2. Push fixes out same-day to unblock users   *** MUST RAISE ***
    goal        Identify and fix interface changes breaking example scripts
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Recent checkin changes and interface changes he made
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Identify and fix interface changes breaking example scripts
      2. Push fixes out same-day to unblock users
    goal        7 commits to examples-cookbooks today; workstream is mid-flight
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Knowledge of which example patterns are most used
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Identify and fix interface changes breaking example scripts
      2. Push fixes out same-day to unblock users
    goal        7 commits to examples-cookbooks today; workstream is mid-flight
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Understanding of the bulk-llm-inference interface changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Identify and fix interface changes breaking example scripts
      2. Push fixes out same-day to unblock users
    goal        7 commits to examples-cookbooks today; workstream is mid-flight
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   README and example scripts repaired; users following old examples will not hit interface errors. Fixes land in PR 402 or follow-up commits same-day.


------------------------------------------------------------------------------
## #pipeline — 9 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 7 commits touching provider-integrations and bulk-llm-inference

    Today is Friday 24 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 commits touching provider-integrations and bulk-llm-inference
    
    What it should get through:
      1. Confirm Gemini batch processor integrates cleanly into provider layer   [Emil Brandvold must raise this]
           - Emil describes batch API wrapper and how it fits the provider factory pattern
           - Dario asks whether batch mode respects existing retry and caching logic
           - Decision: architecture sound or needs refactor before PR 403 lands
    
    On the agenda: Gemini batch processor architecture fit; Caching and resume behavior under batch mode; Online vs batch request path clarity
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Emil's batch processor PR (PR 403) is either approved for merge or clear iteration path defined. Nikolai's caching fixes validated against batch mode lifecycle.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 200 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)

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
      - — and 855 function/class names and 87 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini batch processor implementation; provider integration patterns; understanding of online vs batch request flow
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Gemini batch processor integrates cleanly into provider layer   *** MUST RAISE ***
    goal        Confirm Gemini batch processor integrates cleanly into provider layer
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior perspective on request processing design; knowledge of retry and resume semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm Gemini batch processor integrates cleanly into provider layer
    goal        7 commits touching provider-integrations and bulk-llm-inference
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Emil's batch processor PR (PR 403) is either approved for merge or clear iteration path defined. Nikolai's caching fixes validated against batch mode lifecycle.


==============================================================================
# 2025-01-27 — 3 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 409 and PR 403 are stalled; PR 406 merged but batch work still blocked on parameter passing

    Today is Monday 27 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 409 and PR 403 are stalled; PR 406 merged but batch work still blocked on parameter passing
    
    What it should get through:
      1. Unblock PR 403 Gemini batch processor   [Emil Brandvold must raise this]
           - Emil surfaces remaining parameter-passing issue from reviews
           - Konrad or Dermot validates the batch-specific code path
           - Team agrees on merge timing
    
    On the agenda: PR 409 merge blocker status; PR 403 Gemini processor readiness; Downstream impacts on caching
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 403 clears one more review cycle; PR 409 merged as dependency; batch processor path defined
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 204 changes merged to date

    On the table
      - weekly-2025-01-20 (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 409: Remove upper bound from tiktoken (Emil Brandvold)

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
      - — and 848 function/class names and 86 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Five commits on batch and Gemini tests; understands the refactor and what PR 403 needs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock PR 403 Gemini batch processor   *** MUST RAISE ***
      2. what "Weekly update: week of Jan 20 — v0.1.16 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock PR 403 Gemini batch processor
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Code quality perspective; has approved PR 409
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Unblock PR 403 Gemini batch processor
    goal        PR 409 and PR 403 are stalled; PR 406 merged but batch work still blocked on parameter passing
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Domain expertise on caching and batch semantics
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock PR 403 Gemini batch processor
    goal        PR 409 and PR 403 are stalled; PR 406 merged but batch work still blocked on parameter passing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 403 clears one more review cycle; PR 409 merged as dependency; batch processor path defined


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Five commits in batch/provider-integrations; PR 406 merged; PR 403 still open; workstream mid-flight with known gaps

    Today is Monday 27 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits in batch/provider-integrations; PR 406 merged; PR 403 still open; workstream mid-flight with known gaps
    
    What it should get through:
      1. Route generation params through Gemini batch path   [Dario Kestrel must raise this]
           - Dario or Emil identifies where params drop off
           - Team sketches fix scope
           - Dario commits to follow-up
      2. Cost calc to cover all batch backends   [Emil Brandvold must raise this]
           - Emil or Dario raises cost discrepancy for Gemini
           - Konrad flags if it touches caching math
           - Agreement on scope
      3. send Weekly update: week of Jan 20 — v0.1.16 shipped   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Jan 20 — v0.1.16 shipped
    
    On the agenda: PR 406 batch refactor landed; next steps; Cost calc for non-OpenAI batch jobs; Generation params on Gemini path; Weekly update: week of Jan 20 — v0.1.16 shipped
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Blockers on PR 403 articulated; param and cost issues assigned; PR 406 validated as safe
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 204 changes merged to date

    On the table
      - weekly-2025-01-20 (Konrad Feltrin)
      - weekly-2025-01-20 (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 409: Remove upper bound from tiktoken (Emil Brandvold)

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
      - — and 848 function/class names and 86 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Complete picture of batch refactor; owns timeline
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Route generation params through Gemini batch path
      2. Cost calc to cover all batch backends   *** MUST RAISE ***
      3. send Weekly update: week of Jan 20 — v0.1.16 shipped
    goal        Cost calc to cover all batch backends
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing context; knows cost accounting
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Route generation params through Gemini batch path   *** MUST RAISE ***
      2. Cost calc to cover all batch backends
      3. send Weekly update: week of Jan 20 — v0.1.16 shipped
      4. what "Weekly update: week of Jan 20 — v0.1.16 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Route generation params through Gemini batch path
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Can spot caching or downstream implications
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Route generation params through Gemini batch path
      2. Cost calc to cover all batch backends
      3. send Weekly update: week of Jan 20 — v0.1.16 shipped   *** MUST RAISE ***
      4. that "Weekly update: week of Jan 20 — v0.1.16 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Jan 20 — v0.1.16 shipped
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Blockers on PR 403 articulated; param and cost issues assigned; PR 406 validated as safe


------------------------------------------------------------------------------
## #pipeline — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Workstream mid-flight; generation params not making it through Gemini path; cost calc missing non-OpenAI batch

    Today is Monday 27 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Workstream mid-flight; generation params not making it through Gemini path; cost calc missing non-OpenAI batch
    
    What it should get through:
      1. Identify param-passing break point   [Dario Kestrel must raise this]
           - Dario or Emil traces request through batch pipeline
           - Identifies conversion or API call layer loss
           - Notes fix location
    
    On the agenda: Where generation params drop on Gemini batch; Cost calc scope for non-OpenAI; PR 403 readiness
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Param-passing issue located; cost-calc scope clarified; deferral or quick fix identified
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 204 changes merged to date

    On the table
      - weekly-2025-01-20 (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 403: Feat/gemini batch processor (Emil Brandvold)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 409: Remove upper bound from tiktoken (Emil Brandvold)

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
      - — and 848 function/class names and 86 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Batch API integration details; knows where params are lost
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Identify param-passing break point
    goal        Workstream mid-flight; generation params not making it through Gemini path; cost calc missing non-OpenAI batch
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Cost accounting; request-layer view
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Identify param-passing break point   *** MUST RAISE ***
      2. what "Weekly update: week of Jan 20 — v0.1.16 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Identify param-passing break point
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Param-passing issue located; cost-calc scope clarified; deferral or quick fix identified


==============================================================================
# 2025-01-28 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.17 shipped today; release notes are due; announcement goes out now.

    Today is Tuesday 28 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.17 shipped today; release notes are due; announcement goes out now.
    
    What it should get through:
      1. confirm v0.1.17 ships clean   [Dermot Callaghan must raise this]
           - Dermot flags the three merged PRs: Gemini batch, tiktoken bound removal, bump itself
           - Emil confirms batch processor is solid and tiktoken unbound was safe
           - Dario notes no request-processing regressions
      2. publish release notes and announcement   [Dermot Callaghan must raise this]
           - Dermot has the notes draft ready
           - Emil adds any batch-processor caveats
           - Notes go to the list with announcement mail
    
    On the agenda: What shipped in v0.1.17; Release notes and announcement; Next release window
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.17 release notes published and announcement sent to the list by end of day.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 207 changes merged to date

    On the table
      - Release notes: v0.1.17 (Dermot Callaghan)
      - Release notes: v0.1.16 (Dermot Callaghan)
      - announce-v0-1-17 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 843 function/class names and 84 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. owns the release cadence; wrote the bump commit
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. confirm v0.1.17 ships clean   *** MUST RAISE ***
      2. publish release notes and announcement   *** MUST RAISE ***
      3. that the doc "Release notes: v0.1.17" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.17 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        confirm v0.1.17 ships clean
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. shipped the Gemini batch processor and tiktoken bound removal
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
    goal        v0.1.17 shipped today; release notes are due; announcement goes out now.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. test and CI perspective on what shipped
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
    goal        v0.1.17 shipped today; release notes are due; announcement goes out now.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. knows the request-processing surface that changed
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
    goal        v0.1.17 shipped today; release notes are due; announcement goes out now.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.17 release notes published and announcement sent to the list by end of day.


------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs are older than the era's median merge time; two new ones opened today.

    Today is Tuesday 28 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs are older than the era's median merge time; two new ones opened today.
    
    What it should get through:
      1. clear path for PR 407 verifiers PR   [Dario Kestrel must raise this]
           - Dario explains what the verifiers PR needs to land
           - Emil checks if it blocks batch-mode work
           - Gideon notes viewer impact if any
      2. route older stale PRs to owners   [Emil Brandvold must raise this]
           - Emil flags that PR 411 (ci: cache) is fresh today and needs eyes
           - Gideon notes PR 161 (Prometheus judge) has been waiting; Konrad or someone else should own it
           - Ilse needs review on PR 362; someone commits to looking
    
    On the agenda: Triage older PRs still open; Unblock PR 407 verifiers; ci: cache PR PR 411 status
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Older PRs are assigned to reviewers or deprioritized; PR 407 has a clear blocker-or-ready status; PR 411 has a reviewer assigned.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 207 changes merged to date

    On the table
      - Postmortem: v0.1.15.post1 hotfix (Emil Brandvold)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 843 function/class names and 84 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. active on batch and provider integrations; opened ci: cache PR today
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. clear path for PR 407 verifiers PR
      2. route older stale PRs to owners   *** MUST RAISE ***
    goal        route older stale PRs to owners
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. owns the verifiers PR; knows what's needed to unblock it
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. clear path for PR 407 verifiers PR   *** MUST RAISE ***
      2. route older stale PRs to owners
      3. what "Postmortem: v0.1.15.post1 hotfix" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        clear path for PR 407 verifiers PR
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. can help review from viewer side
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. clear path for PR 407 verifiers PR
      2. route older stale PRs to owners
    goal        Four PRs are older than the era's median merge time; two new ones opened today.
    available   around today

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). local inference perspective on the fix_json issue
    owns        local-offline-inference
    agenda
      1. clear path for PR 407 verifiers PR
      2. route older stale PRs to owners
    goal        Four PRs are older than the era's median merge time; two new ones opened today.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Older PRs are assigned to reviewers or deprioritized; PR 407 has a clear blocker-or-ready status; PR 411 has a reviewer assigned.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Gemini batch processor landed; Emil flagged serialization and metadata issues; multimodal and structured-output designs are open.

    Today is Tuesday 28 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gemini batch processor landed; Emil flagged serialization and metadata issues; multimodal and structured-output designs are open.
    
    What it should get through:
      1. settle batch metadata and serialization cleanup scope   [Emil Brandvold must raise this]
           - Emil explains the pydantic dump noise and batch metadata shouldn't-be-trusted issues
           - Dario and Dermot assess whether fixes block other work
           - Agreement on whether cleanup lands before or after next release
      2. chart structured-output design implications   [Emil Brandvold must raise this]
           - Emil notes he added structured output support; touches batch and provider layers
           - Dario notes request-processing implications
           - Group identifies which services need updates before v0.2
    
    On the agenda: Batch processor issues flagged by Emil; Structured output support and its reach; Design work for multimodal batch support
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Emil's cleanup work is scoped; structured-output design implications are noted for the 0.2 roadmap; next batch work is clear.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 207 changes merged to date

    On the table
      - release-v0-1-17 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 843 function/class names and 84 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. just landed the Gemini batch processor; flagged pydantic serialization noise and batch metadata concerns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. settle batch metadata and serialization cleanup scope   *** MUST RAISE ***
      2. chart structured-output design implications   *** MUST RAISE ***
      3. what "Release notes: v0.1.17" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        settle batch metadata and serialization cleanup scope
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. knows the broader pipeline surface affected by batch changes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. settle batch metadata and serialization cleanup scope
      2. chart structured-output design implications
    goal        Gemini batch processor landed; Emil flagged serialization and metadata issues; multimodal and structured-output designs are open.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request-processing expertise; can spot integration issues
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. settle batch metadata and serialization cleanup scope
      2. chart structured-output design implications
    goal        Gemini batch processor landed; Emil flagged serialization and metadata issues; multimodal and structured-output designs are open.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. test coverage perspective on batch processor
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. settle batch metadata and serialization cleanup scope
      2. chart structured-output design implications
    goal        Gemini batch processor landed; Emil flagged serialization and metadata issues; multimodal and structured-output designs are open.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Emil's cleanup work is scoped; structured-output design implications are noted for the 0.2 roadmap; next batch work is clear.


==============================================================================
# 2025-01-29 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs opened yesterday/today touching batch-mode and provider-integrations; PR 418, PR 419 need eyes; PR 422 has comments from both Dario Kestrel and Nikolai Berresford that need resolution

    Today is Wednesday 29 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs opened yesterday/today touching batch-mode and provider-integrations; PR 418, PR 419 need eyes; PR 422 has comments from both Dario Kestrel and Nikolai Berresford that need resolution
    
    What it should get through:
      1. land generation params in Gemini batch (PR 418)   [Emil Brandvold must raise this]
           - Emil Brandvold explains the param passthrough fix
           - Dario Kestrel checks the config split doesn't break SimpleLLM callers
           - land or identify one blocking comment
      2. move PR 419 forward or defer it   [Emil Brandvold must raise this]
           - Emil Brandvold syncs what the refactor touches
           - Nikolai Berresford confirms factory-class changes don't collide with SimpleLLM work
           - decide: land now or wait for SimpleLLM to stabilize
      3. decide on PR 422 (kluster.ai backend)   [Dario Kestrel must raise this]
           - Dario Kestrel walks Nikolai Berresford and Emil Brandvold through remaining comments
           - group decides: land with requested changes, or wait for SimpleLLM refactor to finish
           - if landing, Dario Kestrel makes final pass
      4. write up Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped   [Nikolai Berresford must raise this]
           - Nikolai Berresford says they will write Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped — Records the week's work and back-to-back v0.1.17 releases.
    
    On the agenda: review PR 418 (generation params in Gemini batch); review PR 419 (klusterai refactor from Emil); land or defer PR 422 (kluster.ai backend from Dario); Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 418 lands; PR 419 lands or is deferred pending SimpleLLM stabilization; PR 422 either lands with a final pass or waits until tomorrow when config is clearer
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 209 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 418: Pass generation params in gemini batch (Emil Brandvold)

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
      - — and 814 function/class names and 81 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ownership of batch-mode and online-request-processing; has reviewed PR 422 multiple times
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. land generation params in Gemini batch (PR 418)
      2. move PR 419 forward or defer it
      3. decide on PR 422 (kluster.ai backend)   *** MUST RAISE ***
      4. write up Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    goal        decide on PR 422 (kluster.ai backend)
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. authored PR 418 and PR 419 on Gemini batch params and klusterai refactor; knows the architecture
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. land generation params in Gemini batch (PR 418)   *** MUST RAISE ***
      2. move PR 419 forward or defer it   *** MUST RAISE ***
      3. decide on PR 422 (kluster.ai backend)
      4. write up Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    goal        land generation params in Gemini batch (PR 418)
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. just merged PR 420 (push_to_hub override); knows the dataset persistence layer
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. land generation params in Gemini batch (PR 418)
      2. move PR 419 forward or defer it
      3. decide on PR 422 (kluster.ai backend)
      4. write up Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped   *** MUST RAISE ***
      5. that the doc "Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly sync notes: week of Jan 27 — v0.1.17 and v0.1.17.post1 shipped
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 418 lands; PR 419 lands or is deferred pending SimpleLLM stabilization; PR 422 either lands with a final pass or waits until tomorrow when config is clearer


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil's commit 87b004556637 'ref: pass generation params in gemini batch' suggests param flow is still incomplete; workstream notes mention cost calc discounting non-OpenAI batch jobs

    Today is Wednesday 29 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil's commit 87b004556637 'ref: pass generation params in gemini batch' suggests param flow is still incomplete; workstream notes mention cost calc discounting non-OpenAI batch jobs
    
    What it should get through:
      1. confirm param passthrough works end-to-end on Gemini batch   [Emil Brandvold must raise this]
           - Emil Brandvold shows what PR 418 fixes
           - Dario Kestrel checks if SimpleLLM callers need backend=None config
           - Gideon Halloway confirms online path handles params correctly
      2. surface cost calc bug for non-OpenAI batch   [Gideon Halloway must raise this]
           - Gideon Halloway flags where cost discounting is wrong
           - Dario Kestrel confirms it's batch-specific (mentions workstream notes)
           - group decides: fix now or defer to next batch-mode push
    
    On the agenda: trace generation params through Gemini batch path; check cost accounting for batch vs online; plan fix for param passthrough or cost calc
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Param flow is either confirmed working or one bug is surfaced and assigned; cost calc discrepancy is either fixed or logged for next sprint
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 209 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 418: Pass generation params in gemini batch (Emil Brandvold)

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
      - — and 814 function/class names and 81 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. owns batch-mode and online-request-processing; understands cost accounting and param flow
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. confirm param passthrough works end-to-end on Gemini batch
      2. surface cost calc bug for non-OpenAI batch
    goal        Emil's commit 87b004556637 'ref: pass generation params in gemini batch' suggests param flow is still incomplete; workstream notes mention cost calc discounting non-OpenAI batch jobs
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. just shipped Gemini batch processor; knows param flow on that path; added test for dataset hash
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm param passthrough works end-to-end on Gemini batch   *** MUST RAISE ***
      2. surface cost calc bug for non-OpenAI batch
    goal        confirm param passthrough works end-to-end on Gemini batch
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. knows where cost calc happens in online path; can spot discrepancies
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. confirm param passthrough works end-to-end on Gemini batch
      2. surface cost calc bug for non-OpenAI batch   *** MUST RAISE ***
    goal        surface cost calc bug for non-OpenAI batch
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Param flow is either confirmed working or one bug is surfaced and assigned; cost calc discrepancy is either fixed or logged for next sprint


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Dario committed 5 example changes; PR 421 and PR 419 touch factory/refactor code that examples depend on; PR 420 (push_to_hub override) may affect published dataset recipes

    Today is Wednesday 29 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario committed 5 example changes; PR 421 and PR 419 touch factory/refactor code that examples depend on; PR 420 (push_to_hub override) may affect published dataset recipes
    
    What it should get through:
      1. align examples with klusterai factory refactor   [Dario Kestrel must raise this]
           - Dario Kestrel shows which examples use klusterai or factory
           - Emil Brandvold confirms refactor is backward-compatible or requires example update
           - Konrad Feltrin or Nikolai Berresford flags if examples need testing
      2. confirm push_to_hub example still works   [Nikolai Berresford must raise this]
           - Nikolai Berresford explains what override does
           - Dario Kestrel checks if any published recipes are affected
           - decide: update examples or note behavior change in release
    
    On the agenda: sync what PR 421 and PR 419 change for examples; confirm examples work with klusterai backend after refactor; check if push_to_hub override (PR 420) needs example updates
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples are confirmed working or are updated to reflect factory/refactor/push_to_hub changes; any breaking example changes are noted for release notes
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 209 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 418: Pass generation params in gemini batch (Emil Brandvold)

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
      - — and 814 function/class names and 81 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. shipped 3 example commits today (PR 421 refactors klusterai example); understands which examples need the klusterai backend
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. align examples with klusterai factory refactor   *** MUST RAISE ***
      2. confirm push_to_hub example still works
    goal        align examples with klusterai factory refactor
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. refactored factory class and klusterai code; knows what examples need updates
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. align examples with klusterai factory refactor
      2. confirm push_to_hub example still works
    goal        Dario committed 5 example changes; PR 421 and PR 419 touch factory/refactor code that examples depend on; PR 420 (push_to_hub override) may affect published dataset recipes
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. just landed push_to_hub override; knows what that changes in dataset recipes
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. align examples with klusterai factory refactor
      2. confirm push_to_hub example still works   *** MUST RAISE ***
    goal        confirm push_to_hub example still works
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Examples are confirmed working or are updated to reflect factory/refactor/push_to_hub changes; any breaking example changes are noted for release notes


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Two users this month asked how much a re-run would cost before they paid for it, and Dario Kestrel wants to turn that into an API

    Today is Wednesday 29 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two users this month asked how much a re-run would cost before they paid for it, and Dario Kestrel wants to turn that into an API
    
    What it should get through:
    
    On the agenda: Dario Kestrel states the ask plainly: a cache_stats() on curator.LLM that reports how many rows of the last run came off disk and how many went to the provider; Gideon Halloway asks what it hands back, a dict or a small object, and whether the number belongs to the LLM instance or the whole process; left open; Emil Brandvold asks what counts as the last run when someone resumed a crashed one halfway, and nobody has an answer so it gets parked
    
    Wrap when: Everyone agrees the method should exist and roughly what it reports; return type, scoping and resume semantics all still open; it is settled that the team agrees two rows rendering an identical prompt should resolve to one stored entry rather than two sends
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 12 release(s) shipped, currently v0.1.17
      - 209 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)
      - PR 418: Pass generation params in gemini batch (Emil Brandvold)

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
      - — and 814 function/class names and 81 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: RAFT.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Two users this month asked how much a re-run would cost before they paid for it, and Dario Kestrel wants to turn that into an API
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Two users this month asked how much a re-run would cost before they paid for it, and Dario Kestrel wants to turn that into an API
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. RAFT emitted the same question against two chunk ids last night. Byte identical messages payload, I diffed them. Both went out as separate requests and both got billed. I would expect the second one to come straight back off disk since we already have that exact answer.   *** MUST SETTLE (clue t1.r1.l_prompt_3) ***
         must contain literally: RAFT
    goal        the team agrees two rows rendering an identical prompt should resolve to one stored entry rather than two sends
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Everyone agrees the method should exist and roughly what it reports; return type, scoping and resume semantics all still open; it is settled that the team agrees two rows rendering an identical prompt should resolve to one stored entry rather than two sends


==============================================================================
# 2025-01-30 — 4 conversation(s), 38 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs merged today across cost accounting, provider integrations, and release engineering need final checkpoint

    Today is Thursday 30 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs merged today across cost accounting, provider integrations, and release engineering need final checkpoint
    
    What it should get through:
      1. Confirm PR 424 cost processor handles litellm and external provider edge cases correctly   [Emil Brandvold must raise this]
           - Emil describes cost processor implementation; Dermot Callaghan flags litellm vs external provider divergence
           - Dermot pushes back on how external provider fallback is calculated; Emil walks through the logic
           - Decision: approved with cost accounting consistent across both paths
      2. Ensure PR 425 version bump is complete and release notes accurate   [Dermot Callaghan must raise this]
           - Dermot walks through changelog for v0.1.17.post1 covering four merged items
           - Emil confirms PR PR 418 Gemini params fix is included; Gideon Halloway confirms cost display bugfix is there
           - Sign-off: release notes complete
      3. Kluster.ai backend integration merged without regressions   [Dario Kestrel must raise this]
           - Dario confirms PR 422 merged cleanly; Dermot Callaghan noted COMMENTED state suggests review feedback addressed
           - Group confirms no fallout in provider dispatch code
           - Status: landed, no action needed
    
    On the agenda: Review PR 424 cost processor for litellm/external providers; Validate PR 425 version bump and release readiness; Kluster.ai backend (PR 422) integration status
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: All three PRs validated; v0.1.17.post1 release ready to announce
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 213 changes merged to date

    On the table
      - release-v0-1-17-post1 (Dermot Callaghan)
      - Release notes: v0.1.17.post1 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release process rigor and cost accounting context from PR 425 bump
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm PR 424 cost processor handles litellm and external provider edge cases correctly
      2. Ensure PR 425 version bump is complete and release notes accurate   *** MUST RAISE ***
      3. Kluster.ai backend integration merged without regressions
      4. that the doc "Release notes: v0.1.17.post1" is done, and where the others can find it   *** MUST RAISE ***
    goal        Ensure PR 425 version bump is complete and release notes accurate
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Cost processor implementation and Gemini batch fix details
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 424 cost processor handles litellm and external provider edge cases correctly   *** MUST RAISE ***
      2. Ensure PR 425 version bump is complete and release notes accurate
      3. Kluster.ai backend integration merged without regressions
      4. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 424 cost processor handles litellm and external provider edge cases correctly
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Kluster.ai backend integration context from PR 422
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 424 cost processor handles litellm and external provider edge cases correctly
      2. Ensure PR 425 version bump is complete and release notes accurate
      3. Kluster.ai backend integration merged without regressions   *** MUST RAISE ***
    goal        Kluster.ai backend integration merged without regressions
    available   around today

### 4. How it should land

    lands as  partial
    leaving   All three PRs validated; v0.1.17.post1 release ready to announce


------------------------------------------------------------------------------
## #releases — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.17.post1 hotfix released; post-merge checkpoint and deployment signoff needed

    Today is Thursday 30 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.17.post1 hotfix released; post-merge checkpoint and deployment signoff needed
    
    What it should get through:
      1. All four merged changes (PR 418, PR 422, PR 424, PR 425) are in release and have test coverage   [Dermot Callaghan must raise this]
           - Dermot walks through what landed: Gemini params fix, Kluster backend, cost processor, version bump
           - Emil confirms PR 418 and PR 424 cost/batch tests pass; Dario Kestrel confirms PR 422 provider dispatch tests clean
           - Decision: release is test-covered
      2. Cost accounting honesty verified before shipping to users   [Emil Brandvold must raise this]
           - Gideon's cost display bugfix (#no-pr) and Emil Brandvold's cost processor (PR 424) must be in sync
           - Emil confirms: cost processor handles OpenAI batch 50% discount correctly; display shows accurate totals
           - Status: cost fixes are complete
      3. Release approved for immediate deployment   [Dermot Callaghan must raise this]
           - Dermot proposes shipping now; no blockers or known issues flagged
           - Group agrees: v0.1.17.post1 ready
           - Decision: deploy
    
    On the agenda: Confirm all four merged items in v0.1.17.post1 are tested; Verify cost accounting fixes are complete before shipping; Greenlight deployment of hotfix
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.17.post1 deployed; announcement posted to team
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 213 changes merged to date

    On the table
      - release-v0-1-17-post1 (Dermot Callaghan)
      - release-v0-1-17-post1 (Dermot Callaghan)
      - announce-v0-1-17-post1 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering ownership and changelog authorship
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. All four merged changes (PR 418, PR 422, PR 424, PR 425) are in release and have test coverage   *** MUST RAISE ***
      2. Cost accounting honesty verified before shipping to users
      3. Release approved for immediate deployment   *** MUST RAISE ***
      4. that "v0.1.17.post1 hotfix is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        All four merged changes (PR 418, PR 422, PR 424, PR 425) are in release and have test coverage
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Context on cost processor merge and Gemini batch fix; test coverage confirmation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. All four merged changes (PR 418, PR 422, PR 424, PR 425) are in release and have test coverage
      2. Cost accounting honesty verified before shipping to users   *** MUST RAISE ***
      3. Release approved for immediate deployment
      4. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Cost accounting honesty verified before shipping to users
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Kluster.ai backend validation; provider integration stability
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. All four merged changes (PR 418, PR 422, PR 424, PR 425) are in release and have test coverage
      2. Cost accounting honesty verified before shipping to users
      3. Release approved for immediate deployment
    goal        v0.1.17.post1 hotfix released; post-merge checkpoint and deployment signoff needed
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.17.post1 deployed; announcement posted to team


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Four merges across batch mode, cost accounting, provider integrations and release engineering landed same-day; team checkpoint on what's live and next

    Today is Thursday 30 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four merges across batch mode, cost accounting, provider integrations and release engineering landed same-day; team checkpoint on what's live and next
    
    What it should get through:
      1. Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy   [Emil Brandvold must raise this]
           - Emil: PR PR 418 fixes generation params passing in Gemini batch API calls
           - Gideon: cost display bugfix (#fc5214f) lands; only OpenAI models get 50% batch discount
           - Team: batch mode is now usable end-to-end with honest cost numbers
      2. Kluster.ai backend integrated; provider dispatch and cost accounting working   [Dario Kestrel must raise this]
           - Dario: PR PR 422 integrates Kluster.ai backend; dispatch chain updated
           - Emil: cost processor handles Kluster.ai pricing correctly (PR PR 424)
           - Status: Kluster.ai live and costed accurately
      3. Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear   [Dermot Callaghan must raise this]
           - Dermot: coverage floor enforced, pre-commit hooks live, Anthropic integration tests in
           - Emil design doc (WS-028) going out today for next cycle
           - Group: Jan hardening is complete; ready for planned work in Feb
    
    On the agenda: Gemini batch and cost accounting fixes are live; Kluster.ai provider backend integrated; v0.1.17.post1 hotfix shipped; what's in the next release cycle
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team synced on Gemini/cost/Kluster landing; v0.1.17.post1 out; next workstream (WS-028) visibility clear
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 213 changes merged to date

    On the table
      - release-v0-1-17-post1 (Dermot Callaghan)
      - release-v0-1-17-post1 (Dermot Callaghan)
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Batch mode and cost processor implementation details; quick-landing pattern from Gemini Batch Processor Push
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy   *** MUST RAISE ***
      2. Kluster.ai backend integrated; provider dispatch and cost accounting working
      3. Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear
      4. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release rigor checkpoint; version bump and coverage status
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy
      2. Kluster.ai backend integrated; provider dispatch and cost accounting working
      3. Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear   *** MUST RAISE ***
      4. that the doc "WS-028 design: Release Engineering, CI & Test Suite, round two" is done, and where the others can find it   *** MUST RAISE ***
    goal        Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider breadth sprint momentum; Kluster.ai integration outcome
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy
      2. Kluster.ai backend integrated; provider dispatch and cost accounting working   *** MUST RAISE ***
      3. Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear
      4. what "Release notes: v0.1.17.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Kluster.ai backend integrated; provider dispatch and cost accounting working
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost display bugfix and CLI metrics precision observations
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Gemini batch generation params and cost accounting now correct; batch mode live and trustworthy
      2. Kluster.ai backend integrated; provider dispatch and cost accounting working
      3. Release and CI hardening checkpoint; coverage floor, pre-commit, next cycle clear
    goal        Four merges across batch mode, cost accounting, provider integrations and release engineering landed same-day; team checkpoint on what's live and next
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team synced on Gemini/cost/Kluster landing; v0.1.17.post1 out; next workstream (WS-028) visibility clear


------------------------------------------------------------------------------
## #incidents — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Dario Kestrel burned most of a day on completions that were not from the model he thought he was calling

    Today is Thursday 30 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel burned most of a day on completions that were not from the model he thought he was calling
    
    What it should get through:
    
    On the agenda: Dario Kestrel reports rerunning the reannotation example against a different model and getting yesterday's completions back verbatim, and only noticing because the run finished in four seconds; Emil Brandvold says the nightly job has been setting CURATOR_DISABLE_CACHE for weeks specifically to dodge this, which means the nightly pays full price every single night and he is not happy about it; Dermot Callaghan pushes back on the shrug: an entry that came from a different request should not have matched at all, and says that is the thing to fix rather than the flag
    
    Wrap when: No fix lands; the nightly keeps its flag, and the keying question gets attached to the cache_stats() work as the underlying cause; it is settled that the team agrees reuse must be scoped per model rather than switched off wholesale
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 13 release(s) shipped, currently v0.1.17.post1
      - 213 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 407: Verifiers for Code (Dario Kestrel)
      - PR 411: ci: cache (Emil Brandvold)

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
      - — and 804 function/class names and 78 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: CURATOR_DISABLE_CACHE=1.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel burned most of a day on completions that were not from the model he thought he was calling
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel burned most of a day on completions that were not from the model he thought he was calling
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Every time I run a model sweep I end up exporting CURATOR_DISABLE_CACHE=1 for the whole thing, which then means the second and third models pay full price for the prompts I already have at that model.   *** MUST SETTLE (clue t1.r1.l_model_2) ***
         must contain literally: CURATOR_DISABLE_CACHE=1
    goal        the team agrees reuse must be scoped per model rather than switched off wholesale
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   No fix lands; the nightly keeps its flag, and the keying question gets attached to the cache_stats() work as the underlying cause; it is settled that the team agrees reuse must be scoped per model rather than switched off wholesale

