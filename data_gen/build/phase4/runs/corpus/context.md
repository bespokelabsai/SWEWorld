# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-03-20 — 3 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR PR 584 (Mistral batch processor) has been in review for 9 days with 9 comments from Nils Brandt; needs final eyes to land

    Today is Thursday 20 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 584 (Mistral batch processor) has been in review for 9 days with 9 comments from Nils Brandt; needs final eyes to land
    
    What it should get through:
      1. Merge PR 584 and unblock Mistral batch support   [Nils Brandt must raise this]
           - Nils Brandt walks through the integration test changes and pytests cleanup
           - Dario Kestrel or Emil Brandvold raises any blocking concerns about the architecture or dependencies
           - group agrees it is ready or flags specific items to address
    
    On the agenda: Review integration test results and batch endpoint handling; Assess poetry dependency lock and test cleanup; Approve for merge pending any final feedback
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 584 approved and merged, or specific blockers named for a quick follow-up
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 297 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). implementation details of Mistral batch request processor and integration test results
    owns        batch-mode, provider-integrations
    agenda
      1. Merge PR 584 and unblock Mistral batch support   *** MUST RAISE ***
      2. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge PR 584 and unblock Mistral batch support
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. knowledge of request-processing patterns and provider integrations
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge PR 584 and unblock Mistral batch support
    goal        PR PR 584 (Mistral batch processor) has been in review for 9 days with 9 comments from Nils Brandt; needs final eyes to land
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. expertise in retry and batch semantics
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Merge PR 584 and unblock Mistral batch support
    goal        PR PR 584 (Mistral batch processor) has been in review for 9 days with 9 comments from Nils Brandt; needs final eyes to land
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 584 approved and merged, or specific blockers named for a quick follow-up


------------------------------------------------------------------------------
## #cookbooks — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: PR 596 merged today with docs cleanup; ws-045 is mid-flight and needs to slot in new provider examples

    Today is Thursday 20 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 596 merged today with docs cleanup; ws-045 is mid-flight and needs to slot in new provider examples
    
    What it should get through:
      1. Confirm PR 596 shape and start examples table   [Konrad Feltrin must raise this]
           - Konrad Feltrin describes the moved files and why
           - Dario Kestrel or Emil Brandvold flags any missing categories or structure issues
           - group agrees the layout works or names what to adjust
      2. Add Mistral batch example to the corpus   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes that Nils Brandt/Theo Marchetti are landing Mistral batch processor
           - group agrees on example shape and location
           - Theo Marchetti or another can author it after landing
    
    On the agenda: Land PR 596 (zh citation fix and file reorganization); Build the examples table with categories; Plan where Mistral batch example fits
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 596 confirmed; examples table structure agreed; Mistral batch example slot reserved
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 297 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. the examples reorganization and citation fixes in PR 596
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 596 shape and start examples table   *** MUST RAISE ***
      2. Add Mistral batch example to the corpus   *** MUST RAISE ***
    goal        Confirm PR 596 shape and start examples table
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. perspective on how examples are discovered and used
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 596 shape and start examples table
      2. Add Mistral batch example to the corpus
    goal        PR 596 merged today with docs cleanup; ws-045 is mid-flight and needs to slot in new provider examples
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. recent work on OpenAI/DeepSeek integrations that might need examples
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 596 shape and start examples table
      2. Add Mistral batch example to the corpus
    goal        PR 596 merged today with docs cleanup; ws-045 is mid-flight and needs to slot in new provider examples
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 596 confirmed; examples table structure agreed; Mistral batch example slot reserved


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: v0.1.21 merged yesterday; Mistral batch work is in final review; multiple PRs waiting; need to align priorities

    Today is Thursday 20 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.21 merged yesterday; Mistral batch work is in final review; multiple PRs waiting; need to align priorities
    
    What it should get through:
      1. Confirm v0.1.21 is stable and released   [Dermot Callaghan must raise this]
           - Dermot Callaghan gives release status
           - group confirms no rollback needed
           - Nils Brandt notes any test suite issues from the release
      2. Get PR 584 (Mistral batch) landed and plan next   [Nils Brandt must raise this]
           - Nils Brandt describes integration test results and pytests changes
           - group approves or flags final blockers
           - if approved, shift focus to PR 579 and PR 585
    
    On the agenda: v0.1.21 release status and rollout; Mistral batch processor (PR 584) final review; Next PR priorities: PR 579 (OpenAI/DeepSeek), PR 585 (retry/batch)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Release confirmed stable; PR 584 path forward clear; next batch of PRs prioritized
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 297 changes merged to date

    On the table
      - v0.1.21 Release Notes (Dermot Callaghan)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch processor implementation status and test cleanup work
    owns        batch-mode, provider-integrations
    agenda
      1. Confirm v0.1.21 is stable and released
      2. Get PR 584 (Mistral batch) landed and plan next   *** MUST RAISE ***
      3. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 584 (Mistral batch) landed and plan next
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. docs cleanup work and examples table progress
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm v0.1.21 is stable and released
      2. Get PR 584 (Mistral batch) landed and plan next
    goal        v0.1.21 merged yesterday; Mistral batch work is in final review; multiple PRs waiting; need to align priorities
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. v0.1.21 release context and what was in the bump
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm v0.1.21 is stable and released   *** MUST RAISE ***
      2. Get PR 584 (Mistral batch) landed and plan next
      3. what "v0.1.21 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm v0.1.21 is stable and released
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. insight into blocked PRs like PR 579 and PR 585 that may land next
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm v0.1.21 is stable and released
      2. Get PR 584 (Mistral batch) landed and plan next
    goal        v0.1.21 merged yesterday; Mistral batch work is in final review; multiple PRs waiting; need to align priorities
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Release confirmed stable; PR 584 path forward clear; next batch of PRs prioritized


