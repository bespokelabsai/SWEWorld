# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-01-03 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 18 PRs older than the era's median merge time; six of them from present team members need a decision to move or close

    Today is Friday 3 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 18 PRs older than the era's median merge time; six of them from present team members need a decision to move or close
    
    What it should get through:
      1. Separate PRs that are blocked on reviews from those awaiting author rewrites   [Dario Kestrel must raise this]
           - Dario flags that PR 78, PR 90, PR 228 have all been waiting since November/early December
           - Gideon notes PR 161 and PR 163 need viewer work but he hasn't had cycles
           - Konrad decides: PR 106 stays but can slip past this release
      2. Triage SimpleLLM refactor blockers vs. nice-to-haves in the stale pile   [Dario Kestrel must raise this]
           - Dario raises that PR 78 and PR 90 are about SimpleLLM folding and should unblock with Emil joining
           - Konrad asks if they can merge after Emil lands or need pre-rebase
           - Dario: we rebase them Monday, not waiting on content
    
    On the agenda: Which of the six stale PRs are still in scope for this era; What each one is blocked on and who can unblock it; Which ones can merge as-is and which need work
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear decision on which PRs merge next week (likely PR 78, PR 90, PR 228 after Emil joins Monday) and which get closed or bumped to 0.1.14. Gideon goes away knowing PR 161 and PR 163 are parked pending viewer refactor. Konrad confirms PR 106 scope for later.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

    On the table
      - Stratos Crunch plan: backend explosion incoming (Konrad Feltrin)
      - 0.1.13 release notes (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1185 function/class names and 151 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ownership of bulk-llm-inference and request processing; knows what PR 78 and PR 90 are blocking
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Separate PRs that are blocked on reviews from those awaiting author rewrites   *** MUST RAISE ***
      2. Triage SimpleLLM refactor blockers vs. nice-to-haves in the stale pile   *** MUST RAISE ***
      3. what "Stratos Crunch plan: backend explosion incoming" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "0.1.13 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Separate PRs that are blocked on reviews from those awaiting author rewrites
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. dataset viewer context; can unblock PR 161 and PR 163 if they need viewer feedback
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Separate PRs that are blocked on reviews from those awaiting author rewrites
      2. Triage SimpleLLM refactor blockers vs. nice-to-haves in the stale pile
    goal        18 PRs older than the era's median merge time; six of them from present team members need a decision to move or close
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. founding context on the curation examples; can decide if PR 106 is still in scope
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Separate PRs that are blocked on reviews from those awaiting author rewrites
      2. Triage SimpleLLM refactor blockers vs. nice-to-haves in the stale pile
    goal        18 PRs older than the era's median merge time; six of them from present team members need a decision to move or close
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear decision on which PRs merge next week (likely PR 78, PR 90, PR 228 after Emil joins Monday) and which get closed or bumped to 0.1.14. Gideon goes away knowing PR 161 and PR 163 are parked pending viewer refactor. Konrad confirms PR 106 scope for later.


==============================================================================
# 2025-01-06 — 4 conversation(s), 47 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Nikolai landed two formatting/tooling PRs; Dario Kestrel requested changes on docstring PR; need to settle the migration path

    Today is Monday 6 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai landed two formatting/tooling PRs; Dario Kestrel requested changes on docstring PR; need to settle the migration path
    
    What it should get through:
      1. Approve or reject ruff migration and pre-commit setup   [Nikolai Berresford must raise this]
           - Nikolai describes the Ruff migration benefits (speed, unified tooling)
           - Dario pushes back on tool churn mid-release cycle
           - Dermot breaks the tie: acceptable if it doesn't block 0.1.14 cut
      2. Resolve docstring standardization and address review feedback   [Dario Kestrel must raise this]
           - Dario outlines the CHANGES_REQUESTED on PR 308
           - Nikolai or Dario Kestrel clarifies scope (batch processors only, or full codebase?)
           - Decision: land it or defer past 0.1.14
    
    On the agenda: PR 302 and PR 303: switch from black to Ruff and pre-commit hooks; PR 308: docstring standardization to Google style
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Nikolai knows whether to merge PR 302/#303 today or wait; PR 308 either gets approval or a clear deferral path
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 146 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1136 function/class names and 137 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Ruff formatter migration (replace black); pre-commit hook setup
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Approve or reject ruff migration and pre-commit setup   *** MUST RAISE ***
      2. Resolve docstring standardization and address review feedback
    goal        Approve or reject ruff migration and pre-commit setup
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Experience with the existing black/formatting workflow; feedback on docstring changes in PR 308
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve or reject ruff migration and pre-commit setup
      2. Resolve docstring standardization and address review feedback   *** MUST RAISE ***
    goal        Resolve docstring standardization and address review feedback
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering perspective on tool churn and CI stability
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Approve or reject ruff migration and pre-commit setup
      2. Resolve docstring standardization and address review feedback
    goal        Nikolai landed two formatting/tooling PRs; Dario Kestrel requested changes on docstring PR; need to settle the migration path
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Nikolai knows whether to merge PR 302/#303 today or wait; PR 308 either gets approval or a clear deferral path


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Ilse landed 8 commits on vLLM examples/docs overnight; Dario writing WS-016 design doc today; Dermot hardening the release

    Today is Monday 6 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Ilse landed 8 commits on vLLM examples/docs overnight; Dario writing WS-016 design doc today; Dermot hardening the release
    
    What it should get through:
      1. Land Ilse Vandekerckhove's vLLM examples and integrate into main README   [Dario Kestrel must raise this]
           - Ilse or Dario Kestrel summarizes what landed overnight (offline processor, examples, local model docs)
           - Dario or Dermot Callaghan checks if tests pass and docs are complete
           - Quick approval or request for fixes before main merge
      2. Settle WS-016 design doc scope and timeline   [Dario Kestrel must raise this]
           - Dario describes what the design doc covers and who it targets
           - Dermot flags any conflicts with 0.1.14 hardening
           - Decision: publish today or refine over the weekend
      3. Clarify what README polish lands today vs. defers   [Dermot Callaghan must raise this]
           - Ilse or Dario Kestrel lists the README commits (table of contents, add examples, add citation)
           - Dermot gates on 0.1.14 release readiness
           - Defer non-critical polish or fast-track if it's simple
    
    On the agenda: vLLM examples and docs landing in main; README and table of contents updates; WS-016 design doc scope and Jan 7 kickoff
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: vLLM examples integrated, WS-016 design doc clarity, and README polish either shipped or deferred past the release
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 146 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1136 function/class names and 137 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Ownership of the examples-cookbooks service; vision for the design doc covering the new workstream
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land Ilse Vandekerckhove's vLLM examples and integrate into main README   *** MUST RAISE ***
      2. Settle WS-016 design doc scope and timeline   *** MUST RAISE ***
      3. Clarify what README polish lands today vs. defers
      4. that the doc "WS-016 design: Examples & Reasoning-Dataset Cookbooks" is done, and where the others can find it   *** MUST RAISE ***
    goal        Land Ilse Vandekerckhove's vLLM examples and integrate into main README
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release coordination perspective; knows which README/doc changes are blocking 0.1.14
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land Ilse Vandekerckhove's vLLM examples and integrate into main README
      2. Settle WS-016 design doc scope and timeline
      3. Clarify what README polish lands today vs. defers   *** MUST RAISE ***
      4. that the doc "WS-014 design: Release Engineering, CI & Test Suite" is done, and where the others can find it   *** MUST RAISE ***
    goal        Clarify what README polish lands today vs. defers
    available   around today

### 4. How it should land

    lands as  partial
    leaving   vLLM examples integrated, WS-016 design doc clarity, and README polish either shipped or deferred past the release


------------------------------------------------------------------------------
## #engineering — 15 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 10 commits landed over the weekend; 2 major merges (PR 299, PR 306) this morning; 6 new PRs opened; team needs to sync on priorities

    Today is Monday 6 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 10 commits landed over the weekend; 2 major merges (PR 299, PR 306) this morning; 6 new PRs opened; team needs to sync on priorities
    
    What it should get through:
      1. Acknowledge overnight work and unblock the week   [Dario Kestrel must raise this]
           - Dario or Konrad Feltrin recaps PR 306 (Merge dev into main) and PR 243 (Anthropic batch refactor)
           - Team confirms main is stable and ready for 0.1.14 branch
           - Identify any hotfixes needed before release cut
      2. Clarify vLLM integration and next steps   [Ilse Vandekerckhove must raise this]
           - Ilse summarizes the 8 commits (offline processor, examples, tests, docs, dependency)
           - Dario or Dermot Callaghan flags any missing coverage or edge cases
           - Decide: merge to main today or stage for 0.1.14 specifically
      3. Settle tooling and standardization path for the release   [Dermot Callaghan must raise this]
           - Nikolai describes PR 302/#303 (Ruff migration, pre-commit)
           - Dario notes the CHANGES_REQUESTED on PR 308 (docstring refactor)
           - Dermot gates on 0.1.14: all three parallel, or defer some to 0.1.15
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will write Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing — Setup notes and access checklist for Emil Brandvold joining the team.
    
    On the agenda: Overnight merges and what's unblocked; vLLM local inference status; Ruff and docstring standardization; 0.1.14 release readiness and timeline; Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team aligns on release timeline, priorities (vLLM, tooling, docs), and who owns what through Jan 7
    
    Do NOT wrap before about 10 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 146 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1136 function/class names and 137 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on overnight merges (PR 306: Merge dev into main); what's unblocked for the week
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Acknowledge overnight work and unblock the week   *** MUST RAISE ***
      2. Clarify vLLM integration and next steps
      3. Settle tooling and standardization path for the release
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    goal        Acknowledge overnight work and unblock the week
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Status on 0.1.14 release and the hardening workstream; what's blocking
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Acknowledge overnight work and unblock the week
      2. Clarify vLLM integration and next steps
      3. Settle tooling and standardization path for the release   *** MUST RAISE ***
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    goal        Settle tooling and standardization path for the release
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Ruff migration PRs and their status; what lands in 0.1.14 vs. 0.1.15
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Acknowledge overnight work and unblock the week
      2. Clarify vLLM integration and next steps
      3. Settle tooling and standardization path for the release
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    goal        10 commits landed over the weekend; 2 major merges (PR 299, PR 306) this morning; 6 new PRs opened; team needs to sync on priorities
    available   around today

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). 8 commits landing overnight on vLLM; status of her ongoing work
    owns        local-offline-inference
    agenda
      1. Acknowledge overnight work and unblock the week
      2. Clarify vLLM integration and next steps   *** MUST RAISE ***
      3. Settle tooling and standardization path for the release
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    goal        Clarify vLLM integration and next steps
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective on sprint goals and team direction
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Acknowledge overnight work and unblock the week
      2. Clarify vLLM integration and next steps
      3. Settle tooling and standardization path for the release
      4. write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing   *** MUST RAISE ***
      5. that the doc "Onboarding: emil, Core Platform Engineer for Request Processing" is done, and where the others can find it   *** MUST RAISE ***
      6. that the doc "Onboarding: ilse, vLLM local inference contributor" is done, and where the others can find it   *** MUST RAISE ***
      7. that "Weekly update: week of Dec 30" has gone out, and what you asked in it   *** MUST RAISE ***
      8. that "Welcome emil to the team" has gone out, and what you asked in it   *** MUST RAISE ***
      9. that "Welcome ilse to the team" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team aligns on release timeline, priorities (vLLM, tooling, docs), and who owns what through Jan 7


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Ilse landed vLLM offline processor code; Millrow Refactor Bot refactored docstrings and token counting; Dario Kestrel requested changes on PR 308

    Today is Monday 6 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Ilse landed vLLM offline processor code; Millrow Refactor Bot refactored docstrings and token counting; Dario Kestrel requested changes on PR 308
    
    What it should get through:
      1. Validate vLLM offline processor fits the provider-integrations pattern   [Ilse Vandekerckhove must raise this]
           - Ilse walks through the offline request processor implementation
           - Dario or Dermot Callaghan checks for conflicts with existing batch/async patterns
           - Approve or request refactoring before merging to main
      2. Clear blockers on provider-integrations docstring and token-counting work   [Dario Kestrel must raise this]
           - Dario or Dermot Callaghan reviews PR 308 (docstring refactoring) and the token-counting PR (PR 307)
           - Resolve CHANGES_REQUESTED and decide if they land in 0.1.14
           - Fast-track or defer based on release timeline
    
    On the agenda: vLLM offline processor architecture and integration; Provider-integrations docstring refactoring and batch processor changes; Token counting unification across processors
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: vLLM processor approved for main; docstring/token-counting work either cleared or deferred; provider-integrations ready for release
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 146 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1136 function/class names and 137 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). vLLM offline processor implementation and integration; edge cases and dependencies discovered
    owns        local-offline-inference
    agenda
      1. Validate vLLM offline processor fits the provider-integrations pattern   *** MUST RAISE ***
      2. Clear blockers on provider-integrations docstring and token-counting work
    goal        Validate vLLM offline processor fits the provider-integrations pattern
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Deep context on the provider integration layer; knows what the batch processor refactors need
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate vLLM offline processor fits the provider-integrations pattern
      2. Clear blockers on provider-integrations docstring and token-counting work   *** MUST RAISE ***
    goal        Clear blockers on provider-integrations docstring and token-counting work
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering view on provider integrations; knows what's safe to land in 0.1.14
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate vLLM offline processor fits the provider-integrations pattern
      2. Clear blockers on provider-integrations docstring and token-counting work
    goal        Ilse landed vLLM offline processor code; Millrow Refactor Bot refactored docstrings and token counting; Dario Kestrel requested changes on PR 308
    available   around today

