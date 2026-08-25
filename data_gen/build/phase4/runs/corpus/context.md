# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-12-24 — 1 conversation(s), 9 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 16 PRs older than the 1-hour median merge time; the longest are 40+ days stale and blocking contributors

    Today is Tuesday 24 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 16 PRs older than the 1-hour median merge time; the longest are 40+ days stale and blocking contributors
    
    What it should get through:
      1. Unblock or formally defer the six oldest PRs (PR 78, PR 90, PR 106, PR 161, PR 163, PR 133)   [Dario Kestrel must raise this]
           - Dario flags PR 78 and PR 90 as part of active request-processing; Konrad notes PR 106 is example-tier and can wait; Gideon pushes for PR 161 and PR 163 as viewer unblocks
           - Konrad and Dario agree PR 133 (env example) is low-priority, defer it
           - Group lands: merge PR 78, PR 90, PR 106 this week; PR 161, PR 163 after 0.1.14 planning
      2. Clarify PR merge velocity expectation for the era ahead   [Konrad Feltrin must raise this]
           - Konrad raises: 16 PRs > 1h median suggests bottleneck, not normal variation
           - Dario and Gideon confirm: no review bottleneck; these are complex subsystems needing author rework or design conversation
           - Outcome: next era targets tighter feedback loops, author + one reviewer sync before resubmit if stale > 2 weeks
    
    On the agenda: Review oldest backlog: PR 78, PR 90, PR 106, PR 161, PR 163, PR 133; Decide merge or defer for each; Set expectation for next era
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Consensus on which stale PRs land this week, which defer to next planning window, and clearer friction-detection for future eras
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 141 changes merged to date

    On the table
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
    role        Core Engineer, Request Processing. context on PR PR 78 and PR 90 — vLLM example and cache-disable arg, both blocking practical workflows
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock or formally defer the six oldest PRs (PR 78, PR 90, PR 106, PR 161, PR 163, PR 133)   *** MUST RAISE ***
      2. Clarify PR merge velocity expectation for the era ahead
    goal        Unblock or formally defer the six oldest PRs (PR 78, PR 90, PR 106, PR 161, PR 163, PR 133)
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. UI work on PR 161 and PR 163 — Prometheus judge and cache-dir helper, both waiting 33+ days
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock or formally defer the six oldest PRs (PR 78, PR 90, PR 106, PR 161, PR 163, PR 133)
      2. Clarify PR merge velocity expectation for the era ahead
    goal        16 PRs older than the 1-hour median merge time; the longest are 40+ days stale and blocking contributors
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns cookbooks; PR PR 106 (text message summarization example) is 40 days old and needs landing or deferral
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock or formally defer the six oldest PRs (PR 78, PR 90, PR 106, PR 161, PR 163, PR 133)
      2. Clarify PR merge velocity expectation for the era ahead   *** MUST RAISE ***
      3. what "0.1.13 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify PR merge velocity expectation for the era ahead
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Consensus on which stale PRs land this week, which defer to next planning window, and clearer friction-detection for future eras


