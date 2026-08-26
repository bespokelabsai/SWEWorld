# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-12-11 — 3 conversation(s), 31 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three commits landed, two PRs merged, and a backlog of stale examples and fixes that need sorting before the release.

    Today is Wednesday 11 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three commits landed, two PRs merged, and a backlog of stale examples and fixes that need sorting before the release.
    
    What it should get through:
      1. Confirm PR 244 is safe to merge and document the error-handling pattern   [Dario Kestrel must raise this]
           - Dermot walks through the four commits (clearer value error, more resilient, logging, WIP)
           - Dario reviews the pattern and approves or asks for changes
           - Konrad signals if this unblocks anything downstream
      2. Triage the 12 stale PRs and decide what goes into 0.1.12 vs. post-release   [Dario Kestrel must raise this]
           - Dario lists the blockers: PR 228 (expired batches), possibly PR 78 (vLLM example)
           - Gideon pushes back: PR 161 and PR 163 are examples, not blockers, can wait
           - Konrad agrees and notes PR 106 has been waiting 27 days—likely post-release
      3. Unblock the release by capturing the decision on scope   [Dario Kestrel must raise this]
           - Dario claims PR 228 as a pre-release must-have; assigns someone to pick it up
           - Dermot or Gideon signals availability; if not, it slips
           - Agreement that PR 78 is nice-to-have, goes to post-release or next week
      4. write up Postmortem: Dec 10 revert of batch auto-delete   [Dermot Callaghan must raise this]
           - Dermot Callaghan says they will write Postmortem: Dec 10 revert of batch auto-delete — Explains reverting the auto-delete-after-download behavior in batch mode.
    
    On the agenda: Status of PR 244 and the two merges today; Which of the 12 stale PRs block 0.1.12; Next steps on PR 228 (expired batches) and PR 78 (vLLM example); Postmortem: Dec 10 revert of batch auto-delete
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear list of what lands in 0.1.12 and what defers; PR 244 approved or sent back for revision; the team exits knowing which 2–3 PRs need immediate attention and which 9 can wait.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 111 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - notes-2024-12-09 (Dario Kestrel)
      - Weekly notes: week of Dec 9 - two reverts (Dario Kestrel)
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

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Four commits touching error handling and resilience across the request layer
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm PR 244 is safe to merge and document the error-handling pattern
      2. Triage the 12 stale PRs and decide what goes into 0.1.12 vs. post-release
      3. Unblock the release by capturing the decision on scope
      4. write up Postmortem: Dec 10 revert of batch auto-delete   *** MUST RAISE ***
      5. the page you are writing, Postmortem: Dec 10 revert of batch auto-delete, has to say this in your own words: The counters we already keep per run are hits against the on-disk responses and requests that actually went out to the provider. Those are the same two numbers the summary table prints at the end.   *** MUST SETTLE (clue t1.r2.L14) ***
      6. that the doc "Postmortem: Dec 10 revert of batch auto-delete" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Postmortem: Dec 10 revert of batch auto-delete
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Approval authority on request-handling changes; owns the release; blocked on three older PRs
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 244 is safe to merge and document the error-handling pattern   *** MUST RAISE ***
      2. Triage the 12 stale PRs and decide what goes into 0.1.12 vs. post-release   *** MUST RAISE ***
      3. Unblock the release by capturing the decision on scope   *** MUST RAISE ***
      4. write up Postmortem: Dec 10 revert of batch auto-delete
      5. that the doc "Weekly notes: week of Dec 9 - two reverts" is done, and where the others can find it   *** MUST RAISE ***
      6. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Weekly notes: week of Dec 9 - two reverts" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 244 is safe to merge and document the error-handling pattern
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Fresh approval on PR 237 (OpenAI missing-key error); reviewed PR 242 (Prompter rename)
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 244 is safe to merge and document the error-handling pattern
      2. Triage the 12 stale PRs and decide what goes into 0.1.12 vs. post-release
      3. Unblock the release by capturing the decision on scope
      4. write up Postmortem: Dec 10 revert of batch auto-delete
    goal        Three commits landed, two PRs merged, and a backlog of stale examples and fixes that need sorting before the release.
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just merged the OpenAI fix; understands the error-handling work in flight
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 244 is safe to merge and document the error-handling pattern
      2. Triage the 12 stale PRs and decide what goes into 0.1.12 vs. post-release
      3. Unblock the release by capturing the decision on scope
      4. write up Postmortem: Dec 10 revert of batch auto-delete
    goal        Three commits landed, two PRs merged, and a backlog of stale examples and fixes that need sorting before the release.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear list of what lands in 0.1.12 and what defers; PR 244 approved or sent back for revision; the team exits knowing which 2–3 PRs need immediate attention and which 9 can wait.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nine commits across four core services, two merges, two active workstreams, and last week's two reverts still fresh.

    Today is Wednesday 11 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nine commits across four core services, two merges, two active workstreams, and last week's two reverts still fresh.
    
    What it should get through:
      1. Summarize the commits and confirm they are coherent changes, not scattered fixes   [Dario Kestrel must raise this]
           - Dario notes the commits split between Dermot Callaghan's error handling and Dario Kestrel's WIP, plus Gideon Halloway's formatting
           - Dermot details the four commits: clearer value error, more resilient, logging, and the revert merge
           - Konrad asks if these all feed the same problem or are separate issues
      2. Confirm 0.1.12 is on track and SimpleLLM refactor will not slip it   [Dario Kestrel must raise this]
           - Dario reports: ws-010 (release) is mid-flight, ws-012 (SimpleLLM refactor) is also mid-flight and independent
           - Gideon or Konrad asks if they can land in parallel or if one blocks the other
           - Dario clarifies: refactor is in codebase, release cherry-picks what's stable
      3. Capture what the week's two reverts taught us and whether we are past the instability   [Dario Kestrel must raise this]
           - Konrad or Gideon mentions the two reverts (batch auto-delete, end-of-run retry logic)
           - Dario notes: both reverts are documented, both are fixed approaches landing today (PR 244, PR 237)
           - Dermot confirms: the four commits address the same root causes that the reverts exposed
    
    On the agenda: Summary of today's commits and merges; Status of the two workstreams (release-and-ci, bulk-llm-inference); What broke recently and what's fixed now
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team exits knowing: (1) today's commits are coherent, (2) 0.1.12 is on schedule, (3) the two reverts are behind us and the fixes are in flight or landed, (4) SimpleLLM refactor will not slip the release.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 111 changes merged to date

    On the table
      - postmortem-2024-12-10 (Dermot Callaghan)
      - notes-2024-12-09 (Dario Kestrel)
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Weekly notes: week of Dec 9 - two reverts (Dario Kestrel)
      - postmortem-2024-12-10 (Dermot Callaghan)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
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

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Four focused commits on error clarity and resilience; merged PR 244 earlier in the day
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Summarize the commits and confirm they are coherent changes, not scattered fixes
      2. Confirm 0.1.12 is on track and SimpleLLM refactor will not slip it
      3. Capture what the week's two reverts taught us and whether we are past the instability
    goal        Nine commits across four core services, two merges, two active workstreams, and last week's two reverts still fresh.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the release, the request layer, and the overall pipeline stability; context on all four services touched
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Summarize the commits and confirm they are coherent changes, not scattered fixes   *** MUST RAISE ***
      2. Confirm 0.1.12 is on track and SimpleLLM refactor will not slip it   *** MUST RAISE ***
      3. Capture what the week's two reverts taught us and whether we are past the instability   *** MUST RAISE ***
      4. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly notes: week of Dec 9 - two reverts" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      8. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Summarize the commits and confirm they are coherent changes, not scattered fixes
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Fresh eyes on two merges (PR 237, PR 242); broader context on examples and recipes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Summarize the commits and confirm they are coherent changes, not scattered fixes
      2. Confirm 0.1.12 is on track and SimpleLLM refactor will not slip it
      3. Capture what the week's two reverts taught us and whether we are past the instability
    goal        Nine commits across four core services, two merges, two active workstreams, and last week's two reverts still fresh.
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just landed the OpenAI error-handling fix; insight into what broke and why
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Summarize the commits and confirm they are coherent changes, not scattered fixes
      2. Confirm 0.1.12 is on track and SimpleLLM refactor will not slip it
      3. Capture what the week's two reverts taught us and whether we are past the instability
    goal        Nine commits across four core services, two merges, two active workstreams, and last week's two reverts still fresh.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team exits knowing: (1) today's commits are coherent, (2) 0.1.12 is on schedule, (3) the two reverts are behind us and the fixes are in flight or landed, (4) SimpleLLM refactor will not slip the release.


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Five changes to four core request-handling services, two new PRs merged, and the release engine depends on stability across all four.

    Today is Wednesday 11 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five changes to four core request-handling services, two new PRs merged, and the release engine depends on stability across all four.
    
    What it should get through:
      1. Confirm the error-handling commits (clearer value error, more resilient, logging) follow a consistent pattern   [Dermot Callaghan must raise this]
           - Dermot walks through the four commits and the pattern: clearer messages, defensive checks, better logging
           - Dario reviews and checks whether the pattern covers all four services uniformly
           - Gideon asks if the logging is sufficient for the viewer to surface errors to the user
      2. Confirm all four services are ready for 0.1.12 and no regressions were introduced   [Dario Kestrel must raise this]
           - Dario states: all four services have been touched, PR 244 and PR 237 are merged, no known blockers
           - Dermot notes: the commits are incremental hardening, not rewrites, so risk is low
           - Gideon confirms: no new issues filed against the four services in the last 24 hours
      3. Identify any telemetry or observability work that must land before the release   [Gideon Halloway must raise this]
           - Gideon asks: do we log enough to debug if a user hits these new error conditions?
           - Dermot notes: the logging commit explicitly addresses this
           - Dario agrees: ship it; we can add metrics post-release if needed
    
    On the agenda: Error-handling pattern across the request layer; Status of the four services and whether they are stable for 0.1.12; Any telemetry or observability gaps in the new error paths
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confirms: (1) error-handling pattern is consistent across the four services, (2) PR 244 and PR 237 are stable for release, (3) no telemetry blockers; ship 0.1.12 with confidence.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 111 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - notes-2024-12-09 (Dario Kestrel)
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

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Four commits touching resilience and error handling across all four services; merged PR 244 (graceful error handling for missing requests)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm the error-handling commits (clearer value error, more resilient, logging) follow a consistent pattern   *** MUST RAISE ***
      2. Confirm all four services are ready for 0.1.12 and no regressions were introduced
      3. Identify any telemetry or observability work that must land before the release
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm the error-handling commits (clearer value error, more resilient, logging) follow a consistent pattern
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns all four services; approved PR 244; has context on what's queued and what ships in 0.1.12
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm the error-handling commits (clearer value error, more resilient, logging) follow a consistent pattern
      2. Confirm all four services are ready for 0.1.12 and no regressions were introduced   *** MUST RAISE ***
      3. Identify any telemetry or observability work that must land before the release
      4. what "Weekly notes: week of Dec 9 - two reverts" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm all four services are ready for 0.1.12 and no regressions were introduced
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just merged PR 237 (OpenAIOnline missing-key error); owns observability and run tracking
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm the error-handling commits (clearer value error, more resilient, logging) follow a consistent pattern
      2. Confirm all four services are ready for 0.1.12 and no regressions were introduced
      3. Identify any telemetry or observability work that must land before the release   *** MUST RAISE ***
    goal        Identify any telemetry or observability work that must land before the release
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team confirms: (1) error-handling pattern is consistent across the four services, (2) PR 244 and PR 237 are stable for release, (3) no telemetry blockers; ship 0.1.12 with confidence.