### 4. How it should land

    lands as  partial
    leaving   vLLM processor approved for main; docstring/token-counting work either cleared or deferred; provider-integrations ready for release


==============================================================================
# 2025-01-07 — 4 conversation(s), 53 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.14 shipped overnight; release notes are due; next cycle's gating criteria need to land today

    Today is Tuesday 7 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.14 shipped overnight; release notes are due; next cycle's gating criteria need to land today
    
    What it should get through:
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged   [Emil Brandvold must raise this]
           - Emil posts draft notes; Dermot Callaghan flags coverage gaps; Dario Kestrel asks if README references are in yet
           - Konrad notes docstrings are the big user-facing win; notes updated to lead with that
           - Emil ships final version and posts announce; Nikolai Berresford confirms PR 318 epic reference is in
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist   [Dermot Callaghan must raise this]
           - Dermot explains why test file layout is now a blocker; shows which coverage gaps matter most
           - Emil says PR 320 integration test setup is in; points to PR 318 as the tracking epic
           - Dario agrees: nothing ships until we have baseline coverage numbers and at least one integration test passing
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green   [Nikolai Berresford must raise this]
           - Nikolai proposes gating criteria; Dermot Callaghan says it's too strict, we need to ship the cache-dir feature
           - Emil volunteers to write the integration test harness; Konrad Feltrin agrees that's the bottleneck
    
    On the agenda: Release notes narrative: what shipped, why it matters to users; Coverage and test suite state: are we ready to release faster?; Next release (v0.1.15) gating criteria and timeline
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.14 release notes are final and shipped; team has agreed that v0.1.15 will not ship until PR 318 is at least partially green and coverage baseline is set
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 151 changes merged to date

    On the table
      - Release notes: v0.1.14 (Emil Brandvold)
      - 0.1.13 release notes (Konrad Feltrin)
      - Stratos Crunch plan: backend explosion incoming (Konrad Feltrin)
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - Weekly sync notes: week of Dec 30 — provider integrations (Dario Kestrel)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1131 function/class names and 135 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. clarity on what shipped and why: docstrings, cache dir config, special tokens fix, test movement
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged   *** MUST RAISE ***
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green
      4. that the doc "Release notes: v0.1.14" is done, and where the others can find it   *** MUST RAISE ***
      5. that "v0.1.14 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      6. what "0.1.13 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Stratos Crunch plan: backend explosion incoming" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Emil finishes and ships release notes; team agrees they match the five PRs that merged
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. release sequencing: we need coverage and CI hardened before the next cut
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist   *** MUST RAISE ***
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green
      4. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly sync notes: week of Dec 30 — provider integrations" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Team agrees v0.1.14 is the last release until coverage passes and integration tests exist
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. big-picture: README and onboarding are due this week, release notes should explain how to get started
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green
    goal        v0.1.14 shipped overnight; release notes are due; next cycle's gating criteria need to land today
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. historical context: what broke the last two releases, what we should have caught
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green
    goal        v0.1.14 shipped overnight; release notes are due; next cycle's gating criteria need to land today
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. integration test status: PR 318 epic is opened, we can point to it as next milestone
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Emil finishes and ships release notes; team agrees they match the five PRs that merged
      2. Team agrees v0.1.14 is the last release until coverage passes and integration tests exist
      3. v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green   *** MUST RAISE ***
    goal        v0.1.15 gating: no feature lands until coverage threshold passes and PR 318 integration tests are green
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.14 release notes are final and shipped; team has agreed that v0.1.15 will not ship until PR 318 is at least partially green and coverage baseline is set


