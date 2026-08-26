# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-04-25 — 4 conversation(s), 46 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 652 opened today with early review; needs to either land or surface blockers before end of week

    Today is Friday 25 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 652 opened today with early review; needs to either land or surface blockers before end of week
    
    What it should get through:
      1. Land or identify blockers for PR 652   [Emil Brandvold must raise this]
           - Dermot raises any concerns from his COMMENTED review
           - Emil addresses feedback or explains design
           - Nikolai flags any integration points with upload changes
    
    On the agenda: Review PR 652 viewer download feature; Address any feedback from Dermot's comments; Check consistency with Nikolai Berresford's recent upload changes; Unblock merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR either approved for merge or concrete blocker identified for Monday
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The viewer download feature implementation and context
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land or identify blockers for PR 652   *** MUST RAISE ***
    goal        Land or identify blockers for PR 652
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Fresh review and potential concerns about the implementation
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land or identify blockers for PR 652
    goal        PR 652 opened today with early review; needs to either land or surface blockers before end of week
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Perspective on the broader upload/download architecture Nikolai Berresford just touched
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Land or identify blockers for PR 652
    goal        PR 652 opened today with early review; needs to either land or surface blockers before end of week
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observer perspective on merge queue state
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land or identify blockers for PR 652
    goal        PR 652 opened today with early review; needs to either land or surface blockers before end of week
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR either approved for merge or concrete blocker identified for Monday


------------------------------------------------------------------------------
## #viewer — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: PR 652 adds dataset download to viewer; needs coordination on surface and architecture

    Today is Friday 25 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 652 adds dataset download to viewer; needs coordination on surface and architecture
    
    What it should get through:
      1. Ensure download feature integrates cleanly with viewer surface and caching   [Emil Brandvold must raise this]
           - Emil explains what the download path looks like and where it hooks in
           - Dario checks against existing viewer affordances and user workflows
           - Dermot flags any caching or persistence layer concerns
    
    On the agenda: Understand download feature scope and placement; Verify consistency with push/dataset lifecycle; Check performance implications
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clear alignment on how download integrates, or deferred to next iteration
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Implementation details of the new download feature
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Ensure download feature integrates cleanly with viewer surface and caching   *** MUST RAISE ***
    goal        Ensure download feature integrates cleanly with viewer surface and caching
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Broader viewer architecture and user-facing API consistency
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Ensure download feature integrates cleanly with viewer surface and caching
    goal        PR 652 adds dataset download to viewer; needs coordination on surface and architecture
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Understanding of how datasets flow through caching and persistence
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Ensure download feature integrates cleanly with viewer surface and caching
    goal        PR 652 adds dataset download to viewer; needs coordination on surface and architecture
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear alignment on how download integrates, or deferred to next iteration


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Nikolai's 3 commits today touch finetuning core; cookbooks repo depends on stable interface

    Today is Friday 25 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai's 3 commits today touch finetuning core; cookbooks repo depends on stable interface
    
    What it should get through:
      1. Surface finetuning changes and catch any cookbook-breaking impacts   [Nikolai Berresford must raise this]
           - Nikolai explains the upload and job ID changes and why
           - Dermot assesses impact on existing cookbook examples
           - Emil flags any release or integration concerns
    
    On the agenda: Nikolai's finetuning changes: upload function and job ID semantics; Impact on published cookbooks and user examples; Any breaking changes or migration needed
    
    Out today: Konrad Feltrin (no commit, review or comment 2025-04-14..2025-05-01) — their input is missing and people may say so
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Either cookbooks are unaffected, or a list of examples that need revision
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Concrete changes to upload function and job ID return semantics
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Surface finetuning changes and catch any cookbook-breaking impacts   *** MUST RAISE ***
      2. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Surface finetuning changes and catch any cookbook-breaking impacts
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Cookbook and recipe perspective; how finetuning is exposed to users
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Surface finetuning changes and catch any cookbook-breaking impacts
    goal        Nikolai's 3 commits today touch finetuning core; cookbooks repo depends on stable interface
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release and integration context
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Surface finetuning changes and catch any cookbook-breaking impacts
    goal        Nikolai's 3 commits today touch finetuning core; cookbooks repo depends on stable interface
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Either cookbooks are unaffected, or a list of examples that need revision


