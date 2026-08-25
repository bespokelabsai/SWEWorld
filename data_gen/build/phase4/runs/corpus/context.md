# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-02-28 — 4 conversation(s), 41 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.20 shipped today; release notes due, announcement ready to send.

    Today is Friday 28 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.20 shipped today; release notes due, announcement ready to send.
    
    What it should get through:
      1. Release notes accurately summarize the four merged PRs and their surface-level impact.   [Dario Kestrel must raise this]
           - Dario Kestrel: here's what I wrote for 0.1.20, covering the four merges
           - Emil Brandvold: Claude 3.7 Reasoning is the headline, litellm gen params is a quiet refactor, session id + viewer resume is the push-to-viewer fix
           - Dario Kestrel: nods, updates the install-command note, publishes
      2. Announcement goes out to stakeholders same day, with install instructions confirmed.   [Dario Kestrel must raise this]
           - Dario Kestrel: the fix in PR 555 is one-liner, just making sure install docs match it
           - Emil Brandvold: already tested, looks good
    
    On the agenda: Release notes capture: Claude 3.7, gen params in litellm, session id in metadata, viewer resume, test coverage; Verify install command fix is documented; Confirm announcement recipients and timing
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.20 release notes published and announcement sent; team and stakeholders notified same day.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - Release notes: v0.1.20 (Dario Kestrel)
      - Release notes: 0.1.19 (Gideon Halloway)
      - announce-v0-1-20 (Dario Kestrel)
      - release-v0-1-20 (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Release lead; owns the tag, the changelog summary, and the announcement. Merged Claude 3.7, the gen params refactor, and the install command fix.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes accurately summarize the four merged PRs and their surface-level impact.   *** MUST RAISE ***
      2. Announcement goes out to stakeholders same day, with install instructions confirmed.   *** MUST RAISE ***
      3. the page you are writing, Release notes: v0.1.20, has to say this in your own words: Release checklist note for the code execution backend: the container the library ships against does not update itself and there is nothing in the codebase that will tell you it is stale. Before you touch that line, go and check what the image status notes say, otherwise you are guessing.   *** MUST SETTLE (clue t4.r1.L11) ***
      4. that the doc "Release notes: v0.1.20" is done, and where the others can find it   *** MUST RAISE ***
      5. that "v0.1.20 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      6. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes accurately summarize the four merged PRs and their surface-level impact.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Drove four of the five workstreams that landed in this release. Knows what multimodal/litellm test coverage gaps just closed and what the hosted-curator session-id change means.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Release notes accurately summarize the four merged PRs and their surface-level impact.
      2. Announcement goes out to stakeholders same day, with install instructions confirmed.
    goal        v0.1.20 shipped today; release notes due, announcement ready to send.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.20 release notes published and announcement sent; team and stakeholders notified same day.


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs stale >2 days; Gideon Halloway opened cost-estimation epics today (PR 559–PR 563) and has PR 546 in flight; Dario Kestrel and Emil Brandvold are senior reviewers.

    Today is Friday 28 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs stale >2 days; Gideon Halloway opened cost-estimation epics today (PR 559–PR 563) and has PR 546 in flight; Dario Kestrel and Emil Brandvold are senior reviewers.
    
    What it should get through:
      1. PR 546 either gets a clear path to landing or gets explicit feedback on what needs to change.   [Gideon Halloway must raise this]
           - Gideon Halloway: PR 546 is the first of the cost estimation work, online processors pre/post-call estimation
           - Dario Kestrel: code looks sound, question is whether this goes in before the status-tracker refactor (PR 557–PR 558)
           - Emil Brandvold: they can be parallel; 546 is the logic, 557/558 is the infrastructure. ship 546.
      2. PR 468 disposition clear: still waiting on something, or can it land?   [Dario Kestrel must raise this]
           - Dario Kestrel: PR 468 has been open 21 days; Emil Brandvold reviewed it, where are we?
           - Emil Brandvold: not blocking anything critical right now. can defer past 0.1.21 if cost estimation takes priority.
      3. Cost-estimation epic scope settled: which of the five issues (PR 559–PR 563) are in scope for this sprint.   [Gideon Halloway must raise this]
           - Gideon Halloway: opened five sub-tasks for the cost estimation work today. what's the priority?
           - Dario Kestrel: PR 560 and PR 563 (online and batch status trackers) are the core; PR 561 and PR 562 are nice-to-have polish.
           - Gideon Halloway: understood; I'll start with 560.
    
    On the agenda: Status of PR 546 (Cost Estimation revamp [1/n] Online processors): blockers, readiness; Status of PR 468 (n samples support): 21 days open, still blocked?; Triage the cost-estimation epics (PR 559–PR 563): which land this sprint?
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 546 gets explicit approval or actionable feedback; PR 468 gets a decision (land or defer); cost-estimation work is ordered by priority.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost Estimation Revamp: knows what PR 546 is trying to do—pre/post API call cost estimation for online processors. Has 15 commits today on token accounting and unified TokenCount/TokenUsage.
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. PR 546 either gets a clear path to landing or gets explicit feedback on what needs to change.   *** MUST RAISE ***
      2. PR 468 disposition clear: still waiting on something, or can it land?
      3. Cost-estimation epic scope settled: which of the five issues (PR 559–PR 563) are in scope for this sprint.   *** MUST RAISE ***
    goal        PR 546 either gets a clear path to landing or gets explicit feedback on what needs to change.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior context on request-processing architecture. Reviewed both stale PRs at various points.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. PR 546 either gets a clear path to landing or gets explicit feedback on what needs to change.
      2. PR 468 disposition clear: still waiting on something, or can it land?   *** MUST RAISE ***
      3. Cost-estimation epic scope settled: which of the five issues (PR 559–PR 563) are in scope for this sprint.
    goal        PR 468 disposition clear: still waiting on something, or can it land?
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Approved PR 552 today; reviewed the others. Knows what landed in 0.1.20 and what's still open.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 546 either gets a clear path to landing or gets explicit feedback on what needs to change.
      2. PR 468 disposition clear: still waiting on something, or can it land?
      3. Cost-estimation epic scope settled: which of the five issues (PR 559–PR 563) are in scope for this sprint.
    goal        Two PRs stale >2 days; Gideon Halloway opened cost-estimation epics today (PR 559–PR 563) and has PR 546 in flight; Dario Kestrel and Emil Brandvold are senior reviewers.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 546 gets explicit approval or actionable feedback; PR 468 gets a decision (land or defer); cost-estimation work is ordered by priority.


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Gideon landed 15 commits today on token accounting unification; Dario Kestrel and Emil Brandvold reviewed and committed to the pipeline; this is the core refactor that cost-estimation work (PR 546) depends on.

    Today is Friday 28 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon landed 15 commits today on token accounting unification; Dario Kestrel and Emil Brandvold reviewed and committed to the pipeline; this is the core refactor that cost-estimation work (PR 546) depends on.
    
    What it should get through:
      1. Token accounting refactor is consistent across all request types (online, batch, offline) and field names no longer leak old TokenCount references.   [Gideon Halloway must raise this]
           - Gideon Halloway: unified TokenCount with TokenUsage throughout codebase, fixed field names, put total in init
           - Dario Kestrel: diffs show the old current_cost gone, running average in place. any remaining TokenCount refs?
           - Gideon Halloway: checked; offline and the test suite all aligned now.
      2. Cost-estimation logic (pre/post API call) uses the running average correctly and doesn't double-count or lose precision.   [Gideon Halloway must raise this]
           - Gideon Halloway: pre-call estimate uses average of prior calls, post-call adjusts with actual usage
           - Dario Kestrel: what happens if the first call is wildly different from the average?
           - Gideon Halloway: the post-call adjustment catches it; next call uses the updated average.
      3. Batch-mode cost tracking aligns with the unified model and doesn't regress on accuracy.   [Dario Kestrel must raise this]
           - Dario Kestrel: batch processes thousands of requests; cost reporting has to be spot-on
           - Emil Brandvold: batch status tracker (PR 563) will handle the pre/post call estimation same way online does
           - Dario Kestrel: good; we're consistent.
    
    On the agenda: Token accounting unified across online, batch, and offline: TokenCount/TokenUsage names consistent; Cost-estimation pre/post-call logic: is the running average correct?; Batch-mode cost tracking: does it work with the unified model?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Token accounting unified and cost-estimation logic verified; no regressions in batch-mode cost tracking.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 15 commits today on token accounting. Unified TokenCount with TokenUsage, fixed token_usage field names, put total in initialization. Knows the unified model inside and out.
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Token accounting refactor is consistent across all request types (online, batch, offline) and field names no longer leak old TokenCount references.   *** MUST RAISE ***
      2. Cost-estimation logic (pre/post API call) uses the running average correctly and doesn't double-count or lose precision.   *** MUST RAISE ***
      3. Batch-mode cost tracking aligns with the unified model and doesn't regress on accuracy.
    goal        Token accounting refactor is consistent across all request types (online, batch, offline) and field names no longer leak old TokenCount references.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior architect of the request pipeline. Reviewed Gideon Halloway's token work. Knows where batch-mode and the other processors need to align.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Token accounting refactor is consistent across all request types (online, batch, offline) and field names no longer leak old TokenCount references.
      2. Cost-estimation logic (pre/post API call) uses the running average correctly and doesn't double-count or lose precision.
      3. Batch-mode cost tracking aligns with the unified model and doesn't regress on accuracy.   *** MUST RAISE ***
    goal        Batch-mode cost tracking aligns with the unified model and doesn't regress on accuracy.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Merged the gen params refactor (PR 552) today. Knows the litellm backend and how it reports token usage; also owns the provider-integrations side.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Token accounting refactor is consistent across all request types (online, batch, offline) and field names no longer leak old TokenCount references.
      2. Cost-estimation logic (pre/post API call) uses the running average correctly and doesn't double-count or lose precision.
      3. Batch-mode cost tracking aligns with the unified model and doesn't regress on accuracy.
    goal        Gideon landed 15 commits today on token accounting unification; Dario Kestrel and Emil Brandvold reviewed and committed to the pipeline; this is the core refactor that cost-estimation work (PR 546) depends on.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Token accounting unified and cost-estimation logic verified; no regressions in batch-mode cost tracking.


------------------------------------------------------------------------------
## #help — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: a user posted a traceback and Dermot Callaghan recognised it as the third variant of the same class of problem this week

    Today is Friday 28 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: a user posted a traceback and Dermot Callaghan recognised it as the third variant of the same class of problem this week
    
    What it should get through:
    
    On the agenda: Dermot Callaghan walks through the OpenAI strict-mode rejection a user hit: the model had a field with a default on it and strict mode would not take the schema, which the user reasonably read as a curator bug; Gideon Halloway adds the one he answered on Monday, where a Gemini run refused a model with an Optional field and the user rewrote the whole schema by trial and error before asking; Dario Kestrel says the two do not have the same rule behind them and he does not want a check that only knows OpenAI's rules and then lies about everything else
    
    Wrap when: three concrete rejection cases collected in one thread; no rule set derived from them yet, and Anthropic's tool-shaped path is noted as unexamined; it is settled that the team agrees changing temperature currently returns the previous run's outputs
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: temperature.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        a user posted a traceback and Dermot Callaghan recognised it as the third variant of the same class of problem this week
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Bumped temperature from 0 to 1.2 on the poem set to get some variety and got the identical 5k rows back. I spent an hour convinced vLLM was ignoring temperature before I worked out where they were coming from.   *** MUST SETTLE (clue t1.r1.l_params_1) ***
         must contain literally: temperature
    goal        the team agrees changing temperature currently returns the previous run's outputs
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        a user posted a traceback and Dermot Callaghan recognised it as the third variant of the same class of problem this week
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   three concrete rejection cases collected in one thread; no rule set derived from them yet, and Anthropic's tool-shaped path is noted as unexamined; it is settled that the team agrees changing temperature currently returns the previous run's outputs


==============================================================================
# 2025-03-01 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #incidents — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Three reverts in one day on core request processing; main branch stability and v0.1.20 release viability need confirmation.

    Today is Saturday 1 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three reverts in one day on core request processing; main branch stability and v0.1.20 release viability need confirmation.
    
    What it should get through:
      1. Understand revert scope and confirm main is stable for release   [Gideon Halloway must raise this]
           - Gideon lays out the three reverts: output token defaults twice, integration tests once
           - Dario checks whether v0.1.20 release notes (already written) assume these changes landed
           - Emil clarifies the deepseek token dump issue that triggered it
      2. Decide whether to reland or defer the token-default fix   [Emil Brandvold must raise this]
           - Gideon outlines the cost projection and success-rate tracking changes that got caught up
           - Emil weighs whether the fix is necessary for Gemini work or can be a follow-on
           - Dario notes if this blocks anything in the next sprint
    
    On the agenda: State what reverted and why; Assess damage to online processing and multimodal; Decide if fixes need to land today or can wait
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Confirmation that v0.1.20 is shippable as-is and reverted code is understood well enough to address properly next week, or decision to reland a narrower fix before release.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - Release notes: v0.1.20 (someone)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. The reverts themselves: output token defaults and integration test passes that went sideways
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Understand revert scope and confirm main is stable for release   *** MUST RAISE ***
      2. Decide whether to reland or defer the token-default fix
      3. what "release-v0-1-20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand revert scope and confirm main is stable for release
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing context and whether this blocks the release
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Understand revert scope and confirm main is stable for release
      2. Decide whether to reland or defer the token-default fix
    goal        Three reverts in one day on core request processing; main branch stability and v0.1.20 release viability need confirmation.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider integration perspective on the token default issue
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand revert scope and confirm main is stable for release
      2. Decide whether to reland or defer the token-default fix   *** MUST RAISE ***
    goal        Decide whether to reland or defer the token-default fix
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Confirmation that v0.1.20 is shippable as-is and reverted code is understood well enough to address properly next week, or decision to reland a narrower fix before release.


------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two open PRs older than the era median merge time; both touch core request processing and observer layer.

    Today is Saturday 1 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two open PRs older than the era median merge time; both touch core request processing and observer layer.
    
    What it should get through:
      1. Determine if PR 546 (cost estimation) can move to merge   [Gideon Halloway must raise this]
           - Gideon notes the reverts mean the cost tracking commits need re-review or rebasing
           - Dario or Emil checks whether the reverts affect the cost estimation logic itself
      2. Clarify status of PR 468 (n samples) and whether it is blocked   [Emil Brandvold must raise this]
           - Emil states whether Gemini work (ws-040) depends on n samples landing
           - Gideon notes if this is blocked on something else or just needs a review pass
    
    On the agenda: Check PR 546 status and what it needs; Assess PR 468 age and next steps
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear signal on whether PR 546 can land after revert triage, and whether PR 468 should be revived or deferred to next cycle.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - Release notes: v0.1.20 (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. New commits on PR 546 (cost estimation) and context on what is blocking it
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Determine if PR 546 (cost estimation) can move to merge   *** MUST RAISE ***
      2. Clarify status of PR 468 (n samples) and whether it is blocked
      3. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine if PR 546 (cost estimation) can move to merge
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. PR 468 context (n samples support) and whether it needs review or is waiting on something else
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if PR 546 (cost estimation) can move to merge
      2. Clarify status of PR 468 (n samples) and whether it is blocked   *** MUST RAISE ***
    goal        Clarify status of PR 468 (n samples) and whether it is blocked
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear signal on whether PR 546 can land after revert triage, and whether PR 468 should be revived or deferred to next cycle.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 14 commits to online-request-processing and 11 to provider-integrations, including a double revert on token defaults; core request path needs triage before release.

    Today is Saturday 1 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 14 commits to online-request-processing and 11 to provider-integrations, including a double revert on token defaults; core request path needs triage before release.
    
    What it should get through:
      1. Untangle cost projection logic and revert fallout   [Gideon Halloway must raise this]
           - Gideon walks through the cost projection commits: success/in-process stats first, then weighted-avg cost with success factor
           - Dario or Emil flags whether the revert leaves a gap in cost estimation or if the approach is sound but timing was off
      2. Resolve output token default handling for deepseek and Gemini   [Emil Brandvold must raise this]
           - Gideon explains the deepseek issue: 0 output tokens causing request dump; the fix and why it reverted
           - Emil notes whether Gemini rate-limit work needs token defaults to be locked down first
      3. Validate online request stability for v0.1.20   [Dario Kestrel must raise this]
           - Dario checks that v0.1.20 release notes do not assume reverted changes
           - Gideon confirms that initialization, cost tracking, and token handling are internally consistent after reverts
    
    On the agenda: Map out what changed on cost projection and why it reverted; Align on token-default handling across providers; Confirm online request path is stable for release
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Agreement on which cost/token changes should reland post-release and confirmation that online request path is safe to ship.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - Release notes: v0.1.20 (Dario Kestrel)
      - Release notes: v0.1.20 (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. The day's 12 commits on cost projection, output tokens, and request initialization; the reverts and what they mean for the request path
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Untangle cost projection logic and revert fallout   *** MUST RAISE ***
      2. Resolve output token default handling for deepseek and Gemini
      3. Validate online request stability for v0.1.20
      4. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Untangle cost projection logic and revert fallout
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini-specific rate limit and token-usage work (ws-040); perspective on whether token defaults matter for provider stability
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Untangle cost projection logic and revert fallout
      2. Resolve output token default handling for deepseek and Gemini   *** MUST RAISE ***
      3. Validate online request stability for v0.1.20
    goal        Resolve output token default handling for deepseek and Gemini
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Release readiness; whether the reverted changes should have been in v0.1.20 or are correctly deferred
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Untangle cost projection logic and revert fallout
      2. Resolve output token default handling for deepseek and Gemini
      3. Validate online request stability for v0.1.20   *** MUST RAISE ***
      4. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate online request stability for v0.1.20
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Agreement on which cost/token changes should reland post-release and confirmation that online request path is safe to ship.


------------------------------------------------------------------------------
## #viewer — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Six changes to progress-and-cli; cost projection reverted; display surface needs to stay consistent with request processing.

    Today is Saturday 1 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six changes to progress-and-cli; cost projection reverted; display surface needs to stay consistent with request processing.
    
    What it should get through:
      1. Ensure progress tracking is coherent with cost estimation after reverts   [Gideon Halloway must raise this]
           - Gideon notes which progress commits depend on the cost commits that reverted
           - Emil checks whether the progress display will degrade or is independent of the reverted cost logic
      2. Confirm run summary and token counters reflect current cost approach   [Emil Brandvold must raise this]
           - Emil reviews whether the end-of-run tables need updates to match the cost estimation refresh
           - Gideon confirms that the commits that landed leave the display surface in a consistent state
    
    On the agenda: Audit progress display against reverted cost changes; Confirm cost counters and run-summary tables are aligned
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Validation that progress bars, cost counters, and summary tables are safe to ship as-is, or identification of display tweaks needed before release.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 280 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Six commits on progress tracking and cost projection; what changed and why the cost-side commits reverted
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Ensure progress tracking is coherent with cost estimation after reverts   *** MUST RAISE ***
      2. Confirm run summary and token counters reflect current cost approach
    goal        Ensure progress tracking is coherent with cost estimation after reverts
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Perspective on whether progress updates are blocked on the cost projection stabilizing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Ensure progress tracking is coherent with cost estimation after reverts
      2. Confirm run summary and token counters reflect current cost approach   *** MUST RAISE ***
    goal        Confirm run summary and token counters reflect current cost approach
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Validation that progress bars, cost counters, and summary tables are safe to ship as-is, or identification of display tweaks needed before release.


==============================================================================
# 2025-03-03 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil opened three PRs today; two are fresh, one is a quick fix already approved

    Today is Monday 3 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil opened three PRs today; two are fresh, one is a quick fix already approved
    
    What it should get through:
      1. RAFT block lands with API shape locked   [Emil Brandvold must raise this]
           - Emil walks through the block API and example usage
           - Konrad pushes back on shape consistency with SimpleStrat
           - Landing: approved with minor style cleanup
      2. Parsing and dataset creation fixes merge cleanly   [Emil Brandvold must raise this]
           - Dermot confirms PR 574 is solid; Emil clarifies PR 573 interaction with caching
           - Both land without changes
      3. write up Handover: Packaging, Version Bumps & Release Cutting   [Dermot Callaghan must raise this]
           - Dermot Callaghan says they will write Handover: Packaging, Version Bumps & Release Cutting — Dermot's write-up handing the release-cutting role (version bumps, tagging, packaging) to Emil Brandvold.
      4. write up Q2 Plan: Consolidation and Provider Breadth   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will write Q2 Plan: Consolidation and Provider Breadth — Konrad's kickoff plan for slowing the pace, squashing PRs, and pruning provider integrations after the Stratos sprint.
    
    On the agenda: RAFT block and example implementation (PR 571); Parse method hash and fingerprint (PR 573); Process response mandatory in dataset files (PR 574); Handover: Packaging, Version Bumps & Release Cutting; Q2 Plan: Consolidation and Provider Breadth
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 574 merges today; PR 571 approved pending style pass; PR 573 queued for merge
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 281 changes merged to date

    On the table
      - Handover: Packaging, Version Bumps & Release Cutting (Dermot Callaghan)
      - Handover: Packaging, Version Bumps & Release Cutting (Dermot Callaghan)
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - weekly-2025-02-24 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 574: fix: make process_response mandatory in create_dataset files (Emil Brandvold)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The RAFT block and example work, plus two fixes to parsing and dataset creation that need review
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. RAFT block lands with API shape locked   *** MUST RAISE ***
      2. Parsing and dataset creation fixes merge cleanly   *** MUST RAISE ***
      3. write up Handover: Packaging, Version Bumps & Release Cutting
      4. write up Q2 Plan: Consolidation and Provider Breadth
      5. that the doc "Postmortem: kluster.ai DeepSeek Output-Token Default" is done, and where the others can find it   *** MUST RAISE ***
    goal        RAFT block lands with API shape locked
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective on API shape and design consistency
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. RAFT block lands with API shape locked
      2. Parsing and dataset creation fixes merge cleanly
      3. write up Handover: Packaging, Version Bumps & Release Cutting
      4. write up Q2 Plan: Consolidation and Provider Breadth   *** MUST RAISE ***
      5. that the doc "Q2 Plan: Consolidation and Provider Breadth" is done, and where the others can find it   *** MUST RAISE ***
      6. that "Weekly update: week of Feb 24" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Q2 Plan: Consolidation and Provider Breadth
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Pipeline and dataset knowledge; already approved PR 574
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. RAFT block lands with API shape locked
      2. Parsing and dataset creation fixes merge cleanly
      3. write up Handover: Packaging, Version Bumps & Release Cutting   *** MUST RAISE ***
      4. write up Q2 Plan: Consolidation and Provider Breadth
      5. that the doc "Handover: Packaging, Version Bumps & Release Cutting" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Handover: Packaging, Version Bumps & Release Cutting
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 574 merges today; PR 571 approved pending style pass; PR 573 queued for merge


------------------------------------------------------------------------------
## #cookbooks — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Emil landed three commits to blocks-and-recipes today, including RAFT block and example

    Today is Monday 3 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil landed three commits to blocks-and-recipes today, including RAFT block and example
    
    What it should get through:
      1. RAFT block API locked in and documented   [Emil Brandvold must raise this]
           - Emil shows the block signature and example call site
           - Konrad checks it against SimpleStrat and agentic patterns
           - Settled: API is consistent
    
    On the agenda: RAFT block design and API; Example coverage and runability
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: RAFT block approved for example publication
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 281 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 574: fix: make process_response mandatory in create_dataset files (Emil Brandvold)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. RAFT implementation and example code
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. RAFT block API locked in and documented   *** MUST RAISE ***
    goal        RAFT block API locked in and documented
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Recipe design patterns and user-facing API judgement
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. RAFT block API locked in and documented
    goal        Emil landed three commits to blocks-and-recipes today, including RAFT block and example
    available   around today

### 4. How it should land

    lands as  partial
    leaving   RAFT block approved for example publication


------------------------------------------------------------------------------
## #engineering — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Gideon landed postmortem on Mar 1 incident and is writing it up today; Emil is picking up Gemini issues; both workstreams are mid-flight

    Today is Monday 3 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon landed postmortem on Mar 1 incident and is writing it up today; Emil is picking up Gemini issues; both workstreams are mid-flight
    
    What it should get through:
      1. Gemini rate-limit and parse-failure-count issues tracked   [Emil Brandvold must raise this]
           - Emil describes the Gemini rate-limit handling and None parse-value counting gap
           - Konrad asks if it blocks provider-integrations or cost-estimation
           - Deferred: opened as issues for next iteration
    
    On the agenda: DeepSeek output-token default root cause and fix; Cost projection success-rate weighting; Gemini rate limits and token estimation issues
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gideon unblocked to land cost-estimation fix; Emil captures Gemini issues for backlog
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 281 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 574: fix: make process_response mandatory in create_dataset files (Emil Brandvold)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini rate-limit handling and token-estimation fixes from litellm; the parse_response failure counting issue
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Gemini rate-limit and parse-failure-count issues tracked   *** MUST RAISE ***
    goal        Gemini rate-limit and parse-failure-count issues tracked
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Architectural oversight and o3-mini structured output path
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Gemini rate-limit and parse-failure-count issues tracked
    goal        Gideon landed postmortem on Mar 1 incident and is writing it up today; Emil is picking up Gemini issues; both workstreams are mid-flight
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon unblocked to land cost-estimation fix; Emil captures Gemini issues for backlog


------------------------------------------------------------------------------
## #general — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Dermot and Emil exchanging release-cutting handover by mail; Konrad publishing Q2 plan today

    Today is Monday 3 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dermot and Emil exchanging release-cutting handover by mail; Konrad publishing Q2 plan today
    
    What it should get through:
      1. Emil confirms release-cutting procedures and takes the role   [Dermot Callaghan must raise this]
           - Dermot publishes handover doc
           - Emil confirms understanding and asks about edge cases
           - Settled: handoff complete
      2. Q2 plan communicated: consolidate, prune, sustain   [Konrad Feltrin must raise this]
           - Konrad publishes plan with context on episode drop and contributor churn
           - Team acknowledges the shift in pace
    
    On the agenda: Release-cutting handover from Dermot to Emil; Q2 consolidation and provider-breadth plan kickoff
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Handover acknowledged; Q2 plan in circulation
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 281 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 546: Cost Estimation revamp [1/n] Online processors (Gideon Halloway)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 574: fix: make process_response mandatory in create_dataset files (Emil Brandvold)

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
      - — and 472 function/class names and 14 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release-cutting procedures and context for handoff to Emil
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Emil confirms release-cutting procedures and takes the role   *** MUST RAISE ***
      2. Q2 plan communicated: consolidate, prune, sustain
    goal        Emil confirms release-cutting procedures and takes the role
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Technical readiness and block-ownership perspective
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Emil confirms release-cutting procedures and takes the role
      2. Q2 plan communicated: consolidate, prune, sustain
    goal        Dermot and Emil exchanging release-cutting handover by mail; Konrad publishing Q2 plan today
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Q2 strategy: consolidation, pruning, and sustainable pace
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Emil confirms release-cutting procedures and takes the role
      2. Q2 plan communicated: consolidate, prune, sustain   *** MUST RAISE ***
    goal        Q2 plan communicated: consolidate, prune, sustain
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Handover acknowledged; Q2 plan in circulation


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
# 2025-03-05 — 1 conversation(s), 10 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil has two fresh PRs waiting for review; one already approved, one needs eyes.

    Today is Wednesday 5 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil has two fresh PRs waiting for review; one already approved, one needs eyes.
    
    What it should get through:
      1. Determine if PR 579 complements or duplicates PR 565/#566   [Dario Kestrel must raise this]
           - Emil explains the scope of PR 579 (openai and deepseek in one PR)
           - Dario asks whether it is the same backend work or a different implementation
           - Land on: either merge both and consolidate later, or one takes precedence
      2. Approve PR 578 for merge   [Konrad Feltrin must raise this]
           - Konrad confirms PR 578 already approved and safe to land
           - Emil confirms no conflicts with the hardening work
           - Move to merge
      3. write up Weekly Notes — Week of Mar 3   [Emil Brandvold must raise this]
           - Emil Brandvold says they will write Weekly Notes — Week of Mar 3 — Emil's sync notes for a quiet week of provider-integration work (17 commits).
    
    On the agenda: Status of PR 578 (gemini rate limits) and PR 579 (openai/deepseek); Whether PR 579 overlaps with Dario Kestrel's PR 565/#566 or takes a different path; Any blocking concerns before merge; Weekly Notes — Week of Mar 3
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 578 merges; PR 579 either merges or is clarified as a parallel effort to Dario Kestrel's backend work.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 284 changes merged to date

    On the table
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 578: Ref/update/ratelimits/gemini (Emil Brandvold)

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
    role        Core Platform Engineer, Request Processing. Five commits on gemini batch rate limits, google project env fix, and openai/deepseek API integration
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if PR 579 complements or duplicates PR 565/#566
      2. Approve PR 578 for merge
      3. write up Weekly Notes — Week of Mar 3   *** MUST RAISE ***
      4. that the doc "Weekly Notes — Week of Mar 3" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly Notes — Week of Mar 3
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Review perspective on input handling changes and provider integration patterns
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Determine if PR 579 complements or duplicates PR 565/#566
      2. Approve PR 578 for merge   *** MUST RAISE ***
      3. write up Weekly Notes — Week of Mar 3
    goal        Approve PR 578 for merge
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Knowledge of openai and deepseek backend requirements
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Determine if PR 579 complements or duplicates PR 565/#566   *** MUST RAISE ***
      2. Approve PR 578 for merge
      3. write up Weekly Notes — Week of Mar 3
      4. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine if PR 579 complements or duplicates PR 565/#566
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 578 merges; PR 579 either merges or is clarified as a parallel effort to Dario Kestrel's backend work.