==============================================================================
# 2025-03-21 — 3 conversation(s), 20 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two batch-related PRs are active and old provider backends are stalling.

    Today is Friday 21 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two batch-related PRs are active and old provider backends are stalling.
    
    What it should get through:
      1. Unblock or defer PR 584 (Mistral batch)   [Nils Brandt must raise this]
           - Nils lays out what's left on PR 584 and what the VCR test is doing
           - Emil asks whether PR 585 depends on it or can land first
           - Decision: merge PR 584 if VCR test is solid, or land PR 585 first and circle back
      2. Clarify scope of PR 585 (retry/batch merging)   [Emil Brandvold must raise this]
           - Emil says SimpleStrat is in the PR but asks if it should land separately
           - Dario or Nils pushes back if it's unrelated or should wait
           - Settle: land retry/batch core, defer recipes
      3. Triage stale openai/deepseek backend PRs   [Dario Kestrel must raise this]
           - Dario says PR 565/#566 have been open 19 days and asks for a checkpoint
           - Emil notes they're blocked by other batch/retry work and can wait
           - Agree: revisit after PR 585 lands or block explicitly
    
    On the agenda: Status on Mistral batch (PR 584) and retry/batch integration (PR 585); Whether SimpleStrat goes into PR 585 or lands as a separate feature; Old OpenAI/DeepSeek PRs (PR 565, PR 566) and their place in the queue
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Nils and Emil agree whether to merge PR 584 this week or defer to next; PR 585 scope is locked down; stale PRs are either marked blocked or scheduled.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 298 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Design sense on batch/retry integration; just reviewed both PRs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock or defer PR 584 (Mistral batch)
      2. Clarify scope of PR 585 (retry/batch merging)   *** MUST RAISE ***
      3. Triage stale openai/deepseek backend PRs
      4. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify scope of PR 585 (retry/batch merging)
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch processor implementation; cost lookup fix; fresh eyes on the PR stack
    owns        batch-mode, provider-integrations
    agenda
      1. Unblock or defer PR 584 (Mistral batch)   *** MUST RAISE ***
      2. Clarify scope of PR 585 (retry/batch merging)
      3. Triage stale openai/deepseek backend PRs
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock or defer PR 584 (Mistral batch)
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Context on where examples live; can spot if batch/retry docs need updating
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock or defer PR 584 (Mistral batch)
      2. Clarify scope of PR 585 (retry/batch merging)
      3. Triage stale openai/deepseek backend PRs
    goal        Two batch-related PRs are active and old provider backends are stalling.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the request layer; can judge whether batch changes clash with concurrent logic
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock or defer PR 584 (Mistral batch)
      2. Clarify scope of PR 585 (retry/batch merging)
      3. Triage stale openai/deepseek backend PRs   *** MUST RAISE ***
    goal        Triage stale openai/deepseek backend PRs
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Nils and Emil agree whether to merge PR 584 this week or defer to next; PR 585 scope is locked down; stale PRs are either marked blocked or scheduled.


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Examples table just merged; SimpleStrat is live; release harness is fresh.

    Today is Friday 21 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Examples table just merged; SimpleStrat is live; release harness is fresh.
    
    What it should get through:
      1. Close or expand examples table categories   [Konrad Feltrin must raise this]
           - Konrad runs through the table and asks if a major category is missing
           - Dario or Emil suggests one; Konrad notes whether it can go in a docs follow-up
           - Land it as-is or add one more before release
      2. Settle SimpleStrat example slot   [Emil Brandvold must raise this]
           - Emil asks if SimpleStrat recipe example is baked and testable
           - Konrad confirms it's in PR 598 and points to the script
           - Agree: slot into table or call it a v0.2 addition
      3. Confirm examples pass CI harness   [Nikolai Berresford must raise this]
           - Nikolai asks whether all examples in the table run in test setup
           - Konrad checks or defers to next sprint
           - Note down any that need mocking or fixtures
    
    On the agenda: Table of examples is merged (PR 597); is anything missing?; Do SimpleStrat examples go into the table now or wait for v0.2?; Examples testability in CI — do they all have the harness they need?
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples table is finalized or a one-line gap is noted for Monday; SimpleStrat example placement is decided; CI harness gaps (if any) are tracked.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 298 changes merged to date

    On the table
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Just merged examples table docs; knows what's in the corpus now
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Close or expand examples table categories   *** MUST RAISE ***
      2. Settle SimpleStrat example slot
      3. Confirm examples pass CI harness
    goal        Close or expand examples table categories
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Can spot if SimpleStrat example should slot into examples/ now that it's landed
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Close or expand examples table categories
      2. Settle SimpleStrat example slot   *** MUST RAISE ***
      3. Confirm examples pass CI harness
      4. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Settle SimpleStrat example slot
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Knows what the test harness needs from example scripts
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Close or expand examples table categories
      2. Settle SimpleStrat example slot
      3. Confirm examples pass CI harness   *** MUST RAISE ***
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm examples pass CI harness
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Broad view of what users hit; can flag if an example category is missing
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Close or expand examples table categories
      2. Settle SimpleStrat example slot
      3. Confirm examples pass CI harness
    goal        Examples table just merged; SimpleStrat is live; release harness is fresh.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Examples table is finalized or a one-line gap is noted for Monday; SimpleStrat example placement is decided; CI harness gaps (if any) are tracked.


