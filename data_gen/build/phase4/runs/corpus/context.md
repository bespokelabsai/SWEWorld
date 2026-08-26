# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-06-03 — 3 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two fixes merged and opened today; three older PRs still pending; small team needs to sync on what is still moving

    Today is Tuesday 3 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two fixes merged and opened today; three older PRs still pending; small team needs to sync on what is still moving
    
    What it should get through:
      1. Land PR 681 as-is or with nits   [Konrad Feltrin must raise this]
           - Konrad flags it's ready; Emil confirms approval stands; merged
      2. Get PR 683 through review or to revision   [Emil Brandvold must raise this]
           - Emil walks through the check; Nikolai's approval noted; next step clear
      3. Decide fate of PR 653, PR 663, PR 675   [Nikolai Berresford must raise this]
           - Nikolai surfaces the age; Konrad or Emil says keep/drop/reassign; owners know
    
    On the agenda: PR 681 cost-reporting safety lands; PR 683 structured output check goes live; Clear the stale PR backlog
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 681 merges; PR 683 path forward is clear; team agrees on three stale PRs
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 360 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 683: ref: check structured outputs support with litellm (Emil Brandvold)

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
      - — and 275 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns the fixes landing today and understands their scope
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Land PR 681 as-is or with nits   *** MUST RAISE ***
      2. Get PR 683 through review or to revision
      3. Decide fate of PR 653, PR 663, PR 675
    goal        Land PR 681 as-is or with nits
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. just approved PR 681 and opened PR 683; knows both pieces
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 681 as-is or with nits
      2. Get PR 683 through review or to revision   *** MUST RAISE ***
      3. Decide fate of PR 653, PR 663, PR 675
    goal        Get PR 683 through review or to revision
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. approved PR 683; blocked on PR 653 and PR 663 which predate this era
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Land PR 681 as-is or with nits
      2. Get PR 683 through review or to revision
      3. Decide fate of PR 653, PR 663, PR 675   *** MUST RAISE ***
    goal        Decide fate of PR 653, PR 663, PR 675
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 681 merges; PR 683 path forward is clear; team agrees on three stale PRs


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three small fixes to dormancy-phase issues landing and opening today; team needs context on direction

    Today is Tuesday 3 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three small fixes to dormancy-phase issues landing and opening today; team needs context on direction
    
    What it should get through:
      1. Align on cost-reporting safeguard approach   [Konrad Feltrin must raise this]
           - Konrad explains the model-unknown case; Emil and Nikolai confirm it does not break anything they own; path clear
      2. Confirm torch safety is holding   [Emil Brandvold must raise this]
           - Emil notes the test update; Nikolai confirms no one is hitting the old path; check passes
      3. Validate litellm structured-output detection   [Emil Brandvold must raise this]
           - Emil walks through the check logic; Nikolai approves the scope; Konrad notes it fits the dormancy phase
    
    On the agenda: Why cost can be None now; Torch import guards working; Litellm compatibility check approach
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees all three fixes are safe; no surprises in review; work stays in flight
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 360 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 683: ref: check structured outputs support with litellm (Emil Brandvold)

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
      - — and 275 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. designed the cost-safety fix; understands the broader dormancy plan
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Align on cost-reporting safeguard approach   *** MUST RAISE ***
      2. Confirm torch safety is holding
      3. Validate litellm structured-output detection
    goal        Align on cost-reporting safeguard approach
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. just landed a test update and opened the litellm structured-output check
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Align on cost-reporting safeguard approach
      2. Confirm torch safety is holding   *** MUST RAISE ***
      3. Validate litellm structured-output detection   *** MUST RAISE ***
    goal        Confirm torch safety is holding
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. knows the code-execution and telemetry layer; just approved the structured-output PR
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Align on cost-reporting safeguard approach
      2. Confirm torch safety is holding
      3. Validate litellm structured-output detection
    goal        Three small fixes to dormancy-phase issues landing and opening today; team needs context on direction
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team agrees all three fixes are safe; no surprises in review; work stays in flight


------------------------------------------------------------------------------
## #viewer — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Two changes to services that touch viewer today; need to confirm display and counting stay sound

    Today is Tuesday 3 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two changes to services that touch viewer today; need to confirm display and counting stay sound
    
    What it should get through:
      1. Viewer cost display safe for unknown-model case   [Emil Brandvold must raise this]
           - Konrad surfaces the change; Emil checks the viewer rendering; no display regression
    
    On the agenda: Cost display handles None safely; Test coverage for the edge case
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Viewer cost counter and progress table handle the new None case cleanly; no UI breaks
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 360 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 663: fix error when torch isn't installed (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 683: ref: check structured outputs support with litellm (Emil Brandvold)

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
      - — and 275 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. just fixed cost reporting for unknown models; affects what viewer shows
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Viewer cost display safe for unknown-model case
    goal        Two changes to services that touch viewer today; need to confirm display and counting stay sound
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns the viewer surface; knows what it displays and how it will render None cost
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Viewer cost display safe for unknown-model case   *** MUST RAISE ***
    goal        Viewer cost display safe for unknown-model case
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Viewer cost counter and progress table handle the new None case cleanly; no UI breaks


