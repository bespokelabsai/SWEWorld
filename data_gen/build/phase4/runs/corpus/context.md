# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-11-19 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.9.post1 hotfix shipped today; release notes due and announcement to be sent

    Today is Tuesday 19 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.9.post1 hotfix shipped today; release notes due and announcement to be sent
    
    What it should get through:
      1. Lock release notes for v0.1.9.post1   [Dario Kestrel must raise this]
           - Dario Kestrel lays out the commits
           - Konrad Feltrin checks coverage
           - Dermot Callaghan confirms nothing is missing
      2. Send announcement mail to team   [Dario Kestrel must raise this]
           - Dario Kestrel drafts it
           - Konrad Feltrin reviews tone
           - Dermot Callaghan hits send
    
    On the agenda: What went into v0.1.9.post1; Release notes and changelog; Announce to users
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.9.post1 release notes published and announcement sent to users; hot fix locked in place
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 77 changes merged to date

    On the table
      - v0.1.9.post1 release notes (Dario Kestrel)
      - v0.1.9 release notes (Dario Kestrel)
      - announce-v0-1-9-post1 (Dario Kestrel)
      - release-v0-1-9-post1 (Dario Kestrel)
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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. release-notes content and decision on what the post1 covers
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Lock release notes for v0.1.9.post1   *** MUST RAISE ***
      2. Send announcement mail to team   *** MUST RAISE ***
      3. that the doc "v0.1.9.post1 release notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.9.post1 hotfix is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "v0.1.9 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "v0.1.9.post1 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Lock release notes for v0.1.9.post1
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. maintainer sign-off and release process oversight
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Lock release notes for v0.1.9.post1
      2. Send announcement mail to team
    goal        v0.1.9.post1 hotfix shipped today; release notes due and announcement to be sent
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. merge and shipping context
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Lock release notes for v0.1.9.post1
      2. Send announcement mail to team
    goal        v0.1.9.post1 hotfix shipped today; release notes due and announcement to be sent
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.9.post1 release notes published and announcement sent to users; hot fix locked in place


------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 2 PRs opened today, 2 merged, 7 PRs older than median merge time; examples and docs riding through release

    Today is Tuesday 19 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 2 PRs opened today, 2 merged, 7 PRs older than median merge time; examples and docs riding through release
    
    What it should get through:
      1. Get eyes on PR 149 viewer and logging PR   [Gideon Halloway must raise this]
           - Gideon Halloway posts context
           - Konrad Feltrin and Dario Kestrel scan for issues
           - team agrees merge-ready or suggests changes
      2. Clear path on stale examples PRs   [Konrad Feltrin must raise this]
           - Konrad Feltrin flags PR 39 and PR 106 status
           - Dario Kestrel and Dermot Callaghan state blockers for PR 78 PR 90 PR 130
           - team decides triage or defer
    
    On the agenda: New PR PR 149 from today; Aging examples PRs backlog; Path forward on blocked work
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 149 queued for merge; clarity on which examples PRs can land this week vs deferred to next
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 77 changes merged to date

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. heavy commit context from today's viewer and logging work; new PR PR 149 ready for review
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Get eyes on PR 149 viewer and logging PR   *** MUST RAISE ***
      2. Clear path on stale examples PRs
    goal        Get eyes on PR 149 viewer and logging PR
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. maintainer review and examples ownership
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get eyes on PR 149 viewer and logging PR
      2. Clear path on stale examples PRs   *** MUST RAISE ***
    goal        Clear path on stale examples PRs
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. vLLM and cache disable feature thinking
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get eyes on PR 149 viewer and logging PR
      2. Clear path on stale examples PRs
    goal        2 PRs opened today, 2 merged, 7 PRs older than median merge time; examples and docs riding through release
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. teacher.py refactor rationale
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Get eyes on PR 149 viewer and logging PR
      2. Clear path on stale examples PRs
    goal        2 PRs opened today, 2 merged, 7 PRs older than median merge time; examples and docs riding through release
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 149 queued for merge; clarity on which examples PRs can land this week vs deferred to next


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 15 commits today including release merge and heavy viewer/logging work; cache concerns raised

    Today is Tuesday 19 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 15 commits today including release merge and heavy viewer/logging work; cache concerns raised
    
    What it should get through:
      1. Confirm v0.1.9.post1 hotfix scope and impact   [Gideon Halloway must raise this]
           - Gideon Halloway summarizes commits
           - team notes any surprises
           - Dario Kestrel flags if cache issues warrant rollback
      2. Get feedback on viewer timing and distribution PR   [Gideon Halloway must raise this]
           - Gideon Halloway walks through timeseries and dark mode changes
           - Konrad Feltrin weighs in on UX
           - team agrees or defers
      3. Understand cache fingerprint and prompt_func variable issues   [Dario Kestrel must raise this]
           - Dario Kestrel lays out PR 143 and PR 148
           - Gideon Halloway notes viewer implications
           - team triages severity
    
    On the agenda: v0.1.9.post1 shipped; what it covered; Gideon's viewer work and PR 149 direction; Cache issues Dario Kestrel opened and next steps
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Release confirmed shipped safely; viewer direction clear; cache issues triaged and assigned
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 77 changes merged to date

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 14 commits on logging, timing, viewer distribution today; new PR 149 PR
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm v0.1.9.post1 hotfix scope and impact   *** MUST RAISE ***
      2. Get feedback on viewer timing and distribution PR   *** MUST RAISE ***
      3. Understand cache fingerprint and prompt_func variable issues
    goal        Confirm v0.1.9.post1 hotfix scope and impact
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. context from examples and docs integration
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm v0.1.9.post1 hotfix scope and impact
      2. Get feedback on viewer timing and distribution PR
      3. Understand cache fingerprint and prompt_func variable issues
    goal        15 commits today including release merge and heavy viewer/logging work; cache concerns raised
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. maintainer perspective on examples quality and release hygiene
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm v0.1.9.post1 hotfix scope and impact
      2. Get feedback on viewer timing and distribution PR
      3. Understand cache fingerprint and prompt_func variable issues
    goal        15 commits today including release merge and heavy viewer/logging work; cache concerns raised
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. cache and vLLM thinking; issues opened on cache behavior
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm v0.1.9.post1 hotfix scope and impact
      2. Get feedback on viewer timing and distribution PR
      3. Understand cache fingerprint and prompt_func variable issues   *** MUST RAISE ***
    goal        Understand cache fingerprint and prompt_func variable issues
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Release confirmed shipped safely; viewer direction clear; cache issues triaged and assigned