------------------------------------------------------------------------------
## #code-review — 14 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 9 PRs opened today; 15 PRs older than era median; PR 317 is blocking ws-012 and ws-015; factory refactor needs eyes before more code lands on top of it

    Today is Tuesday 7 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 9 PRs opened today; 15 PRs older than era median; PR 317 is blocking ws-012 and ws-015; factory refactor needs eyes before more code lands on top of it
    
    What it should get through:
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward   [Emil Brandvold must raise this]
           - Emil explains factory pattern, why SimpleLLM can't work without it, and why backend=None was the original bug
           - Dario asks if this is user-visible; Emil Brandvold says no, it's internal config plumbing
           - Dermot flags that docstring pass may have created the import cycle; team agrees to check test_db_schema.py imports
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet   [Emil Brandvold must raise this]
           - Emil posts PR 320: basic setup for running against a real backend
           - Nikolai asks if it covers batch retries (PR 311); Emil Brandvold says no, that's phase 2
           - Dario approves; points to PR 318 as the epic that should own the rest
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized   [Konrad Feltrin must raise this]
           - Konrad says PR 106 (negotiation example) has been waiting 54 days; needs to know if factory pattern changes how examples are written
           - Emil says examples don't change; they still call LLM(...); factory is internal
           - Dario volunteers to review PR 106 as part of ws-016 cleanup this week
    
    On the agenda: Review PR 317: Factory pattern, backend auto-detect, env var base URL; Review PR 320: Integration test setup, what it covers and what's still missing; Unblock PR 106 and other stale PRs: what changed in the API?
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 317 and PR 320 have clear approval paths or blocking issues; PR 106 review is scheduled; team knows which changes are user-visible vs. internal
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 151 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1131 function/class names and 135 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the factory pattern fix and backend auto-detection; explains why SimpleLLM can't coexist with the new config path
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward   *** MUST RAISE ***
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet   *** MUST RAISE ***
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized
      4. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 317 approved or issues clearly listed; factory pattern is the shape going forward
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. test file movement is done; docstring pass is done; can now see where circular imports are coming from
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized
    goal        9 PRs opened today; 15 PRs older than era median; PR 317 is blocking ws-012 and ws-015; factory refactor needs eyes before more code lands on top of it
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. perspective on whether factory pattern is user-facing or internal-only; README examples should reflect the right API
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized
    goal        9 PRs opened today; 15 PRs older than era median; PR 317 is blocking ws-012 and ws-015; factory refactor needs eyes before more code lands on top of it
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. has blocked PR PR 106 for 54 days waiting for examples; factory pattern might unblock it
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized   *** MUST RAISE ***
    goal        Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. batch retry error handling; can see if circular imports affect batch processor imports
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 317 approved or issues clearly listed; factory pattern is the shape going forward
      2. PR 320 integration test setup is approved; team knows what's tested and what's not yet
      3. Team commits to reviewing stale PRs in priority order; PR 106 unblocked or deprioritized
    goal        9 PRs opened today; 15 PRs older than era median; PR 317 is blocking ws-012 and ws-015; factory refactor needs eyes before more code lands on top of it
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 317 and PR 320 have clear approval paths or blocking issues; PR 106 review is scheduled; team knows which changes are user-visible vs. internal


