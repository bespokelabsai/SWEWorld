# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-12-29 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two new PRs opened today need review before they can merge; one is a critical test fix

    Today is Monday 29 December 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two new PRs opened today need review before they can merge; one is a critical test fix
    
    What it should get through:
      1. Determine if PR 704 is release-ready   [Konrad Feltrin must raise this]
           - Konrad walks through the Claude model additions and why they were needed
           - Emil asks about test coverage and whether the CI exercises these new models
           - They settle on whether tests need to expand or if current coverage is sufficient
      2. Understand and land the test fix   [Konrad Feltrin must raise this]
           - Konrad explains what broke and why the fix works
           - Emil checks that the fix doesn't mask a deeper issue
           - They agree the fix is sound and can merge
    
    On the agenda: Review PR 704 (Claude model support) for correctness and test coverage; Review PR 705 (fix broken tests) to understand root cause; Assess whether either blocks the next release
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both PRs are scoped, one or both can merge, or a blocker surfaces that needs more work
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 368 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Implementation of Claude 4.x and 3.7 model support and the fix for broken tests
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Determine if PR 704 is release-ready   *** MUST RAISE ***
      2. Understand and land the test fix   *** MUST RAISE ***
    goal        Determine if PR 704 is release-ready
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Understanding of CI constraints and release readiness criteria
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if PR 704 is release-ready
      2. Understand and land the test fix
    goal        Two new PRs opened today need review before they can merge; one is a critical test fix
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Both PRs are scoped, one or both can merge, or a blocker surfaces that needs more work


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: A test fix landed in the repo affecting code-execution and CI; the cookbooks that depend on working verifiers need to be checked

    Today is Monday 29 December 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: A test fix landed in the repo affecting code-execution and CI; the cookbooks that depend on working verifiers need to be checked
    
    What it should get through:
      1. Confirm code-execution verifiers are not broken by the test fix   [Emil Brandvold must raise this]
           - Emil checks which tests Konrad Feltrin fixed and what they touch
           - Konrad confirms code-execution is still covered
           - They spot-check one verifier to be sure
    
    On the agenda: Review the test breakage Konrad Feltrin fixed; Check that code-execution verifiers still pass; Confirm the example corpus will run cleanly on the new models
    
    Out today: Nikolai Berresford (no commit, review or comment 2025-06-26..2026-01-21) — their input is missing and people may say so
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: The fix is confirmed safe for the verifier suite, or a secondary breakage is caught before it lands in a release
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 368 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Knowledge of what broke and what the fix does
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm code-execution verifiers are not broken by the test fix
    goal        A test fix landed in the repo affecting code-execution and CI; the cookbooks that depend on working verifiers need to be checked
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. View of CI status and which tests matter for cookbooks
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm code-execution verifiers are not broken by the test fix   *** MUST RAISE ***
    goal        Confirm code-execution verifiers are not broken by the test fix
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   The fix is confirmed safe for the verifier suite, or a secondary breakage is caught before it lands in a release


==============================================================================
# 2025-12-30 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR PR 706 needs final approval and merge

    Today is Tuesday 30 December 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 706 needs final approval and merge
    
    What it should get through:
      1. Get PR 706 merged to restore test health   [Konrad Feltrin must raise this]
           - Konrad presents what broke
           - Emil checks the fix is minimal and correct
           - Approval and land
    
    On the agenda: Review test failures that emerged; Approve fix for PR 706; Decide if other stale PRs need triage before moving on
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 706 is approved and merged; test suite is green again
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 369 changes merged to date

    On the table
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. diagnosis of what went wrong in the test suite and the fix itself
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get PR 706 merged to restore test health   *** MUST RAISE ***
      2. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 706 merged to restore test health
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. perspective on whether the fix is sound and whether it unblocks the release
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get PR 706 merged to restore test health
    goal        PR PR 706 needs final approval and merge
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 706 is approved and merged; test suite is green again