==============================================================================
# 2024-11-20 — 2 conversation(s), 20 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three new PRs opened today, six older ones still waiting; the release workstreams need the queue clear.

    Today is Wednesday 20 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three new PRs opened today, six older ones still waiting; the release workstreams need the queue clear.
    
    What it should get through:
      1. Land Gideon Halloway's cost/token logging PR (PR 159)   [Gideon Halloway must raise this]
           - Gideon Halloway: This adds cost tracking to OpenAI online and LiteLLM batch, using the new `completion_cost` field; Dermot Callaghan: Pattern looks sound, but let me check the integration points against the cache layer
           - Dermot Callaghan: Sign off once CI's green
      2. Decide fate of PR 130 (teacher.py example)   [Dermot Callaghan must raise this]
           - Dermot Callaghan: Still valid, just needs a final pass; Dario Kestrel: Does it block the release? If not, defer to next week
           - Dermot Callaghan: Agrees; defer
      3. Bump and merge PR 156 (aiohttp security)   [Gideon Halloway must raise this]
           - Gideon Halloway: Automation, no review needed; merge once CI passes
    
    On the agenda: Triage the three new PRs (PR 156, PR 159, PR 161); Clear the six stale PRs blocking release
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 159 lands today, PR 156 lands if CI passes. PR 130 deferred to next week. Remaining stale PRs (PR 39, PR 78, PR 90, PR 106, PR 133) still blocking until their owners re-pitch or rework.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 79 changes merged to date

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Shipped two PRs today, knows what's blocking the remaining queue
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land Gideon Halloway's cost/token logging PR (PR 159)   *** MUST RAISE ***
      2. Decide fate of PR 130 (teacher.py example)
      3. Bump and merge PR 156 (aiohttp security)   *** MUST RAISE ***
      4. that the doc "Weekly notes: week of Nov 18 - v0.1.9.post1 out" is done, and where the others can find it   *** MUST RAISE ***
      5. that the doc "Postmortem: Nov 19 hotfix (v0.1.9.post1)" is done, and where the others can find it   *** MUST RAISE ***
    goal        Land Gideon Halloway's cost/token logging PR (PR 159)
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Senior code-review pattern-matching; owns the pipeline layer
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land Gideon Halloway's cost/token logging PR (PR 159)
      2. Decide fate of PR 130 (teacher.py example)   *** MUST RAISE ***
      3. Bump and merge PR 156 (aiohttp security)
    goal        Decide fate of PR 130 (teacher.py example)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing expertise; knows batch mode constraints
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land Gideon Halloway's cost/token logging PR (PR 159)
      2. Decide fate of PR 130 (teacher.py example)
      3. Bump and merge PR 156 (aiohttp security)
    goal        Three new PRs opened today, six older ones still waiting; the release workstreams need the queue clear.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 159 lands today, PR 156 lands if CI passes. PR 130 deferred to next week. Remaining stale PRs (PR 39, PR 78, PR 90, PR 106, PR 133) still blocking until their owners re-pitch or rework.


