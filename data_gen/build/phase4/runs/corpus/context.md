# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-11-25 — 4 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Ten PRs older than the era median merge time; two release cuts in flight need to unblock

    Today is Monday 25 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Ten PRs older than the era median merge time; two release cuts in flight need to unblock
    
    What it should get through:
      1. Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)   [Dario Kestrel must raise this]
           - Dario Kestrel raises that both are 12 days old and blocking his own work
           - Dermot Callaghan notes neither is on the critical path for v0.1.10
           - group agrees to defer pending example pipeline completion
      2. Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship   [Gideon Halloway must raise this]
           - Gideon Halloway flags PR 141 as 7 days old and blocking his structured output examples
           - Gideon Halloway flags PR 163 as ready to merge; viewer improvements
           - Dermot Callaghan and Dario Kestrel approve both for merge
      3. Land PR 106 (text message summarization example) or identify what's missing   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes it's 11 days old
           - Gideon Halloway reviews diff; asks if it needs the new LiteLLM backend to run
           - group agrees to land if no dependency on PR 141
    
    On the agenda: Review and triage the six oldest PRs; Identify which are blockers for v0.1.10/v0.1.11; Separate cosmetic from functional changes
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: At least 3 of the 6 stale PRs move to merged or deferred; PR 141 and PR 163 clear for v0.1.11; release cut unblocked
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - v0.1.9.post1 release notes (Dario Kestrel)
      - postmortem-2024-11-23 (Gideon Halloway)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 156: Bump aiohttp from 3.10.10 to 3.10.11 (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two fresh commits on resume display and litellm examples; owns the v0.1.10 and v0.1.11 releases
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)
      2. Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship   *** MUST RAISE ***
      3. Land PR 106 (text message summarization example) or identify what's missing
      4. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns bulk-llm-inference, caching, online-request-processing; sees the shape of what's blocking
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)   *** MUST RAISE ***
      2. Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship
      3. Land PR 106 (text message summarization example) or identify what's missing
      4. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just merged the v0.1.9 release; knows the stable baseline
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)
      2. Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship
      3. Land PR 106 (text message summarization example) or identify what's missing
    goal        Ten PRs older than the era median merge time; two release cuts in flight need to unblock
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective on examples and curation design
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Merge or defer PR 78 (vLLM example) and PR 90 (disable cache arg)
      2. Clear PR 141 (LiteLLM+instructor) and PR 163 (viewer cache) so v0.1.11 can ship
      3. Land PR 106 (text message summarization example) or identify what's missing   *** MUST RAISE ***
      4. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 106 (text message summarization example) or identify what's missing
    available   around today