------------------------------------------------------------------------------
## #engineering — 16 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Five PRs merged today; three workstreams kicking off or mid-flight; factory refactor is blocking multiple parallel streams

    Today is Tuesday 7 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five PRs merged today; three workstreams kicking off or mid-flight; factory refactor is blocking multiple parallel streams
    
    What it should get through:
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block   [Emil Brandvold must raise this]
           - Emil walks through why backend=None was broken and factory pattern fixes it
           - Ilse asks if vLLM registration changes; Emil Brandvold says no, still the same entry point
           - Dario confirms: public API is untouched, users call LLM(...) as always
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set   [Dermot Callaghan must raise this]
           - Dermot: ws-014 (coverage) starts now, blocker for v0.1.15; won't ship until PR 318 is partly green
           - Emil: ws-015 (throughput) can run in parallel, depends on factory pattern landing but not on coverage
           - Dario: ws-016 (docs) is independent, can write CONTRIBUTING.md and README examples in parallel
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today   [Nikolai Berresford must raise this]
           - Nikolai lists the blockers: PR 318 integration test coverage at least 2 passing, coverage threshold minimum 70%
           - Dermot says 70% is achievable within two weeks if we focus
           - Emil agrees; factory pattern and cache-dir land first, then coverage work, then v0.1.15
    
    On the agenda: Factory pattern integration: is PR 317 ready to land, and what does it unblock?; Three workstreams launching this week: ws-014 (coverage), ws-015 (throughput), ws-016 (docs and examples); What we're NOT shipping in v0.1.15: gating criteria and blockers
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Three workstreams are explicitly scoped and sequenced; factory pattern (PR 317) has clear approval path; v0.1.15 gating is locked in
    
    Do NOT wrap before about 11 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 151 changes merged to date

    On the table
      - Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing (Konrad Feltrin)
      - WS-014 design: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - WS-016 design: Examples & Reasoning-Dataset Cookbooks (Dario Kestrel)
      - Onboarding: Ilse Vandekerckhove, vLLM local inference contributor (Konrad Feltrin)
      - Stratos Crunch plan: backend explosion incoming (Konrad Feltrin)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1131 function/class names and 135 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. factory pattern integration is done; backend auto-detect fix is in; PR 320 sets up the integration test harness
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block   *** MUST RAISE ***
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today
      4. what "Onboarding: emil, Core Platform Engineer for Request Processing" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. test file movement (PR 323) is merged; docstring pass is done; can now measure coverage gaps
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set   *** MUST RAISE ***
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today
      4. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "WS-016 design: Examples & Reasoning-Dataset Cookbooks" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Onboarding: ilse, vLLM local inference contributor" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. README and CONTRIBUTING.md are due this week; onboarding docs are fresh; can now write clear examples
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today
    goal        Five PRs merged today; three workstreams kicking off or mid-flight; factory refactor is blocking multiple parallel streams
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. batch retry error handling and schema validation are in; PR 318 epic is open
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today   *** MUST RAISE ***
      4. what "Stratos Crunch plan: backend explosion incoming" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today
    available   around today

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). vLLM integration is nearly done; litellm merge is in; merge conflicts are resolved
    owns        local-offline-inference
    agenda
      1. PR 317 factory pattern is clear; team knows what SimpleLLM changes enable and what they block
      2. ws-014, ws-015, ws-016 have clear scope and don't block each other; launch sequence is set
      3. v0.1.15 will not ship with vague CI or coverage; gating criteria locked in today
    goal        Five PRs merged today; three workstreams kicking off or mid-flight; factory refactor is blocking multiple parallel streams
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three workstreams are explicitly scoped and sequenced; factory pattern (PR 317) has clear approval path; v0.1.15 gating is locked in