------------------------------------------------------------------------------
## #random — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #random: Gideon Halloway saw a note that another project force-pushed a docker tag and it reminded everyone of last week

    Today is Friday 25 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon Halloway saw a note that another project force-pushed a docker tag and it reminded everyone of last week
    
    What it should get through:
    
    On the agenda: Gideon Halloway grumbles that a tag pointing at a different layer set than yesterday means the string in your logs is not evidence of anything unless you write it down at the time; Konrad Feltrin says he has started pasting the output of docker images into his run notes by hand, which he does not want to keep doing; Nikolai Berresford jokes about pinning by digest and then admits he does not know whether the sandbox images are published with stable digests
    
    Wrap when: a digest-versus-tag question raised in a joking register and left for later; Konrad Feltrin's manual workaround stands; it is settled that the team agrees users see contradictory model-support answers because more than one list of names exists
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: o3.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Two support tickets in a row about o3 getting a schema in one place and not another before I twigged that there was more than one list of model names in the tree. I'd rather explain a hard error than explain that.   *** MUST SETTLE (clue t2.r2.l6) ***
         must contain literally: o3
    goal        the team agrees users see contradictory model-support answers because more than one list of names exists
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Gideon Halloway saw a note that another project force-pushed a docker tag and it reminded everyone of last week
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   a digest-versus-tag question raised in a joking register and left for later; Konrad Feltrin's manual workaround stands; it is settled that the team agrees users see contradictory model-support answers because more than one list of names exists


==============================================================================
# 2025-04-28 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nikolai committed serving infrastructure work touching multiple core services; the team needs to align on scope and impact.

    Today is Monday 28 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai committed serving infrastructure work touching multiple core services; the team needs to align on scope and impact.
    
    What it should get through:
      1. Understand serving infra scope   [Nikolai Berresford must raise this]
           - Nikolai describes the changes
           - Dario and Emil ask about request processing impact
           - Dermot flags any release-blocking concerns
      2. send Weekly update: week of Apr 21   [Emil Brandvold must raise this]
           - Emil Brandvold says they will send Weekly update: week of Apr 21
    
    On the agenda: Scope of serving infra changes; Impact on request layer and caching; Blocking status for ongoing work; Weekly update: week of Apr 21
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what's changing in the serving layer and whether it blocks or is blocked by any open work.
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Serving infrastructure changes across request processing and caching
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Understand serving infra scope   *** MUST RAISE ***
      2. send Weekly update: week of Apr 21
    goal        Understand serving infra scope
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing ownership and context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Understand serving infra scope
      2. send Weekly update: week of Apr 21
    goal        Nikolai committed serving infrastructure work touching multiple core services; the team needs to align on scope and impact.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Provider integration and online-request-processing perspective
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand serving infra scope
      2. send Weekly update: week of Apr 21   *** MUST RAISE ***
      3. that "Weekly update: week of Apr 21" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Apr 21
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Core pipeline and release context
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Understand serving infra scope
      2. send Weekly update: week of Apr 21
    goal        Nikolai committed serving infrastructure work touching multiple core services; the team needs to align on scope and impact.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what's changing in the serving layer and whether it blocks or is blocked by any open work.


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 6 PRs older than the era median (25.6h); Emil has 5 open, Gideon has 1, Nikolai's finetuning client is 2 days old.

    Today is Monday 28 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 6 PRs older than the era median (25.6h); Emil has 5 open, Gideon has 1, Nikolai's finetuning client is 2 days old.
    
    What it should get through:
      1. Clear stale PR queue   [Emil Brandvold must raise this]
           - Emil catalogs status of 468, 643, 651, 652, 654, 656
           - Gideon and Nikolai flag any they can review this week
           - Team decides what merges vs. holds
    
    On the agenda: Which PRs are ready to land; Which need more work or are blocked; Dependencies between open PRs
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Stale PRs either move to review, get unblocked, or are explicitly deferred with a reason.
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Multiple pending features (n-samples, response object, multimodal, download, lazy gemini)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clear stale PR queue   *** MUST RAISE ***
    goal        Clear stale PR queue
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI batch-update frequency fix perspective
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clear stale PR queue
    goal        6 PRs older than the era median (25.6h); Emil has 5 open, Gideon has 1, Nikolai's finetuning client is 2 days old.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Release and CI perspective; finetuning client PR context
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Clear stale PR queue
    goal        6 PRs older than the era median (25.6h); Emil has 5 open, Gideon has 1, Nikolai's finetuning client is 2 days old.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Stale PRs either move to review, get unblocked, or are explicitly deferred with a reason.


