# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-04-18 — 3 conversation(s), 38 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: One PR opened today, four sitting past the era's median merge time; two active drivers need to move

    Today is Friday 18 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One PR opened today, four sitting past the era's median merge time; two active drivers need to move
    
    What it should get through:
      1. Decide whether PR 646 can land or needs revision   [Emil Brandvold must raise this]
           - Emil describes the Gemini job-state issue and why it needs the refactor
           - Gideon or another reviewer asks whether this conflicts with other batch fixes landing
           - Land with approval or mark for revision
      2. Unblock or defer PR 632 and understand why PR 643, PR 468 are still open   [Gideon Halloway must raise this]
           - Gideon raises PR 632 (batch update frequency) — what's blocking it?
           - Emil notes dependencies or conflicts with ongoing batch-mode work
           - Team agrees on next step: land, revise, or defer until after sweep
    
    On the agenda: Triage PR 646 (Gemini job-state check) against other batch-mode fixes; Clear or defer stalled PRs (PR 632, PR 643, PR 468); Flag any blocking release dependencies
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 646 either approved or given concrete revision request; PR 632 has a clear path (land, iterate, or defer). Other stalled PRs understood but may not move today.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. Context on batch-mode bugs and the Gemini job-state fix in PR 646; knowledge of what's blocking release
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Decide whether PR 646 can land or needs revision   *** MUST RAISE ***
      2. Unblock or defer PR 632 and understand why PR 643, PR 468 are still open
      3. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Decide whether PR 646 can land or needs revision
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Batch update frequency fix (PR 632) that's been sitting; can offer perspective on CLI observability concerns
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Decide whether PR 646 can land or needs revision
      2. Unblock or defer PR 632 and understand why PR 643, PR 468 are still open   *** MUST RAISE ***
    goal        Unblock or defer PR 632 and understand why PR 643, PR 468 are still open
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 646 either approved or given concrete revision request; PR 632 has a clear path (land, iterate, or defer). Other stalled PRs understood but may not move today.


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil Brandvold asked how he is supposed to force a new submission while debugging without hand-deleting files

    Today is Friday 18 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil Brandvold asked how he is supposed to force a new submission while debugging without hand-deleting files
    
    What it should get through:
    
    On the agenda: Emil Brandvold on deleting batch_objects.jsonl by hand three times yesterday to get a clean submission, and how that is not something users should be told to do; Dario Kestrel notes CURATOR_DISABLE_CACHE already exists for the response cache and gets set in CI, and asks whether reattach should honour it too or need its own switch; Gideon Halloway says whatever it is, a fresh submit should leave the old batch alone rather than cancel it behind his back
    
    Wrap when: leaning towards reusing the existing env var but not settled; Dario Kestrel will check what CI actually sets before anyone names a new variable; it is settled that the team agrees changing max_tokens currently returns the previous truncated output
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: max_tokens.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Same shape of thing with max_tokens for me. Response came back truncated mid sentence, I raised max_tokens, reran, got handed the truncated text again. Deleted the cache directory in the end, which also threw away four thousand rows that were perfectly fine.   *** MUST SETTLE (clue t1.r1.l_params_2) ***
         must contain literally: max_tokens
    goal        the team agrees changing max_tokens currently returns the previous truncated output
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Emil Brandvold asked how he is supposed to force a new submission while debugging without hand-deleting files
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Emil Brandvold asked how he is supposed to force a new submission while debugging without hand-deleting files
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   leaning towards reusing the existing env var but not settled; Dario Kestrel will check what CI actually sets before anyone names a new variable; it is settled that the team agrees changing max_tokens currently returns the previous truncated output