==============================================================================
# 2024-12-25 — 2 conversation(s), 22 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Dario has 8 open reviews on batch-related work (PR PR 243); Konrad just merged PR 289 fixing batch mapping; need to confirm the batch fixes align

    Today is Wednesday 25 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario has 8 open reviews on batch-related work (PR PR 243); Konrad just merged PR 289 fixing batch mapping; need to confirm the batch fixes align
    
    What it should get through:
      1. Approve or advise on PR PR 243 anthropic-batches integration   [Konrad Feltrin must raise this]
           - Dario Kestrel raises the remaining comments on PR 243 and where batch edge cases stand
           - Konrad Feltrin confirms the batch mapping fix in PR 289 should unblock the ordering issues
           - they land on whether to merge PR 243 before or after additional testing
      2. write up Weekly notes: week of Dec 23 - 0.1.13 out   [Dario Kestrel must raise this]
           - Dario Kestrel says they will write Weekly notes: week of Dec 23 - 0.1.13 out — Recaps a light 33-commit week closing out the release.
    
    On the agenda: Review PR PR 243 (anthropic-batches) against recent batch mapping fixes; Confirm batch output ordering is correct after PR 289 merge; Weekly notes: week of Dec 23 - 0.1.13 out
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR PR 243 either approved with minor adjustments or deferred pending integration tests after the batch mapping fix
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 142 changes merged to date

    On the table
      - 0.1.13 release notes (someone)
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
    role        Core Engineer, Request Processing. batch-mode work and anthropic-batches branch integration
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve or advise on PR PR 243 anthropic-batches integration
      2. write up Weekly notes: week of Dec 23 - 0.1.13 out   *** MUST RAISE ***
      3. that the doc "Weekly notes: week of Dec 23 - 0.1.13 out" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly notes: week of Dec 23 - 0.1.13 out
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. batch mapping fix and order correctness
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Approve or advise on PR PR 243 anthropic-batches integration   *** MUST RAISE ***
      2. write up Weekly notes: week of Dec 23 - 0.1.13 out
      3. what "release-0-1-13" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Approve or advise on PR PR 243 anthropic-batches integration
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR PR 243 either approved with minor adjustments or deferred pending integration tests after the batch mapping fix


------------------------------------------------------------------------------
## #pipeline — 12 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Konrad's batch mapping fix (PR 289) merged today; Dario has 4 commits touching provider-integrations and batch-mode; together they need to confirm the request pipeline handles batches correctly

    Today is Wednesday 25 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad's batch mapping fix (PR 289) merged today; Dario has 4 commits touching provider-integrations and batch-mode; together they need to confirm the request pipeline handles batches correctly
    
    What it should get through:
      1. Validate anthropic-batches provider integration is ready   [Dario Kestrel must raise this]
           - Dario Kestrel walks through the shared cost function and exception handling changes
           - Konrad Feltrin checks that litellm mocking is complete for the anthropic path
           - they agree on whether provider-integrations can land today or needs follow-up testing
    
    On the agenda: Batch output ordering fix from PR 289 and its ripple effects; Anthropic batches provider integration status; Mocking and local testing for batch-mode
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Batch mapping fix confirmed working; anthropic-batches provider integration either merged or deferred for final testing; shared completion cost function in place
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 142 changes merged to date

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
    role        Core Engineer, Request Processing. anthropic-batches branch work, mocking fixes for litellm and anthropic server, shared completion cost function
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate anthropic-batches provider integration is ready   *** MUST RAISE ***
    goal        Validate anthropic-batches provider integration is ready
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. observer role on request-layer stability
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate anthropic-batches provider integration is ready
    goal        Konrad's batch mapping fix (PR 289) merged today; Dario has 4 commits touching provider-integrations and batch-mode; together they need to confirm the request pipeline handles batches correctly
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Batch mapping fix confirmed working; anthropic-batches provider integration either merged or deferred for final testing; shared completion cost function in place


