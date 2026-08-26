# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-05-05 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs merged today; response object is out; seven older PRs need attention

    Today is Monday 5 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs merged today; response object is out; seven older PRs need attention
    
    What it should get through:
      1. Confirm 0.1.24 and response object landed cleanly   [Emil Brandvold must raise this]
           - Emil announces merge complete
           - Konrad asks about API surface changes
           - Group confirms no blockers
      2. Unblock PR 652 or PR 654 for download feature   [Emil Brandvold must raise this]
           - Emil flags critical path items
           - Gideon notes PR 632 impact on observability
           - Group triages which unblock next work
      3. send Weekly update: week of Apr 28   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Apr 28
    
    On the agenda: Response object merged, 0.1.24 status; Stale PR backlog: PR 468, PR 652, PR 654, PR 632, PR 653, PR 640; Weekly update: week of Apr 28
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: 0.1.24 release confirmed shipped; agreement on which stale PRs are on critical path
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 341 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 343 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Landing 0.1.24 and the response object feature
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm 0.1.24 and response object landed cleanly   *** MUST RAISE ***
      2. Unblock PR 652 or PR 654 for download feature   *** MUST RAISE ***
      3. send Weekly update: week of Apr 28
      4. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm 0.1.24 and response object landed cleanly
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Documentation improvements and examples
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm 0.1.24 and response object landed cleanly
      2. Unblock PR 652 or PR 654 for download feature
      3. send Weekly update: week of Apr 28
    goal        Two PRs merged today; response object is out; seven older PRs need attention
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective on API surface and backwards compatibility
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm 0.1.24 and response object landed cleanly
      2. Unblock PR 652 or PR 654 for download feature
      3. send Weekly update: week of Apr 28   *** MUST RAISE ***
      4. that "Weekly update: week of Apr 28" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Apr 28
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI batch update work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm 0.1.24 and response object landed cleanly
      2. Unblock PR 652 or PR 654 for download feature
      3. send Weekly update: week of Apr 28
    goal        Two PRs merged today; response object is out; seven older PRs need attention
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Finetuning client perspective
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm 0.1.24 and response object landed cleanly
      2. Unblock PR 652 or PR 654 for download feature
      3. send Weekly update: week of Apr 28
    goal        Two PRs merged today; response object is out; seven older PRs need attention
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   0.1.24 release confirmed shipped; agreement on which stale PRs are on critical path


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Authentication documentation pass just merged; response object may affect cookbook code samples

    Today is Monday 5 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Authentication documentation pass just merged; response object may affect cookbook code samples
    
    What it should get through:
      1. Confirm auth documentation is clear for new users   [Dermot Callaghan must raise this]
           - Dermot walks through the new section
           - Konrad signals whether it meets 'beginner-ready' bar
           - Group agrees or flags rework
      2. Identify which cookbooks need response-object updates   [Emil Brandvold must raise this]
           - Emil notes the API change scope
           - Dario raises backward-compat concerns
           - Group identifies which examples are most-used
    
    On the agenda: Auth docs clarity for new users; Response object integration into existing examples
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Auth docs verified clear; list of cookbook examples needing response-object updates
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 341 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 343 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Direct changes to authentication documentation
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm auth documentation is clear for new users   *** MUST RAISE ***
      2. Identify which cookbooks need response-object updates
    goal        Confirm auth documentation is clear for new users
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer veto on what constitutes 'clear' for new users
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm auth documentation is clear for new users
      2. Identify which cookbooks need response-object updates
    goal        Authentication documentation pass just merged; response object may affect cookbook code samples
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Perspective on response object changes and example compatibility
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm auth documentation is clear for new users
      2. Identify which cookbooks need response-object updates   *** MUST RAISE ***
    goal        Identify which cookbooks need response-object updates
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Long-term example maintainability concerns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm auth documentation is clear for new users
      2. Identify which cookbooks need response-object updates
    goal        Authentication documentation pass just merged; response object may affect cookbook code samples
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Auth docs verified clear; list of cookbook examples needing response-object updates