------------------------------------------------------------------------------
## #pipeline — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Two of today's commits touch bulk-llm-inference, caching-and-resume, online-request-processing, and provider-integrations. The logging work is mid-flight for v0.1.10.

    Today is Wednesday 20 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two of today's commits touch bulk-llm-inference, caching-and-resume, online-request-processing, and provider-integrations. The logging work is mid-flight for v0.1.10.
    
    What it should get through:
      1. Confirm cost tracking is cache-safe   [Gideon Halloway must raise this]
           - Gideon Halloway: Cost field comes from provider response, included in hash; Dermot Callaghan: That means a new provider version changes the cache key — is that intentional? Gideon Halloway: Yes, cost is deterministic per provider, so it's safe to bake into the key
      2. Land PR PR 149 (time logging) into v0.1.10   [Gideon Halloway must raise this]
           - Gideon Halloway: Merged today, CI passed, Dermot Callaghan approved three times (with a changes-requested in between); Dermot Callaghan: Log output looks clean, LGTM
    
    On the agenda: Verify cost/token logging doesn't break resume or cache; Scope v0.1.10 merge to time and cost visibility
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 159 and PR 149 ship as part of v0.1.10. Cache semantics confirmed safe. Release cut once CI clears the rest of the queue.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 79 changes merged to date

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
      - — and 1293 function/class names and 188 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just shipped time logging (PR PR 149); now adding cost/token logging (PR 159); knows the request layer cold
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm cost tracking is cache-safe   *** MUST RAISE ***
      2. Land PR PR 149 (time logging) into v0.1.10   *** MUST RAISE ***
    goal        Confirm cost tracking is cache-safe
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Batch and resume layer expertise; knows what can break cache invalidation
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm cost tracking is cache-safe
      2. Land PR PR 149 (time logging) into v0.1.10
    goal        Two of today's commits touch bulk-llm-inference, caching-and-resume, online-request-processing, and provider-integrations. The logging work is mid-flight for v0.1.10.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 159 and PR 149 ship as part of v0.1.10. Cache semantics confirmed safe. Release cut once CI clears the rest of the queue.


==============================================================================
# 2024-11-21 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs merged, four opened; six PRs older than median merge time; need to unblock stale work before cutting three releases

    Today is Thursday 21 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged, four opened; six PRs older than median merge time; need to unblock stale work before cutting three releases
    
    What it should get through:
      1. Validate dill pickling strategy didn't break serialization   [Gideon Halloway must raise this]
           - Dermot Callaghan explains the dill approach and bytesio changes
           - Gideon Halloway tests it against the viewer serialization path
           - they land on: dill is safe, no follow-up needed
      2. Clarify which stale PRs block which release cuts   [Dario Kestrel must raise this]
           - Dario Kestrel asks if PR 141, PR 78, PR 90 block 0.1.12
           - Gideon Halloway and Dermot Callaghan clarify: PR 141 and PR 161 can defer to 0.1.13
           - Dario Kestrel confirms: 0.1.12 is clear to cut
    
    On the agenda: Merged work: cost/token logging, dill pickling, linting; Pending viewer and example PRs (PR 163, PR 165); Stale PRs and release blocking
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 163 and PR 165 get final sign-off; dill serialization validated; Dario Kestrel knows he can cut 0.1.12 without waiting for PR 141
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - Weekly notes: week of Nov 18 - v0.1.9.post1 out (Gideon Halloway)
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. Just merged PR 159 (cost/token logging) and PR 167/#168 (dill pickling and linting); knows what's in flight on viewer and example PRs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate dill pickling strategy didn't break serialization   *** MUST RAISE ***
      2. Clarify which stale PRs block which release cuts
      3. what "Weekly notes: week of Nov 18 - v0.1.9.post1 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate dill pickling strategy didn't break serialization
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Just landed linting infrastructure (PR 168) and dill pickling (PR 167); can explain the pickling strategy change and why linting matters for consistency
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate dill pickling strategy didn't break serialization
      2. Clarify which stale PRs block which release cuts
    goal        Three PRs merged, four opened; six PRs older than median merge time; need to unblock stale work before cutting three releases
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on PR 78 and PR 90, which are stale and blocking his release work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate dill pickling strategy didn't break serialization
      2. Clarify which stale PRs block which release cuts   *** MUST RAISE ***
    goal        Clarify which stale PRs block which release cuts
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Has two stale PRs (PR 39 and PR 106) that touch examples and docstrings
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Validate dill pickling strategy didn't break serialization
      2. Clarify which stale PRs block which release cuts
    goal        Three PRs merged, four opened; six PRs older than median merge time; need to unblock stale work before cutting three releases
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 163 and PR 165 get final sign-off; dill serialization validated; Dario Kestrel knows he can cut 0.1.12 without waiting for PR 141