==============================================================================
# 2024-12-26 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 16 PRs older than the era's median merge time; Dario Kestrel, Konrad Feltrin, Gideon Halloway each have PRs stuck for 19+ days

    Today is Thursday 26 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 16 PRs older than the era's median merge time; Dario Kestrel, Konrad Feltrin, Gideon Halloway each have PRs stuck for 19+ days
    
    What it should get through:
      1. Determine which stale PRs can land without breaking anything   [Dario Kestrel must raise this]
           - Dario Kestrel surfaces the three blockers: 78 (vLLM example), 90 (disable cache), 228 (expired batches)
           - Konrad Feltrin and Gideon Halloway flag dependencies in their PRs (161, 163 need viewer work; 106 needs nothing but review)
           - group decides 228 is highest priority, 78 and 90 need rebase after SimpleLLM folding lands
      2. Clear the critical path for the next release   [Konrad Feltrin must raise this]
           - Konrad Feltrin argues 106 is mergeable now (just an example, no subsystem changes)
           - Dario Kestrel agrees; Gideon Halloway notes 163 (viewer cache dir) is prerequisite for 241 (cost UI)
           - decision: land 106 next working day, prioritize rebasing 163 and 241
    
    On the agenda: Age and status of oldest six stale PRs; Which are safe to land, which need rework or rebase; Unblock the critical path for v0.1.14
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three stale PRs triaged: 228 and 78/90 flagged for rebase; 106 (Konrad Feltrin) cleared to land; 163/241 (Gideon Halloway) path clarified
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 142 changes merged to date

    On the table
      - 0.1.13 release notes (Konrad Feltrin)
      - Weekly notes: week of Dec 23 - 0.1.13 out (Dario Kestrel)
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
    role        Core Engineer, Request Processing. ownership of request-processing subsystem and knowledge of what's blocking releases
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Determine which stale PRs can land without breaking anything   *** MUST RAISE ***
      2. Clear the critical path for the next release
      3. what "0.1.13 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Weekly notes: week of Dec 23 - 0.1.13 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine which stale PRs can land without breaking anything
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. context on PR 106 (text message summarization example) and recent 0.1.13 merge
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Determine which stale PRs can land without breaking anything
      2. Clear the critical path for the next release   *** MUST RAISE ***
      3. what "0.1.13 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clear the critical path for the next release
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on viewer and observability PRs (PR 161, PR 163) and their dependencies
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Determine which stale PRs can land without breaking anything
      2. Clear the critical path for the next release
    goal        16 PRs older than the era's median merge time; Dario Kestrel, Konrad Feltrin, Gideon Halloway each have PRs stuck for 19+ days
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three stale PRs triaged: 228 and 78/90 flagged for rebase; 106 (Konrad Feltrin) cleared to land; 163/241 (Gideon Halloway) path clarified


