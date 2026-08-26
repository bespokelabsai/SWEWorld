# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-06-16 — 2 conversation(s), 22 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs older than the era's median merge time; only two people present to discuss them

    Today is Monday 16 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs older than the era's median merge time; only two people present to discuss them
    
    What it should get through:
      1. Decide if 690 and 691 are review-ready or need more work   [Emil Brandvold must raise this]
           - Emil flags both PRs as 3 days old and stalled
           - Nikolai asks what the blockers are
           - Emil either requests changes or brings them to discussion
      2. Determine 653's fate: actively worked or abandoned   [Nikolai Berresford must raise this]
           - Nikolai explains he just merged main into it today
           - Emil asks if it's ready for review or still drafting
           - Nikolai outlines next steps or defers
    
    On the agenda: Status of PRs 690 and 691: what's holding them; PR 653: why it's been open 51 days and whether it's still active; Plan to clear the queue
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear understanding of which PRs are review-ready this week, which need rework, and which are waiting on external factors. No guarantee all four land, but the blockage should be visible.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 366 changes merged to date

    On the table
      - weekly-2025-06-09 (Nikolai Berresford)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 691: feat: auto batch mode (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 267 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release-and-ci; knows what's blocking the pipeline
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Decide if 690 and 691 are review-ready or need more work   *** MUST RAISE ***
      2. Determine 653's fate: actively worked or abandoned
    goal        Decide if 690 and 691 are review-ready or need more work
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. merging main into finetuning-client; knows the state of 653
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Decide if 690 and 691 are review-ready or need more work
      2. Determine 653's fate: actively worked or abandoned   *** MUST RAISE ***
      3. that "Week of Jun 9 recap: bulk inference fix" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Determine 653's fate: actively worked or abandoned
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear understanding of which PRs are review-ready this week, which need rework, and which are waiting on external factors. No guarantee all four land, but the blockage should be visible.


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Monday morning; two present engineers with stalled work and a merge in progress; rest of team absent

    Today is Monday 16 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Monday morning; two present engineers with stalled work and a merge in progress; rest of team absent
    
    What it should get through:
      1. Surface what's in flight and what's stuck   [Nikolai Berresford must raise this]
           - Nikolai mentions the finetuning-client merge
           - Emil lists the three PRs he's blocked on
           - Either of them notes whether anything else needs attention
    
    On the agenda: State of the week: what landed and what's in flight; Blockers on 690, 691, 653; Anything breaking or stuck
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Brief inventory of in-flight work. No decisions needed, just visibility into why progress is slow.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 366 changes merged to date

    On the table
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 691: feat: auto batch mode (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 267 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. state of finetuning-client PR and what merging main revealed
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Surface what's in flight and what's stuck   *** MUST RAISE ***
      2. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Surface what's in flight and what's stuck
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. visibility into stalled PRs and what the team needs unblocked
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Surface what's in flight and what's stuck
    goal        Monday morning; two present engineers with stalled work and a merge in progress; rest of team absent
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Brief inventory of in-flight work. No decisions needed, just visibility into why progress is slow.


==============================================================================
# 2025-06-18 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two reviews landed today on stale PRs; four PRs waiting, two critical to the team

    Today is Wednesday 18 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two reviews landed today on stale PRs; four PRs waiting, two critical to the team
    
    What it should get through:
      1. Clarify whether PR 691 blocks release or can land   [Emil Brandvold must raise this]
           - Emil raises the blocker status and how batch mode affects the release timeline
           - Nikolai pushes back on test coverage or integration risk
           - They settle on a path: land now, test in dormancy mode, or defer
      2. Unblock PR 690 with Gemini multimodal fix   [Emil Brandvold must raise this]
           - Emil describes the Gemini-specific batch request shape issue
           - Nikolai either approves or names the remaining change needed
           - If stuck, they note what else must land before this can merge
      3. write up Weekly sync notes: week of Jun 16   [Nikolai Berresford must raise this]
           - Nikolai Berresford says they will write Weekly sync notes: week of Jun 16 — Logs the one commit landed that week and confirms the queue is quiet
    
    On the agenda: Review PR 691 (auto batch mode) for merge readiness; Review PR 690 (Gemini batch fix) and clarify multimodal path; Triage older PRs 675 and 653: blockers or deferrable; Weekly sync notes: week of Jun 16
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PRs 690 and 691 either merge, move to specific blocking work, or get a clear deferral reason. PR 653 and 675 get a triage note.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 366 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 16 (Nikolai Berresford)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 691: feat: auto batch mode (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 267 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. understanding of release-and-ci and online-request-processing; recent work on multimodal fixes and batch mode
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify whether PR 691 blocks release or can land   *** MUST RAISE ***
      2. Unblock PR 690 with Gemini multimodal fix   *** MUST RAISE ***
      3. write up Weekly sync notes: week of Jun 16
    goal        Clarify whether PR 691 blocks release or can land
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. perspective on code-execution and release flow; experience reviewing batch and multimodal changes
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Clarify whether PR 691 blocks release or can land
      2. Unblock PR 690 with Gemini multimodal fix
      3. write up Weekly sync notes: week of Jun 16   *** MUST RAISE ***
      4. that the doc "Weekly sync notes: week of Jun 16" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly sync notes: week of Jun 16
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PRs 690 and 691 either merge, move to specific blocking work, or get a clear deferral reason. PR 653 and 675 get a triage note.


==============================================================================
# 2025-06-25 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR PR 691 merged today; three older PRs (PR 690, PR 675, PR 653) remain open and need triage

    Today is Wednesday 25 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 691 merged today; three older PRs (PR 690, PR 675, PR 653) remain open and need triage
    
    What it should get through:
      1. Confirm auto batch mode is ready to ship   [Emil Brandvold must raise this]
           - Emil presents the merged PR 691 and its readiness
           - Nikolai confirms review and suggests it rides with next release
           - Both agree no blockers exist for the feature itself
      2. Understand and unblock PR 690 (Gemini batch multimodal)   [Emil Brandvold must raise this]
           - Emil notes PR 690 has been open 12 days and blocks multimodal users
           - Nikolai probes why it has not landed
           - Emil explains the gap and next steps
      3. Triage PR 675 and PR 653 for release readiness   [Nikolai Berresford must raise this]
           - Nikolai raises both as blocking visibility
           - Emil confirms neither blocks v0.1.26
           - Both agree on deferral or unblock strategy
    
    On the agenda: Auto batch mode feature merged and status; Three stalled pull requests blocking the pipeline; Next release planning and dependency chain
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Auto batch mode confirmed ready to ship; stalled PRs triaged and either unblocked or deferred with clear reasoning; weekly notes complete.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 367 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 23 (batch mode) (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. ownership of the auto batch mode feature and its provider integration
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm auto batch mode is ready to ship   *** MUST RAISE ***
      2. Understand and unblock PR 690 (Gemini batch multimodal)   *** MUST RAISE ***
      3. Triage PR 675 and PR 653 for release readiness
      4. that the doc "Weekly sync notes: week of Jun 23 (batch mode)" is done, and where the others can find it   *** MUST RAISE ***
    goal        Confirm auto batch mode is ready to ship
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. code review perspective and approval signal
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm auto batch mode is ready to ship
      2. Understand and unblock PR 690 (Gemini batch multimodal)
      3. Triage PR 675 and PR 653 for release readiness   *** MUST RAISE ***
    goal        Triage PR 675 and PR 653 for release readiness
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Auto batch mode confirmed ready to ship; stalled PRs triaged and either unblocked or deferred with clear reasoning; weekly notes complete.


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Feature PR PR 691 merged; team needs visibility on completion and next steps in dormancy phase

    Today is Wednesday 25 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Feature PR PR 691 merged; team needs visibility on completion and next steps in dormancy phase
    
    What it should get through:
      1. Announce auto batch mode landing and capability   [Emil Brandvold must raise this]
           - Emil walks through what auto batch mode does and who benefits
           - Nikolai asks about performance and cost impact
           - Emil explains the 50% cost savings on batch-eligible jobs
      2. Set release cadence expectations during dormancy   [Emil Brandvold must raise this]
           - Emil signals that auto batch mode will ride v0.1.26 without a new release cut yet
           - Nikolai asks about schedule and blockers
           - Emil confirms the timeline and what needs to land before cut
      3. Surface stalled work that is not blocking   [Nikolai Berresford must raise this]
           - Nikolai notes three PRs open beyond median merge time
           - Emil categorizes them by impact
           - Both agree on visibility for the team
    
    On the agenda: Auto batch mode feature merged and live; Release readiness and timing for v0.1.26; Stalled PR landscape and unblocking strategy
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands auto batch mode is complete; release timing is clear; stalled PR status is transparent; weekly sync notes capture the state.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 367 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 23 (batch mode) (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. feature completion and provider integration details
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Announce auto batch mode landing and capability   *** MUST RAISE ***
      2. Set release cadence expectations during dormancy   *** MUST RAISE ***
      3. Surface stalled work that is not blocking
      4. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Announce auto batch mode landing and capability
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. code quality signal and deployment perspective
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Announce auto batch mode landing and capability
      2. Set release cadence expectations during dormancy
      3. Surface stalled work that is not blocking   *** MUST RAISE ***
    goal        Surface stalled work that is not blocking
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands auto batch mode is complete; release timing is clear; stalled PR status is transparent; weekly sync notes capture the state.


==============================================================================
# 2025-06-26 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil opened PR 693 today for streaming support and needs initial review

    Today is Thursday 26 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil opened PR 693 today for streaming support and needs initial review
    
    What it should get through:
      1. Establish whether streaming is a separate code path or integrated with auto batch mode   [Emil Brandvold must raise this]
           - Emil explains the design choice
           - Dermot asks whether batching and streaming can coexist
           - They agree on the architectural layer
    
    On the agenda: Shape of streaming support in online requests; How this interacts with auto batch mode (PR 691); Whether this blocks or depends on anything else
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear sense of whether the approach is sound; may defer implementation details to follow-up commits
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 367 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 23 (batch mode) (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. implementation of streaming support for OpenAI online requests, understanding of batch vs online tradeoffs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Establish whether streaming is a separate code path or integrated with auto batch mode   *** MUST RAISE ***
      2. what "Weekly sync notes: week of Jun 23 (batch mode)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Establish whether streaming is a separate code path or integrated with auto batch mode
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. deep knowledge of request processing and online request layer design
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Establish whether streaming is a separate code path or integrated with auto batch mode
    goal        Emil opened PR 693 today for streaming support and needs initial review
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear sense of whether the approach is sound; may defer implementation details to follow-up commits


------------------------------------------------------------------------------
## #pipeline — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil's auto batch mode commit affects multiple request-layer services; streaming PR extends online requests

    Today is Thursday 26 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil's auto batch mode commit affects multiple request-layer services; streaming PR extends online requests
    
    What it should get through:
      1. Clarify whether streaming changes request routing or cache invalidation   [Emil Brandvold must raise this]
           - Emil recaps auto batch logic from PR 691
           - Dermot notes resume and caching implications
           - Agreement on which parts need updating
    
    On the agenda: What auto batch mode changed about request routing; Where streaming sits in relation to batch and online modes; Any cache invalidation or resume concerns with streaming
    
    Out today: Dario Kestrel (no commit, review or comment 2025-05-27..2025-10-20) — their input is missing and people may say so
    
    No longer here: Gideon Halloway, Nils Brandt — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Shared understanding of request routing after auto batch mode; streaming work scoped relative to it
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 367 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 23 (batch mode) (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. just landed auto batch mode; knows the decision tree for when to use batch vs online
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify whether streaming changes request routing or cache invalidation   *** MUST RAISE ***
      2. what "Weekly sync notes: week of Jun 23 (batch mode)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify whether streaming changes request routing or cache invalidation
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. understanding of how the request layer decides between batch and online paths
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Clarify whether streaming changes request routing or cache invalidation
    goal        Emil's auto batch mode commit affects multiple request-layer services; streaming PR extends online requests
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Shared understanding of request routing after auto batch mode; streaming work scoped relative to it


==============================================================================
# 2025-07-10 — 3 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: One PR merged today, four stale ones waiting; quick thumbs-up and backlog check.

    Today is Thursday 10 July 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One PR merged today, four stale ones waiting; quick thumbs-up and backlog check.
    
    What it should get through:
      1. Confirm PR 696 merge is correct   [Emil Brandvold must raise this]
           - Emil Brandvold notes the change is doc-only
           - Konrad Feltrin acknowledges the approval
      2. Establish what to do with 653, 675, 690, 693   [Konrad Feltrin must raise this]
           - Konrad Feltrin lists which ones are actually blocking
           - Emil Brandvold marks what he can pick up next
    
    On the agenda: Check PR PR 696 is ready to ship; Review the stale PR backlog and triage it
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 696 merged with confidence; agreement on next stale PR to tackle.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 368 changes merged to date

    On the table
      - v0.1.25 Release Notes (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the change itself and context on why the version tag reference belongs in lib
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 696 merge is correct   *** MUST RAISE ***
      2. Establish what to do with 653, 675, 690, 693
      3. what "v0.1.25 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 696 merge is correct
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. a second set of eyes and maintainer judgment on the reference implementation
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 696 merge is correct
      2. Establish what to do with 653, 675, 690, 693   *** MUST RAISE ***
      3. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Establish what to do with 653, 675, 690, 693
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 696 merged with confidence; agreement on next stale PR to tackle.


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Quick doc-only kickoff to add version tag reference; two services touched, merged same day.

    Today is Thursday 10 July 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Quick doc-only kickoff to add version tag reference; two services touched, merged same day.
    
    What it should get through:
      1. Confirm version tag reference is correct and maintainable   [Emil Brandvold must raise this]
           - Emil Brandvold explains what the tag reference does and why now
           - Konrad Feltrin asks about sync burden
           - they agree it is a one-time fix
    
    On the agenda: Review the version tag reference change; Assess impact on the five affected services
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Both agree the change is correct; no hidden maintenance burden discovered.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 368 changes merged to date

    On the table
      - Weekly sync notes: week of Jul 7 (bulk LLM inference) (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the implementation and knowledge of where the tag reference fits
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm version tag reference is correct and maintainable   *** MUST RAISE ***
      2. what "Weekly sync notes: week of Jul 7 (bulk LLM inference)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      3. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm version tag reference is correct and maintainable
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. historical context and maintainer perspective on what stays in sync
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm version tag reference is correct and maintainable
    goal        Quick doc-only kickoff to add version tag reference; two services touched, merged same day.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both agree the change is correct; no hidden maintenance burden discovered.


------------------------------------------------------------------------------
## #viewer — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Version tag reference touches curator-viewer surface; quick visual check before landing.

    Today is Thursday 10 July 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Version tag reference touches curator-viewer surface; quick visual check before landing.
    
    What it should get through:
      1. Confirm viewer display of version tag is clean   [Emil Brandvold must raise this]
           - Emil Brandvold shows the tag in the UI
           - Konrad Feltrin checks for alignment and clarity
    
    On the agenda: Check how version tag appears in viewer surface; Verify no display regressions
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Version tag displays cleanly in viewer; no UX issues found.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 368 changes merged to date

    On the table
      - Weekly sync notes: week of Jul 7 (bulk LLM inference) (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)

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

    DOES NOT EXIST YET (1 names)
      - — and 264 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the specific change to curator-viewer and where the version tag appears in the UI
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm viewer display of version tag is clean   *** MUST RAISE ***
      2. what "Weekly sync notes: week of Jul 7 (bulk LLM inference)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm viewer display of version tag is clean
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. end-user perspective and concern for viewer UX
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm viewer display of version tag is clean
    goal        Version tag reference touches curator-viewer surface; quick visual check before landing.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Version tag displays cleanly in viewer; no UX issues found.

