# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-01-17 — 3 conversation(s), 27 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil's PR on token rate limits and output token estimation needs eyes before merge

    Today is Friday 17 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil's PR on token rate limits and output token estimation needs eyes before merge
    
    What it should get through:
      1. Approve PR 373 or identify blockers   [Dario Kestrel must raise this]
           - Emil walks through the moving average logic
           - Dario raises concern about resume state persistence
           - Group decides whether to gate behind a flag or land as-is
    
    On the agenda: Review PR 373 approach: separate input/output token limits; Check token estimation accuracy and backward compatibility; Verify integration with existing rate-limiting
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 373 moves toward merge or gets a clear list of changes needed
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 185 changes merged to date

    On the table
      - Release notes: v0.1.15.post1 (someone)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 373: feat: support separate rate limits for input and output tokens and add moving average estimate of output tokens (Emil Brandvold)

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
      - — and 989 function/class names and 103 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Implementation of separate rate limits and moving average output token estimation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve PR 373 or identify blockers
    goal        Emil's PR on token rate limits and output token estimation needs eyes before merge
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Deep knowledge of request processing and token accounting semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve PR 373 or identify blockers   *** MUST RAISE ***
      2. what "release-v0-1-15-post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Approve PR 373 or identify blockers
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Context on what the integration tests are exercising
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Approve PR 373 or identify blockers
    goal        Emil's PR on token rate limits and output token estimation needs eyes before merge
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 373 moves toward merge or gets a clear list of changes needed


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil landed token estimation; Dario opened four related issues same day; need to sync on priority and sequencing

    Today is Friday 17 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil landed token estimation; Dario opened four related issues same day; need to sync on priority and sequencing
    
    What it should get through:
      1. Agree on order for token-accounting issues   [Dario Kestrel must raise this]
           - Dario pitches all four: update-after-response, finish_reason retry control, require_all_response strictness, max_parallel_requests fallback
           - Emil flags which ones unblock his next work
           - Dermot flags coverage/test implications
      2. Confirm Emil's work unblocks cost tracking   [Emil Brandvold must raise this]
           - Emil describes what PR 373 unlocks downstream
           - Dario asks about resume/checkpoint semantics
           - Group agrees this is pre-landing
    
    On the agenda: Emil's token estimation commit and PR 373 status; Dario's four new issues: what order, what priority; How token accounting fits into January Hardening timeline
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Roadmap for token accounting refined; PR 373 path forward clear
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 185 changes merged to date

    On the table
      - Release notes: v0.1.15.post1 (someone)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 373: feat: support separate rate limits for input and output tokens and add moving average estimate of output tokens (Emil Brandvold)

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
      - — and 989 function/class names and 103 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The moving average output token implementation and rate-limit separation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Agree on order for token-accounting issues
      2. Confirm Emil's work unblocks cost tracking   *** MUST RAISE ***
      3. what "release-v0-1-15-post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Emil's work unblocks cost tracking
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Opened four related issues today; deep knowledge of what breaks when token accounting changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree on order for token-accounting issues   *** MUST RAISE ***
      2. Confirm Emil's work unblocks cost tracking
    goal        Agree on order for token-accounting issues
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release velocity constraints and test coverage priorities
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree on order for token-accounting issues
      2. Confirm Emil's work unblocks cost tracking
    goal        Emil landed token estimation; Dario opened four related issues same day; need to sync on priority and sequencing
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Roadmap for token accounting refined; PR 373 path forward clear


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil's token accounting work touches core request processing; needs pipeline team alignment on rate-limit semantics

    Today is Friday 17 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil's token accounting work touches core request processing; needs pipeline team alignment on rate-limit semantics
    
    What it should get through:
      1. Validate PR 373 doesn't break rate-limit enforcement   [Dario Kestrel must raise this]
           - Emil walks through the separate input/output tracking
           - Dario asks about underestimation risk
           - Dermot flags what integration tests cover
    
    On the agenda: How PR 373 handles token-limit enforcement; Interaction with retries and max_parallel_requests (PR 377); Testing coverage for rate-limit edge cases
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 373 ready for merge or rework identified
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 185 changes merged to date

    On the table
      - Release notes: v0.1.15.post1 (someone)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 373: feat: support separate rate limits for input and output tokens and add moving average estimate of output tokens (Emil Brandvold)

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
      - — and 989 function/class names and 103 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The implementation of separate rate limits for input vs output tokens and moving average
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate PR 373 doesn't break rate-limit enforcement
    goal        Emil's token accounting work touches core request processing; needs pipeline team alignment on rate-limit semantics
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Knowledge of what rate-limiting edge cases have bitten us; the issues he just filed
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate PR 373 doesn't break rate-limit enforcement   *** MUST RAISE ***
      2. what "release-v0-1-15-post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate PR 373 doesn't break rate-limit enforcement
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Pipeline testing strategy and what the integration tests check
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate PR 373 doesn't break rate-limit enforcement
    goal        Emil's token accounting work touches core request processing; needs pipeline team alignment on rate-limit semantics
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 373 ready for merge or rework identified


