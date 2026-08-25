# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-03-13 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs in flight touching batch mode and provider integrations; three reviewers; Nils needs unblock on his core work.

    Today is Thursday 13 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs in flight touching batch mode and provider integrations; three reviewers; Nils needs unblock on his core work.
    
    What it should get through:
      1. Merge PR 588 input validation after addressing requested changes   [Konrad Feltrin must raise this]
           - Emil raises concern about dict vs list handling edge case
           - Konrad clarifies the fix scope and test coverage
           - Nils confirms the pattern won't break Mistral batch upload
      2. Clarify batch processor factory pattern for new backends (Mistral, Bedrock)   [Nils Brandt must raise this]
           - Nils describes what the Mistral factory needs
           - Dario asks how Bedrock should fit the same abstraction
           - Emil sketches the refactor if needed, or confirms current shape works
    
    On the agenda: Mistral batch processor design and test coverage; Input validation edge cases in PR 588; Bedrock processor integration approach; Batch processor factory pattern alignment
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 588 approved with minor changes; PR 584 factory shape confirmed so Nils can finish; PR 589 (Bedrock) can proceed without blocking on architecture questions.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 289 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 10 (Nils Brandt)
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. input validation fix and test strategy
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Merge PR 588 input validation after addressing requested changes   *** MUST RAISE ***
      2. Clarify batch processor factory pattern for new backends (Mistral, Bedrock)
      3. what "Weekly Notes — Week of Mar 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Merge PR 588 input validation after addressing requested changes
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch processor implementation details
    owns        batch-mode, provider-integrations
    agenda
      1. Merge PR 588 input validation after addressing requested changes
      2. Clarify batch processor factory pattern for new backends (Mistral, Bedrock)   *** MUST RAISE ***
      3. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify batch processor factory pattern for new backends (Mistral, Bedrock)
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. provider integration expertise and batch-mode patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Merge PR 588 input validation after addressing requested changes
      2. Clarify batch processor factory pattern for new backends (Mistral, Bedrock)
    goal        Four PRs in flight touching batch mode and provider integrations; three reviewers; Nils needs unblock on his core work.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. AWS Bedrock processor patterns for comparison
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Merge PR 588 input validation after addressing requested changes
      2. Clarify batch processor factory pattern for new backends (Mistral, Bedrock)
    goal        Four PRs in flight touching batch mode and provider integrations; three reviewers; Nils needs unblock on his core work.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 588 approved with minor changes; PR 584 factory shape confirmed so Nils can finish; PR 589 (Bedrock) can proceed without blocking on architecture questions.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Nils has landed eight commits on batch, cost, and Mistral; Consolidation era is about broadening provider support; need to verify architecture can sustain three new backends (Mistral, Bedrock, DeepSeek).

    Today is Thursday 13 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nils has landed eight commits on batch, cost, and Mistral; Consolidation era is about broadening provider support; need to verify architecture can sustain three new backends (Mistral, Bedrock, DeepSeek).
    
    What it should get through:
      1. Verify Mistral batch processor is production-ready or unblock final fixes   [Nils Brandt must raise this]
           - Nils walks through the six commits: factory, cost processing, API key handling, file upload
           - Emil asks about error handling in batch submission and polling
           - Dario wants confirmation on retry behavior with batch IDs
      2. Establish cost processing as non-blocking for batch merge or identify dependency   [Emil Brandvold must raise this]
           - Emil describes what cost accounting needs from batch
           - Nils clarifies whether Mistral API returns costs in batch response
           - Dermot asks if cost tracking can be post-landing (v0.1.21) without breaking billing
    
    On the agenda: Mistral batch processor implementation state; Cost processing placement and dependencies; Resume semantics with batch jobs; Request processor factory alignment
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nils and Emil agree on whether PR 584 can merge as-is or needs one more fix; cost processing gets a landing plan (this release or next); Dario knows how to unblock Bedrock PR by following the same pattern.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 289 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 10 (someone)
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). six commits on Mistral batch, cost processing, API key handling
    owns        batch-mode, provider-integrations
    agenda
      1. Verify Mistral batch processor is production-ready or unblock final fixes   *** MUST RAISE ***
      2. Establish cost processing as non-blocking for batch merge or identify dependency
      3. what "notes-2025-03-10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify Mistral batch processor is production-ready or unblock final fixes
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. cost accounting patterns and batch semantics
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Verify Mistral batch processor is production-ready or unblock final fixes
      2. Establish cost processing as non-blocking for batch merge or identify dependency   *** MUST RAISE ***
      3. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Establish cost processing as non-blocking for batch merge or identify dependency
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. request processor abstraction and provider onboarding experience
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Verify Mistral batch processor is production-ready or unblock final fixes
      2. Establish cost processing as non-blocking for batch merge or identify dependency
    goal        Nils has landed eight commits on batch, cost, and Mistral; Consolidation era is about broadening provider support; need to verify architecture can sustain three new backends (Mistral, Bedrock, DeepSeek).
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. request layer and persistence semantics
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Verify Mistral batch processor is production-ready or unblock final fixes
      2. Establish cost processing as non-blocking for batch merge or identify dependency
    goal        Nils has landed eight commits on batch, cost, and Mistral; Consolidation era is about broadening provider support; need to verify architecture can sustain three new backends (Mistral, Bedrock, DeepSeek).
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nils and Emil agree on whether PR 584 can merge as-is or needs one more fix; cost processing gets a landing plan (this release or next); Dario knows how to unblock Bedrock PR by following the same pattern.