------------------------------------------------------------------------------
## #pipeline — 11 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: PR 317 factory pattern is blocking ws-015; PR 298 vLLM is blocked for 2 days; throughput hardening workstream is kicking off

    Today is Tuesday 7 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 317 factory pattern is blocking ws-015; PR 298 vLLM is blocked for 2 days; throughput hardening workstream is kicking off
    
    What it should get through:
      1. PR 317 factory pattern fix is clear; backend auto-detect will use correct config going forward   [Emil Brandvold must raise this]
           - Emil: backend=None was being passed to wrong constructor path, factory pattern fixes it
           - Dario: this was causing silent failures in provider auto-detection, now it's explicit
           - Dermot: confirms this unblocks concurrency tuning because config path is now predictable
      2. ws-015 has explicit scope: file handle cleanup, config stability, concurrency targets, and measurement plan   [Emil Brandvold must raise this]
           - Emil proposes: start with file handle cleanup (safety), then concurrency tuning (throughput)
           - Dermot: what's the target concurrency for online requests? Emil: match provider limits, start at 20 parallel
           - Dario: how do we measure success? Emil: latency per request, tokens per second, cost per 1M tokens
    
    On the agenda: Backend auto-detect fix (PR 317) and why it matters for throughput; vLLM local inference (PR 298): merge conflict resolution and litellm integration; ws-015 scope: file handle cleanup, config paths, concurrency tuning, and measurement plan
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 317 factory pattern is clear; vLLM merge is unblocked; ws-015 has explicit scope and success metrics
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 151 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1131 function/class names and 135 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. factory pattern resolves backend auto-detect config bug; explains why file handles need to be closed safely; PR 320 sets up the first integration test
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 317 factory pattern fix is clear; backend auto-detect will use correct config going forward   *** MUST RAISE ***
      2. ws-015 has explicit scope: file handle cleanup, config stability, concurrency targets, and measurement plan   *** MUST RAISE ***
      3. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        PR 317 factory pattern fix is clear; backend auto-detect will use correct config going forward
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. test file movement is done; docstring pass is in; can now measure where throughput is actually being lost
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 317 factory pattern fix is clear; backend auto-detect will use correct config going forward
      2. ws-015 has explicit scope: file handle cleanup, config stability, concurrency targets, and measurement plan
    goal        PR 317 factory pattern is blocking ws-015; PR 298 vLLM is blocked for 2 days; throughput hardening workstream is kicking off
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. has context on request lifecycle and where retries are actually happening; PR 295 batch retries are blocked and need unblocking
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 317 factory pattern fix is clear; backend auto-detect will use correct config going forward
      2. ws-015 has explicit scope: file handle cleanup, config stability, concurrency targets, and measurement plan
    goal        PR 317 factory pattern is blocking ws-015; PR 298 vLLM is blocked for 2 days; throughput hardening workstream is kicking off
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 317 factory pattern is clear; vLLM merge is unblocked; ws-015 has explicit scope and success metrics