==============================================================================
# 2024-12-16 — 5 conversation(s), 50 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs landed on timeout, retry, and response handling in 48 hours; PR 266 is still open and needs approval before the 0.1.12 cut.

    Today is Monday 16 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs landed on timeout, retry, and response handling in 48 hours; PR 266 is still open and needs approval before the 0.1.12 cut.
    
    What it should get through:
      1. Get PR 266 (retry on response format failure) to approved and ready for merge   [Dario Kestrel must raise this]
           - Dario walks through the response format handling logic and why the retry is safe
           - Konrad checks whether it blocks the release or can wait for 0.1.13
           - Dario confirms it's release-critical and should land today
      2. Confirm timeout and retry chains don't break metadata + cache verification interaction   [Petar Kovalenko must raise this]
           - Petar surfaces whether PR PR 257 (metadata + cache verification) saw any issues with the timeout changes
           - Dario explains the timeout happens before the metadata write, so no regression
           - Konrad signs off that the interaction is clean
      3. Decide which fixes need a runbook entry or operator guidance   [Dario Kestrel must raise this]
           - Dario flags that the timeout default and retry logic should be in the runbook
           - Konrad agrees; notes it belongs in the 0.1.12 release notes
           - Dario volunteers to fold it into the runbook-bulk-llm-inference doc today
      4. write up Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will write Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254) — Explains reverting the LLM-class context-manager refactor for batch parameters.
    
    On the agenda: Review PR 266 (retry on response format failure) against the three merged PRs (PR 263, PR 264, PR 265); Confirm timeout defaults and retry chains don't regress cache verification or metadata handling; Check whether any of these changes need runbook entries or operator guidance; Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 266 approved, confirmed safe to land; runbook entry queued for timeout and retry behavior; confidence that the four PR sequence (263, 264, 265, 266) doesn't create regressions in metadata or cache.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 127 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Postmortem: Dec 10 revert of batch auto-delete (Dermot Callaghan)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Authority on timeout strategy and retry logic across request processors
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get PR 266 (retry on response format failure) to approved and ready for merge   *** MUST RAISE ***
      2. Confirm timeout and retry chains don't break metadata + cache verification interaction
      3. Decide which fixes need a runbook entry or operator guidance   *** MUST RAISE ***
      4. write up Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)
      5. the page you are writing, Runbook: handling curator.LLM incidents, has to say this in your own words: Putting this in the runbook because it keeps coming up: attaching extra metadata columns to a dataset for bookkeeping should come back free on the next run. It is the same set of requests going to the same place, nothing about the work changed.   *** MUST SETTLE (clue t1.r1.l_prompt_2) ***
      6. that the doc "Runbook: handling curator.LLM incidents" is done, and where the others can find it   *** MUST RAISE ***
      7. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      8. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 266 (retry on response format failure) to approved and ready for merge
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release-gate perspective on whether these fixes block 0.1.12
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get PR 266 (retry on response format failure) to approved and ready for merge
      2. Confirm timeout and retry chains don't break metadata + cache verification interaction
      3. Decide which fixes need a runbook entry or operator guidance
      4. write up Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)   *** MUST RAISE ***
      5. that the doc "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)" is done, and where the others can find it   *** MUST RAISE ***
      6. that "Weekly update: week of Dec 9" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. Fresh perspective on whether the metadata + cache verification (PR PR 257) interacts cleanly with the new timeouts
    owns        (nothing specific)
    agenda
      1. Get PR 266 (retry on response format failure) to approved and ready for merge
      2. Confirm timeout and retry chains don't break metadata + cache verification interaction   *** MUST RAISE ***
      3. Decide which fixes need a runbook entry or operator guidance
      4. write up Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254)
      5. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm timeout and retry chains don't break metadata + cache verification interaction
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 266 approved, confirmed safe to land; runbook entry queued for timeout and retry behavior; confidence that the four PR sequence (263, 264, 265, 266) doesn't create regressions in metadata or cache.