==============================================================================
# 2025-03-14 — 2 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dermot's semaphore fix and Konrad's input-handling work both landed today; they need to confirm the pieces fit together.

    Today is Friday 14 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dermot's semaphore fix and Konrad's input-handling work both landed today; they need to confirm the pieces fit together.
    
    What it should get through:
      1. Dermot's semaphore gating prevents row-creation OOMs at scale   [Dermot Callaghan must raise this]
           - Dermot describes the OOM and why gating helps
           - Konrad asks about the performance tradeoff
           - Landing: semaphore approach approved as safe
      2. Konrad's list/string handling covers the case when users don't pass a dictionary   [Konrad Feltrin must raise this]
           - Konrad walks through PR PR 588 and the test
           - Emil confirms the merge and the coverage
           - Confirmation that this ships in the next release
    
    On the agenda: OOM problem and semaphore gating solution; Input handling: list/string case coverage; Logger propagation in this context
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Both changes land and are confirmed to work together; the workstream moves out of this mid-flight phase.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 290 changes merged to date

    On the table
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 434 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. The OOM at scale problem and the semaphore solution
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Dermot's semaphore gating prevents row-creation OOMs at scale   *** MUST RAISE ***
      2. Konrad's list/string handling covers the case when users don't pass a dictionary
    goal        Dermot's semaphore gating prevents row-creation OOMs at scale
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Test coverage for prompt__internal and validation that list/string handling is solid
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Dermot's semaphore gating prevents row-creation OOMs at scale
      2. Konrad's list/string handling covers the case when users don't pass a dictionary   *** MUST RAISE ***
      3. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Konrad's list/string handling covers the case when users don't pass a dictionary
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Logger propagation fix and awareness of the pipeline changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Dermot's semaphore gating prevents row-creation OOMs at scale
      2. Konrad's list/string handling covers the case when users don't pass a dictionary
    goal        Dermot's semaphore fix and Konrad's input-handling work both landed today; they need to confirm the pieces fit together.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both changes land and are confirmed to work together; the workstream moves out of this mid-flight phase.