==============================================================================
# 2025-05-06 — 3 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Three PRs merged today and v0.1.24 tag exists; release notes are due today and announcement must follow.

    Today is Tuesday 6 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged today and v0.1.24 tag exists; release notes are due today and announcement must follow.
    
    What it should get through:
      1. Release notes capture the three merged changes   [Emil Brandvold must raise this]
           - Emil drafts the three lines from the commit subjects
           - Nikolai and Konrad Feltrin glance at coverage
           - Notes are finalized
      2. Announce v0.1.24 to releases subscribers   [Emil Brandvold must raise this]
           - Emil posts the announcement with the release notes link
           - Team sees it in releases channel
    
    On the agenda: Release v0.1.24 is tagged and ready; What shipped: CLI batch update, DeepSeek API, README auth docs; Announce to the wider team
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Release notes doc is written, announcement mail is sent, team knows v0.1.24 is live.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 344 changes merged to date

    On the table
      - v0.1.24 Release Notes (Emil Brandvold)
      - announce-v0-1-24 (Emil Brandvold)
      - release-v0-1-24 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 661: feat: add example of prescription extraction (Emil Brandvold)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 334 function/class names and 41 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. shipped tag and merged commits across three PRs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Release notes capture the three merged changes   *** MUST RAISE ***
      2. Announce v0.1.24 to releases subscribers   *** MUST RAISE ***
      3. that the doc "v0.1.24 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.24 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture the three merged changes
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. code review signal and validation of the merged work
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Release notes capture the three merged changes
      2. Announce v0.1.24 to releases subscribers
    goal        Three PRs merged today and v0.1.24 tag exists; release notes are due today and announcement must follow.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. foundation perspective on what shipped
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Release notes capture the three merged changes
      2. Announce v0.1.24 to releases subscribers
    goal        Three PRs merged today and v0.1.24 tag exists; release notes are due today and announcement must follow.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. examples-cookbooks changes included in the release
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Release notes capture the three merged changes
      2. Announce v0.1.24 to releases subscribers
    goal        Three PRs merged today and v0.1.24 tag exists; release notes are due today and announcement must follow.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Release notes doc is written, announcement mail is sent, team knows v0.1.24 is live.


------------------------------------------------------------------------------
## #code-review — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today, five older PRs stagnant, era median merge is 25.6h; code-review backlog blocks shipping.

    Today is Tuesday 6 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today, five older PRs stagnant, era median merge is 25.6h; code-review backlog blocks shipping.
    
    What it should get through:
      1. PR 661 prescription extraction example gets review and merges   [Emil Brandvold must raise this]
           - Emil surfaces the example as cookbook-ready
           - Konrad or Dermot Callaghan reviews for docs quality
           - PR 661 merges same day if clean
      2. PR 653 finetuning-client decision: merge or defer   [Nikolai Berresford must raise this]
           - Nikolai flags PR 653 has been open 10 days and owns finetuning work
           - Team decides if it blocks this sprint or lands as-is
           - Decision is recorded
    
    On the agenda: Review open PRs blocking May work; Triage the five stale PRs by age and blocker status; Get PR 661 eyes and decide on PR 653 path
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 661 in flight for merge, PR 653 either merged today or explicitly deferred with a date; it is settled that the team agrees the container user should be an argument the executor passes at create time
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 344 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 661: feat: add example of prescription extraction (Emil Brandvold)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 334 function/class names and 41 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. fast review turnaround and understanding of finetuning-client blocker
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. PR 661 prescription extraction example gets review and merges
      2. PR 653 finetuning-client decision: merge or defer   *** MUST RAISE ***
    goal        PR 653 finetuning-client decision: merge or defer
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. authored PR 661 and owns online-request-processing work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 661 prescription extraction example gets review and merges   *** MUST RAISE ***
      2. PR 653 finetuning-client decision: merge or defer
    goal        PR 661 prescription extraction example gets review and merges
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. just merged PR 632, knows the batch update context
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. PR 661 prescription extraction example gets review and merges
      2. PR 653 finetuning-client decision: merge or defer
    goal        Two PRs opened today, five older PRs stagnant, era median merge is 25.6h; code-review backlog blocks shipping.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. review authority on examples and cookbooks
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 661 prescription extraction example gets review and merges
      2. PR 653 finetuning-client decision: merge or defer
    goal        Two PRs opened today, five older PRs stagnant, era median merge is 25.6h; code-review backlog blocks shipping.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. just landed README cleanup, knows the docs state
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 661 prescription extraction example gets review and merges
      2. PR 653 finetuning-client decision: merge or defer
      3. If we are naming a tag in code anyway, the uid feels like the wrong thing to leave to a Dockerfile. Docker takes a user on the create call and we have simply never passed one.   *** MUST SETTLE (clue t4.r2.L3) ***
    goal        the team agrees the container user should be an argument the executor passes at create time
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 661 in flight for merge, PR 653 either merged today or explicitly deferred with a date; it is settled that the team agrees the container user should be an argument the executor passes at create time