------------------------------------------------------------------------------
## #viewer — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Konrad Feltrin pushed two verification runs to the viewer to compare and could not tell them apart from the metadata panel

    Today is Monday 28 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad Feltrin pushed two verification runs to the viewer to compare and could not tell them apart from the metadata panel
    
    What it should get through:
    
    On the agenda: Konrad Feltrin says the two runs differ only in what executed the code and the viewer shows the same recipe, same model, same row count, so the comparison is useless to him; Gideon Halloway says the run metadata carries provider and model already and he would like whatever identified the execution environment to sit in the same block, sourced from whatever the executor resolved rather than from what the user typed; Dario Kestrel asks whether that value comes from the same place the cache key would read it from and says it had better, or the two will drift
    
    Wrap when: Gideon Halloway will sketch the metadata field once the executor exposes a resolved value; nothing merged; it is settled that the team agrees the reported object should expose the directory it inspected as a field
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Konrad Feltrin pushed two verification runs to the viewer to compare and could not tell them apart from the metadata panel
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Konrad Feltrin pushed two verification runs to the viewer to compare and could not tell them apart from the metadata panel
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. cheap fix for the support loop: whatever object these reporting calls hand back should carry the directory it looked at as a field, the way the end-of-run summary already prints the db path.   *** MUST SETTLE (clue t1.r2.L12) ***
    goal        the team agrees the reported object should expose the directory it inspected as a field
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gideon Halloway will sketch the metadata field once the executor exposes a resolved value; nothing merged; it is settled that the team agrees the reported object should expose the directory it inspected as a field


==============================================================================
# 2025-04-29 — 4 conversation(s), 50 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Nikolai has four commits today touching core request processing, provider integrations, and finetuning; the team needs to align on scope and impact before these land.

    Today is Tuesday 29 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai has four commits today touching core request processing, provider integrations, and finetuning; the team needs to align on scope and impact before these land.
    
    What it should get through:
      1. Clarify num_gpus parameter scope and wiring   [Nikolai Berresford must raise this]
           - Nikolai walks through the commit and its services
           - Dario or Emil questions where it hooks into request processing
           - Group agrees whether it's finetuning-only or affects the main pipeline
      2. Understand structured output override and backend impact   [Nikolai Berresford must raise this]
           - Nikolai explains the override and which providers needed it
           - Emil flags any conflict with existing provider integrations or blocked PRs 651 and 643
           - Group decides if this needs a provider-specific flag or is safe globally
      3. Confirm stdout removal is safe and not a breaking change   [Nikolai Berresford must raise this]
           - Nikolai clarifies why stdout is being removed
           - Dario checks impact on caching, retries, and resume behavior
           - Group settles on whether this is a feature removal or cleanup that should mention in next release
    
    On the agenda: What the num_gpus parameter does and where it wires in; The structured output override: what backends does it affect; Removing stdout support: is that a breaking change or cleanup
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nikolai's four commits are understood and greenlighted for PRs, or specific concerns are documented so he can refine before opening.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Four commits on finetuning, request processing and provider integrations, touching num_gpus parameter, structured output override, and stdout removal
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Clarify num_gpus parameter scope and wiring   *** MUST RAISE ***
      2. Understand structured output override and backend impact   *** MUST RAISE ***
      3. Confirm stdout removal is safe and not a breaking change   *** MUST RAISE ***
    goal        Clarify num_gpus parameter scope and wiring
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Deep knowledge of request processing and provider integration constraints
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clarify num_gpus parameter scope and wiring
      2. Understand structured output override and backend impact
      3. Confirm stdout removal is safe and not a breaking change
    goal        Nikolai has four commits today touching core request processing, provider integrations, and finetuning; the team needs to align on scope and impact before these land.
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release and provider integration expertise, has blocked PRs waiting
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify num_gpus parameter scope and wiring
      2. Understand structured output override and backend impact
      3. Confirm stdout removal is safe and not a breaking change
    goal        Nikolai has four commits today touching core request processing, provider integrations, and finetuning; the team needs to align on scope and impact before these land.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Nikolai's four commits are understood and greenlighted for PRs, or specific concerns are documented so he can refine before opening.