==============================================================================
# 2025-01-20 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four pull requests need review; three are stale and blocking

    Today is Monday 20 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four pull requests need review; three are stale and blocking
    
    What it should get through:
      1. Merge PR 384 to ship R1 completions object support   [Dermot Callaghan must raise this]
           - Dermot flags what PR 384 does and why it unblocks r1 models
           - Emil or Dario asks about test coverage or backwards compat
           - Dermot confirms it's safe and lands it
      2. Get PR 378, PR 380, PR 381 unblocked so throughput work can land   [Emil Brandvold must raise this]
           - Emil surfaces what's waiting on each PR and why it matters
           - Dario or Konrad reviews and approves or flags what's missing
           - Emil merges as they clear
      3. Confirm docs and CONTRIBUTING updates propagate without breaking examples   [Dario Kestrel must raise this]
           - Dario notes PR 382 and PR 383 are merged
           - Emil or Konrad spot-check that examples still work with them
           - No action needed if they're already in
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    
    On the agenda: Review and merge PR 384 (completions object support); Unblock PR 378, PR 380, PR 381 on throughput hardening; Confirm PR 382, PR 383 documentation updates are solid; Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 384 merges; PR 378, PR 380, PR 381 get unblocked and may land; docs changes confirmed safe
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 189 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 380: ref: make `invalid_finish_reasons` configurable (Emil Brandvold)

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
      - — and 977 function/class names and 102 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Feature work on completions object and r1 support; understands what's blocking releases
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Merge PR 384 to ship R1 completions object support   *** MUST RAISE ***
      2. Get PR 378, PR 380, PR 381 unblocked so throughput work can land
      3. Confirm docs and CONTRIBUTING updates propagate without breaking examples
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        Merge PR 384 to ship R1 completions object support
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Deep knowledge of throughput and request processing; reviewed the rate-limiting feature
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Merge PR 384 to ship R1 completions object support
      2. Get PR 378, PR 380, PR 381 unblocked so throughput work can land   *** MUST RAISE ***
      3. Confirm docs and CONTRIBUTING updates propagate without breaking examples
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        Get PR 378, PR 380, PR 381 unblocked so throughput work can land
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on examples and docs changes; can validate that interface updates propagate
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge PR 384 to ship R1 completions object support
      2. Get PR 378, PR 380, PR 381 unblocked so throughput work can land
      3. Confirm docs and CONTRIBUTING updates propagate without breaking examples   *** MUST RAISE ***
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        Confirm docs and CONTRIBUTING updates propagate without breaking examples
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintaining perspective on what blocks releases and what's nice-to-have
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Merge PR 384 to ship R1 completions object support
      2. Get PR 378, PR 380, PR 381 unblocked so throughput work can land
      3. Confirm docs and CONTRIBUTING updates propagate without breaking examples
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped   *** MUST RAISE ***
      5. the mail you are writing, Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped, has to say this in your own words: Worth remembering the December rebuild before we sign off on the tag work. The appuser line at the bOtto Brennanm of the sandbox Dockerfile got dropped in a refactor and we shipped four days of runs before anybody spotted it. Nothing on our side would ever have noticed. We take whatever the image decided and start it.   *** MUST SETTLE (clue t4.r2.L2) ***
         must contain literally: appuser
      6. that "Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 384 merges; PR 378, PR 380, PR 381 get unblocked and may land; docs changes confirmed safe


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Eight commits landed; four PRs merged; two workstreams in motion

    Today is Monday 20 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Eight commits landed; four PRs merged; two workstreams in motion
    
    What it should get through:
      1. Surface that rate-limiting merged and throughput hardening is now unblocked   [Emil Brandvold must raise this]
           - Emil notes PR 373 merged and what comes next (PR 378, PR 380, PR 381)
           - Dermot or Dario asks if anything broke
           - Emil says integration tests are red on cuda but fixable
      2. Confirm r1 work is kickoff, not blocked, and what the ask is   [Dermot Callaghan must raise this]
           - Dermot notes PR 384 is out and what it does
           - Emil or Dario asks if batch mode or other backends need changes
           - Dermot says likely not, just a flag; can iterate
      3. Make sure examples still work with the new interface   [Dario Kestrel must raise this]
           - Dario notes PR 382, PR 383 are merged
           - Konrad or Emil spot-checks if anything broke
           - Dario says he'll validate examples today if needed
    
    On the agenda: Rate-limiting and throughput PRs landed; three more pending; R1 completions object support kicked off today; Documentation and examples updates confirmed
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team is aligned on what landed and what's next; no surprises or blockers surface
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 189 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 380: ref: make `invalid_finish_reasons` configurable (Emil Brandvold)

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
      - — and 977 function/class names and 102 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Two active workstreams: release hardening and r1 support; knows what landed over the weekend
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Surface that rate-limiting merged and throughput hardening is now unblocked
      2. Confirm r1 work is kickoff, not blocked, and what the ask is   *** MUST RAISE ***
      3. Make sure examples still work with the new interface
    goal        Confirm r1 work is kickoff, not blocked, and what the ask is
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Rate-limiting feature just merged; three PRs still blocking on throughput work; knows what integration tests are red
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Surface that rate-limiting merged and throughput hardening is now unblocked   *** MUST RAISE ***
      2. Confirm r1 work is kickoff, not blocked, and what the ask is
      3. Make sure examples still work with the new interface
    goal        Surface that rate-limiting merged and throughput hardening is now unblocked
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Two documentation PRs merged; knows if examples broke; context on Stratos cleanup
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Surface that rate-limiting merged and throughput hardening is now unblocked
      2. Confirm r1 work is kickoff, not blocked, and what the ask is
      3. Make sure examples still work with the new interface   *** MUST RAISE ***
    goal        Make sure examples still work with the new interface
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release perspective; knows what matters this sprint
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Surface that rate-limiting merged and throughput hardening is now unblocked
      2. Confirm r1 work is kickoff, not blocked, and what the ask is
      3. Make sure examples still work with the new interface
    goal        Eight commits landed; four PRs merged; two workstreams in motion
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team is aligned on what landed and what's next; no surprises or blockers surface


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Four changes to online-request-processing; four to provider-integrations; rate-limiting merged

    Today is Monday 20 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four changes to online-request-processing; four to provider-integrations; rate-limiting merged
    
    What it should get through:
      1. Unblock throughput hardening so three pending PRs can land   [Emil Brandvold must raise this]
           - Emil surfaces what PR 378, PR 380, PR 381 are blocked on
           - Dermot or Dario approves or asks for clarification
           - Emil merges as they clear or defers to tomorrow
      2. Confirm R1 completions object is a flag-only change, no ripple effects   [Dermot Callaghan must raise this]
           - Dermot describes what PR 384 does and why it's safe
           - Emil or Dario asks if batch mode or other backends are affected
           - Dermot confirms it's isolated to the completions path
      3. Fix integration test cuda mock-out so CI passes   [Emil Brandvold must raise this]
           - Emil flags that tests are trying to touch cuda and failing
           - Dario suggests mocking approach
           - Emil implements and retests today or tomorrow
    
    On the agenda: Rate-limiting landed; three throughput PRs unblock today if possible; R1 completions object support: scope and backwards compat; Integration test failures on cuda: mock strategy
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Throughput PRs are unblocked; R1 support is confirmed safe; cuda test mock is in motion
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 10 release(s) shipped, currently v0.1.15.post1
      - 189 changes merged to date

    On the table
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 380: ref: make `invalid_finish_reasons` configurable (Emil Brandvold)

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
      - — and 977 function/class names and 102 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. R1 completions object feature work; knows what needs to change in the request path
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Unblock throughput hardening so three pending PRs can land
      2. Confirm R1 completions object is a flag-only change, no ripple effects   *** MUST RAISE ***
      3. Fix integration test cuda mock-out so CI passes
    goal        Confirm R1 completions object is a flag-only change, no ripple effects
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Rate-limiting just landed; three throughput PRs pending; integration test failures on cuda mock-out
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock throughput hardening so three pending PRs can land   *** MUST RAISE ***
      2. Confirm R1 completions object is a flag-only change, no ripple effects
      3. Fix integration test cuda mock-out so CI passes   *** MUST RAISE ***
    goal        Unblock throughput hardening so three pending PRs can land
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Documentation updates ensure examples work; context on interface changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock throughput hardening so three pending PRs can land
      2. Confirm R1 completions object is a flag-only change, no ripple effects
      3. Fix integration test cuda mock-out so CI passes
    goal        Four changes to online-request-processing; four to provider-integrations; rate-limiting merged
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Throughput PRs are unblocked; R1 support is confirmed safe; cuda test mock is in motion