==============================================================================
# 2024-11-22 — 1 conversation(s), 10 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR PR 171 just opened; six older PRs are stale and three release workstreams are mid-flight

    Today is Friday 22 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 171 just opened; six older PRs are stale and three release workstreams are mid-flight
    
    What it should get through:
      1. Establish whether Otto's test additions close real gaps or are defensive   [Gideon Halloway must raise this]
           - Gideon Halloway: what does this test that we don't have?
           - Otto Brennan: explains scope
           - Dario Kestrel: proposes we land it and move on
      2. Decide which stale PRs can land before the next release cut   [Dario Kestrel must raise this]
           - Dario Kestrel: notes 78 and 90 are his and they're stale
           - Konrad Feltrin: whether they're release-blocking or next-cycle
           - Dario Kestrel: probably next-cycle, but worth a quick look
    
    On the agenda: Otto's GenericRequest test coverage PR and what it covers; Older PRs blocking release work (78, 90)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Otto's test PR gets a reviewer; team agrees on which stale PRs are release-blocking and which can wait until v0.1.13.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. Understanding of the request layer and what coverage gaps exist
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Establish whether Otto's test additions close real gaps or are defensive   *** MUST RAISE ***
      2. Decide which stale PRs can land before the next release cut
    goal        Establish whether Otto's test additions close real gaps or are defensive
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request processing; knows what GenericRequest needs to cover
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Establish whether Otto's test additions close real gaps or are defensive
      2. Decide which stale PRs can land before the next release cut   *** MUST RAISE ***
    goal        Decide which stale PRs can land before the next release cut
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective on what's core vs nice-to-have in tests
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Establish whether Otto's test additions close real gaps or are defensive
      2. Decide which stale PRs can land before the next release cut
    goal        PR PR 171 just opened; six older PRs are stale and three release workstreams are mid-flight
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Otto's test PR gets a reviewer; team agrees on which stale PRs are release-blocking and which can wait until v0.1.13.


==============================================================================
# 2024-11-23 — 4 conversation(s), 39 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Gideon reverted a significant async litellm change mid-flight, signaling instability that the team needs to understand before it affects releases.

    Today is Saturday 23 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon reverted a significant async litellm change mid-flight, signaling instability that the team needs to understand before it affects releases.
    
    What it should get through:
      1. Establish the old backend is production-ready again   [Gideon Halloway must raise this]
           - Gideon Halloway outlines the revert and why
           - Dermot Callaghan asks whether this blocks the release cuts
    
    On the agenda: What broke with the revamped async litellm; Why the old backend with fixes is more stable; Whether this affects the release pipeline
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands the revert was the right call; releases can proceed on schedule.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. The details of yesterday's checkpoint and today's revert decision
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Establish the old backend is production-ready again   *** MUST RAISE ***
    goal        Establish the old backend is production-ready again
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Perspective on stability vs. feature completeness
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Establish the old backend is production-ready again
    goal        Gideon reverted a significant async litellm change mid-flight, signaling instability that the team needs to understand before it affects releases.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team understands the revert was the right call; releases can proceed on schedule.