------------------------------------------------------------------------------
## #incidents — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Konrad Feltrin tried to reproduce the pass-rate change from Monday and could not, because the second run finished in nine seconds

    Today is Friday 18 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad Feltrin tried to reproduce the pass-rate change from Monday and could not, because the second run finished in nine seconds
    
    What it should get through:
    
    On the agenda: Konrad Feltrin describes pulling the newer image on purpose, rerunning, and getting byte-identical results back in nine seconds, then losing an afternoon before he worked out nothing had executed; Dario Kestrel says the only lever anyone reaches for here is CURATOR_DISABLE_CACHE and that using it means throwing away every other cached row in the run too; Konrad Feltrin says what he wanted was for that rerun to actually re-execute the code, and asks who owns the key that decides that
    
    Wrap when: open: Dario Kestrel says the fingerprint code is his but he needs to look at what the code executor puts into it before promising anything; it is settled that Dario Kestrel saw a restarted run resume a job submitted under a different provider
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. heads up, I killed a run mid-batch, flipped the backend from openai to anthropic in the same script and reran, and it went straight back to polling the openai batch id from the first attempt. only spotted it because the id in the log still had the openai shape on it.   *** MUST SETTLE (clue t3.r2.l_prov_dario) ***
    goal        Dario Kestrel saw a restarted run resume a job submitted under a different provider
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Konrad Feltrin tried to reproduce the pass-rate change from Monday and could not, because the second run finished in nine seconds
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   open: Dario Kestrel says the fingerprint code is his but he needs to look at what the code executor puts into it before promising anything; it is settled that Dario Kestrel saw a restarted run resume a job submitted under a different provider; Dario Kestrel saw a restarted run resume a job submitted under a different provider


==============================================================================
# 2025-04-21 — 5 conversation(s), 60 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: One new PR opened; six others stale beyond median merge time; two drivers have PRs waiting

    Today is Monday 21 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One new PR opened; six others stale beyond median merge time; two drivers have PRs waiting
    
    What it should get through:
      1. Unblock PR 468, PR 643, PR 646 from review queue   [Emil Brandvold must raise this]
           - Emil explains why PR 468 (n samples) is still open after 73 days
           - Gideon notes PR 632 (batch frequency) is ready to land and not a blocker
           - Emil proposes rebasing PR 643 and PR 646 if they conflict with incoming work
      2. Route PR 650 (DeepSeek json_schema) to code review   [Emil Brandvold must raise this]
           - New PR PR 650 from Tomas Berczik flagged as blocking WS-054 work
           - Emil claims review and notes DeepSeek API integration (PR 640) also waiting
    
    On the agenda: Review status of 7 open PRs, focus on age and blockers; Decide which need rebase vs split vs land-as-is; Route PR 650 (DeepSeek json_schema fix) to owner
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 632 marked ready to land; PR 650 routed to Emil Brandvold; plan made for unblocking PR 468, PR 643, PR 646 by rebase or close
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. ownership of release-and-ci and provider-integrations; context on what's blocking in WS-050 and WS-054
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock PR 468, PR 643, PR 646 from review queue   *** MUST RAISE ***
      2. Route PR 650 (DeepSeek json_schema) to code review   *** MUST RAISE ***
    goal        Unblock PR 468, PR 643, PR 646 from review queue
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on progress tracking and CLI batch-update frequency; understanding of what's needed for observability
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock PR 468, PR 643, PR 646 from review queue
      2. Route PR 650 (DeepSeek json_schema) to code review
    goal        One new PR opened; six others stale beyond median merge time; two drivers have PRs waiting
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 632 marked ready to land; PR 650 routed to Emil Brandvold; plan made for unblocking PR 468, PR 643, PR 646 by rebase or close


