# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


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
      3. write up Prompt-level response cache keying   [Dario Kestrel must raise this]
           - Dario Kestrel says they will write Prompt-level response cache keying — the design for prompt-level response cache keying
    
    On the agenda: What shipped in v0.1.17; Release notes and announcement; Next release window; Prompt-level response cache keying
    
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
      3. write up Prompt-level response cache keying
      4. that the doc "Release notes: v0.1.17" is done, and where the others can find it   *** MUST RAISE ***
      5. that "v0.1.17 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      6. what "Release notes: v0.1.16" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        confirm v0.1.17 ships clean
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. shipped the Gemini batch processor and tiktoken bound removal
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
      3. write up Prompt-level response cache keying
    goal        v0.1.17 shipped today; release notes are due; announcement goes out now.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. test and CI perspective on what shipped
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
      3. write up Prompt-level response cache keying
    goal        v0.1.17 shipped today; release notes are due; announcement goes out now.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. knows the request-processing surface that changed
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. confirm v0.1.17 ships clean
      2. publish release notes and announcement
      3. write up Prompt-level response cache keying   *** MUST RAISE ***
      4. the page you are writing, Prompt-level response cache keying, has to say this in your own words: Writing down what I think the sane behaviour is, because right now everyone's answer is rm -rf on the cache dir: if generation_params differ from the stored run, those rows should be going out to the provider again, and only those rows.   *** MUST SETTLE (clue t1.r1.l_params_3) ***
         must contain literally: generation_params
      5. the mail you are writing, Re: Prompt-level response cache keying, has to say this in your own words: Line I'd like us to actually hold to, since it keeps coming up in review. A cache write is an optimisation for the next run. Failing one makes the next run more expensive, it does not make this run invalid. So nothing that has already cost the user money gets aborted because we couldn't put a file on disk, we take the hit on the rerun and carry on.   *** MUST SETTLE (clue t3.r1.L11) ***
      6. that the doc "Prompt-level response cache keying" is done, and where the others can find it   *** MUST RAISE ***
      7. that "Re: Prompt-level response cache keying" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Prompt-level response cache keying
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
      5. the comment you are writing, comment on Handover doc: Request-processing core and provider backends, dario to emil, has to say this in your own words: House rule for the core class, since this comes up in review a lot: `LLM.__init__` already resolves the backend, checks the api key env var is present and normalises the model name. By the time `__call__` has the dataset in hand we have committed to the run and the honest options get much worse.   *** MUST SETTLE (clue t2.r1.L7) ***
         must contain literally: `LLM.__init__`, `__call__`
      6. leave a comment on the wiki page "Handover doc: Request-processing core and provider backends, dario to emil" — you questions or adds to the page, about handing Request-processing core and provider backends to emil   *** MUST RAISE ***
      7. that your question about "comment on Handover doc: Request-processing core and provider backends, dario to emil" is now ON it, where the next person to read it will see it, rather than only said here
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
      3. the page you are writing, Structured output schema validation before dispatch, has to say this in your own words: Adding this to the troubleshooting page since it is the third report: if you edit your response_format between runs, either wipe the cache directory or set CURATOR_DISABLE_CACHE=1 first, otherwise you will get objects built to the previous schema.   *** MUST SETTLE (clue t1.r1.l_schema_2) ***
         must contain literally: response_format, CURATOR_DISABLE_CACHE=1
      4. that the doc "Structured output schema validation before dispatch" is done, and where the others can find it   *** MUST RAISE ***
      5. that "Re: Structured output schema validation before dispatch" has gone out, and what you asked in it   *** MUST RAISE ***
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
# 2025-03-04 — 3 conversation(s), 42 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened or merged today; two stale PRs (>25 days) blocking provider work

    Today is Tuesday 4 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened or merged today; two stale PRs (>25 days) blocking provider work
    
    What it should get through:
      1. Land PR 575 and PR 576 to unblock cost estimation and viewer   [Emil Brandvold must raise this]
           - Emil Brandvold explains the model-name fix in cost processor addresses a Gemini edge case
           - Gideon Halloway validates it aligns with the online processor revamp
           - Dermot Callaghan signs off on PR 576 after checking the viewer push
      2. Triage the stalled provider backends and decide next steps   [Dario Kestrel must raise this]
           - Dario Kestrel flags PR 565 (OpenAI client) and PR 566 (DeepSeek) have been open 2 days and need review
           - Emil Brandvold or Gideon Halloway offers to take a pass or delegates to someone with provider bandwidth
           - group acknowledges the backlog and slots them for next day
    
    On the agenda: Review and merge PR 575 (cost processor model name fix); Review and merge PR 576 (viewer integration); Check on stalled provider backends (PR 565, PR 566)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 575 and PR 576 merge; provider PRs get explicit next-step assigned or flagged for tomorrow
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 283 changes merged to date

    On the table
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 576: Ref/push to viewer (Emil Brandvold)

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
      - — and 469 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Two new PRs ready for eyes: cost processor fix and viewer integration, plus context on mandatory process_response validation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 575 and PR 576 to unblock cost estimation and viewer   *** MUST RAISE ***
      2. Triage the stalled provider backends and decide next steps
      3. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 575 and PR 576 to unblock cost estimation and viewer
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just merged the online processor cost revamp (PR PR 546); knows the shape of the remaining fixes needed
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 575 and PR 576 to unblock cost estimation and viewer
      2. Triage the stalled provider backends and decide next steps
    goal        Three PRs opened or merged today; two stale PRs (>25 days) blocking provider work
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Fresh review of PR 576 (viewer push) with approval; knows the pipeline surface
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 575 and PR 576 to unblock cost estimation and viewer
      2. Triage the stalled provider backends and decide next steps
    goal        Three PRs opened or merged today; two stale PRs (>25 days) blocking provider work
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Unblocked on two provider backend PRs (PR 565, PR 566) that have been sitting; knows what those need
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 575 and PR 576 to unblock cost estimation and viewer
      2. Triage the stalled provider backends and decide next steps   *** MUST RAISE ***
      3. the comment you are writing, comment on Postmortem: kluster.ai DeepSeek Output-Token Default, has to say this in your own words: API convention, please keep to it: bad configuration handed to the core class raises ValueError, same as an unknown backend name or a base_url we cannot parse. Users wrap their setup block in try/except ValueError and script around it.   *** MUST SETTLE (clue t2.r1.L10) ***
         must contain literally: ValueError
      4. leave a comment on the wiki page "Postmortem: kluster.ai DeepSeek Output-Token Default" — you questions or adds to the page, about what broke on 1 Mar and why   *** MUST RAISE ***
      5. that your question about "comment on Postmortem: kluster.ai DeepSeek Output-Token Default" is now ON it, where the next person to read it will see it, rather than only said here
    goal        Triage the stalled provider backends and decide next steps
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 575 and PR 576 merge; provider PRs get explicit next-step assigned or flagged for tomorrow