==============================================================================
# 2025-01-21 — 4 conversation(s), 39 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.16 tag created; release notes and announcement due today

    Today is Tuesday 21 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.16 tag created; release notes and announcement due today
    
    What it should get through:
      1. Release notes capture all five merged changes   [Dermot Callaghan must raise this]
           - Dermot lists the five merges: invalid_finish_reasons config, capacity by max_tokens, cost guard, dataset edge case, version bump
           - Emil confirms both online throughput fixes are in
           - Dario signs off on scope
      2. Announcement goes out to stakeholders   [Dermot Callaghan must raise this]
           - Dermot drafts; asks if Emil or Dario want a line in; ships to general and key channels
    
    On the agenda: Verify what shipped in v0.1.16; Write and ship release notes; Post announcement
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.16 documented and announced; team and users know what shipped
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 194 changes merged to date

    On the table
      - Release notes: v0.1.16 (Dermot Callaghan)
      - Release notes: v0.1.15.post1 (Dermot Callaghan)
      - Release notes: v0.1.15 (Emil Brandvold)
      - announce-v0-1-16 (Dermot Callaghan)
      - release-v0-1-16 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 969 function/class names and 100 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. owns the release process; has merged 5 PRs including the version bump
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Release notes capture all five merged changes   *** MUST RAISE ***
      2. Announcement goes out to stakeholders   *** MUST RAISE ***
      3. that the doc "Release notes: v0.1.16" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.16 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Release notes: v0.1.15.post1" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Release notes: v0.1.15" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture all five merged changes
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on two active workstreams that shipped in this release
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Release notes capture all five merged changes
      2. Announcement goes out to stakeholders
    goal        v0.1.16 tag created; release notes and announcement due today
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. senior review on release quality
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture all five merged changes
      2. Announcement goes out to stakeholders
    goal        v0.1.16 tag created; release notes and announcement due today
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.16 documented and announced; team and users know what shipped