------------------------------------------------------------------------------
## #engineering — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 35 commits landed over the weekend; four PRs merged on timeout/retry; SimpleLLM folding work is mid-flight and needs to coordinate with what just landed.

    Today is Monday 16 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 35 commits landed over the weekend; four PRs merged on timeout/retry; SimpleLLM folding work is mid-flight and needs to coordinate with what just landed.
    
    What it should get through:
      1. Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding   [Dario Kestrel must raise this]
           - Dario summarizes: timeout defaults (PR 265), retry on response format (PR 266 pending), small fixes and logging cleanup (PR 263, PR 264)
           - Konrad notes the pattern: defensive defaults + robust retry chains, which is good for refactoring stability
           - Dermot asks whether the default timeout affects SimpleLLM's factory — Dario Kestrel says no, it's inline in the request processor
      2. Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring   [Konrad Feltrin must raise this]
           - Konrad surfaces the December 13 revert: batch context-manager refactor broke parameter threading
           - Petar notes the new metadata cache verification didn't hit that pattern
           - Dario proposes: SimpleLLM factory stays stateless, no context-manager changes, folding happens in config discovery layer only
      3. Plan SimpleLLM folding without repeating batch-parameter instability   [Dermot Callaghan must raise this]
           - Dermot outlines the SimpleLLM refactor surface: LLM-class factory, backend detection, config inheritance
           - Konrad flags: each of those is orthogonal to timeout defaults; they can land separately
           - Dario agrees and volunteers to land timeout defaults first, then SimpleLLM config in the next batch
    
    On the agenda: Understand what the four timeout/retry PRs landed and why; Confirm SimpleLLM folding isn't blocked or destabilized by these changes; Plan the next refactor without repeating the batch-parameter revert risk
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clear understanding that timeout/retry work and SimpleLLM folding are orthogonal; batch revert patterns understood; plan to land SimpleLLM config changes in separate, small steps to reduce rollback risk.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 127 changes merged to date

    On the table
      - Postmortem: Dec 10 revert of batch auto-delete (Dermot Callaghan)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
      - postmortem-2024-12-13 (Konrad Feltrin)
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Clear picture of what landed on timeout/retry/response-format; knows the state of PR 266
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding   *** MUST RAISE ***
      2. Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring
      3. Plan SimpleLLM folding without repeating batch-parameter instability
      4. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release-gate view; understands what the postmortem on PR PR 254 (batch context manager revert) means for refactoring risk
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding
      2. Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring   *** MUST RAISE ***
      3. Plan SimpleLLM folding without repeating batch-parameter instability
      4. what "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Design perspective on SimpleLLM integration; knows what the config bugs from the backend-params split looked like
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding
      2. Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring
      3. Plan SimpleLLM folding without repeating batch-parameter instability   *** MUST RAISE ***
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Plan SimpleLLM folding without repeating batch-parameter instability
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. Just landed metadata + cache verification; can spot if timeout work created new failure modes
    owns        (nothing specific)
    agenda
      1. Confirm timeout/retry/response-format sequence is coherent and won't block SimpleLLM folding
      2. Understand the batch context-manager revert (PR PR 254) and what to avoid in SimpleLLM refactoring
      3. Plan SimpleLLM folding without repeating batch-parameter instability
    goal        35 commits landed over the weekend; four PRs merged on timeout/retry; SimpleLLM folding work is mid-flight and needs to coordinate with what just landed.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear understanding that timeout/retry work and SimpleLLM folding are orthogonal; batch revert patterns understood; plan to land SimpleLLM config changes in separate, small steps to reduce rollback risk.