------------------------------------------------------------------------------
## #code-review — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Dario Kestrel pushed a first cut of a schema_check module and wants eyes before he wires it into either hook point

    Today is Friday 14 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel pushed a first cut of a schema_check module and wants eyes before he wires it into either hook point
    
    What it should get through:
    
    On the agenda: Dario Kestrel describes _validate_response_format walking the model's fields and what it currently rejects, and admits the reject list came from the help thread and nothing else; Gideon Halloway pushes on the message text: the draft raises with the class name only, and he says when he debugged the Gemini one what he actually needed was which field and which model it was going to; Emil Brandvold raises the offline case, since a vLLM run does not go through a provider at all and he does not want his local runs blocked by a table of hosted-provider rules
    
    Wrap when: draft accepted as a starting point, message content and the offline path both left open; Emil Brandvold to say what the local processor can and cannot honour; it is settled that the team agrees construction currently returns objects that cannot possibly run
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 290 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 434 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. this bit me again in a notebook. cell four builds the LLM and returns happily, cell five hands it the dataset and twenty minutes into the map it turns out the combination was never going to work. the object was already unusable when cell four finished and it told me nothing   *** MUST SETTLE (clue t2.r1.L6) ***
    goal        the team agrees construction currently returns objects that cannot possibly run
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel pushed a first cut of a schema_check module and wants eyes before he wires it into either hook point
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel pushed a first cut of a schema_check module and wants eyes before he wires it into either hook point
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   draft accepted as a starting point, message content and the offline path both left open; Emil Brandvold to say what the local processor can and cannot honour; it is settled that the team agrees construction currently returns objects that cannot possibly run