------------------------------------------------------------------------------
## #engineering — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Test suite red; blocking any further work during dormancy

    Today is Tuesday 30 December 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Test suite red; blocking any further work during dormancy
    
    What it should get through:
      1. Restore test health so dormancy work can continue   [Konrad Feltrin must raise this]
           - Konrad describes the failure
           - Emil asks if it affects other systems
           - Konrad confirms scope and fix
    
    On the agenda: Explain what broke in the test suite; Confirm the fix is sufficient; Return to dormancy maintenance mode
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what broke, fix is confirmed sufficient, dormancy maintenance resumes
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 369 changes merged to date

    On the table
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. root cause analysis and the fix for the broken tests
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Restore test health so dormancy work can continue   *** MUST RAISE ***
      2. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Restore test health so dormancy work can continue
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. understanding of whether the fix is sufficient or if deeper issues exist
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Restore test health so dormancy work can continue
    goal        Test suite red; blocking any further work during dormancy
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what broke, fix is confirmed sufficient, dormancy maintenance resumes


==============================================================================
# 2026-01-02 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil has two PRs stalled for 190+ days; Konrad just landed commits and owns code-execution which several PRs touch

    Today is Friday 2 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil has two PRs stalled for 190+ days; Konrad just landed commits and owns code-execution which several PRs touch
    
    What it should get through:
      1. Decide fate of 690 (Gemini multimodal batch) and 693 (streaming)   [Konrad Feltrin must raise this]
           - Emil explains why 690 and 693 matter to the next phase
           - Konrad assesses whether they fit the fine-tuning handoff work
           - They agree to either merge, defer, or close
      2. Clear or defer the pre-v0.1.26 PR backlog (675, 653, 698, 701)   [Konrad Feltrin must raise this]
           - Konrad scans the list for ones that are truly stale
           - Emil confirms which ones touch his areas
           - They sort into 'still needed', 'nice to have', 'safe to close'
    
    On the agenda: Which old PRs are still relevant to v0.1.26 or the fine-tuning work; Whether 690 and 693 need another look or are waiting on external factors; What the review load looks like and who owns triage going forward
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: A decision on each PR: merge, close, or explicit defer. At minimum, clarity on what is blocking Emil's streaming work.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 369 changes merged to date

    On the table
      - 2026 plan: fine-tuning handoff and drive-by PR triage (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. ownership of code-execution and understanding of which PRs block release
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Decide fate of 690 (Gemini multimodal batch) and 693 (streaming)   *** MUST RAISE ***
      2. Clear or defer the pre-v0.1.26 PR backlog (675, 653, 698, 701)   *** MUST RAISE ***
      3. what "2026 plan: fine-tuning handoff and drive-by PR triage" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Decide fate of 690 (Gemini multimodal batch) and 693 (streaming)
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on streaming and multimodal work that is blocked
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Decide fate of 690 (Gemini multimodal batch) and 693 (streaming)
      2. Clear or defer the pre-v0.1.26 PR backlog (675, 653, 698, 701)
    goal        Emil has two PRs stalled for 190+ days; Konrad just landed commits and owns code-execution which several PRs touch
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   A decision on each PR: merge, close, or explicit defer. At minimum, clarity on what is blocking Emil's streaming work.


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Konrad landed commits touching code-execution and release-and-ci; Emil owns release-and-ci and has stalled PRs in multimodal and streaming

    Today is Friday 2 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad landed commits touching code-execution and release-and-ci; Emil owns release-and-ci and has stalled PRs in multimodal and streaming
    
    What it should get through:
      1. Confirm that code-execution verifiers are exercised in CI   [Konrad Feltrin must raise this]
           - Konrad explains what the 'resolve comments' commit addressed
           - Emil checks whether CI coverage changed
           - They agree whether any cookbook tests need to be added
      2. Map code-execution into the fine-tuning handoff story   [Konrad Feltrin must raise this]
           - Konrad outlines how verifiers are used in the RAFT/SimpleStrat recipes
           - Emil notes which recipes are ready to publish
           - They settle on what goes into v0.1.27 or later
    
    On the agenda: What the two commits (resolve comments, merge main) changed in code-execution or CI; Whether the cookbooks need to be updated or verified before the next release; How code-execution fits into the fine-tuning recipes
    
    Out today: Nikolai Berresford (no commit, review or comment 2025-06-26..2026-01-21) — their input is missing and people may say so
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Confirmation that code-execution tests are in CI, and a plan for which cookbook examples go into the next release.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 369 changes merged to date

    On the table
      - 2026 plan: fine-tuning handoff and drive-by PR triage (Konrad Feltrin)
      - 2026 plan: fine-tuning handoff and drive-by PR triage (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 701: Fixed LiteLLM multi-hosted_vllm request address mixture. (Julian Marsden)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. the merge of new models and the overall arc of the fine-tuning handoff
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm that code-execution verifiers are exercised in CI   *** MUST RAISE ***
      2. Map code-execution into the fine-tuning handoff story   *** MUST RAISE ***
      3. what "2026 plan: fine-tuning handoff and drive-by PR triage" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "2026 plan: fine-tuning handoff and drive-by PR triage" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm that code-execution verifiers are exercised in CI
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. what the CI actually exercises and whether code-execution tests are upstream or downstream of a release
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm that code-execution verifiers are exercised in CI
      2. Map code-execution into the fine-tuning handoff story
    goal        Konrad landed commits touching code-execution and release-and-ci; Emil owns release-and-ci and has stalled PRs in multimodal and streaming
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Confirmation that code-execution tests are in CI, and a plan for which cookbook examples go into the next release.


==============================================================================
# 2026-01-22 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 707 just merged; 6 older PRs are waiting; only two people left to move them

    Today is Thursday 22 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 707 just merged; 6 older PRs are waiting; only two people left to move them
    
    What it should get through:
      1. Acknowledge PR 707 shipped and README is current   [Konrad Feltrin must raise this]
           - Konrad Feltrin notes the merge
           - Nikolai Berresford confirms he saw it
      2. Decide which stale PRs to review, request changes on, or defer   [Nikolai Berresford must raise this]
           - Nikolai Berresford lists the blockers and age
           - Konrad Feltrin and Nikolai Berresford triage by who can unblock what
           - land on next three to ship or consciously defer
    
    On the agenda: PR 707 merged, README current; Stale PR triage: PR 704, PR 675, PR 653, PR 690, PR 693, PR 698
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 707 shipped; stale PR triage sets priorities for the next sync; at least one older PR moves forward or is explicitly deferred
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 371 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 704: feat: add support for Claude 4.x and 3.7 models (Konrad Feltrin)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just shipped PR 707; knows what unblocks the backlog
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Acknowledge PR 707 shipped and README is current   *** MUST RAISE ***
      2. Decide which stale PRs to review, request changes on, or defer
    goal        Acknowledge PR 707 shipped and README is current
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. owns code-execution and release-and-ci; can unblock PR 653
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Acknowledge PR 707 shipped and README is current
      2. Decide which stale PRs to review, request changes on, or defer   *** MUST RAISE ***
    goal        Decide which stale PRs to review, request changes on, or defer
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 707 shipped; stale PR triage sets priorities for the next sync; at least one older PR moves forward or is explicitly deferred


------------------------------------------------------------------------------
## #engineering — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: ws-081 (README refresh) is in landing stage; PR 707 just merged; need to confirm close or identify remaining work

    Today is Thursday 22 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: ws-081 (README refresh) is in landing stage; PR 707 just merged; need to confirm close or identify remaining work
    
    What it should get through:
      1. Confirm README refresh is complete or identify missing pieces   [Konrad Feltrin must raise this]
           - Konrad Feltrin summarizes what shipped in PR 707
           - Nikolai Berresford checks completeness against the plan
    
    On the agenda: README refresh landed and current; What comes next in the cookbook/examples space
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Workstream landing confirmed or blockers identified; next work in examples-cookbooks is clear
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 371 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 704: feat: add support for Claude 4.x and 3.7 models (Konrad Feltrin)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just landed the README refresh
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm README refresh is complete or identify missing pieces   *** MUST RAISE ***
    goal        Confirm README refresh is complete or identify missing pieces
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. perspective on whether README is complete
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm README refresh is complete or identify missing pieces
    goal        ws-081 (README refresh) is in landing stage; PR 707 just merged; need to confirm close or identify remaining work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Workstream landing confirmed or blockers identified; next work in examples-cookbooks is clear


==============================================================================
# 2026-01-23 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 704 has been open 25 days; Konrad Feltrin shipped it today and needs review before it can land

    Today is Friday 23 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 704 has been open 25 days; Konrad Feltrin shipped it today and needs review before it can land
    
    What it should get through:
      1. Establish whether PR 704 is safe to merge   [Konrad Feltrin must raise this]
           - Konrad Feltrin walks through the changes: what model versions were added, where
           - Nikolai Berresford checks for ripple effects in provider-integrations or release-and-ci
           - decision: merge or ask for changes
    
    On the agenda: Review scope of PR 704: model list and pricing updates; Check for side effects in provider integrations; Decide merge readiness
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 704 moves to approved or needs-changes; Konrad Feltrin knows the blocking feedback
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 371 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 704: feat: add support for Claude 4.x and 3.7 models (Konrad Feltrin)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just shipped three commits adding Claude 4.x and 3.7 support; knows what landed
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Establish whether PR 704 is safe to merge   *** MUST RAISE ***
    goal        Establish whether PR 704 is safe to merge
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. owns code-execution and release-and-ci; can spot if the change breaks existing patterns
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Establish whether PR 704 is safe to merge
    goal        PR 704 has been open 25 days; Konrad Feltrin shipped it today and needs review before it can land
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 704 moves to approved or needs-changes; Konrad Feltrin knows the blocking feedback


------------------------------------------------------------------------------
## #engineering — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Konrad Feltrin shipped three commits today across kickoff-stage workstreams; crew needs to know what landed and what is in flight

    Today is Friday 23 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Konrad Feltrin shipped three commits today across kickoff-stage workstreams; crew needs to know what landed and what is in flight
    
    What it should get through:
      1. Surface the cleanup work before it accumulates   [Konrad Feltrin must raise this]
           - Konrad Feltrin: cleaning up request-processing code before it rots, nothing functional
           - Nikolai Berresford: asks what the risk is if we don't clean it
           - lands as: good housekeeping, no blocker
    
    On the agenda: Status on Claude 4.x/3.7 support work; Clean-up work in online-request-processing scope and rationale
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nikolai Berresford understands the scope of both workstreams; crew knows PR 704 is the unlock
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 371 changes merged to date

    On the table
      - 2026 plan: fine-tuning handoff and drive-by PR triage (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 704: feat: add support for Claude 4.x and 3.7 models (Konrad Feltrin)

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
      - — and 263 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just landed three commits: two to online-request-processing, one to code-execution; knows what is done and what remains
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Surface the cleanup work before it accumulates   *** MUST RAISE ***
      2. what "2026 plan: fine-tuning handoff and drive-by PR triage" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Surface the cleanup work before it accumulates
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. owns code-execution and release-and-ci; can spot if cleanup work has hidden implications
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Surface the cleanup work before it accumulates
    goal        Konrad Feltrin shipped three commits today across kickoff-stage workstreams; crew needs to know what landed and what is in flight
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nikolai Berresford understands the scope of both workstreams; crew knows PR 704 is the unlock