------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: The 0.1.12 release is mid-flight; four PRs landed on timeout/retry over the weekend; PR 266 is still pending and the release gate needs to know whether it blocks the cut.

    Today is Monday 16 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The 0.1.12 release is mid-flight; four PRs landed on timeout/retry over the weekend; PR 266 is still pending and the release gate needs to know whether it blocks the cut.
    
    What it should get through:
      1. Decide 0.1.12 release scope: is PR 266 required or can it wait for 0.1.13?   [Dario Kestrel must raise this]
           - Dario flags PR 266 (retry on response format failure) as a defensive improvement but not a blocker for the release
           - Konrad weighs the risk: if we ship without it, do we get more response-format errors in the wild?
           - Dario says the timeout defaults (PR 265) will catch most of them; PR 266 makes the retry more surgical. Can wait for 0.1.13.
      2. Confirm timeout defaults are safe to ship in 0.1.12   [Konrad Feltrin must raise this]
           - Konrad asks: does a 10-minute default timeout break any documented workflows?
           - Dario says no; the docs and examples all use inline timeout or rely on provider defaults. This is a safe fallback.
           - Konrad approves shipping it as part of 0.1.12.
      3. Create release notes entry for timeout behavior and runbook guidance   [Dario Kestrel must raise this]
           - Dario commits to adding a release notes line: 'Default timeout for online requests now 10 minutes; can be overridden per-request'
           - Konrad agrees and notes the runbook entry (Dario Kestrel is already writing) should be published alongside the release notes
           - Plan: release notes + runbook both go into the 0.1.12 cut
    
    On the agenda: Decide whether the 0.1.12 release includes PR 266 or ships without it; Confirm the timeout defaults and retry logic are safe to ship; Plan the release notes and any operator guidance needed
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: 0.1.12 release scope locked: PR 266 deferred to 0.1.13; timeout defaults approved for shipping; release notes and runbook entries committed for today.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 127 changes merged to date

    On the table
      - Postmortem: Dec 10 revert of batch auto-delete (Dermot Callaghan)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Knows what landed and is landing; has visibility into PR 266 (retry on response format) and whether it blocks the cut
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Decide 0.1.12 release scope: is PR 266 required or can it wait for 0.1.13?   *** MUST RAISE ***
      2. Confirm timeout defaults are safe to ship in 0.1.12
      3. Create release notes entry for timeout behavior and runbook guidance   *** MUST RAISE ***
      4. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Decide 0.1.12 release scope: is PR 266 required or can it wait for 0.1.13?
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Release-gate authority; wrote the postmortem on the batch context-manager revert and understands the stability risks
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Decide 0.1.12 release scope: is PR 266 required or can it wait for 0.1.13?
      2. Confirm timeout defaults are safe to ship in 0.1.12   *** MUST RAISE ***
      3. Create release notes entry for timeout behavior and runbook guidance
    goal        Confirm timeout defaults are safe to ship in 0.1.12
    available   around today