------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Six PRs are older than the consolidation era's 25.6h median merge time; Emil has 4, Gideon has 1, and Nikolai's 653 is blocked on input.

    Today is Tuesday 29 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six PRs are older than the consolidation era's 25.6h median merge time; Emil has 4, Gideon has 1, and Nikolai's 653 is blocked on input.
    
    What it should get through:
      1. Merge or clarify path for Emil's viewer and provider PRs   [Emil Brandvold must raise this]
           - Emil summarizes each PR (651, 652, 654, 656) and any review feedback so far
           - Dario or Gideon flag any concerns or conflicts with their services
           - Group assigns reviewers and target merge date for each
      2. Unblock Gideon's batch update frequency fix   [Gideon Halloway must raise this]
           - Gideon explains the fix and why batch update was too slow
           - Emil or Dario reviews and approves if safe, or flags concerns
           - Group decides merge target
      3. Clear path for Nikolai's 653 finetuning client   [Nikolai Berresford must raise this]
           - Nikolai notes his 653 is waiting on input; group confirms no other blockers
           - Dario or Emil summarize status of 468 and 643 if they are blocking anything else
           - Group agrees next review pass target date
    
    On the agenda: Review state of Emil's four multimodal and viewer PRs; Decide on Gideon's batch update frequency PR; Surface any blockers on 468 (n samples) or 643 (response object)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Each PR has a clear reviewer and merge target; no PR is left without a next step.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Context on 643 (response object), 651 (multimodal openai), 652 (dataset download), 654 (lazy gemini batch)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Merge or clarify path for Emil's viewer and provider PRs   *** MUST RAISE ***
      2. Unblock Gideon's batch update frequency fix
      3. Clear path for Nikolai's 653 finetuning client
      4. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge or clarify path for Emil's viewer and provider PRs
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Context on 632 (batch update frequency increase); owns CLI and observability
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Merge or clarify path for Emil's viewer and provider PRs
      2. Unblock Gideon's batch update frequency fix   *** MUST RAISE ***
      3. Clear path for Nikolai's 653 finetuning client
    goal        Unblock Gideon's batch update frequency fix
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Fresh commits on request processing and structured output; can review others' PRs
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Merge or clarify path for Emil's viewer and provider PRs
      2. Unblock Gideon's batch update frequency fix
      3. Clear path for Nikolai's 653 finetuning client   *** MUST RAISE ***
    goal        Clear path for Nikolai's 653 finetuning client
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Each PR has a clear reviewer and merge target; no PR is left without a next step.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Nikolai's four commits touch the core request layer (online-request-processing, provider-integrations, bulk-llm-inference, caching-and-resume); the service owners need to validate impact.

    Today is Tuesday 29 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai's four commits touch the core request layer (online-request-processing, provider-integrations, bulk-llm-inference, caching-and-resume); the service owners need to validate impact.
    
    What it should get through:
      1. Validate caching and resume aren't broken by changes   [Dario Kestrel must raise this]
           - Nikolai describes which commits touch caching or retry paths
           - Dario walks through the caching key and invalidation logic; checks if structured output or stdout removal changes keys
           - Group confirms that cache hits and resume still work across these changes
      2. Confirm structured output override is safe and provider-agnostic   [Emil Brandvold must raise this]
           - Nikolai explains what the override does and which providers needed it
           - Emil checks for conflict with 643 (response object) and notes which backends it affects
           - Group decides if the override can be global or needs a provider flag
      3. Understand stdout removal scope and impact on observability   [Gideon Halloway must raise this]
           - Nikolai clarifies why stdout is being removed and what still gets logged
           - Gideon checks impact on progress bars, error messages, and cost accounting
           - Group confirms that users can still debug and that CLI output is unaffected
    
    On the agenda: Impact on caching and resume semantics from the changes; Structured output override and whether it needs provider-specific code paths; Stdout removal and how it affects tracing, logging, and debugging
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nikolai's changes are validated against request layer semantics, or specific changes are flagged as needing revision before landing.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Deepest expertise on request sequencing, caching invalidation, and retry logic
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate caching and resume aren't broken by changes   *** MUST RAISE ***
      2. Confirm structured output override is safe and provider-agnostic
      3. Understand stdout removal scope and impact on observability
    goal        Validate caching and resume aren't broken by changes
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Release and provider integration context; blocked on 468, 643, 651
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate caching and resume aren't broken by changes
      2. Confirm structured output override is safe and provider-agnostic   *** MUST RAISE ***
      3. Understand stdout removal scope and impact on observability
      4. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm structured output override is safe and provider-agnostic
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability and progress tracking expertise; can catch impact on batch updates or cost accounting
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate caching and resume aren't broken by changes
      2. Confirm structured output override is safe and provider-agnostic
      3. Understand stdout removal scope and impact on observability   *** MUST RAISE ***
    goal        Understand stdout removal scope and impact on observability
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Nikolai's changes are validated against request layer semantics, or specific changes are flagged as needing revision before landing.