------------------------------------------------------------------------------
## #pipeline — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Cost lookup fix merged; Mistral batch test is WIP and needs validation.

    Today is Friday 21 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Cost lookup fix merged; Mistral batch test is WIP and needs validation.
    
    What it should get through:
      1. Validate cost lookup fix   [Nils Brandt must raise this]
           - Nils walks through the change (commit 69f576)
           - Emil asks if it affects batch cost accounting or just provider lookups
           - Confirm it's scoped or note a follow-up
      2. VCR test approach for batch backends   [Nils Brandt must raise this]
           - Nils shows the test structure and asks if recording real Mistral calls is the right move
           - Emil or Dario notes whether secrets/billing are handled
           - Decide: record in test env, mock in CI, or defer live testing
    
    On the agenda: Cost lookup fix landed; does it hold?; VCR test for Mistral batch — is the pattern right for CI?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost fix is confirmed safe (or a rollback is flagged); VCR test approach is cleared for CI or deferred to next week with a note.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 298 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Just fixed cost lookup behaviour; VCR integration test in flight for Mistral batch
    owns        batch-mode, provider-integrations
    agenda
      1. Validate cost lookup fix   *** MUST RAISE ***
      2. VCR test approach for batch backends   *** MUST RAISE ***
      3. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate cost lookup fix
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Knows the cost accounting design; can spot if fix has side effects
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate cost lookup fix
      2. VCR test approach for batch backends
    goal        Cost lookup fix merged; Mistral batch test is WIP and needs validation.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the request layer; can judge cost accounting placement
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate cost lookup fix
      2. VCR test approach for batch backends
    goal        Cost lookup fix merged; Mistral batch test is WIP and needs validation.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Cost fix is confirmed safe (or a rollback is flagged); VCR test approach is cleared for CI or deferred to next week with a note.