==============================================================================
# 2025-03-17 — 3 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #pipeline — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Nils landed four commits on Mistral batch processing over the weekend; the team needs to assess fit and unblock PR 584

    Today is Monday 17 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nils landed four commits on Mistral batch processing over the weekend; the team needs to assess fit and unblock PR 584
    
    What it should get through:
      1. Confirm Mistral batch client architecture fits the provider abstraction   [Nils Brandt must raise this]
           - Nils walks through the sync wrapper and _download_and_load_output parsing
           - Emil raises any concern about response format consistency across providers
           - Dario confirms this pattern holds for deepseek/openai batch modes
      2. Validate token usage tracking for cost accounting   [Emil Brandvold must raise this]
           - Nils explains the response structure and extraction logic
           - Emil checks whether the _TokenUsage instance matches existing cost processor contracts
           - Team agrees on any schema normalization needed
      3. Clear path to merge PR 584 or identify blockers   [Nils Brandt must raise this]
           - Nils describes test coverage: what the integration tests exercise
           - Emil or Dario flag any gaps against the batch workflow
           - Team decides whether this lands as-is or needs another pass
    
    On the agenda: Review Mistral client refactor and async/await changes; Token usage extraction and _TokenUsage instance creation; Integration test coverage and batch request flow
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nils has a clear understanding of what needs adjustment before PR 584 can merge, or confirmation that it is ready for review cycle.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 293 changes merged to date

    On the table
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - Release notes: v0.1.20 (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Four commits on Mistral batch: client refactor, token usage parsing, integration tests
    owns        batch-mode, provider-integrations
    agenda
      1. Confirm Mistral batch client architecture fits the provider abstraction   *** MUST RAISE ***
      2. Validate token usage tracking for cost accounting
      3. Clear path to merge PR 584 or identify blockers   *** MUST RAISE ***
      4. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Mistral batch client architecture fits the provider abstraction
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Understanding of batch processor patterns and token cost accounting
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Mistral batch client architecture fits the provider abstraction
      2. Validate token usage tracking for cost accounting   *** MUST RAISE ***
      3. Clear path to merge PR 584 or identify blockers
    goal        Validate token usage tracking for cost accounting
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on provider abstraction and cost processor design
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm Mistral batch client architecture fits the provider abstraction
      2. Validate token usage tracking for cost accounting
      3. Clear path to merge PR 584 or identify blockers
    goal        Nils landed four commits on Mistral batch processing over the weekend; the team needs to assess fit and unblock PR 584
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nils has a clear understanding of what needs adjustment before PR 584 can merge, or confirmation that it is ready for review cycle.


------------------------------------------------------------------------------
## #code-review — 14 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 10 PRs are older than the era median merge time (6.6h); queue management and unblocking is the agenda

    Today is Monday 17 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 10 PRs are older than the era median merge time (6.6h); queue management and unblocking is the agenda
    
    What it should get through:
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns   [Konrad Feltrin must raise this]
           - Konrad summarizes the refactoring scope and Emil Brandvold's approval
           - Emil confirms comments are satisfied or raises outstanding concern
           - Konrad decides on merge or final pass
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work   [Emil Brandvold must raise this]
           - Emil describes the three-PR dependency: Dario Kestrel's PR 565/#566, then Emil Brandvold's PR 579 and PR 585
           - Dario signals blockers or readiness on his PRs
           - Emil flags whether PR 586 token-usage fix blocks the chain
      3. Triage low-priority config PRs for next action   [Nikolai Berresford must raise this]
           - Gideon and Nikolai Berresford each explain their PR scope
           - Team agrees whether these land before the release cut or after
           - Any blockers named
    
    On the agenda: PR 592 cleanup work: validation refactoring status; Openai/deepseek integration blockers: PR 565, PR 566, PR 579, PR 585; Environment and config PRs: PR 581, PR 583
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear picture of which PRs are ready to merge, which are blocked, and which can be deferred past the release cut.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 293 changes merged to date

    On the table
      - weekly-2025-03-10 (Konrad Feltrin)
      - Release notes: v0.1.20 (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Ownership of landing cleanup work; sight into validation refactoring
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns   *** MUST RAISE ***
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
      3. Triage low-priority config PRs for next action
      4. that "Weekly update: week of Mar 10" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Confirm PR 592 cleanup is ready to merge or flag final concerns
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Active work on PR 579, PR 585, PR 586; understands blocker patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work   *** MUST RAISE ***
      3. Triage low-priority config PRs for next action
    goal        Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Fresh batch mode work; knows where provider integration sits
    owns        batch-mode, provider-integrations
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
      3. Triage low-priority config PRs for next action
    goal        10 PRs are older than the era median merge time (6.6h); queue management and unblocking is the agenda
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on PR 565, PR 566 openai/deepseek API layers
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
      3. Triage low-priority config PRs for next action
    goal        10 PRs are older than the era median merge time (6.6h); queue management and unblocking is the agenda
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. PR 581 environment variable work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
      3. Triage low-priority config PRs for next action
    goal        10 PRs are older than the era median merge time (6.6h); queue management and unblocking is the agenda
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. PR 583 metadata db parameter
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm PR 592 cleanup is ready to merge or flag final concerns
      2. Map blockers for PR 565, PR 566, PR 579, PR 585 openai/deepseek work
      3. Triage low-priority config PRs for next action   *** MUST RAISE ***
      4. what "Release notes: v0.1.20" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Triage low-priority config PRs for next action
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clear picture of which PRs are ready to merge, which are blocked, and which can be deferred past the release cut.


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: standing check-in on the feature while Emil Brandvold is out; the question of the rule source has not moved since the draft

    Today is Monday 17 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: standing check-in on the feature while Emil Brandvold is out; the question of the rule source has not moved since the draft
    
    What it should get through:
    
    On the agenda: Dermot Callaghan asks whether we are maintaining our own table of which model takes which construct, and nobody wants to own that table; Gideon Halloway says the one thing he is sure of is that finding out by asking the provider is not an option, because a run that has to make a call to learn whether it may make calls is going to be the next help thread; Dario Kestrel says he will look at what litellm already exposes for this and report back
    
    Wrap when: nothing decided, Dario Kestrel to check litellm's capability helpers before the next round of the PR; it is settled that the team agrees the support table must match gpt-4o family names by pattern, not by exact key
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 293 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: gpt-4o-2024-08-06.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        standing check-in on the feature while Emil Brandvold is out; the question of the rule source has not moved since the draft
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. someone in help pasted a run on gpt-4o-2024-08-06 where our capability lookup came back false, so they got shunted onto the plain text path. the map only had the bare `gpt-4o` key in it. providers keep bolting dates onto these names, exact-key lookups are never going to survive that   *** MUST SETTLE (clue t2.r1.L2) ***
         must contain literally: gpt-4o-2024-08-06
    goal        the team agrees the support table must match gpt-4o family names by pattern, not by exact key
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        standing check-in on the feature while Emil Brandvold is out; the question of the rule source has not moved since the draft
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   nothing decided, Dario Kestrel to check litellm's capability helpers before the next round of the PR; it is settled that the team agrees the support table must match gpt-4o family names by pattern, not by exact key


==============================================================================
# 2025-03-18 — 2 conversation(s), 26 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 584 has sat for 7 days with changes requested from both Dario Kestrel and Emil Brandvold; blocking the batch-mode workstream and needs resolution today

    Today is Tuesday 18 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 584 has sat for 7 days with changes requested from both Dario Kestrel and Emil Brandvold; blocking the batch-mode workstream and needs resolution today
    
    What it should get through:
      1. Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)   [Nils Brandt must raise this]
           - Nils walks through the Mistral batch shape and where it diverges from Emil's 585 approach
           - Emil pushes back on token estimate handling — batch processors need int wrapping like litellm fix
           - Lands as: merge 584 with token-estimate fix, 585 consolidates the pattern across other batch backends
      2. Verify batch requests don't recreate the kluster cost-estimation blindspot   [Gideon Halloway must raise this]
           - Gideon raises: are batch processors feeding float token estimates into rate limiter like deepseek did?
           - Emil confirms litellm fix wraps in int, batch processors should do the same
           - Lands as: batch processors must wrap token estimates before rate limiter, add test case
      3. Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern   [Dario Kestrel must raise this]
           - Dario: 565/566 have been open 16 days, waiting to see if batch pattern changes the shape
           - Nils/Emil: batch doesn't require reshaping the backend interface, just processing layer
           - Lands as: Dario Kestrel can land 565/566 independently, batch work layers on top
    
    On the agenda: Review of PR 584: Mistral batch implementation and integration points; Token estimate handling and cost processor compatibility; Batch processor pattern vs. existing provider integrations (565/566)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 584 either lands with changes or is explicitly deferred with a clear reason; batch integration pattern is clear enough that 585 and 565/566 can move in parallel
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 293 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - design-ws-047-release-and-ci (Nils Brandt)
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). The Mistral batch processor implementation and understanding of what batch API shape it needs
    owns        batch-mode, provider-integrations
    agenda
      1. Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)   *** MUST RAISE ***
      2. Verify batch requests don't recreate the kluster cost-estimation blindspot
      3. Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern
      4. that the doc "WS-047: Release Engineering, CI & Test Suite" is done, and where the others can find it   *** MUST RAISE ***
      5. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Experience with provider integration patterns from 565/566 (OpenAI/DeepSeek backends) and request processing ownership
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)
      2. Verify batch requests don't recreate the kluster cost-estimation blindspot
      3. Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern   *** MUST RAISE ***
    goal        Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Deep knowledge of request processing and cost estimation; just landed token-wrapping fixes that affect batch processors
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)
      2. Verify batch requests don't recreate the kluster cost-estimation blindspot
      3. Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern
    goal        PR 584 has sat for 7 days with changes requested from both Dario Kestrel and Emil Brandvold; blocking the batch-mode workstream and needs resolution today
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Understanding of cost estimation and backpressure from the kluster incident; owns the rate limiter that batch requests feed into
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clarify the batch processor interface so it can be consolidated with 585 (Feat/retry/batch)
      2. Verify batch requests don't recreate the kluster cost-estimation blindspot   *** MUST RAISE ***
      3. Unblock Dario Kestrel's OpenAI/DeepSeek backends (565/566) by establishing provider integration pattern
      4. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify batch requests don't recreate the kluster cost-estimation blindspot
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 584 either lands with changes or is explicitly deferred with a clear reason; batch integration pattern is clear enough that 585 and 565/566 can move in parallel