------------------------------------------------------------------------------
## #general — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Nikolai Berresford pushed the renamed key and a validation check and asked whether the override should mean anything outside the docker path

    Today is Tuesday 29 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nikolai Berresford pushed the renamed key and a validation check and asked whether the override should mean anything outside the docker path
    
    What it should get through:
    
    On the agenda: Emil Brandvold says he spent an hour on a run last month where he had fat-fingered a backend_params key and nothing complained, it just ran with the default, and he does not want a second knob with the same failure mode; Konrad Feltrin tried the new key against the local backend and against the hosted sandbox backend and both accepted it and ignored it, which he calls worse than refusing it; Dermot Callaghan says an override that only means something on one backend should say so out loud when handed to the others, rather than being quietly dropped
    
    Wrap when: Nikolai Berresford agrees to make the non-docker backends complain, but the exact behaviour, raise versus warn, is left to whoever reviews next; it is settled that Emil Brandvold rules out aborting the run when the stored job cannot be reused
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        Nikolai Berresford pushed the renamed key and a validation check and asked whether the override should mean anything outside the docker path
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. I hacked a guard in locally that raised when the stored job looked off, ran it against a nightly, and it died at 3am four hours in. that is worse than what we have now for anyone running unattended. a job dying because someone touched the config is not a fix.   *** MUST SETTLE (clue t3.r2.l_beh_emil) ***
    goal        Emil Brandvold rules out aborting the run when the stored job cannot be reused
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Nikolai Berresford pushed the renamed key and a validation check and asked whether the override should mean anything outside the docker path
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nikolai Berresford agrees to make the non-docker backends complain, but the exact behaviour, raise versus warn, is left to whoever reviews next; it is settled that Emil Brandvold rules out aborting the run when the stored job cannot be reused; Emil Brandvold rules out aborting the run when the stored job cannot be reused