==============================================================================
# 2024-12-27 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 16 PRs older than the era median; three people have work waiting; Konrad Feltrin just merged and can triage

    Today is Friday 27 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 16 PRs older than the era median; three people have work waiting; Konrad Feltrin just merged and can triage
    
    What it should get through:
      1. Clear batch bug fix (PR 228) or defer past holiday   [Dario Kestrel must raise this]
           - Dario Kestrel raises the three-week stall on batch expired handling
           - Konrad Feltrin pushes back on merge timeline if it touches active paths
           - lands as either merge-ready or explicitly deferred to Jan
      2. Prioritize viewer examples backlog   [Gideon Halloway must raise this]
           - Gideon Halloway flags PR 163 and PR 161 as long-stalled
           - Konrad Feltrin or Dario Kestrel signals if they block next release
           - lands as 'pull into Jan sprint' or 'close'
    
    On the agenda: Which older PRs can land this week; Batch-related blockers (PR 228); Viewer and examples tier
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Two to three PRs either move to ready-to-merge or get explicitly bumped to 2025; batch fix gets a clear decision; it is settled that __init__ stays free of model/response_format checks; incompatibility surfaces at request time
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

    On the table
      - Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254) (Konrad Feltrin)
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

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. merge authority and knowledge of the codebase shape
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Clear batch bug fix (PR 228) or defer past holiday
      2. Prioritize viewer examples backlog
    goal        16 PRs older than the era median; three people have work waiting; Konrad Feltrin just merged and can triage
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. context on blocking PRs and release readiness
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clear batch bug fix (PR 228) or defer past holiday   *** MUST RAISE ***
      2. Prioritize viewer examples backlog
      3. Also please don't add validation into LLM.__init__ for this. Construction should stay cheap and dumb, it just holds config. The moment __init__ starts asserting things about model names we get bug reports from everyone pointing at a new base_url or a proxy we've never heard of. Keep the checking where the request happens, the response tells us what we need to know.   *** MUST SETTLE (clue t2.r1.h2) ***
      4. what "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clear batch bug fix (PR 228) or defer past holiday
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. viewer UI context and observability needs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clear batch bug fix (PR 228) or defer past holiday
      2. Prioritize viewer examples backlog   *** MUST RAISE ***
    goal        Prioritize viewer examples backlog
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Two to three PRs either move to ready-to-merge or get explicitly bumped to 2025; batch fix gets a clear decision; it is settled that __init__ stays free of model/response_format checks; incompatibility surfaces at request time


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Five commits today, one merged refactor across core services; Konrad Feltrin just cut v0.1.13; Dario Kestrel made release-and-ci changes; team needs to confirm nothing broke

    Today is Friday 27 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits today, one merged refactor across core services; Konrad Feltrin just cut v0.1.13; Dario Kestrel made release-and-ci changes; team needs to confirm nothing broke
    
    What it should get through:
      1. Confirm path-handling refactor is solid in v0.1.13   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes the merge and Millrow Refactor Bot's consistency win
           - Dario Kestrel or Dermot Callaghan spot any missed paths or edge cases
           - lands as 'good' or 'watch closely this week'
      2. Understand base URL option and release-and-ci changes   [Dario Kestrel must raise this]
           - Dario Kestrel explains the new option and where it lands in release-and-ci
           - Konrad Feltrin asks if it's backward-compat or needs a changelog line
           - lands as 'ready for v0.1.14' or 'hold for config review'
    
    On the agenda: Path-handling refactor landed (PR PR 291); Base URL option commit status; Any regressions from os.path.join rollout
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confirms the refactor poses no known risk; base URL change is either approved for next release or flagged for review.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

    On the table
      - Weekly notes: week of Dec 23 - 0.1.13 out (Dario Kestrel)
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

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. recent merge of dev into main and v0.1.13 landing; codebase state
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm path-handling refactor is solid in v0.1.13   *** MUST RAISE ***
      2. Understand base URL option and release-and-ci changes
      3. what "Weekly notes: week of Dec 23 - 0.1.13 out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm path-handling refactor is solid in v0.1.13
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. two commits including base URL option; understanding of CI changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm path-handling refactor is solid in v0.1.13
      2. Understand base URL option and release-and-ci changes   *** MUST RAISE ***
    goal        Understand base URL option and release-and-ci changes
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. experience with bulk-llm-inference and pipeline stability
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm path-handling refactor is solid in v0.1.13
      2. Understand base URL option and release-and-ci changes
    goal        Five commits today, one merged refactor across core services; Konrad Feltrin just cut v0.1.13; Dario Kestrel made release-and-ci changes; team needs to confirm nothing broke
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team confirms the refactor poses no known risk; base URL change is either approved for next release or flagged for review.