### 4. How it should land

    lands as  partial
    leaving   0.1.12 release scope locked: PR 266 deferred to 0.1.13; timeout defaults approved for shipping; release notes and runbook entries committed for today.


------------------------------------------------------------------------------
## #pipeline — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 16 changes to bulk-llm-inference, online-request-processing, and provider-integrations just landed; four PRs on timeout/retry; the pipeline team needs to confirm the changes don't create regressions in cache, metadata, or observability.

    Today is Monday 16 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 16 changes to bulk-llm-inference, online-request-processing, and provider-integrations just landed; four PRs on timeout/retry; the pipeline team needs to confirm the changes don't create regressions in cache, metadata, or observability.
    
    What it should get through:
      1. Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines   [Dario Kestrel must raise this]
           - Dario walks through where the timeout is set: OnlineRequestProcessor only, not batch or offline
           - Dermot asks whether batch jobs can inherit the timeout — Dario Kestrel says no, batch uses provider-specific timeouts
           - Gideon confirms the observability side: timeout events are logged as retries, not as separate timeout telemetry
      2. Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains   [Petar Kovalenko must raise this]
           - Petar explains PR PR 257: metadata dict + cache verification added to every response
           - Dario confirms: metadata write happens after response succeeds, so timeout doesn't interfere
           - Gideon notes: good; metadata will be consistent with what got cached
      3. Define what timeout and retry events get logged for troubleshooting and cost tracking   [Gideon Halloway must raise this]
           - Gideon asks: should we log timeout events separately from provider errors?
           - Dario says the current logging treats timeouts as retries; that's fine, but add a structured log field 'timeout_reached=true' for filtering
           - Gideon agrees; will add that to the observability setup
    
    On the agenda: Confirm the 10-minute timeout default is safe across online and batch request processors; Verify metadata + cache verification works cleanly with timeout and retry logic; Decide what timeout and retry events need to be logged or tracked for observability
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Timeout default is confirmed safe for online-only use; batch and offline pipelines unaffected; metadata + cache verification interaction verified clean; observability plan includes timeout-specific logging fields.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 5 release(s) shipped, currently v0.1.11
      - 127 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
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
      - — and 1203 function/class names and 165 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Expert on timeout and retry mechanics; just landed four PRs refining them; knows the state of PR 266
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines   *** MUST RAISE ***
      2. Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains
      3. Define what timeout and retry events get logged for troubleshooting and cost tracking
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines
    available   around today

  Petar Kovalenko  (petar)
    role        Engineer, Request-Processing Internals. Just landed metadata + cache verification; can spot timeout interaction issues
    owns        (nothing specific)
    agenda
      1. Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines
      2. Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains   *** MUST RAISE ***
      3. Define what timeout and retry events get logged for troubleshooting and cost tracking
      4. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability perspective on timeout behavior; knows what metrics and logs matter
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines
      2. Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains
      3. Define what timeout and retry events get logged for troubleshooting and cost tracking   *** MUST RAISE ***
    goal        Define what timeout and retry events get logged for troubleshooting and cost tracking
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Cross-service view; can spot if timeout defaults affect offline or batch pipelines
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm 10-minute timeout default is safe for online requests and doesn't affect batch or offline pipelines
      2. Verify metadata + cache verification (PR PR 257) works cleanly with timeout and retry chains
      3. Define what timeout and retry events get logged for troubleshooting and cost tracking
    goal        16 changes to bulk-llm-inference, online-request-processing, and provider-integrations just landed; four PRs on timeout/retry; the pipeline team needs to confirm the changes don't create regressions in cache, metadata, or observability.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Timeout default is confirmed safe for online-only use; batch and offline pipelines unaffected; metadata + cache verification interaction verified clean; observability plan includes timeout-specific logging fields.