==============================================================================
# 2025-03-24 — 5 conversation(s), 62 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs merged today; nine older PRs need attention to prevent queue staleness

    Today is Monday 24 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs merged today; nine older PRs need attention to prevent queue staleness
    
    What it should get through:
      1. Confirm gemini example and colab display fixes are solid   [Emil Brandvold must raise this]
           - Emil notes PR 602 merged, references already updated to live API
           - Nikolai approves PR 599, colab cleanup confirmed
           - Dermot verifies both land clean in next test run
      2. Unblock mistral batch and metadata db features   [Nils Brandt must raise this]
           - Nils walks through PR 584 mistral batch implementation
           - Nikolai gives feedback on PR 583 metadata db disable logic
           - Group confirms both are ready for merge or names blockers
    
    On the agenda: Confirm PR 602 (gemini ref) and PR 599 (colab display) are merged and working; Address stale PRs older than median merge time, starting with PR 565/#566 (openai/deepseek clients); Triage PR 584 (mistral batch) and PR 583 (metadata db disable) for unblocking
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Two merged today are confirmed solid; path forward is clear for PR 565/#566 (either reaffirm timeline or close); PR 584 and PR 583 get review feedback or approval to merge
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. provider integration patterns and current API usage
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm gemini example and colab display fixes are solid   *** MUST RAISE ***
      2. Unblock mistral batch and metadata db features
    goal        Confirm gemini example and colab display fixes are solid
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. understanding of metadata db disable feature and its implications
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm gemini example and colab display fixes are solid
      2. Unblock mistral batch and metadata db features
    goal        Four PRs merged today; nine older PRs need attention to prevent queue staleness
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch processor implementation details
    owns        batch-mode, provider-integrations
    agenda
      1. Confirm gemini example and colab display fixes are solid
      2. Unblock mistral batch and metadata db features   *** MUST RAISE ***
    goal        Unblock mistral batch and metadata db features
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. foundational expertise on request processing patterns
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm gemini example and colab display fixes are solid
      2. Unblock mistral batch and metadata db features
    goal        Four PRs merged today; nine older PRs need attention to prevent queue staleness
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Two merged today are confirmed solid; path forward is clear for PR 565/#566 (either reaffirm timeline or close); PR 584 and PR 583 get review feedback or approval to merge


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: PR 601 merged today, reorganizing examples and adding tutorial; mistral batch work is ready to slot in

    Today is Monday 24 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 601 merged today, reorganizing examples and adding tutorial; mistral batch work is ready to slot in
    
    What it should get through:
      1. Confirm examples table structure supports discovery   [Konrad Feltrin must raise this]
           - Konrad walks through the new table layout and tutorial addition
           - Dermot checks if all major provider/pattern categories are covered
           - Emil confirms the structure integrates cleanly with CI
      2. Verify examples remain wired into release-test coverage   [Emil Brandvold must raise this]
           - Emil confirms examples are executed in CI
           - Nikolai (via notes) verifies no coverage gaps
           - Dermot signs off on coverage readiness
    
    On the agenda: Review PR 601 examples table organization and new tutorial; Integrate Nils Brandt' mistral batch example into the updated table; Confirm examples are wired into CI test coverage
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 601 table structure is validated; mistral batch example is slotted in with clear naming; examples remain CI-tested and discovery-friendly
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. completed examples table reorganization and new tutorial
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm examples table structure supports discovery   *** MUST RAISE ***
      2. Verify examples remain wired into release-test coverage
    goal        Confirm examples table structure supports discovery
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. release integration experience and provider example patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm examples table structure supports discovery
      2. Verify examples remain wired into release-test coverage   *** MUST RAISE ***
    goal        Verify examples remain wired into release-test coverage
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. foundational maintainer perspective on example coverage
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm examples table structure supports discovery
      2. Verify examples remain wired into release-test coverage
    goal        PR 601 merged today, reorganizing examples and adding tutorial; mistral batch work is ready to slot in
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 601 table structure is validated; mistral batch example is slotted in with clear naming; examples remain CI-tested and discovery-friendly


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three workstreams are landing simultaneously: cost revamp, provider examples, docs cleanup

    Today is Monday 24 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three workstreams are landing simultaneously: cost revamp, provider examples, docs cleanup
    
    What it should get through:
      1. Confirm cost estimation revamp direction is sound for next steps   [Gideon Halloway must raise this]
           - Gideon presents the cost estimation design for online processors
           - Emil and Konrad Feltrin ask clarifying questions about integration points
           - Gideon commits to next steps or flags dependencies
      2. Align on provider example patterns for future additions   [Emil Brandvold must raise this]
           - Emil notes PR 602 merged, examples now match live APIs
           - Konrad confirms this pattern works with the reorganized examples structure
           - Group agrees on how new provider examples should be added going forward
      3. Validate examples table serves discovery and covers gaps   [Konrad Feltrin must raise this]
           - Konrad walks through the reorganized table and new tutorial
           - Gideon and Emil Brandvold give feedback on whether categories feel complete
           - Konrad commits to any follow-up polish or names what to add next
    
    On the agenda: Gideon: cost estimation revamp direction and colab fixes; Emil: gemini example update status; Konrad: examples table structure and tutorial completion; Team: any blockers or follow-up work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Three workstreams are synchronized; cost revamp gets team buy-in; provider example patterns are clear; examples table is validated for completeness; it is settled that the team agrees the pricing/cost table stays separate and is not part of the consolidation
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - weekly-2025-03-17 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. cost estimation design for online processors and colab display fixes
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm cost estimation revamp direction is sound for next steps   *** MUST RAISE ***
      2. Align on provider example patterns for future additions
      3. Validate examples table serves discovery and covers gaps
    goal        Confirm cost estimation revamp direction is sound for next steps
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. gemini example update and provider integration patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm cost estimation revamp direction is sound for next steps
      2. Align on provider example patterns for future additions   *** MUST RAISE ***
      3. Validate examples table serves discovery and covers gaps
      4. Not keen on folding the cost table into the same place. Pricing comes down from litellm and changes weekly, and half of it is per-region; if it lives next to capability data someone will start hand-editing prices. Keep the money table where it is.   *** MUST SETTLE (clue t2.r2.l8) ***
    goal        Align on provider example patterns for future additions
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. examples reorganization and tutorial work
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm cost estimation revamp direction is sound for next steps
      2. Align on provider example patterns for future additions
      3. Validate examples table serves discovery and covers gaps   *** MUST RAISE ***
      4. that "Weekly update: week of Mar 17" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Validate examples table serves discovery and covers gaps
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. review perspective on release readiness and quality
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm cost estimation revamp direction is sound for next steps
      2. Align on provider example patterns for future additions
      3. Validate examples table serves discovery and covers gaps
    goal        Three workstreams are landing simultaneously: cost revamp, provider examples, docs cleanup
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three workstreams are synchronized; cost revamp gets team buy-in; provider example patterns are clear; examples table is validated for completeness; it is settled that the team agrees the pricing/cost table stays separate and is not part of the consolidation