==============================================================================
# 2025-05-01 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: New feature PR opened; 6 stale PRs need path to merge

    Today is Thursday 1 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: New feature PR opened; 6 stale PRs need path to merge
    
    What it should get through:
      1. Get PR 658 reviewed and ready for merge   [Emil Brandvold must raise this]
           - Emil presents design
           - Dermot and Gideon probe integration surface
           - Decision on merge readiness or requested changes
      2. Unblock PR 643 response object PR   [Dermot Callaghan must raise this]
           - Dermot raises blocking concerns from review
           - Emil addresses and confirms resolution
           - Agreement on merge or final feedback
      3. write up Handover: Status Tracking, Cost Reporting & the Viewer Surface   [Gideon Halloway must raise this]
           - Gideon Halloway says they will write Handover: Status Tracking, Cost Reporting & the Viewer Surface — Gideon's write-up handing status tracking, cost reporting, and viewer work to Emil Brandvold.
    
    On the agenda: Review PR 658 agentic/multiturn design and implementation; Unblock stale PRs: PR 468, PR 643, PR 651, PR 652, PR 632; Clarify integration points with response objects and observability; Handover: Status Tracking, Cost Reporting & the Viewer Surface
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 658 has a clear review path; PR 643 either merges or has concrete next steps
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 337 changes merged to date

    On the table
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - WS-055: Release Engineering, CI & Test Suite (Dermot Callaghan)
      - Handover: Status Tracking, Cost Reporting & the Viewer Surface (Gideon Halloway)
      - Handover: Status Tracking, Cost Reporting & the Viewer Surface (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 651: ref: update multimodal support models in openai (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Design and implementation of multi-turn agentic curation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get PR 658 reviewed and ready for merge   *** MUST RAISE ***
      2. Unblock PR 643 response object PR
      3. write up Handover: Status Tracking, Cost Reporting & the Viewer Surface
      4. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 658 reviewed and ready for merge
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Pipeline and inference perspective on response objects
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Get PR 658 reviewed and ready for merge
      2. Unblock PR 643 response object PR   *** MUST RAISE ***
      3. write up Handover: Status Tracking, Cost Reporting & the Viewer Surface
      4. what "WS-055: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock PR 643 response object PR
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability and CLI perspective
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Get PR 658 reviewed and ready for merge
      2. Unblock PR 643 response object PR
      3. write up Handover: Status Tracking, Cost Reporting & the Viewer Surface   *** MUST RAISE ***
      4. the page you are writing, Handover: Status Tracking, Cost Reporting & the Viewer Surface, has to say this in your own words: For a machine with no history the truthful answer is that nothing is on disk and every request will go to the provider. That is a perfectly good number to report, all hits at zero and everything counted as going to the backend.   *** MUST SETTLE (clue t1.r2.L9) ***
      5. that the doc "Handover: Status Tracking, Cost Reporting & the Viewer Surface" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Handover: Status Tracking, Cost Reporting & the Viewer Surface
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 658 has a clear review path; PR 643 either merges or has concrete next steps


------------------------------------------------------------------------------
## #engineering — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: pulling together everything still open so the change can land in a release instead of drifting

    Today is Thursday 1 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: pulling together everything still open so the change can land in a release instead of drifting
    
    What it should get through:
    
    On the agenda: Dario Kestrel reports the invalidation number he promised, and repeats that a stale hit after the execution environment moves should come back as a miss and re-run, not as a fast pass; Nikolai Berresford still has no answer from the sandbox side on which tags stay alive, so the constant has a placeholder in the branch; Dermot Callaghan lists what he is not willing to ship without: one place holding the default, a changelog line when it moves, and the resolved value visible in the log and in run metadata
    
    Wrap when: the shape is agreed and three specifics are still open, the tag value, digest versus tag, and whether non-docker backends raise or warn; Nikolai Berresford to chase the sandbox team; it is settled that the team agrees the shipped default must be a signed-off build rather than an arbitrary or newest tag
    
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
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)

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
      - — and 358 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. On the executor image question: whatever value we bake in as the shipped default has to be a build somebody actually signed off, not just the newest thing that came out of CI green. We have shipped a container to users before that nobody had run the verifier suite against and I would rather not repeat it.   *** MUST SETTLE (clue t4.r1.L3) ***
    goal        the team agrees the shipped default must be a signed-off build rather than an arbitrary or newest tag
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. 
    owns        code-execution, release-and-ci, telemetry
    agenda
    goal        pulling together everything still open so the change can land in a release instead of drifting
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        pulling together everything still open so the change can land in a release instead of drifting
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        pulling together everything still open so the change can land in a release instead of drifting
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   the shape is agreed and three specifics are still open, the tag value, digest versus tag, and whether non-docker backends raise or warn; Nikolai Berresford to chase the sandbox team; it is settled that the team agrees the shipped default must be a signed-off build rather than an arbitrary or newest tag


==============================================================================
# 2025-05-02 — 3 conversation(s), 21 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two merges landed this morning; six older PRs need clarity on blockers

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two merges landed this morning; six older PRs need clarity on blockers
    
    What it should get through:
      1. Confirm PR 656 and PR 659 merge readiness   [Emil Brandvold must raise this]
           - Emil explains the multimodal input fix scope
           - Konrad nods on test coverage
           - Both approved
      2. Unblock stale PR queue   [Gideon Halloway must raise this]
           - Gideon flags PR 632 batch-freq as critical blocker
           - Emil routes PR 643 response-object toward next sprint
           - Others parked pending architecture decisions
    
    On the agenda: Post-merge: PR 656 anthropic backend and PR 659 version bump; Stale PR status: PR 643, PR 652, PR 468, PR 632 blocking; CLI batch-freq work context (Gideon Halloway's PR 632)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 656 and PR 659 confirmed; stale PR triage complete; PR 632 escalated or re-prioritized
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Anthropic multimodal input fix and version bump details
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 656 and PR 659 merge readiness   *** MUST RAISE ***
      2. Unblock stale PR queue
      3. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 656 and PR 659 merge readiness
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder perspective on release readiness
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 656 and PR 659 merge readiness
      2. Unblock stale PR queue
    goal        Two merges landed this morning; six older PRs need clarity on blockers
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI batch update-freq context for parallel work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 656 and PR 659 merge readiness
      2. Unblock stale PR queue   *** MUST RAISE ***
    goal        Unblock stale PR queue
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 656 and PR 659 confirmed; stale PR triage complete; PR 632 escalated or re-prioritized


------------------------------------------------------------------------------
## #pipeline — 7 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work
    
    What it should get through:
      1. Anthropic multimodal request formatting fixed   [Emil Brandvold must raise this]
           - Emil walks through the formatter refactor
           - Dermot questions edge cases with structured output
           - Confirms existing tests cover the change
      2. Batch CLI update-freq and provider fixes are independent   [Gideon Halloway must raise this]
           - Gideon explains CLI polling interval issue
           - Emil confirms no shared state
           - Proceed in parallel
    
    On the agenda: PR 656 anthropic multimodal input formatter bug; Batch CLI update-freq fix scope (Gideon Halloway); Provider coverage and test plan
    
    No longer here: Nils Brandt, Theo Marchetti — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 656 anthropic fix understood; Gideon Halloway proceeds with PR 632 CLI work independently; no follow-up multimodal bug ticket opened
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Root cause of anthropic backend multimodal input formatting bug
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Anthropic multimodal request formatting fixed   *** MUST RAISE ***
      2. Batch CLI update-freq and provider fixes are independent
    goal        Anthropic multimodal request formatting fixed
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Batch update-freq CLI fix parallel work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Anthropic multimodal request formatting fixed
      2. Batch CLI update-freq and provider fixes are independent   *** MUST RAISE ***
    goal        Batch CLI update-freq and provider fixes are independent
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Request-formatter domain knowledge
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Anthropic multimodal request formatting fixed
      2. Batch CLI update-freq and provider fixes are independent
    goal        Anthropic multimodal input bug landed; Gideon Halloway has parallel batch CLI work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 656 anthropic fix understood; Gideon Halloway proceeds with PR 632 CLI work independently; no follow-up multimodal bug ticket opened


------------------------------------------------------------------------------
## #releases — 6 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.24 version bump merged; response object PR stalled 16 days

    Today is Friday 2 May 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.24 version bump merged; response object PR stalled 16 days
    
    What it should get through:
      1. v0.1.24 release approved   [Emil Brandvold must raise this]
           - Emil confirms bump only, no features
           - Konrad confirms nothing controversial
           - Dermot signs off changelog
      2. Response object PR (PR 643) path forward   [Emil Brandvold must raise this]
           - Emil presents blocking concern on PR 643
           - Konrad decides: land after 0.1.24 or hold for next sprint
           - Group aligns on timeline
    
    On the agenda: v0.1.24 version bump (PR 659) scope; Response object PR (PR 643) landability; Release notes and changelog review
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.24 approved; PR 643 response object scheduled for next sprint or unblocked with clear conditions
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 22 release(s) shipped, currently v0.1.23
      - 339 changes merged to date

    On the table
      - v0.1.23 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 632: Fix/curator-cli-batch-update-freq-increase (Gideon Halloway)
      - PR 640: Feat/openai/deepseek api (Tomas Berczik)
      - PR 643: feat: add response object in curator (Emil Brandvold)
      - PR 652: feat: add support to download dataset from viewer (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)

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
      - — and 356 function/class names and 44 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Version bump details and changelog
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. v0.1.24 release approved   *** MUST RAISE ***
      2. Response object PR (PR 643) path forward   *** MUST RAISE ***
      3. what "v0.1.23 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        v0.1.24 release approved
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founder sign-off and strategic context
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. v0.1.24 release approved
      2. Response object PR (PR 643) path forward
    goal        v0.1.24 version bump merged; response object PR stalled 16 days
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. v0.1.24 release approved
      2. Response object PR (PR 643) path forward
    goal        v0.1.24 version bump merged; response object PR stalled 16 days
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.24 approved; PR 643 response object scheduled for next sprint or unblocked with clear conditions

