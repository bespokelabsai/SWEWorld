# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-11-12 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 13 opened, 26 reviewed, two PRs older than median merge time; workstream driving needs unblock

    Today is Tuesday 12 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 13 opened, 26 reviewed, two PRs older than median merge time; workstream driving needs unblock
    
    What it should get through:
      1. Unblock PR 39 (docstring cleanup) and move it to merge   [Konrad Feltrin must raise this]
           - Konrad Feltrin surfaces that PR 39 has been waiting three days
           - Dario Kestrel or Dermot Callaghan confirms it has no blocking feedback
           - Konrad Feltrin pulls and merges it
      2. Confirm PR 44 (starter UI example) is ready to land for examples workstream   [Gideon Halloway must raise this]
           - Gideon Halloway explains PR 44 is blocking the workstream
           - Dario Kestrel or Dermot Callaghan checks if there are unaddressed comments
           - either it merges today or the blocker is named
      3. Confirm PR 61 and PR 65 refactors have settled and no further rounds needed   [Dario Kestrel must raise this]
           - Dario Kestrel walks through why PR 61 (arrow file state) and PR 65 (GenericRequest) landed after multiple rounds
           - Dermot Callaghan and Konrad Feltrin confirm no regression concerns
           - team agrees the pattern is sound
    
    On the agenda: Status on stale PRs: PR 39, PR 44, PR 71; Shape of recent refactors: PR 61, PR 65, PR 70; Colab asyncio fixes: PR 69, PR 72 readiness
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 39 and PR 44 either merged or with clear blockers named; confidence that PR 61/#65 refactor pattern is solid and won't need further review rounds; asyncio colab fixes (PR 69, PR 72) confirmed ready to queue
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 45 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 71: Cleanup build script and .gitignore for build artifacts (Gideon Halloway)
      - PR 72: Fix asyncio with nest_asyncio (Dermot Callaghan)
      - PR 73: Set RLIMIT_NOFILE to avoid "too many files open" errors (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 45: [UI] Resolve dataset viewer component read file location after PR #28
      - issue 46: [UI] Resolve dataset viewer component streaming logic after PR #28
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1296 function/class names and 197 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. ownership of examples-cookbooks and visibility into what blocks the docs workstream
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock PR 39 (docstring cleanup) and move it to merge   *** MUST RAISE ***
      2. Confirm PR 44 (starter UI example) is ready to land for examples workstream
      3. Confirm PR 61 and PR 65 refactors have settled and no further rounds needed
    goal        Unblock PR 39 (docstring cleanup) and move it to merge
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. two stale PRs (PR 44 and PR 71) and context on what the examples workstream needs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock PR 39 (docstring cleanup) and move it to merge
      2. Confirm PR 44 (starter UI example) is ready to land for examples workstream   *** MUST RAISE ***
      3. Confirm PR 61 and PR 65 refactors have settled and no further rounds needed
    goal        Confirm PR 44 (starter UI example) is ready to land for examples workstream
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. heavy commit load and review experience; landed several complex PRs (PR 61 refactor, PR 65 GenericRequest)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock PR 39 (docstring cleanup) and move it to merge
      2. Confirm PR 44 (starter UI example) is ready to land for examples workstream
      3. Confirm PR 61 and PR 65 refactors have settled and no further rounds needed   *** MUST RAISE ***
    goal        Confirm PR 61 and PR 65 refactors have settled and no further rounds needed
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. asyncio expertise (nested loop fixes in PR 69, PR 72) and code style work (PR 64 line length)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Unblock PR 39 (docstring cleanup) and move it to merge
      2. Confirm PR 44 (starter UI example) is ready to land for examples workstream
      3. Confirm PR 61 and PR 65 refactors have settled and no further rounds needed
    goal        13 opened, 26 reviewed, two PRs older than median merge time; workstream driving needs unblock
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 39 and PR 44 either merged or with clear blockers named; confidence that PR 61/#65 refactor pattern is solid and won't need further review rounds; asyncio colab fixes (PR 69, PR 72) confirmed ready to queue


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 57 commits including postmortem-worthy revert; heavy refactoring requiring alignment

    Today is Tuesday 12 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 57 commits including postmortem-worthy revert; heavy refactoring requiring alignment
    
    What it should get through:
      1. Postmortem agreement on revert and prevention for future changes to examples   [Dermot Callaghan must raise this]
           - Dermot Callaghan walks through postmortem-2024-11-05 findings
           - Konrad Feltrin and Dario Kestrel confirm they understand the distill.py and poem.py changes that reverted
           - team agrees on review gate or test coverage to prevent similar diffs
      2. Confirm refactor safety: PR 65 GenericRequest and PR 70 batch size are not regressions   [Dario Kestrel must raise this]
           - Dario Kestrel explains why PR 65 (GenericRequest refactor) was needed and how it changes the interface
           - Konrad Feltrin asks if examples layer needs updates; Dario Kestrel says no or shows the diff
           - team agrees the request/response shape is stable for the next month
    
    On the agenda: Revert context: what happened and how to prevent it; Refactor landing pattern: PR 61, PR 65, PR 70 shape; Next layer: error handling and type safety
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Postmortem context shared; team agrees refactors are safe; confidence that examples workstream won't collide with request layer changes
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 45 changes merged to date

    On the table
      - Postmortem: Nov 5 revert of unwanted diffs (Dermot Callaghan)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 71: Cleanup build script and .gitignore for build artifacts (Gideon Halloway)
      - PR 72: Fix asyncio with nest_asyncio (Dermot Callaghan)
      - PR 73: Set RLIMIT_NOFILE to avoid "too many files open" errors (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 45: [UI] Resolve dataset viewer component read file location after PR #28
      - issue 46: [UI] Resolve dataset viewer component streaming logic after PR #28
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1296 function/class names and 197 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. postmortem authorship and knowledge of what was reverted and why
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Postmortem agreement on revert and prevention for future changes to examples   *** MUST RAISE ***
      2. Confirm refactor safety: PR 65 GenericRequest and PR 70 batch size are not regressions
      3. what "Postmortem: Nov 5 revert of unwanted diffs" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Postmortem agreement on revert and prevention for future changes to examples
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. heavy landing of refactors (PR 65 GenericRequest, PR 70 batch size arg, PR 75 jsonl types) and error handling work (PR 59 tiktoken fallback)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Postmortem agreement on revert and prevention for future changes to examples
      2. Confirm refactor safety: PR 65 GenericRequest and PR 70 batch size are not regressions   *** MUST RAISE ***
    goal        Confirm refactor safety: PR 65 GenericRequest and PR 70 batch size are not regressions
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. documentation work and overview of how examples layer uses the refactored interfaces
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Postmortem agreement on revert and prevention for future changes to examples
      2. Confirm refactor safety: PR 65 GenericRequest and PR 70 batch size are not regressions
    goal        57 commits including postmortem-worthy revert; heavy refactoring requiring alignment
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Postmortem context shared; team agrees refactors are safe; confidence that examples workstream won't collide with request layer changes


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 24 changes across bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations

    Today is Tuesday 12 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 24 changes across bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    
    What it should get through:
      1. Confirm colab asyncio fixes (PR 69 remove asyncio.run, PR 72 nest_asyncio) are compatible and sufficient   [Dermot Callaghan must raise this]
           - Dermot Callaghan explains the two asyncio fixes and how they interact
           - Dario Kestrel asks if both are needed or if one subsumes the other
           - team agrees on testing plan or merges both as-is
      2. Confirm batch mode metadata schema (PR 56 merge) enables next work without rework   [Gideon Halloway must raise this]
           - Gideon Halloway confirms PR 56 merged and batch_mode field is stable
           - Dario Kestrel checks if it blocks any of the in-flight batch-size work (PR 70)
           - team agrees the schema is good for month-ahead planning
    
    On the agenda: Colab asyncio fixes: PR 69 PR 72 and whether they interact; Batch mode metadata schema: PR 56 and next steps; File descriptor limits: PR 73 testing needed
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Colab asyncio path confirmed; batch mode metadata schema confirmed stable; team has testing plan for file descriptor limits
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 45 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 71: Cleanup build script and .gitignore for build artifacts (Gideon Halloway)
      - PR 72: Fix asyncio with nest_asyncio (Dermot Callaghan)
      - PR 73: Set RLIMIT_NOFILE to avoid "too many files open" errors (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 45: [UI] Resolve dataset viewer component read file location after PR #28
      - issue 46: [UI] Resolve dataset viewer component streaming logic after PR #28
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1296 function/class names and 197 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 24 changes including tiktoken fallback, arrow state safety, request/response refactor, batch size parameterization, rlimit fixes, jsonl type fixes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm colab asyncio fixes (PR 69 remove asyncio.run, PR 72 nest_asyncio) are compatible and sufficient
      2. Confirm batch mode metadata schema (PR 56 merge) enables next work without rework
    goal        24 changes across bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. asyncio nest_asyncio fixes (PR 72) and asyncio.run removal (PR 69) for colab compatibility; code style enforcement (PR 64)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm colab asyncio fixes (PR 69 remove asyncio.run, PR 72 nest_asyncio) are compatible and sufficient   *** MUST RAISE ***
      2. Confirm batch mode metadata schema (PR 56 merge) enables next work without rework
    goal        Confirm colab asyncio fixes (PR 69 remove asyncio.run, PR 72 nest_asyncio) are compatible and sufficient
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. metadata.db and batch_mode schema work; build script cleanup; version downgrade for colab
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm colab asyncio fixes (PR 69 remove asyncio.run, PR 72 nest_asyncio) are compatible and sufficient
      2. Confirm batch mode metadata schema (PR 56 merge) enables next work without rework   *** MUST RAISE ***
    goal        Confirm batch mode metadata schema (PR 56 merge) enables next work without rework
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Colab asyncio path confirmed; batch mode metadata schema confirmed stable; team has testing plan for file descriptor limits


------------------------------------------------------------------------------
## #incidents — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: revert incident with evidence of unintended diffs to poem.py and distill.py

    Today is Tuesday 12 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: revert incident with evidence of unintended diffs to poem.py and distill.py
    
    What it should get through:
      1. Agree on root cause and prevention for accidental diffs in examples layer   [Dermot Callaghan must raise this]
           - Dermot Callaghan walks through postmortem; commits 2fa8533 and 611f0d6 reverted
           - Konrad Feltrin and Dario Kestrel confirm the files that were unintentionally changed
           - team names whether this was a merge conflict resolution gone wrong, or a stray edit, and agrees on a gate
    
    On the agenda: What was reverted and impact; Root cause: how diffs ended up in examples; Prevention: process or tooling
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Root cause identified; prevention agreed (e.g., pre-merge review of example files, test gate, CI check); team confident it won't recur
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 45 changes merged to date

    On the table
      - Postmortem: Nov 5 revert of unwanted diffs (Dermot Callaghan)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 71: Cleanup build script and .gitignore for build artifacts (Gideon Halloway)
      - PR 72: Fix asyncio with nest_asyncio (Dermot Callaghan)
      - PR 73: Set RLIMIT_NOFILE to avoid "too many files open" errors (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 45: [UI] Resolve dataset viewer component read file location after PR #28
      - issue 46: [UI] Resolve dataset viewer component streaming logic after PR #28
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1296 function/class names and 197 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. postmortem authorship; understanding of what was reverted and root cause
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree on root cause and prevention for accidental diffs in examples layer   *** MUST RAISE ***
      2. what "Postmortem: Nov 5 revert of unwanted diffs" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Agree on root cause and prevention for accidental diffs in examples layer
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. examples-cookbooks ownership; understanding of which files (distill.py, poem.py) were affected
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Agree on root cause and prevention for accidental diffs in examples layer
    goal        revert incident with evidence of unintended diffs to poem.py and distill.py
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. review volume and merge understanding; may have been first to catch or approve the reverted changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree on root cause and prevention for accidental diffs in examples layer
    goal        revert incident with evidence of unintended diffs to poem.py and distill.py
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Root cause identified; prevention agreed (e.g., pre-merge review of example files, test gate, CI check); team confident it won't recur


==============================================================================
# 2024-11-13 — 1 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 12 PRs opened and reviewed today; version 0.1.7 landed; two older PRs need attention

    Today is Wednesday 13 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 12 PRs opened and reviewed today; version 0.1.7 landed; two older PRs need attention
    
    What it should get through:
      1. Merge remaining release PRs to close 0.1.7 cycle   [Dermot Callaghan must raise this]
           - Dermot reports PR 83 merged, PR 82 waiting on one more approval
           - Gideon confirms PR 83 is good; PR 82 can go if Konrad signs off
           - Konrad approves PR 82; both release PRs merged
      2. Ship batch-mode viewer changes without blocking downstream work   [Gideon Halloway must raise this]
           - Gideon shows PR 95 diff: better no-data state, error handling in dataset viewer
           - Dario asks about edge cases in the error paths
           - Gideon explains the new error messages; they approve; PR 95 can merge
      3. Unblock or defer stale PRs before they age further   [Konrad Feltrin must raise this]
           - Konrad flags PR 39 still waiting for minor docstring fixes; blocks on his review
           - Gideon notes PR 44 (starter example) is still wip, will land after viewer work settles
           - Plan: PR 39 review by end of day, PR 44 deferred to next sprint
      4. write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped   [Dario Kestrel must raise this]
           - Dario Kestrel says they will write Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped — Recaps the week two releases went out back to back.
    
    On the agenda: Release PRs (PR 81, PR 82, PR 83) status and merge order; Pending viewer and request processing PRs (PR 78, PR 90, PR 95); Stale PRs (PR 39, PR 44) — what is blocking them; Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: 0.1.7 release closes, three pending PRs land or are explicitly deferred, stale work gets attention
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 55 changes merged to date

    On the table
      - Moving to PR-only: process plan for Nov/Dec (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 71: Cleanup build script and .gitignore for build artifacts (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 95: better no data view and error handling in dataset viewer (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1298 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release and version management; async/event-loop fixes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Merge remaining release PRs to close 0.1.7 cycle   *** MUST RAISE ***
      2. Ship batch-mode viewer changes without blocking downstream work
      3. Unblock or defer stale PRs before they age further
      4. write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped
      5. what "Moving to PR-only: process plan for Nov/Dec" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge remaining release PRs to close 0.1.7 cycle
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing details; caching logic; JSON parsing fixes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge remaining release PRs to close 0.1.7 cycle
      2. Ship batch-mode viewer changes without blocking downstream work
      3. Unblock or defer stale PRs before they age further
      4. write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped   *** MUST RAISE ***
      5. that the doc "Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped" is done, and where the others can find it   *** MUST RAISE ***
      6. that the doc "Postmortem: Nov 12 revert in distill.py and poem.py" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Viewer UI fixes; sort and filter refactors; batch mode adaptation
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Merge remaining release PRs to close 0.1.7 cycle
      2. Ship batch-mode viewer changes without blocking downstream work   *** MUST RAISE ***
      3. Unblock or defer stale PRs before they age further
      4. write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped
    goal        Ship batch-mode viewer changes without blocking downstream work
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Code quality perspective on docstrings and minor issues
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Merge remaining release PRs to close 0.1.7 cycle
      2. Ship batch-mode viewer changes without blocking downstream work
      3. Unblock or defer stale PRs before they age further   *** MUST RAISE ***
      4. write up Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped
    goal        Unblock or defer stale PRs before they age further
    available   around today

### 4. How it should land

    lands as  partial
    leaving   0.1.7 release closes, three pending PRs land or are explicitly deferred, stale work gets attention


==============================================================================
# 2024-11-14 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 7 PRs merged today including the 0.1.8 release; 2 older PRs still open need decision

    Today is Thursday 14 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 PRs merged today including the 0.1.8 release; 2 older PRs still open need decision
    
    What it should get through:
      1. Decide whether PR 44 and PR 39 block the release or can wait   [Gideon Halloway must raise this]
           - Gideon raises that both are pre-release; Dermot checks if they're actually blocking; consensus they defer
      2. Confirm asyncio and client cleanup fixes are stable   [Dermot Callaghan must raise this]
           - Dermot walks through the fixes; Gideon confirms reviewed cleanly; Dario notes no regressions seen
    
    On the agenda: Review stale PRs (PR 44, PR 39) and defer if needed; Confirm PR 99 and PR 101 are solid after merge; Check remaining open issues (PR 96, PR 102, PR 103, PR 105, PR 107)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: All 7 merged PRs are stable; decision made on stale PRs; release 0.1.8 is clean to ship
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 62 changes merged to date

    On the table
      - Moving to PR-only: process plan for Nov/Dec (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 104: logo size fix in README for mobile (Otto Brennan)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Knows the state of merged cleanup and build-related work; has visibility into open issues PR 96, PR 103, PR 107 that just opened
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Decide whether PR 44 and PR 39 block the release or can wait   *** MUST RAISE ***
      2. Confirm asyncio and client cleanup fixes are stable
      3. what "Moving to PR-only: process plan for Nov/Dec" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Decide whether PR 44 and PR 39 block the release or can wait
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just landed asyncio fixes and explicit client cleanup; knows what's still needed for stability
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Decide whether PR 44 and PR 39 block the release or can wait
      2. Confirm asyncio and client cleanup fixes are stable   *** MUST RAISE ***
    goal        Confirm asyncio and client cleanup fixes are stable
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Batch response format fix merged; unblocked by review
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Decide whether PR 44 and PR 39 block the release or can wait
      2. Confirm asyncio and client cleanup fixes are stable
    goal        7 PRs merged today including the 0.1.8 release; 2 older PRs still open need decision
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   All 7 merged PRs are stable; decision made on stale PRs; release 0.1.8 is clean to ship


------------------------------------------------------------------------------
## #engineering — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Major release day: 7 PRs merged, 5 new issues opened, new contractor Otto Brennan landed, multiple subsystems touched

    Today is Thursday 14 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Major release day: 7 PRs merged, 5 new issues opened, new contractor Otto Brennan landed, multiple subsystems touched
    
    What it should get through:
      1. Brief team on 0.1.8 contents and stability improvements   [Dermot Callaghan must raise this]
           - Dermot walks through asyncio fix and client cleanup; Gideon adds cleanup and UI fixes; Dario mentions batch response format
      2. Categorize new issues by urgency and owner   [Gideon Halloway must raise this]
           - Gideon lists PR 96 (pytest), PR 102 (return type), PR 103 (logo), PR 105 (graph skew), PR 107 (cache); Team agrees PR 103 is Otto Brennan's; PR 96 needs owner; rest are backlog
      3. Onboard Otto Brennan and confirm examples flow   [Konrad Feltrin must raise this]
           - Konrad says Otto Brennan doc is ready; Otto asks about README priorities; Konrad mentions PR 106 is in review; Gideon notes PR 44 is waiting
    
    On the agenda: What went into 0.1.8: asyncio, batch, cleanup; New issues opened today and their severity; Next: Otto Brennan onboarding, examples, and stale PRs
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team knows what 0.1.8 contains; new issues are triaged; Otto Brennan is oriented to first tasks
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 62 changes merged to date

    On the table
      - curator.LLM core build plan (Dermot Callaghan)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - onboarding-Otto Brennan (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 104: logo size fix in README for mobile (Otto Brennan)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Overview of asyncio and batch client fixes; knows what went into this release
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Brief team on 0.1.8 contents and stability improvements   *** MUST RAISE ***
      2. Categorize new issues by urgency and owner
      3. Onboard Otto Brennan and confirm examples flow
      4. what "curator.LLM core build plan" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Brief team on 0.1.8 contents and stability improvements
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Landed cleanup and build work; knows UI fixes and .gitignore improvements
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Brief team on 0.1.8 contents and stability improvements
      2. Categorize new issues by urgency and owner   *** MUST RAISE ***
      3. Onboard Otto Brennan and confirm examples flow
    goal        Categorize new issues by urgency and owner
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Batch response format fix merged; context on batch API work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Brief team on 0.1.8 contents and stability improvements
      2. Categorize new issues by urgency and owner
      3. Onboard Otto Brennan and confirm examples flow
    goal        Major release day: 7 PRs merged, 5 new issues opened, new contractor Otto Brennan landed, multiple subsystems touched
    available   around today

  Otto Brennan  (otto)
    role        Contributor — Install UX & README Polish. Mobile logo fix for README
    owns        (nothing specific)
    agenda
      1. Brief team on 0.1.8 contents and stability improvements
      2. Categorize new issues by urgency and owner
      3. Onboard Otto Brennan and confirm examples flow
    goal        Major release day: 7 PRs merged, 5 new issues opened, new contractor Otto Brennan landed, multiple subsystems touched
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. New example for text summarization; watching Otto Brennan's onboarding
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Brief team on 0.1.8 contents and stability improvements
      2. Categorize new issues by urgency and owner
      3. Onboard Otto Brennan and confirm examples flow   *** MUST RAISE ***
      4. that the doc "Onboarding: otto on install UX & README polish" is done, and where the others can find it   *** MUST RAISE ***
      5. that "Welcome otto to the team" has gone out, and what you asked in it   *** MUST RAISE ***
      6. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Onboard Otto Brennan and confirm examples flow
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team knows what 0.1.8 contains; new issues are triaged; Otto Brennan is oriented to first tasks


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 14 changes to core request layer (bulk-llm-inference, online-request-processing, provider-integrations, caching-and-resume); 6 commits from Dermot landed; 5 related issues opened

    Today is Thursday 14 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 14 changes to core request layer (bulk-llm-inference, online-request-processing, provider-integrations, caching-and-resume); 6 commits from Dermot landed; 5 related issues opened
    
    What it should get through:
      1. Verify asyncio fix prevents event-loop-closed errors in production   [Dermot Callaghan must raise this]
           - Dermot explains the asyncio.run in except block problem; Gideon confirms it was hitting in tests; Dario says will monitor in live batches
      2. Clarify batch cache behavior and required changes for PR 33   [Dario Kestrel must raise this]
           - Dario notes PR 97 landed but PR 33 (check cache before download) still open; Dermot suggests batching cache checks with resume logic; Gideon notes PR 102 (return type clarity) affects this
      3. Plan metrics exposure for PR 57 and provider instrumentation   [Gideon Halloway must raise this]
           - Gideon raises PR 57 as blocker for observability; Dario says it feeds into cost tracking; Dermot agrees to scope it for next cycle
    
    On the agenda: Asyncio and client cleanup impact on stability; Batch mode readiness and cache behavior (PR 33, PR 50); Metrics exposure for cache and provider backends (PR 57)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Asyncio fixes are verified safe; batch mode blockers (PR 33, PR 50) are clarified; metrics work is deferred cleanly
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 62 changes merged to date

    On the table
      - Postmortem: Nov 12 revert in distill.py and poem.py (Dario Kestrel)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 44: Add a starter example for running UI for the first time (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 104: logo size fix in README for mobile (Otto Brennan)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just merged asyncio and explicit client cleanup fixes; knows remaining stability gaps
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Verify asyncio fix prevents event-loop-closed errors in production   *** MUST RAISE ***
      2. Clarify batch cache behavior and required changes for PR 33
      3. Plan metrics exposure for PR 57 and provider instrumentation
      4. what "Postmortem: Nov 12 revert in distill.py and poem.py" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify asyncio fix prevents event-loop-closed errors in production
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Batch response format fix; context on what PR 33 (cache for batch) and PR 50 (vary batch size) need
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Verify asyncio fix prevents event-loop-closed errors in production
      2. Clarify batch cache behavior and required changes for PR 33   *** MUST RAISE ***
      3. Plan metrics exposure for PR 57 and provider instrumentation
    goal        Clarify batch cache behavior and required changes for PR 33
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Knows build and CLI work; can speak to PR 57 (expose metrics for cache)
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Verify asyncio fix prevents event-loop-closed errors in production
      2. Clarify batch cache behavior and required changes for PR 33
      3. Plan metrics exposure for PR 57 and provider instrumentation   *** MUST RAISE ***
    goal        Plan metrics exposure for PR 57 and provider instrumentation
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Asyncio fixes are verified safe; batch mode blockers (PR 33, PR 50) are clarified; metrics work is deferred cleanly


==============================================================================
# 2024-11-15 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 18 reviews across 7 merged PRs this week; 3 stale PRs need attention

    Today is Friday 15 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 18 reviews across 7 merged PRs this week; 3 stale PRs need attention
    
    What it should get through:
      1. Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)   [Gideon Halloway must raise this]
           - Gideon flags PR 110 ready pending one more check
           - Konrad confirms PR 117 is final after 9 commits of updates
           - Dario merges both with no blockers
      2. Triage stale PRs and decide next steps   [Dario Kestrel must raise this]
           - Dario notes PR 78 and PR 90 are his, blocked on broader work
           - Konrad wants PR 39 and PR 106 back on radar next week
           - Group agrees to revisit Monday
    
    On the agenda: Clear merged PRs and their comments; Review and merge waiting PRs: PR 110, PR 117, PR 130; Discuss stale PRs: PR 39, PR 78, PR 90, PR 106
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 110, PR 117, PR 130 merged; stale PRs deferred to next week; the team knows what's still waiting
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 1 release(s) shipped, currently v0.1.8
      - 69 changes merged to date

    On the table
      - Moving to PR-only: process plan for Nov/Dec (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 110: 0.1.9 (Gideon Halloway)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Completed the terminal interactive usage PR and the starter example, knows what still needs review on PR 110
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)   *** MUST RAISE ***
      2. Triage stale PRs and decide next steps
      3. what "Moving to PR-only: process plan for Nov/Dec" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Finished the README and poem example updates across multiple commits
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)
      2. Triage stale PRs and decide next steps
    goal        18 reviews across 7 merged PRs this week; 3 stale PRs need attention
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Multiple batch-mode fixes landed; understands the constraints on file size and pbar counting
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)
      2. Triage stale PRs and decide next steps   *** MUST RAISE ***
      3. that "v0.1.8 is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Triage stale PRs and decide next steps
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. New teacher.py example that refactors the original code
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Merge PR 110 (0.1.9 prep) and PR 117 (README/examples)
      2. Triage stale PRs and decide next steps
    goal        18 reviews across 7 merged PRs this week; 3 stale PRs need attention
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 110, PR 117, PR 130 merged; stale PRs deferred to next week; the team knows what's still waiting


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: 8 commits to examples-cookbooks; workstream mid-flight on examples/docs end-to-end

    Today is Friday 15 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 8 commits to examples-cookbooks; workstream mid-flight on examples/docs end-to-end
    
    What it should get through:
      1. Confirm README and examples work end-to-end for v0.1.8   [Konrad Feltrin must raise this]
           - Konrad walks through the fixes: links, poem.py parsing, starting example
           - Gideon checks if terminal demo still works with the changes
           - Group agrees it's good for release announcement
      2. Land PR 130 and keep example patterns consistent   [Dermot Callaghan must raise this]
           - Dermot walks through teacher.py refactoring
           - Konrad suggests any naming or structure issues
           - Group agrees it fits the corpus
    
    On the agenda: Confirm README is release-ready after Konrad's 9 commits; Ensure all examples run cleanly: poem.py, interactive, teacher.py; Brief on v0.1.9 example roadmap
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: README and examples confirmed ready; PR 130 merged; team knows the getting-started story is clean
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 1 release(s) shipped, currently v0.1.8
      - 69 changes merged to date

    On the table
      - Moving to PR-only: process plan for Nov/Dec (Konrad Feltrin)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 110: 0.1.9 (Gideon Halloway)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Shipped 9 commits on README, poem example, and broken links; knows what still needs polish
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm README and examples work end-to-end for v0.1.8   *** MUST RAISE ***
      2. Land PR 130 and keep example patterns consistent
      3. what "Moving to PR-only: process plan for Nov/Dec" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm README and examples work end-to-end for v0.1.8
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. New teacher.py example refactoring; knows the patterns
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm README and examples work end-to-end for v0.1.8
      2. Land PR 130 and keep example patterns consistent   *** MUST RAISE ***
    goal        Land PR 130 and keep example patterns consistent
    available   around today

  Otto Brennan  (otto)
    role        Contributor — Install UX & README Polish. Mobile logo fix that's already merged
    owns        (nothing specific)
    agenda
      1. Confirm README and examples work end-to-end for v0.1.8
      2. Land PR 130 and keep example patterns consistent
    goal        8 commits to examples-cookbooks; workstream mid-flight on examples/docs end-to-end
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   README and examples confirmed ready; PR 130 merged; team knows the getting-started story is clean


------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.8 shipped; release-v0-1-8 and announce-v0-1-8 due today

    Today is Friday 15 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.8 shipped; release-v0-1-8 and announce-v0-1-8 due today
    
    What it should get through:
      1. Finalize v0.1.8 release notes   [Dario Kestrel must raise this]
           - Dario lists the 7 merged items: batch fixes, terminal UI, README polish, pbar fix
           - Konrad suggests framing for users: what they can do now
           - Notes go out in the mail
    
    On the agenda: Draft release notes for v0.1.8; Review the list of merged features; Send the announcement mail
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.8 release notes finalized and announcement sent
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 1 release(s) shipped, currently v0.1.8
      - 69 changes merged to date

    On the table
      - v0.1.8 release notes (Dario Kestrel)
      - announce-v0-1-8 (Dario Kestrel)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 110: 0.1.9 (Gideon Halloway)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 31: [UI] When metadata.db isn't found, give more examples and actionable suggestions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1295 function/class names and 190 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Authored the v0.1.8 release; merged 7 PRs this week
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Finalize v0.1.8 release notes   *** MUST RAISE ***
      2. that the doc "v0.1.8 release notes" is done, and where the others can find it   *** MUST RAISE ***
      3. what "v0.1.8 is out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Finalize v0.1.8 release notes
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Updated README and examples; knows what the user story is
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Finalize v0.1.8 release notes
    goal        v0.1.8 shipped; release-v0-1-8 and announce-v0-1-8 due today
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Has context on the broader pipeline improvements
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Finalize v0.1.8 release notes
    goal        v0.1.8 shipped; release-v0-1-8 and announce-v0-1-8 due today
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.8 release notes finalized and announcement sent


==============================================================================
# 2024-11-18 — 4 conversation(s), 46 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.9 shipped over the weekend; release notes are due today and no one has written them yet

    Today is Monday 18 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.9 shipped over the weekend; release notes are due today and no one has written them yet
    
    What it should get through:
      1. Record what went into v0.1.9 for the changelog   [Dario Kestrel must raise this]
           - Dario Kestrel outlines the merged PRs and services touched
           - Konrad Feltrin and Dermot Callaghan confirm the viewer and pipeline work is there
           - Dario Kestrel writes the notes
    
    On the agenda: Capture what shipped in v0.1.9; Confirm the examples and viewer changes are documented; Settle the release
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.9 release notes written and ready to ship
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 2 release(s) shipped, currently v0.1.9
      - 75 changes merged to date

    On the table
      - v0.1.9 release notes (Dario Kestrel)
      - v0.1.8 release notes (Dario Kestrel)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response
      - issue 62: Support generation configuration for LLM

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1293 function/class names and 189 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. what shipped in the tag and its shape
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Record what went into v0.1.9 for the changelog   *** MUST RAISE ***
      2. that the doc "v0.1.9 release notes" is done, and where the others can find it   *** MUST RAISE ***
      3. what "v0.1.8 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Record what went into v0.1.9 for the changelog
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. what landed in docs and examples
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Record what went into v0.1.9 for the changelog
    goal        v0.1.9 shipped over the weekend; release notes are due today and no one has written them yet
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. context on the request layer changes that went out
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Record what went into v0.1.9 for the changelog
    goal        v0.1.9 shipped over the weekend; release notes are due today and no one has written them yet
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.9 release notes written and ready to ship


------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 4 PRs opened today, 5 older than the era median merge time; Gideon Halloway shipped 6 commits and needs review on the new work; Dario Kestrel and Konrad Feltrin have work waiting

    Today is Monday 18 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 4 PRs opened today, 5 older than the era median merge time; Gideon Halloway shipped 6 commits and needs review on the new work; Dario Kestrel and Konrad Feltrin have work waiting
    
    What it should get through:
      1. Land or defer Gideon Halloway's postrelease PRs   [Gideon Halloway must raise this]
           - Gideon Halloway describes what PR 140 (0.1.9post1) and PR 141 (LiteLLM backend) do
           - Konrad Feltrin asks whether they block anything or are exploratory
           - Gideon Halloway confirms LiteLLM is for new provider support and post1 is a patch
      2. Get Dario Kestrel's vLLM example and cache disable work reviewed   [Dario Kestrel must raise this]
           - Dario Kestrel reminds the room these have been waiting 5 days
           - Konrad Feltrin or Gideon Halloway commits to reviewing both
           - Dario Kestrel clarifies if either blocks the next release
      3. Settle path forward on the stale examples   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes PR 39 and PR 106 are waiting for eyes
           - Gideon Halloway and Dario Kestrel confirm they can review
           - Konrad Feltrin confirms neither is blocking the examples workstream
    
    On the agenda: Handle Gideon Halloway's new PRs (PR 140 and PR 141); Get eyes on Dario Kestrel's PR 78 and PR 90; Unblock Konrad Feltrin's PR 39 and PR 106
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Gideon's new work moves to review; Dario Kestrel's stale PRs get committed reviewer; path for PR 39 and PR 106 clarified
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 2 release(s) shipped, currently v0.1.9
      - 75 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response
      - issue 62: Support generation configuration for LLM

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1293 function/class names and 189 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on the LiteLLM backend work and table formatting
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land or defer Gideon Halloway's postrelease PRs   *** MUST RAISE ***
      2. Get Dario Kestrel's vLLM example and cache disable work reviewed
      3. Settle path forward on the stale examples
    goal        Land or defer Gideon Halloway's postrelease PRs
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. eyes on quality and what's ready to ship
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Land or defer Gideon Halloway's postrelease PRs
      2. Get Dario Kestrel's vLLM example and cache disable work reviewed
      3. Settle path forward on the stale examples   *** MUST RAISE ***
      4. that "Weekly update: week of Nov 11" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Settle path forward on the stale examples
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on the vLLM and caching work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land or defer Gideon Halloway's postrelease PRs
      2. Get Dario Kestrel's vLLM example and cache disable work reviewed   *** MUST RAISE ***
      3. Settle path forward on the stale examples
      4. that "v0.1.9 is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Get Dario Kestrel's vLLM example and cache disable work reviewed
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon's new work moves to review; Dario Kestrel's stale PRs get committed reviewer; path for PR 39 and PR 106 clarified


------------------------------------------------------------------------------
## #engineering — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 7 commits landed over the weekend and today; Gideon Halloway opened major work on LiteLLM backend for structured output; Otto landed install UI changes; examples-cookbooks workstream is mid-flight

    Today is Monday 18 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 commits landed over the weekend and today; Gideon Halloway opened major work on LiteLLM backend for structured output; Otto landed install UI changes; examples-cookbooks workstream is mid-flight
    
    What it should get through:
      1. Confirm LiteLLM backend approach fits the architecture   [Gideon Halloway must raise this]
           - Gideon Halloway pitches LiteLLM+instructor for structured output as a new provider
           - Dario Kestrel and Dermot Callaghan ask if it competes with or complements vLLM work
           - Gideon Halloway clarifies it's for schema-validated responses, vLLM is for local inference
      2. Assess Otto's install UX work and its effect on README   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes Otto has PR 133 and PR 134 waiting
           - Gideon Halloway confirms the install UI doesn't break anything
           - Konrad Feltrin asks if the UI changes need README updates
      3. Confirm no conflicts in the request layer work   [Dermot Callaghan must raise this]
           - Dermot Callaghan asks if frequency/presence penalty work and LiteLLM work align
           - Gideon Halloway and Dario Kestrel confirm they touch different subsystems
           - Dermot Callaghan notes the core stays stable
    
    On the agenda: Land Friday's work and weekend commits; Settle the LiteLLM backend direction; Unblock Otto's install UI and README work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: LiteLLM direction confirmed; Otto's work unblocked; core request layer integrity verified
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 2 release(s) shipped, currently v0.1.9
      - 75 changes merged to date

    On the table
      - curator.LLM core build plan (Dermot Callaghan)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - curator.LLM core build plan (Dermot Callaghan)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response
      - issue 62: Support generation configuration for LLM

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1293 function/class names and 189 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. the LiteLLM backend work, viewer system prompt feature, and table formatting shipped over the weekend
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm LiteLLM backend approach fits the architecture   *** MUST RAISE ***
      2. Assess Otto's install UX work and its effect on README
      3. Confirm no conflicts in the request layer work
      4. what "curator.LLM core build plan" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm LiteLLM backend approach fits the architecture
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. what landed in the examples and docs
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm LiteLLM backend approach fits the architecture
      2. Assess Otto's install UX work and its effect on README   *** MUST RAISE ***
      3. Confirm no conflicts in the request layer work
      4. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Assess Otto's install UX work and its effect on README
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on the frequency/presence penalty work that merged Friday
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm LiteLLM backend approach fits the architecture
      2. Assess Otto's install UX work and its effect on README
      3. Confirm no conflicts in the request layer work
    goal        7 commits landed over the weekend and today; Gideon Halloway opened major work on LiteLLM backend for structured output; Otto landed install UI changes; examples-cookbooks workstream is mid-flight
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. standing up the curator.LLM core context
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm LiteLLM backend approach fits the architecture
      2. Assess Otto's install UX work and its effect on README
      3. Confirm no conflicts in the request layer work   *** MUST RAISE ***
      4. what "curator.LLM core build plan" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm no conflicts in the request layer work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   LiteLLM direction confirmed; Otto's work unblocked; core request layer integrity verified


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: examples-cookbooks workstream is mid-flight; Gideon Halloway landed table formatting and system prompt; Otto has install UI ready; Konrad Feltrin has two examples waiting

    Today is Monday 18 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: examples-cookbooks workstream is mid-flight; Gideon Halloway landed table formatting and system prompt; Otto has install UI ready; Konrad Feltrin has two examples waiting
    
    What it should get through:
      1. Unblock Otto's install UI and merge it   [Konrad Feltrin must raise this]
           - Konrad Feltrin reviews Otto's PR 133 and PR 134 status
           - Gideon Halloway confirms the UI doesn't break viewer or examples
           - Konrad Feltrin commits to merge PR 134 if PR 133 is ready
      2. Settle priority on the stale examples   [Konrad Feltrin must raise this]
           - Konrad Feltrin lists PR 39 (docstring fixes) and PR 106 (SMS example) as stale
           - Dario Kestrel and Gideon Halloway agree on which should land first
           - Konrad Feltrin commits a review window
    
    On the agenda: Assess what shipped in the examples this weekend; Confirm Otto's install UI readiness; Settle the cookbook examples backlog
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Examples work coherence confirmed; Otto's UI unblocked to merge; stale examples priority set
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 2 release(s) shipped, currently v0.1.9
      - 75 changes merged to date

    On the table
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 130: Add a teacher.py example that slightly refactors Ryan's original code (Dermot Callaghan)
      - PR 133: adding an env example file (Otto Brennan)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 57: Expose more metrics from the raw_response to cache generic request / response
      - issue 62: Support generation configuration for LLM

    DOES NOT EXIST YET (10 names)
      - agentic-curation
      - batch-mode
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - multimodal-prompts
      - progress-and-cli
      - telemetry
      - — and 1293 function/class names and 189 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. what landed in the examples and what's waiting
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock Otto's install UI and merge it   *** MUST RAISE ***
      2. Settle priority on the stale examples   *** MUST RAISE ***
      3. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock Otto's install UI and merge it
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on the example work in progress
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock Otto's install UI and merge it
      2. Settle priority on the stale examples
    goal        examples-cookbooks workstream is mid-flight; Gideon Halloway landed table formatting and system prompt; Otto has install UI ready; Konrad Feltrin has two examples waiting
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Examples work coherence confirmed; Otto's UI unblocked to merge; stale examples priority set