------------------------------------------------------------------------------
## #incidents — 6 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: Incident kind=revert in the packet; two commits reverted (docs lint and structured output). Main is in the tree, so status is unclear.

    Today is Tuesday 6 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Incident kind=revert in the packet; two commits reverted (docs lint and structured output). Main is in the tree, so status is unclear.
    
    What it should get through:
      1. Confirm main is healthy and the revert was necessary and complete   [Nikolai Berresford must raise this]
           - Nikolai states the structured output change broke something (exact impact unclear from commits alone)
           - Gideon or Emil Brandvold confirms main is now green
           - Team agrees no follow-up is needed
      2. Document the revert reasoning so it does not happen again   [Nikolai Berresford must raise this]
           - Nikolai or Dermot Callaghan flags the reason (likely: incompatible with test suite or provider API)
           - Emil notes it for the May sweep postmortem if needed
           - Decision: file an issue or let it sit until the reason resurfaces
    
    On the agenda: State what reverted and the impact; Confirm the revert is complete and main is clean; Document why the structured output change rolled back
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Revert is understood, main is confirmed healthy, and the team knows why structured output had to roll back; it is settled that the team agrees supports_structured_output() is the lookup the structured-output path already goes through
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 344 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 661: feat: add example of prescription extraction (Emil Brandvold)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 334 function/class names and 41 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: response_format, supports_structured_output.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. made the original structured output change and the revert commit
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm main is healthy and the revert was necessary and complete   *** MUST RAISE ***
      2. Document the revert reasoning so it does not happen again   *** MUST RAISE ***
    goal        Confirm main is healthy and the revert was necessary and complete
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. merged PR 632 and understands the batch update context
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm main is healthy and the revert was necessary and complete
      2. Document the revert reasoning so it does not happen again
    goal        Incident kind=revert in the packet; two commits reverted (docs lint and structured output). Main is in the tree, so status is unclear.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns online-request-processing and will confirm the revert did not break the sweep
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm main is healthy and the revert was necessary and complete
      2. Document the revert reasoning so it does not happen again
      3. For anyone reading the online processor: before it puts response_format on the payload it calls supports_structured_output(model), which is just a membership check. If the check says no you get plain text back and a warning, nothing louder.   *** MUST SETTLE (clue t2.r2.l2) ***
         must contain literally: supports_structured_output, response_format
    goal        the team agrees supports_structured_output() is the lookup the structured-output path already goes through
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. recent context on the commit graph
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm main is healthy and the revert was necessary and complete
      2. Document the revert reasoning so it does not happen again
    goal        Incident kind=revert in the packet; two commits reverted (docs lint and structured output). Main is in the tree, so status is unclear.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Revert is understood, main is confirmed healthy, and the team knows why structured output had to roll back; it is settled that the team agrees supports_structured_output() is the lookup the structured-output path already goes through