------------------------------------------------------------------------------
## #random — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #random: model-release chatter turns into a war story about silent truncation

    Today is Tuesday 18 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: model-release chatter turns into a war story about silent truncation
    
    What it should get through:
    
    On the agenda: Gideon Halloway links the release notes for a new hosted endpoint and mentions someone on the forum found it just omits unknown schema keywords instead of erroring; Dermot Callaghan says he wasted a day last year on exactly that against a different provider, because the dataset came back looking plausible and the missing field only turned up in training; Emil Brandvold jokes that a 400 is the good outcome and that he would rather be shouted at than handed a quietly wrong dataset
    
    Wrap when: no action, but the preference for loud failure over quiet degradation is now something three people have said out loud; it is settled that the team agrees changing the model currently returns the previous model's stored answers
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 293 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: gpt-4o, gpt-4o-mini.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Lost most of yesterday to this. Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk. The outputs were the mini ones. I only noticed because the formatting was too sloppy for 4o.   *** MUST SETTLE (clue t1.r1.l_model_1) ***
         must contain literally: gpt-4o-mini, gpt-4o
    goal        the team agrees changing the model currently returns the previous model's stored answers
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        model-release chatter turns into a war story about silent truncation
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        model-release chatter turns into a war story about silent truncation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   no action, but the preference for loud failure over quiet degradation is now something three people have said out loud; it is settled that the team agrees changing the model currently returns the previous model's stored answers