==============================================================================
# 2025-06-04 — 3 conversation(s), 24 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two agent PRs need eyes before the next wave of agentic-curation work lands

    Today is Wednesday 4 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two agent PRs need eyes before the next wave of agentic-curation work lands
    
    What it should get through:
      1. Stopping criterion design approved   [Konrad Feltrin must raise this]
           - Emil walks through the criterion logic and where it hooks into the generation loop
           - Konrad flags any interaction concerns with retries or structured outputs
           - Decision: approve or request changes
    
    On the agenda: Review stopping criterion design in PR 684; Discuss interaction with multi-turn generation loop; Check remaining agent fixes in PR 685
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 684 approved and ready to merge; PR 685 flagged for follow-up
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 363 changes merged to date

    On the table
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 685: Ref agent multiturn minor (Emil Brandvold)

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
      - — and 270 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Implementation of stopping criterion and the multi-turn agent design
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Stopping criterion design approved
    goal        Two agent PRs need eyes before the next wave of agentic-curation work lands
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Fresh eyes on stopping criterion logic and integration with existing agent code
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Stopping criterion design approved   *** MUST RAISE ***
      2. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Stopping criterion design approved
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 684 approved and ready to merge; PR 685 flagged for follow-up


------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three commits to agentic-curation today; stopping criterion is a key missing piece for self-play

    Today is Wednesday 4 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three commits to agentic-curation today; stopping criterion is a key missing piece for self-play
    
    What it should get through:
      1. Stopping criterion integrated into multi-turn agent   [Emil Brandvold must raise this]
           - Emil describes the criterion types (turn count, content-based, learned) and why the design chose what it did
           - Konrad asks about interaction with existing generation features
           - Agreement on the shape; no blocking concerns
    
    On the agenda: Stopping criterion shape and API; Multi-turn agent readiness status; Remaining work on agent improvements
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Stopping criterion lands in PR 684; team aware of multi-turn agent status heading into next sprint
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 363 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 2 (release + CI) (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 685: Ref agent multiturn minor (Emil Brandvold)

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
      - — and 270 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The stopping criterion implementation and design rationale
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Stopping criterion integrated into multi-turn agent   *** MUST RAISE ***
      2. that the doc "Weekly sync notes: week of Jun 2 (release + CI)" is done, and where the others can find it   *** MUST RAISE ***
      3. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Stopping criterion integrated into multi-turn agent
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Feedback on stopping criterion interaction with the broader generation loop
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Stopping criterion integrated into multi-turn agent
    goal        Three commits to agentic-curation today; stopping criterion is a key missing piece for self-play
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Stopping criterion lands in PR 684; team aware of multi-turn agent status heading into next sprint


------------------------------------------------------------------------------
## #cookbooks — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Four changes to release-and-ci; torch-dependency fix and test refactoring need cookbook awareness

    Today is Wednesday 4 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four changes to release-and-ci; torch-dependency fix and test refactoring need cookbook awareness
    
    What it should get through:
      1. Test changes don't mask cookbook failures   [Nikolai Berresford must raise this]
           - Nikolai explains the torch-import guard and why the test needed modification
           - Emil checks if structured-outputs checking still catches real problems
           - Agreement that coverage is maintained
    
    On the agenda: Torch dependency handling in tests; Test structure after PR PR 663 changes; Structured-output support checking in CI
    
    Meeting today: Weekly sync
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Torch-dependency fix and test changes understood as compatible with cookbook verification
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 363 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 2 (release + CI) (Emil Brandvold)
      - Weekly Notes — Week of May 26 (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 685: Ref agent multiturn minor (Emil Brandvold)

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
      - — and 270 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Understanding of the structured-outputs checking work and how it cascades to CI
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Test changes don't mask cookbook failures
    goal        Four changes to release-and-ci; torch-dependency fix and test refactoring need cookbook awareness
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. The torch-dependency fix and test modifications
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Test changes don't mask cookbook failures   *** MUST RAISE ***
      2. what "Weekly Notes — Week of May 26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Test changes don't mask cookbook failures
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Torch-dependency fix and test changes understood as compatible with cookbook verification


==============================================================================
# 2025-06-06 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two commits merged on the same day; bump is a chore but the refactor is landing from agentic curation

    Today is Friday 6 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two commits merged on the same day; bump is a chore but the refactor is landing from agentic curation
    
    What it should get through:
      1. Confirm v0.1.26 bump is ready to ship   [Emil Brandvold must raise this]
           - Emil flags the bump as merged
           - Konrad confirms his approval stands
           - Both agree the release can proceed
      2. Lock in the multiturn stopping criterion refactor   [Emil Brandvold must raise this]
           - Emil summarizes what the refactor tightens
           - Konrad confirms it does not regress the agent shape
    
    On the agenda: Version bump approval; Multiturn refactor landing
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both PRs are confirmed merged and the team knows the refactor is stable enough to include in 0.1.26.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 365 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 2 (release + CI) (Emil Brandvold)
      - Weekly Notes — Week of May 26 (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

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
    role        Core Platform Engineer, Request Processing. ownership of both PRs and context on the refactor and bump
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm v0.1.26 bump is ready to ship   *** MUST RAISE ***
      2. Lock in the multiturn stopping criterion refactor   *** MUST RAISE ***
      3. what "Weekly sync notes: week of Jun 2 (release + CI)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Weekly Notes — Week of May 26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm v0.1.26 bump is ready to ship
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. fresh eyes on the version bump
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm v0.1.26 bump is ready to ship
      2. Lock in the multiturn stopping criterion refactor
    goal        Two commits merged on the same day; bump is a chore but the refactor is landing from agentic curation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both PRs are confirmed merged and the team knows the refactor is stable enough to include in 0.1.26.


------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: Version bump merged; 0.1.26 is ready to cut and tag

    Today is Friday 6 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Version bump merged; 0.1.26 is ready to cut and tag
    
    What it should get through:
      1. Confirm 0.1.26 is ready to tag   [Emil Brandvold must raise this]
           - Emil walks the commits in since 0.1.25
           - Konrad checks against the dormancy plan
           - Both agree scope is locked
      2. Lock the tag and bump for 0.1.26   [Emil Brandvold must raise this]
           - Emil confirms CI green and changelog ready
           - Konrad approves the tag
           - Emil cuts the release
    
    On the agenda: Scope confirmation for 0.1.26; Tag and release readiness
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: 0.1.26 is tagged, version bumped in tree, and a release notes artifact is in flight.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 365 changes merged to date

    On the table
      - v0.1.25 Release Notes (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)

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
    role        Core Platform Engineer, Request Processing. the merged commits and readiness to tag
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm 0.1.26 is ready to tag   *** MUST RAISE ***
      2. Lock the tag and bump for 0.1.26   *** MUST RAISE ***
      3. what "v0.1.25 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm 0.1.26 is ready to tag
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. oversight of what is in scope for this release
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm 0.1.26 is ready to tag
      2. Lock the tag and bump for 0.1.26
    goal        Version bump merged; 0.1.26 is ready to cut and tag
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   0.1.26 is tagged, version bumped in tree, and a release notes artifact is in flight.


==============================================================================
# 2025-06-11 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two significant PRs stalled during dormancy period; new Pydantic fix needs immediate review

    Today is Wednesday 11 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two significant PRs stalled during dormancy period; new Pydantic fix needs immediate review
    
    What it should get through:
      1. Determine if PR 653 can land or needs rework   [Nikolai Berresford must raise this]
           - Nikolai Berresford outlines blockers or readiness status
           - Emil Brandvold assesses against release criteria
           - either defer or schedule merge
      2. Assess priority and fit of new Pydantic fix   [Emil Brandvold must raise this]
           - Emil Brandvold reviews scope and urgency
           - determine if blocks existing work
           - fast-track or queue normally
    
    On the agenda: Review status of PR 653 (finetuning client, 46 days old); Assess PR 675 (app id parameter, 18 days old); Triage PR 689 (Pydantic fix, opened today)
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PRs triaged; PR 689 either merged or queued; plan for landing 653 or closing it
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 365 changes merged to date

    On the table
      - v0.1.25 Release Notes (Emil Brandvold)
      - Winding down to maintenance mode after v0.1.26 (Konrad Feltrin)
      - Weekly sync notes: week of Jun 9 (bulk LLM inference) (Emil Brandvold)
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 689: fix: resolve Pydantic issues (Rafael Duquette)

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
    role        Core Platform Engineer, Request Processing. knowledge of release blocking and CI integration from recent v0.1.25 work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if PR 653 can land or needs rework
      2. Assess priority and fit of new Pydantic fix   *** MUST RAISE ***
      3. that the doc "Weekly sync notes: week of Jun 9 (bulk LLM inference)" is done, and where the others can find it   *** MUST RAISE ***
    goal        Assess priority and fit of new Pydantic fix
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. context on finetuning client work stalled 46 days
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Determine if PR 653 can land or needs rework   *** MUST RAISE ***
      2. Assess priority and fit of new Pydantic fix
      3. what "v0.1.25 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Winding down to maintenance mode after v0.1.26" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine if PR 653 can land or needs rework
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PRs triaged; PR 689 either merged or queued; plan for landing 653 or closing it


==============================================================================
# 2025-06-13 — 2 conversation(s), 14 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today need review; one stale PR waiting 48 days needs sequencing clarity

    Today is Friday 13 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today need review; one stale PR waiting 48 days needs sequencing clarity
    
    What it should get through:
      1. Land PR 690 and PR 691 with approved reviews   [Emil Brandvold must raise this]
           - Emil flags both as ready for eyes
           - Nikolai asks about multimodal and batch interactions
           - Resolution: both approved or feedback noted
      2. Unblock or defer PR 653 based on these two landing   [Nikolai Berresford must raise this]
           - Nikolai raises that 653 has been waiting 48 days
           - Emil clarifies whether multimodal/batch changes affect finetuning path
           - Decision: merge order or rework needed
    
    On the agenda: Review PR 690 (Multimodal Gemini Batch) and PR 691 (auto batch mode); Sequencing with PR 653 (finetuning client); Identify any blockers before merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both 690 and 691 approved; clarity on whether 653 can merge next or needs rework
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 366 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 9 (bulk LLM inference) (Emil Brandvold)
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
    role        Core Platform Engineer, Request Processing. ownership of release-and-ci and online-request-processing; context on multimodal and batch work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 690 and PR 691 with approved reviews   *** MUST RAISE ***
      2. Unblock or defer PR 653 based on these two landing
      3. what "Weekly sync notes: week of Jun 9 (bulk LLM inference)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 690 and PR 691 with approved reviews
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. understanding of which work blocks or unblocks his own; stake in release sequencing
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Land PR 690 and PR 691 with approved reviews
      2. Unblock or defer PR 653 based on these two landing   *** MUST RAISE ***
    goal        Unblock or defer PR 653 based on these two landing
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both 690 and 691 approved; clarity on whether 653 can merge next or needs rework


------------------------------------------------------------------------------
## #engineering — 6 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: One commit merged today (Pydantic fix across five services); two new PRs open same day; need team awareness and integration check

    Today is Friday 13 June 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: One commit merged today (Pydantic fix across five services); two new PRs open same day; need team awareness and integration check
    
    What it should get through:
      1. Confirm Pydantic fix does not break integration across services   [Emil Brandvold must raise this]
           - Emil notes PR 689 merged; touches bulk-llm-inference, caching, online-request-processing, progress, provider integrations
           - Nikolai asks whether code-execution or telemetry see any side effects
           - Resolution: no breakage expected or identified breakage noted
      2. Surface scope of batch and multimodal work to team   [Emil Brandvold must raise this]
           - Emil describes 690 (multimodal Gemini batch) and 691 (auto batch mode)
           - Nikolai flags any overlap with finetuning or code execution
           - Status: scoped clearly or deferred for deeper design
    
    On the agenda: Pydantic fix (PR 689) merged and impact; Two fresh multimodal and batch PRs and their scope; Any fallout or hidden interactions
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team aware of Pydantic fix and its reach; scope of new PRs clear; no hidden integration failures
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Lights Left On: Dormancy After v0.1.26

    Settled
      - 24 release(s) shipped, currently v0.1.25
      - 366 changes merged to date

    On the table
      - Weekly sync notes: week of Jun 9 (bulk LLM inference) (Emil Brandvold)
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
    role        Core Platform Engineer, Request Processing. visibility into what the Pydantic fix touched; context on batch and multimodal work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Pydantic fix does not break integration across services   *** MUST RAISE ***
      2. Surface scope of batch and multimodal work to team   *** MUST RAISE ***
      3. what "Weekly sync notes: week of Jun 9 (bulk LLM inference)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Pydantic fix does not break integration across services
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. understanding of whether fix affects code execution or telemetry; awareness of integration points
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm Pydantic fix does not break integration across services
      2. Surface scope of batch and multimodal work to team
    goal        One commit merged today (Pydantic fix across five services); two new PRs open same day; need team awareness and integration check
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team aware of Pydantic fix and its reach; scope of new PRs clear; no hidden integration failures