==============================================================================
# 2025-01-08 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Week of heavy CI/release work landed; team needs to see what held and what's still pending before the sprint focus shifts

    Today is Wednesday 8 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Week of heavy CI/release work landed; team needs to see what held and what's still pending before the sprint focus shifts
    
    What it should get through:
      1. Confirm v0.1.14 release is stable and no hotfixes needed   [Dermot Callaghan must raise this]
           - Dermot raises any last-minute issues from the cutover
           - Emil and Dario confirm their subsystems are stable
           - Nikolai flags if Ruff migration broke anything downstream
      2. Settle Ruff migration: is it final or do we roll back   [Nikolai Berresford must raise this]
           - Nikolai walks through the pre-commit hook changes
           - Dario or Emil raises any failures from test runs
           - Group decides whether to keep or revert before next cutover
      3. Local vLLM ready for next release or needs a soak period   [Ilse Vandekerckhove must raise this]
           - Ilse confirms cuda memory release is solid
           - Dermot or Emil flag any integration concerns
           - Group agrees on next-release timeline for local-offline-inference
    
    On the agenda: v0.1.14 release wrapped — what stuck during the cutover; Ruff migration landed; black is gone — side effects or gaps; Local vLLM in main; stability check before next release; Three stale PRs still waiting; what's blocking them
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team has a clear picture of release health, Ruff is decided, and local vLLM's release timeline is set. Stale PRs either get a nudge or are deprioritized.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 156 changes merged to date

    On the table
      - Weekly sync notes: week of Jan 6 — v0.1.14 shipped (Dermot Callaghan)
      - notes-2025-01-06 (Dermot Callaghan)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1095 function/class names and 123 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Weekly sync notes covering v0.1.14 release, week's work summary, and what's next
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm v0.1.14 release is stable and no hotfixes needed   *** MUST RAISE ***
      2. Settle Ruff migration: is it final or do we roll back
      3. Local vLLM ready for next release or needs a soak period
      4. that the doc "Weekly sync notes: week of Jan 6 — v0.1.14 shipped" is done, and where the others can find it   *** MUST RAISE ***
      5. what "Weekly sync notes: week of Jan 6 — v0.1.14 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Release notes: v0.1.14" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm v0.1.14 release is stable and no hotfixes needed
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release notes context; state of SimpleLLM refactor landing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm v0.1.14 release is stable and no hotfixes needed
      2. Settle Ruff migration: is it final or do we roll back
      3. Local vLLM ready for next release or needs a soak period
    goal        Week of heavy CI/release work landed; team needs to see what held and what's still pending before the sprint focus shifts
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Poetry.lock fix and its implications for CI stability
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm v0.1.14 release is stable and no hotfixes needed
      2. Settle Ruff migration: is it final or do we roll back
      3. Local vLLM ready for next release or needs a soak period
    goal        Week of heavy CI/release work landed; team needs to see what held and what's still pending before the sprint focus shifts
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Ruff migration work; pre-commit hook simplifications
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm v0.1.14 release is stable and no hotfixes needed
      2. Settle Ruff migration: is it final or do we roll back   *** MUST RAISE ***
      3. Local vLLM ready for next release or needs a soak period
    goal        Settle Ruff migration: is it final or do we roll back
    available   around today

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). Local vLLM feature now in main; cuda memory release fix
    owns        local-offline-inference
    agenda
      1. Confirm v0.1.14 release is stable and no hotfixes needed
      2. Settle Ruff migration: is it final or do we roll back
      3. Local vLLM ready for next release or needs a soak period   *** MUST RAISE ***
    goal        Local vLLM ready for next release or needs a soak period
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team has a clear picture of release health, Ruff is decided, and local vLLM's release timeline is set. Stale PRs either get a nudge or are deprioritized.


------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened today need eyes; PR 324 is Millrow Refactor Bot's cache disable, PR 326 is dependency drift, PR 329 is vLLM loosening

    Today is Wednesday 8 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened today need eyes; PR 324 is Millrow Refactor Bot's cache disable, PR 326 is dependency drift, PR 329 is vLLM loosening
    
    What it should get through:
      1. PR 326 approved and merged — poetry.lock drift stopped   [Dario Kestrel must raise this]
           - Dario explains the drift and why it matters now
           - Dermot or Emil spot-checks the lock changes
           - Quick approval and merge
      2. PR 329 approved if local-offline-inference stays unbroken   [Dermot Callaghan must raise this]
           - Dermot walks through the version range rationale
           - Emil or Ilse confirms local vLLM still runs
           - Approval contingent on integration confidence
      3. PR 324 cache disabling ready or needs iteration before next push   [Emil Brandvold must raise this]
           - Emil or Millrow Refactor Bot presents the CURATOR_DISABLE_CACHE implementation
           - Dario or Dermot raises any config or integration concerns
           - Decision to merge or iterate
    
    On the agenda: PR 326: poetry.lock update rationale; PR 329: VLLM version relax scope and safety; PR 324: Cache disabling via env var — is it ready or needs rework
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 326 and PR 329 merge; PR 324 either merges or gets a clear rework backlog.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 156 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1095 function/class names and 123 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Poetry.lock update reasoning and any implications for install stability
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 326 approved and merged — poetry.lock drift stopped   *** MUST RAISE ***
      2. PR 329 approved if local-offline-inference stays unbroken
      3. PR 324 cache disabling ready or needs iteration before next push
    goal        PR 326 approved and merged — poetry.lock drift stopped
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. VLLM version relax context — why loosening it now is safe
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 326 approved and merged — poetry.lock drift stopped
      2. PR 329 approved if local-offline-inference stays unbroken   *** MUST RAISE ***
      3. PR 324 cache disabling ready or needs iteration before next push
    goal        PR 329 approved if local-offline-inference stays unbroken
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. SimpleLLM refactor state and what PR PR 324 (cache disabling) unblocks
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 326 approved and merged — poetry.lock drift stopped
      2. PR 329 approved if local-offline-inference stays unbroken
      3. PR 324 cache disabling ready or needs iteration before next push   *** MUST RAISE ***
    goal        PR 324 cache disabling ready or needs iteration before next push
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 326 and PR 329 merge; PR 324 either merges or gets a clear rework backlog.