==============================================================================
# 2025-03-19 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.21 shipped today; need to land the release notes and announce it

    Today is Wednesday 19 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.21 shipped today; need to land the release notes and announce it
    
    What it should get through:
      1. Finalize release notes for v0.1.21   [Dermot Callaghan must raise this]
           - Dermot walks through the two bugfixes (token counting, unicode output)
           - Emil and Konrad confirm the fixes are sound
           - Dermot refines the changelog language
      2. Post announcement to stakeholders   [Dermot Callaghan must raise this]
           - Konrad signs off on shipping
           - Dermot sends the mail
    
    On the agenda: What landed in v0.1.21 and why; Changelog accuracy and tone; Release announcement readiness
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.21 release notes are written and announcement is sent; the two bugfixes are documented for users
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 295 changes merged to date

    On the table
      - v0.1.21 Release Notes (Dermot Callaghan)
      - notes-2025-03-17 (Nils Brandt)
      - announce-v0-1-21 (Dermot Callaghan)
      - release-v0-1-21 (Dermot Callaghan)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. the two bugfixes landing today (unicode output fix, token wrap)
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Finalize release notes for v0.1.21   *** MUST RAISE ***
      2. Post announcement to stakeholders   *** MUST RAISE ***
      3. that the doc "v0.1.21 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.21 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Weekly Notes — Week of Mar 17" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "v0.1.21 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Finalize release notes for v0.1.21
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. release oversight and precedent
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Finalize release notes for v0.1.21
      2. Post announcement to stakeholders
    goal        v0.1.21 shipped today; need to land the release notes and announce it
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on the litellm token-wrapping fix that went in
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Finalize release notes for v0.1.21
      2. Post announcement to stakeholders
    goal        v0.1.21 shipped today; need to land the release notes and announce it
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.21 release notes are written and announcement is sent; the two bugfixes are documented for users


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Five commits landed touching batch-mode and provider-integrations; Mistral backend is blocked on api_key configuration

    Today is Wednesday 19 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Five commits landed touching batch-mode and provider-integrations; Mistral backend is blocked on api_key configuration
    
    What it should get through:
      1. Confirm Gemini batch unicode fix is solid   [Dermot Callaghan must raise this]
           - Dermot explains the escaped unicode problem
           - Emil confirms the fix is minimal and targeted
           - Group agrees it's safe
      2. Resolve Mistral api_key configuration so PR PR 584 can land   [Nils Brandt must raise this]
           - Nils walks through the fix (passing api_key to constructor)
           - Emil checks it against the pattern for other providers
           - Gideon flags any auth or initialization concerns
      3. Verify no regression in rate-limiting backpressure after token fixes   [Gideon Halloway must raise this]
           - Gideon raises the original kluster.ai deepseek issue
           - Nils confirms BaseState refactor doesn't change rate-limit behavior
           - Emil agrees the changes are orthogonal to queue management
    
    On the agenda: Gemini unicode output fix status; Mistral api_key blocking issue; Impact on rate limiting and backpressure
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Gemini fix is confirmed safe; Mistral api_key issue is resolved and PR PR 584 can proceed; no rate-limiting regressions are identified
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 295 changes merged to date

    On the table
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). five commits on batch-mode and provider-integrations, including Mistral api_key fix and state management refactor
    owns        batch-mode, provider-integrations
    agenda
      1. Confirm Gemini batch unicode fix is solid
      2. Resolve Mistral api_key configuration so PR PR 584 can land   *** MUST RAISE ***
      3. Verify no regression in rate-limiting backpressure after token fixes
      4. that the doc "Weekly Notes — Week of Mar 17" is done, and where the others can find it   *** MUST RAISE ***
    goal        Resolve Mistral api_key configuration so PR PR 584 can land
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. the Gemini unicode output fix and context on what broke
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm Gemini batch unicode fix is solid   *** MUST RAISE ***
      2. Resolve Mistral api_key configuration so PR PR 584 can land
      3. Verify no regression in rate-limiting backpressure after token fixes
    goal        Confirm Gemini batch unicode fix is solid
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. token-estimation context and provider backend patterns
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Gemini batch unicode fix is solid
      2. Resolve Mistral api_key configuration so PR PR 584 can land
      3. Verify no regression in rate-limiting backpressure after token fixes
    goal        Five commits landed touching batch-mode and provider-integrations; Mistral backend is blocked on api_key configuration
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. rate-limiting and backpressure insights from cost estimation work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm Gemini batch unicode fix is solid
      2. Resolve Mistral api_key configuration so PR PR 584 can land
      3. Verify no regression in rate-limiting backpressure after token fixes   *** MUST RAISE ***
      4. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify no regression in rate-limiting backpressure after token fixes
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Gemini fix is confirmed safe; Mistral api_key issue is resolved and PR PR 584 can proceed; no rate-limiting regressions are identified


