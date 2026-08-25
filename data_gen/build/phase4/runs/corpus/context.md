# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-12-03 — 2 conversation(s), 22 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Gideon has 12 commits refactoring the core request loop; multiple reviewers have left comments on PR 141; batch-mode PR 191 landed today and needs this to be solid

    Today is Tuesday 3 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon has 12 commits refactoring the core request loop; multiple reviewers have left comments on PR 141; batch-mode PR 191 landed today and needs this to be solid
    
    What it should get through:
      1. Agree the refactored request handler shape is sound   [Gideon Halloway must raise this]
           - Gideon walks through the split and why it clarifies retry logic
           - Dario spots the interaction with batch mode caching
           - Consensus that the abstraction holds
      2. Resolve whether logging level changes break anything   [Gideon Halloway must raise this]
           - Gideon explains the new openai logger info level change
           - Dermot flags if this will break any integration tests
           - Defer if needed; doesn't block the refactor
      3. Confirm no resume or cache breakage from the rename   [Dario Kestrel must raise this]
           - Dario asks about temp file write logic after the rename
           - Gideon confirms it's back in place (commit 6daea63)
           - Merge conditional on CI passing
    
    On the agenda: Refactor shape: handle_single_request_with_retries and call_single_request separation; Logging and error handling in base_online_request_processor; Integration risk with batch mode and cache logic
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 141 approved pending green CI; ready to land before v0.1.11 cut
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

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
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM
      - issue 86: Retry when structured output fails

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
    role        Core Engineer — Dataset Viewer & Run Observability. 12 refactoring commits cleaning up the online request processor and adding structured logging
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Agree the refactored request handler shape is sound   *** MUST RAISE ***
      2. Resolve whether logging level changes break anything   *** MUST RAISE ***
      3. Confirm no resume or cache breakage from the rename
    goal        Agree the refactored request handler shape is sound
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the same subsystem; can spot interactions with batch mode and caching
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree the refactored request handler shape is sound
      2. Resolve whether logging level changes break anything
      3. Confirm no resume or cache breakage from the rename   *** MUST RAISE ***
    goal        Confirm no resume or cache breakage from the rename
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Owns bulk-llm-inference; knows the original design intent
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree the refactored request handler shape is sound
      2. Resolve whether logging level changes break anything
      3. Confirm no resume or cache breakage from the rename
    goal        Gideon has 12 commits refactoring the core request loop; multiple reviewers have left comments on PR 141; batch-mode PR 191 landed today and needs this to be solid
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 141 approved pending green CI; ready to land before v0.1.11 cut


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon's 12 commits refactor the core of the online request processor; Dario Kestrel and Gideon Halloway are both driving releases that depend on this landing clean

    Today is Tuesday 3 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon's 12 commits refactor the core of the online request processor; Dario Kestrel and Gideon Halloway are both driving releases that depend on this landing clean
    
    What it should get through:
      1. Confirm the retry abstraction doesn't lose requests or duplicate work   [Gideon Halloway must raise this]
           - Gideon walks the new call_single_request → handle_single_request_with_retries flow
           - Dario asks about backpressure when capacity runs out (commit 4a213cb)
           - Consensus that logging is clearer but behavior is the same
      2. Check that logging changes don't mask failures in batch/provider integrations   [Dario Kestrel must raise this]
           - Dario flags the openai logger level change
           - Gideon explains it's info not debug, so real problems still surface
           - Merge if test coverage exists
      3. Verify resume and caching still work after the rename   [Gideon Halloway must raise this]
           - Gideon notes the resume logging and temp write logic are back (commits 6daea63, 5f0d83)
           - Dario asks about the cache hash in batch mode (PR 191)
           - Land together; no blockers
    
    On the agenda: Behavior of handle_single_request_with_retries under load; Capacity logging and backpressure signaling; Resume and temp-file lifecycle after the refactor
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Refactored request processor ready for both v0.1.11 and v0.1.12; no regression risk identified
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 90 changes merged to date

    On the table
      - v0.1.10 release notes (someone)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 141: Add LiteLLM+instructor (for structured output) backend for curator (Gideon Halloway)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 74: Add more model support with liteLLM
      - issue 86: Retry when structured output fails

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
    role        Core Engineer — Dataset Viewer & Run Observability. Just refactored the core request loop; understands every change
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm the retry abstraction doesn't lose requests or duplicate work   *** MUST RAISE ***
      2. Check that logging changes don't mask failures in batch/provider integrations
      3. Verify resume and caching still work after the rename   *** MUST RAISE ***
      4. what "release-v0-1-10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm the retry abstraction doesn't lose requests or duplicate work
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the request processing subsystem; driving v0.1.12 release which depends on this
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm the retry abstraction doesn't lose requests or duplicate work
      2. Check that logging changes don't mask failures in batch/provider integrations   *** MUST RAISE ***
      3. Verify resume and caching still work after the rename
    goal        Check that logging changes don't mask failures in batch/provider integrations
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Knows the request lifecycle end-to-end; has shipped this code in production
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm the retry abstraction doesn't lose requests or duplicate work
      2. Check that logging changes don't mask failures in batch/provider integrations
      3. Verify resume and caching still work after the rename
    goal        Gideon's 12 commits refactor the core of the online request processor; Dario Kestrel and Gideon Halloway are both driving releases that depend on this landing clean
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Refactored request processor ready for both v0.1.11 and v0.1.12; no regression risk identified