------------------------------------------------------------------------------
## #general — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Weekly update due; two mid-flight workstreams need team visibility; 6 stale PRs need prioritization

    Today is Monday 21 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Weekly update due; two mid-flight workstreams need team visibility; 6 stale PRs need prioritization
    
    What it should get through:
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)   [Emil Brandvold must raise this]
           - Emil reports on gemini batch bugs and whether they are two issues or one response-shape problem
           - Dario notes PR 649 (anthropic token accounting) landed Friday and unblocks cost work
           - Gideon adds that observability fix is in, removing noise from logs
      2. Surface PR review backlog and blockers   [Dario Kestrel must raise this]
           - Dario flags PR 468 (n samples) at 73 days and asks if it should be closed or rebased
           - Emil notes PR 643, PR 646, PR 632 are close to ready; PR 650 came in over the weekend
           - Gideon confirms PR 632 is unrelated to the workstreams and can land independently
    
    On the agenda: Week ahead priorities and WS-050/WS-054 status; Open PR blockers and what needs review; Any incidents or blockers from the weekend
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Team aligned on priorities; WS-050 and WS-054 status clear; plan made to unblock stale PRs this week
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - weekly-2025-04-14 (Emil Brandvold)
      - weekly-2025-04-14 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ownership of request processing and caching; visibility into PR blockers and what's stalled
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)
      2. Surface PR review backlog and blockers   *** MUST RAISE ***
    goal        Surface PR review backlog and blockers
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. recent work on April Stabilization; context on cookbooks and bulk inference
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)
      2. Surface PR review backlog and blockers
    goal        Weekly update due; two mid-flight workstreams need team visibility; 6 stale PRs need prioritization
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. leadership of WS-050 and WS-054; context on batch mode bugs and provider integration work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)   *** MUST RAISE ***
      2. Surface PR review backlog and blockers
      3. that "Weekly update: week of Apr 14" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. recent progress on observability and projected-total readout; context on CLI batch updates
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)
      2. Surface PR review backlog and blockers
    goal        Weekly update due; two mid-flight workstreams need team visibility; 6 stale PRs need prioritization
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. recent code-execution and telemetry work; understanding of release-and-ci ownership
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Update team on Batch Mode bug sweep (WS-050) and cost-accounting work (WS-054)
      2. Surface PR review backlog and blockers
    goal        Weekly update due; two mid-flight workstreams need team visibility; 6 stale PRs need prioritization
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team aligned on priorities; WS-050 and WS-054 status clear; plan made to unblock stale PRs this week


------------------------------------------------------------------------------
## #pipeline — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Dario Kestrel rewrote the reattach path after the review and wants sign-off on the parts people already argued about

    Today is Monday 21 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel rewrote the reattach path after the review and wants sign-off on the parts people already argued about
    
    What it should get through:
    
    On the agenda: Dario Kestrel walks through startup reading the tracker, matching, and only then deciding to submit, and says if anything about the call has moved since last time it should just submit a fresh batch and not touch the old one; Gideon Halloway says a finished batch that was never downloaded should get its results pulled on the next run instead of being fired off again, since it is already paid for; Dermot Callaghan and Emil Brandvold both still want the 404 case nailed down and Dermot Callaghan says he will test what OpenAI, Anthropic, Gemini and Mistral each return for an id that never existed
    
    Wrap when: key-mismatch behaviour and completed-batch download agreed in the thread; missing-id behaviour and the env var name still open, release cut mentioned but not promised; it is settled that Dermot Callaghan wants a fresh submission rather than reuse when the stored job does not match the current run
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel rewrote the reattach path after the review and wants sign-off on the parts people already argued about
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. my take after this week: if the job sitting on the provider isn't the job we would send today, just send a new one and eat the 24h and the money. a duplicate batch costs us a few dollars, handing someone a dataset that quietly blends two configs costs us their trust.   *** MUST SETTLE (clue t3.r2.l_beh_dermot) ***
    goal        Dermot Callaghan wants a fresh submission rather than reuse when the stored job does not match the current run
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel rewrote the reattach path after the review and wants sign-off on the parts people already argued about
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel rewrote the reattach path after the review and wants sign-off on the parts people already argued about
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   key-mismatch behaviour and completed-batch download agreed in the thread; missing-id behaviour and the env var name still open, release cut mentioned but not promised; it is settled that Dermot Callaghan wants a fresh submission rather than reuse when the stored job does not match the current run; Dermot Callaghan wants a fresh submission rather than reuse when the stored job does not match the current run


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nikolai Berresford posted a one-line change and Dermot Callaghan pushed back on where the default should live

    Today is Monday 21 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai Berresford posted a one-line change and Dermot Callaghan pushed back on where the default should live
    
    What it should get through:
    
    On the agenda: Nikolai Berresford wants an env var because that is what he can set on the CI runner without a release; Dermot Callaghan points out he grepped and found the image string written out in three places, the backend, a test fixture and a docs snippet, so his last attempt to move it only moved one of them, and says he wants one place that a release PR touches together with its changelog line; Emil Brandvold asks what happens to somebody who is already passing something into backend_params today and gets told nobody knows
    
    Wrap when: no decision; Dermot Callaghan's single-place preference is the loudest but Nikolai Berresford has not given up on the env var, and the question of whether backend_params keys are validated at all is raised and dropped; it is settled that the team agrees v0.1.8 must not be used for anything user facing
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: v0.1.8.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Nikolai Berresford posted a one-line change and Dermot Callaghan pushed back on where the default should live
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Please do not move anything user facing onto v0.1.8 yet, it is still eating test files in collection. I know it is sitting there in the registry looking newer than everything else, that is exactly how we get bug reports we cannot reproduce.   *** MUST SETTLE (clue t4.r1.L6) ***
         must contain literally: v0.1.8
    goal        the team agrees v0.1.8 must not be used for anything user facing
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Nikolai Berresford posted a one-line change and Dermot Callaghan pushed back on where the default should live
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   no decision; Dermot Callaghan's single-place preference is the loudest but Nikolai Berresford has not given up on the env var, and the question of whether backend_params keys are validated at all is raised and dropped; it is settled that the team agrees v0.1.8 must not be used for anything user facing