------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 9 PRs older than the era's median merge time (6.6h); 2 opened today; need to unblock or clarify intent

    Today is Wednesday 19 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 9 PRs older than the era's median merge time (6.6h); 2 opened today; need to unblock or clarify intent
    
    What it should get through:
      1. Approve batch-mode and release PRs so they can merge   [Konrad Feltrin must raise this]
           - Konrad confirms PR 594 and PR 595 are good to merge
           - Group agrees these unblock downstream work
           - PRs are closed
      2. Clarify path forward on stalled backend integrations   [Dario Kestrel must raise this]
           - Dario explains where PRs PR 565, PR 566, PR 579 stand
           - Emil notes the retry/batch refactor (PR PR 585) may subsume some of it
           - Group decides: merge stable parts, hold structural changes until next era
      3. Unblock feature PRs so they can land or be resurfaced next era   [Gideon Halloway must raise this]
           - Gideon raises disable-rich flag (PR PR 581) for cost-estimation work
           - Nikolai flags metadata-db param (PR PR 583) as ready
           - Group triages: approve ready ones, rescope ones that need rework
    
    On the agenda: Status of batch and provider PRs; Stalled backend integrations (openai, deepseek); Feature PRs blocking other work
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PRs PR 594, PR 595 are approved and merged; path is clear on backend integrations (stable parts land, structural changes deferred); feature PRs either land or are clearly rescoped for next era
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 295 changes merged to date

    On the table
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. approval authority on PR PR 594 and PR 595
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Approve batch-mode and release PRs so they can merge   *** MUST RAISE ***
      2. Clarify path forward on stalled backend integrations
      3. Unblock feature PRs so they can land or be resurfaced next era
    goal        Approve batch-mode and release PRs so they can merge
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ownership of deepseek and openai backends (PRs PR 565, PR 566)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve batch-mode and release PRs so they can merge
      2. Clarify path forward on stalled backend integrations   *** MUST RAISE ***
      3. Unblock feature PRs so they can land or be resurfaced next era
      4. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify path forward on stalled backend integrations
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on disable-rich flag needs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Approve batch-mode and release PRs so they can merge
      2. Clarify path forward on stalled backend integrations
      3. Unblock feature PRs so they can land or be resurfaced next era   *** MUST RAISE ***
    goal        Unblock feature PRs so they can land or be resurfaced next era
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. context on metadata db param (PR PR 583)
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Approve batch-mode and release PRs so they can merge
      2. Clarify path forward on stalled backend integrations
      3. Unblock feature PRs so they can land or be resurfaced next era
    goal        9 PRs older than the era's median merge time (6.6h); 2 opened today; need to unblock or clarify intent
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the retry/batch refactor (PR PR 585) and token-estimation context
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve batch-mode and release PRs so they can merge
      2. Clarify path forward on stalled backend integrations
      3. Unblock feature PRs so they can land or be resurfaced next era
    goal        9 PRs older than the era's median merge time (6.6h); 2 opened today; need to unblock or clarify intent
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PRs PR 594, PR 595 are approved and merged; path is clear on backend integrations (stable parts land, structural changes deferred); feature PRs either land or are clearly rescoped for next era