------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 6 PRs opened, 5 older than median merge time, 7 reviews done today

    Today is Tuesday 21 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 6 PRs opened, 5 older than median merge time, 7 reviews done today
    
    What it should get through:
      1. PR 387 (max_tokens capacity blocking) lands   [Emil Brandvold must raise this]
           - Emil explains the capacity bug: Anthropic tokens hit OTPM, need to block earlier
           - Dario asks if this needs documentation for the batch processor too
           - Konrad approves after brief look at the test coverage
      2. PR 394 (data generation cookbook) lands   [Nikolai Berresford must raise this]
           - Nikolai posts the example; Konrad comments on README clarity
           - Nikolai fixes lint; Konrad approves
      3. Stale PRs get triaged or unblocked   [Dario Kestrel must raise this]
           - Emil mentions PR 378 is his max_parallel PR and still WIP, will update tomorrow
           - Dario notes PR 372 (Gemini batch) is blocked on Nils Brandt not yet here; defer
           - Rest are from Nov/before; someone should close or reassign
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped   [Dermot Callaghan must raise this]
           - Dermot Callaghan says they will send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    
    On the agenda: Review and land PR 387 (max_tokens blocking); Review and land PR 394 (data generation example); Clear older stale PRs (PR 378, PR 372, PR 362, PR 161, PR 133); Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 387 and PR 394 land; team agrees on triage of five older PRs
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 194 changes merged to date

    On the table
      - release-v0-1-16 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 969 function/class names and 100 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. knows the refactoring and capacity logic deeply; has six commits this era
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 387 (max_tokens capacity blocking) lands   *** MUST RAISE ***
      2. PR 394 (data generation cookbook) lands
      3. Stale PRs get triaged or unblocked
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
      5. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 387 (max_tokens capacity blocking) lands
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. context on version bump and config changes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 387 (max_tokens capacity blocking) lands
      2. PR 394 (data generation cookbook) lands
      3. Stale PRs get triaged or unblocked
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped   *** MUST RAISE ***
    goal        send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. architectural perspective on max_tokens and capacity blocking
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 387 (max_tokens capacity blocking) lands
      2. PR 394 (data generation cookbook) lands
      3. Stale PRs get triaged or unblocked   *** MUST RAISE ***
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        Stale PRs get triaged or unblocked
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. standards and backward-compat perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 387 (max_tokens capacity blocking) lands
      2. PR 394 (data generation cookbook) lands
      3. Stale PRs get triaged or unblocked
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        6 PRs opened, 5 older than median merge time, 7 reviews done today
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. context on data generation example
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 387 (max_tokens capacity blocking) lands
      2. PR 394 (data generation cookbook) lands   *** MUST RAISE ***
      3. Stale PRs get triaged or unblocked
      4. send Weekly update: week of Jan 13 — v0.1.15 and v0.1.15.post1 shipped
    goal        PR 394 (data generation cookbook) lands
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 387 and PR 394 land; team agrees on triage of five older PRs


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three commits to online-request-processing and provider-integrations; mid-flight workstream on throughput

    Today is Tuesday 21 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three commits to online-request-processing and provider-integrations; mid-flight workstream on throughput
    
    What it should get through:
      1. Cost estimation guard prevents crashes on models with missing prices   [Emil Brandvold must raise this]
           - Emil: the guard in PR 385 now checks availability before calling get_cost
           - Dario: asks about batch mode fallback
           - Emil: will handle in the batch PR separately
      2. PR 378 (max_parallel) gets unblocked for landing   [Dario Kestrel must raise this]
           - Emil: has been stuck 3 days, unclear if design is right
           - Dario: asks what the blocker is — test isolation? semantics?
           - Emil: it's a factory pattern question; will push a fix tomorrow
    
    On the agenda: Confirm cost estimation guard is solid; Unblock PR 378 (max_parallel processor); Survey remaining throughput issues
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost guard confirmed safe; PR 378 gets a plan to unblock by tomorrow
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 194 changes merged to date

    On the table
      - release-v0-1-16 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 969 function/class names and 100 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns the workstream; knows the cost and capacity bugs; has two active PRs in flight
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost estimation guard prevents crashes on models with missing prices   *** MUST RAISE ***
      2. PR 378 (max_parallel) gets unblocked for landing
      3. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Cost estimation guard prevents crashes on models with missing prices
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. context on the SimpleLLM folding work and cost estimation side effects
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost estimation guard prevents crashes on models with missing prices
      2. PR 378 (max_parallel) gets unblocked for landing
    goal        Three commits to online-request-processing and provider-integrations; mid-flight workstream on throughput
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. senior perspective on concurrency and capacity semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost estimation guard prevents crashes on models with missing prices
      2. PR 378 (max_parallel) gets unblocked for landing   *** MUST RAISE ***
    goal        PR 378 (max_parallel) gets unblocked for landing
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. sees data-gen example feedback; not directly in throughput but owns test-backing infrastructure
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Cost estimation guard prevents crashes on models with missing prices
      2. PR 378 (max_parallel) gets unblocked for landing
    goal        Three commits to online-request-processing and provider-integrations; mid-flight workstream on throughput
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Cost guard confirmed safe; PR 378 gets a plan to unblock by tomorrow


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Three changes to online-request-processing and provider-integrations today; mid-flight workstream

    Today is Tuesday 21 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three changes to online-request-processing and provider-integrations today; mid-flight workstream
    
    What it should get through:
      1. Anthropic OTPM capacity respected before sending requests   [Emil Brandvold must raise this]
           - Emil: PR 387 now blocks capacity in online processor if max_tokens hits OTPM limit
           - Dario: asks if this applies to all providers or just Anthropic
           - Emil: Anthropic only for now; others don't have the same tight limits
      2. Cost estimation does not crash on unknown model prices   [Dermot Callaghan must raise this]
           - Dermot: merged PR 385 checks if cost is available before calling get_cost
           - Emil: confirms this unblocks cost estimation for custom models
           - Dario: approves the guard
    
    On the agenda: Land PR 387 (max_tokens blocking for Anthropic); Confirm cost guard (PR 385) stops crashes; Identify remaining throughput issues for next push
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 387 lands; cost guard confirmed; team knows what's next on throughput
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 194 changes merged to date

    On the table
      - release-v0-1-16 (Dermot Callaghan)
      - release-v0-1-16 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 969 function/class names and 100 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns the refactor; knows capacity, cost, and latency issues; driving the workstream
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Anthropic OTPM capacity respected before sending requests   *** MUST RAISE ***
      2. Cost estimation does not crash on unknown model prices
      3. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Anthropic OTPM capacity respected before sending requests
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. the cost estimation side of the request pipeline
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Anthropic OTPM capacity respected before sending requests
      2. Cost estimation does not crash on unknown model prices   *** MUST RAISE ***
      3. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Cost estimation does not crash on unknown model prices
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. senior architecture review; understands concurrency semantics
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Anthropic OTPM capacity respected before sending requests
      2. Cost estimation does not crash on unknown model prices
    goal        Three changes to online-request-processing and provider-integrations today; mid-flight workstream
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 387 lands; cost guard confirmed; team knows what's next on throughput