### 4. How it should land

    lands as  partial
    leaving   At least 3 of the 6 stale PRs move to merged or deferred; PR 141 and PR 163 clear for v0.1.11; release cut unblocked


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon's two commits touch core request processing; two release cuts in flight need to confirm safety

    Today is Monday 25 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon's two commits touch core request processing; two release cuts in flight need to confirm safety
    
    What it should get through:
      1. Approve resume pbar display and default timeout for v0.1.10   [Gideon Halloway must raise this]
           - Gideon Halloway walks through the pbar fix; notes it improves user visibility on resumed jobs
           - Dario Kestrel checks for side effects on long-running requests
           - Dermot Callaghan: diff looks safe, LGTM once CI passes
      2. Confirm no provider backend regressions from litellm example addition   [Dario Kestrel must raise this]
           - Gideon Halloway notes the new litellm example is in cookbooks, not core
           - Dario Kestrel confirms examples don't affect main request layer
           - group agrees to ship
    
    On the agenda: Review resume display and timeout changes; Confirm safety for v0.1.10 release; Discuss any provider backend concerns
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon's two commits approved for v0.1.10; release cut unblocked; no provider backend concerns
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - v0.1.9.post1 release notes (Dario Kestrel)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 156: Bump aiohttp from 3.10.10 to 3.10.11 (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two commits: resume pbar display fix and default timeout. Fresh litellm example. Sees what's broken in request layer
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Approve resume pbar display and default timeout for v0.1.10   *** MUST RAISE ***
      2. Confirm no provider backend regressions from litellm example addition
      3. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Approve resume pbar display and default timeout for v0.1.10
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns caching and resume; knows which issues are critical vs. nice-to-have
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve resume pbar display and default timeout for v0.1.10
      2. Confirm no provider backend regressions from litellm example addition   *** MUST RAISE ***
      3. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm no provider backend regressions from litellm example addition
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Founder engineer; just landed the v0.1.9 merge; knows the stable baseline
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Approve resume pbar display and default timeout for v0.1.10
      2. Confirm no provider backend regressions from litellm example addition
    goal        Gideon's two commits touch core request processing; two release cuts in flight need to confirm safety
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon's two commits approved for v0.1.10; release cut unblocked; no provider backend concerns


------------------------------------------------------------------------------
## #general — 6 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Weekly update and postmortem due today; three release cuts in flight

    Today is Monday 25 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Weekly update and postmortem due today; three release cuts in flight
    
    What it should get through:
      1. Post weekly update covering Nov 18–25 work and release status   [Konrad Feltrin must raise this]
           - Konrad Feltrin drafts the update; summarizes the week's themes
           - Gideon Halloway and Dario Kestrel add release notes
           - team replies with blockers or concerns
      2. Share Nov 23 postmortem: what reverted, why, and how it's fixed   [Gideon Halloway must raise this]
           - Gideon Halloway posts the postmortem doc
           - Gideon Halloway summarizes: reverted to old litellm backend with stability fixes
           - team acknowledges; no follow-up action needed
    
    On the agenda: Post weekly update for week of Nov 18; Share postmortem: Nov 23 LiteLLM revert and fixes; Brief status on v0.1.10, v0.1.11, v0.1.12 releases
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Weekly update posted; postmortem shared; team has visibility on release cadence and backend stability
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - weekly-2024-11-18 (Konrad Feltrin)
      - Weekly notes: week of Nov 18 - v0.1.9.post1 out (Gideon Halloway)
      - Postmortem: Nov 19 hotfix (v0.1.9.post1) (Gideon Halloway)
      - v0.1.9.post1 release notes (Dario Kestrel)
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - v0.1.9.post1 release notes (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 156: Bump aiohttp from 3.10.10 to 3.10.11 (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective; owns examples and curation platform
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Post weekly update covering Nov 18–25 work and release status   *** MUST RAISE ***
      2. Share Nov 23 postmortem: what reverted, why, and how it's fixed
      3. that "Weekly update: week of Nov 18" has gone out, and what you asked in it   *** MUST RAISE ***
      4. what "Weekly notes: week of Nov 18 - v0.1.9.post1 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Postmortem: Nov 19 hotfix (v0.1.9.post1)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Post weekly update covering Nov 18–25 work and release status
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just cut v0.1.11; has postmortem on Nov 23 revert
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Post weekly update covering Nov 18–25 work and release status
      2. Share Nov 23 postmortem: what reverted, why, and how it's fixed   *** MUST RAISE ***
      3. that the doc "Postmortem: Nov 23 revert to old LiteLLM backend" is done, and where the others can find it   *** MUST RAISE ***
      4. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Share Nov 23 postmortem: what reverted, why, and how it's fixed
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request processing; sees the pipeline health
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Post weekly update covering Nov 18–25 work and release status
      2. Share Nov 23 postmortem: what reverted, why, and how it's fixed
    goal        Weekly update and postmortem due today; three release cuts in flight
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Recently landed v0.1.9; knows what's stable
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Post weekly update covering Nov 18–25 work and release status
      2. Share Nov 23 postmortem: what reverted, why, and how it's fixed
    goal        Weekly update and postmortem due today; three release cuts in flight
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Weekly update posted; postmortem shared; team has visibility on release cadence and backend stability


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Two commits landed overnight; two release cuts need coordination; backlog of stale PRs needs triage

    Today is Monday 25 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two commits landed overnight; two release cuts need coordination; backlog of stale PRs needs triage
    
    What it should get through:
      1. Confirm resume pbar and timeout commits are ready for v0.1.10   [Gideon Halloway must raise this]
           - Gideon Halloway walks through the commits; explains the pbar fix improves user experience on resume
           - Dario Kestrel and Dermot Callaghan skim diffs; no concerns
           - group agrees commits are safe for the release
      2. Sequence three concurrent releases without conflicts   [Dario Kestrel must raise this]
           - Dario Kestrel notes all three are mid-flight; Gideon Halloway owns first two, Dario Kestrel the third
           - team confirms no dependency conflicts
           - group agrees to merge releases in order: v0.1.10 first, then v0.1.11, then v0.1.12
      3. Triage six stale PRs: defer non-blockers, merge quick wins   [Dario Kestrel must raise this]
           - Dario Kestrel lists the six oldest: PR 78, PR 90, PR 106, PR 141, PR 156, PR 161
           - Gideon Halloway flags PR 141 and PR 163 as blockers for his releases
           - group agrees to focus code-review on those four; defer the rest
    
    On the agenda: Brief on Gideon's two commits and their scope; Coordinate release sequencing: v0.1.10, v0.1.11, v0.1.12; Flag stale PRs blocking forward progress
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon's commits approved; release sequence confirmed; code-review priorities set for the day
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - v0.1.9.post1 release notes (Dario Kestrel)
      - v0.1.9.post1 release notes (Dario Kestrel)
      - Onboarding: Otto Brennan on install UX & README polish (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 156: Bump aiohttp from 3.10.10 to 3.10.11 (Millrow Refactor Bot)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Two commits on resume display and timeout defaults; driving two releases; owns observability
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm resume pbar and timeout commits are ready for v0.1.10   *** MUST RAISE ***
      2. Sequence three concurrent releases without conflicts
      3. Triage six stale PRs: defer non-blockers, merge quick wins
      4. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm resume pbar and timeout commits are ready for v0.1.10
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing ownership; sees the full backlog of open issues and PRs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm resume pbar and timeout commits are ready for v0.1.10
      2. Sequence three concurrent releases without conflicts   *** MUST RAISE ***
      3. Triage six stale PRs: defer non-blockers, merge quick wins   *** MUST RAISE ***
      4. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Onboarding: otto on install UX & README polish" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Sequence three concurrent releases without conflicts
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just merged v0.1.9; knows the baseline; owns bulk-llm-inference and examples
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm resume pbar and timeout commits are ready for v0.1.10
      2. Sequence three concurrent releases without conflicts
      3. Triage six stale PRs: defer non-blockers, merge quick wins
    goal        Two commits landed overnight; two release cuts need coordination; backlog of stale PRs needs triage
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon's commits approved; release sequence confirmed; code-review priorities set for the day


==============================================================================
# 2024-11-26 — 3 conversation(s), 31 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 10 PRs older than the era median merge; 3 opened today; need to unblock the queue

    Today is Tuesday 26 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 10 PRs older than the era median merge; 3 opened today; need to unblock the queue
    
    What it should get through:
      1. Identify what's holding up Gideon Halloway's three stale PRs   [Gideon Halloway must raise this]
           - Gideon says which need review vs which need rework
           - Dermot or Konrad Feltrin volunteer to review the ready ones
           - Plan rework timelines for the blocked ones
      2. Get Dario Kestrel's blocking PRs moving   [Dario Kestrel must raise this]
           - Dario states what he needs: review, feedback, or unblock signal
           - Gideon or Dermot Callaghan commit to review
           - Agree on which can land after v0.1.10
      3. send Weekly update: week of Nov 18   [Dermot Callaghan must raise this]
           - Dermot Callaghan says they will send Weekly update: week of Nov 18
    
    On the agenda: What's blocking Gideon Halloway's PR 141, PR 161, PR 163; Dario's PR 78 and PR 90: vLLM example and cache disabling; Konrad's PR 106: text message summarization example; Triage: what can land before next release; Weekly update: week of Nov 18
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear owners and timelines for each stale PR; at least two moved to review-ready or merged; it is settled that cache lookup and cache_stats are computed from the input row hash so they need only the dataset
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 83 changes merged to date

    On the table
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. owns three of the stale PRs (141, 161, 163) and knows their status
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Identify what's holding up Gideon Halloway's three stale PRs   *** MUST RAISE ***
      2. Get Dario Kestrel's blocking PRs moving
      3. send Weekly update: week of Nov 18
      4. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Identify what's holding up Gideon Halloway's three stale PRs
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on vLLM and caching disables
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Identify what's holding up Gideon Halloway's three stale PRs
      2. Get Dario Kestrel's blocking PRs moving   *** MUST RAISE ***
      3. send Weekly update: week of Nov 18
      4. Worth writing down why the row hash is the right level for this. Keying on the row means resume and cache lookup need nothing but the dataset itself, no prompt callable, no live LLM object, so I can rebuild the whole hit/miss picture from the metadata DB on a cold process. That is exactly what cache_stats needs to be cheap. If the key depended on anything we can only compute by constructing the LLM, cache_stats stops being a thing you can call before a run and becomes another run.   *** MUST SETTLE (clue t1.r1.h2) ***
      5. that the doc "v0.1.10 release notes" is done, and where the others can find it   *** MUST RAISE ***
      6. that "v0.1.10 is out" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Get Dario Kestrel's blocking PRs moving
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. README context; can review non-blocking PRs
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Identify what's holding up Gideon Halloway's three stale PRs
      2. Get Dario Kestrel's blocking PRs moving
      3. send Weekly update: week of Nov 18
    goal        10 PRs older than the era median merge; 3 opened today; need to unblock the queue
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. can spot integration issues in request processing
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Identify what's holding up Gideon Halloway's three stale PRs
      2. Get Dario Kestrel's blocking PRs moving
      3. send Weekly update: week of Nov 18   *** MUST RAISE ***
    goal        send Weekly update: week of Nov 18
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear owners and timelines for each stale PR; at least two moved to review-ready or merged; it is settled that cache lookup and cache_stats are computed from the input row hash so they need only the dataset


------------------------------------------------------------------------------
## #engineering — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: v0.1.10 released today; team gathers to sync on what's next

    Today is Tuesday 26 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.10 released today; team gathers to sync on what's next
    
    What it should get through:
      1. Reflect on what v0.1.10 taught us   [Gideon Halloway must raise this]
           - Gideon runs through the final stretch
           - Dermot notes any integration surprises
           - Konrad flags docs or examples gaps
      2. Settle priorities for the next batch   [Dario Kestrel must raise this]
           - Gideon proposes direction
           - Dario pushes on request-processing debt
           - Team agrees on one or two services to focus
    
    On the agenda: v0.1.10 is out: what was the main blocker or gap; Clear cache PR and other small opens: blockers or nice-to-have; Direction: which service gets focus in the next sprint
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team aligned on what v0.1.10 surfaced and what the next sprint prioritizes
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 83 changes merged to date

    On the table
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just shipped the release; knows what's next
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Reflect on what v0.1.10 taught us   *** MUST RAISE ***
      2. Settle priorities for the next batch
      3. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Reflect on what v0.1.10 taught us
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. knows the request-processing debt and what came up during the v0.1.10 cycle
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Reflect on what v0.1.10 taught us
      2. Settle priorities for the next batch   *** MUST RAISE ***
    goal        Settle priorities for the next batch
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. README and examples perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Reflect on what v0.1.10 taught us
      2. Settle priorities for the next batch
    goal        v0.1.10 released today; team gathers to sync on what's next
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. recently landed the LLM core; sees what's next
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Reflect on what v0.1.10 taught us
      2. Settle priorities for the next batch
    goal        v0.1.10 released today; team gathers to sync on what's next
    available   around today

  Otto Brennan  (otto)
    role        Contributor — Install UX & README Polish. testing and setup UX perspective
    owns        (nothing specific)
    agenda
      1. Reflect on what v0.1.10 taught us
      2. Settle priorities for the next batch
    goal        v0.1.10 released today; team gathers to sync on what's next
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team aligned on what v0.1.10 surfaced and what the next sprint prioritizes


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon merged three changes to rate limiting and retry logic in the request pipeline

    Today is Tuesday 26 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon merged three changes to rate limiting and retry logic in the request pipeline
    
    What it should get through:
      1. Confirm token rate limiting behavior is safe to ship   [Gideon Halloway must raise this]
           - Gideon walks through the status tracker changes
           - Dermot asks about queue stalls or fairness
           - Dario notes any compatibility concerns with existing scripts
      2. Clarify parallel retry semantics   [Gideon Halloway must raise this]
           - Gideon explains when parallel retry fires
           - Dermot challenges the failure detection logic
           - Agreement on whether partial results are discarded
    
    On the agenda: Token-based rate limiting (OpenAI-style): how does it integrate with existing request queuing; Parallel retry on LiteLLM: when does it retry, and what happens to partial results; Any provider edge cases we should gate behind feature flags
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon has confidence the rate limiting and retry changes don't have hidden breakage; any edge cases noted for monitoring; it is settled that compatibility is determined by the backend's 400 on the first real request rather than any model list
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 83 changes merged to date

    On the table
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just merged token-based rate limiting and parallel retry logic; knows the design
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm token rate limiting behavior is safe to ship   *** MUST RAISE ***
      2. Clarify parallel retry semantics   *** MUST RAISE ***
      3. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm token rate limiting behavior is safe to ship
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. knows the request layer and can spot edge cases
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm token rate limiting behavior is safe to ship
      2. Clarify parallel retry semantics
      3. On the response_format compatibility question: we are not keeping a table of which models accept a json schema. That list goes stale the week after we write it and then we are the ones rejecting a model that actually works fine. The provider is the source of truth here. Send the request, and if the model can't do structured outputs we get a 400 back with the provider's own wording and surface that to the user as-is. One request's worth of spend is a fair price for not maintaining a whitelist, and the error text is better than anything we'd write ourselves.   *** MUST SETTLE (clue t2.r1.h1) ***
    goal        compatibility is determined by the backend's 400 on the first real request rather than any model list
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. knows request-layer customers and their patterns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm token rate limiting behavior is safe to ship
      2. Clarify parallel retry semantics
    goal        Gideon merged three changes to rate limiting and retry logic in the request pipeline
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon has confidence the rate limiting and retry changes don't have hidden breakage; any edge cases noted for monitoring; it is settled that compatibility is determined by the backend's 400 on the first real request rather than any model list


==============================================================================
# 2024-11-27 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Six commits landed on provider integrations; release v0.1.11 is mid-flight and waiting on signal that this batch is ready.

    Today is Wednesday 27 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six commits landed on provider integrations; release v0.1.11 is mid-flight and waiting on signal that this batch is ready.
    
    What it should get through:
      1. Validate that instructor+liteLLM coverage checks are necessary and sufficient   [Gideon Halloway must raise this]
           - Gideon walks through what happens when instructor or liteLLM are not available
           - Dario asks whether this catches the real failure modes we have seen
           - Landing: agreement that the checks prevent the breakage from the liteLLM revert postmortem
      2. Confirm model init logging is appropriate verbosity for v0.1.11   [Gideon Halloway must raise this]
           - Gideon explains what the logging reveals
           - Dermot questions whether it's noisy in batch mode
           - Landing: understanding that it's init-time only, worth the signal
    
    On the agenda: Instructor + liteLLM coverage guards: what they catch; Model initialization logging: why it matters; Code quality pass: black formatting and commented debug removal
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon's six commits are acknowledged as ready; release v0.1.11 clears that dependency and moves to merge; it is settled that the response cache key is the hash of the raw input row alone
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 83 changes merged to date

    On the table
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Six commits on instructor+liteLLM coverage checks, model init logging, formatting cleanup
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate that instructor+liteLLM coverage checks are necessary and sufficient   *** MUST RAISE ***
      2. Confirm model init logging is appropriate verbosity for v0.1.11   *** MUST RAISE ***
      3. that the doc "Weekly notes: week of Nov 25 - v0.1.10 out" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate that instructor+liteLLM coverage checks are necessary and sufficient
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Familiarity with the request processing layer and what coverage checks matter most
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate that instructor+liteLLM coverage checks are necessary and sufficient
      2. Confirm model init logging is appropriate verbosity for v0.1.11
    goal        Six commits landed on provider integrations; release v0.1.11 is mid-flight and waiting on signal that this batch is ready.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Historical context on why instructor/liteLLM integration exists and what it replaced
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate that instructor+liteLLM coverage checks are necessary and sufficient
      2. Confirm model init logging is appropriate verbosity for v0.1.11
      3. To be clear on the cache key since it came up again in review: it is the hash of the raw input row, full stop. Row in, hash out, that is the whole contract and I want it to stay that narrow. Every time someone folds another thing into a fingerprint we end up with a key nobody can explain to a user who asks why their rerun did what it did. The row is the unit the dataset is made of, so the row is the unit the cache is keyed on. cache_stats should just report against those row hashes and nothing fancier.   *** MUST SETTLE (clue t1.r1.h1) ***
    goal        the response cache key is the hash of the raw input row alone
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon's six commits are acknowledged as ready; release v0.1.11 clears that dependency and moves to merge; it is settled that the response cache key is the hash of the raw input row alone


==============================================================================
# 2024-11-28 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Six PRs have sat longer than the median merge time; two releases are mid-flight and need the queue clear.

    Today is Thursday 28 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six PRs have sat longer than the median merge time; two releases are mid-flight and need the queue clear.
    
    What it should get through:
      1. Unblock or defer PR 141 (LiteLLM+instructor)   [Gideon Halloway must raise this]
           - Gideon raises it as blocking structured output work
           - Konrad or Dario pushes back on scope or priority
           - Either approve with conditions or defer to post-release
      2. Move PR 78 and 90 (vLLM and cache) toward landing   [Dario Kestrel must raise this]
           - Dario describes what's holding them
           - Gideon and Konrad assess whether they block a release
           - Either approve or agree on what's needed to proceed
      3. Establish review bandwidth for remaining queue   [Konrad Feltrin must raise this]
           - Konrad or Dario volunteers to drive the remaining reviews
           - Group agrees on priority order
           - Assign owners or decide what can wait until next week
    
    On the agenda: Review oldest stalled PRs; Identify blockers on structured output and examples; Clear path to merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: At least one PR approved and merged; clear signal on whether the rest block the two active releases or can be deferred.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 83 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. knowledge of the viewer and structured output work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock or defer PR 141 (LiteLLM+instructor)   *** MUST RAISE ***
      2. Move PR 78 and 90 (vLLM and cache) toward landing
      3. Establish review bandwidth for remaining queue
    goal        Unblock or defer PR 141 (LiteLLM+instructor)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on vLLM integration and cache control
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock or defer PR 141 (LiteLLM+instructor)
      2. Move PR 78 and 90 (vLLM and cache) toward landing   *** MUST RAISE ***
      3. Establish review bandwidth for remaining queue
    goal        Move PR 78 and 90 (vLLM and cache) toward landing
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. ownership of examples and ability to unblock Dario's stalled work
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock or defer PR 141 (LiteLLM+instructor)
      2. Move PR 78 and 90 (vLLM and cache) toward landing
      3. Establish review bandwidth for remaining queue   *** MUST RAISE ***
    goal        Establish review bandwidth for remaining queue
    available   around today

### 4. How it should land

    lands as  partial
    leaving   At least one PR approved and merged; clear signal on whether the rest block the two active releases or can be deferred.


==============================================================================
# 2024-12-02 — 3 conversation(s), 21 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 141 has been under heavy review for 14 days with 12 comments from Dario Kestrel in a single day; something needs to break the jam

    Today is Monday 2 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 141 has been under heavy review for 14 days with 12 comments from Dario Kestrel in a single day; something needs to break the jam
    
    What it should get through:
      1. Understand what's blocking the LiteLLM+instructor merge   [Dario Kestrel must raise this]
           - Dario lays out the pattern in the review comments
           - Gideon pushes back on scope or asks for clarification
           - They land on whether this is design-level or implementation-level
      2. send Weekly update: week of Nov 25   [Gideon Halloway must raise this]
           - Gideon Halloway says they will send Weekly update: week of Nov 25
    
    On the agenda: Dario's 12 review rounds: what's blocking; Gideon's response: design or implementation; Next steps: rework or split; Weekly update: week of Nov 25
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Either Gideon starts a rework iteration, or they agree to split the PR and land a subset, or Dario Kestrel gives explicit approval to merge.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 90 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 12 rounds of review comments on the LiteLLM+instructor integration; knows the structured-output requirements
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Understand what's blocking the LiteLLM+instructor merge   *** MUST RAISE ***
      2. send Weekly update: week of Nov 25
    goal        Understand what's blocking the LiteLLM+instructor merge
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. authored the PR; knows the instructor integration details and what the reviews are asking for
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Understand what's blocking the LiteLLM+instructor merge
      2. send Weekly update: week of Nov 25   *** MUST RAISE ***
      3. that "Weekly update: week of Nov 25" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Nov 25
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Either Gideon starts a rework iteration, or they agree to split the PR and land a subset, or Dario Kestrel gives explicit approval to merge.


------------------------------------------------------------------------------
## #pipeline — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon committed a cleanup this morning; the team checks that it landed clean

    Today is Monday 2 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon committed a cleanup this morning; the team checks that it landed clean
    
    What it should get through:
      1. Confirm the import cleanup has no side effects   [Gideon Halloway must raise this]
           - Gideon explains what imports were unused and why safe to remove
           - Dario confirms test coverage
           - They move on if CI is green
    
    On the agenda: Gideon's import cleanup: scope and impact; CI status and test coverage; Any follow-up cleanup needed
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: The cleanup is confirmed safe, or a revert is flagged if tests fail.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 90 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just landed a cleanup commit removing unused imports across five core services
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm the import cleanup has no side effects   *** MUST RAISE ***
    goal        Confirm the import cleanup has no side effects
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. owns the services touched; will see if CI is green
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm the import cleanup has no side effects
    goal        Gideon committed a cleanup this morning; the team checks that it landed clean
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   The cleanup is confirmed safe, or a revert is flagged if tests fail.


------------------------------------------------------------------------------
## #engineering — 7 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario opened two new issues this morning that may affect batch stability; the team needs to assess priority

    Today is Monday 2 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario opened two new issues this morning that may affect batch stability; the team needs to assess priority
    
    What it should get through:
      1. Assess whether the new batch issues block the two pending releases   [Dario Kestrel must raise this]
           - Dario describes the space and cache-key issues
           - Gideon offers context from recent commits
           - They decide if these are release-critical or can land after
    
    On the agenda: Issue PR 189: Out of Space error on OpenAI servers; Issue PR 190: Add the OpenAI key to the cache hash for batch mode; Whether these block the releases
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clear priority: either the issues are added to the release checklist, or they are marked as post-release work.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 90 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 33: Check cache for batch=True completions and skip downloading results files if they exist
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM

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
      - — and 1273 function/class names and 183 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. just opened two new issues on the batch workflow: cache-key problems and space errors on OpenAI
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Assess whether the new batch issues block the two pending releases   *** MUST RAISE ***
    goal        Assess whether the new batch issues block the two pending releases
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. watched batch commits land over the weekend; may have insights on the space error
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Assess whether the new batch issues block the two pending releases
    goal        Dario opened two new issues this morning that may affect batch stability; the team needs to assess priority
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear priority: either the issues are added to the release checklist, or they are marked as post-release work.