------------------------------------------------------------------------------
## #engineering — 14 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 7 commits landed today, 2 merged; v0.1.21 shipped; mistral batch mode is at kickoff with a known blocker

    Today is Wednesday 19 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 7 commits landed today, 2 merged; v0.1.21 shipped; mistral batch mode is at kickoff with a known blocker
    
    What it should get through:
      1. Sync team on v0.1.21 contents and stability   [Dermot Callaghan must raise this]
           - Dermot walks through the two bugfixes
           - Konrad confirms stability
           - Emil notes cost-estimation fix impact on accuracy
      2. Unblock Mistral batch work and confirm ETA   [Nils Brandt must raise this]
           - Nils explains api_key configuration issue
           - Emil confirms the fix is safe and complete
           - Gideon notes this unblocks cost-estimation testing with mistral
      3. Confirm output-token estimation fix has no backpressure regressions   [Gideon Halloway must raise this]
           - Gideon briefing on kluster.ai deepseek postmortem lessons
           - Emil walks through int-wrapping fix
           - Nils notes BaseState refactor is orthogonal
    
    On the agenda: v0.1.21 shipped: what landed and why; Mistral batch backend: blocker status and ETA; Rate-limiting and backpressure: output-token estimate fix implications
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what shipped in v0.1.21 and why; mistral batch api_key blocker is acknowledged and addressed; no concerns are raised about output-token estimation affecting rate limiting
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 295 changes merged to date

    On the table
      - notes-2025-03-17 (Nils Brandt)
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 432 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). five commits on batch-mode, mistral api_key fix, state management refactor
    owns        batch-mode, provider-integrations
    agenda
      1. Sync team on v0.1.21 contents and stability
      2. Unblock Mistral batch work and confirm ETA   *** MUST RAISE ***
      3. Confirm output-token estimation fix has no backpressure regressions
    goal        Unblock Mistral batch work and confirm ETA
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. v0.1.21 release just landed, gemini unicode fix, release notes context
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Sync team on v0.1.21 contents and stability   *** MUST RAISE ***
      2. Unblock Mistral batch work and confirm ETA
      3. Confirm output-token estimation fix has no backpressure regressions
      4. what "Weekly Notes — Week of Mar 17" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Sync team on v0.1.21 contents and stability
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. the output-token estimation fix (int wrapping) that just merged, rate-limiting backpressure lessons
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Sync team on v0.1.21 contents and stability
      2. Unblock Mistral batch work and confirm ETA
      3. Confirm output-token estimation fix has no backpressure regressions   *** MUST RAISE ***
      4. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm output-token estimation fix has no backpressure regressions
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. founder oversight and release QA perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Sync team on v0.1.21 contents and stability
      2. Unblock Mistral batch work and confirm ETA
      3. Confirm output-token estimation fix has no backpressure regressions
    goal        7 commits landed today, 2 merged; v0.1.21 shipped; mistral batch mode is at kickoff with a known blocker
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. token-estimation context and batch-mode depth
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Sync team on v0.1.21 contents and stability
      2. Unblock Mistral batch work and confirm ETA
      3. Confirm output-token estimation fix has no backpressure regressions
    goal        7 commits landed today, 2 merged; v0.1.21 shipped; mistral batch mode is at kickoff with a known blocker
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what shipped in v0.1.21 and why; mistral batch api_key blocker is acknowledged and addressed; no concerns are raised about output-token estimation affecting rate limiting