------------------------------------------------------------------------------
## #releases — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Two merges today touch release-blocking areas; team needs to decide if next cut happens soon or waits

    Today is Wednesday 8 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two merges today touch release-blocking areas; team needs to decide if next cut happens soon or waits
    
    What it should get through:
      1. v0.1.14 postmortem settles any last-minute issues   [Dermot Callaghan must raise this]
           - Dermot raises any cutover friction
           - Emil, Dario, Nikolai confirm no hidden failures
           - Decision: safe to cut 0.1.15 or hold
      2. 0.1.15 timeline decided based on SimpleLLM and Ruff stability   [Dermot Callaghan must raise this]
           - Emil signals SimpleLLM refactor stability
           - Nikolai confirms Ruff CI is solid
           - Group chooses: ship this week or wait
      3. Ruff in CI is non-blocking or needs a guard for next release   [Nikolai Berresford must raise this]
           - Nikolai flags any CI flakes from Ruff
           - Dario or Emil spots any test failures tied to linting
           - Decision to gate or permit next cut
    
    On the agenda: v0.1.14 postmortem: what failed or was close; Next release timing: 0.1.15 this week or soak into next week; Ruff migration stability: ready for release CI or needs buffer
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.15 release timeline is set; Ruff CI is either cleared for release or flagged as needing a week to stabilize. Dependency stability confirmed.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 156 changes merged to date

    On the table
      - notes-2025-01-06 (Dermot Callaghan)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1095 function/class names and 123 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release readiness check; v0.1.14 postmortem; next version timeline
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. v0.1.14 postmortem settles any last-minute issues   *** MUST RAISE ***
      2. 0.1.15 timeline decided based on SimpleLLM and Ruff stability   *** MUST RAISE ***
      3. Ruff in CI is non-blocking or needs a guard for next release
      4. what "Weekly sync notes: week of Jan 6 — v0.1.14 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        v0.1.14 postmortem settles any last-minute issues
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Dependency stability and whether poetry.lock alone was the issue
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. v0.1.14 postmortem settles any last-minute issues
      2. 0.1.15 timeline decided based on SimpleLLM and Ruff stability
      3. Ruff in CI is non-blocking or needs a guard for next release
    goal        Two merges today touch release-blocking areas; team needs to decide if next cut happens soon or waits
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. SimpleLLM refactor landing state and any breaking-change implications for next release
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. v0.1.14 postmortem settles any last-minute issues
      2. 0.1.15 timeline decided based on SimpleLLM and Ruff stability
      3. Ruff in CI is non-blocking or needs a guard for next release
    goal        Two merges today touch release-blocking areas; team needs to decide if next cut happens soon or waits
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Ruff linter in CI; potential test or build issues from the migration
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. v0.1.14 postmortem settles any last-minute issues
      2. 0.1.15 timeline decided based on SimpleLLM and Ruff stability
      3. Ruff in CI is non-blocking or needs a guard for next release   *** MUST RAISE ***
    goal        Ruff in CI is non-blocking or needs a guard for next release
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.15 release timeline is set; Ruff CI is either cleared for release or flagged as needing a week to stabilize. Dependency stability confirmed.