==============================================================================
# 2025-01-22 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #cookbooks — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Four merges in examples-cookbooks plus one fresh PR on math/amc_aime baseline generation; workstream driver present and examples cleanup mid-flight

    Today is Wednesday 22 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four merges in examples-cookbooks plus one fresh PR on math/amc_aime baseline generation; workstream driver present and examples cleanup mid-flight
    
    What it should get through:
      1. Confirm which example scripts need updates for the LLM interface change   [Dermot Callaghan must raise this]
           - Nikolai flags what changed in his merges
           - Dermot cross-checks against example files to spot breakage
           - Dario agrees which ones are urgent
      2. Land a plan to fix broken examples same-day or defer to tomorrow   [Dario Kestrel must raise this]
           - Konrad suggests priority order
           - Nikolai or Dermot volunteers to take the fixes
           - Either lands them or marks them for tomorrow
    
    On the agenda: Walk the merged README and directory changes; Identify any example scripts broken by recent LLM interface changes; Plan quick fixes for those examples
    
    Meeting today: Weekly sync
    
    Out today: Priya Vandersloot (no commit, review or comment 2025-01-16..2025-02-03) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples either confirmed working or a list of three or fewer scripts to fix tagged for today or tomorrow; the v0.1.16 release notes remain accurate.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 198 changes merged to date

    On the table
      - notes-2025-01-20 (Nikolai Berresford)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 857 function/class names and 87 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Eight commits on README updates, directory renames, and addressing comments across examples-cookbooks
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm which example scripts need updates for the LLM interface change
      2. Land a plan to fix broken examples same-day or defer to tomorrow
    goal        Four merges in examples-cookbooks plus one fresh PR on math/amc_aime baseline generation; workstream driver present and examples cleanup mid-flight
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Two commits fixing docs links and adding attribution; perspective on whether example scripts are still working
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm which example scripts need updates for the LLM interface change   *** MUST RAISE ***
      2. Land a plan to fix broken examples same-day or defer to tomorrow
      3. what "Weekly sync notes: week of Jan 20 — v0.1.16 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm which example scripts need updates for the LLM interface change
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. The workstream driver; knows what the cleanup mandate is and what examples need attention
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm which example scripts need updates for the LLM interface change
      2. Land a plan to fix broken examples same-day or defer to tomorrow   *** MUST RAISE ***
    goal        Land a plan to fix broken examples same-day or defer to tomorrow
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Foundational perspective on what the example corpus should cover and why
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm which example scripts need updates for the LLM interface change
      2. Land a plan to fix broken examples same-day or defer to tomorrow
    goal        Four merges in examples-cookbooks plus one fresh PR on math/amc_aime baseline generation; workstream driver present and examples cleanup mid-flight
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Examples either confirmed working or a list of three or fewer scripts to fix tagged for today or tomorrow; the v0.1.16 release notes remain accurate.