------------------------------------------------------------------------------
## #general — 8 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Petar just joined the team (active today); Konrad Feltrin is writing the onboarding doc; general channel is the place to welcome and set context for the team.

    Today is Monday 16 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Petar just joined the team (active today); Konrad Feltrin is writing the onboarding doc; general channel is the place to welcome and set context for the team.
    
    On the agenda: Introduce Petar Kovalenko and their role in request-processing internals; Lay out the onboarding resources: doc (Konrad Feltrin writing), runbook, design doc; Signpost the early priorities: understand batch vs. online flow, then metadata + cache verification integration
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Petar welcomed; onboarding doc and resources clearly signposted; early priorities clear (batch vs. online, then metadata integration); team aware of Petar Kovalenko's arrival and first-day contribution.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    background  You work with these people. None of that matters here.
    goal        just chatting, nothing work related: Welcome Petar Kovalenko and set context on their role in request-processing internals

  Dario Kestrel  (dario)
    background  You work with these people. None of that matters here.
    goal        just chatting, nothing work related: Welcome Petar Kovalenko and set context on their role in request-processing internals

  Dermot Callaghan  (dermot)
    background  You work with these people. None of that matters here.
    goal        just chatting, nothing work related: Welcome Petar Kovalenko and set context on their role in request-processing internals

  Gideon Halloway  (gideon)
    background  You work with these people. None of that matters here.
    goal        just chatting, nothing work related: Welcome Petar Kovalenko and set context on their role in request-processing internals

  Petar Kovalenko  (petar)
    background  You work with these people. None of that matters here.
    goal        just chatting, nothing work related: Welcome Petar Kovalenko and set context on their role in request-processing internals