------------------------------------------------------------------------------
## #releases — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: weekly bump is Thursday and the validator PR is close but has two open questions on it

    Today is Monday 24 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: weekly bump is Thursday and the validator PR is close but has two open questions on it
    
    What it should get through:
    
    On the agenda: Dermot Callaghan asks whether a check that can refuse a run people are currently getting away with counts as a breaking change for the bump; Emil Brandvold wants the changelog line to name the bypass, on the grounds that anyone it blocks unfairly needs a way out in the same release; Dario Kestrel flags that the offline and local-server behaviour is still unresolved and would rather hold the PR than ship a check that stops vLLM users for no reason
    
    Wrap when: held out of Thursday's cut, revisit once the offline behaviour is settled; it is settled that the team agrees warn-and-continue is unacceptable here and it must be a hard failure
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        weekly bump is Thursday and the validator PR is close but has two open questions on it
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. the other flavour of this is worse: on some backends we log a warning that the format cannot be honoured and then just carry on. you get a green run, a full parquet, and every row is an unparsed string you find out about two days later. I would much rather it blow up in my face on line one than hand me a plausible looking dataset   *** MUST SETTLE (clue t2.r1.L9) ***
    goal        the team agrees warn-and-continue is unacceptable here and it must be a hard failure
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        weekly bump is Thursday and the validator PR is close but has two open questions on it
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   held out of Thursday's cut, revisit once the offline behaviour is settled; it is settled that the team agrees warn-and-continue is unacceptable here and it must be a hard failure


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil Brandvold's 40k-row Anthropic batch=True run died when his box rebooted, and re-running the script started a fresh batch while the first one was still sitting on the provider side

    Today is Monday 24 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil Brandvold's 40k-row Anthropic batch=True run died when his box rebooted, and re-running the script started a fresh batch while the first one was still sitting on the provider side
    
    What it should get through:
    
    On the agenda: Emil Brandvold describes the rerun firing a second submission and the first one finishing hours later with nobody reading it; Dario Kestrel states the goal plainly: same script, same run, restart should attach to what is already in flight rather than submit again; open question nobody answers: what counts as 'the same run', and whether the existing metadata DB already knows enough to tell
    
    Wrap when: agreed the reattach behaviour is the feature; where the state lives and what identifies a run left for a design pass Dario Kestrel says he will sketch; it is settled that the team agrees an in-process-only job identifier is lost on restart and forces manual recovery
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Lost a 12 hour Anthropic batch yesterday, ssh session died and took the python process with it. The id only ever existed inside that process, so I spent the morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down. Fine for me, absolutely not something I'd tell a user to do.   *** MUST SETTLE (clue t3.r1.L1) ***
    goal        the team agrees an in-process-only job identifier is lost on restart and forces manual recovery
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Emil Brandvold's 40k-row Anthropic batch=True run died when his box rebooted, and re-running the script started a fresh batch while the first one was still sitting on the provider side
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Emil Brandvold's 40k-row Anthropic batch=True run died when his box rebooted, and re-running the script started a fresh batch while the first one was still sitting on the provider side
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   agreed the reattach behaviour is the feature; where the state lives and what identifies a run left for a design pass Dario Kestrel says he will sketch; it is settled that the team agrees an in-process-only job identifier is lost on restart and forces manual recovery