==============================================================================
# 2025-05-07 — 2 conversation(s), 22 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil merged the prescription extraction example today; it touches multimodal-prompts which several people own.

    Today is Wednesday 7 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil merged the prescription extraction example today; it touches multimodal-prompts which several people own.
    
    What it should get through:
      1. Confirm prescription example is ready and fits the examples corpus   [Emil Brandvold must raise this]
           - Emil states the merge is clean and tested
           - Nikolai notes the code-execution angle is sound
           - Dermot flags or clears any corpus integration risk
      2. Unblock or defer the three stalled multimodal/cookbook PRs   [Dermot Callaghan must raise this]
           - Emil lists the three open PRs (PR 652, PR 654, PR 658) and their blockers
           - Discussion lands on which can move this week or which defer
    
    On the agenda: Prescription extraction example merged and in v0.1.24; Torch dependency fix (PR PR 663) status; Multimodal path forward and blocked PRs
    
    Meeting today: Weekly sync
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Prescription example is live in v0.1.24 and integrated into the example suite. At least one blocked PR moves forward or a decision lands on deferrals.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 345 changes merged to date

    On the table
      - v0.1.24 Release Notes (Emil Brandvold)
      - Weekly Notes — Week of May 5 (Dermot Callaghan)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Vision/multimodal workstream ready to land; example code for prescription extraction
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm prescription example is ready and fits the examples corpus   *** MUST RAISE ***
      2. Unblock or defer the three stalled multimodal/cookbook PRs
      3. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm prescription example is ready and fits the examples corpus
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Review perspective on code-execution angle and torch dependency fix
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm prescription example is ready and fits the examples corpus
      2. Unblock or defer the three stalled multimodal/cookbook PRs
    goal        Emil merged the prescription extraction example today; it touches multimodal-prompts which several people own.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Ownership of the examples-cookbooks surface; weekly notes due today
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm prescription example is ready and fits the examples corpus
      2. Unblock or defer the three stalled multimodal/cookbook PRs   *** MUST RAISE ***
      3. the page you are writing, Postmortem: Examples/Cookbooks Lint & Structured-Output Revert, has to say this in your own words: review comment I keep leaving: if your branch depends on what a model can do, look it up in the support table and add the pattern there if it is missing. do not grow a fourth capability dict next to the one you are writing. the table is cheap to extend and everything reading it improves at once   *** MUST SETTLE (clue t2.r1.L4) ***
      4. that the doc "Weekly Notes — Week of May 5" is done, and where the others can find it   *** MUST RAISE ***
      5. that the doc "Postmortem: Examples/Cookbooks Lint & Structured-Output Revert" is done, and where the others can find it   *** MUST RAISE ***
    goal        Unblock or defer the three stalled multimodal/cookbook PRs
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Prescription example is live in v0.1.24 and integrated into the example suite. At least one blocked PR moves forward or a decision lands on deferrals.


------------------------------------------------------------------------------
## #code-review — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Nikolai Berresford opened the first draft of the pinning change and asked for eyes before he wires up the override

    Today is Wednesday 7 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai Berresford opened the first draft of the pinning change and asked for eyes before he wires up the override
    
    What it should get through:
    
    On the agenda: Gideon Halloway reports that while testing the branch he passed the image as a plain repository name with no tag after the colon and the run went ahead against whatever the registry served, which cost him most of a morning before he compared two runs side by side, and he says it should stop before the container starts and tell him what he got wrong; Dermot Callaghan bikesheds the key name in backend_params, docker_image versus image versus sandbox_image, and says whichever it is has to read unambiguously next to the other docker keys; Konrad Feltrin asks whether the same key means anything for the local backend and gets no answer
    
    Wrap when: Nikolai Berresford will rename the key and add a check on the value; the local-backend question is left in a review comment unresolved; it is settled that the team agrees the repo gives no indication of which sandbox build is acceptable
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 345 changes merged to date

    On the table
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: curator-sandbox.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Lost most of yesterday to this. I picked a curator-sandbox tag off the registry listing because it looked like the newest one, ran the verifier suite against it, got twelve failures that had nothing to do with my code. Grepped the whole repo afterwards for any hint of which build we consider good and there is nothing in there, the numbers are not written down anywhere in the codebase.   *** MUST SETTLE (clue t4.r1.L2) ***
         must contain literally: curator-sandbox
    goal        the team agrees the repo gives no indication of which sandbox build is acceptable
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Nikolai Berresford opened the first draft of the pinning change and asked for eyes before he wires up the override
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nikolai Berresford will rename the key and add a check on the value; the local-backend question is left in a review comment unresolved; it is settled that the team agrees the repo gives no indication of which sandbox build is acceptable