==============================================================================
# 2024-12-17 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: 0.1.12 shipped today; tag is out; release notes due; announce mail due

    Today is Tuesday 17 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 0.1.12 shipped today; tag is out; release notes due; announce mail due
    
    What it should get through:
      1. Release notes capture what shipped   [Dario Kestrel must raise this]
           - Dario sketches the eight merged PRs
           - Konrad confirms the changelog is complete
           - Dario posts release-v0-1-12
      2. Announce the release to the team   [Dario Kestrel must raise this]
           - Dario confirms the tag is live
           - Konrad checks it resolves
           - Dario posts announce-v0-1-12 mail
    
    On the agenda: Confirm v0.1.12 is tagged and live; Write and post release notes; Decide on next release cadence
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.12 is tagged, release notes are written and posted, announcement mail is sent to the team
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 135 changes merged to date

    On the table
      - v0.1.12 release notes (Dario Kestrel)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
      - Postmortem: Dec 10 revert of batch auto-delete (Dermot Callaghan)
      - Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254) (Konrad Feltrin)
      - announce-v0-1-12 (Dario Kestrel)
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
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. merged all 8 PRs that shipped in 0.1.12; knows what changed and why
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture what shipped   *** MUST RAISE ***
      2. Announce the release to the team   *** MUST RAISE ***
      3. that the doc "v0.1.12 release notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.12 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture what shipped
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. second pair of eyes on every change; saw the full arc from PR through merge
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Release notes capture what shipped
      2. Announce the release to the team
    goal        0.1.12 shipped today; tag is out; release notes due; announce mail due
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.12 is tagged, release notes are written and posted, announcement mail is sent to the team