------------------------------------------------------------------------------
## #code-review — 14 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs opened or merged today; Emil has two waiting (4 and 1 days old); Dario just opened PR 398 with a new example

    Today is Wednesday 22 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs opened or merged today; Emil has two waiting (4 and 1 days old); Dario just opened PR 398 with a new example
    
    What it should get through:
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral   [Dario Kestrel must raise this]
           - Dermot flags which are blockers
           - Emil pushes back on PR 378 and PR 387 timeline
           - Dario marks blockers for this week
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)   [Emil Brandvold must raise this]
           - Emil explains both PRs briefly
           - Konrad or Nikolai volunteers to review one
           - Outcome is either a reviewer assigned or a deferral reason
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow   [Dario Kestrel must raise this]
           - Dario describes the deepseek-r1 math baseline example
           - Nikolai or Dermot volunteers to review
           - Merge or mark for tomorrow morning
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped   [Nikolai Berresford must raise this]
           - Nikolai Berresford says they will write Weekly sync notes: week of Jan 20 — v0.1.16 shipped — Records the week's work and the v0.1.16 release.
    
    On the agenda: Triage the stale PR backlog; Get fresh eyes on PR 378 and PR 387; Land or defer PR 398; Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Review assignments on Emil's two PRs; decision on PR 398; agreement on which stale PRs get attention this week.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 198 changes merged to date

    On the table
      - Weekly sync notes: week of Jan 20 — v0.1.16 shipped (Nikolai Berresford)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 387: ref: block capacity by max_tokens for anthropic online (Emil Brandvold)

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
      - — and 857 function/class names and 87 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Two commits today on empty dataset handling; PR PR 378 and PR 387 both waiting for review
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)   *** MUST RAISE ***
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    goal        Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just merged four PRs; knows the current state of examples-cookbooks and the review cycle
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped   *** MUST RAISE ***
      5. that the doc "Weekly sync notes: week of Jan 20 — v0.1.16 shipped" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Just opened PR 398 (math and amc_aime baseline with deepseek-r1); knows the requirements for the new cookbook example
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral   *** MUST RAISE ***
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow   *** MUST RAISE ***
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    goal        Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Four reviews done today; perspective on which older PRs are blockers
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    goal        Four PRs opened or merged today; Emil has two waiting (4 and 1 days old); Dario just opened PR 398 with a new example
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. One comment on PR 394; knows the curation-platform requirements
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Agree which of the five stale PRs (PR 133, PR 161, PR 362, PR 372, PR 378, PR 387) can land this week and which need rework or deferral
      2. Get at least one review on PR 378 (max parallel) and PR 387 (Anthropic token capacity)
      3. Review PR 398 and confirm whether it lands today or waits for tomorrow
      4. write up Weekly sync notes: week of Jan 20 — v0.1.16 shipped
    goal        Four PRs opened or merged today; Emil has two waiting (4 and 1 days old); Dario just opened PR 398 with a new example
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Review assignments on Emil's two PRs; decision on PR 398; agreement on which stale PRs get attention this week.