------------------------------------------------------------------------------
## #incidents — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: A revert in bulk-llm-inference on the day of multiple release cuts needs explicit incident tracking to avoid cascading into releases.

    Today is Saturday 23 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: A revert in bulk-llm-inference on the day of multiple release cuts needs explicit incident tracking to avoid cascading into releases.
    
    What it should get through:
      1. Mark the incident closed with the revert merged   [Gideon Halloway must raise this]
           - Gideon Halloway posts the revert
           - Dario Kestrel checks for breakage
           - Dermot Callaghan clears it for release
    
    On the agenda: State the revert and its impact; Confirm no downstream breakage; Decide if a hotfix or immediate release is needed
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Incident is resolved; releases can proceed or are held with explicit reasoning.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. The revert commit and its rationale
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Mark the incident closed with the revert merged   *** MUST RAISE ***
    goal        Mark the incident closed with the revert merged
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on any downstream impact to request processing
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Mark the incident closed with the revert merged
    goal        A revert in bulk-llm-inference on the day of multiple release cuts needs explicit incident tracking to avoid cascading into releases.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release coordination perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Mark the incident closed with the revert merged
    goal        A revert in bulk-llm-inference on the day of multiple release cuts needs explicit incident tracking to avoid cascading into releases.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Incident is resolved; releases can proceed or are held with explicit reasoning.


------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Ten PRs are older than the median merge time; Gideon Halloway, Dario Kestrel, and Konrad Feltrin all have work waiting for review, and several are blocking features or hygiene improvements.

    Today is Saturday 23 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Ten PRs are older than the median merge time; Gideon Halloway, Dario Kestrel, and Konrad Feltrin all have work waiting for review, and several are blocking features or hygiene improvements.
    
    What it should get through:
      1. Move oldest PRs toward approval or close-out   [Konrad Feltrin must raise this]
           - Konrad Feltrin or Dario Kestrel skim the PR list
           - Gideon Halloway flags which ones unblock releases
           - Someone takes the first four and leaves detailed feedback
      2. Land cache-disable and vLLM example PRs if they are clean   [Dario Kestrel must raise this]
           - Dario Kestrel walks through his vLLM PR
           - Konrad Feltrin or Gideon Halloway spot issues or approve
    
    On the agenda: Triage the oldest stale PRs by blocker status; Review Gideon Halloway's pending viewer and example PRs; Get approval on Dario Kestrel's feature PRs
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: At least three stale PRs have actionable feedback or merge approval; the blockage starts to clear.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. His own pending PRs and context on what they unblock
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Move oldest PRs toward approval or close-out
      2. Land cache-disable and vLLM example PRs if they are clean
    goal        Ten PRs are older than the median merge time; Gideon Halloway, Dario Kestrel, and Konrad Feltrin all have work waiting for review, and several are blocking features or hygiene improvements.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective on code quality and consistency
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Move oldest PRs toward approval or close-out   *** MUST RAISE ***
      2. Land cache-disable and vLLM example PRs if they are clean
    goal        Move oldest PRs toward approval or close-out
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on the vLLM and cache-disable features
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Move oldest PRs toward approval or close-out
      2. Land cache-disable and vLLM example PRs if they are clean   *** MUST RAISE ***
    goal        Land cache-disable and vLLM example PRs if they are clean
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   At least three stale PRs have actionable feedback or merge approval; the blockage starts to clear.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: The revert of async litellm touches four pipeline services; Dario Kestrel and Gideon Halloway need to confirm the fallback does not break request processing or cost accounting before releases ship.

    Today is Saturday 23 November 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The revert of async litellm touches four pipeline services; Dario Kestrel and Gideon Halloway need to confirm the fallback does not break request processing or cost accounting before releases ship.
    
    What it should get through:
      1. Validate the old backend is safe for production release   [Gideon Halloway must raise this]
           - Gideon Halloway walks through what the revert changes
           - Dario Kestrel checks request routing and cost handling
           - Both confirm provider integrations are stable
    
    On the agenda: Confirm the old litellm backend handles all request types correctly; Check cost and latency tracking are not degraded; Verify provider integrations are stable
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Pipeline team is confident the revert does not degrade production request handling; releases can proceed.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 3 release(s) shipped, currently v0.1.9.post1
      - 82 changes merged to date

    On the table
      - PR 39: Fix minor code issues with incorrect docstring etc. (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)

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
    role        Core Engineer — Dataset Viewer & Run Observability. The revert and its implications for the request pipeline
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate the old backend is safe for production release   *** MUST RAISE ***
    goal        Validate the old backend is safe for production release
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Deep knowledge of request processing and what the pipeline depends on
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate the old backend is safe for production release
    goal        The revert of async litellm touches four pipeline services; Dario Kestrel and Gideon Halloway need to confirm the fallback does not break request processing or cost accounting before releases ship.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Pipeline team is confident the revert does not degrade production request handling; releases can proceed.