------------------------------------------------------------------------------
## #help — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: Emil Brandvold's verification pass over 20k rows spent most of its wall clock outside the container

    Today is Monday 21 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil Brandvold's verification pass over 20k rows spent most of its wall clock outside the container
    
    What it should get through:
    
    On the agenda: Emil Brandvold timed it: every executor start goes out to the registry even when the image is already sitting in his local images list, roughly 40 seconds a pop on hotel wifi, and he wants it to look locally first and only go to the network when the image genuinely is not there; Nikolai Berresford adds that the CI box has no outbound registry access and the run dies on the pull even though the image was loaded into the daemon in a previous step; Gideon Halloway asks which tag Emil Brandvold actually ended up running and nobody can answer from the logs, so Gideon Halloway says the run should say the resolved name and tag once at startup where he can see it
    
    Wrap when: three separate annoyances collected, no code written; Nikolai Berresford says he will fold the pull behaviour into the pinning PR if it is small; it is settled that the team agrees a per-request capability lookup is wasted work because the answer is fixed for the whole run
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 334 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 645: feature: set dtype flag (Tobias Renner)
      - PR 646: ref: check job state before download in gemini (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Emil Brandvold's verification pass over 20k rows spent most of its wall clock outside the container
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Emil Brandvold's verification pass over 20k rows spent most of its wall clock outside the container
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. profiled the 40k row poem run because the bars were stuttering. we do the capability lookup per request, so that is 40k passes over the same model string and 40k identical debug lines in the log. the answer cannot change between row 1 and row 40000, the model name is fixed the moment you configure the thing   *** MUST SETTLE (clue t2.r1.L5) ***
    goal        the team agrees a per-request capability lookup is wasted work because the answer is fixed for the whole run
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   three separate annoyances collected, no code written; Nikolai Berresford says he will fold the pull behaviour into the pinning PR if it is small; it is settled that the team agrees a per-request capability lookup is wasted work because the answer is fixed for the whole run


==============================================================================
# 2025-04-22 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs merged today plus one just opened; two workstreams landing

    Today is Tuesday 22 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today plus one just opened; two workstreams landing
    
    What it should get through:
      1. PR 649 confirmed as safe to ship   [Dario Kestrel must raise this]
           - Dario explains the casting bug in token metadata
           - Dermot asks if it affects batch streaming
           - Dario confirms it's anthropic-specific
      2. PR 646 framed as sweep closure not quick fix   [Emil Brandvold must raise this]
           - Emil explains this closes the batch-mode bug sweep by fixing the root ordering issue
           - Dermot notes this is different from previous patchwork
           - Emil confirms — no more symptom fixes
      3. PR 651 queued for review cycle   [Emil Brandvold must raise this]
           - Emil posts the PR scope
           - Dermot asks if it blocks anything
           - Emil: no — just model list refresh
    
    On the agenda: PR 649: anthropic token accounting fix — casting bug contained; PR 646: gemini job state ordering — root cause vs symptom; PR 651: multimodal openai models — what changed
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: All three merged PRs acknowledged as landing; PR 651 queued for eyes and will merge same-day style; no blockers found
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. context on both landing workstreams and the new multimodal PR
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 649 confirmed as safe to ship
      2. PR 646 framed as sweep closure not quick fix   *** MUST RAISE ***
      3. PR 651 queued for review cycle   *** MUST RAISE ***
    goal        PR 646 framed as sweep closure not quick fix
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. the anthropic token accounting fix and why it matters
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 649 confirmed as safe to ship   *** MUST RAISE ***
      2. PR 646 framed as sweep closure not quick fix
      3. PR 651 queued for review cycle
    goal        PR 649 confirmed as safe to ship
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. testing perspective on the refactors
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 649 confirmed as safe to ship
      2. PR 646 framed as sweep closure not quick fix
      3. PR 651 queued for review cycle
    goal        Three PRs merged today plus one just opened; two workstreams landing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   All three merged PRs acknowledged as landing; PR 651 queued for eyes and will merge same-day style; no blockers found


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Three provider-facing commits; two workstreams landing back-to-back

    Today is Tuesday 22 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three provider-facing commits; two workstreams landing back-to-back
    
    What it should get through:
      1. Anthropic token bug is anthropic-only, not cascading   [Dario Kestrel must raise this]
           - Dario walks through where the casting happens
           - Emil asks if online-request-processing sees it elsewhere
           - Dario: just in anthropic metadata; other backends unaffected
      2. Batch-mode sweep closed by ordering root cause fix   [Emil Brandvold must raise this]
           - Emil: PR 646 fixes job-state-before-download ordering in gemini
           - Gideon asks if other backends have the same issue
           - Emil: gemini-specific; others already check state correctly
      3. April grind status clear; Gideon Halloway's batch-update PR path visible   [Emil Brandvold must raise this]
           - Emil: cost in metadata and batch streaming done; GPT-4.1 works end-to-end
           - Gideon raises PR 632 blockers and whether they're grind-related
           - Emil: not critical path; can land in next pass
    
    On the agenda: Anthropic casting bug scope; Gemini ordering — batch-mode sweep closed; What's left in the grind
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Both landing workstreams confirmed stable; provider integrations clean; Gideon has clarity on PR 632 unblock timing
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. the gemini ordering fix and anthropic token fix; cost accounting status
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Anthropic token bug is anthropic-only, not cascading
      2. Batch-mode sweep closed by ordering root cause fix   *** MUST RAISE ***
      3. April grind status clear; Gideon Halloway's batch-update PR path visible   *** MUST RAISE ***
    goal        Batch-mode sweep closed by ordering root cause fix
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. the casting bug details and whether it cascades
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Anthropic token bug is anthropic-only, not cascading   *** MUST RAISE ***
      2. Batch-mode sweep closed by ordering root cause fix
      3. April grind status clear; Gideon Halloway's batch-update PR path visible
    goal        Anthropic token bug is anthropic-only, not cascading
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. his blocked PR (PR 632) and whether batch update freq is related
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Anthropic token bug is anthropic-only, not cascading
      2. Batch-mode sweep closed by ordering root cause fix
      3. April grind status clear; Gideon Halloway's batch-update PR path visible
    goal        Three provider-facing commits; two workstreams landing back-to-back
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both landing workstreams confirmed stable; provider integrations clean; Gideon has clarity on PR 632 unblock timing


==============================================================================
# 2025-04-23 — 2 conversation(s), 23 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 9 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs older than median merge time; two owners present need to unblock or redirect

    Today is Wednesday 23 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs older than median merge time; two owners present need to unblock or redirect
    
    What it should get through:
      1. Clear blockers on PR 632 (batch CLI) merge   [Gideon Halloway must raise this]
           - Gideon states where it stands and what's waiting
           - Emil or others surface blocking concerns or dependencies
           - Decision: merge, request changes, or defer
      2. Route PR 643 (response object) to merge or closure   [Emil Brandvold must raise this]
           - Emil outlines what the PR does and why
           - Gideon or Dario raise design or API concerns if any
           - Next step: ready to merge or needs rework
      3. Surface why PR 468 (n-samples) has stalled 75 days   [Emil Brandvold must raise this]
           - Emil or Gideon states the blocker or waiting reason
           - Others confirm whether it is still needed
           - Keep, rebase and try again, or close
    
    On the agenda: PR 632 batch update frequency: current state and blockers; PR 643 response object: scope and dependencies; PR 468 n-samples support: 75 days open, what's stuck
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Two of the three PRs either move to merge or get a clear next step; the team knows what unblocks the third
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - Weekly Notes — Week of Apr 21 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Merge status on batch CLI update; knows what blocks it
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clear blockers on PR 632 (batch CLI) merge   *** MUST RAISE ***
      2. Route PR 643 (response object) to merge or closure
      3. Surface why PR 468 (n-samples) has stalled 75 days
      4. that the doc "Weekly Notes — Week of Apr 21" is done, and where the others can find it   *** MUST RAISE ***
    goal        Clear blockers on PR 632 (batch CLI) merge
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Two open PRs (468, 643) and context on generation params and response object work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clear blockers on PR 632 (batch CLI) merge
      2. Route PR 643 (response object) to merge or closure   *** MUST RAISE ***
      3. Surface why PR 468 (n-samples) has stalled 75 days   *** MUST RAISE ***
    goal        Route PR 643 (response object) to merge or closure
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Two of the three PRs either move to merge or get a clear next step; the team knows what unblocks the third


------------------------------------------------------------------------------
## #pipeline — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Dario Kestrel said in incidents he would look at the fingerprint and this is him looking at it out loud

    Today is Wednesday 23 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel said in incidents he would look at the fingerprint and this is him looking at it out loud
    
    What it should get through:
    
    On the agenda: Dario Kestrel reads out what goes into the key for a code-execution row today, the program text and the test cases, and says that being all of it is why Konrad Feltrin's rerun was free; Emil Brandvold says he has been bitten by the same shape of thing before in a different subsystem and that when the thing doing the work changes underneath, a hit is worse than a miss because it looks like a result; Gideon Halloway asks whether existing on-disk caches would all go cold the day this changes and the thread stalls on nobody wanting to answer that before a release
    
    Wrap when: Dario Kestrel stops short of a change, says he wants Nikolai Berresford in the room and that the invalidation blast radius needs a number before he touches it; it is settled that Emil Brandvold notes the persisted job record does not include the model it was submitted with
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel said in incidents he would look at the fingerprint and this is him looking at it out loud
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel said in incidents he would look at the fingerprint and this is him looking at it out loud
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. the record we keep for a pending job is the id, the request file path and a timestamp. that is it. nothing on disk tells me which model it went out with, so when someone pastes me a run dir I genuinely cannot say whether picking it back up is safe or not. that has bitten me twice this week.   *** MUST SETTLE (clue t3.r2.l_model_emil) ***
    goal        Emil Brandvold notes the persisted job record does not include the model it was submitted with
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel said in incidents he would look at the fingerprint and this is him looking at it out loud
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Dario Kestrel stops short of a change, says he wants Nikolai Berresford in the room and that the invalidation blast radius needs a number before he touches it; it is settled that Emil Brandvold notes the persisted job record does not include the model it was submitted with; Emil Brandvold notes the persisted job record does not include the model it was submitted with


==============================================================================
# 2025-04-24 — 5 conversation(s), 48 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Gideon landed two commits on progress and CLI today, touching core observability; the team needs to align on implications.

    Today is Thursday 24 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon landed two commits on progress and CLI today, touching core observability; the team needs to align on implications.
    
    What it should get through:
      1. Validate batch status tracker progress bar changes   [Gideon Halloway must raise this]
           - Gideon walks through the pbar logic change
           - Emil checks if it affects batch lifecycle tracking
           - Team agrees on any follow-up needed
      2. Confirm CLI test display fix is complete   [Gideon Halloway must raise this]
           - Gideon explains the test failure and fix
           - Emil or Dario spot-check against expected behavior
    
    On the agenda: Gideon's pbar updates for batch status tracking; CLI test display fix and validation; Any ripple effects on monitoring or observability
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon's commits are validated; team is confident in the batch and CLI changes. No blocking issues identified.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - Weekly Notes — Week of Apr 21 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. hands-on fixes to pbar and CLI test display
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate batch status tracker progress bar changes   *** MUST RAISE ***
      2. Confirm CLI test display fix is complete   *** MUST RAISE ***
      3. what "Weekly Notes — Week of Apr 21" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate batch status tracker progress bar changes
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on how batch status tracking integrates with the request layer
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate batch status tracker progress bar changes
      2. Confirm CLI test display fix is complete
    goal        Gideon landed two commits on progress and CLI today, touching core observability; the team needs to align on implications.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. perspective on how progress display affects user experience across job types
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate batch status tracker progress bar changes
      2. Confirm CLI test display fix is complete
    goal        Gideon landed two commits on progress and CLI today, touching core observability; the team needs to align on implications.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon's commits are validated; team is confident in the batch and CLI changes. No blocking issues identified.


------------------------------------------------------------------------------
## #pipeline — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon's commit touches online-request-processing; Emil and Gideon need to sync on batch observability.

    Today is Thursday 24 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon's commit touches online-request-processing; Emil and Gideon need to sync on batch observability.
    
    What it should get through:
      1. Ensure batch job status tracking remains accurate after pbar update   [Gideon Halloway must raise this]
           - Gideon describes the change to batch status tracker pbar
           - Emil confirms no breakage in request layer integration
    
    On the agenda: Review pbar updates for batch status tracking; Confirm no regressions in batch lifecycle monitoring
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Batch status tracking validated; any edge cases in lifecycle handling identified and planned.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. direct knowledge of the pbar and batch status tracker implementation
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Ensure batch job status tracking remains accurate after pbar update   *** MUST RAISE ***
    goal        Ensure batch job status tracking remains accurate after pbar update
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. understanding of how the request layer integrates with progress tracking
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Ensure batch job status tracking remains accurate after pbar update
    goal        Gideon's commit touches online-request-processing; Emil and Gideon need to sync on batch observability.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Batch status tracking validated; any edge cases in lifecycle handling identified and planned.


------------------------------------------------------------------------------
## #viewer — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Gideon's pbar commit affects progress-and-cli; Viewer channel needs to see the change.

    Today is Thursday 24 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon's pbar commit affects progress-and-cli; Viewer channel needs to see the change.
    
    What it should get through:
      1. Validate pbar display is accurate and user-facing progress readout is unchanged   [Gideon Halloway must raise this]
           - Gideon walks through the pbar update logic
           - Emil checks against expected viewer behavior
    
    On the agenda: Review pbar fix for accuracy and clarity; Validate end-to-end progress display behavior
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Pbar fix is confirmed safe; progress display is consistent with viewer expectations.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. direct implementation of the pbar fix
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate pbar display is accurate and user-facing progress readout is unchanged   *** MUST RAISE ***
    goal        Validate pbar display is accurate and user-facing progress readout is unchanged
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on viewer surface expectations
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate pbar display is accurate and user-facing progress readout is unchanged
    goal        Gideon's pbar commit affects progress-and-cli; Viewer channel needs to see the change.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Pbar fix is confirmed safe; progress display is consistent with viewer expectations.


------------------------------------------------------------------------------
## #code-review — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Dario Kestrel put up a first pass that reads batch_objects.jsonl on startup and reattaches by id

    Today is Thursday 24 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel put up a first pass that reads batch_objects.jsonl on startup and reattaches by id
    
    What it should get through:
    
    On the agenda: Dermot Callaghan flags that the draft keys on the dataset path and nothing else, and tells the story of bumping max_tokens on a rerun and getting the shorter completions handed straight back to him; Emil Brandvold on his RAFT run: he changed the response_format schema between two runs and the resumed batch produced rows the new parser could not read, which he says cost him a whole evening of thinking his parser was broken; Gideon Halloway points out the draft resubmits any batch that is not in-progress, and that he paid twice for one that had already completed while the process was down
    
    Wrap when: draft not approved; Dario Kestrel takes the key question and the terminal-state question away separately, and says he will list what states each provider can hand back; it is settled that the team agrees a swallowed cache-write failure must instead be surfaced as a warning naming the path
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel put up a first pass that reads batch_objects.jsonl on startup and reattaches by id
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel put up a first pass that reads batch_objects.jsonl on startup and reattaches by id
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel put up a first pass that reads batch_objects.jsonl on startup and reattaches by id
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Adjacent gripe. The one place we do already wrap a cache write in try/except, the except body is a bare pass. Burned an hour last week wondering why a rerun redid everything from scratch; the write had failed on a permissions thing on a mounted dir and we never said one word about it. If we're going to carry on regardless then it needs to come out at warning level with the path in it, otherwise it's indistinguishable from the cache just not working.   *** MUST SETTLE (clue t3.r1.L10) ***
    goal        the team agrees a swallowed cache-write failure must instead be surfaced as a warning naming the path
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   draft not approved; Dario Kestrel takes the key question and the terminal-state question away separately, and says he will list what states each provider can hand back; it is settled that the team agrees a swallowed cache-write failure must instead be surfaced as a warning naming the path


------------------------------------------------------------------------------
## #releases — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: the weekly cut is Thursday and Nikolai Berresford wants to know whether the pinning change can ride along

    Today is Thursday 24 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: the weekly cut is Thursday and Nikolai Berresford wants to know whether the pinning change can ride along
    
    What it should get through:
    
    On the agenda: Dermot Callaghan says the thing that annoys him about silent image movement is that a user cannot look at anything and see why their verifier numbers moved between two curator versions, and that a version change here has to be visible in the same place every other behaviour change is; Emil Brandvold asks how often the sandbox image publishes and whether bumping it is a patch or a minor for bespokelabs-curator; Nikolai Berresford says he will ask the sandbox side what tags they keep alive and for how long before anyone picks a number
    
    Wrap when: the tag value is still blank; agreement that whatever the bump mechanism is, it happens deliberately in a PR and not by a daemon pulling overnight; it is settled that the team agrees v0.1.7 is the build everything verified runs on
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: v0.1.7.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        the weekly cut is Thursday and Nikolai Berresford wants to know whether the pinning change can ride along
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        the weekly cut is Thursday and Nikolai Berresford wants to know whether the pinning change can ride along
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. For what it is worth the docker backend smoke test has been running against v0.1.7 since February and it is the last build I would personally call safe. Everything we have actually verified end to end sits on that one.   *** MUST SETTLE (clue t4.r1.L5) ***
         must contain literally: v0.1.7
    goal        the team agrees v0.1.7 is the build everything verified runs on
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        the weekly cut is Thursday and Nikolai Berresford wants to know whether the pinning change can ride along
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   the tag value is still blank; agreement that whatever the bump mechanism is, it happens deliberately in a PR and not by a daemon pulling overnight; it is settled that the team agrees v0.1.7 is the build everything verified runs on