==============================================================================
# 2025-05-08 — 1 conversation(s), 12 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs older than the era median; two people with code waiting; risk of stalled work in consolidation phase

    Today is Thursday 8 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs older than the era median; two people with code waiting; risk of stalled work in consolidation phase
    
    What it should get through:
      1. Unblock agentic multiturn and viewer downloads   [Emil Brandvold must raise this]
           - Emil raises blockers on 658; Nikolai reviews the design
           - Discussion clarifies whether multiturn is ready to merge or needs iteration
      2. Assess gemini batch serialization and GCS upload issues   [Emil Brandvold must raise this]
           - Emil flags new issues 664 and 665 as context for 654 review
           - Discussion connects download batch laziness to rate limiting problem
      3. Land torch dependency and finetuning client PRs   [Nikolai Berresford must raise this]
           - Nikolai seeks merge approval for 663 (quick fix)
           - Emil or Nikolai clarifies finetuning client scope and blockers on 653
    
    On the agenda: Review status of 658 (agentic multiturn, 7 days old); Address 652 and 654 (viewer download, 13 and 11 days old); Tackle torch dependency fix 663 and finetuning client 653
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Two to three PRs merge; remainder get clear feedback on what blocks them (design questions, test coverage, or gemini provider fixes)
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 345 changes merged to date

    On the table
      - Postmortem: Examples/Cookbooks Lint & Structured-Output Revert (Dermot Callaghan)
      - Weekly Notes — Week of May 5 (Dermot Callaghan)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on viewer download feature, agentic multiturn, and gemini batch processing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock agentic multiturn and viewer downloads   *** MUST RAISE ***
      2. Assess gemini batch serialization and GCS upload issues   *** MUST RAISE ***
      3. Land torch dependency and finetuning client PRs
      4. what "Postmortem: Examples/Cookbooks Lint & Structured-Output Revert" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly Notes — Week of May 5" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock agentic multiturn and viewer downloads
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. finetuning client implementation and torch dependency fix
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Unblock agentic multiturn and viewer downloads
      2. Assess gemini batch serialization and GCS upload issues
      3. Land torch dependency and finetuning client PRs   *** MUST RAISE ***
    goal        Land torch dependency and finetuning client PRs
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Two to three PRs merge; remainder get clear feedback on what blocks them (design questions, test coverage, or gemini provider fixes)


==============================================================================
# 2025-05-09 — 1 conversation(s), 10 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Five PRs are older than the era's median merge time; two of them block Emil Brandvold's downstream work and Nikolai Berresford's are waiting on review feedback

    Today is Friday 9 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five PRs are older than the era's median merge time; two of them block Emil Brandvold's downstream work and Nikolai Berresford's are waiting on review feedback
    
    What it should get through:
      1. Establish which of Emil Brandvold's three PRs can merge this week   [Emil Brandvold must raise this]
           - Emil Brandvold states blockers for 652 (viewer download), 654 (gemini lazy batch), and 658 (agentic multiturn)
           - Nikolai Berresford notes what review comments he's seen or what's missing
           - both agree on what each PR needs to land
      2. Clarify review expectations for Nikolai Berresford's two PRs so they unblock   [Nikolai Berresford must raise this]
           - Nikolai Berresford flags what feedback he's waiting for on 653 and 663
           - Emil Brandvold or Dermot Callaghan indicates what they need to see before signing off
           - plan emerges for next steps
    
    On the agenda: Review status of five stale PRs and decide on merge path; Identify which PRs are blockers for other work; Surface any design concerns or test gaps before merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Agreement on which PRs merge this week and what each one needs; unblock at least one of Emil Brandvold's three stale PRs; it is settled that the team agrees write protection on the mount is what makes verifier results trustworthy and it was absent on a custom image
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 23 release(s) shipped, currently v0.1.24
      - 345 changes merged to date

    On the table
      - v0.1.24 Release Notes (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 654: perf: make download batch lazy in gemini processor (Emil Brandvold)
      - PR 658: Feat/agentic/multiturn (Emil Brandvold)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 666: fix: migrate to `logger.warning` (Rafael Duquette)

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

    DOES NOT EXIST YET (2 names)
      - agentic-curation
      - — and 329 function/class names and 37 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. ownership of three blocked PRs (652, 654, 658); context on viewer download, gemini perf, and agentic multiturn work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Establish which of Emil Brandvold's three PRs can merge this week   *** MUST RAISE ***
      2. Clarify review expectations for Nikolai Berresford's two PRs so they unblock
      3. what "v0.1.24 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Establish which of Emil Brandvold's three PRs can merge this week
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. knowledge of torch dependency fix (663) and finetuning client changes (653); fresh perspective on what's been sitting
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Establish which of Emil Brandvold's three PRs can merge this week
      2. Clarify review expectations for Nikolai Berresford's two PRs so they unblock   *** MUST RAISE ***
      3. Half the reason the workspace bind is set up the way it is: a model solution physically cannot edit the test file, so grading means something. Ran last week's batch on a custom image someone handed me and three solutions passed by overwriting the assertions. I only caught it because the pass rate jumped.   *** MUST SETTLE (clue t4.r2.L5) ***
    goal        Clarify review expectations for Nikolai Berresford's two PRs so they unblock
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Agreement on which PRs merge this week and what each one needs; unblock at least one of Emil Brandvold's three stale PRs; it is settled that the team agrees write protection on the mount is what makes verifier results trustworthy and it was absent on a custom image