------------------------------------------------------------------------------
## #pipeline — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 5 changes to online-request-processing, 4 to provider-integrations; cost revamp merged, gemini fixes in flight

    Today is Tuesday 4 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 5 changes to online-request-processing, 4 to provider-integrations; cost revamp merged, gemini fixes in flight
    
    What it should get through:
      1. Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection   [Gideon Halloway must raise this]
           - Gideon Halloway walks through the 0→better-default and weighted-avg→weighted-avg×success-factor logic
           - Emil Brandvold confirms the litellm int wrapper stacks cleanly on top
           - group agrees the kluster deepseek case is now handled
      2. Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop   [Emil Brandvold must raise this]
           - Emil Brandvold flags that failed responses with None parsed values weren't being counted, throwing off summaries
           - Gideon Halloway or Dermot Callaghan confirm the tally fix is correct
           - process_response now mandatory in create_dataset closes a validation gap
      3. Route Gemini rate limit handling: own path or lean on generic fallback   [Emil Brandvold must raise this]
           - Emil Brandvold explains Gemini rate limits need special handling instead of falling through generic
           - Dario Kestrel or Gideon Halloway asks whether to add a Gemini-specific branch or strengthen the generic
           - group decides: either patch it now or flag as follow-up if the generic path is good enough
    
    On the agenda: Validate the output-token-estimate and success-factor fixes; Land the litellm float→int wrapper and token-field fixes; Clarify Gemini rate limit handling versus generic fallback
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost estimation revamp is complete and landing; Gemini rate limit strategy is decided (fix now or defer)
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 283 changes merged to date

    On the table
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - Weekly sync notes: week of Feb 24 — v0.1.19.post1 and v0.1.20 shipped (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 576: Ref/push to viewer (Emil Brandvold)

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
      - — and 469 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just shipped the online processor cost revamp (PR 546); knows the exact bug (output token default 0) that caused kluster deepseek to dump requests at once, plus the success-factor fix for remaining-cost projection
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection   *** MUST RAISE ***
      2. Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop
      3. Route Gemini rate limit handling: own path or lean on generic fallback
      4. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Three commits stacked on top of Gideon's work: token estimate wrapping in int (litellm backend float issue), mime_type grab off Image, and mandatory process_response validation; also driving the Gemini rate limit and failed-response-None-value tally fixes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection
      2. Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop   *** MUST RAISE ***
      3. Route Gemini rate limit handling: own path or lean on generic fallback   *** MUST RAISE ***
      4. what "Weekly sync notes: week of Feb 24 — v0.1.19.post1 and v0.1.20 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Fresh review of the cost-estimation chain; owns the bulk pipeline and can spot integration gaps
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection
      2. Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop
      3. Route Gemini rate limit handling: own path or lean on generic fallback
    goal        5 changes to online-request-processing, 4 to provider-integrations; cost revamp merged, gemini fixes in flight
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request-processing core; may spot downstream impact in online or batch paths
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm output-token default and success-factor fixes prevent request dumps and improve cost projection
      2. Land token-field fixes (mime_type, None-value tally, process_response mandatory) to close cost estimation loop
      3. Route Gemini rate limit handling: own path or lean on generic fallback
    goal        5 changes to online-request-processing, 4 to provider-integrations; cost revamp merged, gemini fixes in flight
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Cost estimation revamp is complete and landing; Gemini rate limit strategy is decided (fix now or defer)


------------------------------------------------------------------------------
## #engineering — 16 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 7 commits, 2 merged, 3 workstreams active, 2 blocked on old PRs

    Today is Tuesday 4 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 commits, 2 merged, 3 workstreams active, 2 blocked on old PRs
    
    What it should get through:
      1. Cost estimation 1/n is done; next steps clear   [Gideon Halloway must raise this]
           - Gideon Halloway: cost revamp landed, output token default and success factor fixed
           - Emil Brandvold: token-field fixes stacking on top, process_response now mandatory
           - group agrees the consolidation sprint is tracking well
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly   [Emil Brandvold must raise this]
           - Emil Brandvold flags PR 468 is 25 days old and PR 571 just opened
           - Dario Kestrel or Konrad Feltrin says whether those are blockers or can slip
           - group assigns owner or marks as next-sprint
      3. Dario gets time to review provider backends or handoff is assigned   [Dario Kestrel must raise this]
           - Dario Kestrel asks for review time on PR 565 and PR 566 or delegates to Gideon Halloway/Emil Brandvold
           - group slots it or confirms it's lower priority than Gemini fixes
           - understood: provider breadth is consolidation-era work, should move this week
    
    On the agenda: State of cost estimation fixes and what's next; Review blockers and stalled work; Confirm priorities for rest of week
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands cost revamp is landing, blockers are either unblocked or deferred, and provider backend review is scheduled
    
    Do NOT wrap before about 11 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 283 changes merged to date

    On the table
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 576: Ref/push to viewer (Emil Brandvold)

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
      - — and 469 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Six commits across cost estimation, token handling, and process_response validation; two PRs open and waiting; two driving workstreams
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Cost estimation 1/n is done; next steps clear
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly   *** MUST RAISE ***
      3. Dario gets time to review provider backends or handoff is assigned
    goal        Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost revamp just merged; knows the remaining steps in the 1/n series and what it unblocks
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Cost estimation 1/n is done; next steps clear   *** MUST RAISE ***
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly
      3. Dario gets time to review provider backends or handoff is assigned
      4. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Cost estimation 1/n is done; next steps clear
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider backend work stalled; knows the two new backends and what's needed to land them
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Cost estimation 1/n is done; next steps clear
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly
      3. Dario gets time to review provider backends or handoff is assigned   *** MUST RAISE ***
      4. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Dario gets time to review provider backends or handoff is assigned
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Reviewed PR 576 (viewer); owns the pipeline surface and can flag integration risks
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Cost estimation 1/n is done; next steps clear
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly
      3. Dario gets time to review provider backends or handoff is assigned
    goal        7 commits, 2 merged, 3 workstreams active, 2 blocked on old PRs
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Helping with cost revamp; can advise on whether it blocks downstream work
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Cost estimation 1/n is done; next steps clear
      2. Unblock PR 468 (n samples) and PR 571 (RAFT) or defer them explicitly
      3. Dario gets time to review provider backends or handoff is assigned
    goal        7 commits, 2 merged, 3 workstreams active, 2 blocked on old PRs
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team understands cost revamp is landing, blockers are either unblocked or deferred, and provider backend review is scheduled


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
      4. the page you are writing, Batch job status persistence across process restarts, has to say this in your own words: House rule for anything that only reports on the cache: connect to the metadata db with mode=ro.   *** MUST SETTLE (clue t1.r2.L6) ***
         must contain literally: mode=ro
      5. the mail you are writing, Re: Batch job status persistence across process restarts, has to say this in your own words: For what it's worth, the online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate and we argued about it for a while.   *** MUST SETTLE (clue t3.r1.L8) ***
      6. the mail you are writing, Re: Batch job status persistence across process restarts, has to say this in your own words: Support thread worth reading: user points CURATOR_CACHE_DIR at /mnt/shared so they can start a run on the laptop and finish it on the box. Their expectation is that everything a rerun needs is under that path. Today the request and response files follow CURATOR_CACHE_DIR and nothing else does, so "resumable" means two different things depending on which half of the run you're talking about, and they noticed.   *** MUST SETTLE (clue t3.r1.L3) ***
         must contain literally: CURATOR_CACHE_DIR
      7. that the doc "Batch job status persistence across process restarts" is done, and where the others can find it   *** MUST RAISE ***
      8. that "Re: Batch job status persistence across process restarts" has gone out, and what you asked in it   *** MUST RAISE ***
      9. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
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
# 2025-04-07 — 4 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two batch-related PRs need review; Dermot's PR 614 is already 5 days old

    Today is Monday 7 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two batch-related PRs need review; Dermot's PR 614 is already 5 days old
    
    What it should get through:
      1. PR 621 finish reason fix approved and merged   [Emil Brandvold must raise this]
           - Emil walks through the Gemini response shape issue and the fix
           - Dermot asks whether this is a separate bug or fallout from parts-key fix (PR 612)
           - Conclusion: separate but both needed, PR 621 lands today
      2. PR 614 unblocked or scheduled for landing   [Dermot Callaghan must raise this]
           - Dermot outlines why batch cancellation has edge cases in resumable jobs
           - Emil confirms the interaction with caching logic is clear
           - Either approved today or deferred to after PR 621 lands
    
    On the agenda: PR 621: finish reason missing in Gemini batch; PR 614: batch cancellation edge cases; stale PRs and merge blockers
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 621 approved; PR 614 either merged or visibly unblocked for Wednesday
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 315 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 31 (someone)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 614: fix: multiple bugs in batch cancellation (Dermot Callaghan)
      - PR 615: feat: add failed requests jsonl (Emil Brandvold)

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
      - — and 367 function/class names and 46 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini batch response-shape details and the sequence of fixes landed
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 621 finish reason fix approved and merged   *** MUST RAISE ***
      2. PR 614 unblocked or scheduled for landing
      3. what "notes-2025-03-31" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 621 finish reason fix approved and merged
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Testing and edge-case perspective on batch cancellation and error handling
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 621 finish reason fix approved and merged
      2. PR 614 unblocked or scheduled for landing   *** MUST RAISE ***
    goal        PR 614 unblocked or scheduled for landing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 621 approved; PR 614 either merged or visibly unblocked for Wednesday


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Batch mode fixes landed over the weekend; pipeline layer needs to reason about impact on request flow and cost tracking

    Today is Monday 7 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Batch mode fixes landed over the weekend; pipeline layer needs to reason about impact on request flow and cost tracking
    
    What it should get through:
      1. Confirm Gemini batch fixes don't regress cost or retry logic   [Emil Brandvold must raise this]
           - Emil explains the two fixes and why they landed separately
           - Dario checks whether retry logic sees the finish reason correctly now
           - Gideon confirms metrics are clean; no spike in silent batch failures
      2. Decide if broader Gemini batch audit is needed or if fixes close the issue   [Dario Kestrel must raise this]
           - Dermot raises whether other providers have similar response-shape surprises
           - Emil notes this was specific to how Gemini structures multi-part responses
           - Conclusion: Gemini-specific, but add a test case to catch similar issues faster
    
    On the agenda: Gemini batch parts and finish-reason sequence of bugs; Whether both bugs are Gemini-specific or a broader batch-response-shape issue; Impact on retries, cost accounting, and rate limits
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confident in the batch fixes; no new audit needed; PR 621 clears for merge; it is settled that Gideon Halloway saw cost accounting go 10x wrong because a resumed job's model differed from the configured one
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 315 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 31 (someone)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 614: fix: multiple bugs in batch cancellation (Dermot Callaghan)
      - PR 615: feat: add failed requests jsonl (Emil Brandvold)

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
      - — and 367 function/class names and 46 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini batch fix details and understanding of parts-key vs finish-reason as separate issues
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Gemini batch fixes don't regress cost or retry logic   *** MUST RAISE ***
      2. Decide if broader Gemini batch audit is needed or if fixes close the issue
      3. what "notes-2025-03-31" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Gemini batch fixes don't regress cost or retry logic
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Provider integration testing and experience with how different backends respond to malformed batch submissions
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm Gemini batch fixes don't regress cost or retry logic
      2. Decide if broader Gemini batch audit is needed or if fixes close the issue
    goal        Batch mode fixes landed over the weekend; pipeline layer needs to reason about impact on request flow and cost tracking
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Batch API contract knowledge and retry logic awareness
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm Gemini batch fixes don't regress cost or retry logic
      2. Decide if broader Gemini batch audit is needed or if fixes close the issue   *** MUST RAISE ***
    goal        Decide if broader Gemini batch audit is needed or if fixes close the issue
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Statistics and observability layer perspective on whether the fix is visible in metrics
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm Gemini batch fixes don't regress cost or retry logic
      2. Decide if broader Gemini batch audit is needed or if fixes close the issue
      3. the cost counter after a resume prices everything at whatever model the current config says, while the responses are coming back from whatever the job was actually submitted with. saw it come out about 10x off. we are going to get an issue filed about that number and I have nothing good to say.   *** MUST SETTLE (clue t3.r2.l_model_gideon) ***
    goal        Gideon Halloway saw cost accounting go 10x wrong because a resumed job's model differed from the configured one
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team confident in the batch fixes; no new audit needed; PR 621 clears for merge; it is settled that Gideon Halloway saw cost accounting go 10x wrong because a resumed job's model differed from the configured one; Gideon Halloway saw cost accounting go 10x wrong because a resumed job's model differed from the configured one


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Monday morning: batch fixes landed, KlusterAI work ready, and ws-055 design due today

    Today is Monday 7 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Monday morning: batch fixes landed, KlusterAI work ready, and ws-055 design due today
    
    What it should get through:
      1. Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug   [Emil Brandvold must raise this]
           - Emil recaps parts-key fix (PR 612) and finish-reason fix (PR 621)
           - Dermot asks if there are similar issues waiting or if Gemini batch is stable now
           - Dario suggests moving ws-050 to 'done' unless a third issue shows up this week
      2. Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly   [Nikolai Berresford must raise this]
           - Nikolai confirms PR 620 (config map) is landed and PR 622 (llama4 models) is unblocked
           - Emil confirms no interaction with batch-mode changes
           - Quick approval; plan to merge PR 622 today
      3. Confirm ws-055 (release/CI) kickoff timing and what blocks it   [Dermot Callaghan must raise this]
           - Dermot signals he's writing ws-055 design today and it's due now
           - Dario confirms ws-055 should start Apr 8 (tomorrow)
           - Team acknowledges: ws-050 and ws-053 close this week; ws-054 and ws-055 open
    
    On the agenda: Batch mode bug sweep status and closure plan; KlusterAI llama4 additions and model list stability; Week's focus: still consolidation or shift to new provider breadth work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clear picture of three workstreams wrapping (ws-050, ws-053, ws-047) and two starting (ws-054, ws-055); PR 622 ready to merge; Dermot's design due today
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 315 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - weekly-2025-03-31 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 614: fix: multiple bugs in batch cancellation (Dermot Callaghan)
      - PR 615: feat: add failed requests jsonl (Emil Brandvold)

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
      - — and 367 function/class names and 46 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Status on Gemini batch fixes and what's queued in ws-050
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug   *** MUST RAISE ***
      2. Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly
      3. Confirm ws-055 (release/CI) kickoff timing and what blocks it
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. KlusterAI model list update and llama4 additions ready to land
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug
      2. Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly   *** MUST RAISE ***
      3. Confirm ws-055 (release/CI) kickoff timing and what blocks it
    goal        Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Testing and merge readiness perspective; writing WS-055 design
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug
      2. Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly
      3. Confirm ws-055 (release/CI) kickoff timing and what blocks it   *** MUST RAISE ***
      4. the page you are writing, WS-055: Release Engineering, CI & Test Suite, has to say this in your own words: Recording the layout while I'm in here. The run fingerprint hashes the prompt function, the model name, the generation params and the dataset; one directory per fingerprint under the cache root; requests and responses live in it. CURATOR_DISABLE_CACHE bypasses that directory cleanly. We have not been consistent about applying that to newer state.   *** MUST SETTLE (clue t3.r1.L4) ***
         must contain literally: CURATOR_DISABLE_CACHE
      5. that the doc "WS-055: Release Engineering, CI & Test Suite" is done, and where the others can find it   *** MUST RAISE ***
      6. what "Weekly update: week of Mar 31" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm ws-055 (release/CI) kickoff timing and what blocks it
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Roadmap and blocking issues overview
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Ws-050 (Gemini batch sweep) closure plan: are we done or is there a third bug
      2. Ws-053 (KlusterAI) ready to close; PR 622 merges cleanly
      3. Confirm ws-055 (release/CI) kickoff timing and what blocks it
    goal        Monday morning: batch fixes landed, KlusterAI work ready, and ws-055 design due today
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear picture of three workstreams wrapping (ws-050, ws-053, ws-047) and two starting (ws-054, ws-055); PR 622 ready to merge; Dermot's design due today


------------------------------------------------------------------------------
## #general — 6 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Dermot's ws-055 design is due today; Konrad Feltrin's weekly mail is a standing item; weekend PRs need acknowledgment

    Today is Monday 7 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dermot's ws-055 design is due today; Konrad Feltrin's weekly mail is a standing item; weekend PRs need acknowledgment
    
    What it should get through:
      1. Ws-055 design visible to the team and unblocked for tomorrow's start   [Dermot Callaghan must raise this]
           - Dermot posts design-ws-055-release-and-ci and a summary
           - Konrad confirms it aligns with the release cadence
           - Team reads and any blockers surface in thread
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed   [Dario Kestrel must raise this]
           - Brief recap: Gemini batch fixes, KlusterAI config, rich CLI env disable
           - Gideon confirms no metrics anomalies
           - Team moves forward with PR 621 and PR 622 in flight
      3. send Weekly update: week of Mar 31   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Mar 31
    
    On the agenda: WS-055 design posted and reviewed; Weekend summary: three PRs merged, two new PRs, no incidents; Week's shape: consolidation theme continues, two workstreams closing; Weekly update: week of Mar 31
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: WS-055 design posted; team aligned on the week; no regressions flagged from weekend changes
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 315 changes merged to date

    On the table
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - weekly-2025-03-31 (Konrad Feltrin)
      - weekly-2025-03-31 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 614: fix: multiple bugs in batch cancellation (Dermot Callaghan)
      - PR 615: feat: add failed requests jsonl (Emil Brandvold)

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
      - — and 367 function/class names and 46 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Roadmap and timeline perspective
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed   *** MUST RAISE ***
      3. send Weekly update: week of Mar 31
    goal        Weekend changes (three merges, no incidents) acknowledged and risks assessed
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Ws-055 design due today; it shapes the week's release/CI work
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start   *** MUST RAISE ***
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed
      3. send Weekly update: week of Mar 31
      4. what "Weekly update: week of Mar 31" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Ws-055 design visible to the team and unblocked for tomorrow's start
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Status on active workstreams
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed
      3. send Weekly update: week of Mar 31
    goal        Dermot's ws-055 design is due today; Konrad Feltrin's weekly mail is a standing item; weekend PRs need acknowledgment
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective and weekly cadence ownership
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed
      3. send Weekly update: week of Mar 31   *** MUST RAISE ***
      4. that "Weekly update: week of Mar 31" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Mar 31
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. KlusterAI work closure update
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed
      3. send Weekly update: week of Mar 31
    goal        Dermot's ws-055 design is due today; Konrad Feltrin's weekly mail is a standing item; weekend PRs need acknowledgment
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability and metrics perspective
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Ws-055 design visible to the team and unblocked for tomorrow's start
      2. Weekend changes (three merges, no incidents) acknowledged and risks assessed
      3. send Weekly update: week of Mar 31
    goal        Dermot's ws-055 design is due today; Konrad Feltrin's weekly mail is a standing item; weekend PRs need acknowledgment
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   WS-055 design posted; team aligned on the week; no regressions flagged from weekend changes


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
      1. write up Docker code executor image pinning   [Nikolai Berresford must raise this]
           - Nikolai Berresford says they will write Docker code executor image pinning — the design for docker code executor image pinning
    
    On the agenda: Konrad Feltrin walks through the diff in pass rate and the fact that the only thing that moved was what docker pulled; Nikolai Berresford says the Docker backend of CodeExecutor asks for the sandbox image by name with no tag, so whatever is newest wins, and states the shape of the feature: a pinned tag plus a way for callers to override it through backend_params; open question nobody answers: which tag to pin to, and whether the pinned value lives in code or somewhere a user can set without editing curator; Docker code executor image pinning
    
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
      1. write up Docker code executor image pinning   *** MUST RAISE ***
      2. the mail you are writing, Re: Docker code executor image pinning, has to say this in your own words: If we do tighten this, my preference is the first task blows up at create.   *** MUST SETTLE (clue t4.r2.L12) ***
      3. the mail you are writing, Re: Docker code executor image pinning, has to say this in your own words: Reading the docker backend before I review this: when a caller sets `backend_params={'image': ...}` the create call goes down a shorter path than the default one, and the extra kwargs we assemble for our own tag never get near it. I do not think anybody chose that, it is just where the code ended up.   *** MUST SETTLE (clue t4.r2.L9) ***
         must contain literally: backend_params={'image': ...}
      4. the mail you are writing, Re: Docker code executor image pinning, has to say this in your own words: On the thread with the team who want their own image: they want it purely so scipy and their internal client lib are already there, they are not asking us to change how the container runs. I told them the workspace still comes in read-only from our side and they said fine, they write everything to stdout anyway.   *** MUST SETTLE (clue t4.r2.L6) ***
         must contain literally: read-only
      5. that the doc "Docker code executor image pinning" is done, and where the others can find it   *** MUST RAISE ***
      6. that "Re: Docker code executor image pinning" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Docker code executor image pinning
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. write up Docker code executor image pinning
      2. lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit.   *** MUST SETTLE (clue t3.r2.l_model_dermot) ***
         must contain literally: gpt-4o-mini, gpt-4o
    goal        Dermot Callaghan got outputs from the old model after editing the model name and restarting
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   agreement that the image has to stop floating and that callers need an override, with the tag value, the override key name and where the default lives all still undecided; Nikolai Berresford says he will look at what the sandbox repo actually publishes; it is settled that Dermot Callaghan got outputs from the old model after editing the model name and restarting; Dermot Callaghan got outputs from the old model after editing the model name and restarting


==============================================================================
# 2025-05-02 — 3 conversation(s), 21 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two merges landed this morning; six older PRs need clarity on blockers

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two merges landed this morning; six older PRs need clarity on blockers
    
    What it should get through:
      1. Confirm PR 656 and PR 659 merge readiness   [Emil Brandvold must raise this]
           - Emil explains the multimodal input fix scope
           - Konrad nods on test coverage
           - Both approved
      2. Unblock stale PR queue   [Gideon Halloway must raise this]
           - Gideon flags PR 632 batch-freq as critical blocker
           - Emil routes PR 643 response-object toward next sprint
           - Others parked pending architecture decisions
    
    On the agenda: Post-merge: PR 656 anthropic backend and PR 659 version bump; Stale PR status: PR 643, PR 652, PR 468, PR 632 blocking; CLI batch-freq work context (Gideon Halloway's PR 632)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 656 and PR 659 confirmed; stale PR triage complete; PR 632 escalated or re-prioritized
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Anthropic multimodal input fix and version bump details
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 656 and PR 659 merge readiness   *** MUST RAISE ***
      2. Unblock stale PR queue
      3. the comment you are writing, comment on Handover: Status Tracking, Cost Reporting & the Viewer Surface, has to say this in your own words: For the cost estimate in the cookbook I do not want a percentage I have to invert. I want misses as a plain int so I can multiply it by price per row and put a dollar figure in front of someone before they hit go.   *** MUST SETTLE (clue t1.r1.l_stats_2) ***
         must contain literally: misses
      4. leave a comment on the wiki page "Handover: Status Tracking, Cost Reporting & the Viewer Surface" — you questions or adds to the page, about handing Status tracking, cost reporting and the viewer surface to emil   *** MUST RAISE ***
      5. that your question about "comment on Handover: Status Tracking, Cost Reporting & the Viewer Surface" is now ON it, where the next person to read it will see it, rather than only said here
      6. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 656 and PR 659 merge readiness
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective on release readiness
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 656 and PR 659 merge readiness
      2. Unblock stale PR queue
    goal        Two merges landed this morning; six older PRs need clarity on blockers
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI batch update-freq context for parallel work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 656 and PR 659 merge readiness
      2. Unblock stale PR queue   *** MUST RAISE ***
    goal        Unblock stale PR queue
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 656 and PR 659 confirmed; stale PR triage complete; PR 632 escalated or re-prioritized


------------------------------------------------------------------------------
## #pipeline — 7 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work
    
    What it should get through:
      1. Anthropic multimodal request formatting fixed   [Emil Brandvold must raise this]
           - Emil walks through the formatter refactor
           - Dermot questions edge cases with structured output
           - Confirms existing tests cover the change
      2. Batch CLI update-freq and provider fixes are independent   [Gideon Halloway must raise this]
           - Gideon explains CLI polling interval issue
           - Emil confirms no shared state
           - Proceed in parallel
    
    On the agenda: PR 656 anthropic multimodal input formatter bug; Batch CLI update-freq fix scope (Gideon Halloway); Provider coverage and test plan
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 656 anthropic fix understood; Gideon Halloway proceeds with PR 632 CLI work independently; no follow-up multimodal bug ticket opened
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Root cause of anthropic backend multimodal input formatting bug
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Anthropic multimodal request formatting fixed   *** MUST RAISE ***
      2. Batch CLI update-freq and provider fixes are independent
    goal        Anthropic multimodal request formatting fixed
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Batch update-freq CLI fix parallel work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Anthropic multimodal request formatting fixed
      2. Batch CLI update-freq and provider fixes are independent   *** MUST RAISE ***
    goal        Batch CLI update-freq and provider fixes are independent
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Request-formatter domain knowledge
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Anthropic multimodal request formatting fixed
      2. Batch CLI update-freq and provider fixes are independent
    goal        Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 656 anthropic fix understood; Gideon Halloway proceeds with PR 632 CLI work independently; no follow-up multimodal bug ticket opened


------------------------------------------------------------------------------
## #releases — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.24 version bump merged; response object PR stalled 16 days

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.24 version bump merged; response object PR stalled 16 days
    
    What it should get through:
      1. v0.1.24 release approved   [Emil Brandvold must raise this]
           - Emil confirms bump only, no features
           - Konrad confirms nothing controversial
           - Dermot signs off changelog
      2. Response object PR (PR 643) path forward   [Emil Brandvold must raise this]
           - Emil presents blocking concern on PR 643
           - Konrad decides: land after 0.1.24 or hold for next sprint
           - Group aligns on timeline
    
    On the agenda: v0.1.24 version bump (PR 659) scope; Response object PR (PR 643) landability; Release notes and changelog review
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.24 approved; PR 643 response object scheduled for next sprint or unblocked with clear conditions
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Version bump details and changelog
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. v0.1.24 release approved   *** MUST RAISE ***
      2. Response object PR (PR 643) path forward   *** MUST RAISE ***
      3. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        v0.1.24 release approved
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder sign-off and strategic context
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. v0.1.24 release approved
      2. Response object PR (PR 643) path forward
    goal        v0.1.24 version bump merged; response object PR stalled 16 days
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. v0.1.24 release approved
      2. Response object PR (PR 643) path forward
    goal        v0.1.24 version bump merged; response object PR stalled 16 days
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.24 approved; PR 643 response object scheduled for next sprint or unblocked with clear conditions