==============================================================================
# 2025-01-09 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs merged today, one open with feedback; provider and batch work landing

    Today is Thursday 9 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs merged today, one open with feedback; provider and batch work landing
    
    What it should get through:
      1. Merge PR 334 test overload   [Emil Brandvold must raise this]
           - Emil Brandvold describes overloading backends in integration tests
           - Dermot Callaghan asks about GPU mocking on CI
           - Emil Brandvold confirms mock strategy, ready to merge
      2. Confirm PR 330 circular import   [Petar Kovalenko must raise this]
           - Petar Kovalenko walks through the import fix
           - Dermot Callaghan notes approval already given
           - group agrees it's safe
    
    On the agenda: PR 334 test overload status; PR 330 circular import verification; batch/provider integration readiness
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 334 merges today; PR 330 already approved and merged; batch/provider import cleanup complete
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 159 changes merged to date

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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1054 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Factory pattern refactor, lazy imports, integration test overhaul
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Merge PR 334 test overload   *** MUST RAISE ***
      2. Confirm PR 330 circular import
      3. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge PR 334 test overload
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. CI and linting perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Merge PR 334 test overload
      2. Confirm PR 330 circular import
    goal        Two PRs merged today, one open with feedback; provider and batch work landing
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. circular import fix and batch processor knowledge
    owns        (nothing specific)
    agenda
      1. Merge PR 334 test overload
      2. Confirm PR 330 circular import   *** MUST RAISE ***
    goal        Confirm PR 330 circular import
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 334 merges today; PR 330 already approved and merged; batch/provider import cleanup complete


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three PRs merged today, factory refactor and test overhaul complete, provider work stable

    Today is Thursday 9 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today, factory refactor and test overhaul complete, provider work stable
    
    What it should get through:
      1. Factory pattern refactor settled   [Emil Brandvold must raise this]
           - Emil Brandvold summarizes factory, env var, backend init fixes
           - Dario Kestrel asks about config backward compat
           - Emil Brandvold confirms no breaking changes for users
      2. Integration test strategy clear   [Emil Brandvold must raise this]
           - Emil Brandvold explains test overload across backends
           - Dermot Callaghan notes GPU mocking is critical for CI
           - group agrees coverage baseline
      3. Release blockers identified   [Dermot Callaghan must raise this]
           - Dermot Callaghan lists coverage gaps and ruff work
           - Emil Brandvold notes lazy import PR close to done
           - Dario Kestrel mentions no request processing blockers
    
    On the agenda: What landed: PR 317, PR 320, PR 330; In flight: PR 334, lazy import work; What's blocking next release
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team clear on what shipped; next release (v0.1.15) blockers known; factory refactor considered stable
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 159 changes merged to date

    On the table
      - Weekly sync notes: week of Jan 6 — v0.1.14 shipped (Dermot Callaghan)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1054 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. factory pattern, lazy loading, config fixes, integration test strategy
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Factory pattern refactor settled   *** MUST RAISE ***
      2. Integration test strategy clear   *** MUST RAISE ***
      3. Release blockers identified
      4. what "Weekly sync notes: week of Jan 6 — v0.1.14 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Factory pattern refactor settled
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. CI/test perspective; release readiness view
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Factory pattern refactor settled
      2. Integration test strategy clear
      3. Release blockers identified   *** MUST RAISE ***
    goal        Release blockers identified
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request processing context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Factory pattern refactor settled
      2. Integration test strategy clear
      3. Release blockers identified
    goal        Three PRs merged today, factory refactor and test overhaul complete, provider work stable
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. batch processor details
    owns        (nothing specific)
    agenda
      1. Factory pattern refactor settled
      2. Integration test strategy clear
      3. Release blockers identified
    goal        Three PRs merged today, factory refactor and test overhaul complete, provider work stable
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team clear on what shipped; next release (v0.1.15) blockers known; factory refactor considered stable


------------------------------------------------------------------------------
## #pipeline — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active

    Today is Thursday 9 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active
    
    What it should get through:
      1. Config changes don't break online throughput   [Emil Brandvold must raise this]
           - Emil Brandvold walks through factory pattern and config precedence
           - Dario Kestrel asks about env var defaults
           - Emil Brandvold confirms backward compat, no breaking changes
      2. Integration tests cover all backends   [Emil Brandvold must raise this]
           - Emil Brandvold describes PR 334 test overload approach
           - Dermot Callaghan questions GPU mocking strategy
           - Petar Kovalenko notes batch processor state
      3. Lazy imports don't degrade startup   [Emil Brandvold must raise this]
           - Emil Brandvold outlines what's lazy loaded and when
           - Ilse Vandekerckhove confirms offline backends unaffected
           - group satisfied with minimal import overhead
    
    On the agenda: Lazy import impact on startup; Config changes in online requests; Integration test backend mocking; Resume/retry stability
    
    Out today: Gideon Halloway (no commit, review or comment 2025-01-07..2025-01-27) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Online request processing refactors complete and tested; no throughput regression; resume/retry path solid; lazy imports ready for production
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 8 release(s) shipped, currently v0.1.14
      - 159 changes merged to date

    On the table
      - Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing (Konrad Feltrin)
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
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 

    DOES NOT EXIST YET (6 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - telemetry
      - — and 1054 function/class names and 110 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. lazy imports, config overhaul, integration test coverage
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Config changes don't break online throughput   *** MUST RAISE ***
      2. Integration tests cover all backends   *** MUST RAISE ***
      3. Lazy imports don't degrade startup   *** MUST RAISE ***
      4. what "Onboarding: emil, Core Platform Engineer for Request Processing" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "WS-014 design: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Config changes don't break online throughput
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. cost estimation, backend swapping perspective
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Config changes don't break online throughput
      2. Integration tests cover all backends
      3. Lazy imports don't degrade startup
    goal        Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. CI coverage strategy
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Config changes don't break online throughput
      2. Integration tests cover all backends
      3. Lazy imports don't degrade startup
    goal        Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. batch/retry details
    owns        (nothing specific)
    agenda
      1. Config changes don't break online throughput
      2. Integration tests cover all backends
      3. Lazy imports don't degrade startup
    goal        Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active
    available   around today

  Ilse Vandekerckhove  (ilse)
    role        Contributor, Local Inference Backends (vLLM). offline backend perspective
    owns        local-offline-inference
    agenda
      1. Config changes don't break online throughput
      2. Integration tests cover all backends
      3. Lazy imports don't degrade startup
    goal        Five commits to online-request-processing and bulk-llm-inference; factory refactor and lazy loading active
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Online request processing refactors complete and tested; no throughput regression; resume/retry path solid; lazy imports ready for production