==============================================================================
# 2024-12-04 — 3 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five batch-related PRs merged today, three more pending, and a revert on retry logic that needs sorting before 0.1.12 ships

    Today is Wednesday 4 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five batch-related PRs merged today, three more pending, and a revert on retry logic that needs sorting before 0.1.12 ships
    
    What it should get through:
      1. Agree which batch PRs land before release cut   [Dario Kestrel must raise this]
           - Dario Kestrel states PR 197 and PR 198 are critical path; Gideon Halloway asks if PR 202 changes the contract; Dario Kestrel confirms both can land together
      2. Clarify retry-once fix does not break batch contract   [Gideon Halloway must raise this]
           - Gideon Halloway describes the single-retry bug he just fixed in online; Dario Kestrel confirms batch has its own retry loop; they note no conflict
    
    On the agenda: Which of Dario Kestrel's pending batch PRs unblock the release, and in what order; How PR 202 (OnlineRequestProcessor fix) affects batch retry logic; What's left before shipping
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Dario and Gideon Halloway agree on merge order for PR 197, PR 198, PR 202; Dermot Callaghan confirms all three pass CI before cut
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 95 changes merged to date

    On the table
      - v0.1.10 release notes (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer, Request Processing. wrote most of the batch retry logic and three related PRs today; understands the shape of remaining work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Agree which batch PRs land before release cut   *** MUST RAISE ***
      2. Clarify retry-once fix does not break batch contract
      3. what "v0.1.10 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Agree which batch PRs land before release cut
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just fixed the OnlineRequestProcessor retry-once bug (PR 202); sees the parallel async pattern that Dario Kestrel needs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Agree which batch PRs land before release cut
      2. Clarify retry-once fix does not break batch contract   *** MUST RAISE ***
    goal        Clarify retry-once fix does not break batch contract
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. raised the max retry count to 50; perspective on retry semantics across both online and batch
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Agree which batch PRs land before release cut
      2. Clarify retry-once fix does not break batch contract
    goal        Five batch-related PRs merged today, three more pending, and a revert on retry logic that needs sorting before 0.1.12 ships
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Dario and Gideon Halloway agree on merge order for PR 197, PR 198, PR 202; Dermot Callaghan confirms all three pass CI before cut


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 23 changes to request processing across bulk, online, caching, provider layers; revert on retry logic; 9 new issues opened on retry, rate limit, and capacity semantics

    Today is Wednesday 4 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 23 changes to request processing across bulk, online, caching, provider layers; revert on retry logic; 9 new issues opened on retry, rate limit, and capacity semantics
    
    What it should get through:
      1. Decide which of Gideon Halloway's new retry issues (PR 201, PR 203, PR 205, PR 207) block 0.1.12 ship   [Gideon Halloway must raise this]
           - Gideon Halloway lists the issues: single-retry bug (shipped in 0.1.11, fixed in PR 202), auth errors should hard-fail not retry, rate limit needs cooldown; Dario Kestrel says PR 202 lands with batch fixes; Dermot Callaghan asks if we cherry-pick to 0.1.11 or just ship 0.1.12
      2. Confirm async retry parallelism is production-ready for batch   [Dario Kestrel must raise this]
           - Dario Kestrel points to commits 3fb6f96 (parallel async) and 0f72e9ad (more specific exception handling); Gideon Halloway confirms the pattern; Dermot Callaghan notes he reviewed both, no blockers
      3. Triage rate limit, capacity, and token estimation work for post-ship   [Gideon Halloway must raise this]
           - Gideon Halloway lists PR 205 (cooldown after rate limit), PR 206 (output token est), PR 207 (has_capacity using headers); Dario Kestrel notes these are quality-of-life, not blocking; Dermot Callaghan agrees
    
    On the agenda: What Gideon Halloway's new retry issues mean for 0.1.12 ship readiness; Whether parallel async retry changes in main branch need cherry-pick backport logic; Post-ship backlog: auth errors, rate limit cooldown, capacity estimation
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees PR 202 and Dario Kestrel's batch PRs ship with 0.1.12; new retry/rate-limit issues defer to post-ship unless 0.1.11 users report hard breaks
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 95 changes merged to date

    On the table
      - Weekly notes: week of Nov 25 - v0.1.10 out (Gideon Halloway)
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer, Request Processing. implemented batch file cleanup, more retries, progress bar fix on resume; knows what the batch layer needs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Decide which of Gideon Halloway's new retry issues (PR 201, PR 203, PR 205, PR 207) block 0.1.12 ship
      2. Confirm async retry parallelism is production-ready for batch   *** MUST RAISE ***
      3. Triage rate limit, capacity, and token estimation work for post-ship
      4. that the doc "Weekly notes: week of Dec 2 - v0.1.11 out" is done, and where the others can find it   *** MUST RAISE ***
    goal        Confirm async retry parallelism is production-ready for batch
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just finished parallel async retries (#3fb6f96) and fixed the retry-once bug (PR 202); raised a dozen new issues on edge cases like auth errors and rate limiting
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Decide which of Gideon Halloway's new retry issues (PR 201, PR 203, PR 205, PR 207) block 0.1.12 ship   *** MUST RAISE ***
      2. Confirm async retry parallelism is production-ready for batch
      3. Triage rate limit, capacity, and token estimation work for post-ship   *** MUST RAISE ***
      4. what "Weekly notes: week of Nov 25 - v0.1.10 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Decide which of Gideon Halloway's new retry issues (PR 201, PR 203, PR 205, PR 207) block 0.1.12 ship
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. raised max retries to 50; knows the retry semantics from both sides; perspective on what 0.1.11 shipped with
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Decide which of Gideon Halloway's new retry issues (PR 201, PR 203, PR 205, PR 207) block 0.1.12 ship
      2. Confirm async retry parallelism is production-ready for batch
      3. Triage rate limit, capacity, and token estimation work for post-ship
    goal        23 changes to request processing across bulk, online, caching, provider layers; revert on retry logic; 9 new issues opened on retry, rate limit, and capacity semantics
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team agrees PR 202 and Dario Kestrel's batch PRs ship with 0.1.12; new retry/rate-limit issues defer to post-ship unless 0.1.11 users report hard breaks


------------------------------------------------------------------------------
## #incidents — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Commit d631f0e reverted retry logic; PR 202 is the replacement; need to confirm fix is solid before release

    Today is Wednesday 4 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Commit d631f0e reverted retry logic; PR 202 is the replacement; need to confirm fix is solid before release
    
    What it should get through:
      1. Understand the revert: what broke, when it shipped, why it mattered   [Gideon Halloway must raise this]
           - Gideon Halloway explains: parallel async retries in 0.1.11 caused all entries to retry even on transient errors; PR 202 reverts to serial then applies correct fix
      2. Confirm PR 202 fix is correct and complete   [Gideon Halloway must raise this]
           - Gideon Halloway walks through the new try/except specificity and single-retry guard in PR 202; Dario Kestrel confirms it matches batch semantics; Dermot Callaghan approves
      3. Decide: merge PR 202 and drop the revert, or ship revert + PR 202 both   [Dario Kestrel must raise this]
           - Dario Kestrel prefers clean history: PR 202 should replace the revert; Gideon Halloway agrees; they will force-push if needed
    
    On the agenda: Why the revert happened and what broke; Scope of PR 202 fix and whether it covers the regression; Merge order: does revert stay or does PR 202 replace it
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Team agrees PR 202 is the right fix; revert will be cleaned up or dropped in next rebase; 0.1.12 ships with PR 202, not the revert
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 95 changes merged to date

    On the table
      - Postmortem: Nov 23 revert to old LiteLLM backend (Gideon Halloway)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer — Dataset Viewer & Run Observability. understands why the revert happened (parallel async retries caused retries-on-all-entries); just shipped the fix in PR 202
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Understand the revert: what broke, when it shipped, why it mattered   *** MUST RAISE ***
      2. Confirm PR 202 fix is correct and complete   *** MUST RAISE ***
      3. Decide: merge PR 202 and drop the revert, or ship revert + PR 202 both
      4. what "Postmortem: Nov 23 revert to old LiteLLM backend" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand the revert: what broke, when it shipped, why it mattered
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. shipping batch retry improvements today; needs to know if the revert affects his batch work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Understand the revert: what broke, when it shipped, why it mattered
      2. Confirm PR 202 fix is correct and complete
      3. Decide: merge PR 202 and drop the revert, or ship revert + PR 202 both   *** MUST RAISE ***
    goal        Decide: merge PR 202 and drop the revert, or ship revert + PR 202 both
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. senior review; saw the revert come through
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Understand the revert: what broke, when it shipped, why it mattered
      2. Confirm PR 202 fix is correct and complete
      3. Decide: merge PR 202 and drop the revert, or ship revert + PR 202 both
    goal        Commit d631f0e reverted retry logic; PR 202 is the replacement; need to confirm fix is solid before release
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team agrees PR 202 is the right fix; revert will be cleaned up or dropped in next rebase; 0.1.12 ships with PR 202, not the revert


==============================================================================
# 2024-12-05 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs in flight with approvals and merges needed; two live release workstreams depend on pipeline stability

    Today is Thursday 5 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs in flight with approvals and merges needed; two live release workstreams depend on pipeline stability
    
    What it should get through:
      1. Land PR 210 and confirm it addresses cost mapping   [Gideon Halloway must raise this]
           - Gideon Halloway raises the missing cost default for litellm models
           - Konrad Feltrin approves PR 210
           - Gideon Halloway confirms merge
      2. Resolve remaining review comments on PR 211 and merge   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes Dario Kestrel's four rounds of comments and Konrad Feltrin's two
           - Dario Kestrel walks through the last round of feedback
           - Konrad Feltrin lands the approval
      3. Confirm PR 202 retry fix is in and stable   [Gideon Halloway must raise this]
           - Dermot Callaghan confirms approval
           - Gideon Halloway confirms merge and notes no incidents since
    
    On the agenda: Status of PR 210 (LiteLLM cost handling); Status of PR 211 (persona-hub example) and address review comments; Status of PR 202 (retry fix) and confirm it is merged
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: All three PRs merged; pipeline code-review queue unblocked; both release workstreams can proceed
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 98 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer — Dataset Viewer & Run Observability. Knows the cost handling and retry fixes in detail
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 210 and confirm it addresses cost mapping   *** MUST RAISE ***
      2. Resolve remaining review comments on PR 211 and merge
      3. Confirm PR 202 retry fix is in and stable   *** MUST RAISE ***
      4. that the doc "Postmortem: Dec 4 revert of end-of-run retry logic" is done, and where the others can find it   *** MUST RAISE ***
    goal        Land PR 210 and confirm it addresses cost mapping
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Built the persona-hub example; knows what it does and why
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Land PR 210 and confirm it addresses cost mapping
      2. Resolve remaining review comments on PR 211 and merge   *** MUST RAISE ***
      3. Confirm PR 202 retry fix is in and stable
    goal        Resolve remaining review comments on PR 211 and merge
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Heavy reviewer on PR 211; knows curation patterns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 210 and confirm it addresses cost mapping
      2. Resolve remaining review comments on PR 211 and merge
      3. Confirm PR 202 retry fix is in and stable
    goal        Three PRs in flight with approvals and merges needed; two live release workstreams depend on pipeline stability
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Approved PR 202 and PR 198; knows the retry fix implications
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 210 and confirm it addresses cost mapping
      2. Resolve remaining review comments on PR 211 and merge
      3. Confirm PR 202 retry fix is in and stable
    goal        Three PRs in flight with approvals and merges needed; two live release workstreams depend on pipeline stability
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   All three PRs merged; pipeline code-review queue unblocked; both release workstreams can proceed


------------------------------------------------------------------------------
## #pipeline — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 19 changes to the request layer today; four new issues filed on cache, cost, and batch behavior; two PRs merged that touch retry and cost logic

    Today is Thursday 5 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 19 changes to the request layer today; four new issues filed on cache, cost, and batch behavior; two PRs merged that touch retry and cost logic
    
    What it should get through:
      1. Triage cache hit failures and fingerprinting issue PR 215   [Dario Kestrel must raise this]
           - Dario Kestrel describes identical files not hitting the same cache
           - Gideon Halloway asks if it is a hash collision or path-dependent bug
           - Dario Kestrel points to the reproduction in his commits
      2. Confirm asyncio double-while-loop fix in #3b8cfcbd is complete   [Gideon Halloway must raise this]
           - Gideon Halloway describes the short timeout replacement for double-spinning
           - Dario Kestrel asks if it affects max throughput
           - Gideon Halloway says no, just prevents CPU waste
      3. Agree on cost tracking and batch cancel behavior for v0.1.12   [Dario Kestrel must raise this]
           - Dario Kestrel notes his commits on cancel logic and batch tracking
           - Dermot Callaghan asks if this blocks the release
           - Dario Kestrel says depends on whether cancel is user-facing enough to document
    
    On the agenda: Dario's cache and fingerprinting issues (PR 215, PR 217); Dario's batch cancel and cost handling; Gideon's asyncio.wait timeout fix and its impact
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Issues logged and triaged; asyncio fix confirmed safe; batch cancel behavior decided; release v0.1.12 can proceed
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 98 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer, Request Processing. Just filed four issues on cache, batch cancel, cost tracking, and fingerprinting; has run logs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Triage cache hit failures and fingerprinting issue PR 215   *** MUST RAISE ***
      2. Confirm asyncio double-while-loop fix in #3b8cfcbd is complete
      3. Agree on cost tracking and batch cancel behavior for v0.1.12   *** MUST RAISE ***
    goal        Triage cache hit failures and fingerprinting issue PR 215
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Landed the cost fix in PR 210 and the retry fix in PR 202; knows where the asyncio loop was double-spinning
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Triage cache hit failures and fingerprinting issue PR 215
      2. Confirm asyncio double-while-loop fix in #3b8cfcbd is complete   *** MUST RAISE ***
      3. Agree on cost tracking and batch cancel behavior for v0.1.12
    goal        Confirm asyncio double-while-loop fix in #3b8cfcbd is complete
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Understands the request layer plumbing and cost accounting
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Triage cache hit failures and fingerprinting issue PR 215
      2. Confirm asyncio double-while-loop fix in #3b8cfcbd is complete
      3. Agree on cost tracking and batch cancel behavior for v0.1.12
    goal        19 changes to the request layer today; four new issues filed on cache, cost, and batch behavior; two PRs merged that touch retry and cost logic
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Issues logged and triaged; asyncio fix confirmed safe; batch cancel behavior decided; release v0.1.12 can proceed


------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.12 release is mid-flight; Dario Kestrel is driving it; four issues opened today on cost, cache, and request handling

    Today is Thursday 5 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.12 release is mid-flight; Dario Kestrel is driving it; four issues opened today on cost, cache, and request handling
    
    What it should get through:
      1. Confirm pipeline changes are safe to ship in v0.1.12   [Dario Kestrel must raise this]
           - Dario Kestrel notes PR 210 and PR 202 are merged and tested
           - Dermot Callaghan confirms CI passed on both
           - Dario Kestrel says we can proceed with tag
      2. Decide if PR 212 (OpenAI TPM fallback) goes in v0.1.12 or v0.1.13   [Konrad Feltrin must raise this]
           - Dermot Callaghan raises the issue and notes it blocks users with no tier
           - Konrad Feltrin says it is one-line fix
           - Dario Kestrel decides whether to cherry-pick or defer
    
    On the agenda: Confirm pipeline changes in v0.1.12 are release-safe; Address issue PR 212 on OpenAI fallback TPM/RPM; Decide on postmortem-2024-12-04 visibility before cut
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.12 cleared for tag; PR 212 triaged (cherry-pick or defer); postmortem written and linked; release proceeds
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 4 release(s) shipped, currently v0.1.10
      - 98 changes merged to date

    On the table
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
    role        Core Engineer, Request Processing. Driving the v0.1.12 release; knows what landed and what is still in flight
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm pipeline changes are safe to ship in v0.1.12   *** MUST RAISE ***
      2. Decide if PR 212 (OpenAI TPM fallback) goes in v0.1.12 or v0.1.13
    goal        Confirm pipeline changes are safe to ship in v0.1.12
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Knows the persona-hub example and whether it is release-safe
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm pipeline changes are safe to ship in v0.1.12
      2. Decide if PR 212 (OpenAI TPM fallback) goes in v0.1.12 or v0.1.13   *** MUST RAISE ***
    goal        Decide if PR 212 (OpenAI TPM fallback) goes in v0.1.12 or v0.1.13
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Reviewed the merge commit on PR 202 and understands the retry fix impact
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm pipeline changes are safe to ship in v0.1.12
      2. Decide if PR 212 (OpenAI TPM fallback) goes in v0.1.12 or v0.1.13
    goal        v0.1.12 release is mid-flight; Dario Kestrel is driving it; four issues opened today on cost, cache, and request handling
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.12 cleared for tag; PR 212 triaged (cherry-pick or defer); postmortem written and linked; release proceeds


==============================================================================
# 2024-12-06 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.11 tagged and merged this morning; release notes due and announcement pending.

    Today is Friday 6 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.11 tagged and merged this morning; release notes due and announcement pending.
    
    What it should get through:
      1. Release notes capture the six merged fixes accurately   [Dario Kestrel must raise this]
           - Dario Kestrel drafts from the PR titles and merged commits
           - Dermot Callaghan spot-checks against the actual changes
           - Dario Kestrel ships it
      2. Announcement mail goes to stakeholders same day   [Dario Kestrel must raise this]
           - Dario Kestrel writes the mail pointing to the release notes
           - Dermot Callaghan signs off
    
    On the agenda: Verify all six merges are solid; Write and post release notes; Cut the announcement mail
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.11 release notes published and announcement mail sent to Dario Kestrel, Dermot Callaghan, and Konrad Feltrin by end of day.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 104 changes merged to date

    On the table
      - v0.1.11 release notes (Dario Kestrel)
      - v0.1.10 release notes (Dario Kestrel)
      - announce-v0-1-11 (Dario Kestrel)
      - release-v0-1-11 (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. the release notes and changelog assembled from today's merges
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture the six merged fixes accurately   *** MUST RAISE ***
      2. Announcement mail goes to stakeholders same day   *** MUST RAISE ***
      3. that the doc "v0.1.11 release notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.11 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "v0.1.10 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "v0.1.11 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture the six merged fixes accurately
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. quality check on the merged code
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Release notes capture the six merged fixes accurately
      2. Announcement mail goes to stakeholders same day
    goal        v0.1.11 tagged and merged this morning; release notes due and announcement pending.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.11 release notes published and announcement mail sent to Dario Kestrel, Dermot Callaghan, and Konrad Feltrin by end of day.


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Twelve PRs are older than the release cycle median; six are high-priority stale and need a path forward.

    Today is Friday 6 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Twelve PRs are older than the release cycle median; six are high-priority stale and need a path forward.
    
    What it should get through:
      1. Identify which of PR 161, PR 163, PR 165, PR 78, PR 90, PR 106 can merge safely now vs need wait for next cycle   [Gideon Halloway must raise this]
           - Gideon Halloway calls out the ones blocking examples or observability
           - Dario Kestrel notes which of his are safe to land
           - Konrad Feltrin flags PR 106 as ready
    
    On the agenda: Triage the six stale PRs by risk and benefit; Decide which can land before the next release; Assign review or ask for rebase where needed
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Agreement on which stale PRs can land this cycle and which need rebasing or deferral; no merges, just a plan.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 104 changes merged to date

    On the table
      - Weekly notes: week of Dec 2 - v0.1.11 out (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 47: Simple way to cancel submitted batches
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator

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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on the release work just landed and what blocks on the open queue
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Identify which of PR 161, PR 163, PR 165, PR 78, PR 90, PR 106 can merge safely now vs need wait for next cycle   *** MUST RAISE ***
      2. what "Weekly notes: week of Dec 2 - v0.1.11 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Identify which of PR 161, PR 163, PR 165, PR 78, PR 90, PR 106 can merge safely now vs need wait for next cycle
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ownership of two blocked PRs (vLLM example, disable-cache feature) and the batch cancellation work
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Identify which of PR 161, PR 163, PR 165, PR 78, PR 90, PR 106 can merge safely now vs need wait for next cycle
    goal        Twelve PRs are older than the release cycle median; six are high-priority stale and need a path forward.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. the context on PR 106 (text message summarization example)
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Identify which of PR 161, PR 163, PR 165, PR 78, PR 90, PR 106 can merge safely now vs need wait for next cycle
    goal        Twelve PRs are older than the release cycle median; six are high-priority stale and need a path forward.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Agreement on which stale PRs can land this cycle and which need rebasing or deferral; no merges, just a plan.


==============================================================================
# 2024-12-09 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened in two days on core request processing; two merged already; rate-limit work is release-critical

    Today is Monday 9 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened in two days on core request processing; two merged already; rate-limit work is release-critical
    
    What it should get through:
      1. Establish whether PR 231 and PR 234 block the 0.1.12 release cut   [Dario Kestrel must raise this]
           - Dario raises that both are ready but rate-limit design could use one more set of eyes
           - Konrad signals whether rate limits are a release gate or a follow-on
           - Dermot confirms PR 231 is solid; both land or defer as a unit
      2. Unblock the backlog of 13 stale PRs by deciding triage order   [Konrad Feltrin must raise this]
           - Konrad flags which old PRs align with next workstream priorities
           - Dario and Dermot call out which ones are actually blocking other work
           - Decision: one or two get attention this week; rest stay parked
      3. write up Bulk LLM Inference: next-phase design   [Dermot Callaghan must raise this]
           - Dermot Callaghan says they will write Bulk LLM Inference: next-phase design — Scopes the follow-on curator.LLM core work starting Dec 10.
    
    On the agenda: Where PR 231 (batch reliability fixes) stands and what it needs; Whether PR 234 (manual rate limits) is release-blocking or can land after 0.1.12; Stale PR backlog: which of the 13+ old PRs should move forward; Bulk LLM Inference: next-phase design
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 230, PR 231, PR 234 clear or their path is decided; backlog triage happens so nobody is surprised when the old PRs surface again
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 106 changes merged to date

    On the table
      - weekly-2024-12-02 (Konrad Feltrin)
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
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views

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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Rate-limit design and implementation across all three PRs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Establish whether PR 231 and PR 234 block the 0.1.12 release cut   *** MUST RAISE ***
      2. Unblock the backlog of 13 stale PRs by deciding triage order
      3. write up Bulk LLM Inference: next-phase design
      4. what "Weekly update: week of Dec 2" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Establish whether PR 231 and PR 234 block the 0.1.12 release cut
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Implementation details on cache fixes (PR 230) and batch reliability (PR 231)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Establish whether PR 231 and PR 234 block the 0.1.12 release cut
      2. Unblock the backlog of 13 stale PRs by deciding triage order
      3. write up Bulk LLM Inference: next-phase design   *** MUST RAISE ***
      4. the page you are writing, Bulk LLM Inference: next-phase design, has to say this in your own words: Cache directory resolution lives in exactly one place in the caching layer and everything that needs the location calls it. I have deleted three hand-rolled path joins in review this quarter.   *** MUST SETTLE (clue t1.r2.L3) ***
      5. that the doc "Bulk LLM Inference: next-phase design" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Bulk LLM Inference: next-phase design
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release readiness perspective; oversight on rate-limit changes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Establish whether PR 231 and PR 234 block the 0.1.12 release cut
      2. Unblock the backlog of 13 stale PRs by deciding triage order   *** MUST RAISE ***
      3. write up Bulk LLM Inference: next-phase design
      4. that "Weekly update: week of Dec 2" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Unblock the backlog of 13 stale PRs by deciding triage order
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 230, PR 231, PR 234 clear or their path is decided; backlog triage happens so nobody is surprised when the old PRs surface again


------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 12 commits landed over the weekend and Monday morning; three major PRs touching core pipeline; next workstream (bulk-llm inference v2) needs stability baseline

    Today is Monday 9 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 12 commits landed over the weekend and Monday morning; three major PRs touching core pipeline; next workstream (bulk-llm inference v2) needs stability baseline
    
    What it should get through:
      1. Confirm that cache-and-resume is now reliable enough for the next phase   [Dermot Callaghan must raise this]
           - Dermot explains why path-dependent caching was breaking resume
           - Konrad and Dario ask whether this is a fix or a workaround
           - Decision: it's solid, moves us forward
    
    On the agenda: What the cache fix (PR 230) actually solved and why HF's pickler mattered; What batch reliability (PR 231) covers: retry logic, deletion guards, download avoidance; Rate-limit design (PR 234): manual vs. auto-detect and why we need both
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what landed and why it matters; confidence that pipeline is ready for design-phase work on bulk-llm-inference v2
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 106 changes merged to date

    On the table
      - design-ws-012-bulk-llm-inference (Dermot Callaghan)
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
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views

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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Rate-limit refactor and the three design decisions it required
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm that cache-and-resume is now reliable enough for the next phase
    goal        12 commits landed over the weekend and Monday morning; three major PRs touching core pipeline; next workstream (bulk-llm inference v2) needs stability baseline
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Seven commits fixing cache reliability and batch handling; what the HF pickler fix unlocks
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm that cache-and-resume is now reliable enough for the next phase   *** MUST RAISE ***
      2. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm that cache-and-resume is now reliable enough for the next phase
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release and stability perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm that cache-and-resume is now reliable enough for the next phase
    goal        12 commits landed over the weekend and Monday morning; three major PRs touching core pipeline; next workstream (bulk-llm inference v2) needs stability baseline
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what landed and why it matters; confidence that pipeline is ready for design-phase work on bulk-llm-inference v2


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 10+ changes each to bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; these are the request layer's core files

    Today is Monday 9 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 10+ changes each to bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; these are the request layer's core files
    
    What it should get through:
      1. Verify that manual rate-limit defaults don't cause provider rejection or user frustration   [Dario Kestrel must raise this]
           - Dario walks through the test-call function and what it measures
           - Dermot and Gideon flag if defaults conflict with known provider behavior
           - Decision: defaults are conservative but usable; advanced users can tune
      2. Confirm batch request lifecycle survives unclean shutdown and replay   [Dermot Callaghan must raise this]
           - Dermot explains what 'print out unsubmitted request files' does and why it matters
           - Dario asks whether this is visible to users or internal diagnostic
           - Decision: diagnostic for now; becomes user-facing if we ship batch as public API
    
    On the agenda: Does the pickler fix solve resume without breaking viewer or progress tracking?; What do the manual rate-limit defaults look like and are they sane for typical users?; How does request state survive a hard crash: what the unsubmitted files are and how to replay them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario and Dermot have high confidence that rate limits are sane and batch state is durable; Gideon knows whether to watch the viewer layer
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 106 changes merged to date

    On the table
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
      - issue 55: Complain louder when num generic requests != num generic responses after parsing
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views

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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Rate-limit refactoring; test-call function design; manual vs. auto-detect trade-offs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Verify that manual rate-limit defaults don't cause provider rejection or user frustration   *** MUST RAISE ***
      2. Confirm batch request lifecycle survives unclean shutdown and replay
    goal        Verify that manual rate-limit defaults don't cause provider rejection or user frustration
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Implementation of the pickler fix; batch request lifecycle; what unsubmitted request files mean
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Verify that manual rate-limit defaults don't cause provider rejection or user frustration
      2. Confirm batch request lifecycle survives unclean shutdown and replay   *** MUST RAISE ***
    goal        Confirm batch request lifecycle survives unclean shutdown and replay
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observer role; can spot if the changes create new progress-bar or viewer issues
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Verify that manual rate-limit defaults don't cause provider rejection or user frustration
      2. Confirm batch request lifecycle survives unclean shutdown and replay
    goal        10+ changes each to bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations; these are the request layer's core files
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Dario and Dermot have high confidence that rate limits are sane and batch state is durable; Gideon knows whether to watch the viewer layer