==============================================================================
# 2025-01-02 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario landed foundational resume code across batch/online/provider layers during the break; team needs to assess the abstraction before he continues

    Today is Thursday 2 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario landed foundational resume code across batch/online/provider layers during the break; team needs to assess the abstraction before he continues
    
    What it should get through:
      1. Validate resume abstraction is sound before expanding test coverage   [Dario Kestrel must raise this]
           - Dario walks through what the base class does and where it sits
           - Dermot flags any friction with SimpleLLM folding plans
           - Land on: proceed as-is, or reshape before tests
    
    On the agenda: Three commits landed: abstracted resume base, tracker resubmit logic, test coverage; Whether abstraction sits at the right level for batch and online paths; What's next: filling out the test suite or reshaping
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario gets thumbs-up to continue hardening tests, or identifies one reshape before proceeding
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

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
    role        Core Engineer, Request Processing. three commits on resume/batch/provider foundations just landed
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate resume abstraction is sound before expanding test coverage   *** MUST RAISE ***
    goal        Validate resume abstraction is sound before expanding test coverage
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. perspective on how SimpleLLM folding will interact with the new base code
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate resume abstraction is sound before expanding test coverage
    goal        Dario landed foundational resume code across batch/online/provider layers during the break; team needs to assess the abstraction before he continues
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Dario gets thumbs-up to continue hardening tests, or identifies one reshape before proceeding


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Six PRs (78, 90, 106, 133, 161, 163) are 42+ days old; team returned after the break and needs to decide which ones are still live

    Today is Thursday 2 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six PRs (78, 90, 106, 133, 161, 163) are 42+ days old; team returned after the break and needs to decide which ones are still live
    
    What it should get through:
      1. Surface which PRs are still wanted vs can be closed   [Dario Kestrel must raise this]
           - Dario lists the batch/cache ones (78, 90, 228) and their status
           - Gideon flags the viewer PRs (161, 163) as still needed or not
           - Konrad same for PR 106; decide: keep open or close
      2. Unblock at least one PR by identifying what review/reshape it needs   [Konrad Feltrin must raise this]
           - Walk the three most-relevant ones
           - Identify: waiting-for-author, needs-review, or needs-reshape
           - Assign next action
    
    On the agenda: Which of the six stale PRs are still relevant; What's blocking each one from merge; Triage into: review now, deprecate, or explicit hold
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Two or three PRs get scheduled for review or close; team knows which ones are still active
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

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
    role        Core Engineer, Request Processing. owns several of the blocked PRs (78, 90, 228); knows what's waiting on review
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Surface which PRs are still wanted vs can be closed   *** MUST RAISE ***
      2. Unblock at least one PR by identifying what review/reshape it needs
    goal        Surface which PRs are still wanted vs can be closed
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns PR 106; can speak to priority and any unblocking needed
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Surface which PRs are still wanted vs can be closed
      2. Unblock at least one PR by identifying what review/reshape it needs   *** MUST RAISE ***
    goal        Unblock at least one PR by identifying what review/reshape it needs
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. owns two UI PRs (PR 161, PR 163); knows viewer backlog
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Surface which PRs are still wanted vs can be closed
      2. Unblock at least one PR by identifying what review/reshape it needs
    goal        Six PRs (78, 90, 106, 133, 161, 163) are 42+ days old; team returned after the break and needs to decide which ones are still live
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Two or three PRs get scheduled for review or close; team knows which ones are still active


------------------------------------------------------------------------------
## #pipeline — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Dario landed foundational batch/provider/online code during the break; the pipeline team needs to assess it before Nils Brandt joins to expand batch work next week

    Today is Thursday 2 January 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario landed foundational batch/provider/online code during the break; the pipeline team needs to assess it before Nils Brandt joins to expand batch work next week
    
    What it should get through:
      1. Surface any friction in the new tracker/resubmit logic and provider config enums   [Dario Kestrel must raise this]
           - Dario shows the enum refactor and how it flows to providers
           - Dermot flags any places the provider interface got more complex
           - Gideon raises progress-tracking implications; land on: ship as-is or minor reshapes
    
    On the agenda: What landed: resume base, tracker resubmit, test scaffolding; Provider backend shape: are the new enums and config surfaces right; Online path: what does the new tracking logic mean for concurrent requests and resumption
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario has feedback on whether the provider/tracker shapes will work at scale before Nils Brandt arrives; minor fixes if needed by Friday
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 143 changes merged to date

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
    role        Core Engineer, Request Processing. landed resume base and test work on batch side; knows what's next on provider enum/config
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Surface any friction in the new tracker/resubmit logic and provider config enums   *** MUST RAISE ***
    goal        Surface any friction in the new tracker/resubmit logic and provider config enums
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. perspective on how provider backends will handle the new tracker/append logic
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Surface any friction in the new tracker/resubmit logic and provider config enums
    goal        Dario landed foundational batch/provider/online code during the break; the pipeline team needs to assess it before Nils Brandt joins to expand batch work next week
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. observability angle; can flag what the tracking changes mean for progress reporting
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Surface any friction in the new tracker/resubmit logic and provider config enums
    goal        Dario landed foundational batch/provider/online code during the break; the pipeline team needs to assess it before Nils Brandt joins to expand batch work next week
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Dario has feedback on whether the provider/tracker shapes will work at scale before Nils Brandt arrives; minor fixes if needed by Friday