==============================================================================
# 2025-01-23 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 387 merged today needs review acknowledgment; five stale PRs need attention; PR 378 blocked for five days

    Today is Thursday 23 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 387 merged today needs review acknowledgment; five stale PRs need attention; PR 378 blocked for five days
    
    What it should get through:
      1. Confirm PR 387 correctly implements max_tokens capacity blocking   [Dario Kestrel must raise this]
           - Emil presents the change and capacity impact
           - Dario reviews against request-processing semantics
           - Merge confirmed
      2. Determine what unblocks PR 378 and when   [Emil Brandvold must raise this]
           - Emil raises five-day block on max parallel processor
           - Dario or Nikolai identifies next step or dependency
           - Decision deferred or assigned
    
    On the agenda: Review and approve PR 387 (max_tokens capacity blocking for Anthropic); Address stale PRs PR 378, PR 372, PR 362, PR 161, PR 133; Discuss unblocking path for PR 378 (max parallel request processor)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 387 formally closed; clarity on whether PR 378 can move this week or lands in next cycle
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 199 changes merged to date

    On the table
      - Release notes: v0.1.16 (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 398: add math and amc_aime baseline data gen w/ deepseek-r1 (Dario Kestrel)

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
    role        Core Platform Engineer, Request Processing. Anthropic capacity blocking work, max_tokens changes, finish_reasons configuration
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 387 correctly implements max_tokens capacity blocking
      2. Determine what unblocks PR 378 and when   *** MUST RAISE ***
    goal        Determine what unblocks PR 378 and when
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior review of request processing changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 387 correctly implements max_tokens capacity blocking   *** MUST RAISE ***
      2. Determine what unblocks PR 378 and when
      3. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 387 correctly implements max_tokens capacity blocking
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Context on requirements.txt updates to examples-cookbooks
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm PR 387 correctly implements max_tokens capacity blocking
      2. Determine what unblocks PR 378 and when
    goal        PR 387 merged today needs review acknowledgment; five stale PRs need attention; PR 378 blocked for five days
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 387 formally closed; clarity on whether PR 378 can move this week or lands in next cycle


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil is in landing phase of January throughput work; changes merged today; team needs to know what shipped

    Today is Thursday 23 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil is in landing phase of January throughput work; changes merged today; team needs to know what shipped
    
    What it should get through:
      1. Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing   [Emil Brandvold must raise this]
           - Emil describes what shipped and capacity gains expected
           - Dario validates testing coverage
           - Team acknowledges ready for production
      2. Identify which job patterns will benefit and set expectations   [Dario Kestrel must raise this]
           - Dario raises job pattern questions
           - Emil clarifies max_tokens impact per provider
           - Dario or Emil owns communicating changes to users
    
    On the agenda: January throughput hardening is landing: max_tokens blocking, finish_reasons config, capacity efficiency; Capacity impact assessment: what jobs should run faster now?; Planning next: what hits the limit next?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what throughput improvements shipped, which job types benefit, and what the next bottleneck likely is
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 11 release(s) shipped, currently v0.1.16
      - 199 changes merged to date

    On the table
      - Release notes: v0.1.16 (Dermot Callaghan)
      - Weekly sync notes: week of Jan 20 — v0.1.16 shipped (Nikolai Berresford)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 372: Add Gemini batch request processor (Millrow Refactor Bot)
      - PR 378: feat: support max parallel request processor (Emil Brandvold)
      - PR 398: add math and amc_aime baseline data gen w/ deepseek-r1 (Dario Kestrel)

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
    role        Core Platform Engineer, Request Processing. Completed max_tokens capacity blocking, finish_reasons config, online processor efficiency gains
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing   *** MUST RAISE ***
      2. Identify which job patterns will benefit and set expectations
      3. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Weekly sync notes: week of Jan 20 — v0.1.16 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior context on capacity blocking semantics and testing strategy
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing
      2. Identify which job patterns will benefit and set expectations   *** MUST RAISE ***
    goal        Identify which job patterns will benefit and set expectations
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Bulk-inference and multimodal context; recent R1 completions work
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing
      2. Identify which job patterns will benefit and set expectations
    goal        Emil is in landing phase of January throughput work; changes merged today; team needs to know what shipped
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Context on requirements.txt and release-and-ci
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm January throughput work (max_tokens, finish_reasons, capacity efficiency) is in v0.1.16 and ready for testing
      2. Identify which job patterns will benefit and set expectations
    goal        Emil is in landing phase of January throughput work; changes merged today; team needs to know what shipped
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what throughput improvements shipped, which job types benefit, and what the next bottleneck likely is