==============================================================================
# 2025-03-25 — 3 conversation(s), 34 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Nine open PRs with six older than the era median merge time; two batch-related PRs under active review

    Today is Tuesday 25 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nine open PRs with six older than the era median merge time; two batch-related PRs under active review
    
    What it should get through:
      1. PR 584 Mistral batch unblocks or names what it needs   [Nils Brandt must raise this]
           - Nils Brandt states what's left (token usage, batch state enum, VCR cassettes)
           - Emil Brandvold or Dario Kestrel push back on scope or priorities
           - decision: land as-is or add one more hardening pass
      2. PR 585 and PR 579 get a path forward or explicit defer   [Emil Brandvold must raise this]
           - Emil Brandvold outlines which blocks which and why
           - Dario Kestrel weighs in on openai backend readiness
           - group decides: land retry first, or batch-first sequencing
      3. Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked   [Dario Kestrel must raise this]
           - Dario Kestrel names PR 565 OpenAI client as bottleneck
           - group acknowledges or deprioritizes
           - no explicit commit, but surfaces whether this week or next sprint
    
    On the agenda: State of the backlog: which PRs are actually blocking releases; PR 584 Mistral batch processor — what's holding review; PR 585 and PR 579 retry/batch patterns — where they land
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clarity on which batch-related PRs land before release, and explicit deferral of older PRs so they do not clutter the channel
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - Onboarding: Nils Brandt and Theo Marchetti (Konrad Feltrin)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)
      - PR 585: Feat/retry/batch (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch implementation details and what blocks it from landing
    owns        batch-mode, provider-integrations
    agenda
      1. PR 584 Mistral batch unblocks or names what it needs   *** MUST RAISE ***
      2. PR 585 and PR 579 get a path forward or explicit defer
      3. Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Onboarding: nils and theo" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 584 Mistral batch unblocks or names what it needs
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider integration expertise and retry/batch patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 584 Mistral batch unblocks or names what it needs
      2. PR 585 and PR 579 get a path forward or explicit defer   *** MUST RAISE ***
      3. Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 585 and PR 579 get a path forward or explicit defer
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Client.py changes and metadata db context
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 584 Mistral batch unblocks or names what it needs
      2. PR 585 and PR 579 get a path forward or explicit defer
      3. Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked
    goal        Nine open PRs with six older than the era median merge time; two batch-related PRs under active review
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing patterns and OpenAI backend knowledge
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 584 Mistral batch unblocks or names what it needs
      2. PR 585 and PR 579 get a path forward or explicit defer
      3. Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked   *** MUST RAISE ***
    goal        Stale PRs (PR 468, PR 565, PR 583) stay or get unblocked
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clarity on which batch-related PRs land before release, and explicit deferral of older PRs so they do not clutter the channel


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: One commit each to provider-integrations and release-and-ci; tests being removed for Mistral

    Today is Tuesday 25 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One commit each to provider-integrations and release-and-ci; tests being removed for Mistral
    
    What it should get through:
      1. Gemini example refactor and test removals do not leave gaps   [Emil Brandvold must raise this]
           - Emil Brandvold explains what was removed (mistral from tests, gemini example refactored)
           - Nils Brandt confirms mistral batch has own test coverage now via ws-047
           - decision: coverage is adequate or we add back a smoke test
    
    On the agenda: Gemini example and Mistral test cleanup — impact check; Provider integration test coverage after removals
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Confirmation that provider test suite is still sufficient after Mistral refactoring and example cleanup
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)
      - PR 585: Feat/retry/batch (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini example update and test coverage cleanup knowledge
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Gemini example refactor and test removals do not leave gaps   *** MUST RAISE ***
      2. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Gemini example refactor and test removals do not leave gaps
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch provider perspective and what landed
    owns        batch-mode, provider-integrations
    agenda
      1. Gemini example refactor and test removals do not leave gaps
    goal        One commit each to provider-integrations and release-and-ci; tests being removed for Mistral
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider backend patterns and cost estimation logic
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Gemini example refactor and test removals do not leave gaps
    goal        One commit each to provider-integrations and release-and-ci; tests being removed for Mistral
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Confirmation that provider test suite is still sufficient after Mistral refactoring and example cleanup


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario Kestrel's sketch reuses the caching-and-resume fingerprint and Dermot Callaghan does not trust it for this

    Today is Tuesday 25 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel's sketch reuses the caching-and-resume fingerprint and Dermot Callaghan does not trust it for this
    
    What it should get through:
    
    On the agenda: Dario Kestrel proposes hanging the batch record off the existing run fingerprint so resume is free; Dermot Callaghan on the afternoon he lost last month: he pointed the same script at a different model, got handed back the previous run's completions, and only noticed from the token counts; Emil Brandvold pushes back that a separate tracker file is simpler, and asks what happens when someone edits temperature between runs
    
    Wrap when: no decision on fingerprint-vs-tracker; Dermot Callaghan says he will read what the fingerprint actually hashes today and report back; it is settled that the team agrees batch submission and the online path go through the same reuse lookup
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 301 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 584: feat: implement Mistral batch request processor (Nils Brandt)
      - PR 585: Feat/retry/batch (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 432 function/class names and 1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: jsonl.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel's sketch reuses the caching-and-resume fingerprint and Dermot Callaghan does not trust it for this
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel's sketch reuses the caching-and-resume fingerprint and Dermot Callaghan does not trust it for this
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Reminder for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup, that is why when the online path stopped re-sending duplicates last month the batch path quietly stopped too.   *** MUST SETTLE (clue t1.r1.l_scope_1) ***
         must contain literally: jsonl
    goal        the team agrees batch submission and the online path go through the same reuse lookup
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   no decision on fingerprint-vs-tracker; Dermot Callaghan says he will read what the fingerprint actually hashes today and report back; it is settled that the team agrees batch submission and the online path go through the same reuse lookup


==============================================================================
# 2025-03-26 — 4 conversation(s), 41 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Konrad's commit lands today; two PRs older than 15 days block progress

    Today is Wednesday 26 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad's commit lands today; two PRs older than 15 days block progress
    
    What it should get through:
      1. Confirm PR 604 merge unblocks downstream work   [Konrad Feltrin must raise this]
           - Konrad explains why string vs list matters for parse()
           - Emil points out coupling with PR 585
           - Decision: merge, note dependency
      2. Identify which of the six stale PRs should land this week   [Emil Brandvold must raise this]
           - Emil summarizes PR 579, PR 585, PR 590 status
           - Konrad flags what unblocks Mistral batch follow-up
           - Defer PR 468, PR 565, PR 583 to next planning
    
    On the agenda: Review PR 604: input shape preservation logic; Assess blocking impact on PR 579, PR 585; Triage remaining stale PRs
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 604 merges; stale PRs ranked by urgency; PR 579 and PR 585 marked for next sprint
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 303 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - notes-2025-03-24 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 407 function/class names and -1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. The PR's rationale: prompt() and parse() should both preserve input shape
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 604 merge unblocks downstream work   *** MUST RAISE ***
      2. Identify which of the six stale PRs should land this week
      3. the page you are writing, Weekly Notes — Week of Mar 24, has to say this in your own words: Sandbox Image Release Log, status notes. v0.1.5 superseded. v0.1.6 superseded, glibc mismatch broke the C toolchain tests. v0.1.8 built 12 Mar, candidate only, blocked on the pytest collection regression, do not promote until that is fixed. Older lines archived below.   *** MUST SETTLE (clue t4.r1.L4) ***
         must contain literally: v0.1.5, v0.1.6, v0.1.8
      4. that the doc "Weekly Notes — Week of Mar 24" is done, and where the others can find it   *** MUST RAISE ***
      5. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 604 merge unblocks downstream work
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Fresh eyes on the solution; owns related provider-integrations work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 604 merge unblocks downstream work
      2. Identify which of the six stale PRs should land this week   *** MUST RAISE ***
      3. what "Weekly Notes — Week of Mar 24" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Identify which of the six stale PRs should land this week
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 604 merges; stale PRs ranked by urgency; PR 579 and PR 585 marked for next sprint


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nils's Mistral batch work merged today; Konrad Feltrin committed hardening PR; landing phase conversation

    Today is Wednesday 26 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nils's Mistral batch work merged today; Konrad Feltrin committed hardening PR; landing phase conversation
    
    What it should get through:
      1. Confirm Mistral batch backend is landing this week   [Konrad Feltrin must raise this]
           - Konrad reports PR 604 merged, hyperparameters tuned
           - Emil notes cost processing in place
           - Agreement: batch processor ready, VCR test as follow-up
      2. Understand input handling fix scope and impact   [Konrad Feltrin must raise this]
           - Konrad walks through string vs list shape preservation
           - Emil checks coupling with cost calculation
           - Konrad: isolated to prompt()/parse(), no provider impact
    
    On the agenda: Mistral batch backend status: feature-complete?; Input handling fix impact on request processing; Follow-up tasks: VCR integration tests
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Mistral batch backend treated as complete; PR 604 documented in weekly notes; VCR tests deferred to next week
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 303 changes merged to date

    On the table
      - notes-2025-03-24 (Konrad Feltrin)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - notes-2025-03-24 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 407 function/class names and -1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective on input handling fix and its place in the week
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm Mistral batch backend is landing this week   *** MUST RAISE ***
      2. Understand input handling fix scope and impact   *** MUST RAISE ***
      3. what "Weekly Notes — Week of Mar 24" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly Notes — Week of Mar 24" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Mistral batch backend is landing this week
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider-integrations ownership; understands cost processing and batch cancellation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Mistral batch backend is landing this week
      2. Understand input handling fix scope and impact
    goal        Nils's Mistral batch work merged today; Konrad Feltrin committed hardening PR; landing phase conversation
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Mistral batch backend treated as complete; PR 604 documented in weekly notes; VCR tests deferred to next week


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Konrad's PR 604 touches bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; Nils Brandt's batch work merged

    Today is Wednesday 26 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad's PR 604 touches bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; Nils Brandt's batch work merged
    
    What it should get through:
      1. Confirm PR 604 doesn't break caching or cost tracking   [Emil Brandvold must raise this]
           - Emil reviews shape-preservation logic
           - Gideon checks cost lookup still works post-merge
           - Dario confirms caching key unchanged
           - Decision: no regression risk, good to go
      2. Mistral batch cost processing is correct and testable   [Gideon Halloway must raise this]
           - Emil confirms cost lookup fixture in place
           - Gideon notes no live-API tests yet (VCR deferred)
           - Agreement: cost processing landed, integration test follow-up
    
    On the agenda: Input shape preservation in prompt()/parse(); Mistral batch cost processing and retry behavior; Caching implications of PR 604 changes
    
    Meeting today: Weekly sync
    
    No longer here: Nils Brandt — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 604 approved for merge with no caching regressions; Mistral batch cost tracking in place; VCR integration test marked as deferred work; it is settled that Emil Brandvold got results for old prompts after editing the prompt function and restarting
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 303 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 407 function/class names and -1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider-integrations lead; reviewed both PRs; owns request processing layer
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 604 doesn't break caching or cost tracking   *** MUST RAISE ***
      2. Mistral batch cost processing is correct and testable
      3. this one is nastier. I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. the request jsonl sitting on disk was the new one, the job on the provider side was the old one, and nobody compared the two.   *** MUST SETTLE (clue t3.r2.l_pay_emil) ***
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 604 doesn't break caching or cost tracking
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns bulk-llm-inference core; understands caching implications of input normalization
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 604 doesn't break caching or cost tracking
      2. Mistral batch cost processing is correct and testable
    goal        Konrad's PR 604 touches bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; Nils Brandt's batch work merged
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Owns progress-and-cli; understands cost estimation layer
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 604 doesn't break caching or cost tracking
      2. Mistral batch cost processing is correct and testable   *** MUST RAISE ***
      3. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Mistral batch cost processing is correct and testable
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 604 approved for merge with no caching regressions; Mistral batch cost tracking in place; VCR integration test marked as deferred work; it is settled that Emil Brandvold got results for old prompts after editing the prompt function and restarting; Emil Brandvold got results for old prompts after editing the prompt function and restarting


------------------------------------------------------------------------------
## #help — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: someone running the branch against their own OpenAI-compatible server got blocked by the new check even though their server handles the schema fine

    Today is Wednesday 26 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: someone running the branch against their own OpenAI-compatible server got blocked by the new check even though their server handles the schema fine
    
    What it should get through:
    
    On the agenda: Gideon Halloway posts the user's command with a base_url we have never heard of and the refusal message, which claims the model does not support structured output when we simply have no entry for it; Dermot Callaghan says the same thing happens on his Ollama box and he had to comment out the check to get through his afternoon, which is exactly the workaround we said we did not want to create; Dario Kestrel lands on the distinction that mattering here is a schema we know is wrong versus a model we know nothing about, and those two cannot have the same outcome
    
    Wrap when: the unknown-capability case is now the last blocking question; Dario Kestrel to write it up on the PR before the next release window; it is settled that the team agrees people are already patching around the exception to get runs through
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 303 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 407 function/class names and -1 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: try/except.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        someone running the branch against their own OpenAI-compatible server got blocked by the new check even though their server handles the schema fine
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. I wrapped that call in a try/except locally to get the demo dataset out for the Friday cut and I have been carrying the patch since. Not shipping it, but I am also not deleting it, which tells you something.   *** MUST SETTLE (clue t1.r1.l_unhash_2) ***
         must contain literally: try/except
    goal        the team agrees people are already patching around the exception to get runs through
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        someone running the branch against their own OpenAI-compatible server got blocked by the new check even though their server handles the schema fine
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   the unknown-capability case is now the last blocking question; Dario Kestrel to write it up on the PR before the next release window; it is settled that the team agrees people are already patching around the exception to get runs through

